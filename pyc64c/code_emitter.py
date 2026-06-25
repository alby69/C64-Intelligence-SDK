"""Code Emitter — 6502 machine code buffer with labels and fixups."""

from .ops import OPS, hex2, hex4

PRG_LOAD_ADDR = 0x0801
PRG_CODE_OFFSET = 0x080D


class CodeEmitter:
    def __init__(self, base_addr=PRG_CODE_OFFSET):
        self.base = base_addr
        self.buf = []
        self.labels = {}
        self.fixups = []
        self.listing = []
        self._uid = 0

    def here(self):
        return len(self.buf)

    def addr(self):
        return self.base + len(self.buf)

    def _b(self, v):
        self.buf.append(v & 0xFF)

    def _w(self, v):
        self._b(v)
        self._b((v >> 8) & 0xFF)

    def data(self, arr, comment=''):
        a = self.addr()
        for b in arr:
            self._b(b)
        self.listing.append({
            'addr': a, 'bytes': list(arr), 'mnem': '.byte',
            'op': ','.join(hex2(b) for b in arr),
            'comment': comment, 'isData': True
        })

    def label(self, name):
        if name in self.labels:
            raise ValueError(f"Label doppia: '{name}'")
        self.labels[name] = self.here()
        self.listing.append({
            'addr': self.addr(), 'bytes': [], 'mnem': '',
            'op': '', 'comment': name + ':', 'isLabel': True, 'labelName': name
        })

    def uniq(self, pfx='_L'):
        n = self._uid
        self._uid += 1
        return f'{pfx}{n}'

    def _get_op(self, mnem, mode):
        ops = OPS.get(mnem, {})
        op = ops.get(mode)
        if op is None:
            raise ValueError(f"Opcode mancante: {mnem} {mode}")
        return op

    def _li(self, addr, bytes_, mnem, op, mode, comment='', fixup=False):
        self.listing.append({
            'addr': addr, 'bytes': list(bytes_), 'mnem': mnem,
            'op': op, 'mode': mode, 'comment': comment, 'fixup': fixup
        })

    def rti(self, comment=''):
        a = self.addr()
        self._b(0x40)
        self._li(a, [0x40], 'RTI', '', 'imp', comment)

    def imp(self, mnem, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'imp')
        self._b(op)
        self._li(a, [op], mnem, '', 'imp', comment)

    def acc(self, mnem, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'acc')
        self._b(op)
        self._li(a, [op], mnem, 'A', 'acc', comment)

    def imm(self, mnem, val, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'imm')
        v = val & 0xFF
        self._b(op)
        self._b(v)
        self._li(a, [op, v], mnem, f'#{hex2(v)}', 'imm', comment)

    def zp(self, mnem, zp_a, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'zp')
        v = zp_a & 0xFF
        self._b(op)
        self._b(v)
        self._li(a, [op, v], mnem, hex2(v), 'zp', comment)

    def zpx(self, mnem, zp_a, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'zpx')
        v = zp_a & 0xFF
        self._b(op)
        self._b(v)
        self._li(a, [op, v], mnem, f'{hex2(v)},X', 'zpx', comment)

    def zpy(self, mnem, zp_a, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'zpy')
        v = zp_a & 0xFF
        self._b(op)
        self._b(v)
        self._li(a, [op, v], mnem, f'{hex2(v)},Y', 'zpy', comment)

    def abs(self, mnem, target, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'abs')
        self._b(op)
        if isinstance(target, str):
            self.fixups.append({'at': self.here(), 'type': 'abs', 'label': target, 'addrOf': a})
            self._b(0)
            self._b(0)
            self._li(a, [op, 0, 0], mnem, target, 'abs', comment, True)
        else:
            v = target & 0xFFFF
            self._w(v)
            self._li(a, [op, v & 0xFF, (v >> 8) & 0xFF], mnem, hex4(v), 'abs', comment)

    def abx(self, mnem, target, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'abx')
        self._b(op)
        if isinstance(target, str):
            self.fixups.append({'at': self.here(), 'type': 'abs', 'label': target, 'addrOf': a})
            self._b(0)
            self._b(0)
            self._li(a, [op, 0, 0], mnem, f'{target},X', 'abx', comment, True)
        else:
            v = target & 0xFFFF
            self._w(v)
            self._li(a, [op, v & 0xFF, (v >> 8) & 0xFF], mnem, f'{hex4(v)},X', 'abx', comment)

    def aby(self, mnem, target, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'aby')
        self._b(op)
        if isinstance(target, str):
            self.fixups.append({'at': self.here(), 'type': 'abs', 'label': target, 'addrOf': a})
            self._b(0)
            self._b(0)
            self._li(a, [op, 0, 0], mnem, f'{target},Y', 'aby', comment, True)
        else:
            v = target & 0xFFFF
            self._w(v)
            self._li(a, [op, v & 0xFF, (v >> 8) & 0xFF], mnem, f'{hex4(v)},Y', 'aby', comment)

    def inx(self, mnem, zp_a, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'inx')
        v = zp_a & 0xFF
        self._b(op)
        self._b(v)
        self._li(a, [op, v], mnem, f'({hex2(v)},X)', 'inx', comment)

    def iny(self, mnem, zp_a, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'iny')
        v = zp_a & 0xFF
        self._b(op)
        self._b(v)
        self._li(a, [op, v], mnem, f'({hex2(v)}),Y', 'iny', comment)

    def jsr(self, target, comment=''):
        a = self.addr()
        op = OPS['JSR']['abs']
        self._b(op)
        if isinstance(target, str):
            self.fixups.append({'at': self.here(), 'type': 'abs', 'label': target, 'addrOf': a})
            self._b(0)
            self._b(0)
            self._li(a, [op, 0, 0], 'JSR', target, 'abs', comment, True)
        else:
            v = target & 0xFFFF
            self._w(v)
            self._li(a, [op, v & 0xFF, (v >> 8) & 0xFF], 'JSR', hex4(v), 'abs', comment)

    def jmp(self, target, comment=''):
        a = self.addr()
        op = OPS['JMP']['abs']
        self._b(op)
        if isinstance(target, str):
            self.fixups.append({'at': self.here(), 'type': 'abs', 'label': target, 'addrOf': a})
            self._b(0)
            self._b(0)
            self._li(a, [op, 0, 0], 'JMP', target, 'abs', comment, True)
        else:
            v = target & 0xFFFF
            self._w(v)
            self._li(a, [op, v & 0xFF, (v >> 8) & 0xFF], 'JMP', hex4(v), 'abs', comment)

    def branch(self, mnem, lbl, comment=''):
        a = self.addr()
        op = self._get_op(mnem, 'rel')
        self._b(op)
        instr_end = self.here() + 1
        self.fixups.append({'at': self.here(), 'type': 'rel', 'label': lbl,
                           'addrOf': a, 'instrEnd': instr_end})
        self._b(0)
        self._li(a, [op, 0], mnem, lbl, 'rel', comment, True)

    def resolve_fixups(self):
        errs = []
        for f in self.fixups:
            lbl = f['label']
            offset = 0
            plus = lbl.find('+') if isinstance(lbl, str) else -1
            if plus > 0:
                offset = int(lbl[plus + 1:]) or 0
                lbl = lbl[:plus]
            if lbl not in self.labels:
                errs.append(f"Unresolved label: '{f['label']}'")
                continue
            tgt = self.labels[lbl]
            tgt_addr = self.base + tgt + offset
            if f['type'] in ('lo', 'hi'):
                byte_ = (tgt_addr & 0xFF) if f['type'] == 'lo' else ((tgt_addr >> 8) & 0xFF)
                self.buf[f['at']] = byte_
                for le in self.listing:
                    if le.get('fixup') and le.get('addr') == f['addrOf']:
                        le['bytes'][1] = byte_
                        le['op'] = f'#{hex2(byte_)}'
                        le['fixup'] = False
                        break
            elif f['type'] == 'abs':
                self.buf[f['at']] = tgt_addr & 0xFF
                self.buf[f['at'] + 1] = (tgt_addr >> 8) & 0xFF
                for le in self.listing:
                    if le.get('fixup') and le.get('addr') == f['addrOf']:
                        le['bytes'][1] = tgt_addr & 0xFF
                        le['bytes'][2] = (tgt_addr >> 8) & 0xFF
                        le['op'] = hex4(tgt_addr)
                        le['fixup'] = False
                        break
            else:  # rel
                delta = tgt - f['instrEnd']
                if delta < -128 or delta > 127:
                    errs.append(f"Branch fuori range: '{f['label']}' (∆={delta})")
                else:
                    self.buf[f['at']] = delta & 0xFF
                    for le in self.listing:
                        if le.get('fixup') and le.get('addr') == f['addrOf']:
                            le['bytes'][1] = delta & 0xFF
                            le['fixup'] = False
                            break
        return errs

    def to_bytes(self):
        return bytes(self.buf)

    def byte_count(self):
        return len(self.buf)
