import logging
import typing as t

from pathlib import Path
from concurrent import futures
from threading import Thread
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

        def report_results(relpath: str, result: dict, errors: t.List[str]):
            results_queue.put((relpath, result, errors))

        pool = futures.ThreadPoolExecutor()

        tasks = []
        for path, root in files:
            task = pool.submit(self._get_scan_file_fn(), path, root, report_results)
            tasks.append(task)

        results_processing = Thread(target=process_results)
        results_processing.start()

        futures.wait(tasks, return_when=futures.ALL_COMPLETED)

        #for task in tasks:
            #print(task)

        results_queue.put(None)

        return results

    def _get_scan_file_fn(self) -> t.Callable[[Path, t.Optional[Path], t.Callable[[str, dict, t.List[str]], None]], None]:
        def _scan_file(path: Path, root: t.Optional[Path], report_results: t.Callable[[str, dict, t.List[str]], None]):
            PoolScanner._scan_file_parallel(path, root, self.analysers, self._task_timeout, report_results)

        return _scan_file

    @staticmethod
    def _scan_file_parallel(path: Path,
                            root: t.Optional[Path],
                            analysers: [FileAnalyser],
                            timeout: int,
                            report_results: t.Callable[[str, dict, t.List[str]], None]):
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

        pool = get_pool()
        tasks = [pool.apply_async(
            _apply_analysis, (analyser, path, root),
            callback=task_completed(analyser.category_name),
            error_callback=task_failed(analyser.category_name))
                for analyser in analysers if analyser.accepts(path)]

        for _task in tasks:
            _task.wait(timeout=timeout)
            if not _task.ready():
                if worker := pool.find_worker(_task):
                    worker.terminate()

        report_results(relpath, result, errors)


def _apply_analysis(analyser: FileAnalyser, path: Path, root: t.Optional[Path]) -> dict:
    return analyser(path, root=root)
