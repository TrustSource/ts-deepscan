import typing as t
import concurrent.futures as futures

import ts_deepscan.util as util


from . import FileScanInput, FileScanResult, ScanResults

from .Scanner import Scanner
from ..analyser import FileAnalyser


class PoolExecutorScanner(Scanner):

    def __init__(self, num_jobs: int, task_timeout=FileAnalyser.DEFAULT_TIMEOUT, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_jobs = num_jobs
        self._task_timeout = task_timeout

    def _do_scan(self, files: t.List[FileScanInput]) -> ScanResults:
        results = {}
        tasks = []

        def task_completed(_task: futures.Future[FileScanResult]):
            if _task.cancelled():
                self.finishedTasks += 1
                self._progress()
                return

            relpath, result, errors = _task.result()
            self._notifyCompletion(relpath, result, errors)

            if result:
                results[relpath] = result                

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
                    util.info(f"Scan of {tp} has been cancelled")

                task_to_cancel.cancel()

        executor.shutdown(wait=False)
        util.info(f"Shutdown scanner...")

        return results
