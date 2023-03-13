# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Optional
from abc import ABC, abstractmethod
from pathlib import Path

class FileAnalyser(ABC):
    def __call__(self, path: Path):
        return self.analyse(path) if self.accepts(path) else None

    @abstractmethod
    def _match(self, path: Path) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def analyse(self, path: Path) -> Optional[Any]:
        raise NotImplementedError()

    @property
    def options(self) -> dict:
        return {}

    def accepts(self, path: Path) -> bool:
        if path.is_file() and self._match(path):
            return True
        else:
            return False