"""C64 VIC Interface (Level 1 & 2)"""

# Sprite 1 Horizontal Position 53251 $D003 sprite 1 Vertical Position 53252 $D004 sprite 2 Horizontal ...
SPRITE1_X = 53250
def set_sprite1_x(val: byte):
    poke(53250, val)

def get_sprite1_x() -> byte:
    return peek(53250)
