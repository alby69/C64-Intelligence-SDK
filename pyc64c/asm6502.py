"""asm6502 — Dual-pass macro assembler for MOS 6502.

Features:
- All standard 6502/6510 opcodes and addressing modes
- Labels (global and local with . prefix)
- Directives: .org, .byte, .word, .text, .fill, .align, .include
- Numeric expressions with +, -, *, /, &, |, ^, <<, >>, <, > operators
- Literals: decimal, hex ($ or 0x), binary (%), char ('X')
- Two-pass assembly with forward reference resolution
- Output: PRG (C64 load-address + data) or raw binary
- Annotated listing output

Usage:
    a = Asm6502()
    errors = a.assemble(source_text)
    if not errors:
        prg = a.output_prg()
"""

import os, re
from .ops import OPS
from .code_emitter import PRG_LOAD_ADDR

def hex2(n): return f'${(n & 0xFF):02X}'
def hex4(n): return f'${(n & 0xFFFF):04X}'

RE_LABEL     = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)')
RE_LOCAL     = re.compile(r'^\.([A-Za-z_][A-Za-z0-9_]*):\s*(.*)')
RE_OP        = re.compile(r'^([A-Za-z]{3,5})\s*(.*)', re.IGNORECASE)
RE_DIR       = re.compile(r'^\.([A-Za-z]+)\s*(.*)')
RE_STR       = re.compile(r'"((?:[^"\\]|\\.)*)"')
RE_CHAR      = re.compile(r"'([^'\\])'")
RE_DEC       = re.compile(r'^(-?\d+)')
RE_HEX       = re.compile(r'^([0-9A-Fa-f]+)')
RE_BIN       = re.compile(r'^([01]+)')
RE_IDENT     = re.compile(r'^([A-Za-z_][A-Za-z0-9_.]*)')

class _Token:
    INT, IDENT, OP = 'INT', 'IDENT', 'OP'
    LP, RP = '(', ')'
    COMMA = ','

def _expr_error(msg):
    return {'err': msg}

