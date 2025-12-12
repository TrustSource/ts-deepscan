# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import typing as t
import dataclasses_json
import osadl_matrix

from pathlib import Path
from copy import copy
from datetime import datetime

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


# Alias for a file scan input represented as:
#  ( absolute_file_path, optional_root_path )
FileScanInput = t.Tuple[Path, t.Optional[Path]]

# Alias for a file scan result represented as:
#  { analyser_category: analyser_result_data }
FileScanResult = t.Dict[str, t.Any]

# Alisas for scanner results represented as:
#  { relative_file_path: { analyser_category: analyser_result_data } }
ScanResults = t.Dict[str, FileScanResult]


@dataclass_json
@dataclass
class Scan:
    uid: t.Optional[str] = None
    url: t.Optional[str] = None
    result: dict = field(default_factory=lambda: {})
    no_result: list = field(default_factory=lambda: [])
    options: dict = field(default_factory=lambda: {})
    time: datetime = field(default_factory=lambda: datetime.now())
    stats: dict = field(default_factory=lambda: {})
    summary: dict = field(default_factory=lambda: {})


def _add_copyright_info(info: t.Union[t.Dict[str, t.Any], t.List[t.Dict[str, t.Any]]],
                        copyrights: t.Dict[str, t.Dict[str, t.List[str]]]):
    if isinstance(info, list):
        for i in info:
            _add_copyright_info(i, copyrights)
    else:
        for holder in info.get('holders', []):
            holder_data = copyrights.get(holder, {'dates': [], 'clauses': []})

            if (_date := info.get('date')) and (_date not in holder_data['dates']):
                holder_data['dates'].append(_date)

            if (_clause := info.get('clauses')) and (_clause not in holder_data['clauses']):
                holder_data['clauses'].append(_clause)

            copyrights[holder] = holder_data


def _add_license_info(info: dict, licenses: set, copyrights: dict):
    if lic_key := info.get('key'):
        licenses.add(lic_key)

    elif lic_keys := info.get('licenses'):
        licenses.update(set(lic_keys))

    if copyright_info := info.get('copyright'):
        _add_copyright_info(copyright_info, copyrights)


def compute_summary(scan: Scan):
    licenses: t.Set[str] = set()
    copyrights: t.Dict[str, t.Dict[str, t.List[str]]] = {}
    crypto_algorithms: t.Dict[str, t.List[str]] = {}

    for res in scan.result.values():
        if lic_info := res.get('license'):
            _add_license_info(lic_info, licenses, copyrights)

        # Collect licenses from commets iff. no license result was found
        elif comments := res.get('comments'):

            for c in comments:
                if c_lic_info := c.get('license'):
                    _add_license_info(c_lic_info, licenses, copyrights)
                else:
                    _add_license_info(c, licenses, copyrights)

        if crypto_algs := res.get('crypto'):
            for crypto_alg in crypto_algs:
                alg = crypto_alg['algorithm']
                codings = crypto_algorithms.get(alg, [])
                if (coding := crypto_alg.get('coding')) and (coding not in codings):
                    codings.append(coding)
                crypto_algorithms[alg] = codings

    licenses_list = list(licenses)

    scan.summary = {
        'licenses': licenses_list,
        'copyrights': copyrights,
        'crypto_algorithms': crypto_algorithms,
        'incompatible_licenses': compute_licenses_compatibility(licenses_list)
    }


def compute_licenses_compatibility(lics: t.List[str]) -> t.List[t.List[str]]:
    lics = copy(lics)
    result = []

    while len(lics) > 1:
        l1 = lics.pop()
        for l2 in lics:
            if osadl_matrix.is_compatible(l1, l2) == osadl_matrix.OSADLCompatibility.NO:
                result.append([l1, l2])
            elif osadl_matrix.is_compatible(l2, l1) == osadl_matrix.OSADLCompatibility.NO:
                result.append([l2, l1])

    return result
