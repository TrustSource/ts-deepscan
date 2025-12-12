"""
Caching wrapper for FileAnalyser implementations.

This module provides CachedAnalyzer which wraps any FileAnalyser with
transparent caching using the shared ResultsCache.
"""
import json
import typing as t
import xxhash

from pathlib import Path

from . import FileAnalyser, AnalysisResult
from ..caching import ResultsCache, CacheableResult, DEFAULT_CACHE_DIR


def _fast_file_hash(path: Path, blocksize: int = 1 << 20) -> str:
    """Compute a fast xxhash64 hash of a file's contents."""
    h = xxhash.xxh64()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(blocksize)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _options_fingerprint(opts: t.Optional[t.Mapping[str, t.Any]]) -> t.Optional[str]:
    """Compute a fingerprint for options dict to include in cache key."""
    if not opts:
        return None
        
    payload = json.dumps(
        opts, sort_keys=True, separators=(',', ':'), ensure_ascii=False
    ).encode('utf-8')
    
    h = xxhash.xxh64()
    h.update(payload)
    
    return h.hexdigest()


class CacheableAnalysisResult(AnalysisResult, CacheableResult):
    """
    Extends AnalysisResult with cache metadata for delayed storage.
    
    Inherits from both AnalysisResult and CacheableResult, so it can be:
    - Used as an AnalysisResult in the analysis pipeline
    - Passed directly to ResultsCache.store() for caching
    
    When CachedAnalyzer.auto_store is False, this is returned instead of
    storing the result immediately. The caller (e.g., a post-processor)
    can later store it using ResultsCache.store(result) directly.
    """
    
    def __init__(
        self,
        category: str,
        data: t.Any,
        cache_key: str,
        fastpath_key: str,
        file_size: int,
        mtime_ns: int,
    ):
        AnalysisResult.__init__(self, category, data)
        CacheableResult.__init__(self, data, cache_key, fastpath_key, file_size, mtime_ns)


class CachingAnalyzer(FileAnalyser):
    """
    Wraps a FileAnalyser with transparent caching.
    
    This analyser uses a ResultsCache to cache analysis results,
    avoiding redundant computation for unchanged files.
    
    Args:
        analyser: The underlying FileAnalyser to wrap
        cache: Optional shared ResultsCache instance. If not provided,
            a new cache will be created with default settings.
        version: Cache version string for invalidation
        auto_store: If True, store results immediately. If False, return
            CacheableAnalysisResult for delayed storage.
        use_fastpath: If True, use stat-based fast-path optimization.
    """
    
    def __init__(
        self,
        analyser: FileAnalyser,
        cache: t.Optional[ResultsCache] = None,
        version: str = '1',
        auto_store: bool = True,
        use_fastpath: bool = True,
    ) -> None:
        self.analyser = analyser
        self.version = version
        self.auto_store = auto_store
        self.use_fastpath = use_fastpath
        
        # Use provided cache or create a new one
        if cache is not None:
            self._cache = cache
            self._owns_cache = False
        else:
            self._cache = ResultsCache(cache_dir=DEFAULT_CACHE_DIR)
            self._owns_cache = True
    
    @property
    def cache(self) -> ResultsCache:
        """The underlying ResultsCache instance."""
        return self._cache
    
    @property
    def category(self) -> str:
        return self.analyser.category
    
    @property
    def options(self) -> dict:
        return self.analyser.options
    
    def _match(self, path: Path) -> bool:
        return self.analyser._match(path)
    
    def _make_cache_key(
        self,
        file_hash: str,
        file_size: int,
        opt_fp: t.Optional[str],
    ) -> str:
        """Generate the primary cache key."""
        base = f'{self.category}:v{self.version}:{file_hash}:{file_size}'
        return f'{base}:opts:{opt_fp}' if opt_fp else base
    
    def _make_fastpath_key(
        self,
        path: Path,
        opt_fp: t.Optional[str],
    ) -> str:
        """Generate the fast-path cache key."""
        return f"fast:{self.category}:v{self.version}:{path.resolve()}:{opt_fp or 'noopts'}"
    
    def apply(self, path: Path, root: t.Optional[Path] = None) -> t.Optional[AnalysisResult]:
        """
        Apply analysis with caching support.
        
        Args:
            path: Path to the file to analyse
            root: Root directory for relative path computation
            
        Returns:
            - AnalysisResult if cache hit or auto_store=True
            - CacheableAnalysisResult (subclass of AnalysisResult) if cache miss and auto_store=False
            - None if no result
        """
        if not path.is_file():
            raise FileNotFoundError(path)
        
        st = path.stat()
        opt_fp = _options_fingerprint(self.options)
        fastpath_key = self._make_fastpath_key(path, opt_fp)
        
        # Try fast-path first
        if self.use_fastpath:
            hit, data = self._cache.get_with_fastpath(
                cache_key='',  # We don't have it yet, but fastpath might
                fastpath_key=fastpath_key,
                file_size=st.st_size,
                mtime_ns=st.st_mtime_ns,
            )
            if hit:
                return AnalysisResult(self.category, data) if data is not None else None
        
        # Compute content hash for authoritative key
        file_hash = _fast_file_hash(path)
        cache_key = self._make_cache_key(file_hash, st.st_size, opt_fp)
        
        # Try primary key lookup
        hit, data = self._cache.get(cache_key)
        if hit:
            # Refresh fastpath
            if self.use_fastpath:
                st2 = path.stat()
                self._cache.set_with_fastpath(
                    cache_key, data, fastpath_key, st2.st_size, st2.st_mtime_ns
                )
            return AnalysisResult(self.category, data) if data is not None else None
        
        # Cache miss → compute
        result = self.analyser.apply(path, root)
        
        # Get current stat for cache info (file may have changed during analysis)
        st_now = path.stat()
        
        if self.auto_store:
            # Store the result immediately
            data = result.data if result else None
            if self.use_fastpath:
                self._cache.set_with_fastpath(
                    cache_key, data, fastpath_key, st_now.st_size, st_now.st_mtime_ns
                )
            else:
                self._cache.set(cache_key, data)
            return result
        else:
            # Return CacheableAnalysisResult for delayed storage
            if result is None:
                return None
            return CacheableAnalysisResult(
                category=result.category,
                data=result.data,
                cache_key=cache_key,
                fastpath_key=fastpath_key,
                file_size=st_now.st_size,
                mtime_ns=st_now.st_mtime_ns,
            )
    
    def store(self, cacheable: CacheableAnalysisResult) -> AnalysisResult:
        """
        Store a CacheableAnalysisResult in the cache.
        
        This method is used when auto_store=False for delayed storage of results.
        Note: You can also call cache.store(cacheable) directly.
        
        Args:
            cacheable: The CacheableAnalysisResult to store
            
        Returns:
            The same CacheableAnalysisResult (which is an AnalysisResult)
        """
        self._cache.store(cacheable)
        return cacheable
    
    def clear(self) -> None:
        """Completely empties the cache directory."""
        self._cache.clear()
    
    def close(self) -> None:
        """Close the underlying diskcache (flushes to disk)."""
        if self._owns_cache:
            self._cache.close()
