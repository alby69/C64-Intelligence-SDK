import os
import sys
import pytest

# Ensure parents can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pyc64c.compiler import compile_to_prg
from c64kit.core.memory import C64Memory
from c64kit.video.vic import VICII
from c64kit.audio.sid import SID

def test_hello_ecosystem_compilation():
    src = """def main() -> byte:
    poke(53280, 0)
    poke(53269, 1)  # Enable Sprite 0
    return 0
"""
    prg_bytes, res = compile_to_prg(src)
    assert res.success
    assert prg_bytes is not None
    assert len(prg_bytes) > 0

def test_mcp_and_emulation():
    mem = C64Memory()
    vic = VICII(mem)
    sid = SID(mem)

    # Verify hardware mapped VIC border
    vic.set_border_color(2) # Red
    assert mem.read(0xD020) == 2

    # Verify hardware mapped SID Voice 1 Low Freq
    sid.play_tone_voice(0, 0x12, 0x34, 0x11, True)
    assert mem.read(0xD400) == 0x12
    assert mem.read(0xD401) == 0x34
