# C64-Intelligence-SDK — Master Roadmap & Evolution Plan

> **Versione:** 2.1-strategic
> **Data:** 2026-07-16
> **Autore:** Team di Architettura C64-Intelligence-SDK & Alberto Abate
> **Stato:** Approvata & Inizializzata

---

## 1. Visione di Insieme dell'Ecosistema

Il **C64-Intelligence-SDK** si sta evolvendo da un insieme di strumenti e script sparsi a una piattaforma integrata di sviluppo assistito da intelligenza artificiale per il Commodore 64, posizionandosi come un **ambiente di sviluppo integrato (IDE) "AI-Native" di nuova generazione**, ispirato al glorioso **CBM .prg Studio** ma proiettato verso il futuro grazie a funzionalità AI profondamente integrate nel workflow dello sviluppatore.

La filosofia cardine del progetto rimane il **disaccoppiamento forte (loose coupling)**. Ogni componente dell'ecosistema è un'unità autonoma (gestita come sottomodulo Git) che espone API ben definite. Questa separazione garantisce la manutenibilità e permette a ciascun modulo di evolvere in modo indipendente o di essere eseguito come servizio standalone.

### Componenti dell'Ecosistema Attuale

1. **`core/` (C64-LLM)**: Il cervello dell'ecosistema. Gestisce l'orchestrazione multi-agente, la pipeline RAG semantica, la validazione, l'integrazione con modelli locali (nanoGPT) ed esterni, e implementa il ciclo di auto-guarigione (*self-healing*) del codice.
2. **`tools/` (PYC64)**: Il motore di compilazione e l'IDE testuale (TUI). Include il compilatore per il linguaggio `C64PY` (Python-like), il macro-assemblatore 6502, un simulatore e l'interfaccia basata su libreria Textual (`pyc64_ui`).
3. **`kb-agent/` (C64-KB-Agent)**: Il servizio di Knowledge Base semantica. Espone endpoint REST per l'indicizzazione dei documenti e la ricerca semantica con FAISS + Sentence-Transformers, oltre a un risolutore di indirizzi fisici del C64.
4. **`debugger/` (C64-Debugger)**: L'agente di runtime e diagnostica. Gestisce breakpoint, watchpoint, tracciamento dell'esecuzione e un client socket verso il protocollo monitor dell'emulatore VICE.
5. **`scraper/` (C64-Scrapy)**: Il motore di recupero delle informazioni. Effettua lo scraping mirato da siti storici (Codebase64, C64 Wiki, ecc.) per alimentare la Knowledge Base.
6. **`tutorial/` (C64GameTutorial)**: Risorse educative e soluzioni assembly pre-convalidate utilizzate per regression testing e training dell'AI.

---

## 2. Analisi Comparativa: C64 Intelligence SDK (Stato Attuale) vs CBM .prg Studio (Target)

