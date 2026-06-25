"""C64 CIA2 Interface (Level 1 & 2)"""

# CI2PRA Data Port Register A Bits 0-1: Select the 16K VIC-II chip memory bank (ll=bank 0, 00= bank 3)...
CIA2_DATA_A = 56576
def set_cia2_data_a(val: byte):
    poke(56576, val)

def get_cia2_data_a() -> byte:
    return peek(56576)

# Timer A (low byte) 56581 $DD05 TI2AHI Timer A (high byte) 56582 $DD06 TI2BLO Timer B (low byte) 5658...
TI2ALO = 56580
def set_ti2alo(val: byte):
    poke(56580, val)

def get_ti2alo() -> byte:
    return peek(56580)

# T02MIN Time of Day Clock Minutes Bits 0-3: Second digit of Time of Day minutes (BCD) Bits 4-6: First...
OA = 56586
def set_oa(val: byte):
    poke(56586, val)

def get_oa() -> byte:
    return peek(56586)

# CI2CRA Control Register A Bit 0: Start Timer A (l=start, O=stop) Bit 1: Select Timer A output on Por...
OE = 56590
def set_oe(val: byte):
    poke(56590, val)

def get_oe() -> byte:
    return peek(56590)
