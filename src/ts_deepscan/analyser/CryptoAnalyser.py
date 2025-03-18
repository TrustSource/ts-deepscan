import pyminr
import typing as t

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

    def analyse(self, path: Path, root: t.Optional[Path] = None):
        result = set()

        def _report_result(algorithm, coding):
            result.add((algorithm, coding))

        with path.open('rb') as fp:
            pyminr.find_crypto_algorithms(fp.read(), _report_result)

        return [{'algorithm': res[0], 'coding': res[1]} for res in result]
