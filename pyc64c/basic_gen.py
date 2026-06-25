"""BASIC Generator — produces C64 BASIC code from AST"""


class BASICGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.lines = []
        self.cur_line = 10
        self.vars = {}
        self.next_var_id = 0
        self.func_lines = {}

    def _gen_var(self, name):
        if name in self.vars:
            return self.vars[name]
        b_name = name.upper()
        if len(name) <= 2 and not name[0].isdigit():
            b_name = name.upper()
        else:
            b_name = 'V' + str(self.next_var_id)
        reserved = {'IF', 'TO', 'ON', 'OR', 'AS', 'GO', 'GOTO', 'GOSUB',
                     'FOR', 'NEXT', 'REM', 'DATA', 'READ', 'THEN', 'ELSE',
                     'PRINT', 'INPUT', 'SYS', 'POKE', 'PEEK', 'WAIT',
                     'END', 'RETURN', 'STEP', 'NOT', 'AND', 'STOP'}
        if b_name in reserved:
            b_name = 'V' + str(self.next_var_id)
        self.next_var_id += 1
        self.vars[name] = b_name
        return b_name

    def generate(self):
        self.lines = []
        self.cur_line = 10
        self.func_lines.clear()

        # Assign line numbers to functions
        for i, f in enumerate(self.ast['funcs']):
            if f['name'] == 'main':
                self.func_lines[f['name']] = 1000
            else:
                self.func_lines[f['name']] = 2000 + (i * 500)

        # Global inits
        for g in self.ast['globals']:
            if g.get('init'):
                self.add(self._gen_var(g['name']) + ' = ' + self._expr(g['init']))

        # Call main, then END
        if 'main' in self.func_lines:
            self.add('GOSUB ' + str(self.func_lines['main']))
        self.add('END')

        # Function bodies
        for f in self.ast['funcs']:
            self.cur_line = self.func_lines.get(f['name'], 5000)
            self.add('REM FUNCTION ' + f['name'])
            self._block(f['body'])
            self.add('RETURN')

        return '\n'.join(self.lines)

    def add(self, cmd):
        self.lines.append(f'{self.cur_line} {cmd}')
        self.cur_line += 10

    def _block(self, block):
        for s in block.get('stmts', []):
            self._stmt(s)

    def _stmt(self, s):
        if not s:
            return
        if s['k'] == 'ExprStmt':
            self._stmt(s['expr'])
            return

        kind = s['k']

        if kind == 'VarDecl':
            self.add(self._gen_var(s['name']) + ' = ' + (self._expr(s['init']) if s.get('init') else '0'))

        elif kind == 'Assign':
            self.add(self._expr(s['target']) + ' = ' + self._expr(s['value']))

        elif kind == 'If':
            if_line = self.cur_line
            self.add(f'IF NOT ({self._expr(s["cond"])}) THEN GOTO {if_line + 1000}')
            self._block(s['then'])
            end_then = self.cur_line
            if s.get('else'):
                else_start = self.cur_line
                self._patch_line(if_line, lambda l: l.replace(str(if_line + 1000), str(else_start)))
                self.add('GOTO ' + str(end_then + 1000))
                self._block(s['else'])
                end_else = self.cur_line
                self._patch_line(end_then, lambda l: l.replace(str(end_then + 1000), str(end_else)))
            else:
                end_if = self.cur_line
                self._patch_line(if_line, lambda l: l.replace(str(if_line + 1000), str(end_if)))

        elif kind == 'While':
            start_w = self.cur_line
            cond_line = self.cur_line
            self.add('REM WHILE ' + self._expr(s['cond']))
            self._block(s['body'])
            self.add('GOTO ' + str(start_w))
            end_w = self.cur_line
            self._patch_line(cond_line, lambda l: l.replace(
                'REM WHILE ' + self._expr(s['cond']),
                f'IF NOT ({self._expr(s["cond"])}) THEN GOTO {end_w} : REM WHILE'
            ))

        elif kind == 'For':
            self._stmt(s['init'])
            start_f = self.cur_line
            self.add(f'IF NOT ({self._expr(s["cond"])}) THEN GOTO {start_f + 1000}')
            loop_cond_line = self.cur_line - 10
            self._block(s['body'])
            self._stmt(s['incr'])
            self.add('GOTO ' + str(start_f))
            end_f = self.cur_line
            self._patch_line(loop_cond_line, lambda l: l.replace(str(start_f + 1000), str(end_f)))

        elif kind == 'Call':
            self._emit_call(s)

        elif kind == 'Return':
            self.add('RETURN')

    def _emit_call(self, s):
        name = s['name']
        args = s['args']
        if name in ('print', 'println'):
            expr_str = ';'.join(self._expr(a) for a in args)
            self.add(f'PRINT {expr_str}{"" if name == "println" else ";"}')
        elif name in ('print_at',):
            col = self._expr(args[0]) if len(args) > 0 else '0'
            row = self._expr(args[1]) if len(args) > 1 else '0'
            text = self._expr(args[2]) if len(args) > 2 else '""'
            self.add(f'POKE 211,{col}:POKE 214,{row}:SYS 58732:PRINT {text};')
        elif name in self.func_lines:
            self.add(f'GOSUB {self.func_lines[name]}')
        elif name == 'poke':
            self.add(f'POKE {self._expr(args[0])},{self._expr(args[1])}')
        elif name == 'wait':
            self.add(f'FOR TI=1 TO {self._expr(args[0])}:NEXT')
        elif name == 'wait_frames':
            self.add(f'FOR TI=1 TO {self._expr(args[0])}:WAIT 53266,128:NEXT')
        elif name == 'clear_screen':
            self.add('PRINT CHR$(147)')
        elif name == 'border_color':
            self.add(f'POKE 53280,{self._expr(args[0])}')
        elif name == 'screen_color':
            self.add(f'POKE 53281,{self._expr(args[0])}')
        elif name in ('peek',):
            self.add(f'PEEK({self._expr(args[0])})')
        else:
            self.add(f'REM CALL {name}')

    def _expr(self, e):
        if e is None:
            return '0'
        kind = e['k']
        if kind == 'Literal':
            if e['kind'] == 'str':
                return '"' + e['value'] + '"'
            if e['kind'] == 'bool':
                return '-1' if e['value'] == 1 else '0'
            return str(e['value'])
        if kind == 'Ident':
            return self._gen_var(e['name'])
        if kind == 'Call':
            return self._expr_call(e)
        if kind == 'BinaryOp':
            return self._expr_binary(e)
        if kind == 'UnaryOp':
            op = e['op']
            if op == '!':
                return 'NOT (' + self._expr(e['operand']) + ')'
            return op + '(' + self._expr(e['operand']) + ')'
        return '0'

    def _expr_call(self, e):
        name = e['name']
        args = e['args']
        if name == 'peek':
            return 'PEEK(' + self._expr(args[0]) + ')'
        return '0'

    def _expr_binary(self, e):
        op = e['op']
        left = self._expr(e['left'])
        right = self._expr(e['right'])
        op_map = {
            '&&': 'AND', '||': 'OR', '&': 'AND', '|': 'OR',
            '!=': '<>', '==': '=', '<': '<', '>': '>',
            '<=': '<=', '>=': '>=', '+': '+', '-': '-',
            '*': '*', '/': '/',
        }
        if op == '%':
            return f'({left}-INT({left}/{right})*{right})'
        mapped = op_map.get(op, op)
        return f'({left} {mapped} {right})'

    def _patch_line(self, line_num, transform):
        prefix = str(line_num) + ' '
        for i, l in enumerate(self.lines):
            if l.startswith(prefix):
                self.lines[i] = transform(l)
