# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Converts PETSCII byte values to the C64 character ROM screen codes used to look up glyphs,
following the standard conversion table (https://sta.c64.org/cbm64pettoscr.html). This is the
same conversion the KERNAL applies when sending a byte to the screen, which is why control
codes such as CHR$(147) (CLR/HOME) display as the familiar reverse-video heart in listings.
"""

def _build_table() -> list[int]:
    table = [0] * 256
    for petscii in range(256):
        if petscii == 0xFF:
            table[petscii] = 0x5E  # PETSCII $FF (pi) maps directly to screen code $5E
            continue

        if petscii <= 0x1F:
            offset = 0x80
        elif petscii <= 0x3F:
            offset = 0
        elif petscii <= 0x5F:
            offset = -0x40
        elif petscii <= 0x7F:
            offset = -0x20
        elif petscii <= 0x9F:
            offset = 0x40
        elif petscii <= 0xBF:
            offset = -0x40
        else:
            offset = -0x80

        table[petscii] = (petscii + offset) & 0xFF
    return table

_TO_SCREEN_CODE_TABLE = _build_table()

def to_screen_code(petscii: int) -> int:
    """
    Converts a PETSCII byte value to its corresponding C64 character ROM screen code.
    """
    return _TO_SCREEN_CODE_TABLE[petscii & 0xFF]
