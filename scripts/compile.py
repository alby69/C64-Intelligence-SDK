#!/usr/bin/env python3
"""Compila un file .c64 in .prg. Uso: compile.py [sorgente.c64]"""
import sys, os
sys.path.insert(0, '/app')
from pyc64c.compiler import compile_to_prg

src = sys.argv[1] if len(sys.argv) > 1 else '/app/source/test_python.c64'
with open(src) as f:
    s = f.read()

prg, res = compile_to_prg(s)
if prg:
    base = os.path.splitext(os.path.basename(src))[0]
    out = '/app/output/' + base + '.prg'
    with open(out, 'wb') as f:
        f.write(prg)
    print('OK: ' + out + ' (' + str(len(prg)) + ' bytes)')
else:
    errs = list(res.lex_errors or []) + list(res.parse_errors or [])
    if res.builder:
        errs += list(res.builder.fixup_errs or [])
    for e in errs:
        print(e)
    sys.exit(1)
