import pyminr
import typing as t

from pathlib import Path

from ..analyser import SourceCodeAnalyser
from ..commentparser.language import Lang, classify


class CryptoAnalyser(SourceCodeAnalyser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def category(self) -> str:
        return 'crypto'

    @property
    def options(self) -> dict:
        return {
            'includeCrypto': True
        }

    def analyse(self, path: Path, root: t.Optional[Path] = None):
        result = set()

        def _report_result(algorithm, coding):
            result.add((algorithm, coding))

        with path.open('rb') as fp:
            pyminr.find_crypto_algorithms(fp.read(), _report_result)

        return [{'algorithm': res[0], 'coding': res[1]} for res in result]
