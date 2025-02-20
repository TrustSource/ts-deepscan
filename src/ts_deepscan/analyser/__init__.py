# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import typing as t

from pathlib import Path
from abc import ABC, abstractmethod


class FileAnalyser(ABC):
    DEFAULT_TIMEOUT = 60

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout

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
    def _match(self, path: Path) -> bool:
        try:
            with path.open('r', encoding='utf-8') as _:
                return True
        except UnicodeDecodeError:
            return False
