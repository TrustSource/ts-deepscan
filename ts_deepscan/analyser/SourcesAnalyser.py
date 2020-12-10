# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

from ..commentparser import Comment, extract_comments
from ..commentparser.language import Lang, classify
from .FileAnalyser import FileAnalyser
from .textutils import *


class SourcesAnalyser(FileAnalyser):
    category_name = 'comments'

    def __init__(self, dataset):
        self.dataset = dataset


    def match(self, path, opts):
        return classify(path) != Lang.Unknown

    def analyse(self, path, opts):
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
                for res in self.analyse_comments(merged, opts):
                    results.append(res)

                if len(results) > 0:
                    return results

        return None


    def analyse_comments(self, comments, opts):
        if len(comments) > 0:
            head, *tail = comments
            res = analyse_license_text(head.text, self.dataset, opts)
            if res:
                res['line'] = head.startLine
                res['endLine'] = head.endLine
                comments = tail

                yield res

        for c in comments:
            res = analyse_text(c.text, self.dataset, opts)
            if res:
                res['line'] = c.startLine
                res['endLine'] = c.endLine

                yield res

