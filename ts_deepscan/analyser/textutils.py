# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import string
import spacy
import pathlib
#import re

from spacy.vocab import Vocab
from spacy.tokens import Doc

from .spdx import parse_spdx_expr
from ..scancode.cluecode.copyrights import detect_copyrights

_nlp = None


def create_doc(text = None):
    global _nlp

    if not _nlp:
#        nlp = spacy.load('en')
        _nlp = spacy.load('en_core_web_sm')

    if text:
        try:
            doc = _nlp(text)
            return doc
        except UnicodeEncodeError:
            return None
    else:
        return Doc(Vocab())


def compute_hash(doc):
    hashwords = [t.text for t in doc if not (t.is_space or t.is_punct)]
    hashstr = ' '.join(hashwords)
    return hashlib.md5(hashstr.encode('utf-8')).hexdigest()


def compute_file_hash(path: pathlib.Path) -> str:
    with path.open() as fp:
        content = fp.read()
        return hashlib.md5(content.encode('utf-8')).hexdigest()


def compute_similarity(doc1, doc2):
    w1 = {t.orth for t in doc1 if not (t.is_space or t.is_punct)}
    w2 = {t.orth for t in doc2 if not (t.is_space or t.is_punct)}

    score = float(2 * len(w1.intersection(w2))) / (len(w1) + len(w2))

    return score


# def extract_copyright(text):
# #    results = []
#     for s in [r'\B©\B', r'\bcopyright\b', r'\B\(c\)\B']:
#         matches = [m.start() for m in re.finditer(s, text.lower())]
#         for cop_begin in matches:
#             if cop_begin >= 0:
#                 cop_end = text.find(u'\n', cop_begin)
#                 cop_begin = text.rfind(u'\n', 0, cop_begin)
#
#                 if cop_begin < 0:
#                     cop_begin = 0
#
#                 if cop_end < 0:
#                     cop_sent = text[cop_begin:]
#                 else:
#                     cop_sent = text[cop_begin:cop_end]
#
#                 cop_sent = cop_sent.strip(' \n\t')
#                 cop_doc = create_doc(cop_sent)
#
#                 result = {
#                     'clause': cop_sent,
#                     'date': '',
#                     'holders': []
#                 }
#
#                 for ent in cop_doc.ents:
#                     if ent.label_ in ['DATE']:
#                         result['date'] = ent.text
#
#                     if ent.label_ in ['PERSON', 'ORG']:
#                         result['holders'].append(ent.text)
#
#                 if result['date'] and result['holders']:
#                     return result
#
# #                elif result['date'] or result['holders']:
# #                    results.append(result)
#
#     return None #if not results else results[0]

def extract_copyright(text):
    authors = []
    copyrights = []

    def push_detection_to_results(t, v):
        if t == 'years':
            copyrights[-1]['date'] = v
        else:
            res = copyrights[-1].get(t, [])
            res.append(v)
            copyrights[-1][t] = res


    for spdx_copyright_text in find_spdx_copyright_text(text):
        copyrights.append({'clause': 'SPDX-FileCopyrightText: {}'.format(spdx_copyright_text)})

        for (ty, val, _, _) in detect_copyrights('Copyright {}'.format(spdx_copyright_text), copyrights=False):
            push_detection_to_results(ty, val)


    for (ty, val, _, _) in detect_copyrights(text):
        if ty == 'copyrights':
            copyrights.append({'clause': val})
        elif ty == 'authors':
            authors.append(val)
        else:
            push_detection_to_results(ty, val)

    result = {}

    if copyrights:
        result['copyright'] = copyrights

    if authors:
        result['authors'] = authors

    return result



def find_spdx_copyright_text(text):
    expr_begin = 0
    expr = 'spdx-filecopyrighttext:'

    while True:
        expr_begin = text.lower().find(expr, expr_begin)
        if expr_begin == -1: return

        expr_begin += len(expr)
        expr_end = text.find(u'\n', expr_begin)

        if expr_end == -1:
            yield text[expr_begin:]
        else:
            yield text[expr_begin:expr_end]

        expr_begin = expr_end


def find_spdx_license_id(text):
    expr = 'spdx-license-identifier:'
    expr_begin = text.lower().find(expr)

    if expr_begin >= 0:
        expr_begin += len(expr)
        expr_end = text.find(u'\n', expr_begin)
        if expr_end < 0:
            return text[expr_begin:]
        else:
            return text[expr_begin:expr_end]

    return None

_ignored_aliases = [
    'Intel', 'MIT', 'Crossword', 'Cube', 'curl', 'DOC', 'EPICS', 'Fair', 'Glide', 'JSON', 'Libpng', 'MakeIndex',
    'Nokia', 'Noweb', 'NTP', 'OML', 'OpenSSL', 'Plexus', 'PostgreSQL', 'psutils', 'psfrag', 'Ruby', 'Saxpath',
    'Sendmail', 'Sleepycat', 'TCL', 'Vim', 'W3C', 'X11', 'Xerox', 'Xnet', 'Zed', 'Zlib'
]

def find_aliases(text, dataset):
    for k, v in dataset.data.items():
        name = v['name']
        aliases = v['aliases']

        if k not in aliases and k not in _ignored_aliases:
            aliases.append(k)
        
        if name not in aliases:
            aliases.append(name)

        for alias in aliases:
            if not alias:
                continue

            index = text.find(alias)
            if index == -1:
                continue

            boundaries = string.whitespace + string.punctuation
            if index > 0 and text[index - 1] not in boundaries:
                continue

            index = index + len(alias)
            if index < len(text) and text[index] not in boundaries:
                continue

            yield k



def analyse_text(text, dataset, opts):
    copyrights = extract_copyright(text) if opts and opts.includeCopyright else {}
    spdx = find_spdx_license_id(text)

    licenses = []

    if spdx:
        try:
            expr = parse_spdx_expr(spdx)
        except Exception:
            expr = None

        if expr:
            licenses = expr.licenses

    if not licenses:
        licenses = [lic for lic in find_aliases(text, dataset)]


    if licenses or copyrights or spdx:
        result = {'text': text, 'licenses': licenses}

        if spdx:
            result['spdx'] = spdx

        if copyrights:
            result.update(copyrights)

        return result

    return None



def analyse_license_text(text, dataset, opts):
    key, score = dataset.find_match(text)
    if key:
        result = {
            'key': key,
            'score': score,
        }

        _copyright = extract_copyright(text) if opts and opts.includeCopyright else None
        if _copyright:
            result.update(_copyright)

        return result