# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import re

from .textutils import *

from . import TextFileAnalyser, AnalysisResult
from ..analyser.Dataset import Dataset
from ..commentparser.language import Lang, classify

MAX_LICENSE_TEXT_LENGTH = 100000

_common_license_file_names = [
    "LICENSE", "COPYING", "COPYRIGHT", "NOTICE", "ABOUT", "INSTALL", "README", "CODE_OF_CONDUCT"
]

class LicenseAnalyser(TextFileAnalyser):
    def __init__(self, 
                 dataset: Dataset, 
                 include_copyright=False,
                 analyse_all_text_files=False,
                 *args, 
                 **kwargs):
        
        super().__init__(*args, **kwargs)

        self.dataset = dataset
        self.include_copyright = include_copyright
        self.analyse_all_text_files = analyse_all_text_files

    @property
    def category(self) -> str:
        return 'license'

    def _match(self, path):
        return classify(path) == Lang.Unknown and super()._match(path)

    @property
    def options(self) -> dict:
        # TODO: add categorization of options: 'include_copyright' -> 'license.include_copyright'
        # TODO: rename 'includeCopyright' -> 'include_copyright'
        return {
            'includeCopyright': self.include_copyright,
            'analyseAllTextFiles': self.analyse_all_text_files
        }

    def apply(self, path: Path, root: t.Optional[Path] = None) -> t.Optional[AnalysisResult]:
        with path.open('r', encoding='utf-8', errors="surrogateescape") as fp:
            result = None
            content = fp.read()
            
            if len(content) < MAX_LICENSE_TEXT_LENGTH:
                if re.search('|'.join(_common_license_file_names), path.name, re.IGNORECASE):
                    result = analyse_license_text(content, self.dataset, search_copyright=self.include_copyright)

            if result is None and self.analyse_all_text_files:
                result = analyse_text(content, self.dataset,
                                      timeout=self.timeout,
                                      search_copyright=self.include_copyright)

            return AnalysisResult(self.category, result) if result else None
