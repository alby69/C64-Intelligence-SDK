"""PRG Builder — assembles the final .PRG file with BASIC stub + code + BSS."""

from .code_emitter import CodeEmitter, PRG_LOAD_ADDR, PRG_CODE_OFFSET
from .ast_nodes import TYPE_SIZE, is_fixed_type, fp_scale
from .code_gen import CodeGenerator
from .runtime import runtime_labels_and_bytes


class PRGBuilder:
    def __init__(self, ast, planner, uses_float, sem_scope):
        self.ast = ast
        self.planner = planner
        self.uses_float = uses_float
        self._sem_scope = sem_scope or type('obj', (object,), {'lookup': lambda s, x: None})()
        self.STUB = [0x0B, 0x08, 0x00, 0x00, 0x9E,
                     0x32, 0x30, 0x36, 0x31, 0x00, 0x00, 0x00]
        self.e = CodeEmitter(PRG_CODE_OFFSET)
        self.fixup_errs = []
        self.built = False

    def build(self):
        try:
            self._emit_startup()
            self._emit_func_bodies()
            self._emit_runtime()
            self._emit_bss()
            self.fixup_errs = self.e.resolve_fixups()
            self.built = True
        except Exception as err:
            self.fixup_errs.append(f"Build error: {err}")
        return self

    def _emit_startup(self):
        e = self.e
        if not self.uses_float:
            e.imm('LDA', 0x36, 'BASIC ROM → RAM')
            e.zp('STA', 0x01, 'CPU port LORAM=0 HIRAM=1 CHAREN=1')
        has_main = any(f['name'] == 'main' for f in self.ast['funcs'])
        if has_main:
            e.jsr('main', 'call main()')
        else:
            e.imp('BRK', '!!! main() undefined — halt')
        if not self.uses_float:
            e.imm('LDA', 0x37, 'restore BASIC ROM')
            e.zp('STA', 0x01, 'CPU port → $37')
        e.imp('RTS', 'return to BASIC')

    def _emit_func_bodies(self):
        cg = CodeGenerator(self.e, self.planner, self._sem_scope, self.ast)
        for f in self.ast['funcs']:
            layout = self.planner.func_layouts.get(f['name'])
            info = f"ret={f.get('ret', 'void')}  frame={layout.get('frameBytes', 0) if layout else 0}B"
            try:
                cg.gen_func(f)
                if self.e.listing:
                    self.e.listing[-1]['comment'] = f"{f['name']}()  {info}"
            except Exception as err:
                self.e.imp('NOP', f'[CODEGEN ERR] {f["name"]}: {err}')
                self.e.imp('RTS', '')

    def _needs_routine(self, name):
        """Check if any function calls a given builtin name."""
        for f in self.ast['funcs']:
            if self._find_call(f['body'], name):
                return True
        return False

    def _find_call(self, node, name):
        if not isinstance(node, dict):
            return False
        k = node.get('k', '')
        if k == 'Call' and node.get('name') == name:
            return True
        for child in ('stmts', 'args', 'then', 'else', 'body', 'init', 'incr',
                      'expr', 'cond', 'left', 'right', 'operand', 'value', 'target'):
            val = node.get(child)
            if val is None:
                continue
            if isinstance(val, list):
                for v in val:
                    if self._find_call(v, name):
                        return True
            elif self._find_call(val, name):
                return True
        return False

    def _emit_runtime(self):
        runtime_labels, runtime_bytes = runtime_labels_and_bytes(0)
        to_emit = []
        builtin_to_runtime = {
            'clear_screen': '_cls',
            'print_at': '_print_str',
            'print': '_print_str',
            'println': '_print_str',
            'wait': '_wait_frames',
            'wait_frames': '_wait_frames',
        }
        runtime_names = set()
        for builtin, rt in builtin_to_runtime.items():
            if self._needs_routine(builtin):
                runtime_names.add(rt)
        # Also check for print_byte / mul_byte usage
        if self._needs_routine('print') or self._needs_routine('println'):
            runtime_names.add('_print_byte')
        for f in self.ast['funcs']:
            if self._find_mul(f['body']):
                runtime_names.add('_mul_byte')
                break

        if not runtime_names:
            return

        # Emit all selected runtime labels and the supporting routines they need
        needed = set(runtime_names)
        # _print_str needs no extra; _print_byte needs no extra (has direct JSR $FFD2)
        # _cls needs no extra; _wait_frames needs no extra; _mul_byte needs no extra

        rt_base = self.e.here()
        self.e.data(runtime_bytes, 'runtime library')
        rt_end = self.e.here()

        # Register runtime labels at their correct addresses
        for name, offset in runtime_labels.items():
            if name in needed:
                addr = rt_base + offset
                self.e.labels[name] = addr
                self.e.listing.append({
                    'addr': self.e.base + addr, 'bytes': [], 'mnem': '',
                    'op': '', 'comment': f'{name}: (runtime)', 'isLabel': True,
                    'labelName': name
                })

    def _find_mul(self, node):
        if not isinstance(node, dict):
            return False
        k = node.get('k', '')
        if k == 'BinaryOp' and node.get('op') == '*':
            return True
        for child in ('stmts', 'args', 'then', 'else', 'body', 'init', 'incr',
                      'expr', 'cond', 'left', 'right', 'operand', 'value', 'target'):
            val = node.get(child)
            if val is None:
                continue
            if isinstance(val, list):
                for v in val:
                    if self._find_mul(v):
                        return True
            elif self._find_mul(val):
                return True
        return False

    def _emit_bss(self):
        bss_vars = [g for g in self.planner.globals if not g['isZP']]
        if bss_vars or self.planner.uses_float:
            self.e.label('__bss')
        if self.planner.uses_float:
            self.e.label('_ftmp')
            self.e.data([0, 0, 0, 0, 0], 'float tmp buf')
        for g in bss_vars:
            self.e.label(f'_{g["name"]}')
            bytes_ = [0] * g['size']
            self.e.data(bytes_, f"{g['type']}{'[' + str(g.get('arrCount', 0)) + ']' if g.get('isArr') else ''} {g['name']}")
        if self.planner.uses_float:
            for fname, layout in self.planner.func_layouts.items():
                for v in layout['locals']:
                    if not v.get('isArr') and v.get('addr') is None:
                        lbl = f'_{fname}_{v["name"]}'
                        self.e.label(lbl)
                        self.e.data([0] * v.get('size', 1),
                                    f'{v["type"]} {fname}::{v["name"]}')
                        v['bss_label'] = lbl

    def prg_size(self):
        return 2 + len(self.STUB) + self.e.byte_count()

    def code_size(self):
        return self.e.byte_count()

    def to_prg(self):
        code = self.e.to_bytes()
        prg = bytearray(2 + len(self.STUB) + len(code))
        prg[0] = PRG_LOAD_ADDR & 0xFF
        prg[1] = (PRG_LOAD_ADDR >> 8) & 0xFF
        for i, b in enumerate(self.STUB):
            prg[2 + i] = b
        for i, b in enumerate(code):
            prg[2 + len(self.STUB) + i] = b
        return bytes(prg)
