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


class URLScanException(ScanException):
    code = 1
    description = "Invalid URL"


class HTTPScanException(ScanException):
    code = 2

class GitScanException(ScanException):
    code = 3