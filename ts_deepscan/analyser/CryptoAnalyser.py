import pyminr

from pathlib import Path

from ..analyser import FileAnalyser
from ..commentparser.language import Lang, classify

class CryptoAnalyser(FileAnalyser):
    category_name = 'crypto'

    def _match(self, path: Path):
        return classify(path) != Lang.Unknown

    @property
    def options(self) -> dict:
        return {
            'includeCrypto': True
        }

    def analyse(self, path: Path):
        result = []

        def _report_result(algorithm, coding):
            result.append({
                'algorithm': algorithm,
                'coding': coding
            })

        with path.open('rb') as fp:
            pyminr.find_crypto_algorithms(fp.read(), _report_result)

        return result