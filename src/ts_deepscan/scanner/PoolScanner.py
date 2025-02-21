import logging
import threading
import typing as t

from pathlib import Path
from concurrent import futures
from threading import Thread, Lock
from queue import Queue

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
        results_queue = Queue()

        def process_results():
            while True:
                res = results_queue.get()

                if res is None:
                    break

                relpath, result, errors = res

                self._notifyCompletion(relpath, result, errors)

                if result:
                    results.update({
                        relpath: result
                    })

        lock = Lock()
        pool = futures.ThreadPoolExecutor()

        tasks = []
        for path, root in files:
            task = pool.submit(PoolScanner._scan_file_parallel,
                               path, root, self.analysers, self._task_timeout, results_queue, lock)
            tasks.append(task)

        results_processing = Thread(target=process_results)
        results_processing.start()

        futures.wait(tasks, return_when=futures.ALL_COMPLETED)
        results_queue.put(None)

        return results

    @staticmethod
    def _scan_file_parallel(path: Path,
                            root: t.Optional[Path],
                            analysers: [FileAnalyser],
                            timeout: int,
                            results: Queue,
                            lock: Lock):
        result = {}
        errors = []

        relpath = str(path.relative_to(root) if root else path)

        def task_completed(_cat):
            def _callback(_res):
                if _res:
                    result[_cat] = _res
            return _callback

        def task_failed(_cat):
            def _callback(_err):
                msg = f'An error occured while scanning {relpath} using \'{_cat}\' analyser'
                logging.exception(msg)
                errors.append(msg)
            return _callback

        with lock:
            pool = get_pool()
            tasks = [pool.apply_async(
                _apply_analysis, (analyser, path, root),
                callback=task_completed(analyser.category_name),
                error_callback=task_failed(analyser.category_name))
                    for analyser in analysers if analyser.accepts(path)]

        for _task in tasks:
            _task.wait(timeout=timeout)
            if not _task.ready():
                with lock:
                    if worker := pool.find_worker(_task):
                        worker.terminate()

        results.put((relpath, result, errors))


def _apply_analysis(analyser: FileAnalyser, path: Path, root: t.Optional[Path]) -> dict:
    return analyser(path, root=root)
