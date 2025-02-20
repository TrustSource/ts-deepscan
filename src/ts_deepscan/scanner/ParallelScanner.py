# SPDX-FileCopyrightText: 2022 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import logging
import queue
import typing as t
import multiprocessing as mp

from pathlib import Path

from .Scanner import Scanner
from ..analyser import FileAnalyser


def get_context() -> mp.context.DefaultContext:
    """
    Return multiprocessing context based on the OS        
    """
    if sys.platform != "win32":
        return mp.get_context('fork')
    else:
        return mp.get_context('spawn')


_ctx = get_context()


class ParallelScanner(Scanner):
    Queue = _ctx.Queue
    Process = _ctx.Process

    results_wait_time = 60

    __enable_logging = True

    def __init_subclass__(cls, enable_logging=True, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__enable_logging = enable_logging

    def __init__(self, num_jobs: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_jobs = num_jobs if num_jobs > 0 else mp.cpu_count() - 1

    def _log(self, msg, lvl=logging.INFO):
        if self.__class__.__enable_logging:
            logging.log(lvl, msg)

    def _do_scan(self, files: t.List[t.Tuple[Path, Path]]) -> dict:
        results = {}

        tasks = _ctx.Queue()
        task_results = _ctx.Queue()

        workers = self._create_workers(tasks, task_results, min(self._num_jobs, len(files)))

        self._log(f'Num of workers: {self._num_jobs}')

        for w in workers:
            w.start()

        for f in files:
            tasks.put(f)

        for _ in range(self._num_jobs):
            tasks.put((None, None))

        tasks_done = 0
        while not self._cancelled and tasks_done < len(files):
            try:
                relpath, result, errors = task_results.get(timeout=ParallelScanner.results_wait_time)

            except queue.Empty:
                self._log(f'No results received within {ParallelScanner.results_wait_time} seconds. Checking status...')

                w_live = []
                w_failed = []

                for w in workers:
                    if w.exitcode is None or w.exitcode == 0:
                        w_live.append(w)
                    else:
                        w_failed.append(w)

                if len(w_failed) > 0:
                    for w in w_failed:
                        self._log(f'Worker exited with code {w.exitcode}', logging.ERROR)

                    self._log('Restarting failed workers')

                    w_restarted = self._create_workers(tasks, task_results, len(w_failed))
                    for w in w_restarted:
                        w.start()

                    workers = w_live + w_restarted
                    continue

                elif any(w.is_alive() for w in workers):
                    continue

                else:
                    self._log(f'All workers exited')
                    break

            self._notifyCompletion(relpath, result, errors)

            if result:
                results.update({
                    relpath: result
                })

            tasks_done += 1

        for w in workers:
            if self._cancelled:
                w.terminate()
            w.join()

        return results

    def _create_workers(self, tasks: _ctx.Queue, results: _ctx.Queue, num: int = 1) -> 'Worker':
        return [ParallelScanner.Worker(tasks, results, self.analysers) for _ in range(num)]

    class Worker(_ctx.Process):
        def __init__(self, tasks: _ctx.Queue, results: _ctx.Queue, analysers: t.List[FileAnalyser]):
            super().__init__()

            self._tasksQueue = tasks
            self._resultsQueue = results

            self._analysers = analysers

        def run(self) -> None:
            while True:
                path, root = self._tasksQueue.get()

                if not path:
                    break

                result = Scanner._scan_file(path, self._analysers, root)
                self._resultsQueue.put(result)
