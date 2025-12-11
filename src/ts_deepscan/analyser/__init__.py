# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import typing as t

from pathlib import Path
from abc import ABC, abstractmethod


class FileAnalyser(ABC):
    # Analysis timeout in seconds
    DEFAULT_TIMEOUT = 60

    # Max file size in bytes
    MAX_FILE_SIZE = 10 ** 6

    def __init__(self, timeout=DEFAULT_TIMEOUT, max_file_size=MAX_FILE_SIZE):
        self.timeout = timeout
        self.max_file_size = max_file_size

    @property
    @abstractmethod
    def category(self) -> str:
        raise NotImplementedError()

    def __call__(self, path: Path, root: t.Optional[Path] = None):
        return self.analyse(path, root) if self.accepts(path) else None

    @abstractmethod
    def _match(self, path: Path) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def analyse(self, path: Path, root: t.Optional[Path] = None) -> t.Optional[t.Any]:
        raise NotImplementedError()

    @property
    def options(self) -> dict:
        return {}

    def accepts(self, path: Path) -> bool:
        if path.is_file() and self._match(path):
            return True
        else:
            return False


class TextFileAnalyser(FileAnalyser, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _match(self, path: Path) -> bool:
        if not path.exists():
            return False

        if path.stat().st_size > self.max_file_size:
            return False

        # Check for common binary file signatures
        try:
            with path.open('rb') as fp:
                header = fp.read(8)
                                
                if header.startswith((b'\x89PNG', b'\xff\xd8\xff', b'GIF8', b'\x00\x00\x00', b'PK\x03\x04')):
                    return False
                
                # Check for null bytes in header (often found in binary files)                
                if b'\x00' in header:
                    return False
                
        except (IOError, OSError):
            return False

        # Try to read as UTF-8 text with strict error handling
        try:
            with path.open('r', encoding='utf-8', errors='strict') as fp:
                # Read first chunk to validate it's text
                fp.read(1024)
                return True
            
        except (UnicodeDecodeError, IOError, OSError):
            return False


class SourceCodeAnalyser(TextFileAnalyser, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _match(self, path: Path) -> bool:
        from ..commentparser.language import classify, Lang

        return classify(path) != Lang.Unknown and super()._match(path)