"""C64 CIA1 Interface (Level 1 & 2)"""

# 56325 Timer...
TIMALO = 56324
def set_timalo(val: byte):
    poke(56324, val)

def get_timalo() -> byte:
    return peek(56324)
