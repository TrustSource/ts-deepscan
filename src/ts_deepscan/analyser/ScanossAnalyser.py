import typing as t

from pathlib import Path
from scanoss.winnowing import Winnowing

from ..analyser import SourceCodeAnalyser
from ..commentparser.language import Lang, classify


class ScanossAnalyser(SourceCodeAnalyser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._winnowing = Winnowing()

    @property
    def category(self) -> str:
        return 'scanoss'

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

