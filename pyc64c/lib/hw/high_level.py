"""High-level Level 3 Abstractions for C64 Hardware"""

from .vic import *
from .colors import *

class Sprite:
    def __init__(self, index: byte):
        self.index = index
        self.mask = 1 << index

    def enable(self):
        v = get_sprite_enable()
        set_sprite_enable(v | self.mask)

    def disable(self):
        v = get_sprite_enable()
        set_sprite_enable(v & (255 ^ self.mask))

    def pos(self, x: word, y: byte):
        # Set Y
        addr_y = 53249 + (self.index << 1)
        poke(addr_y, y)

        # Set X lo
        addr_x = 53248 + (self.index << 1)
        poke(addr_x, x & 255)

        # Set X hi (MSB)
        msb = peek(53264)
        if x > 255:
            set_sprite_msb_x(msb | self.mask)
        else:
            set_sprite_msb_x(msb & (255 ^ self.mask))

    def color(self, col: byte):
        addr = 53287 + self.index
        poke(addr, col)

class RasterIRQ:
    """Prototype for Raster IRQ management"""
    def __init__(self, line: byte):
        self.line = line

    def setup(self):
        sei()
        # Disable CIA 1 timer interrupts to avoid interference
        poke(56333, 127)

        # Set raster line to trigger on
        set_raster_line(self.line)

        # Set MSB of raster line (Bit 7 of $D011) to 0
        v = get_vic_ctrl1()
        set_vic_ctrl1(v & 127)

        # Enable Raster IRQ in VIC
        m = get_vic_irq_mask()
        set_vic_irq_mask(m | 1)

        # Acknowledgement of existing IRQs
        set_vic_irq_status(255)

        cli()

# Global instances for convenience
Sprite0 = Sprite(0)
Sprite1 = Sprite(1)
Sprite2 = Sprite(2)
Sprite3 = Sprite(3)
Sprite4 = Sprite(4)
Sprite5 = Sprite(5)
Sprite6 = Sprite(6)
Sprite7 = Sprite(7)