| Area | C64 Intelligence SDK (Stato Attuale) | CBM .prg Studio (Target) | Gap Critico / Strategia di Copertura |
|------|--------------------------------------|--------------------------|--------------------------------------|
| **IDE** | Gradio UI (web semplice) + TUI Textual | IDE desktop MDI, tabbed, project-based | 🔴 **Mancanza di IDE grafico**: Sviluppo di un client desktop desktop-class basato su Tauri + React. |
| **Editor Codice** | Editor testuale base nella TUI | Syntax highlighting, formatting, renumbering | 🔴 Monaco Editor integrato con grammatiche custom per C64PY, BASIC e 6502 ASM. |
| **Sprite/Char** | Non presente | Editor visuale sprite (con export) + character + screen designer | 🔴 **Mancanza di tool visuali**: Integrazione di editor grafici HTML5 Canvas pixel-perfect con export ASM/BASIC. |
| **Debugger** | Validator sintattico + cycle counter | Debugger 6510/65816 step-by-step, breakpoints, memory view | 🔴 Connessione bidirezionale WebSocket con il protocollo monitor di VICE (x64sc). |
| **Emulazione** | Nessuna integrazione diretta | Nessuna integrazione nativa (ma produce .prg) | 🟡 Integrazione trasparente con VICE e supporto per simulatori WASM per testing rapido. |
| **Multi-piattaforma** | Solo C64 | C64/128, VIC20, C16/Plus4, PET, Mega65 | 🟡 PYC64 è nativo C64, ma l'architettura supporta target multipli modificando il code generator. |
| **AI** | ✅ Multi-agente, RAG, LoRA, Codegen | ❌ Assente | ✅ **Questo è il nostro vantaggio competitivo principale.** |
| **Gestione Progetti**| Nessuna | Progetti multi-file, build system | 🔴 Introduzione del formato di progetto standardizzato `.c64proj`. |
| **Formati Disk** | Estrazione D64/G64/PRG | Creazione/import/export D64/D71/D81/T64 | 🟡 Implementazione di tools di creazione/manipolazione dei formati disk di Commodore. |
| **SID Tool** | Non presente | Editor/viewer SID con MIDI | 🔴 Sviluppo di un SID Workbench con visualizzazione envelope ADSR ed export. |
| **Git** | Non presente | Integrazione Git nativa | 🟡 Mappatura trasparente del workspace con Git. |
| **Compilatore** | PYC64 (Python→6502) + ACME | Kick Assembler, assembler nativo | 🟡 PYC64 è unico, evoluzione verso un linguaggio ad alto livello completo. |

---

## 3. Spunti di Miglioramento Strategici

### A. Trasformare l'AI da "Chatbot" a "Copilot Integrato"
L'AI deve passare da assistente conversazionale a parte integrante del flusso di digitazione:
- **Inline Completion**: mentre l'utente scrive ASM, BASIC o C64PY, l'AI suggerisce in tempo reale le istruzioni successive (stile GitHub Copilot).
- **Smart Refactor**: refactoring del codice guidato dall'AI (es. "Ottimizza questa routine per risparmiare cicli CPU").
- **Bug Prediction**: il Validator/Linter preemptive evidenzia errori logici o di temporizzazione prima ancora del build.
- **Knowledge Graph Visuale**: navigatore interattivo che collega concetti hardware (es. registri VIC-II) a esempi e documentazione estratti semanticamente dal RAG.

### B. Evoluzione del Linguaggio C64PY (PYC64)
Sviluppare il compilatore Python-to-6502 per renderlo un linguaggio ad alto livello maturo:
- **Type System**: aggiunta di tipi espliciti (`uint8`, `uint16`, `zp_ptr`) per forzare la generazione di codice 6502 altamente ottimizzato.
- **Standard Library**: routine pre-ottimizzate per grafica (sprites, scroll, collisioni) e audio.
- **Inline Assembly**: supporto nativo per blocchi `asm:` direttamente all'interno delle funzioni Python.
- **Memory Allocator**: gestione automatica avanzata della Zero Page e della memoria RAM alta.

### C. Strumenti Visivi (Visual Tools)
Replicare e superare l'esperienza dei tool visuali di CBM .prg Studio:
- **Sprite Editor**: disegno pixel-perfect multicor/hi-res con preview animata in tempo reale ed export immediato in dati per assembler o BASIC.
- **Character Editor**: creazione di charset personalizzati con tool di manipolazione (rotazione, flip, inversione).
- **Screen Designer**: griglia visuale 40x25 per posizionare caratteri e definire colori, con generazione automatica di codice di setup.
- **SID Workbench**: editor di inviluppi ADSR con riproduttore integrato basato su WebAudio/WASM SID.
- **Memory Map Visualizer**: mappa interattiva colorata che rappresenta l'occupazione di RAM, ROM e registri di I/O.

---

## 4. Architettura Target del "C64 Intelligence Studio"

L'architettura garantisce il mantenimento del disaccoppiamento forte: l'IDE comunica esclusivamente tramite protocolli di rete standardizzati (REST, WebSockets, gRPC).

