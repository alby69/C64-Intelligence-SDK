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
        elif name == 'bitmap_clear':
            self.add('FOR I=8192 TO 16191:POKE I,0:NEXT')
        elif name == 'border_color':
            self.add(f'POKE 53280,{self._expr(args[0])}')
        elif name == 'screen_color':
            self.add(f'POKE 53281,{self._expr(args[0])}')
        elif name == 'sprite_enable':
            idx = self._expr(args[0])
            on = self._expr(args[1])
            self.add(f'V=PEEK(53269):IF {on} THEN POKE 53269,V OR (2^{idx}) ELSE POKE 53269,V AND (255-2^{idx})')
        elif name == 'sprite_pos':
            idx = self._expr(args[0])
            x = self._expr(args[1])
            y = self._expr(args[2])
            self.add(f'POKE 53248+{idx}*2,{x} AND 255:POKE 53249+{idx}*2,{y}')
            self.add(f'V=PEEK(53264):IF {x}>255 THEN POKE 53264,V OR (2^{idx}) ELSE POKE 53264,V AND (255-2^{idx})')
        elif name == 'sprite_color':
            self.add(f'POKE 53287+{self._expr(args[0])},{self._expr(args[1])}')
        elif name == 'sprite_multicolor':
            idx = self._expr(args[0])
            on = self._expr(args[1])
            self.add(f'V=PEEK(53276):IF {on} THEN POKE 53276,V OR (2^{idx}) ELSE POKE 53276,V AND (255-2^{idx})')
        elif name == 'sprite_config':
            self.add(f'POKE 53285,{self._expr(args[0])}:POKE 53286,{self._expr(args[1])}')
        elif name == 'bitmap_mode':
            on = self._expr(args[0])
            self.add(f'V=PEEK(53265):IF {on} THEN POKE 53265,V OR 32 ELSE POKE 53265,V AND 223')
        elif name == 'multicolor_mode':
            on = self._expr(args[0])
            self.add(f'V=PEEK(53270):IF {on} THEN POKE 53270,V OR 16 ELSE POKE 53270,V AND 239')
        elif name == 'sprite_stretch':
            idx = self._expr(args[0])
            h = self._expr(args[1])
            v = self._expr(args[2])
            self.add(f'V=PEEK(53277):IF {h} THEN POKE 53277,V OR (2^{idx}) ELSE POKE 53277,V AND (255-2^{idx})')
            self.add(f'V=PEEK(53271):IF {v} THEN POKE 53271,V OR (2^{idx}) ELSE POKE 53271,V AND (255-2^{idx})')
        elif name == 'sprite_pointer':
            idx = self._expr(args[0])
            ptr = self._expr(args[1])
            self.add(f'POKE 2040+{idx},{ptr}')
        elif name == 'sid_volume':
            self.add(f'POKE 54296,(PEEK(54296) AND 240) OR ({self._expr(args[0])} AND 15)')
        elif name == 'sid_setup':
            voice = self._expr(args[0])
            a = self._expr(args[1])
            d = self._expr(args[2])
            s = self._expr(args[3])
            r = self._expr(args[4])
            self.add(f'POKE 54277+{voice}*7,({a}*16)+{d}:POKE 54278+{voice}*7,({s}*16)+{r}')
        elif name == 'sid_freq':
            voice = self._expr(args[0])
            freq = self._expr(args[1])
            self.add(f'POKE 54272+{voice}*7,{freq} AND 255:POKE 54273+{voice}*7,{freq}/256')
        elif name == 'sid_pw':
            voice = self._expr(args[0])
            pw = self._expr(args[1])
            self.add(f'POKE 54274+{voice}*7,{pw} AND 255:POKE 54275+{voice}*7,{pw}/256')
        elif name == 'sid_gate':
            voice = self._expr(args[0])
            wf = self._expr(args[1])
            on = self._expr(args[2])
            self.add(f'POKE 54276+{voice}*7,{wf} OR {on}')
        elif name == 'sid_filter':
            cutoff = self._expr(args[0])
            res = self._expr(args[1])
            mode = self._expr(args[2])
            self.add(f'POKE 54293,{cutoff} AND 7:POKE 54294,{cutoff}/8')
            self.add(f'POKE 54295,({res}*16) OR (PEEK(54295) AND 15)')
            # mode also contains voices to filter in lower 4 bits
            self.add(f'POKE 54296,(PEEK(54296) AND 15) OR ({mode} AND 240)')
            self.add(f'POKE 54295,(PEEK(54295) AND 240) OR ({mode} AND 15)')
        elif name == 'sid_clear':
            self.add('FOR I=54272 TO 54296:POKE I,0:NEXT')
        elif name == 'vic_bank':
            bank = self._expr(args[0])
            self.add(f'POKE 56576,(PEEK(56576) AND 252) OR (3-({bank} AND 3))')
        elif name == 'screen_memory':
            addr = self._expr(args[0])
            self.add(f'POKE 53272,(PEEK(53272) AND 15) OR (({addr}/1024) AND 15)*16')
        elif name == 'character_memory':
            addr = self._expr(args[0])
            self.add(f'POKE 53272,(PEEK(53272) AND 240) OR (({addr}/1024) AND 14)')
        elif name == 'sprite_collision_sprite':
            self.add('V=PEEK(53278)')
        elif name == 'sprite_collision_data':
            self.add('V=PEEK(53279)')
        elif name == 'raster_line':
            self.add('V=PEEK(53266)')
        elif name == 'sid_random':
            self.add('V=PEEK(54299)')
        elif name == 'raster_irq':
            line = self._expr(args[0])
            self.add(f'POKE 53266,{line} AND 255:V=PEEK(53265):IF {line}>255 THEN POKE 53265,V OR 128 ELSE POKE 53265,V AND 127')
        elif name == 'scroll_x':
            self.add(f'POKE 53270,(PEEK(53270) AND 248) OR ({self._expr(args[0])} AND 7)')
        elif name == 'scroll_y':
            self.add(f'POKE 53265,(PEEK(53265) AND 248) OR ({self._expr(args[0])} AND 7)')
        elif name == 'screen_size':
            cols = self._expr(args[0])
            rows = self._expr(args[1])
            self.add(f'V=PEEK(53270):IF {cols}=40 THEN POKE 53270,V OR 8 ELSE POKE 53270,V AND 247')
            self.add(f'V=PEEK(53265):IF {rows}=25 THEN POKE 53265,V OR 8 ELSE POKE 53265,V AND 247')
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
        if name == 'sprite_collision_sprite':
            return 'PEEK(53278)'
        if name == 'sprite_collision_data':
            return 'PEEK(53279)'
        if name == 'raster_line':
            return 'PEEK(53266)'
        if name == 'sid_random':
            return 'PEEK(54299)'
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
