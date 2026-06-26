"""Common Hardware Abstractions"""

def set_reg(addr: word, val: byte):
    poke(addr, val)

def get_reg(addr: word) -> byte:
    return peek(addr)
