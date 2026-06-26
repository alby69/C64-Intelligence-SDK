"""C64 SID Interface (Level 1 & 2)"""

# l Voice 1 Frequency Control (low byte) 54273 $D401 FREHIl Voice 1 Frequency Control (high byte) Loca...
SID_V1_FREQ_LO = 54272
def set_sid_v1_freq_lo(val: byte):
    poke(54272, val)

def get_sid_v1_freq_lo() -> byte:
    return peek(54272)

# l Voice 1 Attack/Decay Register Bits 0-3: Select decay cycle duration (0-15) Bits 4-7: Select attack...
SID_V1_AD = 54277
def set_sid_v1_ad(val: byte):
    poke(54277, val)

def get_sid_v1_ad() -> byte:
    return peek(54277)

# l Voice 1 Sustain/Release Control Register Bits 0-3: Select release cycle duration (0-15) Bits 4-7: ...
SID_V1_SR = 54278
def set_sid_v1_sr(val: byte):
    poke(54278, val)

def get_sid_v1_sr() -> byte:
    return peek(54278)

# Voice 2 Control Register Bit 0: Gate Bit: l=Start attack/decay /sustain, 0=Start release Bit 1: Sync...
VCREG2 = 54283
def set_vcreg2(val: byte):
    poke(54283, val)

def get_vcreg2() -> byte:
    return peek(54283)

# Bits 0-2: Low portion of filter cutoff frequency Bits 5-7: Unused 54294 $D416 CUTHI Filter Cutoff Fr...
CUTLO = 54293
def set_cutlo(val: byte):
    poke(54293, val)

def get_cutlo() -> byte:
    return peek(54293)

# Read Game Paddle 1 (or 3) Position 54298 $D41A POTY Read Game Paddle 2 (or 4) Position 54299 $D41B R...
POTX = 54297
def set_potx(val: byte):
    poke(54297, val)

def get_potx() -> byte:
    return peek(54297)

# Envelope Generator 3 Output This register allows you to read the output of the voice 3 Envelope gene...
ENV3 = 54300
def set_env3(val: byte):
    poke(54300, val)

def get_env3() -> byte:
    return peek(54300)
