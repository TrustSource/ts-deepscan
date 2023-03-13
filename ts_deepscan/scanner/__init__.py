# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

from typing import List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict

from ts_python_client.commands.ScanCommand import Scan as TSScan


@dataclass
class Scan(TSScan):
    result: dict = field(default_factory=lambda: {})
    no_result: list = field(default_factory=lambda: [])
    options: dict = field(default_factory=lambda: {})
    stats: dict = field(default_factory=lambda: {})
    incompatible_licenses: list = field(default_factory=lambda: [])
    time: datetime = datetime.now()

    @property
    def licenses(self) -> List[str]:
        lics = set()

        def add_license(item):
            lic = item.get('license', None)
            if lic and 'key' in lic:
                lics.add(lic['key'])

        for res in self.result.values():
            add_license(res)

            for c in res.get('comments', []):
                lics.update(c.get('licenses', []))
                add_license(c)

        return list(lics)

    @property
    def root_licenses(self) -> [str]:
        lics = []
        for k, v in self.result.items():
            p = Path(k)
            if not p.parent or not p.parent.name:
                lic = v.get('license', None)
                if lic and 'score' in lic:
                    lics.append(lic['key'])
        return lics

    def compute_licenses_compatibility(self):
        import osadl_matrix
        lics = self.licenses
        while len(lics) > 1:
            l1 = lics.pop()
            for l2 in lics:
                if osadl_matrix.is_compatible(l1, l2) == osadl_matrix.OSADLCompatibility.NO:
                    self.incompatible_licenses.append([l1, l2])
                elif osadl_matrix.is_compatible(l2, l1) == osadl_matrix.OSADLCompatibility.NO:
                    self.incompatible_licenses.append([l2, l1])

    @staticmethod
    def from_dict(data: dict) -> 'Scan':
        return Scan(
            result = data.get('result', {}),
            no_result = data.get('no_result', []),
            options=data.get('options', {}),
            stats = data.get('stats', {}),
            incompatible_licenses=data.get('incompatible_licenses', [])
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d['time'] = str(d['time'])
        return d