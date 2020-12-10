# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

class ScanException(Exception):
    code = None
    description = None

    def __init__(self, description=None):
        super(Exception, self).__init__()
        if description is not None:
            self.description = description

    def __index__(self, description=None):
        super(Exception, self).__init__()
        if description is not None:
            self.description = description

    def __str__(self):
        code = self.code if self.code is not None else "???"
        return "%s: %s" % (code, self.description)



class InternalScanException(ScanException):
    code = 0
    description = "Internal error"