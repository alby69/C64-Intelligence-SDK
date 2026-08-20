# Architettura — C64 Intelligence SDK

> Versione: 2.0 · Data: 2026-08-20 · Stato: adottata (ADR-0001 & Roadmap Ecosystem)

## Principio guida: "Massimo Disaccoppiamento & Standalone-first"

Ogni sub-repo nell'ecosistema ha un'identità precisa e confini netti:

- **C64-Scrapy** (`scraper/`): Acquisizione dati da web, spider, REST API (:8001) e notifiche webhook HTTP. Non fa RAG, UI o storage KB.
- **C64-KB-Agent** (`kb-agent/`): Cura, standardizzazione, versioning SemVer, Quality Gate e REST API (:8002) per la Knowledge Base FTS5. Non fa scraping né generazione codice.
- **C64-LLM** (`core/`): Orchestrazione multi-agente, RAG FAISS, Py6502Sandbox isolata, RAGCache. Consuma KB solo via KBAgentClient REST API.
- **C64-Intelligence-SDK** (root): Aggregatore con plugin system, IDE React+Tauri, API Gateway (:8000), EventBus e Telemetria unificata.

Conseguenze operative:
- Nessun repo accede al filesystem di un altro repo.
- Tutta la comunicazione avviene via schemi JSON unificati (`c64-schemas`), REST API o Event Bus HTTP.
- Isolamento runtime tramite `Py6502Sandbox` (processi separati con timeout e controlli di memoria).

## Architecture Overview

```
C64-Intelligence-SDK (orchestratore, IDE, telemetry :8000)
         │
         ├──► C64-Scrapy (API :8001) ──► Webhook HTTP ──► C64-KB-Agent
         │                                                      │
         │                                                      ▼
         ├──► C64-KB-Agent (API :8002) ◄── Event Bus ───────────┘
         │       │
         │       └──► API Documents / Search / Releases / Quality
         │            │
         ▼            ▼
    C64-LLM (core/)
         │
         ├──► KBAgentClient ──► C64-KB-Agent API (:8002)
         ├──► ScrapyClient  ──► C64-Scrapy API (:8001 via SDK proxy)
         ├──► Vector Store  ──► FAISS / RAGCache
         ├──► Sandbox       ──► py6502 isolato (multiprocessing)
         └──► Event Bus     ──► Publisher / Subscriber
```

## Schemi Unificati (`c64-schemas`)

I contratti dati sono formalizzati nel package Python `c64-schemas` (`sdk/schemas/`):

1. **C64Document** (`c64_document.schema.json`): entità documento con ID SHA256 deterministico, source_url, content_type, language, metadata e validation_status.
2. **C64KBManifest** (`c64_kb_manifest.schema.json`): manifest per versioning SemVer della KB (es. `2.1.0`), note di release e hash del dataset.
3. **C64EcosystemEvent** (`events.schema.json`): schema per eventi di sistema (`kb.document.ingested`, `kb.index.rebuilt`, `scrapy.spider.finished`, ecc.).

## Event Bus & Telemetria

- **EventBus** (`sdk/event_bus/`): bus di eventi leggero Redis-less basato su callback locali e HTTP listeners.
- **Telemetry** (`sdk/telemetry/`): `TraceContext` per propagazione `trace_id` e logger strutturato in formato JSON per l'osservabilità end-to-end.
