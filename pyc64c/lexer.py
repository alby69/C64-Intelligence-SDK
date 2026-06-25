"""Python-like C64PY Lexer — ported from lexer_py.js"""

from .token_types import (
    TT, Token, C64PY_KEYWORDS, C64PY_TYPES, C64PY_BUILTINS
)


class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(msg)
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, src):
        self.src = src
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self.errors = []
        self.indent_stack = [0]
        self.at_start_of_line = True

    def peek(self, off=0):
        i = self.pos + off
        return self.src[i] if 0 <= i < len(self.src) else ''

    def eof(self):
        return self.pos >= len(self.src)

    def advance(self):
        c = self.src[self.pos]
        self.pos += 1
        if c == '\n':
            self.line += 1
            self.col = 1
            self.at_start_of_line = True
        else:
            self.col += 1
        return c

    def _tok(self, type_, value, line=None, col=None):
        return Token(type_, value, line or self.line, col or self.col)

    def _err(self, msg, line=None, col=None):
        self.errors.append({
            'msg': msg,
            'line': line or self.line,
            'col': col or self.col
        })

    def tokenize(self):
        while not self.eof():
            line = self.line
            col = self.col

            if self.at_start_of_line:
                self.at_start_of_line = False
                indent = 0
                while not self.eof() and self.peek() in (' ', '\t'):
                    c = self.advance()
                    indent += 4 if c == '\t' else 1
                if self.eof():
                    break
                if self.peek() == '\n':
                    self.advance()
                    self.at_start_of_line = True
                    continue
                if self.peek() == '#':
                    while not self.eof() and self.peek() != '\n':
                        self.advance()
                    if self.peek() == '\n':
                        self.advance()
                        self.at_start_of_line = True
                    continue

                cur_indent = self.indent_stack[-1]
                if indent > cur_indent:
                    self.indent_stack.append(indent)
                    self.tokens.append(self._tok(TT.INDENT, None, line, col))
                else:
                    while indent < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        self.tokens.append(self._tok(TT.DEDENT, None, line, col))

            while not self.eof() and self.peek() in (' ', '\t'):
                self.advance()
            if self.eof():
                break

            if self.peek() == '\n':
                self.tokens.append(self._tok(TT.NEWLINE, '\n', self.line, self.col))
                self.advance()
                continue

            if self.peek() == '#':
                while not self.eof() and self.peek() != '\n':
                    self.advance()
                continue

            c = self.peek()

            # Hex literal: $xxxx or 0x...
            if c == '$' or (c == '0' and self.peek(1) in ('x', 'X')):
                start = self.pos
                if self.peek() == '$':
                    self.advance()
                else:
                    self.advance()
                    self.advance()
                while self.peek() and self.peek() in '0123456789ABCDEFabcdef':
                    self.advance()
                raw = self.src[start:self.pos]
                val = int(raw.replace('$', '').replace('0x', '').replace('0X', ''), 16)
                t = self._tok(TT.HEX_LIT, val, line, col)
                t.raw = raw
                self.tokens.append(t)
                continue

            # Number: int or float
            if c and c.isdigit():
                num = ''
                while self.peek() and self.peek().isdigit():
                    num += self.advance()
                if self.peek() == '.':
                    num += self.advance()
                    while self.peek() and self.peek().isdigit():
                        num += self.advance()
                    if self.peek() in ('e', 'E'):
                        num += self.advance()
                        if self.peek() in ('+', '-'):
                            num += self.advance()
                        while self.peek() and self.peek().isdigit():
                            num += self.advance()
                    self.tokens.append(self._tok(TT.FLOAT_LIT, float(num), line, col))
                    continue
                self.tokens.append(self._tok(TT.INT_LIT, int(num), line, col))
                continue

            # String literal (double or single quotes)
            if c in ('"', "'"):
                quote = c
                self.advance()
                s = []
                while not self.eof() and self.peek() != quote:
                    if self.peek() == '\\':
                        self.advance()
                        s.append(self.advance())
                    else:
                        s.append(self.advance())
                if not self.eof():
                    self.advance()
                self.tokens.append(self._tok(TT.STR_LIT, ''.join(s), line, col))
                continue

            # Identifier / keyword
            if c and (c.isalpha() or c == '_'):
                ident = ''
                while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
                    ident += self.advance()
                if ident in ('and',):
                    self.tokens.append(self._tok(TT.AND, ident, line, col))
                elif ident in ('or',):
                    self.tokens.append(self._tok(TT.OR, ident, line, col))
                elif ident in ('not',):
                    self.tokens.append(self._tok(TT.NOT, ident, line, col))
                elif ident in C64PY_KEYWORDS:
                    self.tokens.append(self._tok(TT.KEYWORD, ident, line, col))
                elif ident in C64PY_TYPES:
                    self.tokens.append(self._tok(TT.TYPE, ident, line, col))
                elif ident in C64PY_BUILTINS:
                    self.tokens.append(self._tok(TT.BUILTIN, ident, line, col))
                else:
                    self.tokens.append(self._tok(TT.IDENT, ident, line, col))
                continue

            # Two-char operators
            two = c + (self.peek(1) or '')
            if two == '->':
                self.advance()
                self.advance()
                self.tokens.append(self._tok(TT.ARROW, '->', line, col))
                continue
            if two in ('==', '!=', '<=', '>=', '<<', '>>', '&&', '||'):
                self.advance()
                self.advance()
                if two == '&&':
                    self.tokens.append(self._tok(TT.AND, '&&', line, col))
                elif two == '||':
                    self.tokens.append(self._tok(TT.OR, '||', line, col))
                else:
                    self.tokens.append(self._tok(TT.CMP, two, line, col))
                continue

            # Single-char operators
            if c in '<>':
                self.advance()
                self.tokens.append(self._tok(TT.CMP, c, line, col))
                continue
            if c in '+-*/%&|^':
                self.advance()
                self.tokens.append(self._tok(TT.OP, c, line, col))
                continue
            if c == '=':
                self.advance()
                self.tokens.append(self._tok(TT.ASSIGN, '=', line, col))
                continue
            if c == '!':
                self.advance()
                self.tokens.append(self._tok(TT.NOT, '!', line, col))
                continue

            punct = {
                '(': TT.LPAREN, ')': TT.RPAREN,
                '[': TT.LBRACK, ']': TT.RBRACK,
                ',': TT.COMMA, '.': TT.DOT, ':': TT.COLON,
            }
            if c in punct:
                self.advance()
                self.tokens.append(self._tok(punct[c], c, line, col))
                continue

            self._err(f"Carattere inatteso: {c}", line, col)
            self.advance()

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(self._tok(TT.DEDENT, None, self.line, self.col))
        self.tokens.append(self._tok(TT.EOF, None, self.line, self.col))
        return self.tokens, self.errors
