# C64-Intelligence-SDK — Master Roadmap & Evolution Plan

> **Versione:** 2.0-strategic
> **Data:** 2026-07-02  
> **Autore:** Team di Architettura C64-Intelligence-SDK
> **Stato:** Proposta di Evoluzione Strategica (Approvata)

---

## 1. Visione di Insieme dell'Ecosistema

Il **C64-Intelligence-SDK** si sta evolvendo da un insieme di strumenti e script sparsi a una piattaforma integrata di sviluppo assistito da intelligenza artificiale per il Commodore 64, posizionandosi come una sorta di **CBM Studio o VSCode di nuova generazione (AI-Native)**.

La filosofia cardine del progetto è il **disaccoppiamento forte (loose coupling)**. Ogni componente dell'ecosistema è un'unità autonoma (gestita come sottomodulo Git) che espone API ben definite. Questa separazione garantisce la manutenibilità e permette a ciascun modulo di evolvere in modo indipendente o di essere eseguito come servizio standalone.

### Componenti dell'Ecosistema Attuale

1. **`core/` (C64-LLM)**: Il cervello dell'ecosistema. Gestisce l'orchestrazione multi-agente, la pipeline RAG semantica, la validazione, l'integrazione con modelli locali (nanoGPT) ed esterni, e implementa il ciclo di auto-guarigione (*self-healing*) del codice.
2. **`tools/` (PYC64)**: Il motore di compilazione e l'IDE testuale (TUI). Include il compilatore per il linguaggio `C64PY` (Python-like), il macro-assemblatore 6502, un simulatore e l'interfaccia basata su libreria Textual (`pyc64_ui`).
3. **`kb-agent/` (C64-KB-Agent)**: Il servizio di Knowledge Base semantica. Espone endpoint REST per l'indicizzazione dei documenti e la ricerca semantica con FAISS + Sentence-Transformers, oltre a un risolutore di indirizzi fisici del C64.
4. **`debugger/` (C64-Debugger)**: L'agente di runtime e diagnostica. Gestisce breakpoint, watchpoint, tracciamento dell'esecuzione e un client socket verso il protocollo monitor dell'emulatore VICE.
5. **`scraper/` (C64-Scrapy)**: Il motore di recupero delle informazioni. Effettua lo scraping mirato da siti storici (Codebase64, C64 Wiki, ecc.) per alimentare la Knowledge Base.
6. **`tutorial/` (C64GameTutorial)**: Risorse educative e soluzioni assembly pre-convalidate utilizzate per regression testing e training dell'AI.

---

## 2. Analisi SWOT dell'Ecosistema

| **Punti di Forza (Strengths)** | **Punti di Debolezza (Weaknesses)** |
|---|---|
| Architettura a submoduli Git pulita e modularità spinta delle responsabilità. | Interfacce grafiche frammentate (TUI in Textual per `tools/`, Gradio UI in `core/`). |
| Pipeline di self-healing avanzata per la correzione automatica del codice generato. | Mancanza di un orchestratore visivo centralizzato che connetta l'AI con il compilatore e il debugger in tempo reale. |
| Knowledge Base robusta con indici vettoriali locali e ricerca semantica. | Dipendenza parziale da terminali o container Docker multipli per l'esecuzione dei vari agenti. |

| **Opportunità (Opportunities)** | **Minacce (Threats)** |
|---|---|
| Creazione di un agente **`C64-GUI`** centralizzato (stile VSCode/CBM Studio) come frontend unificato. | Possibile accoppiamento stretto se l'interfaccia grafica chiama direttamente le classi interne anziché le API di rete. |
| Esposizione di ogni agente come microservizio REST/WebSocket (Docker). | Sovraccarico di configurazione o latenza se i protocolli IPC/Rete non sono altamente efficienti. |
| Offrire un'esperienza di sviluppo "low-code/AI-assisted" per programmatori retrò. | Frammentazione della documentazione e disallineamento dei contratti delle API. |

---

## 3. Proposta di Evoluzione: Il Submodulo `C64-GUI`

Per risolvere la frammentazione delle interfacce attuali (Textual TUI e Gradio Web UI) e fornire un ambiente di sviluppo integrato coeso, si propone l'introduzione di un nuovo agente/submodulo: **`C64-GUI`**.

### 3.1 Ruolo di `C64-GUI`
`C64-GUI` agirà esclusivamente come **Frontend Orchestrator e Client Visivo**. Non conterrà logica di compilazione, modellazione AI o esecuzione diretta del codice. Interagirà con gli altri moduli esclusivamente tramite protocolli di rete standardizzati (REST, WebSockets, gRPC), garantendo il mantenimento del disaccoppiamento forte.

