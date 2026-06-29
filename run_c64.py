#!/usr/bin/env python3
"""
PYC64 CLI — Compile C64PY (.c64) source to BASIC/ASM/PRG and run via c64py.

Usage:
  python3 run_c64.py compile input.c64              → output .bas, .asm, .prg
  python3 run_c64.py run input.c64                  → compile + run in c64py emulator
  python3 run_c64.py basic input.c64                → generate BASIC only
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyc64c.compiler import compile_source, compile_to_prg, hex2, hex4
from pyc64c.code_emitter import PRG_LOAD_ADDR, PRG_CODE_OFFSET


def cmd_basic(args):
    src = read_source(args.input)
    result = compile_source(src)
    if result.lex_errors:
        for e in result.lex_errors:
            print(f"[LEXER ERROR] {e['msg']} ({e.get('line',0)}:{e.get('col',0)})", file=sys.stderr)
        sys.exit(1)
    if result.parse_errors:
        for e in result.parse_errors:
            print(f"[PARSER ERROR] {e['msg']} ({e.get('line',0)}:{e.get('col',0)})", file=sys.stderr)
        sys.exit(1)
    print(result.basic_code)


def cmd_compile(args):
    base = os.path.splitext(args.input)[0]
    ext = os.path.splitext(args.input)[1].lower()

    if ext == '.asm':
        from pyc64c.asm6502 import Asm6502
        asm = Asm6502()
        src = read_source(args.input)
        errs = asm.assemble(src, filepath=args.input)
        if errs:
            for e in errs:
                print(f"[ASM ERROR] {e['msg']} (line {e.get('line',0)})", file=sys.stderr)
            sys.exit(1)
        prg_data = asm.output_prg()
        print(f"[ASM]    {args.input} compiled")
    else:
        src = read_source(args.input)
        prg_data, result = compile_to_prg(src)

        # Save BASIC
        bas_path = base + '.bas'
        with open(bas_path, 'w') as f:
            f.write(result.basic_code)
        print(f"[BASIC] {bas_path}")

        if result.lex_errors:
            for e in result.lex_errors:
                print(f"[LEXER ERROR] {e['msg']} ({e.get('line',0)}:{e.get('col',0)})", file=sys.stderr)
        if result.parse_errors:
            for e in result.parse_errors:
                print(f"[PARSER ERROR] {e['msg']} ({e.get('line',0)}:{e.get('col',0)})", file=sys.stderr)

    if prg_data:
        prg_path = base + '.prg'
        with open(prg_path, 'wb') as f:
            f.write(prg_data)
        print(f"[PRG]    {prg_path} ({len(prg_data)} byte)")
        print(f"[LOAD]   ${PRG_LOAD_ADDR:04X}")
        print(f"[CODE]   ${PRG_CODE_OFFSET:04X}")
        print(f"[SIZE]   {len(prg_data)} byte")

        # ASM hex dump
        asm_path = base + ('.lst' if ext == '.asm' else '.asm')
        with open(asm_path, 'w') as f:
            f.write(hex_dump(prg_data))
        print(f"[ASM]    {asm_path}")
    else:
        print("[ERROR] Compilation failed", file=sys.stderr)
        sys.exit(1)


def cmd_run(args):
    """Compile and run in c64py emulator."""
    input_path = args.input

    # Detect if input is already a .prg file
    if input_path.endswith('.prg'):
        with open(input_path, 'rb') as f:
            prg_data = f.read()
        print(f"[LOAD]   {input_path} ({len(prg_data)} byte)")
    else:
        src = read_source(input_path)
        prg_data, result = compile_to_prg(src)

        if result.lex_errors:
            for e in result.lex_errors:
                print(f"[LEXER ERROR] {e['msg']} ({e.get('line',0)}:{e.get('col',0)})", file=sys.stderr)
        if result.parse_errors:
            for e in result.parse_errors:
                print(f"[PARSER ERROR] {e['msg']} ({e.get('line',0)}:{e.get('col',0)})", file=sys.stderr)

        if not prg_data:
            print("[ERROR] Compilation failed, cannot run", file=sys.stderr)
            sys.exit(1)

    # Save PRG file (only if we compiled from source)
    if not input_path.endswith('.prg'):
        prg_path = os.path.splitext(input_path)[0] + '.prg'
        with open(prg_path, 'wb') as f:
            f.write(prg_data)
        print(f"[PRG]    {prg_path} ({len(prg_data)} byte)")
    else:
        prg_path = input_path

    # Find VICE ROMs
    vice_dirs = [
        '/usr/local/share/vice/C64',
        '/usr/share/vice/C64',
        '/usr/lib/vice/C64',
    ]
    rom_dir = None
    for d in vice_dirs:
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'basic-901226-01.bin')):
            rom_dir = d
            break
    if not rom_dir:
        rom_dir = '.'
        print(f"[C64]    Warning: C64 ROMs not found. Copy ROM files to {rom_dir}", file=sys.stderr)

    # Run in c64py
    print("[C64]    Starting c64py emulator...")
    try:
        from c64py import C64
        c64 = C64(
            enable_sid=args.sid,
            enable_resid=args.resid,
            vic_emulation='fast'
        )
        c64.load_roms(rom_dir)
        c64.initialize_iec_bus()

        # Use c64py's auto-load mechanism (loads after BASIC boot)
        c64.prg_file_path = prg_path

        print("[C64]    Running... (Ctrl+C to stop)")
        import time
        start = time.time()
        while True:
            c64.run(max_cycles=50000)
            if time.time() - start > args.timeout:
                print(f"[C64]    Timeout ({args.timeout}s)")
                break
    except ImportError:
        print("[C64]    c64py not installed. Install with: pip install c64py", file=sys.stderr)
        print("[C64]    PRG was generated anyway. Use VICE: x64sc " + prg_path, file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[C64]    Stopped by user")
    except Exception as e:
        print(f"[C64]    Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()


def read_source(path):
    with open(path, 'r') as f:
        return f.read()


def hex_dump(prg_data):
    lines = []
    lines.append(f"; C64PY — PRG Hex Dump  ({len(prg_data)} byte)")
    lines.append(f"; Load addr: ${PRG_LOAD_ADDR:04X}")
    lines.append(f"; Code start: ${PRG_CODE_OFFSET:04X}")
    lines.append("")
    for i in range(0, len(prg_data), 8):
        chunk = prg_data[i:i + 8]
        hex_str = ' '.join(f'${b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"+{i:04X}  {hex_str:<29}  {ascii_str}")
    lines.append("")
    lines.append(f"LOAD \"file\",8,1")
    lines.append(f"SYS {PRG_CODE_OFFSET}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='PYC64 — C64PY Compiler & Emulator')
    sub = parser.add_subparsers(dest='command')

    p_compile = sub.add_parser('compile', help='Compila .c64 → .prg + .bas + .asm')
    p_compile.add_argument('input', help='File sorgente .c64')
    p_compile.add_argument('--basic-only', action='store_true', help='Genera solo BASIC')

    p_basic = sub.add_parser('basic', help='Genera solo BASIC da .c64')
    p_basic.add_argument('input', help='File sorgente .c64')

    p_run = sub.add_parser('run', help='Compila + esegui in c64py emulator')
    p_run.add_argument('input', help='File sorgente .c64')
    p_run.add_argument('--sid', action='store_true', help='Abilita SID')
    p_run.add_argument('--resid', action='store_true', help='Abilita reSID')
    p_run.add_argument('--timeout', type=int, default=30, help='Timeout secondi (default 30)')

    args = parser.parse_args()
    if args.command == 'basic':
        cmd_basic(args)
    elif args.command == 'compile':
        cmd_compile(args)
    elif args.command == 'run':
        cmd_run(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
