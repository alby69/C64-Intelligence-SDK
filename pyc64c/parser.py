"""Python-like Parser — ported from parser_py.js"""

from .token_types import TT
from .ast_nodes import N


class ParseError(Exception):
    def __init__(self, msg, line=0, col=0):
        super().__init__(msg)
        self.line = line
        self.col = col


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []
        self.node_count = 0

    def peek(self, off=0):
        i = self.pos + off
        return self.tokens[i] if i < len(self.tokens) else self.tokens[-1]

    def cur(self):
        return self.peek(0)

    def is_eof(self):
        return self.cur().type == TT.EOF

    def check(self, type_, val=None):
        t = self.cur()
        return t.type == type_ and (val is None or t.value == val)

    def check_kw(self, kw):
        return self.check(TT.KEYWORD, kw)

    def check_type(self):
        return self.cur().type == TT.TYPE

    def advance(self):
        t = self.cur()
        if not self.is_eof():
            self.pos += 1
        return t

    def expect(self, type_, val=None):
        if not self.check(type_, val):
            t = self.cur()
            expected = val or type_
            raise ParseError(f"Expected {expected}, found {t.value or t.type}", t.line, t.col)
        return self.advance()

    def expect_kw(self, kw):
        return self.expect(TT.KEYWORD, kw)

    def try_eat(self, type_, val=None):
        if self.check(type_, val):
            self.advance()
            return True
        return False

    def mk(self, n):
        self.node_count += 1
        return n

    def _err(self, msg, tok=None):
        tok = tok or self.cur()
        self.errors.append({'msg': msg, 'line': tok.line or 0, 'col': tok.col or 0})

    def sync(self):
        while not self.is_eof():
            t = self.cur()
            if t.type in (TT.NEWLINE, TT.DEDENT):
                return
            if t.type == TT.KEYWORD and t.value in ('if', 'elif', 'else', 'while', 'def', 'for'):
                return
            self.advance()

    def parse(self):
        globals_ = []
        funcs = []
        while not self.is_eof():
            while self.try_eat(TT.NEWLINE):
                pass
            if self.is_eof():
                break
            try:
                if self.check_kw('def'):
                    funcs.append(self.parse_func_decl())
                elif self.check(TT.IDENT) and self.peek(1).type == TT.COLON:
                    globals_.append(self.parse_var_decl())
                else:
                    self._err("Global declaration expected (def or var:type)")
                    self.advance()
            except ParseError as e:
                self.errors.append({'msg': e.args[0], 'line': e.line, 'col': e.col})
                self.sync()
        return N.Program(globals_, funcs)

    def parse_suite(self):
        if self.check(TT.NEWLINE) or self.check(TT.INDENT):
            while self.try_eat(TT.NEWLINE):
                pass
            return self.parse_block()
        s = self.parse_stmt()
        return [s] if s else []

    def parse_block(self):
        self.expect(TT.INDENT)
        stmts = []
        while not self.is_eof() and not self.check(TT.DEDENT):
            while self.try_eat(TT.NEWLINE):
                pass
            if self.check(TT.DEDENT):
                break
            s = self.parse_stmt()
            if s:
                stmts.append(s)
            while self.try_eat(TT.NEWLINE):
                pass
        self.expect(TT.DEDENT)
        return stmts

    def parse_stmt(self):
        t = self.cur()
        if self.check_kw('if'):
            return self.parse_if()
        if self.check_kw('while'):
            return self.parse_while()
        if self.check_kw('for'):
            return self.parse_for()
        if self.check_kw('return'):
            l = t.line
            self.advance()
            val = None
            if not self.check(TT.NEWLINE) and not self.check(TT.DEDENT):
                val = self.parse_expr()
            return self.mk(N.Return(val, l))
        if self.check_kw('pass'):
            self.advance()
            return None
        if self.check_kw('break'):
            self.advance()
            return self.mk(N.Break(t.line))
        if self.check_kw('continue'):
            self.advance()
            return self.mk(N.Continue(t.line))
        if self.check(TT.IDENT) and self.peek(1).type == TT.COLON:
            return self.parse_var_decl()
        e = self.parse_expr()
        if self.try_eat(TT.ASSIGN):
            val = self.parse_expr()
            return self.mk(N.Assign(e, val, t.line))
        return self.mk(N.ExprStmt(e, t.line))

    def parse_func_decl(self):
        line = self.cur().line
        self.expect_kw('def')
        name = self.expect(TT.IDENT).value
        self.expect(TT.LPAREN)
        params = []
        if not self.check(TT.RPAREN):
            while True:
                p_name = self.expect(TT.IDENT).value
                self.expect(TT.COLON)
                p_type = self.advance().value
                params.append({'name': p_name, 'type': p_type, 'isArr': False})
                if not self.try_eat(TT.COMMA):
                    break
        self.expect(TT.RPAREN)
        ret = 'void'
        if self.try_eat(TT.ARROW):
            ret = self.advance().value
        self.expect(TT.COLON)
        body = self.parse_suite()
        return self.mk(N.FuncDecl(name, params, ret, N.Block(body), line))

    def parse_var_decl(self):
        line = self.cur().line
        name = self.expect(TT.IDENT).value
        self.expect(TT.COLON)
        type_ = self.advance().value
        is_arr = False
        arr_size = 0
        if self.try_eat(TT.LBRACK):
            arr_size = self.expect(TT.INT_LIT).value
            self.expect(TT.RBRACK)
            is_arr = True
        init = None
        if self.try_eat(TT.ASSIGN):
            init = self.parse_expr()
        return self.mk(N.VarDecl(type_, name, init, is_arr, arr_size, None, line))

    def parse_if(self):
        line = self.cur().line
        self.expect_kw('if')
        cond = self.parse_expr()
        self.expect(TT.COLON)
        then_b = self.parse_suite()
        else_b = None
        if self.check_kw('elif'):
            else_b = [self.parse_if()]
        elif self.check_kw('else'):
            self.expect_kw('else')
            self.expect(TT.COLON)
            else_b = self.parse_suite()
        return self.mk(N.If(cond, N.Block(then_b), N.Block(else_b) if else_b else None, line))

    def parse_while(self):
        line = self.cur().line
        self.expect_kw('while')
        cond = self.parse_expr()
        self.expect(TT.COLON)
        body = self.parse_suite()
        return self.mk(N.While(cond, N.Block(body), line))

    def parse_for(self):
        line = self.cur().line
        self.expect_kw('for')
        id_ = self.expect(TT.IDENT).value
        self.expect_kw('in')
        if self.check(TT.BUILTIN, 'range'):
            self.advance()
        else:
            self.expect(TT.IDENT, 'range')
        self.expect(TT.LPAREN)
        start = self.parse_expr()
        self.expect(TT.COMMA)
        end = self.parse_expr()
        self.expect(TT.RPAREN)
        self.expect(TT.COLON)
        body = self.parse_suite()
        init = N.Assign(N.Ident(id_, line), start, line)
        cond = N.BinaryOp('<', N.Ident(id_, line), end)
        incr = N.Assign(N.Ident(id_, line), N.BinaryOp('+', N.Ident(id_, line), N.Literal('int', 1, '1')), line)
        return self.mk(N.For(init, cond, incr, N.Block(body), line))

    def parse_expr(self):
        return self.parse_logical()

    def parse_logical(self):
        e = self.parse_cmp()
        while self.check(TT.AND) or self.check(TT.OR):
            op = self.advance().value
            r = self.parse_cmp()
            e = self.mk(N.BinaryOp(op, e, r))
        return e

    def parse_cmp(self):
        e = self.parse_bitwise()
        while self.check(TT.CMP):
            op = self.advance().value
            r = self.parse_bitwise()
            e = self.mk(N.BinaryOp(op, e, r))
        return e

    def parse_bitwise(self):
        e = self.parse_shift()
        while self.check(TT.OP) and self.cur().value in ('&', '|', '^'):
            op = self.advance().value
            r = self.parse_shift()
            e = self.mk(N.BinaryOp(op, e, r))
        return e

    def parse_shift(self):
        e = self.parse_additive()
        while self.check(TT.OP) and self.cur().value in ('<<', '>>'):
            op = self.advance().value
            r = self.parse_additive()
            e = self.mk(N.BinaryOp(op, e, r))
        return e

    def parse_additive(self):
        e = self.parse_multiplicative()
        while self.check(TT.OP) and self.cur().value in ('+', '-'):
            op = self.advance().value
            r = self.parse_multiplicative()
            e = self.mk(N.BinaryOp(op, e, r))
        return e

    def parse_multiplicative(self):
        e = self.parse_unary()
        while self.check(TT.OP) and self.cur().value in ('*', '/', '%'):
            op = self.advance().value
            r = self.parse_unary()
            e = self.mk(N.BinaryOp(op, e, r))
        return e

    def parse_unary(self):
        if self.check(TT.NOT) or (self.check(TT.OP) and self.cur().value == '-'):
            op = self.advance().value
            r = self.parse_unary()
            return self.mk(N.UnaryOp(op, r))
        return self.parse_primary()

    def parse_primary(self):
        t = self.cur()
        if self.try_eat(TT.LPAREN):
            e = self.parse_expr()
            self.expect(TT.RPAREN)
            return e
        if self.check(TT.INT_LIT):
            return self.mk(N.Literal('int', self.advance().value, str(t.value)))
        if self.check(TT.HEX_LIT):
            return self.mk(N.Literal('int', self.advance().value, t.raw))
        if self.check(TT.FLOAT_LIT):
            return self.mk(N.Literal('float', self.advance().value, str(t.value)))
        if self.check(TT.STR_LIT):
            return self.mk(N.Literal('str', self.advance().value, '"' + t.value + '"'))
        if self.check_kw('True'):
            self.advance()
            return self.mk(N.Literal('bool', 1, 'True'))
        if self.check_kw('False'):
            self.advance()
            return self.mk(N.Literal('bool', 0, 'False'))
        if self.check(TT.IDENT):
            name = self.advance().value
            if self.try_eat(TT.LPAREN):
                args = []
                if not self.check(TT.RPAREN):
                    while True:
                        args.append(self.parse_expr())
                        if not self.try_eat(TT.COMMA):
                            break
                self.expect(TT.RPAREN)
                return self.mk(N.Call(name, args, t.line))
            if self.try_eat(TT.LBRACK):
                idx = self.parse_expr()
                self.expect(TT.RBRACK)
                return self.mk(N.ArrayAccess(name, idx, t.line))
            return self.mk(N.Ident(name, t.line))
        if self.check(TT.TYPE):
            type_ = self.advance().value
            if self.try_eat(TT.LPAREN):
                expr = self.parse_expr()
                self.expect(TT.RPAREN)
                return self.mk(N.Cast(type_, expr, t.line))
            return self.mk(N.Ident(type_, t.line))
        if self.check(TT.BUILTIN):
            name = self.advance().value
            self.expect(TT.LPAREN)
            args = []
            if not self.check(TT.RPAREN):
                while True:
                    args.append(self.parse_expr())
                    if not self.try_eat(TT.COMMA):
                        break
            self.expect(TT.RPAREN)
            return self.mk(N.Call(name, args, t.line))
        raise ParseError(f"Invalid expression: {t.value or t.type}", t.line, t.col)
