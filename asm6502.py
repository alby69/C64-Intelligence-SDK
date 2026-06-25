#!/usr/bin/env python3
"""CLI for the PYC64 6502 assembler — assemble .asm → .prg, list, dump."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyc64c.asm6502 import Asm6502, hex2, hex4

def main():
    if len(sys.argv) < 2:
        print("Usage: asm6502.py <source.asm> [options]")
        print()
        print("Options:")
        print("  -o FILE     Output path (default: <source>.prg)")
        print("  -l          Print annotated listing")
        print("  -L FILE     Write listing to FILE")
        print("  --org ADDR  Set origin address (default: $0801)")
        print("  --raw       Output raw binary (no PRG load address)")
        print("  --labels    Print symbol table")
        print()
        print("Examples:")
        print("  asm6502.py hello.asm")
        print("  asm6502.py hello.asm -l -o hello.prg")
        return 1

    src_path = sys.argv[1]
    out_path = None
    show_listing = False
    listing_file = None
    origin = 0x0801
    raw = False
    show_labels = False

    i = 2
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == '-o' and i + 1 < len(sys.argv):
            out_path = sys.argv[i + 1]
            i += 2
        elif a == '-l':
            show_listing = True
            i += 1
        elif a == '-L' and i + 1 < len(sys.argv):
            listing_file = sys.argv[i + 1]
            i += 2
        elif a == '--org' and i + 1 < len(sys.argv):
            org_str = sys.argv[i + 1]
            if org_str.startswith('$'):
                origin = int(org_str[1:], 16)
            else:
                origin = int(org_str)
            i += 2
        elif a == '--raw':
            raw = True
            i += 1
        elif a == '--labels':
            show_labels = True
            i += 1
        else:
            print(f"Opzione sconosciuta: {a}")
            return 1

    if not os.path.exists(src_path):
        print(f"File non trovato: {src_path}")
        return 1

    with open(src_path) as f:
        source = f.read()

    a = Asm6502()
    errors = a.assemble(source, origin=origin)

    if errors:
        for e in errors:
            print(f"Linea {e['line']}: ERRORE: {e['msg']}")
        return 1

    # Output
    if out_path is None:
        base = os.path.splitext(src_path)[0]
        out_path = base + '.prg'

    if raw:
        data = a.output_binary()
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f"✓ Raw binary ({len(data)} bytes): {out_path}")
    else:
        prg = a.output_prg()
        with open(out_path, 'wb') as f:
            f.write(prg)
        print(f"✓ PRG ({len(prg)} bytes): {out_path}")

    if show_labels:
        print()
        print("Symbol table:")
        for name, addr in sorted(a.get_labels().items(), key=lambda x: x[1]):
            print(f"  {name:20s} = ${addr:04X}")

    if show_listing:
        print()
        print("Annotated listing:")
        for l in a.get_listing():
            addr = l.get('addr', 0)
            bs = ' '.join(hex2(b) for b in l.get('bytes', []))
            if l.get('isLabel'):
                print(f"${addr:04X}  {bs:20s}  {l.get('labelName','')}:")
            elif l.get('fixup'):
                print(f"${addr:04X}  {bs:20s}  {l.get('mnem',''):6s} {l.get('op','')}  [fixup]")
            elif bs:
                print(f"${addr:04X}  {bs:20s}  {l.get('mnem',''):6s} {l.get('op','')}")
            else:
                print(f"${addr:04X}  {'':20s}  {l.get('text','').strip()}")

    if listing_file:
        with open(listing_file, 'w') as f:
            for l in a.get_listing():
                f.write(f"{l.get('addr',0):04X}  {' '.join(hex2(b) for b in l.get('bytes',[])):20s}\n")

    return 0

if __name__ == '__main__':
    sys.exit(main())
