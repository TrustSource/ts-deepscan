# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

class SpdxParseError(Exception):
    pass

class SpdxOp:
    def __init__(self, op, *args):
        self.op = op
        self.args = [a for a in args]

    @property
    def licenses(self):
        lics = []
        for a in self.args:
            lics.extend(a.licenses)

        return lics

class SpdxLic:
    def __init__(self, key):
        self.key = key

    @property
    def licenses(self):
        return [self.key]



def parse_spdx_expr(expr):
    expr = expr.strip()

    ops = [None]
    stack = []

    pos = 0
    prev = 0

    def reduce():
        nonlocal stack, ops
        start = 0
        for i, v in enumerate(reversed(stack)):
            if v == '(':
                start = len(stack) - i
                break

        if start == 0:
            args = stack
            stack = []
        else:
            args = stack[start:]
            stack = stack[0:start-1]

        if ops[-1]:
            ops[-1].args = args
            stack.append(ops[-1])
            ops.pop()
        elif len(args) == 1:
            stack.append(args[0])
        else:
            raise SpdxParseError()

    def read():
        nonlocal stack, ops, prev
        token = expr[prev:pos].strip()
        prev = pos + 1

        if token == 'AND':
            if not ops[-1]:
                ops[-1] = SpdxOp('AND')
            elif ops[-1].op != 'AND':
                raise SpdxParseError()

        elif token == 'OR':
            if not ops[-1]:
                ops[-1] = SpdxOp('OR')
            elif ops[-1].op != 'OR':
                raise SpdxParseError()

        elif token == 'WITH':
            if not ops[-1]:
                ops[-1] = SpdxOp('WITH')
            else:
                raise SpdxParseError()

        elif token != '':
            stack.append(SpdxLic(token))


    while pos < len(expr):
        if expr[pos] == '(':
            ops.append(None)
            stack.append('(')
            prev = pos + 1

        elif expr[pos] == ')':
            read()
            reduce()

        elif expr[pos] == ' ':
            read()

        pos += 1

    read()
    reduce()

    if len(stack) == 1:
        return stack[0]
    elif len(stack) > 1:
        raise SpdxParseError()
    else:
        return None


#print(parse_spdx_expr('GPL-2.0-or-later').licenses)