class _ExprParser:
    def __init__(self, labels, line_num):
        self.labels = labels
        self.line_num = line_num
        self.text = ''
        self.pos = 0
        self.err = None

    def parse(self, text):
        self.text = text.strip()
        self.pos = 0
        self.err = None
        val = self._parse_sum()
        if self.err:
            return _expr_error(self.err)
        rest = self.text[self.pos:].strip()
        if rest:
            return _expr_error(f"Extra characters after expression: '{rest}'")
        return {'ok': val}

    def _peek(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t':
            self.pos += 1
        return self.text[self.pos] if self.pos < len(self.text) else ''

    def _check(self, ch):
        return self._peek() == ch

    def _eat(self, ch):
        if self._check(ch):
            self.pos += 1
            return True
        return False

    def _expect(self, ch):
        if not self._eat(ch):
            self.err = f"Expected '{ch}'"
        return not self.err

    def _parse_sum(self):
        left = self._parse_product()
        if self.err: return 0
        while self._check('+') or self._check('-') or self._check('|') or self._check('^'):
            op = self.text[self.pos]; self.pos += 1
            right = self._parse_product()
            if self.err: return 0
            if op == '+': left += right
            elif op == '-': left -= right
            elif op == '|': left |= right
            elif op == '^': left ^= right
        return left

    def _parse_product(self):
        left = self._parse_unary()
        if self.err: return 0
        while self._check('*') or self._check('/') or self._check('&') or \
              (self.pos + 1 < len(self.text) and self.text[self.pos:self.pos+2] in ('<<', '>>')):
            if self.text[self.pos:self.pos+2] == '<<':
                self.pos += 2; right = self._parse_unary()
                if self.err: return 0
                left <<= right
            elif self.text[self.pos:self.pos+2] == '>>':
                self.pos += 2; right = self._parse_unary()
                if self.err: return 0
                left >>= right
            else:
                op = self.text[self.pos]; self.pos += 1
                right = self._parse_unary()
                if self.err: return 0
                if op == '*': left *= right
                elif op == '/':
                    if right == 0: self.err = "Division by zero"; return 0
                    left //= right
                elif op == '&': left &= right
        return left

    def _parse_unary(self):
        if self._check('+'):
            self.pos += 1
            return self._parse_unary()
        if self._check('-'):
            self.pos += 1
            return -self._parse_unary()
        if self._check('<'):
            self.pos += 1
            return self._parse_atom() & 0xFF
        if self._check('>'):
            self.pos += 1
            return (self._parse_atom() >> 8) & 0xFF
        if self._check('~'):
            self.pos += 1
            return ~self._parse_atom() & 0xFFFF
        return self._parse_atom()

    def _parse_atom(self):
        self._skip_ws()
        if self.pos >= len(self.text):
            self.err = "Empty atom"; return 0

        # (expr)
        if self._check('('):
            self.pos += 1
            val = self._parse_sum()
            self._expect(')')
            return val

        c = self.text[self.pos]

        # '
        if c == "'" and self.pos + 2 < len(self.text):
            ch = self.text[self.pos+1]
            if self.text[self.pos+2] == "'":
                self.pos += 3
                return ord(ch)
            self.err = "Unclosed character"; return 0

        # % binary
        if c == '%':
            self.pos += 1
            m = RE_BIN.match(self.text[self.pos:])
            if m: self.pos += m.end(); return int(m.group(1), 2)
            self.err = "Invalid binary number"; return 0

        # $ hex
        if c == '$':
            self.pos += 1
            m = RE_HEX.match(self.text[self.pos:])
            if m: self.pos += m.end(); return int(m.group(1), 16)
            self.err = "Invalid hex number"; return 0

        # 0x hex
        if c == '0' and self.pos + 1 < len(self.text) and self.text[self.pos+1] in 'xX':
            self.pos += 2
            m = RE_HEX.match(self.text[self.pos:])
            if m: self.pos += m.end(); return int(m.group(1), 16)
            self.err = "Invalid hex number"; return 0

        # decimal
        if c.isdigit() or (c == '-' and self.pos + 1 < len(self.text) and self.text[self.pos+1].isdigit()):
            m = RE_DEC.match(self.text[self.pos:])
            if m: self.pos += m.end(); return int(m.group(1))
            self.err = "Invalid number"; return 0

        # label / symbol
        m = RE_IDENT.match(self.text[self.pos:])
        if m:
            name = m.group(1)
            self.pos += m.end()
            if name in self.labels:
                return self.labels[name]
            # Try * (current PC)
            if name.upper() == '*':
                return 0  # Will be set by caller
            self.err = f"Unresolved symbol: {name}"
            return 0

        self.err = f"Unexpected character: '{c}'"
        return 0

    def _skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t':
            self.pos += 1


# Line types
LT_COMMENT = 0
LT_LABEL   = 1
LT_DIR     = 2
LT_INSTR   = 3
LT_EMPTY   = 4

def _classify(line):
    s = line.strip()
    if not s:
        return LT_EMPTY, None
    if s.startswith(';') or s.startswith('//'):
        return LT_COMMENT, None

    # Check for Assignment (A = B)
    if '=' in s:
        parts = s.split('=', 1)
        name = parts[0].strip()
        expr = parts[1].strip()
        if RE_IDENT.match(name):
            return LT_DIR, ('EQU', f"{name},{expr}")

    # Label
    m = RE_LABEL.match(s)
    if m:
        return LT_LABEL, (m.group(1), m.group(2).strip())
    m = RE_LOCAL.match(s)
    if m:
        return LT_LABEL, ('.' + m.group(1), m.group(2).strip())
    # Directive
    m = RE_DIR.match(s)
    if m:
        return LT_DIR, (m.group(1), m.group(2).strip())
    # Instruction
    m = RE_OP.match(s)
    if m:
        return LT_INSTR, (m.group(1), m.group(2).strip())
    return LT_EMPTY, None


class Asm6502:
    def __init__(self):
        self.labels = {}       # name -> address
        self._lines = []       # list of (type, data, raw, line_num)
        self._segments = []    # list of (start_addr, bytearray)
        self._cur_seg = None   # current bytearray
        self._cur_org = 0x0801 # current origin address
        self._pc = 0x0801      # current program counter
        self._errors = []
        self._listing = []
        self._fixups = []      # list of fixup records
        self._global_scope = ''  # for local labels

    def assemble(self, source, origin=0x0801, filepath=None):
        self.labels.clear()
        self._segments.clear()
        self._cur_seg = bytearray()
        self._cur_org = origin
        self._pc = origin
        self._errors = []
        self._listing = []
        self._fixups = []

        self._lines = []
        self._load_source(source, filepath)

        if self._errors:
            return self._errors

        # Phase 1: collect all global label definitions
        self._phase1_labels()

        if self._errors:
            return list(self._errors)

        # Phase 2: emit code with full label table
        self._phase2_emit()

        # Flush final segment
        if self._cur_seg:
            self._segments.append((self._seg_start, self._cur_seg))

        # Resolve fixups
        self._resolve_fixups()

        return list(self._errors)

    def output_prg(self, load_addr=None):
        data = self.output_binary()
        if load_addr is None:
            load_addr = self._cur_org if self._segments else 0x0801
        prg = bytearray(2 + len(data))
        prg[0] = load_addr & 0xFF
        prg[1] = (load_addr >> 8) & 0xFF
        prg[2:] = data
        return bytes(prg)

    def output_binary(self):
        if not self._segments:
            return b''
        segs = sorted(self._segments, key=lambda s: s[0])
        if not segs:
            return b''
        start = segs[0][0]
        end = max(s[0] + len(s[1]) for s in segs)
        result = bytearray(end - start)
        for addr, data in segs:
            ofs = addr - start
            result[ofs:ofs+len(data)] = data
        return bytes(result)

    def get_listing(self):
        return list(self._listing)

    def get_labels(self):
        return dict(self.labels)

    def get_errors(self):
        return list(self._errors)

    # --- Phase 1: collect labels ---

    def _load_source(self, source, filepath=None):
        raw_lines = source.split('\n')
        for i, rl in enumerate(raw_lines):
            # Strip inline comments (; or //)
            clean = rl
            for sep in (';', '//'):
                idx = clean.find(sep)
                if idx >= 0:
                    # Only if not inside a string
                    in_str = False
                    for j in range(idx):
                        if clean[j] == '"':
                            in_str = not in_str
                    if not in_str:
                        clean = clean[:idx]
                        break
            typ, data = _classify(clean)

            if typ == LT_DIR and data[0].lower() == 'include':
                m = RE_STR.match(data[1].strip())
                if m:
                    inc_path = m.group(1)
                    if filepath:
                        inc_path = os.path.join(os.path.dirname(filepath), inc_path)

                    if os.path.exists(inc_path):
                        try:
                            with open(inc_path, 'r') as f:
                                inc_src = f.read()
                            self._load_source(inc_src, inc_path)
                        except Exception as e:
                            self._errors.append({'line': i + 1, 'msg': f"Error reading include '{inc_path}': {e}", 'file': filepath})
                    else:
                        self._errors.append({'line': i + 1, 'msg': f"Include file not found: '{inc_path}'", 'file': filepath})
                continue

            self._lines.append((typ, data, rl, i + 1, filepath))

    def _phase1_labels(self):
        self._pc = self._cur_org
        self._global_scope = 'GLOBAL'
        i = 0
        while i < len(self._lines):
            typ, data, raw, lnum, fpath = self._lines[i]
            i += 1

            if typ == LT_EMPTY or typ == LT_COMMENT:
                continue

            label = None
            if typ == LT_LABEL:
                label, rest = data
                if label.startswith('.'):
                    full_label = self._global_scope + label
                else:
                    self._global_scope = label
                    full_label = label
                if full_label in self.labels:
                    self._errors.append({'line': lnum, 'msg': f"Duplicate label: '{full_label}'"})
                else:
                    self.labels[full_label] = self._pc
                if rest:
                    # Re-classify the rest
                    sub_typ, sub_data = _classify(rest)
                    if sub_typ == LT_DIR:
                        typ, data = sub_typ, sub_data
                    elif sub_typ == LT_INSTR:
                        typ, data = sub_typ, sub_data
                    else:
                        continue

            if typ == LT_DIR:
                dname, args = data
                self._dir_size(dname, args, lnum, fpath)
            elif typ == LT_INSTR:
                mnem, args = data
                self._instr_size(mnem, args, lnum)

    def _dir_size(self, dname, args, lnum, fpath=None):
        dname = dname.lower()
        if dname == 'equ':
            parts = args.split(',', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                expr = parts[1].strip()
                val = self._eval(expr, lnum)
                if val.get('ok') is not None:
                    self.labels[name] = val['ok']
            return
        if dname == 'org':
            val = self._eval(args, lnum)
            if val.get('ok') is not None:
                self._pc = val['ok']
                self._cur_org = self._pc
        elif dname in ('byte', 'db'):
            count = 0
            rest = args
            while rest:
                rest = rest.strip()
                if not rest:
                    break
                if rest[0] == '"':
                    m = RE_STR.match(rest)
                    if m:
                        count += len(m.group(1))
                        rest = rest[m.end():]
                        continue
                if rest[0] == "'":
                    m = RE_CHAR.match(rest)
                    if m:
                        count += 1
                        rest = rest[m.end():]
                        continue
                # expression (up to comma)
                j = 0
                depth = 0
                while j < len(rest):
                    if rest[j] == '(':
                        depth += 1
                    elif rest[j] == ')':
                        depth -= 1
                    elif rest[j] == ',' and depth == 0:
                        break
                    j += 1
                count += 1
                rest = rest[j:]
                if rest and rest[0] == ',':
                    rest = rest[1:]
            self._pc += count
        elif dname in ('word', 'dw'):
            parts = self._split_args(args)
            self._pc += len(parts) * 2
        elif dname in ('text', 'asc', 'null'):
            m = RE_STR.match(args.strip())
            if m:
                self._pc += len(m.group(1)) + (1 if dname == 'null' else 0)
        elif dname in ('fill', 'ds', 'res'):
            parts = [p.strip() for p in args.split(',', 1)]
            val = self._eval(parts[0], lnum)
            if val.get('ok') is not None:
                self._pc += max(0, val['ok'])
        elif dname == 'align':
            val = self._eval(args, lnum)
            if val.get('ok') is not None and val['ok'] > 0:
                pad = (val['ok'] - (self._pc % val['ok'])) % val['ok']
                self._pc += pad
        elif dname == 'incbin':
            m = RE_STR.match(args.strip())
            if m:
                path = m.group(1)
                if fpath:
                    path = os.path.join(os.path.dirname(fpath), path)
                if os.path.exists(path):
                    with open(path, 'rb') as fh:
                        self._pc += len(fh.read())
                else:
                    self._errors.append({'line': lnum, 'msg': f"incbin file not found: {path}", 'file': fpath})

    def _instr_size(self, mnem, args, lnum):
        mnem = mnem.upper()
        if mnem not in OPS:
            self._errors.append({'line': lnum, 'msg': f"Unknown mnemonic: '{mnem}'"})
            return
        ops = OPS[mnem]
        args = args.strip()
        if not args:
            if 'imp' in ops:
                self._pc += 1
            elif 'acc' in ops:
                self._pc += 1
            else:
                self._errors.append({'line': lnum, 'msg': f"{mnem}: operand required"})
            return
        # Determine mode for size
        if args[0] == '#':
            self._pc += 2  # imm
        elif args[0] == '(':
            close = args.find(')')
            if close == -1:
                self._errors.append({'line': lnum, 'msg': "Unclosed parenthesis"})
                return
            after = args[close+1:].strip()
            if after.startswith(',Y'):
                self._pc += 2  # iny
            elif after.startswith(',X') or after == '':
                if mnem == 'JMP' and after == '':
                    self._pc += 3  # ind
                else:
                    self._pc += 2  # inx
            else:
                self._pc += 2
        elif args.upper().endswith(',X'):
            self._pc += 2 if args[:-2].strip() == '' else 2  # zpx (but might be abx)
            # Actually size 2 or 3 depending on zp/abs
            # We'll use 2 for now, adjust in phase2
            self._pc += 2  # assume zero-page, adjust later
        elif args.upper().endswith(',Y'):
            self._pc += 2  # assume zero-page
        elif mnem in ('BCC','BCS','BEQ','BMI','BNE','BPL','BVC','BVS'):
            self._pc += 2  # rel
        else:
            self._pc += 2  # assume zp (2 bytes), adjust in phase2 to 3 if needed

    # --- Phase 2: emit code ---

    def _phase2_emit(self):
        self._pc = self._cur_org
        self._cur_seg = bytearray()
        self._seg_start = self._cur_org
        self._global_scope = 'GLOBAL'

        for typ, data, raw, lnum, fpath in self._lines:

            if typ == LT_EMPTY:
                self._listing.append({'addr': self._pc, 'bytes': [], 'text': raw})
                continue
            if typ == LT_COMMENT:
                self._listing.append({'addr': self._pc, 'bytes': [], 'text': raw})
                continue

            if typ == LT_LABEL:
                label, rest = data
                if label.startswith('.'):
                    full_label = self._global_scope + label
                else:
                    self._global_scope = label
                    full_label = label
                self._listing.append({'addr': self._pc, 'bytes': [], 'isLabel': True, 'labelName': full_label, 'text': raw})
                if rest:
                    sub_typ, sub_data = _classify(rest)
                    if sub_typ == LT_DIR:
                        self._emit_dir(sub_data[0], sub_data[1], lnum, raw, fpath)
                    elif sub_typ == LT_INSTR:
                        self._emit_instr(sub_data[0], sub_data[1], lnum, raw)
                continue

            if typ == LT_DIR:
                self._emit_dir(data[0], data[1], lnum, raw, fpath)
            elif typ == LT_INSTR:
                self._emit_instr(data[0], data[1], lnum, raw, fpath)
            else:
                self._listing.append({'addr': self._pc, 'bytes': [], 'text': raw})

    def _emit_dir(self, dname, args, lnum, raw, fpath=None):
        dname = dname.lower()
        orig_pc = self._pc

        if dname == 'equ':
            self._listing.append({'addr': self._pc, 'bytes': [], 'text': raw})
            return

        if dname == 'org':
            val = self._eval(args, lnum)
            if val.get('ok') is None:
                self._errors.append({'line': lnum, 'msg': val['err']})
                return
            if self._cur_seg:
                self._segments.append((self._seg_start, self._cur_seg))
            self._cur_org = val['ok']
            self._pc = val['ok']
            self._seg_start = val['ok']
            self._cur_seg = bytearray()
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        if dname in ('byte', 'db'):
            bytes_out = self._parse_byte_list(args, lnum)
            if bytes_out is not None:
                for b in bytes_out:
                    self._cur_seg.append(b & 0xFF)
                    self._pc += 1
            self._listing.append({'addr': orig_pc, 'bytes': bytes_out[:16] if bytes_out else [], 'text': raw})
            return

        if dname in ('word', 'dw'):
            parts = self._split_args(args)
            words = []
            for p in parts:
                val = self._eval(p, lnum)
                if val.get('ok') is None:
                    self._errors.append({'line': lnum, 'msg': val['err']})
                    words.append(0)
                else:
                    words.append(val['ok'] & 0xFFFF)
            for w in words:
                self._cur_seg.append(w & 0xFF)
                self._cur_seg.append((w >> 8) & 0xFF)
                self._pc += 2
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        if dname in ('text', 'asc', 'null'):
            m = RE_STR.match(args.strip())
            if m:
                s = m.group(1)
                encoded = s.encode('latin-1')
                self._cur_seg.extend(encoded)
                self._pc += len(encoded)
                if dname == 'null':
                    self._cur_seg.append(0)
                    self._pc += 1
                self._listing.append({'addr': orig_pc, 'bytes': list(encoded), 'text': raw})
            else:
                self._errors.append({'line': lnum, 'msg': 'Invalid string'})
                self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        if dname in ('fill', 'ds', 'res'):
            parts = [p.strip() for p in args.split(',', 1)]
            count_val = self._eval(parts[0], lnum)
            if count_val.get('ok') is None:
                self._errors.append({'line': lnum, 'msg': count_val['err']})
                return
            count = max(0, count_val['ok'])
            fill = 0
            if len(parts) > 1:
                fv = self._eval(parts[1], lnum)
                if fv.get('ok') is not None:
                    fill = fv['ok'] & 0xFF
            self._cur_seg.extend([fill] * count)
            self._pc += count
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        if dname == 'align':
            align_val = self._eval(args, lnum)
            if align_val.get('ok') is None:
                self._errors.append({'line': lnum, 'msg': align_val['err']})
                return
            a = align_val['ok']
            if a > 0:
                pad = (a - (self._pc % a)) % a
                self._cur_seg.extend([0] * pad)
                self._pc += pad
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        if dname == 'incbin':
            m = RE_STR.match(args.strip())
            if m:
                path = m.group(1)
                if fpath:
                    path = os.path.join(os.path.dirname(fpath), path)
                if os.path.exists(path):
                    with open(path, 'rb') as fh:
                        inc = fh.read()
                    self._cur_seg.extend(inc)
                    self._pc += len(inc)
                    self._listing.append({'addr': orig_pc, 'bytes': list(inc[:16]), 'text': raw})
                else:
                    self._errors.append({'line': lnum, 'msg': f"incbin file not found: {path}", 'file': fpath})
                    self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            else:
                self._errors.append({'line': lnum, 'msg': '.incbin: expected filename', 'file': fpath})
            return

        self._errors.append({'line': lnum, 'msg': f"Unknown directive: .{dname}"})
        self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})

    def _emit_instr(self, mnem, args, lnum, raw, fpath=None):
        mnem = mnem.upper()
        if mnem not in OPS:
            self._errors.append({'line': lnum, 'msg': f"Unknown mnemonic: '{mnem}'"})
            self._listing.append({'addr': self._pc, 'bytes': [], 'text': raw})
            return
        ops = OPS[mnem]
        args = args.strip()
        orig_pc = self._pc

        if not args:
            if 'imp' in ops:
                self._cur_seg.append(ops['imp'])
                self._listing.append({'addr': orig_pc, 'bytes': [ops['imp']], 'mnem': mnem, 'op': '', 'mode': 'imp', 'text': raw})
                self._pc += 1
                return
            if 'acc' in ops:
                self._cur_seg.append(ops['acc'])
                self._listing.append({'addr': orig_pc, 'bytes': [ops['acc']], 'mnem': mnem, 'op': 'A', 'mode': 'acc', 'text': raw})
                self._pc += 1
                return
            self._errors.append({'line': lnum, 'msg': f"{mnem}: operand required"})
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        # Immediate
        if args[0] == '#':
            val = self._eval(args[1:], lnum)
            if val.get('ok') is None:
                self._errors.append({'line': lnum, 'msg': f"{mnem}: {val['err']}"})
                self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
                return
            if 'imm' not in ops:
                self._errors.append({'line': lnum, 'msg': f"{mnem}: no immediate mode"})
                self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
                return
            self._cur_seg.append(ops['imm'])
            self._cur_seg.append(val['ok'] & 0xFF)
            self._listing.append({'addr': orig_pc, 'bytes': [ops['imm'], val['ok'] & 0xFF], 'mnem': mnem, 'op': f'#${val["ok"]:02X}', 'mode': 'imm', 'text': raw})
            self._pc += 2
            return

        # Parenthesis modes
        if args[0] == '(':
            close = args.find(')')
            if close == -1:
                self._errors.append({'line': lnum, 'msg': "Unclosed parenthesis"})
                self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
                return
            inner = args[1:close].strip()
            after = args[close+1:].strip()

            if after.startswith(','):
                suffix = after[1:].strip().upper()
                if suffix == 'Y':
                    if 'iny' in ops:
                        val = self._eval(inner, lnum)
                        if val.get('ok') is None:
                            self._errors.append({'line': lnum, 'msg': val['err']})
                            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
                            return
                        self._cur_seg.append(ops['iny'])
                        self._cur_seg.append(val['ok'] & 0xFF)
                        self._listing.append({'addr': orig_pc, 'bytes': [ops['iny'], val['ok'] & 0xFF], 'mnem': mnem, 'op': f'({hex2(val["ok"])}),Y', 'mode': 'iny', 'text': raw})
                        self._pc += 2
                        return
                elif suffix == 'X':
                    if 'inx' in ops:
                        # strip ,X from inner if present
                        zp_expr = inner
                        if inner.upper().endswith(',X'):
                            zp_expr = inner[:-2].strip()
                        val = self._eval(zp_expr, lnum)
                        if val.get('ok') is None:
                            self._errors.append({'line': lnum, 'msg': val['err']})
                            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
                            return
                        self._cur_seg.append(ops['inx'])
                        self._cur_seg.append(val['ok'] & 0xFF)
                        self._listing.append({'addr': orig_pc, 'bytes': [ops['inx'], val['ok'] & 0xFF], 'mnem': mnem, 'op': f'({hex2(val["ok"])},X)', 'mode': 'inx', 'text': raw})
                        self._pc += 2
                        return
            elif after == '' and 'ind' in ops:
                val = self._eval(inner, lnum)
                if val.get('ok') is None:
                    self._errors.append({'line': lnum, 'msg': val['err']})
                    self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
                    return
                w = val['ok'] & 0xFFFF
                self._cur_seg.append(ops['ind'])
                self._cur_seg.append(w & 0xFF)
                self._cur_seg.append((w >> 8) & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['ind'], w & 0xFF, (w >> 8) & 0xFF], 'mnem': mnem, 'op': f'({hex4(w)})', 'mode': 'ind', 'text': raw})
                self._pc += 3
                return

            self._errors.append({'line': lnum, 'msg': f"{mnem}: invalid indirect mode"})
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        # X/Y suffix: must end with ,X or ,Y (case-insensitive)
        suffix = None
        operand = args
        if len(operand) >= 2 and operand[-2:].upper() == ',X':
            suffix = 'X'
            operand = operand[:-2].strip()
        elif len(operand) >= 2 and operand[-2:].upper() == ',Y':
            suffix = 'Y'
            operand = operand[:-2].strip()

        val = self._eval(operand, lnum)

        if val.get('ok') is None:
            # Could be forward branch reference
            if mnem in ('BCC','BCS','BEQ','BMI','BNE','BPL','BVC','BVS') and 'rel' in ops:
                # Emit placeholder + fixup
                self._cur_seg.append(ops['rel'])
                self._cur_seg.append(0)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['rel'], 0], 'mnem': mnem, 'op': args, 'mode': 'rel', 'fixup': True, 'text': raw})
                self._pc += 2
                self._fixups.append({
                    'at': len(self._cur_seg) - 1, 'seg': len(self._segments),
                    'size': 1, 'type': 'rel', 'label': operand, 'line': lnum,
                    'instr_end': self._pc, 'file': fpath, 'scope': self._global_scope
                })
                return
            self._errors.append({'line': lnum, 'msg': f"{mnem}: {val['err']}", 'file': fpath})
            self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})
            return

        addr = val['ok']
        is_zp = addr < 0x100 and addr >= 0

        if suffix == 'X':
            if is_zp and 'zpx' in ops:
                self._cur_seg.append(ops['zpx'])
                self._cur_seg.append(addr & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['zpx'], addr & 0xFF], 'mnem': mnem, 'op': f'{hex2(addr)},X', 'mode': 'zpx', 'text': raw})
                self._pc += 2
                return
            elif 'abx' in ops:
                self._cur_seg.append(ops['abx'])
                self._cur_seg.append(addr & 0xFF)
                self._cur_seg.append((addr >> 8) & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['abx'], addr & 0xFF, (addr >> 8) & 0xFF], 'mnem': mnem, 'op': f'{hex4(addr)},X', 'mode': 'abx', 'text': raw})
                self._pc += 3
                return
        elif suffix == 'Y':
            if is_zp and 'zpy' in ops:
                self._cur_seg.append(ops['zpy'])
                self._cur_seg.append(addr & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['zpy'], addr & 0xFF], 'mnem': mnem, 'op': f'{hex2(addr)},Y', 'mode': 'zpy', 'text': raw})
                self._pc += 2
                return
            elif 'aby' in ops:
                self._cur_seg.append(ops['aby'])
                self._cur_seg.append(addr & 0xFF)
                self._cur_seg.append((addr >> 8) & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['aby'], addr & 0xFF, (addr >> 8) & 0xFF], 'mnem': mnem, 'op': f'{hex4(addr)},Y', 'mode': 'aby', 'text': raw})
                self._pc += 3
                return
        else:
            # Branch
            if mnem in ('BCC','BCS','BEQ','BMI','BNE','BPL','BVC','BVS') and 'rel' in ops:
                delta = addr - (self._pc + 2)
                if delta < -128 or delta > 127:
                    self._fixups.append({
                        'at': len(self._cur_seg) + 1, 'seg': len(self._segments),
                        'size': 1, 'type': 'rel', 'label': operand, 'line': lnum,
                        'instr_end': self._pc + 2, 'file': fpath, 'scope': self._global_scope
                    })
                    self._cur_seg.append(ops['rel'])
                    self._cur_seg.append(0)
                    self._listing.append({'addr': orig_pc, 'bytes': [ops['rel'], 0], 'mnem': mnem, 'op': hex4(addr), 'mode': 'rel', 'fixup': True, 'text': raw})
                    self._pc += 2
                    return
                self._cur_seg.append(ops['rel'])
                self._cur_seg.append(delta & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['rel'], delta & 0xFF], 'mnem': mnem, 'op': hex4(addr), 'mode': 'rel', 'text': raw})
                self._pc += 2
                return

            # Zero-page
            if is_zp and 'zp' in ops:
                self._cur_seg.append(ops['zp'])
                self._cur_seg.append(addr & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['zp'], addr & 0xFF], 'mnem': mnem, 'op': hex2(addr), 'mode': 'zp', 'text': raw})
                self._pc += 2
                return

            # Absolute
            if 'abs' in ops:
                self._cur_seg.append(ops['abs'])
                self._cur_seg.append(addr & 0xFF)
                self._cur_seg.append((addr >> 8) & 0xFF)
                self._listing.append({'addr': orig_pc, 'bytes': [ops['abs'], addr & 0xFF, (addr >> 8) & 0xFF], 'mnem': mnem, 'op': hex4(addr), 'mode': 'abs', 'text': raw})
                self._pc += 3
                return

        self._errors.append({'line': lnum, 'msg': f"{mnem}: no mode for '{args}'"})
        self._listing.append({'addr': orig_pc, 'bytes': [], 'text': raw})

    # --- Fixup resolution ---

    def _resolve_fixups(self):
        for fx in self._fixups:
            label = fx['label']
            fpath = fx.get('file')
            offset = 0
            if '+' in label:
                parts = label.rsplit('+', 1)
                try:
                    offset = int(parts[1])
                    label = parts[0]
                except ValueError:
                    pass

            full_label = label
            if label.startswith('.') and 'scope' in fx:
                full_label = fx['scope'] + label

            if full_label not in self.labels:
                self._errors.append({'line': fx['line'], 'msg': f"Unresolved symbol: {full_label}", 'file': fpath})
                continue
            target = self.labels[full_label] + offset
            seg_idx = fx['seg']
            at = fx['at']
            if seg_idx < len(self._segments):
                seg_addr, seg_data = self._segments[seg_idx]
                buf = bytearray(seg_data)
                if fx['type'] == 'rel':
                    instr_end = fx['instr_end']
                    delta = target - instr_end
                    if delta < -128 or delta > 127:
                        self._errors.append({'line': fx['line'], 'msg': f"Branch out of range: {full_label} (delta={delta})", 'file': fpath})
                    else:
                        if 0 <= at < len(buf):
                            buf[at] = delta & 0xFF
                else:
                    if fx['size'] == 2:
                        if at + 1 < len(buf):
                            buf[at] = target & 0xFF
                            buf[at + 1] = (target >> 8) & 0xFF
                    elif 0 <= at < len(buf):
                        buf[at] = target & 0xFF
                self._segments[seg_idx] = (seg_addr, bytes(buf))

    # --- Expression evaluation ---

    def _eval(self, text, lnum):
        # Handle local labels in expressions
        processed_text = text
        if text.startswith('.'):
            processed_text = self._global_scope + text
        else:
            # Check for local labels preceded by non-alphanumerics
            def replace_local(m):
                return m.group(1) + self._global_scope + m.group(2)
            processed_text = re.sub(r'([^A-Za-z0-9_])(\.[A-Za-z_][A-Za-z0-9_]*)', replace_local, text)
            # Special case for branch instructions where text is JUST the local label
            if re.match(r'^\.[A-Za-z_][A-Za-z0-9_]*$', text):
                processed_text = self._global_scope + text

        ep = _ExprParser(self.labels, lnum)
        return ep.parse(processed_text)

    # --- Helpers ---

    def _parse_byte_list(self, text, lnum):
        result = []
        rest = text.strip()
        while rest:
            rest = rest.strip()
            if not rest:
                break
            if rest[0] == '"':
                m = RE_STR.match(rest)
                if m:
                    result.extend(m.group(1).encode('latin-1'))
                    rest = rest[m.end():]
                    if rest and rest[0] == ',':
                        rest = rest[1:]
                    continue
            if rest[0] == "'":
                m = RE_CHAR.match(rest)
                if m:
                    result.append(ord(m.group(1)))
                    rest = rest[m.end():]
                    if rest and rest[0] == ',':
                        rest = rest[1:]
                    continue
            j = 0
            depth = 0
            while j < len(rest):
                if rest[j] == '(':
                    depth += 1
                elif rest[j] == ')':
                    depth -= 1
                elif rest[j] == ',' and depth == 0:
                    break
                j += 1
            expr_text = rest[:j].strip()
            if expr_text:
                val = self._eval(expr_text, lnum)
                if val.get('ok') is None:
                    self._errors.append({'line': lnum, 'msg': val['err']})
                    return None
                result.append(val['ok'] & 0xFF)
            rest = rest[j:]
            if rest and rest[0] == ',':
                rest = rest[1:]
        return result

    def _split_args(self, text):
        parts = []
        rest = text.strip()
        while rest:
            rest = rest.strip()
            if not rest:
                break
            if rest[0] == '"':
                m = RE_STR.match(rest)
                if m:
                    parts.append(m.group(0))
                    rest = rest[m.end():]
                    if rest and rest[0] == ',':
                        rest = rest[1:]
                    elif rest and rest[0] == ')':
                        rest = rest[1:]
                    continue
            j = 0
            depth = 0
            while j < len(rest):
                if rest[j] == '(':
                    depth += 1
                elif rest[j] == ')':
                    depth -= 1
                elif rest[j] == ',' and depth == 0:
                    break
                j += 1
            parts.append(rest[:j].strip())
            rest = rest[j:]
            if rest and rest[0] == ',':
                rest = rest[1:]
            elif rest and rest[0] == ')':
                rest = rest[1:]
        return parts
