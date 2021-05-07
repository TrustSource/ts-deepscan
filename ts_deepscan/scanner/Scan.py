import uuid
import json

from typing import Dict

from datetime import datetime
from ..analyser.FileAnalyser import AnalyserOptions


class Scan(object):
    def __init__(self, options: AnalyserOptions, time: datetime=datetime.now()):
        self.time = str(time)
        self.options = {
            'includeCopyright': options.includeCopyright
        }
        self.result = {}

    @staticmethod
    def load(data: str):
        return Scan(**json.loads(data))

    def dump(self) -> str:
        return json.dumps(self.__dict__)


