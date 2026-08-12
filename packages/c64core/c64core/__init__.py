# C64 Shared Core Constants and Utilities

# Hardware Address Constants
VIC_BASE = 0xD000
SID_BASE = 0xD400
CIA1_BASE = 0xDC00
CIA2_BASE = 0xDD00

# VIC-II Register Offsets / Addresses
VIC_SPRITE0_X = 0xD000
VIC_SPRITE0_Y = 0xD001
VIC_MSB_X = 0xD010
VIC_CTRL1 = 0xD011
VIC_RASTER = 0xD012
VIC_SPRITE_ENABLE = 0xD015
VIC_CTRL2 = 0xD016
VIC_MEM_POINTERS = 0xD018
VIC_BORDER_COLOR = 0xD020
VIC_BG_COLOR = 0xD021

# SID Register Offsets / Addresses
SID_VOICE1_FREQ_LO = 0xD400
SID_VOICE1_FREQ_HI = 0xD401
SID_VOICE1_PULSE_LO = 0xD402
SID_VOICE1_PULSE_HI = 0xD403
SID_VOICE1_CONTROL = 0xD404
SID_VOICE1_ATTACK_DECAY = 0xD405
SID_VOICE1_SUSTAIN_RELEASE = 0xD406
SID_VOLUME_FILTER = 0xD418

# KERNAL Vectors
KERNAL_RESET = 0xFFFC
KERNAL_IRQ = 0xFFFE
KERNAL_NMI = 0xFFFA

# Zero Page Limits
ZP_START = 0x00
ZP_END = 0xFF


# --- PETSCII Converter ---

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
