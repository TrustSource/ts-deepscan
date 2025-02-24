# SPDX-FileCopyrightText: 2024 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import yara
import typing as t

from pathlib import Path

from . import FileAnalyser


class YaraAnalyser(FileAnalyser):
    category_name = 'yara'

    __rules: t.List[yara.Rules] = []

    def __init__(self, rules_path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rules_path = rules_path

    @staticmethod
    def _compile_rules(path: Path) -> t.List[yara.Rules]:
        rules = []
        if path.is_file():
            try:
                rules.append(yara.compile(str(path.absolute())))
            except Exception as err:
                print(f'Could not load YARA rule: {err}')

        elif path.is_dir():
            for yar in path.glob('*.yar'):
                try:
                    rules.append(yara.compile(str(yar)))
                except Exception as err:
                    print(f'Could not load YARA rule: {err}')

        return rules

    def _match(self, path: Path) -> bool:
        return True

    @property
    def options(self) -> dict:
        return {
            'includeYara': True
        }

    def analyse(self, path: Path, root: t.Optional[Path] = None) -> t.Optional[t.Any]:
        res = []

        if not YaraAnalyser.__rules:
            YaraAnalyser.__rules = YaraAnalyser._compile_rules(self._rules_path)

        for rule in YaraAnalyser.__rules:
            try:
                for m in rule.match(str(path), timeout=self.timeout):
                    res.append({
                        f'{m.rule}': m.meta
                    })

            except TimeoutError:
                pass

        return res if res else None
