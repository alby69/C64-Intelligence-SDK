# C64 Ecosystem — Analisi Architetturale e Roadmap

## Panoramica

Questo documento analizza l'ecosistema di repository GitHub creato da **Alberto Abate (@alby69)** per lo sviluppo su **Commodore 64**. I cinque repository formano un sistema integrato che copre generazione AI, compilazione, formazione tecnica e acquisizione dati.

---

## 1. I 5 Repository

| Repository | Ruolo | Descrizione |
|------------|-------|-------------|
| **C64-Intelligence-SDK** | Hub / Orchestrator | Meta-repository che aggrega gli altri come submodules. Orchestra i servizi Docker. |
| **C64-LLM** | Core AI | Assistente multi-agente (Researcher, Coder, Validator). Genera Assembly 6502 e BASIC v2. |
| **PYC64** | Toolchain | Compilatore Python-like → Assembly 6502 → `.PRG`. Include TUI IDE. |
| **C64GameTutorial** | Documentazione | Manuale didattico IT+EN (~24.000 righe). Pipeline CI/CD di validazione. |
| **C64-Scrapy** | Data Acquisition | Framework Scrapy per estrarre documentazione tecnica da siti web. |

---

## 2. Sovrapposizioni Critiche (Overlaps)

1. **Web Crawling**: C64-LLM ha un crawler interno (`c64_asm_scraper.py`) che duplica le funzioni di C64-Scrapy.
2. **Validazione Codice**: C64-LLM e C64GameTutorial hanno sistemi di validazione indipendenti.
3. **Estrazione Formati**: Il parsing di D64/G64/PRG è confinato in C64-LLM ma è una funzione generica.
4. **Knowledge Base**: La documentazione è sparsa tra manuali in C64-LLM, C64GameTutorial e output di C64-Scrapy.
5. **Assemblatori**: Molteplici toolchain in uso (ACME, TMPx, assembler interno di PYC64).

---

## 3. Strategia di Disaccoppiamento (Roadmap)

### Fase 1 — Estrazione Moduli (In corso)
Creazione di package Python indipendenti utilizzabili da tutto l'ecosistema:
- **c64validator**: Estratto da `core/utils/`. Include simulatore py6502 e wrapper ACME.
- **c64extractor**: Estratto da `core/pipeline/`. Gestisce D64/G64/PRG e detokenizer BASIC.

### Fase 2 — Integrazione e Uniformità
- **C64-LLM**: Usare i nuovi package invece delle utility interne.
- **PYC64**: Integrare `c64validator` per feedback in tempo reale nell'IDE.
- **C64-Scrapy**: Diventare l'unico fornitore di dati web per la Knowledge Base.

### Fase 3 — Servizi Centralizzati
- **C64-KB-Service**: Un servizio API centralizzato per il RAG (FAISS + Embedding).
- **C64-Validator-Service**: API di validazione e simulazione remota.

---

## 4. Architettura Target

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     C64-Intelligence-SDK (Hub)                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐               │
│  │  C64-LLM        │  │  PYC64       │  │  C64GameTutorial│               │
│  │  (AI Agent)     │  │  (IDE/Comp)  │  │  (Docs/Learn)   │               │
│  └────────┬────────┘  └──────┬───────┘  └────────┬────────┘               │
│           │                  │                   │                        │
│           └──────────────────┼───────────────────┘                        │
│                              ▼                                            │
│        ┌──────────────────────────────────────────────────────────┐      │
│        │        Shared Logic Packages (c64validator, c64extractor)│      │
│        └──────────────────────────────────────────────────────────┘      │
│                              ▲                                            │
│              ┌───────────────┴───────────────┐                          │
│              │       C64-KB-Service (RAG)    │                          │
│              └───────────────┬───────────────┘                          │
│                              ▲                                            │
│                    ┌─────────┴──────────┐                               │
│                    │     C64-Scrapy     │                               │
│                    └────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

*Documento aggiornato in base all'analisi dell'integrazione py6502 e piano di disaccoppiamento.*
