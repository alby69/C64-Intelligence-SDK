# C64 Intelligence Studio

IDE moderna per lo sviluppo su Commodore 64. Compila, debugga, emula e sviluppa in BASIC V2 e Assembly 6502 con un'interfaccia desktop basata su React + Tauri + FastAPI e un'architettura a microservizi completamente disaccoppiata.

```
C64-Intelligence-SDK/
├── sdk/              → Unified Schemas (c64-schemas), EventBus, Telemetry & Integration Tests
├── frontend/         → React + Vite + Monaco + TailwindCSS  (interfaccia IDE)
├── services/         → FastAPI backend (core-service :8000, kb-agent :8002)
├── plugins/          → Plugin integrati dai submoduli
├── core/             → C64-LLM         — AI agents, pipeline, KBAgentClient, Py6502Sandbox
├── tools/            → PYC64           — Compilatore C64PY, TUI, simulatore 6502
├── editor/           → READYCode-Py    — Tokenizer, diskimage, bridge VICE/Ultimate
├── tutorial/         → C64GameTutorial — Tutorial e soluzioni assembly
├── scraper/          → C64-Scrapy      — Scraping REST API (:8001) e webhook ingestion
├── kb-agent/         → C64-KB-Agent    — Knowledge base REST API (:8002), versioning, quality gate
├── debugger/         → C64-Debugger    — Debugger VICE remoto
├── geckos/           → GeckOS-NG       — Sistema operativo multitasking 6502
└── gamedev/          → C64-GameDev     — Kit sviluppo giochi (c64kit + c64lib)
```

Per l'architettura (principio "Standalone-first, Integrated-second", mappa moduli, microservizi disaccoppiati, Event Bus) vedere [ARCHITECTURE.md](ARCHITECTURE.md). Per licenze e sicurezza: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) e [SECURITY.md](SECURITY.md).

## Quick Start

```bash
# 1. Inizializza tutti i submoduli e installa gli schemi unificati
./sdk/scripts/bootstrap.sh

# 2. Avvia l'intero ecosistema via Docker Compose
docker compose -f docker-compose.ecosystem.yml up

# Oppure avvia i singoli microservizi in locale:
make setup
make ide-backend   # Core Service su http://localhost:8000
make ide-frontend  # React IDE su http://localhost:5173
```

## Microservizi dell'Ecosistema

| Microservizio | Porta | Descrizione |
|---|---|---|
| **C64-Scrapy** | `8001` | Server REST per trigger spider e scraping on-demand, notifiche webhook HTTP |
| **C64-KB-Agent** | `8002` | Server REST per documenti, FTS5 search, versioning SemVer e Quality Gate |
| **Core Service** | `8000` | Gateway IDE, LSP WebSocket, AI Copilot, Proxy Acquisition e Plugin Execution |

## Plugin System (11 plugin)

I plugin sono attivabili da tre interfacce:

### 1. IDE Grafica (http://localhost:5173)
Sidebar plugin → click per eseguire comandi. Monaco editor + terminale + AI copilot + debugger.

### 2. CLI diretta

```bash
python3 plugins/tutorial/wrapper.py list          # Elenco capitoli
python3 plugins/knowledge/wrapper.py status       # Stato knowledge base
python3 plugins/knowledge/wrapper.py search sprite # Cerca documentazione
python3 plugins/disk-tools/wrapper.py create -o /tmp/test.d64 --label MIOGIOCO
```

### 3. API REST (http://localhost:8000)

```bash
curl http://localhost:8000/api/v1/plugins
curl -X POST http://localhost:8000/api/v1/plugins/tutorial/exec \
  -H "Content-Type: application/json" \
  -d '{"command":"list","cli_args":["list"]}'
```

## Autore

**Alberto Abate** — alberto.abate@gmail.com

## Licenza

GNU General Public License v3.0
