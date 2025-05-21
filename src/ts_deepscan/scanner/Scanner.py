# SPDX-FileCopyrightText: 2022 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import os
import fnmatch
import functools
import shutil
import tempfile
import logging

from pathlib import Path
from shutil import ReadError
from typing import List, Tuple, Set, Optional, Callable
from gitignore_parser import parse_gitignore

from ..analyser import FileAnalyser


def _register_unpack_formats() -> Set[str]:
    """
    Registers unpack formats and returns all supported archive extensions.
    """

    def unpack_zip(filename, extract_dir):
        shutil.unpack_archive(filename, extract_dir, format='zip')

    if "wheel" not in shutil._UNPACK_FORMATS:  # noqa
        shutil.register_unpack_format('wheel', ['.whl'], unpack_zip)

    if "jar" not in shutil._UNPACK_FORMATS:  # noqa
        shutil.register_unpack_format('jar', ['.jar'], unpack_zip)

    return functools.reduce(lambda exts, fmt: exts.union(set(fmt[1])), shutil.get_unpack_formats(), set())


_archive_exts = _register_unpack_formats()

DEFAULT_FILE_MAX_SIZE = 1024 * int(os.environ.get('TS_DEPSCAN_FILE_MAX_SIZE', 1000))


class Scanner(object):
    def __init__(self,
                 analysers: [FileAnalyser],
                 file_max_size: int = DEFAULT_FILE_MAX_SIZE,
                 ignore_patterns: Optional[List[str]] = None,
                 ignore_hidden_files: bool = True,
                 default_gitignores: Optional[List[Path]] = None,
                 unpack_archives: bool = True):

        self.analysers = analysers
        self.file_max_size = file_max_size

        # File patterns
        self.ignore_patterns = [] if not ignore_patterns else ignore_patterns
        self.ignore_hidden_files = ignore_hidden_files
        self.default_gitignores = default_gitignores if default_gitignores else []

        # Archives
        self.unpack_archives = unpack_archives
        self.unpack_folder = None

        # Statistics
        self.totalTasks = 0
        self.finishedTasks = 0

        # Result callbacks

        # Callback accepting a relative path
        self.onPathIgnored: Optional[Callable[[str], None]] = None
        # Callback accepting relative path and results
        self.onFileScanCompleted: Optional[Callable[[str, dict, list], None]] = None
        # Callback accepting number of finished and total tasks
        self.onProgress: Optional[Callable[[int, int], None]] = None

        # Running
        self._cancelled = False

        # Cleanup files
        self._cleanup: List[Path] = []

    @staticmethod
    def _scan_file(path: Path, analysers: [FileAnalyser], root: Optional[Path]) -> Tuple[str, dict, List[str]]:
        result = {}
        errors = []

        relpath = str(path.relative_to(root) if root else path)

        for analyse in analysers:
            try:
                if analyse.accepts(path) and (res := analyse(path, root=root)):
                    result[analyse.category_name] = res
            except: # noqa
                msg = f'An error occured while scanning {relpath} using \'{analyse.category_name}\' analyser'
                logging.exception(msg)
                errors.append(msg)

        return relpath, result, errors

    @property
    def options(self) -> dict:
        opts = [a.options for a in self.analysers]
        return functools.reduce(lambda a, b: {**a, **b}, opts)

    @property
    def cancelled(self):
        return self._cancelled

    def run(self, paths: [Path]) -> dict:
        files: List[Tuple[Path, Optional[Path]]] = []

        if self.unpack_folder:
            unpack_path = self.unpack_folder
        else:
            temp_dir = tempfile.TemporaryDirectory()
            unpack_path = Path(temp_dir.name)

        def match(_path: Path, gitignores: List[Callable[[Path], bool]]):
            if self.ignore_hidden_files and _path.name.startswith('.'):
                return False

            if any(fnmatch.fnmatch(_path.name, pat) for pat in self.ignore_patterns):
                return False

            return all(not gitignore(_path) for gitignore in gitignores)

        def walk(_path: Path, _root: Optional[Path], gitignores: List[Callable[[Path], bool]]):
            if _path.is_file():
                ext = ''.join(_path.suffixes)
                if self.unpack_archives and (archive_ext := next((e for e in _archive_exts if ext.endswith(e)), None)):
                    extract_dir = unpack_path / _path.name[:-len(archive_ext)]
                    try:
                        shutil.unpack_archive(_path, extract_dir)
                        self._cleanup.append(extract_dir)

                        # Do not apply gitignores to extracted archives
                        yield from walk(extract_dir, unpack_path, [])
                    except (ValueError, ReadError):
                        pass
                else:
                    yield _path.resolve(), _root.resolve() if _root else None

            elif _path.is_dir():
                gitignore_file = _path / '.gitignore'
                if gitignore_file.exists():
                    gitignores = gitignores + [parse_gitignore(gitignore_file)]

                for p in _path.iterdir():
                    if not match(p, gitignores):
                        if self.onPathIgnored:
                            p = p.resolve()
                            p = p.relative_to(_root.resolve()) if _root else p
                            self.onPathIgnored(str(p))
                        continue
                    else:
                        yield from walk(p, _root, gitignores)

        try:
            for path in paths:
                if path.is_dir():
                    root = path if path.is_absolute() else (Path.cwd() / path).resolve()
                    default_gitignores = [parse_gitignore(p, base_dir=root) for p in self.default_gitignores]
                else:
                    root = path.parent
                    default_gitignores = []

                for p in walk(path, root, default_gitignores):
                    files.append(p)

            self.totalTasks = len(files)
            self.finishedTasks = 0

            if self.totalTasks == 0:
                return {}

            return self._do_scan(files)

        finally:
            self._do_cleanup()

    def cancel(self):
        self._cancelled = True

    def _do_scan(self, files: List[Tuple[Path, Path]]) -> dict:
        results = {}

        for path, root in files:
            relpath, result, errors = self.__class__._scan_file(path, self.analysers, root)

            self._notifyCompletion(relpath, result, errors)

            if result:
                results.update({
                    relpath: result
                })

        return results

    def _do_cleanup(self):
        for p in (p for p in self._cleanup if p.exists()):
            if p.is_file():
                p.unlink()
            else:
                shutil.rmtree(p)

    def _progress(self):
        self.finishedTasks += 1

        if self.onProgress:
            self.onProgress(self.finishedTasks, self.totalTasks)

    def _notifyCompletion(self, relpath: str, result: dict, errors: list):
        if self.onFileScanCompleted:
            self.onFileScanCompleted(relpath, result, errors)

        self._progress()
