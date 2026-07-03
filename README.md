# PYC64 — Python-to-C64 Cross-Compiler & TUI IDE

PYC64 is a powerful development toolkit for the Commodore 64, providing a Python-like language that compiles directly to 6502 machine code.

**This project is a core component of the [C64-Intelligence-SDK](https://github.com/alby69/C64-Intelligence-SDK), acting as the primary compilation engine and developer interface (`tools/` pillar).**

It provides:
- A high-level **Python-like** language with type annotations.
- A built-in **6502 Macro Assembler**.
- A modern **TUI (Terminal User Interface)** IDE built with Textual.
- Seamless integration with **C64-LLM** for AI-assisted programming.
- An integrated **6502 Simulator** for rapid testing.

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
