"""Compiler Architecture Documentation."""

# Compiler Architecture

The PYC64 compiler translates a Python-inspired language into Commodore 64 machine code (6502).

## Pipeline

1.  **Lexer (`lexer.py`)**: Converts source text into tokens. Handles indentation-based scoping.
2.  **Parser (`parser.py`)**: Converts tokens into an Abstract Syntax Tree (AST).
3.  **Memory Planner (`compiler.py`)**: Analyzes the AST and allocates memory for global and local variables. It decides whether to use Zero Page or BSS segments.
4.  **Code Generator (`code_gen.py`)**: Traverses the AST and emits 6502 instructions.
5.  **Runtime Library (`runtime.py`)**: Provides pre-assembled 6502 routines for common tasks (printing, math, screen control).
6.  **PRG Builder (`prg_builder.py`)**: Combines the generated code, a BASIC stub (`SYS 2061`), and the runtime library into a final `.PRG` file.

## Built-in Functions

- `print(val)`: Prints a string or a byte.
- `println(val)`: Same as print, with a newline.
- `print_at(x, y, text)`: Positions the cursor and prints text.
- `poke(addr, val)`: Writes a byte to memory.
- `peek(addr)`: Reads a byte from memory.
- `clear_screen()`: Clears the screen.
- `border_color(color)`: Sets the border color.
- `screen_color(color)`: Sets the screen color.
- `wait_frames(n)`: Waits for `n` frames.
- `sei()` / `cli()`: Disables/Enables interrupts.
