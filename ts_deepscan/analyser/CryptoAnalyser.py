import pyminr

from ..analyser import FileAnalyser
from ..commentparser.language import Lang, classify

class CryptoAnalyser(FileAnalyser):
    category_name = 'crypto'

    def __init__(self):
        pyminr.load_crypto_definitions()

    def __del__(self):
        pyminr.clean_crypto_definitions()

    def match(self, path, opts):
        return classify(path) != Lang.Unknown

    def analyse(self, path, opts):
        result = []

        def _report_result(algorithm, coding):
            result.append({
                'algorithm': algorithm,
                'coding': coding
            })

        with path.open('rb') as fp:
            src = fp.read()
            pyminr.find_crypto_algorithms(src, _report_result)

        return result