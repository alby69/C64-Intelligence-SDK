# C64 Intelligence SDK

Un SDK modulare per lo sviluppo su Commodore 64, che integra compilatore C64PY,
simulatore 6502, TUI editor, agenti AI, knowledge base, scraping e debugger.

## Architettura

```
C64-Intelligence-SDK/
├── core/          → C64-LLM        — AI agents, pipeline, knowledge base
├── tools/         → PYC64          — Compilatore C64PY, TUI, simulatore 6502
├── tutorial/      → C64GameTutorial — Tutorial e soluzioni assembly
├── scraper/       → C64-Scrapy     — Scraping documentazione C64
├── kb-agent/      → C64-KB-Agent   — Agente knowledge base specializzato
├── debugger/      → C64-Debugger   — Debugger per C64
│
├── pyc64c.py      → Wrapper: importa tools.pyc64c (compilatore)
├── pyc64_ui.py    → Wrapper: importa tools.pyc64_ui (TUI)
├── run_c64.py     → CLI compilatore + emulatore c64py
└── Makefile       → Docker compose per build e run
```

## Submoduli

| Percorso | Repository | Ruolo |
|----------|-----------|-------|
| `core/` | [C64-LLM](https://github.com/alby69/C64-LLM) | Agenti AI, pipeline, ciclo di validazione |
| `tools/` | [PYC64](https://github.com/alby69/PYC64) | Compilatore C64PY, TUI, simulatore 6502 |
| `tutorial/` | [C64GameTutorial](https://github.com/alby69/C64GameTutorial) | Tutorial C64 assembler |
| `scraper/` | [C64-Scrapy](https://github.com/alby69/C64-Scrapy) | Scraping documentazione |
| `kb-agent/` | [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent) | Agente knowledge base |
| `debugger/` | [C64-Debugger](https://github.com/alby69/C64-Debugger) | Debugger C64 |

## Quick Start

```bash
# Inizializza tutti i submoduli
git submodule update --init --recursive

# Build e run con Docker
make build
make run
```

## Comandi CLI

```bash
# Compila un file .c64 in .prg
python run_c64.py compile input.c64

# Compila ed esegui in c64py
python run_c64.py run input.c64

# Genera solo BASIC
python run_c64.py basic input.c64
```

## Autore

**Alberto Abate** — alberto.abate@gmail.com

## Licenza

GNU General Public License v3.0
