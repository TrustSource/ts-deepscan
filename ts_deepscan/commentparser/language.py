# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum, unique

@unique
class Lang(Enum):
    Unknown = 0
    AppleScript = 1
    Assembly = 2
    Batch = 3
    C = 4
    Clif = 5
    Clojure = 6
    CMake = 7
    CSharp = 8
    Dart = 9
    Elixir = 10
    Fortran = 11
    GLSLF = 12 # OpenGL Shading Language
    Go = 13
    Haskell = 14
    HTML = 15
    Flex = 16
    Java = 17
    JavaScript = 18
    Kotlin = 19
    Lisp = 20
    Matlab = 21
    Markdown = 22
    MySQL = 23
    NinjaBuild = 24
    ObjectiveC = 25
    Perl = 26
    Python = 27
    R = 28
    Ruby = 29
    Rust = 30
    Shader = 31
    Shell = 32
    SQL = 33
    Swift = 34
    SWIG = 35
    TypeScript = 36
    Yacc = 37
    Yaml = 38
    XML = 39

    @property
    def style(self):
        if self in [Lang.Assembly, Lang.C, Lang.CSharp, Lang.Dart, Lang.Flex, Lang.GLSLF, Lang.Go, Lang.Java,
                    Lang.JavaScript, Lang.Kotlin, Lang.ObjectiveC, Lang.Rust, Lang.Shader, Lang.Swift,
                    Lang.SWIG, Lang.TypeScript, Lang.Yacc]:
            return Style.bcpl

        elif self == Lang.Batch:
            return Style.batch

        elif self == Lang.CMake:
            return Style.cmake

        elif self == Lang.Fortran:
            return Style.fortran

        elif self == Lang.Haskell:
            return Style.haskell

        elif self in [Lang.HTML, Lang.Markdown, Lang.XML]:
            return Style.html

        elif self in [Lang.Clojure, Lang.Lisp]:
            return Style.lisp

        elif self == Lang.Ruby:
            return Style.ruby

        elif self in [Lang.Clif, Lang.Elixir, Lang.NinjaBuild, Lang.Perl, Lang.Python, Lang.R, Lang.Shell, Lang.Yaml]:
            return Style.shell

        elif self == Lang.Matlab:
            return Style.matlab

        elif self == Lang.MySQL:
            return Style.mysql

        elif self == Lang.SQL:
            return Style.sql

        return Style.unknown

    @property
    def singleLineCommentStart(self):
        if self.style in [Style.applescript, Style.haskell, Style.sql]:
            return "--"
        elif self.style == Style.batch:
            return "@REM"
        elif self.style == Style.bcpl:
            return "//"
        elif self.style == Style.fortran:
            return "!"
        elif self.style == Style.lisp:
            return ";"
        elif self.style == Style.matlab:
            return "%"
        elif self.style in [Style.shell, Style.ruby, Style.cmake, Style.mysql]:
            return "#"

        return ""

    @property
    def multiLineCommentStart(self):
        if self.style == Style.applescript:
            return "(*"

        elif self.style in [Style.bcpl, Style.mysql] and self != Lang.Rust:
            return "/*"

        elif self.style == Style.cmake:
            return "#[["

        elif self.style == Style.haskell:
            return "{-"

        elif self.style == Style.html:
            return "<!--"

        elif self.style == Style.matlab:
            return "%{"

        elif self.style == Style.ruby:
            return "=begin"

        return ""

    @property
    def multiLineCommentEnd(self):
        if self.style == Style.applescript:
            return "*)"

        elif self.style in [Style.bcpl, Style.mysql] and self != Lang.Rust:
            return "*/"

        elif self.style == Style.cmake:
            return "]]"

        elif self.style == Style.haskell:
            return "-}"

        elif self.style == Style.html:
            return "-->"

        elif self.style == Style.matlab:
            return "%}"

        elif self.style == Style.ruby:
            return "=end"

        return ""

    # (ok, escape)
    def is_quote(self, quote):
        if quote in ['"', '\'']:
            return True, True
        elif quote == '`' and self == Lang.Go:
            return True, False

        return False, False

    @property
    def is_nested_allowed(self):
        return self == Lang.Swift



@unique
class Style(Enum):
    unknown = 0
    applescript = 1     # -- ... and (*... *)
    batch = 2           # @ REM
    bcpl = 3            # // ... and / *... * /
    cmake = 4           #  # ... and #[[ ... ]]
    fortran = 5         # ! ...
    haskell = 6         # -- ... and {- ... -}
    html = 7            # <!-- ... -->
    lisp = 8            # ;; ...
    matlab = 9          # % ...
    mysql = 10          #  # ... and /* ... */
    ruby = 11           #  # ... and =begin ... =end
    shell = 12          #  # ... and %{ ... %}
    sql = 13            # -- ... and / *... * /


def classify(path):
    ext = path.suffix
    if len(ext) == 0 or ext[0] != '.':
        return Lang.Unknown

    ext = ext[1:]

    if ext == "applescript":
        return Lang.AppleScript
    elif ext == "bat":
        return Lang.Batch
    elif ext in ["c", "cc", "cpp", "c++", "h", "hh", "hpp"]:
        return Lang.C
    elif ext ==  "clif":
        return Lang.Clif
    elif ext ==  "cmake":
        return Lang.CMake
    elif ext ==  "cs":
        return Lang.CSharp
    elif ext == "dart":
        return Lang.Dart
    elif ext in ["ex", "exs"]:
        return Lang.Elixir
    elif ext in ["f", "f90", "f95"]:
        return Lang.Fortran
    elif ext == "glslf":
        return Lang.GLSLF
    elif ext == "go":
        return Lang.Go
    elif ext == "hs":
        return Lang.Haskell
    elif ext in ["html", "htm", "ng", "sgml"]:
        return Lang.HTML
    elif ext == "java":
        return Lang.Java
    elif ext == "js":
        return Lang.JavaScript
    elif ext == "kt":
        return Lang.Kotlin
    elif ext == "l":
        return Lang.Flex
    elif ext in ["lisp", "el", "clj"]:
        return Lang.Lisp
    elif ext in ["m", "mm"]:
        return Lang.ObjectiveC
    elif ext == "md":
        return Lang.Markdown
    elif ext == "gn":
        return Lang.NinjaBuild
    elif ext in ["pl", "pm"]:
        return Lang.Perl
    elif ext in ["py", "pi"]:
        return Lang.Python
    elif ext == "r":
        return Lang.R
    elif ext ==  "rb":
        return Lang.Ruby
    elif ext == "rs":
        return Lang.Rust
    elif ext ==  "s":
        return Lang.Assembly
    elif ext == "sh":
        return Lang.Shell
    elif ext == "shader":
        return Lang.Shader
    elif ext ==  "sql":
        return Lang.SQL
    elif ext == "swift":
        return Lang.Swift
    elif ext == "swig":
        return Lang.SWIG
    elif ext in ["ts", "tsx"]:
        return Lang.TypeScript
    elif ext == "y":
        return Lang.Yacc
    elif ext == "yaml":
        return Lang.Yaml
    elif ext in ["xml", "xmi", "xslt", "xsd"]:
        return Lang.XML

    return Lang.Unknown