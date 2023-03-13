# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import re

from .textutils import *

from . import FileAnalyser
from ..analyser import Dataset


class LicenseAnalyser(FileAnalyser):
    category_name = 'license'

    def __init__(self, dataset: Dataset, include_copyright = False):
        self.dataset = dataset
        self.include_copyright = include_copyright

    def _match(self, path):
        return re.search('LICENSE|COPYING|COPYRIGHT', path.name, re.IGNORECASE)

    @property
    def options(self) -> dict:
        # TODO: add categorization of options: 'include_copyright' -> 'license.include_copyright'
        # TODO: rename 'includeCopyright' -> 'include_copyright'
        return {
            'includeCopyright': self.include_copyright
        }

    def analyse(self, path):
        with path.open(errors="surrogateescape") as fp:
            content = fp.read()

            result = analyse_license_text(content, self.dataset, search_copyright=self.include_copyright)

            if result is None:
                result = analyse_text(content, self.dataset, search_copyright=self.include_copyright)

            return result