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

### 5. C64-KB-Agent — RAG & Knowledge Base Centralizzata (`kb-agent/`)
Microservizio autonomo basato su **FastAPI**, **Sentence-Transformers** e **FAISS** per ospitare ed eseguire interrogazioni semantiche (RAG) e ospitare il database dei registri hardware, alleggerendo l'uso di memoria RAM delle UI locali.

### 6. Shared Packages (`packages/`)
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

## Automazione Submodule

Questo pacchetto automatizza il workflow multi-repo descritto nel documento **IMPLEMENTATION_SPEC_AND_GUIDE.md** (Paragrafo 2), eliminando la necessità di comandi git manuali per spostarsi tra i repository dei sottomoduli.

### Prerequisito: `.gitmodules`
Il file `.gitmodules` è pre-configurato con il parametro `branch = main` per tracciare correttamente i branch remoti.

### Comandi Principali

#### Scenario B — Aggiornamento da remoto (documento, par. 2)
Hai lavorato su un repo separato (es. C64-LLM), hai fatto push su GitHub e ora vuoi "riagganciare" le modifiche nel collettore:

```bash
# Via Docker (consigliato)
docker compose run --rm sdk-updater update

# Aggiorna e pusha il collettore
docker compose run --rm sdk-updater update --push

# Forza l'update anche se ci sono modifiche locali non committate (esegue lo stash automatico)
docker compose run --rm sdk-updater update --force
```

#### Scenario A — Sviluppo locale nei submodule (documento, par. 2)
Hai modificato i file direttamente dentro `core/` o `tools/` e vuoi committare e pushare tutto:

```bash
# Commit e push automatici di tutti i sottomoduli dirty, poi aggiorna il parent
docker compose run --rm sdk-updater dev-sync -m "feat: nuova integrazione VICE"

# Come sopra ma pusha anche il collettore
docker compose run --rm sdk-updater dev-sync -m "feat: nuova integrazione VICE" --push
```

#### Utility di Stato e Manutenzione

```bash
# Stato di tutti i sottomoduli (branch, commit, modifiche)
docker compose run --rm sdk-updater status

# Sincronizza gli URL da .gitmodules
docker compose run --rm sdk-updater sync

# Reset di emergenza (torna ai commit tracciati dal parent)
docker compose run --rm sdk-updater reset
docker compose run --rm sdk-updater reset --hard
```

#### Esecuzione nativa (senza Docker)

Se preferisci non usare Docker, puoi lanciare lo script direttamente dal tuo terminale:
```bash
./scripts/update-submodules.sh status
./scripts/update-submodules.sh update --push
./scripts/update-submodules.sh dev-sync -m "fix: bug raster"
```

### Cosa fa automaticamente lo script
1. **Rileva detached HEAD**: se un sottomodulo è in stato detached, lo script esegue il checkout del branch corretto impostando il tracking con `origin/<branch>`.
2. **Fetch remoto**: esegue `git fetch origin` per ciascun sottomodulo.
3. **Merge**: esegue `git merge origin/<branch>` per importare i nuovi commit.
4. **Gestione conflitti**: se un merge fallisce, abortisce automaticamente e segnala l'errore senza lasciare il repository sporco.
5. **Commit parent**: esegue `git add <submodule>` nel collettore e crea un commit con messaggio standardizzato (`chore(submodules): update <path> to <commit>`).
6. **Push opzionale**: se usi `--push`, effettua il push del collettore su origin.

---

## Struttura del Repository

```
C64-Intelligence-SDK/
├── core/                    # C64-LLM — Assistente AI (Submodule)
├── tools/                   # PYC64 — IDE e Compilatore (Submodule)
├── tutorial/                # C64GameTutorial — Manuale (Submodule)
├── scraper/                 # C64-Scrapy — Crawler (Submodule)
├── kb-agent/                # C64-KB-Agent — RAG & Knowledge Base (Submodule)
├── debugger/                # C64-Debugger — Debugger a basso livello (Submodule)
├── packages/                # Package Python Condivisi
│   ├── c64validator/        # Validazione e Simulazione
│   └── c64extractor/        # Estrazione e Disassembly
├── scripts/                 # Script di automazione e gestione submodule
│   ├── submodule-manager.py # Logica Python per l'automazione
│   └── update-submodules.sh # Wrapper shell di compatibilità
├── Dockerfile.updater       # Dockerfile per il servizio sdk-updater
├── docker-compose.override.yml # Servizio sdk-updater
├── data/                    # Dati condivisi (Volume Docker)
├── docker-compose.yml       # Orchestrazione ecosistema
└── ROADMAP.md               # Evoluzione futura
```

---

## Licenza

L'ecosistema utilizza licenze Open Source (GPL v3.0, MIT, CC BY 4.0) a seconda del modulo. Consultare i singoli repository per i dettagli.

*Progetto sviluppato da Alberto Abate (@alby69) per preservare e potenziare l'arte della programmazione su sistemi 8-bit.*
