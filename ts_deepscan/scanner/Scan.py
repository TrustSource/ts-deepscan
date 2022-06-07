import json

from typing import List
from datetime import datetime

from ..analyser.FileAnalyser import AnalyserOptions

class Scan(object):
    def __init__(self, options: AnalyserOptions, time: datetime=datetime.now()):
        self.time = str(time)
        self.options = {
            'includeCopyright': options.includeCopyright
        }
        self.result = {}

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
    def is_compatible_licenses(self):
#        import osadl_matrix
#        lics = self.licenses
#        return len(lics) <= 1 or osadl_matrix.is_compatible(lics) != osadl_matrix.OSADLCompatibility.NO
        return True

    @staticmethod
    def load(data: str):
        return Scan(**json.loads(data))

    def dump(self) -> str:
        return json.dumps(self.__dict__)


