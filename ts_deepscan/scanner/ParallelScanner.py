# SPDX-FileCopyrightText: 2022 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import logging
import queue
import multiprocessing as mp

from typing import List, Tuple
from pathlib import Path

from .Scanner import Scanner
from ..analyser import FileAnalyser

def get_context() -> mp.context.BaseContext:
    """
    Return multiprocessing context based on the OS        
    """
    if sys.platform != "win32":
        return mp.get_context('fork')
    else:
        return mp.get_context('spawn')

_ctx = get_context()


class ParallelScanner(Scanner):
    enable_logging = False
    results_wait_time = 60

    def __init__(self, num_jobs: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_jobs = num_jobs if num_jobs > 0 else mp.cpu_count() - 1

        if ParallelScanner.enable_logging:
            logging.info(f'Number of jobs: {self._num_jobs}')

    def _do_scan(self, files: List[Tuple[Path, Path]]) -> dict:
        results = {}
        
        tasksQueue = _ctx.Queue()
        resultsQueue = _ctx.Queue()

        workers = self._create_workers(tasksQueue, resultsQueue, self._num_jobs)

        for w in workers:
            w.start()

        for f in files:
            tasksQueue.put(f)

        for _ in range(self._num_jobs):
            tasksQueue.put((None, None))

        tasks_done = 0
        while tasks_done < len(files):
            try:
                relpath, result, error = resultsQueue.get(timeout=ParallelScanner.results_wait_time)
            except queue.Empty:
                if ParallelScanner.enable_logging:
                    logging.info(f'No results received within {ParallelScanner.results_wait_time} seconds.')

                w_live = []
                w_failed = []

                for w in workers:
                    if w.exitcode is None or w.exitcode == 0:
                        w_live.append(w)
                    else:
                        w_failed.append(w)

                if len(w_failed) > 0:
                    if ParallelScanner.enable_logging:
                        for w in w_failed:
                            logging.error(f'Worker exited with code {w.exitcode}.')
                        logging.info('Restarting failed workers')

                    w_restarted = self._create_workers(tasksQueue, resultsQueue, len(w_failed))
                    for w in w_restarted:
                        w.start()

                    workers = w_live + w_restarted
                    continue

                elif any(w.is_alive() for w in workers):
                    continue

                else:
                    if ParallelScanner.enable_logging:
                        logging.info(f'All workers exited.')
                    break

            if error:
                self._notifyError(relpath, error)
            else:
                self._notifySuccess(relpath, result)

            if result:
                results.update({
                    relpath: result
                })

            tasks_done += 1

        for w in workers:
            w.join()

        return results


    def _create_workers(self, qTasks: _ctx.Queue, qResults: _ctx.Queue, num: int = 1) -> 'Worker':
        return [ParallelScanner.Worker(qTasks, qResults, self.analysers) for _ in range(num)]


    class Worker(_ctx.Process):
        def __init__(self, tasksQueue: _ctx.Queue, resultsQueue: _ctx.Queue, analysers: List[FileAnalyser]):
            super().__init__()

            self._tasksQueue = tasksQueue
            self._resultsQueue = resultsQueue

            self._analysers = analysers

        def run(self) -> None:
            while True:
                try:
                    path, root = self._tasksQueue.get()
                    if not path:
                        break

                    relpath = str(path.relative_to(root) if root else path)
                    result = relpath, Scanner._scan_file(path, self._analysers), None

                except Exception as err:
                    result = relpath, {}, err

                self._resultsQueue.put(result)




