# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import os
from dataclasses import dataclass, field, asdict

def _match_prop(opts, prop, val):
    return prop in opts and opts[prop] == val

_DEFAULT_FILE_MAX_SIZE = 1024 * int(os.environ.get('TS_DEPSCAN_FILE_MAX_SIZE', 1000))

@dataclass
class AnalyserOptions:
    includeCopyright: bool = False
    filterFiles: bool = True
    filePatterns: list = field(default_factory=lambda: [])
    fileSizeLimit: int = _DEFAULT_FILE_MAX_SIZE

    def match(self, opts: dict):
        return opts and \
               _match_prop(opts, 'includeCopyright', self.includeCopyright) and \
               _match_prop(opts, 'filterFiles', self.filterFiles)

    @staticmethod
    def from_dict(data: dict) -> 'AnalyserOptions':
        return AnalyserOptions(
            includeCopyright=data.get('includeCopyright', False),
            filterFiles=data.get('filterFiles', True),
            filePatterns=data.get('filePatterns', []),
            fileSizeLimit = data.get('fileSizeLimit', _DEFAULT_FILE_MAX_SIZE)
        )

    def to_dict(self) -> dict:
        return asdict(self)


class FileAnalyser(object):
    def __call__(self, path, opts=AnalyserOptions()):
        return self.analyse(path, opts) if self.accepts(path, opts) else None

    def accepts(self, path, opts=AnalyserOptions()):
        if path.is_file() and self.match(path, opts):
            return True
        else:
            return False

    def match(self, path, opts):
        raise NotImplementedError()

    def analyse(self, path, opts):
        raise NotImplementedError()
