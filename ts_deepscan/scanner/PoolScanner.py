import logging
import typing as t

from pathlib import Path

from .pool import get_pool
from .Scanner import Scanner
from ..analyser import FileAnalyser


class PoolScanner(Scanner):
    def __init_subclass__(cls, enable_logging=True, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__enable_logging = enable_logging

    def __init__(self, num_jobs: int, task_timeout=FileAnalyser.DEFAULT_TIMEOUT, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_jobs = num_jobs
        self._task_timeout = task_timeout

    def _log(self, msg, lvl=logging.INFO):
        if self.__class__.__enable_logging:
            logging.log(lvl, msg)

    def _do_scan(self, files: t.List[t.Tuple[Path, Path]]) -> dict:
        results = {}

        def task_completed(res):
            relpath, result, errors = res
            self._notifyCompletion(relpath, result, errors)
            if result:
                results.update({
                    relpath: result
                })

        pool = get_pool()
        tasks = [pool.apply_async(
            Scanner._scan_file, (path, self.analysers, root),
            callback=task_completed) for path, root in files]

        tasks_not_ready = []

        for _task in tasks:
            _task.wait(timeout=self._task_timeout)
            if not _task.ready():
                tasks_not_ready.append(_task)
                if worker := pool.find_worker(_task):
                    worker.terminate()

#        pool.terminate()
#        pool.join()

        for _task in tasks_not_ready:
            if not _task.ready():
                self._progress()

        return results

