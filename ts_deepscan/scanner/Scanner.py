# SPDX-FileCopyrightText: 2022 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import os
import fnmatch
import functools

from pathlib import Path
from typing import List, Tuple, Optional, Callable

from ..analyser import FileAnalyser

DEFAULT_FILE_MAX_SIZE = 1024 * int(os.environ.get('TS_DEPSCAN_FILE_MAX_SIZE', 1000))

class Scanner(object):
    def __init__(self,
                 analysers: [FileAnalyser],
                 file_max_size: int = DEFAULT_FILE_MAX_SIZE,
                 ignore_patterns: List[str] = None,
                 ignore_hidden_files: bool = True):

        self.analysers = analysers
        self.file_max_size = file_max_size

        # File patterns
        self.ignore_patterns = [] if not ignore_patterns else ignore_patterns
        self.ignore_hidden_files = ignore_hidden_files

        # Statistics
        self.totalTasks = 0
        self.finishedTasks = 0

        ## Result callbacks

        # Callback accepting relative path and results
        self.onFileScanSuccess: Optional[Callable[[str, dict], None]] = None
        # Callback accepting a relative path and an exception
        self.onFileScanError: Optional[Callable[[str, Exception], None]] = None
        # Callback accepting number of finished and total tasks
        self.onProgress: Optional[Callable[[int, int], None]] = None


    @staticmethod
    def _scan_file(path: Path, analysers: [FileAnalyser]) -> dict:
        result = {}

        for analyse in analysers:
            if analyse.accepts(path) and (res := analyse(path)):
                result[analyse.category_name] = res

        return result

    @property
    def options(self) -> dict:
        opts = [a.options for a in self.analysers]
        return functools.reduce(lambda a, b: {**a, **b}, opts)

    def run(self, paths: [Path]):
        files: List[Tuple[Path, Optional[Path]]]  = []

        def match(name: str):
            if self.ignore_hidden_files and name.startswith('.'):
                return False

            if any(fnmatch.fnmatch(name, pat) for pat in self.ignore_patterns):
                return False

            return True

        def walk(path: Path, root: Optional[Path]):
            if path.is_file():
                yield path.resolve(), root
            elif path.is_dir():
                for p in path.iterdir():
                    if not match(p.name):
                        continue
                    else:
                        yield from walk(p, root)

        for path in paths:
            if path.is_dir():
                root = path if path.is_absolute() else Path.cwd() / path
            else:
                root = None #Path.cwd()

            for p in walk(path, root):
                files.append(p)

        self.totalTasks = len(files)
        self.finishedTasks = 0

        if self.totalTasks == 0:
            return {}

        self._notifyProgress()
        return self._do_scan(files)


    def _do_scan(self, files: List[Tuple[Path, Path]]) -> dict:
        results = {}

        for path, root in files:
            relpath = str(path.relative_to(root) if root else path)
            try:
                result = Scanner._scan_file(path, self.analysers)
                self._notifySuccess(relpath, result)

                if result:
                    results.update({
                        relpath: result
                    })

            except Exception as err:
                self._notifyError(relpath, err)

        return results


    def _notifySuccess(self, relpath: str, result: dict):
        if self.onFileScanSuccess:
            self.onFileScanSuccess(relpath, result)

        self._progress()

    def _notifyError(self, relpath: str, error: Exception):
        if self.onFileScanError:
            self.onFileScanError(relpath, error)

        self._progress()

    def _progress(self):
        self.finishedTasks += 1
        self._notifyProgress()

    def _notifyProgress(self):
        if self.onProgress:
            self.onProgress(self.finishedTasks, self.totalTasks)