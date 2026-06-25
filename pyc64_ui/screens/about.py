"""About screen — project info and key bindings."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Markdown
from textual.containers import Vertical
from textual.binding import Binding


ABOUT_TEXT = """# PYC64 — Python-to-C64 Cross-Compiler & 6502 Assembler

**v0.2.0** — Pure Python toolkit for Commodore 64 development.

## Key Bindings

| Key | Action |
|-----|--------|
| `Ctrl+S` | Save and compile |
| `Ctrl+O` | File browser (sources + output) |
| `Ctrl+Q` | Quit |
| `F1` | This help |
| `Ctrl+←` | Narrow editor panel |
| `Ctrl+→` | Widen editor panel |
| `Ctrl+↑` | Widen output panel (tabs) |
| `Ctrl+↓` | Widen error panel |
| `Enter` | Open selected file |
| `Del` | Delete selected file |
| `←` `→` | Change file category |

## Pipeline

```
Source (.c64) → Lexer → Parser → CodeGen → PRG (.prg)
                                      └→ BASIC (.bas)
```

## Output directories

| Folder | Content |
|----------|-----------|
| `output/basic/` | Generated BASIC listings |
| `output/asm/` | Saved assembly sources |
| `output/prg/` | Compiled PRG binaries |

## Credits

Author: Alberto Abate
Original concept by Leonardo Boselli.

## License

GNU GPL v3 — © 2024 Alberto Abate
"""


class AboutScreen(Screen):
    """Help / about screen."""

    BINDINGS = [
        Binding('escape', 'dismiss', 'Back'),
        Binding('f1', 'dismiss', 'Close'),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(Markdown(ABOUT_TEXT), id='about-content')
        yield Footer()
