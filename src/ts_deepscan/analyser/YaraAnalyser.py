# SPDX-FileCopyrightText: 2024 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import yara
import typing as t

from io import StringIO, BytesIO
from pathlib import Path

from . import FileAnalyser


class YaraAnalyser(FileAnalyser):
    category_name = 'yara'

    def __init__(self, rules_path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._rules_buf: t.Optional[BytesIO] = None

        if rules := YaraAnalyser._compile_rules(rules_path):
            self._rules_buf = BytesIO()
            rules.save(file=self._rules_buf)

        self._rules: t.Optional[yara.Rules] = None

    @staticmethod
    def _compile_rules(path: Path) -> t.Optional[yara.Rules]:
        try:
            return yara.compile(str(path.absolute()))
        except Exception as err:
            print(f'Could not load YARA rule: {err}')
            return None

    def _match(self, path: Path) -> bool:
        return True

    @property
    def options(self) -> dict:
        return {
            'includeYara': True
        }

    def analyse(self, path: Path, root: t.Optional[Path] = None) -> t.Optional[t.Any]:
        res = []

        if not self._rules and self._rules_buf:
            self._rules_buf.seek(0)
            try:
                self._rules = yara.load(file=self._rules_buf)
            finally:
                self._rules_buf.close()
                self._rules_buf = None

        if self._rules:
            try:
                for m in self._rules.match(str(path), timeout=self.timeout):
                    res.append({
                        f'{m.rule}': m.meta
                    })

            except TimeoutError:
                pass

        return res if res else None
