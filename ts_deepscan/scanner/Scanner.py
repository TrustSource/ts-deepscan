# SPDX-FileCopyrightText: 2022 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import os
import logging
import fnmatch

from .. import config

from typing import List, Tuple, Optional, Callable
from pathlib import Path

from ..analyser.FileAnalyser import *
from .ScanException import *


class Scanner(object):
    __version = "0.3"

    def __init__(self, paths: [Path], analysers: [FileAnalyser], options: AnalyserOptions=None, *args, **kwargs):
        self.__paths = paths

        self.analysers = analysers
        self.options = options

        # Statistics
        self.totalTasks = 0
        self.finishedTasks = 0

        # Result callbacks

        # Callback accepting relative path and results
        self.onFileScanSuccess: Optional[Callable[[str, dict], None]] = None
        # Callback accepting a relative path and an exception
        self.onFileScanError: Optional[Callable[[str, Exception], None]] = None
        # Callback accepting number of finished and total tasks
        self.onProgress: Optional[Callable[[int, int], None]] = None


    @staticmethod
    def scan_file(path: Path, analysers: [FileAnalyser], options: AnalyserOptions) -> dict:
        result = {}

        if path.is_file() and path.stat().st_size > options.fileSizeLimit:
            return {}

        analysers = [a for a in analysers if a.accepts(path, options)]

        for analyse in analysers:
            res = analyse(path, options)
            if res:
                result[analyse.category_name] = res

        return result


    def run(self):
        logging.info('Scanner version: {}'.format(Scanner.__version))

        files: List[Tuple[Path, Path]]  = []

        for p in self.__paths:
            if p.is_file():
                files.append((p, p.parent))

            elif p.is_dir():
                for root, ds, fs in os.walk(str(p)):
                    ds[:] = [d for d in ds if not d.startswith('.')]
                    for f in fs:
                        if f.startswith('.'):
                            continue

                        if not self.options.filePatterns or any(fnmatch.fnmatch(f, pat) for pat in self.options.filePatterns):
                            files.append((Path(os.path.join(root, f)), p))

        self.totalTasks = len(files)
        self._notifyProgress()

        try:
            return self._do_scan(files)

        except ScanException as err:
            logging.error(err)
            raise

        except:
            logging.exception('Internal error')
            raise InternalScanException


    def _do_scan(self, files: List[Tuple[Path, Path]]) -> dict:
        results = {}

        for path, root in files:
            relpath = str(path.relative_to(root))
            try:
                result = Scanner.scan_file(path, self.analysers, self.options)
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