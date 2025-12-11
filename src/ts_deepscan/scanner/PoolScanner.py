import logging
import typing as t

import ts_deepscan.util as util

from pathlib import Path
from concurrent import futures
from threading import Thread, RLock
from queue import Queue

from .pool import Pool
from .Scanner import Scanner
from ..analyser import FileAnalyser


class PoolScanner(Scanner):

    def __init__(self, num_jobs: int, task_timeout=FileAnalyser.DEFAULT_TIMEOUT, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_jobs = num_jobs
        self._task_timeout = task_timeout

        self._pool: t.Optional[Pool] = None
        self._pool_lock: RLock = RLock()

    def _get_pool(self):
        self._pool_lock.acquire()
        try:
            if not self._pool:
                self._pool = Pool.create(self._num_jobs)
                util.info(f'Created a new pool with {self._pool.num_processes} workers')
        finally:
            self._pool_lock.release()

        return self._pool

    def _do_scan(self, files: t.List[t.Tuple[Path, t.Optional[Path]]]) -> dict:
        results = {}
        results_queue: Queue = Queue()

        def process_results():
            while True:
                res = results_queue.get()

                if res is None:
                    break

                relpath, result, errors = res

                error_msgs = []
                for cat, err in errors.items():
                    util.error(err)
                    error_msgs.append(f'An error occured while scanning {relpath} using \'{cat}\' analyser')

                self._notifyCompletion(relpath, result, error_msgs)

                if result:
                    results.update({
                        relpath: result
                    })

        def report_results(relpath: str, result: dict, errors: t.Dict[str, str]):
            results_queue.put((relpath, result, errors))

        pool = futures.ThreadPoolExecutor()

        tasks = []
        for path, root in files:
            task = pool.submit(self._get_scan_file_fn(), path, root, report_results)
            tasks.append(task)

        results_processing = Thread(target=process_results)
        results_processing.start()

        logging.debug("Waiting for tasks to complete...")
        futures.wait(tasks, return_when=futures.ALL_COMPLETED)
        logging.debug("All tasks completed.")

        results_queue.put(None)
        results_processing.join()
        logging.debug("Results processing thread has finished.")

        return results

    def _get_scan_file_fn(self) -> t.Callable[[Path,
                                               t.Optional[Path],
                                               t.Callable[[str, dict, t.Dict[str, str]], None]], None]:

        def _scan_file(path: Path,
                       root: t.Optional[Path],
                       report_results: t.Callable[[str, dict, t.Dict[str, str]], None]):

            PoolScanner._scan_file_parallel(path,
                                            root,
                                            self.analysers,
                                            self._task_timeout,
                                            report_results,
                                            self._get_pool())

        return _scan_file

    @staticmethod
    def _scan_file_parallel(path: Path,
                            root: t.Optional[Path],
                            analysers: t.List[FileAnalyser],
                            timeout: int,
                            report_results: t.Callable[[str, dict, t.Dict[str, str]], None],
                            pool: Pool):
        result = {}
        errors = {}

        relpath = str(path.relative_to(root) if root else path)

        def task_completed(_cat):
            def _callback(_res):
                if _res:
                    result[_cat] = _res
            return _callback

        def task_failed(_cat):
            def _callback(_err):
                errors[_cat] = _err
            return _callback

        tasks = [pool.apply_async(
            _apply_analysis, (analyser, path, root),
            callback=task_completed(analyser.category),
            error_callback=task_failed(analyser.category))
                for analyser in analysers if analyser.accepts(path)]

        for _task in tasks:
            _task.wait(timeout=timeout)
            if not _task.ready():
                if worker := pool.find_worker(_task):
                    worker.terminate()

        report_results(relpath, result, errors)


def _apply_analysis(analyser: FileAnalyser, path: Path, root: t.Optional[Path]) -> t.Optional[t.Any]:
    return analyser(path, root=root)
