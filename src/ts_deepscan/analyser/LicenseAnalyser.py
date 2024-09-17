# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import re

from .textutils import *

from . import TextFileAnalyser
from ..analyser import Dataset
from ..commentparser.language import Lang, classify

MAX_LICENSE_TEXT_LENGTH = 100000


class LicenseAnalyser(TextFileAnalyser):
    category_name = 'license'

    def __init__(self, dataset: Dataset, include_copyright=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dataset = dataset
        self.include_copyright = include_copyright

    def _match(self, path):
        return classify(path) == Lang.Unknown and super()._match(path)

    @property
    def options(self) -> dict:
        # TODO: add categorization of options: 'include_copyright' -> 'license.include_copyright'
        # TODO: rename 'includeCopyright' -> 'include_copyright'
        return {
            'includeCopyright': self.include_copyright
        }

    def analyse(self, path: Path, root: t.Optional[Path] = None):
        with path.open('r', encoding='utf-8', errors="surrogateescape") as fp:
            result = None
            content = fp.read()

            if len(content) < MAX_LICENSE_TEXT_LENGTH:
                if re.search('LICENSE|COPYING|COPYRIGHT', path.name, re.IGNORECASE):
                    result = analyse_license_text(content, self.dataset, search_copyright=self.include_copyright)

            if result is None:
                result = analyse_text(content, self.dataset,
                                      timeout=self.timeout,
                                      search_copyright=self.include_copyright)

            return result
