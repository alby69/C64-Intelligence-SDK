# C64 Intelligence SDK

**Piattaforma integrata per lo sviluppo su Commodore 64** — un ecosistema completo che combina AI generativa, compilazione cross-platform e formazione tecnica.

```
┌──────────────────────────────────────────────────────────────┐
│                    C64 Intelligence SDK                       │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  C64-LLM (core) │  │  PYC64       │  │  C64GameTutorial │ │
│  │  Assistente AI  │  │  Compilatore │  │  Manuale +       │ │
│  │  Multi-Agente   │  │  Python→C64  │  │  Esercizi ASM    │ │
│  └─────────────────┘  └──────────────┘  └─────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Componenti

### 1. C64-LLM — Assistente AI Multi-Agente (`core/`)

Assistente alla programmazione specializzato per Commodore 64 basato su **Qwen2.5-Coder**, capace di generare codice **Assembly 6502** e **BASIC v2** con architettura multi-agente e sistema RAG.

**Caratteristiche:**
- **Architettura Multi-Agente**: Researcher, Coder, Validator, Orchestrator con Self-Healing
- **C64 Knowledge Engine**: RAG con FAISS, sentence-transformers, indicizzazione vettoriale
- **Wiki Grafo Interattivo**: Mappa concettuale SVG (87 nodi, 105 archi) nella UI Gradio
- **Validator Integrato**: ACME assembler per Assembly, parser sintattico per BASIC v2, Cycle Counter
- **Knowledge Distillation**: Sistema Teacher→Student per specializzare Qwen su C64
- **LoRA Fine-Tuning**: Training su CPU/GPU per adattamento al dominio C64
- **Web Crawler**: Scraping proattivo da 25+ fonti (C64-Wiki, Codebase64, Archive.org, GitHub ecc.)

**Backend LLM supportati:**
- GGUF (llama.cpp) su CPU — `Qwen2.5-Coder-1.5B-Instruct-Q4_K_M`
- HuggingFace Transformers con 4-bit quantization
- LoRA checkpoint loading/unloading runtime

### 2. PYC64 — Compilatore Python→C64 (`tools/`)

Cross-compilatore che traduce codice **Python-like** in **Assembly 6502** e lo assembla in file `.PRG` nativi per Commodore 64.

**Caratteristiche:**
- Compilatore Python→6502 (Lexer, Parser, Codegen, Runtime)
- Assemblatore 6502 integrato
- TUI (Textual IDE) con editor, tabs BASIC/Listing/Hex, pannello errori
- Workflow Dockerizzato con `docker compose`

### 3. C64GameTutorial — Manuale di Programmazione Arcade (`tutorial/`)

Manuale didattico completo (Italiano + Inglese) per creare videogiochi arcade su Commodore 64.

**Contenuti:**
- 27 capitoli + 7 appendici (~12700 righe IT, ~11200 EN)
- 28 soluzioni assembly + template gioco completo
- Dalle basi 6502/Turbo Macro Pro al raster interrupt, SID, sprite multiplex, Arcade OS
- Pipeline di validazione automatica con GitHub Actions

---

## Architettura del Sistema

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    C64-LLM       │     │      PYC64       │     │  C64GameTutorial │
│  (core/)         │     │   (tools/)       │     │  (tutorial/)     │
│                  │     │                  │     │                  │
│  Agent Multi-AI  │◄───►│  Compilatore     │     │  Manuale +       │
│  RAG + Validator │     │  Python→6502     │     │  Esempi .asm     │
│  UI Gradio       │     │  TUI IDE         │     │  Template Gioco  │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    data/  (Volumi Docker)  │
                    │  vectorstore/ models/      │
                    └───────────────────────────┘
```

---

## Guida Rapida all'Installazione

