"""Compiler Documentation."""

# PYC64 Compiler

The PYC64 compiler translates Python-like source code into Commodore 64 machine code.

## Language Specification

The language is a subset of Python with explicit type annotations for variables.

### Types

- `byte`: 8-bit unsigned integer (0-255).
- `word`: 16-bit unsigned integer (0-65535).
- `int`: 16-bit signed integer.
- `bool`: Boolean (`True` or `False`).
- `str`: String literal.

### Syntax

- **Indentation**: Scoping is defined by indentation (4 spaces).
- **Functions**: Defined using `def name(param: type) -> ret_type:`.
- **Loops**: `while cond:` and `for i in range(start, end):`.
- **Conditionals**: `if`, `elif`, `else`.

## Built-ins

- `print(value)`: Output to screen.
- `poke(address, value)`: Write byte to memory.
- `peek(address)`: Read byte from memory.
- `wait_frames(n)`: Pause for `n` video frames.
- `clear_screen()`: Clear the PETSCII screen.

## Compilation Process

Source (.c64) → Lexer → Parser → Memory Planning → Code Generation → Assembly → PRG (.prg)
