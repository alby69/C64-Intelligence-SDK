# C64PY Hardware DSL Architecture

This document describes the 4-level abstraction layer for Commodore 64 hardware programming in C64PY, as outlined in the project ROADMAP.

## Level 0: Native Operations
The lowest level involves direct memory access and assembly instructions.
- `poke(53280, 0)`
- `peek(53280)`
- `asm("LDA #$00")`

## Level 1: Named Symbols
Instead of magic numbers, use named constants extracted from the hardware manuals.
- `from pyc64c.lib.hw.vic import BORDER_COLOR`
- `poke(BORDER_COLOR, BLACK)`

## Level 2: Hardware Operations
Functional abstractions that hide the implementation details (like 16-bit handling or bit masking).
- `from pyc64c.lib.hw.vic import set_border`
- `set_border(RED)`
- `set_sprite_expand_y(0xFF)`

## Level 3: Component Abstractions
High-level Python classes that manage complex hardware states and multiple registers.
- `from pyc64c.lib.hw.high_level import Sprite`
- `s = Sprite(0)`
- `s.enable()`
- `s.pos(300, 100)` (Automatically handles the X-MSB bit)

## Level 4: System Framework (Future)
Context managers and declarative hardware definitions.
- `with RasterIRQ(line=100): vic.border = RED`
- `with SID.Voice(1) as v: v.play_note(C4)`

---
*Note: This library is partially generated from "Mapping the 64" documentation.*
