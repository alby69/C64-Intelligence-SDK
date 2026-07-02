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
            var = self._var(s['name'])
            if not var:
                return
            if self._is_16(s):
                self._emit_word_to_zp(s['init'], 0xFB)
                self.e.zp('LDA', 0xFB)
                self._st_var_byte(var, f'{s["name"]} lo')
                self.e.zp('LDA', 0xFC)
                if var['isZP']:
                    self.e.zp('STA', var['addr'] + 1, f'{s["name"]} hi')
                else:
                    addr = var.get('addr') or var.get('bss_label', 0)
                    if isinstance(addr, str):
                        self.e.abs('STA', f"{addr}+1", f'{s["name"]} hi')
                    else:
                        self.e.abs('STA', addr + 1, f'{s["name"]} hi')
            else:
                self._emit_expr_to_a(s['init'])
                self._st_var_byte(var, f'{s["name"]} = ...')

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

        # Special case for x = x + ... or x += ...
        if (rhs['k'] == 'BinaryOp' and rhs['op'] == '+' and
            rhs['left']['k'] == 'Ident' and rhs['left']['name'] == lhs_name):
            self._emit_word_to_fb_fc(rhs['right'])
            self.e.imp('CLC')
            if var['isZP']:
                self.e.zp('LDA', var['addr'])
                self.e.zp('ADC', 0xFB)
                self.e.zp('STA', var['addr'])
                self.e.zp('LDA', var['addr'] + 1)
                self.e.zp('ADC', 0xFC)
                self.e.zp('STA', var['addr'] + 1)
            else:
                addr = var.get('addr') or var.get('bss_label', 0)
                self.e.abs('LDA', addr)
                self.e.zp('ADC', 0xFB)
                self.e.abs('STA', addr)
                self.e.abs('LDA', addr + 1)
                self.e.zp('ADC', 0xFC)
                self.e.abs('STA', addr + 1)
            return

        self._emit_word_to_zp(rhs, 0xFB)
        self.e.zp('LDA', 0xFB)
        if var['isZP']:
            self.e.zp('STA', var['addr'])
            self.e.zp('LDA', 0xFC)
            self.e.zp('STA', var['addr'] + 1)
        else:
            addr = var.get('addr') or var.get('bss_label', 0)
            self.e.abs('STA', addr)
            self.e.zp('LDA', 0xFC)
            self.e.abs('STA', addr + 1)

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

            if addr_val is not None:
                if byte_val is not None:
                    self.e.imm('LDA', byte_val & 0xFF, f'poke val ${byte_val:02X}')
                else:
                    self._emit_expr_to_a(args[1])
                if addr_val < 0x100:
                    self.e.zp('STA', addr_val & 0xFF, f'poke ${addr_val:04X}')
                else:
                    self.e.abs('STA', addr_val & 0xFFFF, f'poke ${addr_val:04X}')
            else:
                # Dynamic address: use stack to avoid scratchpad collisions
                self._emit_expr_to_a(args[1]) # value to A
                self.e.imp('PHA')
                self._emit_word_to_fd_fe(args[0]) # address to FD/FE
                self.e.imm('LDY', 0)
                self.e.imp('PLA')
                self.e.iny('STA', 0xFD) # STA ($FD),Y
            return

        if name in ('poke16',):
            if args[0]['k'] == 'Literal':
                addr = args[0]['value']
                self._emit_word_to_fb_fc(args[1]) # value -> FB/FC
                self.e.zp('LDA', 0xFB)
                self.e.abs('STA', addr)
                self.e.zp('LDA', 0xFC)
                self.e.abs('STA', addr + 1)
            else:
                # Dynamic address: use stack to preserve the 16-bit value
                self._emit_word_to_zp(args[1], 0xFB) # value to FB/FC
                self.e.zp('LDA', 0xFC); self.e.imp('PHA')
                self.e.zp('LDA', 0xFB); self.e.imp('PHA')
                self._emit_word_to_fd_fe(args[0]) # address to FD/FE
                self.e.imm('LDY', 0)
                self.e.imp('PLA'); self.e.iny('STA', 0xFD) # STA ($FD),Y  (lo)
                self.e.imp('INY')
                self.e.imp('PLA'); self.e.iny('STA', 0xFD) # STA ($FD),Y  (hi)
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
            else:
                self._emit_word_to_fb_fc(args[0])
                self.e.imm('LDY', 0)
                self.e.iny('LDA', 0xFB)
            return

        if name in ('peek16',):
            if args[0]['k'] == 'Literal':
                addr = args[0]['value']
                self.e.abs('LDA', addr)
                self.e.zp('STA', 0xFB)
                self.e.abs('LDA', addr + 1)
                self.e.zp('STA', 0xFC)
            else:
                self._emit_word_to_fb_fc(args[0])
                self.e.imm('LDY', 0)
                self.e.iny('LDA', 0xFB)
                self.e.zp('STA', 0xFD) # temp lo
                self.e.imp('INY')
                self.e.iny('LDA', 0xFB)
                self.e.zp('STA', 0xFC) # hi
                self.e.zp('LDA', 0xFD)
                self.e.zp('STA', 0xFB) # restore lo to FB
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

        if name == 'bitmap_clear':
            self.e.jsr('_bitmap_clear', 'bitmap_clear')
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

        if name in ('text_color',):
            if args:
                self._emit_expr_to_a(args[0])
                self.e.abs('STA', 0x0286, 'text color')
            return

        if name in ('wait_frames',):
            if args:
                self._emit_expr_to_a(args[0])
                self.e.jsr('_wait_frames', 'wait frames')
            return

        if name == 'sprite_collision_sprite':
            self.e.abs('LDA', 0xD01E, 'sprite-sprite collision')
            return

        if name == 'sprite_collision_data':
            self.e.abs('LDA', 0xD01F, 'sprite-data collision')
            return

        if name == 'raster_line':
            self.e.abs('LDA', 0xD012, 'raster line')
            return

        if name == 'sid_random':
            self.e.abs('LDA', 0xD41B, 'sid random')
            return

        if name == 'raster_irq':
            if args:
                # line -> $FB/FC
                self._emit_word_to_fb_fc(args[0])
                self.e.zp('LDA', 0xFB); self.e.abs('STA', 0xD012)
                self.e.abs('LDA', 0xD011); self.e.imm('AND', 0x7F); self.e.zp('STA', 0xFD)
                self.e.zp('LDA', 0xFC); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL')
                self.e.zp('ORA', 0xFD); self.e.abs('STA', 0xD011)
            return

        if name == 'scroll_x':
            if args:
                self.e.abs('LDA', 0xD016); self.e.imm('AND', 0xF8); self.e.zp('STA', 0xFB)
                self._emit_expr_to_a(args[0]); self.e.imm('AND', 0x07); self.e.zp('ORA', 0xFB)
                self.e.abs('STA', 0xD016)
            return

        if name == 'scroll_y':
            if args:
                self.e.abs('LDA', 0xD011); self.e.imm('AND', 0xF8); self.e.zp('STA', 0xFB)
                self._emit_expr_to_a(args[0]); self.e.imm('AND', 0x07); self.e.zp('ORA', 0xFB)
                self.e.abs('STA', 0xD011)
            return

        if name == 'screen_size':
            if len(args) >= 2:
                # cols
                self._emit_expr_to_a(args[0])
                self.e.imm('CMP', 40); self.e.abs('LDA', 0xD016)
                lbl_c38 = self.e.uniq('_sc38')
                self.e.branch('BNE', lbl_c38)
                self.e.imm('ORA', 0x08); self.e.abs('STA', 0xD016); lbl_cend = self.e.uniq('_sce')
                self.e.jmp(lbl_cend)
                self.e.label(lbl_c38); self.e.imm('AND', 0xF7); self.e.abs('STA', 0xD016); self.e.label(lbl_cend)
                # rows
                self._emit_expr_to_a(args[1])
                self.e.imm('CMP', 25); self.e.abs('LDA', 0xD011)
                lbl_r24 = self.e.uniq('_sr24')
                self.e.branch('BNE', lbl_r24)
                self.e.imm('ORA', 0x08); self.e.abs('STA', 0xD011); lbl_rend = self.e.uniq('_sre')
                self.e.jmp(lbl_rend)
                self.e.label(lbl_r24); self.e.imm('AND', 0xF7); self.e.abs('STA', 0xD011); self.e.label(lbl_rend)
            return

        if name == 'sprite_enable':
            if len(args) >= 2:
                # reg $D015 -> $FC/FD
                self.e.imm('LDA', 0x15)
                self.e.zp('STA', 0xFC)
                self.e.imm('LDA', 0xD0)
                self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[0])
                self.e.zp('STA', 0xFE, 'idx -> $FE')
                self._emit_expr_to_a(args[1])
                self.e.imp('TAX', 'on/off -> X')
                self.e.zp('LDA', 0xFE, 'idx')
                self.e.jsr('_set_sprite_bit', 'call set_sprite_bit')
            return

        if name == 'sprite_pos':
            if len(args) >= 3:
                # idx, x, y
                # idx -> A, x -> $FB/FC, y -> X
                self._emit_word_to_fb_fc(args[1]) # x
                self._emit_expr_to_x(args[2])    # y
                self._emit_expr_to_a(args[0])    # idx
                self.e.jsr('_set_sprite_pos', 'call set_sprite_pos')
            return

        if name == 'sprite_color':
            if len(args) >= 2:
                self._emit_expr_to_a(args[1])
                self.e.imp('TAX', 'color -> X')
                self._emit_expr_to_a(args[0])
                self.e.imp('TAY', 'idx -> Y')
                self.e.aby('STX', 0xD027, 'STX $D027,Y')
            return

        if name == 'sprite_pointer':
            if len(args) >= 2:
                self._emit_expr_to_a(args[1])
                self.e.imp('TAX', 'ptr -> X')
                self._emit_expr_to_a(args[0])
                self.e.imp('TAY', 'idx -> Y')
                self.e.aby('STX', 0x07F8, 'STX $07F8,Y')
            return

        if name == 'bitmap_mode':
            if args:
                on_val = args[0].get('value') if args[0]['k'] == 'Literal' else None
                self.e.abs('LDA', 0xD011, 'read SCROLY')
                if on_val:
                    self.e.imm('ORA', 0x20, 'set BMM')
                else:
                    self.e.imm('AND', 0xDF, 'clear BMM')
                self.e.abs('STA', 0xD011, 'write SCROLY')
            return

        if name == 'multicolor_mode':
            if args:
                on_val = args[0].get('value') if args[0]['k'] == 'Literal' else None
                self.e.abs('LDA', 0xD016, 'read SCROLX')
                if on_val:
                    self.e.imm('ORA', 0x10, 'set MCM')
                else:
                    self.e.imm('AND', 0xEF, 'clear MCM')
                self.e.abs('STA', 0xD016, 'write SCROLX')
            return

        if name == 'sprite_multicolor':
            if len(args) >= 2:
                self.e.imm('LDA', 0x1C); self.e.zp('STA', 0xFC)
                self.e.imm('LDA', 0xD0); self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[0]); self.e.zp('STA', 0xFE)
                self._emit_expr_to_a(args[1]); self.e.imp('TAX')
                self.e.zp('LDA', 0xFE)
                self.e.jsr('_set_sprite_bit', 'call set_sprite_bit')
            return

        if name == 'sprite_stretch':
            if len(args) >= 3:
                self._emit_expr_to_a(args[0]); self.e.zp('STA', 0xFE)
                # H
                self.e.imm('LDA', 0x1D); self.e.zp('STA', 0xFC)
                self.e.imm('LDA', 0xD0); self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[1]); self.e.imp('TAX')
                self.e.zp('LDA', 0xFE)
                self.e.jsr('_set_sprite_bit', 'X stretch')
                # V
                self.e.imm('LDA', 0x17); self.e.zp('STA', 0xFC)
                self.e.imm('LDA', 0xD0); self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[2]); self.e.imp('TAX')
                self.e.zp('LDA', 0xFE)
                self.e.jsr('_set_sprite_bit', 'Y stretch')
            return

        if name == 'sprite_config':
            if len(args) >= 2:
                self._emit_expr_to_a(args[0])
                self.e.abs('STA', 0xD025, 'sprite multicolor 0')
                self._emit_expr_to_a(args[1])
                self.e.abs('STA', 0xD026, 'sprite multicolor 1')
            return

        if name == 'sid_volume':
            if args:
                self.e.abs('LDA', 0xD418)
                self.e.imm('AND', 0xF0)
                self.e.zp('STA', 0xFB)
                self._emit_expr_to_a(args[0])
                self.e.imm('AND', 0x0F)
                self.e.zp('ORA', 0xFB)
                self.e.abs('STA', 0xD418)
            return

        if name == 'sid_setup':
            if len(args) >= 5:
                # attack/decay
                # A*16 + D -> Y
                self._emit_expr_to_a(args[1]); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL')
                self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[2]); self.e.zp('ORA', 0xFD); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 5)
                self.e.jsr('_set_sid_reg')
                # sustain/release
                self._emit_expr_to_a(args[3]); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL')
                self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[4]); self.e.zp('ORA', 0xFD); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 6)
                self.e.jsr('_set_sid_reg')
            return

        if name == 'sid_freq':
            if len(args) >= 2:
                self._emit_word_to_fb_fc(args[1])
                # low
                self.e.zp('LDA', 0xFB); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 0)
                self.e.jsr('_set_sid_reg')
                # high
                self.e.zp('LDA', 0xFC); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 1)
                self.e.jsr('_set_sid_reg')
            return

        if name == 'sid_pw':
            if len(args) >= 2:
                self._emit_word_to_fb_fc(args[1])
                # low
                self.e.zp('LDA', 0xFB); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 2)
                self.e.jsr('_set_sid_reg')
                # high
                self.e.zp('LDA', 0xFC); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 3)
                self.e.jsr('_set_sid_reg')
            return

        if name == 'sid_gate':
            if len(args) >= 3:
                # wf OR on -> Y
                self._emit_expr_to_a(args[1]); self.e.zp('STA', 0xFD)
                self._emit_expr_to_a(args[2]); self.e.zp('ORA', 0xFD); self.e.imp('TAY')
                self._emit_expr_to_a(args[0]); self.e.imm('LDX', 4)
                self.e.jsr('_set_sid_reg')
            return

        if name == 'sid_clear':
            # Fast clear with loop
            self.e.imm('LDA', 0); self.e.imm('LDX', 24)
            lbl_l = self.e.uniq('_sidc')
            self.e.label(lbl_l); self.e.abx('STA', 0xD400); self.e.imp('DEX'); self.e.branch('BPL', lbl_l)
            return

        if name == 'vic_bank':
            if args:
                # bits 0-1 of $DD00. 11=bank0, 10=bank1, 01=bank2, 00=bank3. Pattern is 3-bank.
                self._emit_expr_to_a(args[0]); self.e.zp('STA', 0xFB)
                self.e.imm('LDA', 3); self.e.imp('SEC'); self.e.zp('SBC', 0xFB)
                self.e.imm('AND', 0x03); self.e.zp('STA', 0xFB)
                self.e.abs('LDA', 0xDD00); self.e.imm('AND', 0xFC); self.e.zp('ORA', 0xFB)
                self.e.abs('STA', 0xDD00)
            return

        if name == 'sid_filter':
            if len(args) >= 3:
                # cutoff -> $FB/FC
                self._emit_word_to_fb_fc(args[0])
                # LOW 3 bits of cutoff to $D415
                self.e.zp('LDA', 0xFB); self.e.imm('AND', 0x07); self.e.abs('STA', 0xD415)
                # HI 8 bits (cutoff/8) to $D416
                self.e.zp('LDA', 0xFB); self.e.acc('LSR'); self.e.acc('LSR'); self.e.acc('LSR'); self.e.zp('STA', 0xFD)
                self.e.zp('LDA', 0xFC); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL')
                self.e.zp('ORA', 0xFD); self.e.abs('STA', 0xD416)

                # resonance -> bits 4-7 of $D417
                self._emit_expr_to_a(args[1]); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL'); self.e.acc('ASL')
                self.e.zp('STA', 0xFD)
                self.e.abs('LDA', 0xD417); self.e.imm('AND', 0x0F); self.e.zp('ORA', 0xFD); self.e.abs('STA', 0xD417)

                # mode -> bits 4-6 of $D418, bits 0-3 of $D417
                self._emit_expr_to_a(args[2]); self.e.zp('STA', 0xFE)
                # voices to filter (bits 0-3 of mode -> $D417)
                self.e.zp('LDA', 0xFE); self.e.imm('AND', 0x0F); self.e.zp('STA', 0xFD)
                self.e.abs('LDA', 0xD417); self.e.imm('AND', 0xF0); self.e.zp('ORA', 0xFD); self.e.abs('STA', 0xD417)
                # mode (bits 4-6 of mode -> $D418)
                self.e.zp('LDA', 0xFE); self.e.imm('AND', 0x70); self.e.zp('STA', 0xFD)
                self.e.abs('LDA', 0xD418); self.e.imm('AND', 0x8F); self.e.zp('ORA', 0xFD); self.e.abs('STA', 0xD418)
            return

        if name in ('sei',):
            self.e.imp('SEI', 'sei')
            return

        if name in ('cli',):
            self.e.imp('CLI', 'cli')
            return

        if name == 'kernal_chrout':
            if args:
                self._emit_expr_to_a(args[0])
                self.e.jsr(0xFFD2, 'CHROUT')
            return

        if name == 'kernal_chrin':
            self.e.jsr(0xFFCF, 'CHRIN')
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

    def _emit_word_to_fb_fc(self, node):
        self._emit_word_to_zp(node, 0xFB)

    def _emit_word_to_fd_fe(self, node):
        self._emit_word_to_zp(node, 0xFD)

    def _emit_word_to_zp(self, node, zp_addr):
        if node['k'] == 'Literal':
            val = node['value']
            self.e.imm('LDA', val & 0xFF)
            self.e.zp('STA', zp_addr)
            self.e.imm('LDA', (val >> 8) & 0xFF)
            self.e.zp('STA', zp_addr + 1)
        elif node['k'] == 'Ident':
            var = self._var(node['name'])
            if var:
                if var['isZP']:
                    self.e.zp('LDA', var['addr'])
                    self.e.zp('STA', zp_addr)
                    if self._is_16(node):
                        self.e.zp('LDA', var['addr'] + 1)
                        self.e.zp('STA', zp_addr + 1)
                    else:
                        self.e.imm('LDA', 0)
                        self.e.zp('STA', zp_addr + 1)
                else:
                    addr = var.get('addr') or var.get('bss_label', 0)
                    self.e.abs('LDA', addr)
                    self.e.zp('STA', zp_addr)
                    if self._is_16(node):
                        self.e.abs('LDA', addr + 1)
                        self.e.zp('STA', zp_addr + 1)
                    else:
                        self.e.imm('LDA', 0)
                        self.e.zp('STA', zp_addr + 1)
        else:
            self._emit_expr_to_a(node)
            # node might be 16-bit, so it might have put hi byte in $FC
            self.e.zp('STA', zp_addr)
            if self._is_16(node):
                self.e.zp('LDA', 0xFC)
                self.e.zp('STA', zp_addr + 1)
            else:
                self.e.imm('LDA', 0)
                self.e.zp('STA', zp_addr + 1)

    def get_bytecode(self):
        return self.e.buf
