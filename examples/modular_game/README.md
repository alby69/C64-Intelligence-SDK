# Modular Game Example

This project demonstrates how to structure a medium-sized C64 assembly project using Turbo Macro Pro (TMP) style modularity, now supported by the `pyc64c` assembler.

## Structure

- `MAIN.asm`: Entry point, BASIC stub, and main orchestration.
- `CONSTANTS.asm`: Hardware register definitions and game constants.
- `ZEROPAGE.asm`: Variable definitions in the zero page.
- `IRQ.asm`: Raster interrupt initialization and handler.
- `PLAYER.asm`: Player movement and sprite management.
- `GAMELOOP.asm`: High-level game logic updates.
- `DATA.asm`: Binary assets (sprites, etc.) included via `.fill` or `.incbin`.

## Features

- **Include files**: Uses `.include "file.asm"` to pull in modules.
- **Assignments**: Uses `LABEL = VALUE` for constants and variables.
- **Local labels**: Uses `.local_label` for scope-limited branching (relative to the last global label).
- **Raster IRQ**: Stable(ish) raster interrupt example.
- **Joystick Input**: Reads Port 2 joystick for movement.

## Building

To compile the project:

```bash
python3 run_c64.py compile examples/modular_game/MAIN.asm
```

This will generate `MAIN.prg` which can be run on a C64 or emulator.