### Prerequisiti
- Docker + Docker Compose
- Python 3.10+ (per esecuzione nativa)
- ACME Assembler (per validazione, incluso nell'immagine Docker)

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

L'interfaccia AI sarà disponibile su `http://localhost:7860`.

### Setup nativo (senza Docker)

```bash
cd core
pip install -r requirements.txt
pip install sentence-transformers faiss-cpu  # per RAG
python -m agent.agent_pro
```

---

## Pipeline Dati

```
PDF/D64/G64/PRG/Archive.org/Siti Web
        │
        ▼
┌─────────────────────────────────────┐
│  Estrattori:                        │
│  - pdf2marker.py / pdf2text.py      │
│  - extract_d64.py / extract_g64.py  │
│  - extract_prg.py                   │
│  - c64_asm_scraper.py / scrape_url  │
│  - download Archive.org / Google Dr.│
└──────────────┬──────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  text_cleaner.py (pulizia testo)    │
│  build_dataset.py (QA pairs)        │
└──────────────┬──────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  C64KnowledgeBase.build_index()     │
│  → sentence-transformers/all-MiniLM│
│  → FAISS vector store               │
│  → data/vectorstore/                │
└──────────────┬──────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  RAG in Chat (contesto → LLM)       │
└─────────────────────────────────────┘
```

---

## Struttura del Repository

```
C64-Intelligence-SDK/
├── core/                    # C64-LLM — Assistente AI Multi-Agente
│   ├── agent/               # Agenti: orchestrator, researcher, coder, validator...
│   ├── pipeline/            # Pipeline dati: estrazione, pulizia, dataset
│   ├── prompts/             # Template prompt (YAML)
│   ├── config/              # Configurazioni YAML (agente, teacher, crawler)
│   ├── knowledge_base/      # Documentazione tecnica C64 (9 manuali .md)
│   ├── utils/               # Utility: cycle counter, prompt manager, validatori
│   ├── docs/                # Documentazione tecnica (9 documenti)
│   ├── tests/               # Test: agenti, validatori, RAG
│   ├── data/                # Dati persistenti (PDF, dataset, modelli, grafo)
│   ├── examples/            # Esempi di integrazione
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run_pipeline.py      # Script pipeline master
│
├── tools/                   # PYC64 — Compilatore Python→C64
│   ├── pyc64c/              # Core compilatore (lexer, parser, codegen, runtime, assembler)
│   ├── pyc64_ui/            # TUI Textual IDE
│   ├── examples/            # Esempi .c64 e .asm
│   ├── docs/                # Documentazione PYC64
│   ├── scripts/             # Script di utility
│   └── Dockerfile + Makefile
│
├── tutorial/                # C64GameTutorial — Manuale Programmazione Arcade
│   ├── md/                  # Manuale originale IT (27 capitoli + appendici)
│   ├── en/                  # Traduzione EN (27 capitoli)
│   ├── soluzioni/           # Soluzioni esercizi (.asm)
│   ├── game/                # Template gioco completo
│   ├── tools/               # Script supporto (validate, size-report, vice-test)
│   ├── data/                # Dati tutorial
│   └── mkdocs.yml           # Configurazione sito documentazione
│
├── data/                    # Dati condivisi (montati come volumi Docker)
│   └── vectorstore/         # Indice FAISS condiviso
│
├── plugins/                 # Logica integrazione "Cheshire-style" (estendibile)
├── docker-compose.yml       # Orchestrazione servizi
└── .gitmodules              # Submodules: core, tools, tutorial
```

---

## Submodules

| Submodule | Repository | Descrizione |
|-----------|-----------|-------------|
| `core/` | [alby69/C64-LLM](https://github.com/alby69/C64-LLM) | Assistente AI Multi-Agente |
| `tools/` | [alby69/PYC64](https://github.com/alby69/PYC64) | Compilatore Python→C64 |
| `tutorial/` | [alby69/C64GameTutorial](https://github.com/alby69/C64GameTutorial) | Manuale programmazione arcade |

---

## Comandi Docker

```bash
# AI Assistant (Gradio UI su :7860)
docker compose up c64-ui

# Pipeline dati: ricostruisci Knowledge Base (RAG)
docker compose run c64-pipeline

# Training LoRA
docker compose run c64-train

# Pipeline manuale
docker compose run c64-pipeline python pipeline/pdf2marker.py /app/data/input/manuale.pdf /app/data/output/manuale
docker compose run c64-pipeline python pipeline/text_cleaner.py /app/data/output/manuale.txt /app/data/output/manuale_clean.txt
docker compose run c64-pipeline python pipeline/build_dataset.py /app/data /app/data/output/dataset_unified.jsonl
docker compose run c64-pipeline python agent/knowledge_base.py

# Per PYC64 TUI (usa docker-compose.yml separato in tools/)
docker compose -f tools/docker-compose.yml run --rm pyc64
```

---

## Riferimenti

- [Documentazione Tecnica C64-LLM](core/docs/TECHNICAL_MANUAL.md)
- [Manuale UI](core/docs/UI_MANUAL.md)
- [Flusso Dati](core/docs/FLUSSO_DATI.md)
- [Wiki Grafo Tutorial](core/docs/WIKI_GRAPH.md)
- [Piano Distillazione](core/docs/PIANO_DISTILLAZIONE.md)
- [Fonti della Conoscenza](core/docs/FONTI_DELLA_CONOSCENZA.md)

---

## Licenza

- **C64-LLM (core/)** — GNU General Public License v3.0
- **PYC64 (tools/)** — GNU General Public License v3.0
- **C64GameTutorial (tutorial/)** — CC BY 4.0 (testo) / MIT (codice)

---

*Progetto sviluppato da Alberto Abate per preservare e potenziare l'arte della programmazione su sistemi 8-bit.*
