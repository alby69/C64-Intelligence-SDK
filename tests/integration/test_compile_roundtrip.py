"""Test di integrazione end-to-end (Epic F).

Scenario 1 — Compile round-trip: run_c64.py compila un .c64 in un .prg valido.
"""

import os
import subprocess
import sys
import tempfile

import pytest

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_c64(args, cwd=SDK_ROOT):
    return subprocess.run(
        [sys.executable, "run_c64.py"] + args,
        capture_output=True, text=True, cwd=cwd,
    )


class TestCompileRoundTrip:
    def test_compile_c64_to_prg(self, tmp_path):
        src = os.path.join(SDK_ROOT, "examples", "primes.c64")
        assert os.path.isfile(src), "esempio primes.c64 mancante"
        import shutil
        copy = os.path.join(str(tmp_path), "primes.c64")
        shutil.copy2(src, copy)
        result = _run_c64(["compile", copy])
        assert result.returncode == 0, result.stderr
        out = os.path.join(str(tmp_path), "primes.prg")
        assert os.path.isfile(out), "PRG non generato"

        with open(out, "rb") as fh:
            header = fh.read(2)
        # Header PRG: load address little-endian (BASIC start tipicamente $0801)
        load_addr = header[0] | (header[1] << 8)
        assert load_addr == 0x0801, f"load address inatteso: ${load_addr:04X}"

    def test_compile_invalid_c64_fails(self, tmp_path):
        bad = os.path.join(str(tmp_path), "bad.c64")
        with open(bad, "w") as fh:
            fh.write("??invalid??\n")
        result = _run_c64(["compile", bad])
        assert result.returncode != 0