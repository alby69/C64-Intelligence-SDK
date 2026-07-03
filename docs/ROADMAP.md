# PYC64 — Roadmap

> **Versione:** 1.0-draft  
> **Data:** 2026-07-02  
> **Autore:** Analisi basata su revisione architetturale del progetto PYC64 (https://github.com/alby69/PYC64) e integrazione con C64-Intelligence-SDK (https://github.com/alby69/C64-Intelligence-SDK)

---

## 1. Visione e Contesto

PYC64 è un cross-compilatore **Python-like → Assembly 6502 → PRG nativo C64**, con TUI IDE integrata, posizionato come componente `tools/` all'interno dell'ecosistema **C64-Intelligence-SDK**.

L'obiettivo strategico è trasformare PYC64 da compilatore standalone a **motore di compilazione orchestrato dall'AI Multi-Agente C64-LLM**, mantenendo la sua autonomia operativa.

---

## 2. Analisi SWOT

| **Strengths** | **Weaknesses** |
|---|---|
| Compilatore completo (Lexer→Parser→Codegen→Assembler) in puro Python | Nessuna documentazione API pubblica per l'integrazione programmatica |
| TUI Textual moderna e usabile | Nessun protocollo di comunicazione con C64-LLM (core/) |
| Workflow Dockerizzato e Makefile | Mancanza di test suite automatizzata visibile |
| Output nativo `.PRG` direttamente eseguibile | Nessun supporto per ottimizzazioni 6502 avanzate (loop unrolling, zero-page) |
| | Nessuna integrazione con il Knowledge Base / RAG del SDK |

| **Opportunities** | **Threats** |
|---|---|
| Integrazione come "Compilatore Agent" nel sistema multi-agente C64-LLM | C64-LLM potrebbe generare codice che PYC64 non supporta, causando errori silenziosi |
| Esposizione di API REST/gRPC per orchestrazione da parte dell'Orchestrator | Divergenza tra il linguaggio Python-like supportato e le aspettative dell'AI |
| Pipeline CI/CD convalidata dal Validator del SDK | Mancanza di retrocompatibilità se il linguaggio .c64 evolve troppo rapidamente |
| Knowledge Distillation: usare PYC64 per generare dataset di training per C64-LLM | Fragmentazione del linguaggio tra PYC64 e gli esempi del tutorial |

---

## 3. Obiettivi per Fase

### Fase 1 — Fondamenta di Integrazione (Q3 2026)

| ID | Obiettivo | Priorità | Complessità | Stato |
|---|---|---|---|---|
| F1.1 | **API programmatica** — Esporre il compilatore come libreria importabile (`from pyc64c import compile_source`) con interfaccia stabile | 🔴 Alta | Media | ✅ Completato |
| F1.2 | **Protocollo SDK** — Definire formato JSON di scambio dati con C64-LLM (input: codice .c64 + metadati; output: PRG binary + listing + errori + metriche) | 🔴 Alta | Media | ✅ Completato |
| F1.3 | **Contract Testing** — Test di integrazione con C64-LLM che verificano la compatibilità del formato di scambio | 🟡 Media | Media | ✅ Completato |
| F1.4 | **Integrazione Decoupled** — Refactoring del bridge di integrazione per gestione dinamica delle dipendenze SDK | 🔴 Alta | Media | ✅ Completato |
| F1.5 | **Documentazione API/SDK** — Generare documentazione per integrazione e API pubblica | 🟡 Media | Bassa | ✅ Completato |

### Fase 2 — Potenziamento del Compilatore (Q4 2026)

| ID | Obiettivo | Priorità | Complessità | Stato |
|---|---|---|---|---|
| F2.1 | **Ottimizzatore 6502** — Implementare pass di ottimizzazione: constant folding, dead code elimination, zero-page allocation, loop unrolling | 🔴 Alta | Alta | 🟡 In Corso |
| F2.2 | **Supporto tipi avanzati** — Array multidimensionali, struct/record, puntatori, gestione memoria dinamica (heap) | 🟡 Media | Alta | ⏳ Pianificato |
| F2.3 | **Libreria standard C64** — Wrappers Python-like per KERNAL, SID, VIC-II, CIA (es. `sid.play(freq)`, `sprite.set(x, y, frame)`) | 🔴 Alta | Alta | ⏳ Pianificato |
| F2.4 | **Debug symbols** — Generare file `.sym` compatibili con VICE per il debugging step-by-step | 🟡 Media | Media | ✅ Completato |

### Fase 3 — Integrazione AI-Nativa (Q1 2027)

| ID | Obiettivo | Priorità | Complessità |
|---|---|---|---|
| F3.1 | **Agent Compiler** — PYC64 esposto come servizio Docker con endpoint REST/gRPC che riceve codice dall'Orchestrator C64-LLM | 🔴 Alta | Media |
| F3.2 | **Feedback loop** — Il compilatore restituisce errori strutturati all'AI in formato machine-readable per self-healing automatico | 🔴 Alta | Media |
| F3.3 | **RAG Integration** — PYC64 può interrogare il Knowledge Base del SDK per risolvere ambiguità semantiche nel codice sorgente | 🟡 Media | Alta |
| F3.4 | **Profiler integrato** — Metriche di performance (cycle count, memoria usata, frame time) restituite all'AI per ottimizzazione iterativa | 🟡 Media | Alta |

### Fase 4 — Ecosistema e Scalabilità (Q2 2027)

| ID | Obiettivo | Priorità | Complessità |
|---|---|---|---|
| F4.1 | **Multi-target** — Supporto per altre piattaforme 6502 (Atari 8-bit, NES, Apple II) con backend modulare | 🟢 Bassa | Alta |
| F4.2 | **Package Manager** — Sistema di moduli `.c64` con dipendenze, registry locale e condivisione | 🟢 Bassa | Alta |
| F4.3 | **Web IDE** — Interfaccia browser (basata su Monaco Editor) oltre alla TUI, con cloud compilation | 🟢 Bassa | Alta |
| F4.4 | **Dataset Generation** — Pipeline automatica che genera coppie (Python-like → 6502) per fine-tuning di C64-LLM | 🟡 Media | Alta |

---

## 4. Architettura Target di Integrazione

```
┌─────────────────────────────────────────────────────────────────┐
│                    C64-Intelligence-SDK                          │
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────────────────┐    │
│  │  C64-LLM        │         │        PYC64 (tools/)       │    │
│  │  (core/)        │         │                             │    │
│  │                 │         │  ┌─────────────────────┐   │    │
│  │  Orchestrator   │◄───────►│  │  Compiler Agent     │   │    │
│  │  Coder Agent    │  JSON   │  │  (REST/gRPC)          │   │    │
│  │  Validator      │ Protocol│  └─────────────────────┘   │    │
│  │                 │         │           │               │    │
│  │  RAG Engine     │         │  ┌────────▼────────┐      │    │
│  │  FAISS KB       │         │  │  pyc64c Core    │      │    │
│  └─────────────────┘         │  │  Lexer→Parser   │      │    │
│           │                  │  │  →Codegen→Asm   │      │    │
│           │                  │  └────────┬────────┘      │    │
│           │                  │           │               │    │
│           ▼                  │  ┌────────▼────────┐      │    │
│  ┌─────────────────┐         │  │  Optimizer      │      │    │
│  │  data/          │         │  │  6502           │      │    │
│  │  vectorstore/   │◄────────┤  └────────┬────────┘      │    │
│  │  models/        │  RAG    │           │               │    │
│  └─────────────────┘  Query  │  ┌────────▼────────┐      │    │
│                              │  │  Output Engine  │      │    │
│                              │  │  .PRG + .SYM    │      │    │
│                              │  │  + Metrics      │      │    │
│                              │  └─────────────────┘      │    │
│                              └─────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Protocollo di Scambio (JSON)

```json
// Request: C64-LLM → PYC64
{
  "version": "1.0",
  "source_code": "def main():\n    print("hello")",
  "language": "c64-python",
  "options": {
    "optimize": true,
    "target": "c64",
    "generate_symbols": true,
    "zero_page_alloc": true
  },
  "context": {
    "rag_query_id": "abc123",
    "session_id": "sess-456"
  }
}

// Response: PYC64 → C64-LLM
{
  "status": "success | error | warning",
  "artifacts": {
    "prg_base64": "...",
    "listing": "...",
    "hex_dump": "...",
    "symbols": "..."
  },
  "metrics": {
    "compile_time_ms": 120,
    "binary_size_bytes": 2048,
    "estimated_cycles": 4500,
    "memory_usage": { "zero_page": 32, "ram": 512 }
  },
  "diagnostics": [
    {
      "severity": "error | warning | info",
      "line": 5,
      "column": 12,
      "message": "Variable 'x' may exceed 8-bit range",
      "suggestion": "Use uint16_t or clamp value"
    }
  ],
  "rag_suggestions": [
    "Consider using zero-page for loop counter 'i'"
  ]
}
```

---

## 5. Miglioramenti Tecnici Specifici

### 5.1 Compilatore Core (`pyc64c/`)

| Area | Stato Attuale | Miglioramento Proposto |
|---|---|---|
| **Lexer** | Presumibilmente regex-based | Aggiungere supporto per Unicode identifiers, migliorare error recovery con `ErrorToken` |
| **Parser** | Presumibilmente recursive descent | Implementare AST con visitor pattern; aggiungere type inference base |
| **Codegen** | Presumibilmente direct emission | Aggiungere IR (Intermediate Representation) a 3-address code per abilitare ottimizzazioni |
| **Assembler** | Presumibilmente custom | Supporto per macro, label locali, espressioni costanti a compile-time |
| **Runtime** | Presumibilmente minimale | Libreria runtime per gestione stack, allocazione heap, interrupt handlers |

### 5.2 TUI IDE (`pyc64_ui/`)

| Feature | Stato Attuale | Miglioramento Proposto |
|---|---|---|
| Editor | Base con syntax highlighting | LSP-like features: autocomplete, go-to-definition, inline diagnostics |
| Tabs | BASIC / Listing / Hex | Aggiungere tab "Assembly" (6502 puro), "Symbols", "Memory Map" |
| Error Panel | Lista testuale | Errori cliccabili che saltano alla linea; filtri per severità |
| Integrazione | Standalone | Modalità "Agent Mode": riceve codice da C64-LLM e mostra risultati in tempo reale |

### 5.3 DevOps e Qualità

| Area | Azione |
|---|---|
| **CI/CD** | GitHub Actions: lint, test, build Docker, integration test con C64-LLM mock |
| **Test Suite** | Unit test per ogni fase del compilatore; golden tests con output atteso; property-based testing |
| **Benchmark** | Suite di benchmark con codice .c64 di riferimento; tracking regressione performance |
| **Coverage** | Target: >80% coverage su `pyc64c/` |

---

## 6. Sinergie con C64-Intelligence-SDK

### 6.1 Flusso di Lavoro Integrato

```
Utente: "Scrivi un gioco Breakout in Python per C64"
         │
         ▼
┌─────────────────┐
│ C64-LLM         │
│ Orchestrator    │
│ genera codice   │
│ .c64            │
└────────┬────────┘
         │ JSON Protocol
         ▼
┌─────────────────┐
│ PYC64 Compiler  │
│ Agent           │
│ compila → .PRG  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Success │ │ Error  │
│→ VICE   │ │→ C64-LLM│
│  test   │ │ Self-  │
│         │ │ Healing│
└────────┘ └────────┘
```

### 6.2 Punti di Contatto Tecnici

| Componente SDK | Interazione con PYC64 |
|---|---|
| **C64-LLM / Coder Agent** | Genera codice .c64; riceve errori di compilazione per iterazione self-healing |
| **C64-LLM / Validator** | Convalida output .PRG con ACME assembler come double-check; confronta listing |
| **C64-LLM / RAG Engine** | PYC64 può queryare KB per risolvere ambiguità (es. "come si accede a $D020 in Python-like?") |
| **C64GameTutorial** | Esempi del tutorial possono essere convertiti in test .c64 per PYC64; PYC64 può generare soluzioni alternative |
| **Pipeline Dati** | Output di PYC64 (coppie Python-like/6502) alimenta dataset per fine-tuning C64-LLM |

### 6.3 Plugin Architecture (Cheshire-style)

Il SDK menziona una cartella `plugins/` con logica "Cheshire-style". PYC64 dovrebbe esporre un'interfaccia plugin che permetta:

- **Plugin di Ottimizzazione**: terze parti possono registrare pass di ottimizzazione 6502
- **Plugin di Backend**: supporto per nuove piattaforme (Atari, NES) come backend swappable
- **Plugin di Output**: generatori aggiuntivi (es. formato cartridge, D64 disk image)

---

## 7. Metriche di Successo

| Metrica | Target Fase 1 | Target Fase 2 | Target Fase 3 |
|---|---|---|---|
| Compilazione senza errori (test suite) | 95% | 98% | 99.5% |
| Tempo compilazione medio | <500ms | <300ms | <200ms |
| Riduzione binary size (vs non ottimizzato) | — | -20% | -35% |
| Integrazione con C64-LLM (test pass) | 100% | 100% | 100% |
| Documentazione coverage API | 100% | 100% | 100% |
| Test coverage | 60% | 75% | 85% |

---

## 8. Rischi e Mitigazioni

| Rischio | Impatto | Mitigazione |
|---|---|---|
| **Breaking changes nel linguaggio .c64** | Alto | Versioning del protocollo; deprecation policy; test di regressione |
| **Performance compilatore insufficiente per AI real-time** | Medio | Caching compilazione; compilazione incrementale; profiling continuo |
| **Divergenza semantica tra Python e 6502** | Medio | Documentazione esplicita delle limitazioni; linter dedicato; warning proattivi |
| **Manutenzione doppia (standalone + SDK)** | Medio | Mono-repo con CI condiviso; release sincronizzate; changelog unificato |

---

## 9. Prossimi Passi Immediati

1. **Definire il JSON Protocol** — Meeting di allineamento con maintainer C64-LLM per stabilire il contratto di interfaccia
2. **Refactor `pyc64c/` per API pubblica** — Estrarre `compile_source()`, `assemble_source()` come funzioni di primo livello con typing
3. **Setup CI/CD** — GitHub Actions con pytest, mypy, black, integration test mock
4. **Draft documentazione API** — Sphinx setup con autodoc per `pyc64c/`
5. **PoC integrazione** — Script Python che simula C64-LLM → PYC64 → output PRG

---

## 10. Riferimenti

- Repository PYC64: https://github.com/alby69/PYC64
- Repository C64-Intelligence-SDK: https://github.com/alby69/C64-Intelligence-SDK
- Submodules SDK: `core/` → C64-LLM, `tools/` → PYC64, `tutorial/` → C64GameTutorial

---

*Questa roadmap è un documento vivente. Aggiornamenti e revisioni sono benvenuti tramite PR.*