```
┌─────────────────────────────────────────────────────────────┐
│                  C64 Intelligence Studio                     │
│              (Tauri Desktop App - React/TS)                │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Editor     │  Visual     │  Debugger   │  AI Copilot     │
│  (Monaco)   │  Tools      │  (VICE)     │  (Chat/Inline)  │
└──────┬──────┴──────┬──────┴──────┬──────┴────────┬────────┘
       │             │             │               │
       └─────────────┴─────────────┴───────────────┘
                         │
                    WebSocket/REST
                         │
┌────────────────────────┼──────────────────────────────────┐
│              C64 Intelligence Core (Python)                │
│  ┌──────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │  AI Engine   │ │  PYC64      │ │  Build/Assembler    │ │
│  │  (C64-LLM)   │ │  Compiler   │ │  (ACME/Kick/CA65)   │ │
│  │  RAG/FAISS   │ │  Python→6502│ │                     │ │
│  └──────────────┘ └─────────────┘ └─────────────────────┘ │
│  ┌──────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │  Debugger    │ │  Disk Tools │ │  Project Manager    │ │
│  │  (VICE Mon.) │ │  (D64/PRG)  │ │  (Git/Assets)       │ │
│  └──────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Layer                                      │
│  SQLite (projects) │ FAISS (RAG) │ FileSystem (assets)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Piano di Migrazione Dettagliato (12 Mesi)

### 🏗️ FASE 1: Fondamenta e Architettura (Mesi 1-3)
**Obiettivo**: Trasformare l'SDK in un framework modulare multi-servizio.
- **Re-architecture (F1.1)**: Separazione backend (Python) da frontend (Tauri/React). Il backend diventa un Language Server + AI Engine.
- **Plugin System (F1.2)**: Definizione di protocolli standard per strumenti (`IEditorTool`, `IBuildTool`, `IDebugger`).
- **Project Format (F1.3)**: Implementazione del formato `.c64proj` (JSON/YAML) per gestire configurazioni multi-file, target di compilazione, percorsi di asset e compilatori.
- **Monorepo (F1.4)**: Riorganizzazione in workspace (core, ide, tools, ai).
- **CI/CD (F1.5)**: Configurazione di workflow GitHub Actions per la build cross-platform su Windows, macOS e Linux.

### 💻 FASE 2: IDE Core (Mesi 3-6)
**Obiettivo**: Costruzione della shell desktop unificata.
- **Shell Desktop (F2.1)**: Applicazione desktop con Tauri (Rust) e React/TypeScript.
- **Code Editor (F2.2)**: Integrazione di Monaco Editor con evidenziazione sintattica avanzata per C64PY, BASIC v2 e 6502 ASM.
- **File Explorer (F2.3)**: Gestione ad albero del workspace di progetto con drag & drop.
- **Tab & Terminal System (F2.4)**: Interfaccia multi-scheda e terminale integrato tramite XTerm.js per visualizzare l'output del build.

### 🎨 FASE 3: Strumenti Visivi (Mesi 4-7)
**Obiettivo**: Sviluppo degli editor grafici e sonori integrati.
- **Sprite Editor (F3.1)**: Interfaccia visuale Canvas per sprite 24x21 (hi-res) / 12x21 (multicolor) con esportazione ASM/BASIC e supporto animazione.
- **Character & Tile Editor (F3.2)**: Disegno di charset custom 8x8 pixel.
- **Screen Designer (F3.3)**: Griglia visuale 40x25 per posizionare i caratteri sullo schermo ed esportazione in blocchi `POKE` o istruzioni assembly.
- **Memory Map (F3.4)**: Visualizzatore grafico della memoria del C64 con colori dinamici per aree di sistema, variabili e codice utente.

### 🐛 FASE 4: Debugger e Runtime (Mesi 6-8)
**Obiettivo**: Chiusura del gap di diagnostica ed esecuzione.
- **Emulator Bridge (F4.1)**: Connessione asincrona a VICE via protocollo monitor binary su socket TCP.
- **Debugger UI (F4.2)**: Pannelli per visualizzare i registri CPU (A, X, Y, SP, PC, Flags), stack, e dump di memoria in tempo reale.
- **Controllo Flusso (F4.3)**: Stepping controllato (step-into, step-over, break, run to cursor).

### 🤖 FASE 5: AI Integration Nativa (Mesi 7-10)
**Obiettivo**: Raggiungere l'esperienza di sviluppo "AI-Native".
- **Inline Copilot (F5.1)**: Completamento di codice inline assistito da LLM locali (es. Qwen-Coder via llama.cpp).
- **AI Sidebar (F5.2)**: Chat interattiva con il contesto del codice attivo e query sul RAG di documentazione C64.
- **Self-Healing UI (F5.3)**: Visualizzazione grafica asincrona del processo di auto-correzione quando la build fallisce.

### 🚀 FASE 6: Multi-piattaforma, Gestione Dischi e Rilascio (Mesi 9-12)
- **Multi-target (F6.1)**: Configurazione compilation per C128, VIC20, PET, Mega65.
- **Disk Tools (F6.2)**: Manipolazione e creazione di immagini disco (.D64, .D71, .D81, .T64).
- **Git & Package Manager (F6.3)**: Controllo di versione e gestione pacchetti/librerie riusabili.

---

## 6. Stack Tecnologico Consigliato

| Layer | Tecnologia | Motivazione |
|-------|------------|-------------|
| **Frontend IDE** | Tauri (Rust) + React + TypeScript + Tailwind | Prestazioni eccellenti, bundle compatto (<5MB), sicurezza nativa Rust. |
| **Editor di Codice** | Monaco Editor | Standard di mercato (lo stesso di VS Code), supporto LSP integrato. |
| **Backend API** | FastAPI + Uvicorn | Prestazioni asincrone elevate, OpenAPI auto-generato, integrazione nativa con Python. |
| **Motore AI** | llama.cpp (GGUF locale) + sentence-transformers | Approccio local-first, privacy garantita, nessuna chiave API esterna richiesta. |
| **Emulazione** | VICE (x64sc) & WASM Emulator | Emulatore di riferimento con protocollo di debug maturo su socket TCP. |
| **Compilazione** | PYC64 Compiler + ACME / KickAssembler | Flessibilità multi-assemblatore. |

---

## 7. Protocolli di Rete e Contratti d'Interfaccia

Le interazioni avvengono tramite messaggi JSON standardizzati. Di seguito sono definiti i contratti principali.

### 7.1 Protocollo di Progetto (`.c64proj` schema JSON)
Ogni progetto viene descritto da un file `.c64proj` posizionato nella cartella radice:

```json
{
  "project_name": "MyRetroGame",
  "version": "1.0.0",
  "author": "Alberto Abate",
  "target": "C64",
  "entry_point": "src/main.c64",
  "output_name": "game.prg",
  "build_config": {
    "optimize": true,
    "assembler": "acme",
    "load_address": "0x0801"
  },
  "assets": [
    {
      "type": "sprite",
      "path": "assets/player.spr",
      "build_action": "generate_asm"
    },
    {
      "type": "sid",
      "path": "assets/music.sid",
      "build_action": "inject"
    }
  ]
}
```

### 7.2 Protocollo Assistente AI (GUI ──► C64-LLM Agent Service)

```json
{
  "session_id": "session_user_456",
  "prompt": "Come posso impostare un raster interrupt sulla linea 150 usando C64PY?",
  "rag_enabled": true,
  "context": {
    "open_file": "main.c64",
    "cursor_line": 12
  }
}
```

---

## 8. Considerazioni Critiche e Gestione Rischi

1. **Complessità del Debugger**: L'integrazione con VICE richiede comunicazione socket TCP robusta. Nelle prime fasi, supporteremo un emulatore 6502 minimale scritto in Python/WASM per il debug di base prima di connettere VICE.
2. **Reattività dell'AI**: Modelli locali come Qwen2.5-Coder-1.5B/3B offrono buone performance su CPU. Prevediamo opzioni di quantizzazione spinta (Q4_K_M o Q2_K) per garantire fluidità.
3. **Controllo di Regressione**: Ogni estensione del compilatore `PYC64` e del gestore di progetto deve superare la suite di test automatizzati per evitare regressioni.
