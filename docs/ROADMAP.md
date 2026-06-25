# ROADMAP

## Current Progress

- **Project Refactoring**: Updated metadata, author info, and translated documentation/comments to English.
- **TUI (Terminal UI)**: Fully functional editor with source, BASIC, and Assembly tabs.
- **Compiler**: Supports basic Python-like syntax, functions, loops, and conditionals. Generates `.PRG` and `.BAS`.

## Future Goals

- **16/32-bit Integers**: Improve the code generator to handle multi-byte arithmetic more efficiently.
- **VIC-II / SID Support**: Add high-level built-ins for sprites, colors, and sound.
- **VSCode Extension**: Syntax highlighting, snippets, and integrated build tasks for a modern development experience.
- **Native C64 Tools**: A small assembly-based tool to load and run scripts directly on the machine.
- **Graphics Library**: Simple primitives for high-resolution graphics.
- **Hardware DSL Architecture**: Implementing a 4-level abstraction layer for C64 hardware.
    - *Level 0*: Pure Assembly / Native POKE.
    - *Level 1*: Named memory symbols and registers.
    - *Level 2*: Hardware operations (e.g., `set_border(RED)`).
    - *Level 3*: High-level components (e.g., `Sprite` objects, `RasterIRQ` context managers).
- **Automated Documentation Extraction**: PDF/EPUB to Markdown extraction for automated hardware library generation.
