#
# Copyright (c) 2016-2018 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/scancode-toolkit/
# The ScanCode software is licensed under the Apache License version 2.0.
# Data generated with ScanCode require an acknowledgment.
# ScanCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with ScanCode or any ScanCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with ScanCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  ScanCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  ScanCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/scancode-toolkit/ for support and download.


import unicodedata

from text_unidecode import unidecode


def numbered_text_lines(text):
    return enumerate(unicode_text_lines(text), 1)


def unicode_text_lines(text):
    for line in text.splitlines(True):
        yield remove_verbatim_cr_lf_tab_chars(line)


def remove_verbatim_cr_lf_tab_chars(s):
    """
    Return a string replacing by a space any verbatim but escaped line endings
    and tabs (such as a literal \n or \r \t).
    """
    if not s:
        return s
    return s.replace('\\r', ' ').replace('\\n', ' ').replace('\\t', ' ')



def toascii(s, translit=False):
    """
    Convert a Unicode or byte string to ASCII characters, including replacing
    accented characters with their non-accented equivalent.

    If `translit` is False use the Unicode NFKD equivalence.
    If `translit` is True, use a transliteration with the unidecode library.

    Non ISO-Latin and non ASCII characters are stripped from the output. When no
    transliteration is possible, the resulting character is replaced by an
    underscore "_".

    For Unicode NFKD equivalence, see http://en.wikipedia.org/wiki/Unicode_equivalence
    The convertion may NOT preserve the original string length and with NFKD some
    characters may be deleted.
    Inspired from: http://code.activestate.com/recipes/251871/#c10 by Aaron Bentley.
    """
    if translit:
        converted = unidecode(s)
    else:
        converted = unicodedata.normalize('NFKD', s)

    converted = converted.replace('[?]', '_')
    converted = converted.encode('ascii', 'ignore')
    return converted.decode('ascii')



CR = '\r'
LF = '\n'
CRLF = CR + LF
CRLF_NO_CR = ' ' + LF


def unixlinesep(text, preserve=False):
    """
    Normalize a string to Unix line separators. Preserve character offset by
    replacing with spaces if preserve is True.
    """
    return text.replace(CRLF, CRLF_NO_CR if preserve else LF).replace(CR, LF)