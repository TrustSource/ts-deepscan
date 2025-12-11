import time
import json
import typing as t
import xxhash

from pathlib import Path
from diskcache import Cache

from . import FileAnalyser

# Sentinel object to distinguish "not in cache" from "cached None"
_CACHE_MISS = object()


def _fast_file_hash(path: Path, blocksize: int = 1 << 20) -> str:
    h = xxhash.xxh64()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(blocksize)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _options_fingerprint(opts: t.Optional[t.Mapping[str, t.Any]]) -> t.Optional[str]:
    if not opts:
        return None
        
    payload = json.dumps(opts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    
    h = xxhash.xxh64()
    h.update(payload)
    
    return h.hexdigest()


_default_cache_location = Path('~/.ts-scan/caches/ds').expanduser()

class CachedAnalyzer(FileAnalyser):
    def __init__(
        self,
        analyser: FileAnalyser,
        cache_dir: Path = _default_cache_location,
        version: str = "1",
        use_fastpath: bool = True,
        stat_first: bool = True,  
        size_limit: int = 2 * 1024 * 1024 * 1024,  # 2 GiB
        eviction_policy: str = "least-recently-stored",
        shards: int = 8,      
    ) -> None:        
        
        self.analyser = analyser
        self.cache_dir = str(cache_dir)
        self.version = str(version)        
        self.use_fastpath = use_fastpath
        self.stat_first = stat_first

        self.cache = Cache(
            directory=cache_dir,
            size_limit=size_limit,
            eviction_policy=eviction_policy,
            shards=shards,
        )

    @property    
    def category(self) -> str:
        return self.analyser.category
    
    @property
    def options(self) -> dict:
        return self.analyser.options

    def _match(self, path: Path) -> bool:
        return self.analyser._match(path)

    
    def analyse(self, path: Path, root: t.Optional[Path] = None) -> t.Optional[t.Any]:        
        if not path.is_file():
            raise FileNotFoundError(path)

        st = path.stat() if self.stat_first else None
        opt_fp = _options_fingerprint(self.options)

        key_fastpath = self._key_fastpath(path, opt_fp)

        if self.use_fastpath and st is not None:
            fp = self.cache.get(key_fastpath)
            if fp and isinstance(fp, dict):
                if fp.get("size") == st.st_size and fp.get("mtime_ns") == st.st_mtime_ns:
                    cached = self.cache.get(fp.get("cache_key"), default=_CACHE_MISS)
                    if cached is not _CACHE_MISS:
                        return cached

        # Authoritative content hash
        h = _fast_file_hash(path)
        size = st.st_size if st is not None else path.stat().st_size
        key = self._key(h, size, opt_fp)

        cached = self.cache.get(key, default=_CACHE_MISS)
        if cached is not _CACHE_MISS:
            # refresh fastpath metadata
            if self.use_fastpath:
                st2 = path.stat()
                self.cache.set(
                    key_fastpath,
                    {"cache_key": key, "size": st2.st_size, "mtime_ns": st2.st_mtime_ns},
                    expire=None,
                )
            return cached

        # Cache miss → compute
        result = self.analyser.analyse(path, root)

        # Store result
        self.cache.set(key, result, expire=None)

        # Store/update fastpath metadata
        if self.use_fastpath:
            st3 = path.stat()
            self.cache.set(
                key_fastpath,
                {"cache_key": key, "size": st3.st_size, "mtime_ns": st3.st_mtime_ns},
                expire=None,
            )

        return result


    def _key(self, file_hash: str, file_size: int, opt_fp: t.Optional[str]) -> str:
        base = f"{self.category}:v{self.version}:{file_hash}:{file_size}"
        return f"{base}:opts:{opt_fp}" if opt_fp else base

    def _key_fastpath(self, path: Path, opt_fp: t.Optional[str]) -> str:
        return f"fast:{self.category}:v{self.version}:{path.resolve()}:{opt_fp or 'noopts'}"
    
    def clear(self) -> None:
        """Completely empties the cache directory."""
        self.cache.clear()

    def close(self) -> None:
        """Close the underlying diskcache (flushes to disk)."""
        self.cache.close()
