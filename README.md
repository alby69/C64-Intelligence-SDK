# PYC64 — Python-to-C64 Cross-Compiler & TUI IDE

Compiles **Python-like** code into native **Commodore 64** machine code,
assembles **6502** assembly into `.PRG` files,
and provides a **TUI** (Terminal User Interface) editor — all in pure Python.

---

## Quick Start with Docker

```bash
# First build (only once)
docker compose build

# Launch TUI: editor, compilation, BASIC/listing/hex tabs
docker compose run --rm pyc64
```

Or using Make:

```bash
make build   # docker compose build
make run     # docker compose run --rm pyc64
```

---

## Useful Commands

```bash
# Compile test_python.c64 → output/test_python.prg
docker compose run --rm compile

# Assemble examples/hello.asm → output/hello.prg
docker compose run --rm asm

# Clean output directory
rm -rf output/*
```

---

## TUI (Textual) — Features

```
┌────────── Header ───────────╮
│ ┌─ Editor ───┐ ┌─ Tabs ───┐ │
│ │ Source     │ │ BASIC    │ │
│ │ .c64       │ │ Listing  │ │
│ │            │ │ Hex      │ │
│ └────────────┘ └──────────┘ │
│ ┌── Error Panel ───────────┐│
│ │ ✓ No errors              ││
│ └──────────────────────────┘│
└────────── Footer ───────────┘
```

| Key | Action |
|-------|--------|
| `Ctrl+S` | Save and compile |
| `Ctrl+O` | Open file |
| `F1` | Help |
| `Ctrl+Q` | Quit |

---

## Project Structure

| Path         | Description |
|--------------|-------------|
| `pyc64c/`    | Compiler core (Lexer, Parser, Codegen, Runtime, Assembler) |
| `pyc64_ui/`  | Textual-based TUI (Editor, Tabs, Controller) |
| `examples/`  | Example source files (.c64 and .asm) |

---

## Authors & Credits

**Author:** Alberto Abate
**Email:** alberto.abate@gmail.com
**Repository:** (https://github.com/alby69/pyc64)

Original concept by Leonardo Boselli.
Developed with the assistance of Claude (Anthropic).

---

## License

This project is licensed under the **GNU General Public License v3.0**.
Respect all third-party code licenses included in this repository.
