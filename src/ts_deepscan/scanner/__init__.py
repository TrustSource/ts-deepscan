# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import dataclasses_json

from typing import List
from datetime import datetime
from pathlib import Path

from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json

dataclasses_json.cfg.global_config.encoders[datetime] = datetime.isoformat
dataclasses_json.cfg.global_config.decoders[datetime] = datetime.fromisoformat

@dataclass_json
@dataclass
class Scan:
    result: dict = field(default_factory=lambda: {})
    no_result: list = field(default_factory=lambda: [])
    options: dict = field(default_factory=lambda: {})
    stats: dict = field(default_factory=lambda: {})
    incompatible_licenses: list = field(default_factory=lambda: [])
    time: datetime = field(default_factory=lambda: datetime.now())

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