```
                  ┌──────────────────────────────────────────┐
                  │                C64-GUI                   │
                  │   (Frontend: Electron / VSCode-like /    │
                  │         Flet / PySide / WebApp)          │
                  └────┬──────────────┬──────────────┬───────┘
                       │              │              │
             JSON/REST │    WebSocket │    JSON/REST │
             /gRPC     │    /Socket   │    /gRPC     │
                       ▼              ▼              ▼
                ┌────────────┐ ┌────────────┐ ┌────────────┐
                │  C64-LLM   │ │C64-Debugger│ │   PYC64    │
                │  (core/)   │ │ (debugger/)│ │  (tools/)  │
                └────────────┘ └────────────┘ └────────────┘
                       │                             ▲
             JSON/REST │                             │
                       ▼                             │
                ┌────────────┐                       │
                │C64-KB-Agent│───────────────────────┘
                │ (kb-agent/)│       Query RAG
                └────────────┘
```

### 3.2 Architettura Tecnologica Proposta per `C64-GUI`
Si valutano due strade principali per l'implementazione del client visivo:

1. **Approccio Electron / VSCode Extension (Raccomandato per scalabilità)**:
   - Sviluppare un'estensione VSCode avanzata o un IDE standalone basato su Electron/Vite.
   - Sfrutta l'ecosistema VSCode esistente (syntax highlighting, file manager, terminale integrato, pannelli personalizzabili).
   - Comunica tramite un Language Server Protocol (LSP) personalizzato o WebSocket con i servizi backend in esecuzione (PYC64 compiler, C64-LLM agent, C64-Debugger).
2. **Approccio Python-Native (Flet / PySide6 / PyQt)**:
   - Sviluppare la GUI in puro Python utilizzando Flet (basato su Flutter) o PySide6 (Qt).
   - Vantaggio: mantiene la codebase interamente in Python, facilitando l'installazione tramite pacchetti `pip`.
   - Implementa un'architettura asincrona (`asyncio`) per gestire la reattività della GUI rispetto alle risposte di rete dei sottomoduli.

---

## 4. Piano di Evoluzione in 5 Fasi

### Fase 1: Consolidamento e Standardizzazione delle API (Q3-Q4 2026)
L'obiettivo è garantire che ogni sottomodulo esistente sia esponibile come servizio di rete indipendente con contratti API rigidamente definiti.

- **F1.1: Standardizzazione Nomenclatura**: Eliminare ogni riferimento a "C64PY" come nome del compilatore, mantenendo `C64PY` per indicare il *linguaggio* di programmazione e `PYC64` per indicare il *compilatore/IDE testuale* sotto `tools/`.
- **F1.2: Esposizione di PYC64 come Servizio**: Implementare un wrapper REST/gRPC (es. FastAPI) per il compilatore in `tools/pyc64c/sdk.py`.
- **F1.3: Consolidamento C64-KB-Agent**: Completare la transizione di `kb-agent/` a microservizio autonomo (FastAPI) con API per indicizzazione, RAG vettoriale e risoluzione di registri hardware.
- **F1.4: Esposizione C64-Debugger**: Creare un server di debugging WebSocket sopra `debugger/` che gestisca la connessione con l'emulatore VICE e invii eventi di esecuzione (register states, memory dump) alla rete.

### Fase 2: Architettura Multi-Servizio Dockerizzata (Q1 2027)
Configurare l'ambiente di runtime dell'SDK in modo che ogni agente venga eseguito in un container Docker dedicato, orchestrato tramite `docker-compose`.

- **F2.1: Docker Compose Unificato**: Aggiornare il file `docker-compose.yml` nella root del progetto per avviare:
  - `c64-kb-agent` (porta 8001)
  - `c64-llm-core` (porta 8000)
  - `c64-compiler` (porta 8002)
  - `c64-debugger` (porta 8003)
- **F2.2: Test di Integrazione End-to-End**: Creare contratti di integrazione automatici in `tests/` per verificare la comunicazione continua tra i servizi Docker.

### Fase 3: Sviluppo di `C64-GUI` Core (Q2 2027)
Avviare lo sviluppo dell'interfaccia grafica centralizzata mantenendo il disaccoppiamento totale.

- **F3.1: Progettazione Layout IDE**: Un layout a tre pannelli stile VSCode/CBM Studio:
  - *Sinistra*: Workspace/File Explorer + Pannello AI (Chat interattiva, suggerimenti di self-healing).
  - *Centro*: Editor di codice con syntax highlighting per `C64PY` e assembly 6502.
  - *Destra/Sotto*: Pannello di controllo compilazione (BASIC/Listing/Hex) e Tab Debugger (Registri CPU, Memory map, Watchpoints, Schermo emulatore integrato o connesso).
- **F3.2: Implementazione Client di Rete**: Sviluppare il middleware della GUI per inviare codice al compilatore, ricevere pacchetti binari, richiedere suggerimenti di codice a `C64-LLM` e monitorare l'esecuzione in `C64-Debugger`.

### Fase 4: Integrazione AI Avanzata nella GUI (Q3 2027)
Portare la potenza di `C64-LLM` direttamente all'interno dell'esperienza visiva dello sviluppatore.

