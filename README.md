# C64 Intelligence Studio

IDE moderna per lo sviluppo su Commodore 64. Compila, debugga, emula e sviluppa in BASIC V2 e Assembly 6502 con un'interfaccia desktop basata su React + Tauri + FastAPI.

```
C64-Intelligence-SDK/
├── frontend/         → React + Vite + Monaco + TailwindCSS  (interfaccia IDE)
├── services/         → FastAPI backend con plugin system
├── plugins/          → 10 plugin integrati dai submoduli
├── core/             → C64-LLM         — AI agents, pipeline, knowledge base
├── tools/            → PYC64           — Compilatore C64PY, TUI, simulatore 6502
├── editor/           → READYCode-Py    — Tokenizer, diskimage, bridge VICE/Ultimate
├── tutorial/         → C64GameTutorial — Tutorial e soluzioni assembly
├── scraper/          → C64-Scrapy      — Scraping documentazione C64
├── kb-agent/         → C64-KB-Agent    — Knowledge base (FAISS + SQLite FTS5)
├── debugger/         → C64-Debugger    — Debugger VICE remoto
└── geckos/           → GeckOS-NG       — Sistema operativo multitasking 6502
```

## Quick Start

```bash
# 1. Inizializza tutti i submoduli
git submodule update --init --recursive

# 2. Installa tutto (venv + editor + backend + frontend)
make setup

# 3. Avvia l'IDE (due terminali)
make ide-backend   # Terminale 1 → FastAPI su http://localhost:8000
make ide-frontend  # Terminale 2 → React su http://localhost:5173
```

Poi apri **http://localhost:5173** nel browser. Per l'app desktop nativa:

```bash
make tauri-dev     # Richiede Rust + Cargo + Tauri CLI
```

## Plugin System (10 plugin)

I plugin sono attivabili da tre interfacce:

### 1. IDE Grafica (http://localhost:5173)
Sidebar plugin → click per eseguire comandi. Monaco editor + terminale + AI copilot + debugger.

### 2. CLI diretta

```bash
make plugins  # Elenca tutti i plugin

python3 plugins/tutorial/wrapper.py list          # Elenco capitoli
python3 plugins/tutorial/wrapper.py show 1        # Mostra capitolo 1
python3 plugins/knowledge/wrapper.py status       # Stato knowledge base
python3 plugins/knowledge/wrapper.py search sprite # Cerca documentazione
python3 plugins/disk-tools/wrapper.py create -o /tmp/test.d64 --label MIOGIOCO
python3 plugins/geckos/wrapper.py status          # Stato build GeckOS
python3 plugins/geckos/wrapper.py build           # Compila GeckOS-NG
python3 plugins/debugger/wrapper.py attach        # Connetti a VICE
python3 plugins/ai-agent/wrapper.py status        # Stato agente AI
```

### 3. API REST (http://localhost:8000)

```bash
curl http://localhost:8000/api/v1/plugins
curl -X POST http://localhost:8000/api/v1/plugins/tutorial/exec \
  -H "Content-Type: application/json" \
  -d '{"command":"list","cli_args":["list"]}'
```

## Plugin

| Plugin | Submodule | Comandi |
|--------|-----------|---------|
| **ai-agent** | core/ | generate, explain, optimize, debug, status, search, distill, train |
| **compiler** | tools/ | compile, basic |
| **debugger** | debugger/ | attach, run, step, continue, breakpoint, registers, memory, crash-analyze, disassemble, reset |
| **disk-tools** | editor/ | list, inject, extract, create, format, prg-to-disk, petscii-convert |
| **editor** | tools/ | tokenize, detokenize, minify, prettify |
| **emulator** | editor/ | run, vice-run, vice-attach, vice-step, vice-reset, vice-memory, vice-registers, vice-info, vice-upload |
| **geckos** | geckos/ | build, deploy, run, status |
| **knowledge** | kb-agent/ | search, docs, status, list-api, list-files |
| **project-manager** | tools/ | load, build |
| **tutorial** | tutorial/ | list, show, example, template, search, references |

## CLI (run_c64.py — legacy)

```bash
# Compila .c64 in .prg
python3 run_c64.py compile input.c64
# Genera solo BASIC
python3 run_c64.py basic input.c64
# Tokenizza BASIC → .prg
python3 run_c64.py tokenize input.bas -o output.prg
# Disk image
python3 run_c64.py disk create -o mydisk.d64 "MY DISK"
```

## Docker TUI (legacy)

```bash
make docker-build   # Build immagini Docker
make docker-run     # Avvia TUI terminale (pyc64_ui)
```

## Submoduli

| Percorso | Repository | Plugin |
|----------|-----------|--------|
| `core/` | [C64-LLM](https://github.com/alby69/C64-LLM) | ai-agent |
| `tools/` | [PYC64](https://github.com/alby69/PYC64) | compiler, editor, project-manager |
| `editor/` | [C64-Code](https://github.com/alby69/C64-Code) | disk-tools, emulator |
| `tutorial/` | [C64GameTutorial](https://github.com/alby69/C64GameTutorial) | tutorial |
| `scraper/` | [C64-Scrapy](https://github.com/alby69/C64-Scrapy) | — (alimenta kb-agent) |
| `kb-agent/` | [C64-KB-Agent](https://github.com/alby69/C64-KB-Agent) | knowledge |
| `debugger/` | [C64-Debugger](https://github.com/alby69/C64-Debugger) | debugger |
| `geckos/` | [C64-OS](https://github.com/alby69/C64-OS) | geckos |

## Autore

**Alberto Abate** — alberto.abate@gmail.com

## Licenza

GNU General Public License v3.0
