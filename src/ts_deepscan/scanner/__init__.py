# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import os
import typing as t
import osadl_matrix

from pathlib import Path
from copy import copy
from datetime import datetime

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from ..analyser import AnalysisResult

# Alias for a file scan input represented as:
#  ( absolute_file_path, optional_root_path )
FileScanInput = t.Tuple[Path, t.Optional[Path]]

# Alias for a file scan result represented as:
#  ( relative_file_path, [ analyser_results ], [ error_messages ] )
FileScanResult = t.Tuple[str, t.List[AnalysisResult], t.List[str]]

# Alisas for scanner results represented as:
#  { relative_file_path: [ analyser_results ] }
ScanResults = t.Dict[str, t.List[AnalysisResult]]


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
    summary: t.Dict[str, 'Summary'] = field(default_factory=lambda: {})

    def summary_at_path(self, path: str) -> t.Optional['Summary']:
        result = Summary()
        for p, s in self.summary.items():
            if p.startswith(path):
                result._merge(s)
        return result

@dataclass_json
@dataclass
class Summary:    
    licenses: t.Set[str] = field(default_factory=lambda: set())
    copyrights: t.Dict[str, t.Dict[str, t.List[str]]] = field(default_factory=lambda: {})
    crypto_algorithms: t.Dict[str, t.List[str]] = field(default_factory=lambda: {})
    # components: t.Dict[frozenset, t.Set[str]] = field(
    #     default_factory=lambda: {},
    #     metadata=config(
    #         encoder=lambda d: [[list(k), list(v)] for k, v in d.items()],
    #         decoder=lambda lst: {frozenset(k): set(v) for k, v in lst}
    #     )
    # )
    components: t.Dict[str, t.Set[str]] = field(default_factory=lambda: {})

    @property
    def isEmpty(self) -> bool:
        return not (self.licenses or self.copyrights or self.crypto_algorithms or self.components)

    def _add_copyright_info(self, info: t.Union[t.Dict[str, t.Any], t.List[t.Dict[str, t.Any]]]):
        if isinstance(info, list):
            for i in info:
                self._add_copyright_info(i)
        else:
            for holder in info.get('holders', []):
                holder_data = self.copyrights.get(holder, {'dates': [], 'clauses': []})

                if (_date := info.get('date')) and (_date not in holder_data['dates']):
                    holder_data['dates'].append(_date)

                if (_clause := info.get('clauses')) and (_clause not in holder_data['clauses']):
                    holder_data['clauses'].append(_clause)

                self.copyrights[holder] = holder_data    


    def _add_license_info(self, info: dict):
        if lic_key := info.get('key'):
            self.licenses.add(lic_key)

        elif lic_keys := info.get('licenses'):
            self.licenses.update(set(lic_keys))

        if copyright_info := info.get('copyright'):
            self._add_copyright_info(copyright_info)


    def _add_component(self, purls: t.List[str], version: t.Optional[str] = None):        
        if purls:
            #purl = frozenset(purls)
            purl = purls[0]
            vers = self.components.setdefault(purl, set())
            if v := version:
                vers.add(v)        

    def _merge(self, other: 'Summary'):
        self.licenses.update(other.licenses)

        for holder, holder_data in other.copyrights.items():
            existing_holder_data = self.copyrights.get(holder, {'dates': [], 'clauses': []})

            for date in holder_data.get('dates', []):
                if date not in existing_holder_data['dates']:
                    existing_holder_data['dates'].append(date)

            for clause in holder_data.get('clauses', []):
                if clause not in existing_holder_data['clauses']:
                    existing_holder_data['clauses'].append(clause)

            self.copyrights[holder] = existing_holder_data

        for alg, codings in other.crypto_algorithms.items():
            existing_codings = self.crypto_algorithms.get(alg, [])
            for coding in codings:
                if coding not in existing_codings:
                    existing_codings.append(coding)
            self.crypto_algorithms[alg] = existing_codings

        for purl, versions in other.components.items():
            existing_versions = self.components.get(purl, set())
            existing_versions.update(versions)
            self.components[purl] = existing_versions


class SummaryTree:
    def __init__(self):
        self.children: t.Dict[str, 'SummaryTree'] = {}
        self.summary: Summary = Summary()

    def get_node(self, path: str) -> 'SummaryTree':
        keys = path.split(os.sep)        
        node = self

        for k in keys:
            if k not in node.children:
                new_node = SummaryTree()
                node.children[k] = new_node
                node = new_node
            else:
                node = node.children[k]

        return node

    def flatten(self) -> t.Dict[str, Summary]:    
        def _flatten(node: 'SummaryTree', path: str) -> t.Dict[str, Summary]:
            if not node.children:
                return {path: node.summary} if not node.summary.isEmpty else {}
            
            else:
                merge = True
                flattened = {}
                
                purls = set(node.summary.components.keys())
                
                for child_path, child_node in node.children.items():
                    child_flattened = _flatten(child_node, os.path.join(path, child_path))
                    flattened.update(child_flattened)
                    
                    if not all(set(child_flattened.components.keys()).issubset(purls) for child_flattened in child_flattened.values()):
                        merge = False

                if merge:
                    while flattened:
                        _, child_summary = flattened.popitem()
                        node.summary._merge(child_summary)
                
                if not node.summary.isEmpty:
                    flattened[path] = node.summary

                return flattened


        return _flatten(self, '')
        

def compute_summary(scan: Scan):        
    summary = SummaryTree()

    # Sort paths by depth (children first), then alphabetically within same depth
    # sorted_paths = sorted(scan.result.keys(), key=lambda p: (-p.count(os.sep), p))

    for path, res in scan.result.items():        
        dirpath = os.path.dirname(path)
        summary_entry = summary.get_node(dirpath).summary
        
        if lic_info := res.get('license'):
            summary_entry._add_license_info(lic_info)            

        # Collect licenses from commets iff. no license result was found
        elif comments := res.get('comments'):
            for c in comments:
                if c_lic_info := c.get('license'):
                    summary_entry._add_license_info(c_lic_info)
                else:
                    summary_entry._add_license_info(c)

        if crypto_algs := res.get('crypto'):
            for crypto_alg in crypto_algs:
                alg = crypto_alg['algorithm']
                codings = summary_entry.crypto_algorithms.get(alg, [])
                if (coding := crypto_alg.get('coding')) and (coding not in codings):
                    codings.append(coding)
                summary_entry.crypto_algorithms[alg] = codings

        if scanoss := res.get('scanoss'):
            for scanoss_scan in scanoss.get('scan', []):
                if purl := scanoss_scan.get('purl'):                    
                    summary_entry._add_component(purl, scanoss_scan.get('version'))


    scan.summary = summary.flatten()


    #licenses_list = list(licenses)
    # scan.summary = {
    #     'licenses': licenses_list,
    #     'copyrights': copyrights,
    #     'crypto_algorithms': crypto_algorithms,
    #     'incompatible_licenses': compute_licenses_compatibility(licenses_list)
    # }


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
