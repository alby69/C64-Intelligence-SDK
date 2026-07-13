# C64 Intelligence SDK

**Piattaforma integrata per lo sviluppo su Commodore 64** — un ecosistema completo che unisce AI generativa, compilazione cross-platform, ricerca semantica (RAG) e debug low-level in emulatore.

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
│           │            ┌─────┴───────────────────┴──────────┐      │        │
│           │            │  C64-KB-Agent (kb-agent/)          │      │        │
│           │            │  RAG & Registers Microservice (API)│◄─────┘        │
│           │            └─────────────────┬──────────────────┘               │
│           │                              │                                  │
│           │            ┌─────────────────┴──────────────────┐               │
│           └───────────►│  C64-Debugger (debugger/)          │               │
│                        │  VICE Monitor Bridge (Socket API)  │               │
│                        └────────────────────────────────────┘               │
│                                                                             │
│        ┌──────────────────────────────────────────────────────────┐         │
│        │        Shared Logic Packages (c64validator, c64extractor)│         │
│        └──────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Componenti dell'Ecosistema (Submoduli)

### 1. C64-LLM — Assistente AI Multi-Agente (`core/`)
Assistente alla programmazione specializzato per Commodore 64 basato su **Qwen2.5-Coder**, capace di generare codice **Assembly 6502** e **BASIC v2** con architettura multi-agente e sistema RAG con Self-Healing ricorsivo.

### 2. PYC64 — Compilatore Python→C64 (`tools/`)
Cross-compilatore che traduce codice **Python-like** in **Assembly 6502** e lo assembla in file `.PRG` nativi per Commodore 64. Include una TUI IDE completa.

### 3. C64GameTutorial — Manuale di Programmazione Arcade (`tutorial/`)
Manuale didattico completo (Italiano + Inglese) per creare videogiochi arcade su Commodore 64, con decine di esempi, soluzioni e automazione di test in VICE.

### 4. C64-Scrapy — Data Acquisition Framework (`scraper/`)
Framework basato su Scrapy per estrarre documentazione tecnica, sorgenti e metadata da portali specializzati (C64-Wiki, Codebase64, Archive.org), alimentando in streaming la base di conoscenza.

### 5. C64-KB-Agent — RAG & Knowledge Base Centralizzata (`kb-agent/`)
Microservizio centralizzato basato su **FastAPI**, **Sentence-Transformers** e **FAISS**. Fornisce API per l'indicizzazione semantica, la ricerca vettoriale e la risoluzione di indirizzi di memoria e registri hardware (VIC-II, SID, CIA 1, CIA 2) con bit-breakdown ed esempi di codice.

### 6. C64-Debugger-Agent — Debugging Low-Level (`debugger/`)
Subprogetto dedicato all'interfaccia a basso livello con l'emulatore. Implementa un client socket binario monitor per la connessione diretta a VICE (porta 6510) per estrarre lo stato dei registri, effettuare step e diagnosticare i crash.

### 7. Shared Packages (`packages/`)
Librerie Python condivise per standardizzare l'esecuzione in tutti i moduli:
- **c64validator**: Motore di validazione. Include simulatore py6502, stima cicli di clock e wrapper per assembler ACME.
- **c64extractor**: Suite di estrazione dati per formati C64 (PRG, D64, G64) con detokenizer BASIC v2 e disassemblatore automatico.
- **c64debugger**: Shared debugging logic con supporto al monitor socket di VICE.

---

## Architettura Decoupled

L'SDK implementa una strategia di disaccoppiamento dove le logiche complesse sono isolate in sottomoduli e pacchetti indipendenti. Questo garantisce:
- **Modularità**: I sottomoduli di compilazione, dell'AI e del debugger consumano le stesse librerie condivise (`packages/`).
- **Ottimizzazione di Memoria**: Centralizzando la computazione vettoriale (RAG) nel microservizio `C64-KB-Agent`, l'interfaccia utente dell'AI (`core`) e il compilatore (`tools`) rimangono leggeri e veloci.
- **Interoperabilità**: Qualsiasi modulo dell'ecosistema può interrogare l'API di `C64-KB-Agent` per ottenere tooltip e informazioni dettagliate sui registri fisici del C64.

Per i dettagli sulla visione di sviluppo e sul piano d'azione globale, consulta il file [ROADMAP.md](ROADMAP.md).

---

## Guida Rapida all'Installazione

### Prerequisiti
- Docker e Docker Compose
- Python 3.10+
- ACME Assembler (opzionale per validazione nativa senza Docker)

### Setup Completo (Docker)

La suite Docker Compose orchestra l'intero ecosistema in modo centralizzato:

1. **Scarica il modello GGUF per CPU (AI Assistant)**:
   ```bash
   mkdir -p data/models
   wget -O data/models/qwen2.5-coder-1.5b.Q4_K_M.gguf \
     https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
   ```

2. **Compilazione delle immagini**:
   ```bash
   docker compose build
   ```

3. **Avvio del microservizio RAG & Knowledge Base (`kb-agent`)**:
   ```bash
   docker compose up -d kb-agent
   ```

4. **Avvio dell'interfaccia Gradio (C64 AI Assistant UI)**:
   ```bash
   docker compose up c64-ui
   ```

### Avvio Nativo Locale (Senza Docker)

È possibile installare e testare individualmente ciascun componente. Ad esempio, per il microservizio Knowledge Base:

```bash
# Entra nel sottomodulo
cd kb-agent

# Crea ed attiva l'ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa in modalità editable
pip install -r requirements.txt
pip install -e .

# Esegui i test di validazione
python3 -m pytest kb_agent/tests/ -v

# Avvia l'applicazione
uvicorn kb_agent.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Automazione e Gestione Submodule

Questo pacchetto integra uno script avanzato per automatizzare la gestione e l'allineamento dei sottomoduli Git, evitando errori di detached HEAD o conflitti di puntatori.

### Comandi Principali

#### 1. Stato di tutti i sottomoduli (active branch, commit, dirty status)
```bash
docker compose run --rm sdk-updater status
# Oppure localmente:
./scripts/update-submodules.sh status
```

#### 2. Aggiornamento automatico da remoto (Scenario B)
Sincronizza, scarica gli ultimi aggiornamenti di ciascun sottomodulo e riallinea i puntatori nel collettore principale:
```bash
# Esegue update e merge dei sottomoduli
docker compose run --rm sdk-updater update

# Sincronizza ed effettua anche il push del collettore principale
docker compose run --rm sdk-updater update --push
```

#### 3. Sviluppo e Sincronizzazione locale (Scenario A)
Se stai modificando il codice direttamente all'interno delle cartelle dei sottomoduli (es. `core/` o `kb-agent/`), puoi eseguire il commit e push automatico nei rispettivi sottomoduli avanzandone il puntatore nell'SDK:
```bash
docker compose run --rm sdk-updater dev-sync -m "feat: aggiunte rotte per registri SID" --push
```

#### 4. Ripristino di emergenza
Se vuoi riportare tutti i sottomoduli allo stato esatto tracciato dall'SDK (annullando modifiche locali):
```bash
docker compose run --rm sdk-updater reset --hard
```

---

## Licenza

L'ecosistema utilizza licenze Open Source (GPL v3.0, MIT, CC BY 4.0) a seconda del sottomodulo specifico. Consultare i singoli repository per i dettagli.

*Progetto ideato e sviluppato da Alberto Abate (@alby69) per preservare e potenziare l'arte della programmazione su sistemi 8-bit.*
