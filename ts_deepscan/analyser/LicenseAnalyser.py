# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import re

from .textutils import *
from .FileAnalyser import FileAnalyser


class LicenseAnalyser(FileAnalyser):
    category_name = 'license'

    def __init__(self, dataset):
        self.dataset = dataset

    def match(self, path, opts):
        if not opts or opts.filterFiles:
            return re.search('LICENSE|COPYING|COPYRIGHT', path.name, re.IGNORECASE)
        else:
            return True

    def analyse(self, path, opts):
        with path.open(errors="surrogateescape") as fp:
            content = fp.read()

            result = analyse_license_text(content, self.dataset, opts)

            if result is None:
                result = analyse_text(content, self.dataset, opts)

            return result