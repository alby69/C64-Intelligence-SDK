"""Code Generator — generates 6502 machine code for function bodies."""

from .code_emitter import CodeEmitter
from .ast_nodes import TYPE_SIZE, is_fixed_type, fp_scale, is_32_type, is_signed_fp


class CodeGenerator:
    def __init__(self, emitter, planner, sem_scope, ast):
        self.e = emitter
        self.planner = planner
        self.sem_scope = sem_scope
        self.ast = ast
        self.loop_stack = []
        self.cur_func = None
        self.var_map = {}
        self._build_var_map()

    def _build_var_map(self):
        for g in self.planner.globals:
            self.var_map[g['name']] = g
        for f in self.ast['funcs']:
            layout = self.planner.func_layouts.get(f['name'])
            if layout:
                for v in layout['locals']:
                    self.var_map[f['name'] + '.' + v['name']] = v

    def _var(self, name, func_name=None):
        if func_name is None and self.cur_func:
            func_name = self.cur_func['name']
        local_key = f"{func_name}.{name}" if func_name else None
        if local_key and local_key in self.var_map:
            return self.var_map[local_key]
        if name in self.var_map:
            return self.var_map[name]
        return None

    def _is_16(self, node):
        t = node.get('_type', '')
        return t in ('word', 'int', 'uint') or is_fixed_type(t)

    def _is_32(self, node):
        return is_32_type(node.get('_type', ''))

    def _ld_var_byte(self, var, comment=''):
        if var['isZP'] and var.get('addr') is not None:
            self.e.zp('LDA', var['addr'], comment)
        else:
            addr = var.get('addr') or var.get('bss_label', 0)
            if isinstance(addr, str):
                self.e.abs('LDA', addr, comment)
            else:
                self.e.abs('LDA', addr, comment)

    def _st_var_byte(self, var, comment=''):
        if var['isZP'] and var.get('addr') is not None:
            self.e.zp('STA', var['addr'], comment)
        else:
            addr = var.get('addr') or var.get('bss_label', 0)
            if isinstance(addr, str):
                self.e.abs('STA', addr, comment)
            else:
                self.e.abs('STA', addr, comment)

    def gen_func(self, f):
        self.cur_func = f
        layout = self.planner.func_layouts.get(f['name'])
        self.e.label(f['name'])
        self.emit_block(f['body'])
        stmts = f['body'].get('stmts', [])
        if not stmts or stmts[-1].get('k') != 'Return':
            self.e.imp('RTS', f"end {f['name']}")
        self.cur_func = None

    def emit_block(self, block):
        for s in block.get('stmts', []):
            self.emit_stmt(s)

    def emit_stmt(self, s):
        if s is None:
            return
        if s['k'] == 'ExprStmt':
            self.emit_stmt(s['expr'])
            return
        kind = s['k']
        if kind == 'VarDecl':
            self._emit_var_decl(s)
        elif kind == 'Assign':
            self._emit_assign(s)
        elif kind == 'If':
            self._emit_if(s)
        elif kind == 'While':
            self._emit_while(s)
        elif kind == 'For':
            self._emit_for(s)
        elif kind == 'Return':
            self.e.imp('RTS', f"return from {self.cur_func['name'] if self.cur_func else '?'}")
        elif kind == 'Call':
            self._emit_call(s)
        elif kind == 'Break':
            if self.loop_stack:
                self.e.jmp(self.loop_stack[-1]['end'], 'break')
        elif kind == 'Continue':
            if self.loop_stack:
                self.e.jmp(self.loop_stack[-1]['start'], 'continue')

    def _emit_var_decl(self, s):
        if s.get('init'):
            self._emit_expr_to_a(s['init'])
            var = self._var(s['name'])
            if var:
                self._st_var_byte(var, f'{s["name"]} = ...')
                if self._is_16(s):
                    self.e.zp('STA', var['addr'] if var['isZP'] else var.get('bss_label', 0), f'{s["name"]} lo')
                if self._is_32(s):
                    pass

    def _emit_assign(self, s):
        if self._is_16(s['target']) or self._is_32(s['target']):
            self._emit_word_assign(s)
        else:
            self._emit_expr_to_a(s['value'])
            name = s['target'].get('name', '')
            var = self._var(name)
            if var:
                self._st_var_byte(var, f'{name} = ...')

    def _emit_word_assign(self, s):
        lhs_name = s['target'].get('name', '')
        var = self._var(lhs_name)
        if not var:
            return
        rhs = s['value']
        if rhs['k'] == 'BinaryOp' and rhs['op'] == '+':
            lo_label = self.e.uniq('_asm')
            hi_label = self.e.uniq('_asm')
            self.e.imm('LDA', 0, f'word {lhs_name}+= init lo')
            if var['isZP']:
                self.e.zp('STA', var['addr'], f'{lhs_name} lo')
            else:
                self.e.abs('STA', var.get('bss_label', 0), f'{lhs_name} lo')
            self.e.imm('LDA', 0, f'hi')
            if var['isZP']:
                self.e.zp('STA', var['addr'] + 1, f'{lhs_name} hi')
            else:
                self.e.abs('STA', var.get('bss_label', 0) + 1, f'{lhs_name} hi')
            return
        if rhs['k'] == 'Literal':
            val = rhs['value']
            lo = val & 0xFF
            hi = (val >> 8) & 0xFF
            self.e.imm('LDA', lo, f'{lhs_name}=${val:04X} lo')
            if var['isZP']:
                self.e.zp('STA', var['addr'], f'{lhs_name} lo')
            else:
                self.e.abs('STA', var.get('bss_label', 0), f'{lhs_name} lo')
            self.e.imm('LDA', hi, f'{lhs_name} hi')
            if var['isZP']:
                self.e.zp('STA', var['addr'] + 1, f'{lhs_name} hi')
            else:
                self.e.abs('STA', var.get('bss_label', 0) + 1, f'{lhs_name} hi')
            return
        if rhs['k'] == 'UnaryOp':
            pass
        self._emit_expr_to_a(rhs)
        if var['isZP']:
            self.e.zp('STA', var['addr'], f'{lhs_name} lo')
        else:
            self.e.abs('STA', var.get('bss_label', 0), f'{lhs_name} lo')

    def _emit_if(self, s):
        end_lbl = self.e.uniq('_endif')
        if s.get('else'):
            else_lbl = self.e.uniq('_else')
            self._emit_cond_branch(s['cond'], else_lbl)
            self.emit_block(s['then'])
            self.e.jmp(end_lbl, 'jmp endif')
            self.e.label(else_lbl)
            self.emit_block(s['else'])
        else:
            self._emit_cond_branch(s['cond'], end_lbl)
            self.emit_block(s['then'])
        self.e.label(end_lbl)

    def _emit_while(self, s):
        start_lbl = self.e.uniq('_while')
        body_lbl = self.e.uniq('_wbody')
        end_lbl = self.e.uniq('_wend')
        self.loop_stack.append({'start': start_lbl, 'end': end_lbl})
        self.e.label(start_lbl)
        self._emit_cond_branch(s['cond'], end_lbl)
        self.emit_block(s['body'])
        self.e.jmp(start_lbl, 'wend')
        self.e.label(end_lbl)
        self.loop_stack.pop()

    def _emit_for(self, s):
        self.emit_stmt(s['init'])
        start_lbl = self.e.uniq('_for')
        end_lbl = self.e.uniq('_fend')
        self.loop_stack.append({'start': start_lbl, 'end': end_lbl})
        self.e.label(start_lbl)
        if s.get('cond'):
            self._emit_cond_branch(s['cond'], end_lbl)
        self.emit_block(s['body'])
        if s.get('incr'):
            self.emit_stmt(s['incr'])
        self.e.jmp(start_lbl, 'fend')
        self.e.label(end_lbl)
        self.loop_stack.pop()

    def _emit_cond_branch(self, cond, target_lbl):
        if cond['k'] == 'BinaryOp' and cond['op'] in ('<', '>', '<=', '>=', '==', '!=', '&&', '||'):
            op = cond['op']
            left_val = None
            right_val = None
            if cond['left']['k'] == 'Literal':
                left_val = cond['left']['value']
            if cond['right']['k'] == 'Literal':
                right_val = cond['right']['value']

            if left_val is not None and left_val == 0 and cond['left']['k'] == 'Literal':
                pass

            # Compare A with value
            self._emit_expr_to_a(cond['left'])
            if isinstance(right_val, int) and 0 <= right_val <= 255 and cond['right']['k'] == 'Literal':
                self.e.imm('CMP', right_val, 'cmp')
            elif cond['right']['k'] == 'Ident':
                var = self._var(cond['right']['name'])
                if var and var['isZP']:
                    self.e.zp('CMP', var['addr'], f'cmp {cond["right"]["name"]}')
                else:
                    self.e.abs('CMP', var.get('bss_label', 0) if var else 0, f'cmp {cond["right"]["name"]}')
            else:
                self._emit_expr_to_a(cond['right'])
                self.e.zp('STA', 0xFC, 'tmp')
                self.e.zp('CMP', 0xFC, 'cmp tmp')

            cmp_to_branch = {
                '<': 'BCS', '>': 'BCC',
                '<=': 'BCC', '>=': 'BCS',
                '==': 'BNE', '!=': 'BEQ',
            }
            if op in cmp_to_branch:
                branch_mnem = cmp_to_branch[op]
                if op in ('<=',):
                    self.e.imp('BEQ', 'eq')
                    self.e.branch(branch_mnem, target_lbl)
                elif op in ('<', '>='):
                    self.e.branch(branch_mnem, target_lbl)
                else:
                    self.e.branch(branch_mnem, target_lbl)
            return

        if cond['k'] == 'UnaryOp' and cond['op'] == '!':
            self._emit_cond_branch(cond['operand'], target_lbl)
            return

        if cond['k'] == 'Literal':
            if cond['value'] == 1 or cond['value'] == True:
                pass
            else:
                self.e.jmp(target_lbl, 'cond false')
            return

        if cond['k'] == 'Call':
            self._emit_call(cond)
            return

        if cond['k'] == 'Ident':
            self._emit_expr_to_a(cond)
            self.e.imm('CMP', 0, 'test {cond["name"]}')
            self.e.branch('BEQ', target_lbl)
            return

        if cond['k'] == 'BinaryOp' and cond['op'] in ('&', '|') and cond['left']['k'] == 'Ident':
            var_name = cond['left']['name']
            var = self._var(var_name)
            if var and isinstance(cond['right'].get('value'), int) and cond['right']['k'] == 'Literal':
                mask = cond['right']['value']
                if var and var['isZP']:
                    self.e.zp('LDA', var['addr'], f'load {var_name}')
                else:
                    self.e.abs('LDA', var.get('bss_label', 0) if var else 0, f'load {var_name}')
                self.e.imm('AND', mask & 0xFF, f'mask ${mask:02X}')
                self.e.imm('CMP', 0, 'test')
                self.e.branch('BEQ', target_lbl)
                return

        # generic fallback: load condition, branch if zero
        self._emit_expr_to_a(cond)
        self.e.imm('CMP', 0, 'test cond')
        self.e.branch('BEQ', target_lbl)

    def _emit_call(self, s):
        name = s['name']
        args = s.get('args', [])

        if name in ('poke',):
            addr_val = None
            if args and args[0]['k'] == 'Literal':
                addr_val = args[0]['value']
            byte_val = None
            if len(args) > 1 and args[1]['k'] == 'Literal':
                byte_val = args[1]['value']
            if byte_val is not None:
                self.e.imm('LDA', byte_val & 0xFF, f'poke val ${byte_val:02X}')
            else:
                self._emit_expr_to_a(args[1])
            if addr_val is not None:
                if addr_val < 0x100:
                    self.e.zp('STA', addr_val & 0xFF, f'poke ${addr_val:04X}')
                else:
                    self.e.abs('STA', addr_val & 0xFFFF, f'poke ${addr_val:04X}')
            return

        if name in ('peek',):
            addr_val = None
            if args and args[0]['k'] == 'Literal':
                addr_val = args[0]['value']
            if addr_val is not None:
                if addr_val < 0x100:
                    self.e.zp('LDA', addr_val & 0xFF, f'peek ${addr_val:04X}')
                else:
                    self.e.abs('LDA', addr_val & 0xFFFF, f'peek ${addr_val:04X}')
            return

        if name in ('print',):
            if args and args[0]['k'] == 'Literal' and args[0]['kind'] == 'str':
                s_val = args[0]['value']
                self.e.jsr('_print_str', f'print "{s_val}"')
                self.e.data(list(s_val.encode('latin-1')) + [0], f'str "{s_val}"')
                return
            if args:
                self._emit_expr_to_a(args[0])
                self.e.jsr('_print_byte', 'print byte')
            return

        if name in ('println',):
            if args and args[0]['k'] == 'Literal' and args[0]['kind'] == 'str':
                s_val = args[0]['value']
                self.e.jsr('_print_str', f'println "{s_val}"')
                self.e.data(list(s_val.encode('latin-1')) + [0], f'str "{s_val}"')
            elif args:
                self._emit_expr_to_a(args[0])
                self.e.jsr('_print_byte', 'println byte')
            self.e.imm('LDA', 0x0D, 'newline')
            self.e.jsr(0xFFD2, 'KERNAL CHROUT')
            return

        if name in ('clear_screen',):
            self.e.jsr('_cls', 'clear_screen')
            return

        if name in ('border_color',):
            if args:
                self._emit_expr_to_a(args[0])
                self.e.abs('STA', 0xD020, 'border color')
            return

        if name in ('screen_color',):
            if args:
                self._emit_expr_to_a(args[0])
                self.e.abs('STA', 0xD021, 'screen color')
            return

        if name in ('wait_frames',):
            if args:
                self._emit_expr_to_a(args[0])
                self.e.jsr('_wait_frames', 'wait frames')
            return

        if name in ('sei',):
            self.e.imp('SEI', 'sei')
            return

        if name in ('cli',):
            self.e.imp('CLI', 'cli')
            return

        if name in ('print_at',):
            if len(args) >= 2:
                self._emit_expr_to_x(args[0], 'col -> X')
                self._emit_expr_to_y(args[1], 'row -> Y')
                self.e.imp('CLC', 'PLOT set cursor')
                self.e.jsr(0xFFF0, 'KERNAL PLOT')
            if len(args) >= 3:
                text = args[2]
                if text['k'] == 'Literal' and text.get('kind') == 'str':
                    s_val = text['value']
                    self.e.jsr('_print_str', f'print_at "{s_val}"')
                    self.e.data(list(s_val.encode('latin-1')) + [0], f'str "{s_val}"')
            return

    def _emit_expr_to_a(self, node):
        if node is None:
            self.e.imm('LDA', 0, 'nil')
            return
        kind = node['k']
        if kind == 'Literal':
            val = node['value']
            if node.get('kind') in ('bool',):
                val = 1 if val == 1 else 0
            self.e.imm('LDA', val & 0xFF, f'lit ${val:02X}')
        elif kind == 'Ident':
            var = self._var(node['name'])
            if var:
                if var['isZP'] and var.get('addr') is not None:
                    self.e.zp('LDA', var['addr'], f'ld {node["name"]}')
                else:
                    addr = var.get('addr') or var.get('bss_label', 0)
                    if isinstance(addr, str):
                        self.e.abs('LDA', addr, f'ld {node["name"]}')
                    else:
                        self.e.abs('LDA', addr, f'ld {node["name"]}')
            else:
                self.e.imm('LDA', 0, f'?{node["name"]}')
        elif kind == 'BinaryOp':
            self._emit_binop_to_a(node)
        elif kind == 'UnaryOp':
            if node['op'] == '-':
                self._emit_expr_to_a(node['operand'])
                self.e.imp('EOR', '#$FF')
                self.e.imp('CLC')
                self.e.imp('ADC', 1)
            elif node['op'] == '!':
                self._emit_expr_to_a(node['operand'])
                self.e.imm('CMP', 0)
                self.e.imm('LDA', 0)
                self.e.branch('BNE', self.e.uniq('_not'))
                self.e.imm('LDA', 1)
            else:
                self._emit_expr_to_a(node['operand'])
        elif kind == 'Call':
            self._emit_call(node)
        elif kind == 'Cast':
            self._emit_expr_to_a(node['expr'])
        else:
            self.e.imm('LDA', 0, f'?{kind}')

    def _emit_binop_to_a(self, node):
        op = node['op']
        left = node['left']
        right = node['right']

        right_val = None
        if right['k'] == 'Literal':
            right_val = right['value']

        if op == '+' and isinstance(right_val, int) and right_val < 256:
            self._emit_expr_to_a(left)
            self.e.imp('CLC')
            self.e.imm('ADC', right_val & 0xFF, f'+ ${right_val:02X}')
            return

        if op == '-' and isinstance(right_val, int) and right_val < 256:
            self._emit_expr_to_a(left)
            self.e.imp('SEC')
            self.e.imm('SBC', right_val & 0xFF, f'- ${right_val:02X}')
            return

        if op == '&' and isinstance(right_val, int):
            self._emit_expr_to_a(left)
            self.e.imm('AND', right_val & 0xFF, f'& ${right_val:02X}')
            return

        if op == '|' and isinstance(right_val, int):
            self._emit_expr_to_a(left)
            self.e.imm('ORA', right_val & 0xFF, f'| ${right_val:02X}')
            return

        if op == '^' and isinstance(right_val, int):
            self._emit_expr_to_a(left)
            self.e.imm('EOR', right_val & 0xFF, f'^ ${right_val:02X}')
            return

        if op == '<<' and isinstance(right_val, int):
            self._emit_expr_to_a(left)
            for _ in range(right_val):
                self.e.acc('ASL', '<<')
            return

        if op == '>>' and isinstance(right_val, int):
            self._emit_expr_to_a(left)
            for _ in range(right_val):
                self.e.acc('LSR', '>>')
            return

        if op == '*':
            self._emit_expr_to_a(left)
            tmp = self.e.uniq('_mul')
            if isinstance(right_val, int) and 0 <= right_val < 256:
                self.e.zp('STA', 0xFC, 'tmp')
                self.e.imm('LDA', right_val, f'mul ${right_val:02X}')
                self.e.jsr('_mul_byte', 'mul byte')
            else:
                self._emit_expr_to_a(right)
                self.e.zp('STA', 0xFC, 'tmp')
                self.e.zp('LDA', 0xFB, 'restore')
                self.e.jsr('_mul_byte', 'mul')
            return

        if op == '+':
            self._emit_expr_to_a(right)
            self.e.zp('STA', 0xFC, 'tmp')
            self._emit_expr_to_a(left)
            self.e.imp('CLC')
            self.e.zp('ADC', 0xFC, '+')
            return

        if op == '-':
            self._emit_expr_to_a(right)
            self.e.zp('STA', 0xFC, 'tmp')
            self._emit_expr_to_a(left)
            self.e.imp('SEC')
            self.e.zp('SBC', 0xFC, '-')
            return

        if op in ('&', '|', '^'):
            self._emit_expr_to_a(left)
            self.e.zp('STA', 0xFC, 'tmp')
            self._emit_expr_to_a(right)
            if op == '&':
                self.e.zp('AND', 0xFC, '&')
            elif op == '|':
                self.e.zp('ORA', 0xFC, '|')
            else:
                self.e.zp('EOR', 0xFC, '^')
            return

        # fallback
        self._emit_expr_to_a(left)

    def _emit_expr_to_x(self, node, comment=''):
        self._emit_expr_to_a(node)
        self.e.imp('TAX', comment)

    def _emit_expr_to_y(self, node, comment=''):
        self._emit_expr_to_a(node)
        self.e.imp('TAY', comment)

    def get_bytecode(self):
        return self.e.buf
