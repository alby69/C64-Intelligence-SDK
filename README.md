# C64 Intelligence SDK

**Piattaforma integrata per lo sviluppo su Commodore 64** — un ecosistema completo che combina AI generativa, compilazione cross-platform e formazione tecnica.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         C64 Intelligence SDK (Hub)                          │
│                                                                             │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐  ┌───────────┐  │
│  │  C64-LLM (core) │  │  PYC64       │  │  C64GameTutorial│  │C64-Scrapy │  │
│  │  Assistente AI  │  │  Compilatore │  │  Manuale +       │  │ (scraper) │  │
│  │  Multi-Agente   │  │  Python→C64  │  │  Esercizi ASM    │  │ Crawler   │  │
│  └────────┬────────┘  └──────┬───────┘  └────────┬────────┘  └─────┬─────┘  │
│           │                  │                   │                 │        │
│           └──────────────────┼───────────────────┼─────────────────┘        │
│                              ▼                   ▼                          │
│        ┌──────────────────────────────────────────────────────────┐         │
│        │        Shared Logic Packages (c64validator, c64extractor)│         │
│        └──────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Componenti dell'Ecosistema

### 1. C64-LLM — Assistente AI Multi-Agente (`core/`)
Assistente alla programmazione specializzato per Commodore 64 basato su **Qwen2.5-Coder**, capace di generare codice **Assembly 6502** e **BASIC v2** con architettura multi-agente e sistema RAG.

### 2. PYC64 — Compilatore Python→C64 (`tools/`)
Cross-compilatore che traduce codice **Python-like** in **Assembly 6502** e lo assembla in file `.PRG` nativi per Commodore 64. Include una TUI IDE completa.

### 3. C64GameTutorial — Manuale di Programmazione Arcade (`tutorial/`)
Manuale didattico completo (Italiano + Inglese) per creare videogiochi arcade su Commodore 64, con decine di esempi e soluzioni.

### 4. C64-Scrapy — Data Acquisition Framework (`scraper/`)
Framework basato su Scrapy per estrarre documentazione tecnica, sorgenti e metadata da portali specializzati (C64-Wiki, Codebase64, Archive.org), alimentando la Knowledge Base dell'AI.

### 5. Shared Packages (`packages/`)
- **c64validator**: Motore di validazione universale. Include simulatore py6502, stima cicli di clock e wrapper per assembler ACME.
- **c64extractor**: Suite di estrazione dati per formati C64 (PRG, D64, G64) con detokenizer BASIC v2 e disassemblatore automatico.

---

## Architettura Decoupled

L'SDK implementa una strategia di disaccoppiamento dove le logiche core sono estratte in package indipendenti. Questo permette:
- **Modularità**: I toolchain di compilazione e l'AI usano le stesse librerie di validazione.
- **Affidabilità**: Validazione del codice tramite simulazione pure-Python (py6502) senza dipendenze esterne.
- **Efficienza**: Acquisizione dati centralizzata tramite lo scraper dedicato.

Per i dettagli sulla visione a lungo termine, consulta il file [ROADMAP.md](ROADMAP.md).

---

## Guida Rapida all'Installazione

### Prerequisiti
- Docker + Docker Compose
- Python 3.10+
- ACME Assembler (opzionale per validazione nativa)

### Setup rapido (Docker)

```bash
# 1. Scarica il modello GGUF per CPU
mkdir -p data/models
wget -O data/models/qwen2.5-coder-1.5b.Q4_K_M.gguf \
  https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf

# 2. Build dell'immagine
docker compose build

# 3. Avvia interfaccia Gradio (AI Assistant)
docker compose up c64-ui
```

---

## Struttura del Repository

```
C64-Intelligence-SDK/
├── core/                    # C64-LLM — Assistente AI (Submodule)
├── tools/                   # PYC64 — IDE e Compilatore (Submodule)
├── tutorial/                # C64GameTutorial — Manuale (Submodule)
├── scraper/                 # C64-Scrapy — Crawler (Submodule)
├── packages/                # Package Python Condivisi
│   ├── c64validator/        # Validazione e Simulazione
│   └── c64extractor/        # Estrazione e Disassembly
├── data/                    # Dati condivisi (Volume Docker)
├── docker-compose.yml       # Orchestrazione ecosistema
└── ROADMAP.md               # Evoluzione futura
```

---

## Licenza

L'ecosistema utilizza licenze Open Source (GPL v3.0, MIT, CC BY 4.0) a seconda del modulo. Consultare i singoli repository per i dettagli.

*Progetto sviluppato da Alberto Abate (@alby69) per preservare e potenziare l'arte della programmazione su sistemi 8-bit.*
