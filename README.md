# C64 Intelligence SDK

Un SDK modulare per lo sviluppo su Commodore 64, che integra compilatore C64PY,
simulatore 6502, TUI editor, agenti AI, knowledge base, scraping e debugger.

## Architettura

```
C64-Intelligence-SDK/
├── core/          → C64-LLM         — AI agents, pipeline, knowledge base
├── tools/         → PYC64           — Compilatore C64PY, TUI, simulatore 6502
├── editor/        → READYCode-Py    — Tokenizer BASIC, .d64/.d81, minify/prettify, bridge
├── tutorial/      → C64GameTutorial — Tutorial e soluzioni assembly
├── scraper/       → C64-Scrapy      — Scraping documentazione C64
├── kb-agent/      → C64-KB-Agent    — Agente knowledge base specializzato
├── debugger/      → C64-Debugger    — Debugger per C64
├── geckos/        → C64-OS          — GeckOS-NG multitasking OS
├── editor-src/    → C64-Code        — READYCode originale (C#/.NET, reference)
│
├── pyc64c.py      → Wrapper: importa tools.pyc64c (compilatore)
├── pyc64_ui.py    → Wrapper: importa tools.pyc64_ui (TUI)
├── run_c64.py     → CLI compilatore + emulatore + editor
└── Makefile       → Docker compose + editor targets
```

## Submoduli

| Percorso | Repository | Ruolo |
|----------|-----------|-------|
| `core/` | [C64-LLM](https://github.com/alby69/C64-LLM) | Agenti AI, pipeline, ciclo di validazione |
| `tools/` | [PYC64](https://github.com/alby69/PYC64) | Compilatore C64PY, TUI, simulatore 6502 |
| `editor/` | [READYCode-Py](https://github.com/alby69/C64-Intelligence-SDK/tree/main/editor) | Tokenizer BASIC V2, .d64/.d81, minify/prettify, bridge C64U/VICE |
| `editor-src/` | [C64Code](https://github.com/alby69/C64Code) | READYCode originale (C#/.NET, reference) |
| `tutorial/` | [C64GameTutorial](https://github.com/alby69/C64GameTutorial) | Tutorial C64 assembler |
| `scraper/` | [C64-Scrapy](https://github.com/alby69/C64-Scrapy) | Scraping documentazione |
| `kb-agent/` | [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent) | Agente knowledge base |
| `debugger/` | [C64-Debugger](https://github.com/alby69/C64-Debugger) | Debugger C64 |
| `geckos/` | [C64-OS](https://github.com/alby69/C64-OS) | Sistema operativo multitasking (GeckOS-NG) |

## Sistema Operativo On-Target

La sottocartella `geckos/os/` contiene l'integrazione di GeckOS-NG con la SDK, includendo applicazioni personalizzate per il Commodore 64: la shell interattiva `tui_editor`, il debugger di sistema `debugger` e il daemon AI di sottofondo `ai_agent`. Consultare `geckos/os/README.md` per maggiori dettagli.

## Quick Start

```bash
# Inizializza tutti i submoduli
git submodule update --init --recursive

# Installa editor (READYCode-Py)
make editor-build

# Build e run con Docker
make build
make run
```

## Comandi CLI

### Compilatore C64PY (`run_c64.py`)

```bash
# Compila un file .c64 in .prg
python3 run_c64.py compile input.c64

# Compila ed esegui in c64py
python3 run_c64.py run input.c64

# Genera solo BASIC
python3 run_c64.py basic input.c64
```

### Editor READYCode (`run_c64.py` o `python3 -m readycode_py`)

```bash
# Tokenizza BASIC → .prg
python3 run_c64.py tokenize input.bas -o output.prg

# Detokenizza .prg → BASIC
python3 run_c64.py detokenize input.prg -o output.bas

# Minifica BASIC (riduce dimensione)
python3 run_c64.py minify input.bas -o compact.bas

# Prettify BASIC (migliora leggibilità)
python3 run_c64.py prettify input.bas -o formatted.bas
```

### Disk Image (.d64/.d81)

```bash
# Crea immagine disco vuota
python3 -m readycode_py disk create -o mydisk.d64 --name "MY DISK"

# Lista directory
python3 -m readycode_py disk list mydisk.d64

# Inserisci file
python3 -m readycode_py disk inject mydisk.d64 program.prg

# Estrai file
python3 -m readycode_py disk extract mydisk.d64 PROGRAM -o extracted.prg

# Elimina file
python3 -m readycode_py disk delete mydisk.d64 PROGRAM

# Rinomina file
python3 -m readycode_py disk rename mydisk.d64 OLDNAME NEWNAME
```

### Bridge Hardware

```bash
# C64 Ultimate — carica ed esegui PRG
python3 -m readycode_py bridge-c64u run --host 192.168.1.100 --file program.prg

# VICE — carica PRG nell'emulatore
python3 -m readycode_py bridge-vice run --file program.prg

# PETSCII — conversione screen code
python3 -m readycode_py petscii $41
```

## Autore

**Alberto Abate** — alberto.abate@gmail.com

## Licenza

GNU General Public License v3.0
