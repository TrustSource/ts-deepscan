import pyminr

from pathlib import Path

from ..analyser import TextFileAnalyser
from ..commentparser.language import Lang, classify


class CryptoAnalyser(TextFileAnalyser):
    category_name = 'crypto'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _match(self, path: Path):
        return classify(path) != Lang.Unknown and super()._match(path)

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
