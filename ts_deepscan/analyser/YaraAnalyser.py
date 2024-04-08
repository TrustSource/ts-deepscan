# SPDX-FileCopyrightText: 2024 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import yara
import typing as t

from pathlib import Path

from . import FileAnalyser


class YaraAnalyser(FileAnalyser):
    def __init__(self, rules_path: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._rules = YaraAnalyser._compile_rules(rules_path)
        print(f'{len(self._rules)} YARA rules loaded')

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

    def analyse(self, path: Path) -> t.Optional[t.Any]:
        res = []

        for r in self._rules:
            try:
                for m in r.match(str(path), timeout=60):
                    res.append({
                        f'{m.rule}': m.meta
                    })
            except TimeoutError:
                pass

        if res:
            return {
                'yara': res
            }

        return None
