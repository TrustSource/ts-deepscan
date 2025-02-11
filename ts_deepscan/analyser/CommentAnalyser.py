# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Iterable
from pathlib import Path

from . import TextFileAnalyser
from .Dataset import Dataset
from .textutils import analyse_text, analyse_license_text

from ..commentparser import Comment, extract_comments
from ..commentparser.language import Lang, classify


class CommentAnalyser(TextFileAnalyser):
    category_name = 'comments'

    def __init__(self, dataset: Dataset, include_copyright=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dataset = dataset
        self.include_copyright = include_copyright

    def _match(self, path: Path) -> bool:
        return classify(path) != Lang.Unknown and super()._match(path)

    @property
    def options(self) -> dict:
        # TODO: add categorization of options: 'include_copyright' -> 'comments.include_copyright'
        # TODO: rename 'includeCopyright' -> 'include_copyright'
        return {
            'includeCopyright': self.include_copyright
        }

    def analyse(self, path: Path, root: Optional[Path] = None) -> Optional[list]:
        with path.open(errors="surrogateescape") as fp:
            content = fp.read()
            comments = extract_comments(content, classify(path))

            # Merge comments
            if comments:
                merged = []
                cur, *tail = comments

                for c in tail:
                    if c.startLine == cur.endLine + 1:
                        cur = Comment(cur.startLine, c.endLine, cur.text + '\n' + c.text)
                    else:
                        merged.append(cur)
                        cur = c

                merged.append(cur)
                results = []
                for res in self.__analyse_comments(merged):
                    results.append(res)

                if len(results) > 0:
                    return results

        return None

    def __analyse_comments(self, comments) -> Iterable[dict]:
        if len(comments) > 0:
            head, *tail = comments
            res = analyse_license_text(head.text, self.dataset,
                                       search_copyright=self.include_copyright)
            if res:
                res['line'] = head.startLine
                res['endLine'] = head.endLine
                comments = tail

                yield res

        for c in comments:
            res = analyse_text(c.text, self.dataset,
                               timeout=self.timeout,
                               search_copyright=self.include_copyright)
            if res:
                res['line'] = c.startLine
                res['endLine'] = c.endLine

                yield res