- **F4.1: Interfaccia Copilot/Chat Integrata**: Visualizzare i suggerimenti dell'agente AI a lato dell'editor di codice. Abilitare il refactoring con un click direttamente dal pannello GUI.
- **F4.2: Visualizzazione del Self-Healing**: Quando la compilazione fallisce, la GUI mostra in modo interattivo il processo asincrono di self-healing condotto dall'Orchestrator di `C64-LLM`, indicando i tentativi e le correzioni applicate sul codice prima di presentare la soluzione finale.
- **F4.3: Memory Map Visualizer**: Sfruttare l'API di `C64-KB-Agent` per mostrare graficamente una mappa della memoria del C64, evidenziando le aree occupate dalle variabili generate dal compilatore `PYC64` e le locazioni dei registri hardware (VIC-II, SID, CIA).

### Fase 5: Consolidamento e Rilascio di "CBM-Studio AI" (Q4 2027)
Rilasciare l'ecosistema completo come un ambiente di sviluppo chiavi in mano.

- **F5.1: Installatore Monolitico (opzionale)**: Fornire uno script o un installer che configuri l'intero ecosistema con una singola azione, nascondendo la complessità dei container Docker sotto la GUI.
- **F5.2: Pipeline CI/CD**: Abilitare il rilascio automatico dei sottomoduli con versioning allineato.

---

## 5. Protocolli di Rete e Contratti d'Interfaccia

Per garantire che la GUI e gli agenti rimangano rigorosamente disaccoppiati, tutte le interazioni avvengono tramite messaggi JSON standardizzati. Di seguito sono definiti i contratti principali.

### 5.1 Protocollo di Compilazione (GUI ──► PYC64 Compiler Service)
*Richiesta di compilazione di un sorgente .c64 in formato PRG con simboli di debug.*

```json
{
  "request_id": "req_comp_001",
  "source_code": "def main() -> byte:\n    poke(53280, 0)\n    return 0",
  "options": {
    "optimize": true,
    "generate_symbols": true
  }
}
```

*Risposta di successo dal compilatore:*

```json
{
  "request_id": "req_comp_001",
  "status": "success",
  "artifacts": {
    "prg_base64": "S3l...[truncated]...",
    "listing": "; Listing generated...\nORG $080D\n...",
    "symbols": {
      "main": "080d"
    }
  },
  "metrics": {
    "compile_time_ms": 32,
    "binary_size_bytes": 15
  }
}
```

### 5.2 Protocollo Assistente AI (GUI ──► C64-LLM Agent Service)
*Invia una richiesta di spiegazione di codice o generazione assistita con contesto RAG.*

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

*Risposta dell'AI Orchestrator (con suggerimento di codice strutturato):*

```json
{
  "session_id": "session_user_456",
  "status": "completed",
  "response": "Per configurare un raster interrupt in C64PY, puoi utilizzare i registri del chip VIC-II ($D011, $D012). Ecco il codice:",
  "generated_code": "def setup_raster():\n    sei()\n    # Imposta la linea di interrupt\n    poke(53266, 150) \n    # Attiva l'interrupt del raster\n    poke(53282, 1) \n    cli()",
  "sources": [
    {
      "title": "VIC-II Raster Interrupts",
      "source": "C64 Programmer's Reference Guide",
      "url": "https://github.com/alby69/C64-KB-Agent/..."
    }
  ]
}
```

### 5.3 Protocollo di Controllo Debugger (GUI ──► C64-Debugger WebSocket)
*Invia comandi di controllo al debugger e riceve aggiornamenti sullo stato dei registri.*

*Messaggio inviato dalla GUI (Set Breakpoint):*

```json
{
  "command": "set_breakpoint",
  "address": "080d",
  "enabled": true
}
```

*Messaggio inviato dal Debugger Service alla GUI (Breakpoint Hit):*

```json
{
  "event": "breakpoint_hit",
  "address": "080d",
  "cpu_state": {
    "pc": "080d",
    "a": "00",
    "x": "ff",
    "y": "00",
    "sp": "f6",
    "flags": {
      "n": 0, "v": 0, "b": 1, "d": 0, "i": 1, "z": 1, "c": 0
    }
  }
}
```

---

## 6. Indicatori di Successo e Qualità

Per valutare il successo dell'evoluzione dell'ecosistema e del nuovo sottomodulo `C64-GUI`:

1. **Grado di Disaccoppiamento**: 100% delle chiamate tra la GUI e gli agenti deve transitare via API di rete (nessun import diretto di moduli Python tra i sottomoduli Git).
2. **Reattività della GUI**: Latenza dell'interfaccia grafica inferiore a 50ms per interazioni locali, e tempi di risposta di autocompletamento (LSP) inferiori a 150ms.
3. **Robustezza dei Contratti**: Copertura al 100% dei test di integrazione dei protocolli JSON definiti sopra.
4. **Usabilità dell'AI**: Percentuale di correzione automatica di codice errato (self-healing) superiore all'85% in ambiente controllato di compilazione.

---

*Questo piano rappresenta la visione strategica unitaria per convertire il C64-Intelligence-SDK nel più sofisticato ecosistema di sviluppo assistito per sistemi vintage a 8-bit.*
