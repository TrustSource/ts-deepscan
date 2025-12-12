
import typing as t

from abc import ABC, abstractmethod

from ...caching import ResultsCache, CacheableResult

from .. import ScanResults


class PostProcessor(ABC):
    @abstractmethod
    def apply(self, results: ScanResults) -> ScanResults:
        raise NotImplementedError()
        
    
class CompositePostProcessor(PostProcessor):
    def __init__(self, processors: t.List[PostProcessor]):
        self.__processors = processors

    def apply(self, results: ScanResults) -> ScanResults:
        results = results
        
        for processor in self.__processors:
            results = processor.apply(results)

        return results
    

class CachingPostProcessor(PostProcessor):
    from ...caching import ResultsCache, CacheableResult

    def __init__(self, cache: ResultsCache, processor: t.Optional[PostProcessor] = None):
        self._cache = cache
        self._processor = processor        
        
    def apply(self, results: ScanResults) -> ScanResults:
        if self._processor:
            results = self._processor.apply(results)

        for file_results in results.values():
            for cat, res in file_results.items():
                if isinstance(res, CacheableResult):
                    self._cache.store(res)
                    file_results[cat] = res.data

        return results