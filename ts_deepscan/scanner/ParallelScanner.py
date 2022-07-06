# SPDX-FileCopyrightText: 2022 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import multiprocessing as mp

from typing import List, Tuple, Optional
from pathlib import Path

from .Scanner import Scanner
from ..analyser.FileAnalyser import FileAnalyser, AnalyserOptions


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
    def __init__(self, num_jobs: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._num_jobs = num_jobs if num_jobs > 0 else mp.cpu_count() - 1


    def _do_scan(self, files: List[Tuple[Path, Path]]) -> dict:
        results = {}
        
        tasksQueue = _ctx.Queue()
        resultsQueue = _ctx.Queue()

        workers = [Worker(tasksQueue, resultsQueue, self.analysers, self.options) for _ in range(self._num_jobs)]

        for w in workers:
            w.start()

        for f in files:
            tasksQueue.put(f)

        tasks_done = 0
        while tasks_done < len(files):
            relpath, result, error = resultsQueue.get()

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
            w.terminate()

        return results


class Worker(_ctx.Process):
    def __init__(self, tasksQueue: _ctx.Queue, resultsQueue: _ctx.Queue, analysers: List[FileAnalyser], options: AnalyserOptions):
        super().__init__()

        self._tasksQueue = tasksQueue
        self._resultsQueue = resultsQueue

        self._analysers = analysers
        self._options = options

    def run(self) -> None:
        while True:
            path, rootpath = self._tasksQueue.get()
            relpath = str(path.relative_to(rootpath))

            try:
                result = relpath, Scanner.scan_file(path, self._analysers, self._options), None

            except Exception as err:
                result = relpath, {}, err

            self._resultsQueue.put(result)

