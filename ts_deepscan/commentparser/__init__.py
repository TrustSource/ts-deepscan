# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

from .language import Lang


def extract_comments(content, lang):
    if not content:
        return None

    if not content.endswith('\n'):
        content += '\n'

    lexer = Lexer(content, lang, offset=0, pos=Position(1, [0]))
    lexer.lex()
    return lexer.comments


class Comment(object):
    def __init__(self, startLine, endLine, text):
        self.startLine = startLine
        self.endLine = endLine
        self.text = text


class Position(object):
    def __init__(self, line, lineChar):
        self.line = line
        self.lineChar = lineChar


class Lexer(object):
    def __init__(self, content, lang, offset, pos):
        self.__content = content
        self.__lang = lang
        self.__offset = offset
        self.__pos = pos
        self.comments = []

    def lex(self):
        while True:

            c, ok = self.peekChar()
            if not ok:
                break

            if c in ['"', '\'', '`']:
                if self.__lang == Lang.HTML:
                    break

                ok, escape = self.__lang.is_quote(c)
                if not ok:
                    break

                content = ""
                isDocString = False
                quote = c

                if self.__lang == Lang.Python:
                    if c == '\'' and self.match("'''"):
                        quote = "'''"
                        if self.__pos.lineChar[len(self.__pos.lineChar)-1] == 3:
                            isDocString = True
                    elif c == '"' and self.match('"""'):
                        quote = '"""'
                        if self.__pos.lineChar[len(self.__pos.lineChar)-1] == 3:
                            isDocString = True
                    else:
                        self.readChar()
                else:
                    self.readChar()

                startLine = self.__pos.line
                while True:
                    c, ok = self.peekChar()
                    if not ok:
                        # EOF in string
                        return

                    if escape and c == '\\':
                        self.readChar()

                    elif self.match(quote):
                        break

                    elif self.__lang in [Lang.JavaScript, Lang.Perl] and c == '\n':
                        break

                    c = self.readChar()
                    if isDocString:
                        content += c

                    if self.eof:
                        # EOF in string
                        return

                if isDocString:
                    self.comments.append(Comment(
                        startLine=startLine,
                        endLine=self.__pos.line,
                        text=content
                    ))

            else:
                startLine = self.__pos.line
                content = ""
                ok, start, end = self.multiLineComment()
                if ok:
                    nesting = 0
                    while True:
                        if self.eof:
                            # EOF in multiline comment
                            return

                        c = self.readChar()
                        content += c

                        if self.__lang.is_nested_allowed and self.match(start):
                            content += start
                            nesting += 1

                        if self.match(end):
                            if nesting > 0:
                                content += end
                                nesting -= 1
                            else:
                                break

                    self.comments.append(Comment(
                        startLine=startLine,
                        endLine=self.__pos.line,
                        text=content
                    ))

                elif self.singleLineComment():
                    while True:
                        if self.eof:
                            # EOF in single line comment
                            return

                        c = self.readChar()
                        if c == '\n':
                            self.unreadChar(c)
                            break
                        content += c

                    self.comments.append(Comment(
                        startLine = startLine,
                        endLine=self.__pos.line,
                        text=content
                    ))

            self.readChar()


    def singleLineComment(self):
        if self.match(self.__lang.singleLineCommentStart):
            return True

        if self.__lang == Lang.SQL:
            return self.match(Lang.MySQL.singleLineCommentStart)
        elif self.__lang == Lang.ObjectiveC:
            return self.match(Lang.Matlab.singleLineCommentStart)


        return False


    def multiLineComment(self):
        s = self.__lang.multiLineCommentStart
        if self.match(s):
            return True, s, self.__lang.multiLineCommentEnd

        if self.__lang == Lang.SQL:
            s = Lang.MySQL.multiLineCommentStart
            if self.match(s):
                return True, s, Lang.MySQL.multiLineCommentEnd
        elif self.__lang == Lang.ObjectiveC:
            s = Lang.Matlab.multiLineCommentStart
            if self.match(s):
                return True, s, Lang.Matlab.multiLineCommentEnd

        return False, "", ""


    def match(self, s):
        if s == "":
            return False

        orig = s
        read = ""
        while len(s) > 0 and not self.eof:
            r = s[0]
            c, ok = self.peekChar()
            if ok and c == r:
                read += c
            else:
                for c in reversed(read):
                    self.unreadChar(c)

                return False

            s = s[1:]
            self.readChar()

        return read == orig

    @property
    def eof(self):
        return len(self.__content) <= self.__offset


    def peekChar(self):
        if self.eof:
            return None, False

        return self.__content[self.__offset], True


    def readChar(self):
        r = self.__content[self.__offset]

        if r == '\n':
            self.__pos.line += 1
            self.__pos.lineChar.append(0)
        else:
            self.__pos.lineChar[len(self.__pos.lineChar) - 1] += 1

        self.__offset += 1
        return r


    def unreadChar(self, c):
        self.__offset -= 1

        if c == '\n':
            self.__pos.line -= 1
            if len(self.__pos.lineChar) > 1:
                self.__pos.lineChar = self.__pos.lineChar[:len(self.__pos.lineChar) - 1]
            else:
                self.__pos.lineChar[0] = 0
        else:
            self.__pos.lineChar[len(self.__pos.lineChar) - 1] -= 1