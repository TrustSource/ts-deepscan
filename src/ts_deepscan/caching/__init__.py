"""
Caching infrastructure for analysis results.

This module provides a simple key-value cache for storing analysis results.
Key generation and domain logic belongs to the caller (e.g., CachedAnalyser).
"""
import typing as t

from pathlib import Path
from diskcache import Cache


# Sentinel object to distinguish "not in cache" from "cached None"
_CACHE_MISS = object()

# Default cache location
DEFAULT_CACHE_DIR = Path('~/.ts-scan/caches/ds').expanduser()


class Cacheable(t.Protocol):
    """Protocol for objects that can be stored in the cache."""
    data: t.Any
    cache_key: str
    fastpath_key: str
    file_size: int
    mtime_ns: int


class CacheableResult:
    """
    A result with cache metadata for storage.
    
    This is the base cacheable type used by ResultsCache.store().
    Analysers may extend this (e.g., CacheableAnalysisResult) to add
    domain-specific fields like category.
    
    Attributes:
        data: The data to cache
        cache_key: The primary cache key (content-based)
        fastpath_key: The fast-path cache key (stat-based)
        file_size: File size at analysis time
        mtime_ns: File modification time (nanoseconds) at analysis time
    """
    
    def __init__(
        self,
        data: t.Any,
        cache_key: str,
        fastpath_key: str,
        file_size: int,
        mtime_ns: int,
    ):
        self.data = data
        self.cache_key = cache_key
        self.fastpath_key = fastpath_key
        self.file_size = file_size
        self.mtime_ns = mtime_ns


class ResultsCache:
    """
    A simple key-value cache for analysis results.
    
    This cache stores and retrieves data by keys. Key generation and
    domain-specific logic (categories, versions, file hashing) belongs
    to the caller.
    
    Features:
        - Simple get/set by key
        - Optional fast-path optimization using file stat (size + mtime)
        - Configurable size limits and eviction policies
        - Sharded storage for concurrent access
    
    Example:
        cache = ResultsCache()
        
        # Simple lookup by key
        data = cache.get(key)
        if data is not None:
            return data
        
        # Store result
        cache.set(key, result)
        
        # Or with fastpath support
        hit, data = cache.get_with_fastpath(cache_key, fastpath_key, size, mtime_ns)
        if hit:
            return data
        
        cache.set_with_fastpath(cache_key, result, fastpath_key, size, mtime_ns)
    """
    
    def __init__(
        self,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        size_limit: int = 2 * 1024 * 1024 * 1024,  # 2 GiB
        eviction_policy: str = 'least-recently-stored',
        shards: int = 8,
    ) -> None:
        """
        Initialize the results cache.
        
        Args:
            cache_dir: Directory to store cache files
            size_limit: Maximum cache size in bytes (default 2 GiB)
            eviction_policy: Cache eviction policy
            shards: Number of shards for concurrent access
        """
        self.cache_dir = cache_dir
        
        self._cache = Cache(
            directory=str(cache_dir),
            size_limit=size_limit,
            eviction_policy=eviction_policy,
            shards=shards,
        )
    
    def get(self, key: str) -> t.Tuple[bool, t.Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            Tuple of (hit, data) where hit is True if found
        """
        result = self._cache.get(key, default=_CACHE_MISS)
        if result is _CACHE_MISS:
            return False, None
        return True, result
    
    def set(self, key: str, data: t.Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            data: The data to cache (can be None)
        """
        self._cache.set(key, data, expire=None)
    
    def get_with_fastpath(
        self,
        cache_key: str,
        fastpath_key: str,
        file_size: int,
        mtime_ns: int,
    ) -> t.Tuple[bool, t.Any]:
        """
        Get a value using fast-path optimization.
        
        First checks the fastpath entry (stat-based). If the file size and
        mtime match, returns the cached data without content hashing.
        
        Args:
            cache_key: The primary cache key (content-based)
            fastpath_key: The fast-path cache key (stat-based)
            file_size: Current file size
            mtime_ns: Current file modification time (nanoseconds)
            
        Returns:
            Tuple of (hit, data) where hit is True if found
        """
        # Try fast-path first
        fp = self._cache.get(fastpath_key)
        if fp and isinstance(fp, dict):
            if fp.get('size') == file_size and fp.get('mtime_ns') == mtime_ns:
                fp_cache_key = fp.get('cache_key')
                if fp_cache_key is not None:
                    result = self._cache.get(fp_cache_key, default=_CACHE_MISS)
                    if result is not _CACHE_MISS:
                        return True, result
        
        # Try primary key
        result = self._cache.get(cache_key, default=_CACHE_MISS)
        if result is not _CACHE_MISS:
            # Refresh fastpath metadata
            self._cache.set(
                fastpath_key,
                {'cache_key': cache_key, 'size': file_size, 'mtime_ns': mtime_ns},
                expire=None,
            )
            return True, result
        
        return False, None
    
    def set_with_fastpath(
        self,
        cache_key: str,
        data: t.Any,
        fastpath_key: str,
        file_size: int,
        mtime_ns: int,
    ) -> None:
        """
        Store a value with fast-path metadata.
        
        Args:
            cache_key: The primary cache key
            data: The data to cache (can be None)
            fastpath_key: The fast-path cache key
            file_size: File size for fastpath metadata
            mtime_ns: File mtime for fastpath metadata
        """
        self._cache.set(cache_key, data, expire=None)
        self._cache.set(
            fastpath_key,
            {'cache_key': cache_key, 'size': file_size, 'mtime_ns': mtime_ns},
            expire=None,
        )
    
    @t.overload
    def store(
        self,
        data: t.Any,
        cache_key: str,
        fastpath_key: str,
        file_size: int,
        mtime_ns: int,
    ) -> None: ...
    
    @t.overload
    def store(self, data: Cacheable) -> None: ...
    
    def store(
        self,
        data: t.Any,
        cache_key: t.Optional[str] = None,
        fastpath_key: t.Optional[str] = None,
        file_size: t.Optional[int] = None,
        mtime_ns: t.Optional[int] = None,
    ) -> None:
        """
        Store data in the cache (convenience method).
        
        Can be called with individual parameters or with a Cacheable object
        (e.g., CacheableAnalysisResult from CachedAnalyser).
        
        Args:
            data: The data to cache, or a Cacheable object
            cache_key: The primary cache key (not needed if data is Cacheable)
            fastpath_key: The fast-path cache key (not needed if data is Cacheable)
            file_size: File size for fastpath metadata (not needed if data is Cacheable)
            mtime_ns: File mtime for fastpath metadata (not needed if data is Cacheable)
        """
        # Check if data is a Cacheable object
        if cache_key is None:
            cacheable = data
            self.set_with_fastpath(
                cacheable.cache_key,
                cacheable.data,
                cacheable.fastpath_key,
                cacheable.file_size,
                cacheable.mtime_ns,
            )
        else:
            # All params must be provided
            assert fastpath_key is not None
            assert file_size is not None
            assert mtime_ns is not None
            self.set_with_fastpath(cache_key, data, fastpath_key, file_size, mtime_ns)
    
    def clear(self) -> None:
        """Completely empties the cache directory."""
        self._cache.clear()
    
    def close(self) -> None:
        """Close the underlying diskcache (flushes to disk)."""
        self._cache.close()
