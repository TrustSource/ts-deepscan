import typing as t

from pathlib import Path
from scanoss.winnowing import Winnowing

from ..analyser import TextFileAnalyser
from ..commentparser.language import Lang, classify


class ScanossAnalyser(TextFileAnalyser):
    category_name = 'scanoss'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._winnowing = Winnowing()

    def _match(self, path: Path):
        return classify(path) != Lang.Unknown and super()._match(path)

    @property
    def options(self) -> dict:
        return {
            'includeWfp': True
        }

    def analyse(self, path: Path, root: t.Optional[Path] = None):
        relpath = path.relative_to(root) if root else path

        if res := self._winnowing.wfp_for_file(str(path), str(relpath)):
            return {
                'wfp': res
            }
        else:
            return None

