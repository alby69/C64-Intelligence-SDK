"""AST node types used by the compiler pipeline."""

from dataclasses import dataclass, field
from typing import Any, Optional


class N:
    """AST node factory (static methods returning dicts for JS compat)."""

    @staticmethod
    def Program(globals_, funcs):
        return {'k': 'Program', 'globals': globals_, 'funcs': funcs}

    @staticmethod
    def FuncDecl(name, params, ret, body, line=0):
        return {'k': 'FuncDecl', 'name': name, 'params': params,
                'ret': ret, 'body': body, 'line': line}

    @staticmethod
    def VarDecl(type_, name, init=None, isArr=False, arrSize=None, arrInit=None, line=0):
        return {'k': 'VarDecl', 'type': type_, 'name': name, 'init': init,
                'isArr': isArr, 'arrSize': arrSize, 'arrInit': arrInit, 'line': line}

    @staticmethod
    def Block(stmts):
        return {'k': 'Block', 'stmts': stmts}

    @staticmethod
    def Assign(target, value, line=0):
        return {'k': 'Assign', 'target': target, 'value': value, 'line': line}

    @staticmethod
    def If(cond, then_, else_=None, line=0):
        return {'k': 'If', 'cond': cond, 'then': then_, 'else': else_, 'line': line}

    @staticmethod
    def While(cond, body, line=0):
        return {'k': 'While', 'cond': cond, 'body': body, 'line': line}

    @staticmethod
    def DoWhile(body, cond, line=0):
        return {'k': 'DoWhile', 'body': body, 'cond': cond, 'line': line}

    @staticmethod
    def For(init, cond, incr, body, line=0):
        return {'k': 'For', 'init': init, 'cond': cond, 'incr': incr,
                'body': body, 'line': line}

    @staticmethod
    def Return(value=None, line=0):
        return {'k': 'Return', 'value': value, 'line': line}

    @staticmethod
    def Break(line=0):
        return {'k': 'Break', 'line': line}

    @staticmethod
    def Continue(line=0):
        return {'k': 'Continue', 'line': line}

    @staticmethod
    def Call(name, args, line=0):
        return {'k': 'Call', 'name': name, 'args': args, 'line': line}

    @staticmethod
    def BinaryOp(op, left, right):
        return {'k': 'BinaryOp', 'op': op, 'left': left, 'right': right}

    @staticmethod
    def UnaryOp(op, operand):
        return {'k': 'UnaryOp', 'op': op, 'operand': operand}

    @staticmethod
    def PostfixOp(op, operand):
        return {'k': 'PostfixOp', 'op': op, 'operand': operand}

    @staticmethod
    def Literal(kind, value, raw=None):
        return {'k': 'Literal', 'kind': kind, 'value': value, 'raw': raw or str(value)}

    @staticmethod
    def Ident(name, line=0):
        return {'k': 'Ident', 'name': name, 'line': line}

    @staticmethod
    def ArrayAccess(name, idx, line=0):
        return {'k': 'ArrayAccess', 'name': name, 'idx': idx, 'line': line}

    @staticmethod
    def Cast(type_, expr, line=0):
        return {'k': 'Cast', 'type': type_, 'expr': expr, 'line': line}

    @staticmethod
    def ExprStmt(expr, line=0):
        return {'k': 'ExprStmt', 'expr': expr, 'line': line}


# Type system helpers
TYPE_SIZE = {
    'byte': 1, 'word': 2, 'int': 2, 'uint': 2, 'bool': 1,
    'float': 5, 'string': 2, 'void': 0,
    'long': 4, 'ulong': 4, 'dword': 4,
    'q8_8': 2, 'q16_8': 3, 'q8_16': 3, 'q16_16': 4,
    'sq8_8': 2, 'sq16_8': 3, 'sq8_16': 3, 'sq16_16': 4,
}

UNSIGNED_TYPES = frozenset({'byte', 'word', 'uint', 'ulong', 'dword'})
SIGNED_RANGES = {'int': (-32768, 32767), 'long': (-2147483648, 2147483647)}


def is_fixed_type(t):
    import re
    return bool(re.match(r'^q|^sq', t or ''))


def fp_frac_bits(t):
    import re
    m = re.search(r'(\d+)$', t or '')
    return int(m.group(1)) if m else 0


def fp_scale(t):
    return 1 << fp_frac_bits(t)


def is_signed_fp(t):
    return (t or '').startswith('sq')


def is_32_type(t):
    return t in ('long', 'ulong', 'dword')


def promote_types(a, b):
    order = ['byte', 'word', 'int', 'uint', 'q8_8', 'sq8_8',
             'q16_8', 'sq16_8', 'q8_16', 'sq8_16',
             'q16_16', 'sq16_16', 'long', 'ulong', 'dword', 'float']
    if a == 'unknown' or b == 'unknown':
        return 'unknown'
    try:
        ia = order.index(a)
    except ValueError:
        ia = -1
    try:
        ib = order.index(b)
    except ValueError:
        ib = -1
    return a if ia >= ib else b


def builtin_ret_type(name, args):
    float_math = {'sqr', 'log', 'exp', 'floor', 'sin', 'cos', 'tan', 'atn',
                  'float_to_str', 'rnd', 'fadd', 'fsub', 'fmul', 'fdiv', 'fpow'}
    if name in float_math:
        return 'float'
    if name in ('peek',):
        return 'byte'
    if name in ('peek16',):
        return 'word'
    return 'void'
