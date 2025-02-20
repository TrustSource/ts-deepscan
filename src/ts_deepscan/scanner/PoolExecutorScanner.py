import logging
import typing as t
import concurrent.futures as futures

from pathlib import Path

from .Scanner import Scanner
from ..analyser import FileAnalyser


class PoolExecutorScanner(Scanner):
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
        tasks = []

        def task_completed(_task: futures.Future[t.Tuple[str, dict, list]]):
            if _task.cancelled():
                self.finishedTasks += 1
                self._progress()
                return

            relpath, result, errors = _task.result()
            self._notifyCompletion(relpath, result, errors)

            if result:
                results.update({
                    relpath: result
                })

        executor = futures.ProcessPoolExecutor(max_workers=self._num_jobs if self._num_jobs > 0 else None)

        task_paths = {}

        for path, root in files:
            task = executor.submit(Scanner._scan_file, path, self.analysers, root)
            task.add_done_callback(task_completed)

            tasks.append(task)
            task_paths[task] = path

        while len(tasks) > 0:
            done, not_done = futures.wait(tasks, timeout=10, return_when=futures.FIRST_COMPLETED)

            if not_done == 0:
                break
            elif len(done) > 0:
                tasks = not_done
            else:
                tasks = list(not_done)
                task_to_cancel = tasks.pop()

                if tp := task_paths[task_to_cancel]:
                    print(f"Scan of {tp} has been cancelled")

                task_to_cancel.cancel()

        executor.shutdown(wait=False)
        print(f"Shutdown scanner...")

        return results
