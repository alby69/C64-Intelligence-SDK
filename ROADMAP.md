# C64 Ecosystem Roadmap

Questo documento delinea il futuro dell'ecosistema C64, consolidando gli obiettivi di integrazione, disaccoppiamento e sviluppo a lungo termine del **C64 Intelligence SDK**.

---

## 1. Analisi dell'Ecosistema & Stato dei Collegamenti

Il progetto si evolve come un **Hub/Collettore di Agenti Specializzati e Disaccoppiati**. Ciascun modulo (subproject) è gestito come Git Submodule per consentire uno sviluppo indipendente e riutilizzabilità multipiattaforma:

1. **C64-LLM (core/)**: L'assistente AI principale. Coordina gli agenti di ragionamento (Coder, Researcher, Validator) e implementa la logica di self-healing.
2. **PYC64 (tools/)**: Compilatore Python→C64 e ambiente IDE testuale (TUI). Fornisce gli strumenti pratici di sviluppo.
3. **C64GameTutorial (tutorial/)**: Manuale interattivo di programmazione arcade con REPL/playground integrato per scopi didattici.
4. **C64-Scrapy (scraper/)**: Componente centralizzato di acquisizione dati web. Estrae la documentazione tecnica (Wiki, Codebase64, manuali).
5. **Shared Logic Packages (packages/)**: `c64validator` (simulatore py6502 e ACME) e `c64extractor` (BASIC detokenizer e PRG/D64 parser) agiscono come mattoni condivisi per garantire uniformità comportamentale.

### Evoluzione verso Disaccoppiamento Avanzato
Per evitare colli di bottiglia e accoppiamenti di codice rigidi (es. moduli che importano file da cartelle sorelle tramite percorsi relativi complessi), l'architettura si muove verso la **servitizzazione** dei componenti tramite API locali e package Python autocontenuti.

---

## 2. Agente di Conoscenza Centralizzato: `C64-KB-Agent`

Attualmente, `C64-LLM` esegue localmente l'estrazione RAG e gestisce l'indice FAISS/ChromaDB. Questo comporta un elevato consumo di RAM e impedisce a strumenti come `PYC64` (TUI) o a estensioni esterne (es. VSCode) di accedere alla stessa base di conoscenza senza caricare pesanti framework AI.

### La Soluzione: `C64-KB-Agent` (Servizio Centralizzato)
Proponiamo la creazione di un microservizio/agente dedicato alla Knowledge Base:
- **Alimentazione automatica (Scraper -> KB)**: `C64-Scrapy` invia i dati estratti direttamente agli endpoint di indicizzazione del `C64-KB-Agent`.
- **Servizio Unificato (KB -> LLM & Tools)**: Espone API REST (FastAPI) o gRPC per:
  - **RAG Semantico**: Ricerca vettoriale con embedding per l'LLM.
  - **Query Tecniche Veloci**: Risoluzione istantanea di indirizzi di memoria, registri VIC-II/SID/CIA e istruzioni Assembly per l'IDE e la TUI.
  - **Linguaggio Naturale**: Traduzione di richieste d'uso per registri hardware in assembly pre-compilato.

```
┌─────────────────┐       ┌─────────────────┐
│   C64-Scrapy    ├──────►│  C64-KB-Agent   │ (Servizio centralizzato)
└─────────────────┘       └──────┬───┬──────┘
                                 │   │
        ┌────────────────────────┘   └────────────────────────┐
        ▼                                                     ▼
┌─────────────────┐                                   ┌─────────────────┐
│ C64-LLM (Core)  │                                   │   PYC64 (IDE)   │
│ RAG Query / Gen │                                   │ Tooltips/Context│
└─────────────────┘                                   └─────────────────┘
```

---

## 3. Studio sulla Necessità di un Debugger & `C64-Debugger-Agent`

### Perché un Debugger è Vitale?
La programmazione Assembly 6502 su C64 soffre della totale assenza di eccezioni a runtime. Bug tipici come:
- Stack overflow/underflow (es. `PHA` senza `PLA` o salti `JSR`/`RTS` sbilanciati).
- Branch fuori range.
- Scritture errate in aree di memoria riservate o registri hardware che bloccano lo schermo.

provocano crash silenziosi o infiniti loop. La sola analisi statica non basta. È necessario un **Debugger interattivo a livello di emulazione o simulazione**.

### Proposta: `C64-Debugger-Agent` (Agente Specifico)
Proponiamo la creazione di un agente debugger specializzato capace di:
1. **Analisi Dinamica**: Tracciare passo-passo i registri (A, X, Y), il Program Counter (PC), il registro di stato (SR) e l'indice dello Stack (SP).
2. **Integrazione Emulatore (VICE Monitor API)**: Connettersi alla porta monitor binaria di VICE (`-moncommands` o protocollo socket) per inserire breakpoint dinamici, analizzare i registri in tempo reale sul hardware emulato e catturare i crash.
3. **Debugging Agentico (Self-Healing Integrato)**: Quando l'emulatore crasha, l'agente cattura lo stato di memoria e registri, lo invia all'LLM insieme al codice sorgente e identifica automaticamente la riga di codice difettosa, proponendo la patch correttiva.

### Strategia di Repository: Perché Creare un Nuovo Repo per il Debugger?
Consigliamo vivamente di creare un **nuovo repository dedicato** (es. `C64-Debugger`) da includere come submodule in `tools/` o nella root, piuttosto che inserirlo all'interno di `core` o `tools`.
- **Separazione delle Responsabilità (SoC)**: Evita di appesantire il core AI con dipendenze di basso livello (socket, protocolli VICE, interfacce grafiche di debug interattive).
- **Estendibilità**: Consente l'utilizzo del debugger come tool standalone o integrabile in altri IDE (es. estensione VSCode) senza dover installare i modelli linguistici e i framework AI dell'SDK.
- **Ciclo di Rilascio Indipendente**: Consente aggiornamenti specifici sul motore di simulazione/emulazione senza influenzare le pipeline LLM.

---

## 4. Piano di Intervento Progressivo (Milestones di Evoluzione)

### Milestone 1: Consolidamento e Uniformità (In Corso)
- [x] **Meta-repository SDK**: Creato C64-Intelligence-SDK per orchestrare l'ecosistema.
- [x] **Disaccoppiamento Core**: Estratte le logiche di validazione (`c64validator`) ed estrazione (`c64extractor`) in package Python indipendenti.
- [x] **Integrazione py6502**: Simulazione e disassemblaggio pure-Python integrati per validazione veloce senza dipendenze esterne.
- [x] **Supporto Illegal Opcodes**: Implementato il supporto per gli opcode non documentati del 6502 (LAX, SAX, DCP, ecc.) in `c64validator`.
- [ ] **Uniformità Toolchain**: Completare il refactoring di `C64-LLM`, `PYC64` e `C64GameTutorial` per utilizzare esclusivamente i package condivisi `packages/c64validator` e `packages/c64extractor`.
- [ ] **Mappatura Memoria**: Estendere l'adapter py6502 per mappare le locazioni di memoria C64 più comuni (VIC-II, SID, CIA) per simulazioni accurate.

### Milestone 2: Servizi Centralizzati & C64-KB-Agent (Fase 4)
- [ ] **Sviluppo C64-KB-Agent**: Creazione del microservizio FastAPI per gestire le operazioni di embedding, indexing e query RAG.
- [ ] **Pipeline Scraper -> KB**: Modificare le pipeline di `C64-Scrapy` per inviare i file Markdown e i metadati direttamente all'API del `C64-KB-Agent`.
- [ ] **Client RAG su C64-LLM**: Sostituire l'infrastruttura RAG locale in `C64-LLM` con chiamate API al `C64-KB-Agent`, riducendo l'impronta di memoria dell'assistente AI.
- [ ] **Integrazione TUI/IDE**: Integrare tooltip informativi sui registri hardware in `PYC64` interrogando il `C64-KB-Agent` a runtime.

### Milestone 3: Framework Sviluppo Assembly & BASIC Avanzato (Fase 5)
- [ ] **Estensione Cicli di Clock**: Integrare la stima dei cicli macchina nel validatore di codice assembly per ottimizzare le routine critiche (es. raster interrupt, scroll fluidi).
- [ ] **Detokenizer BASIC v2 Bidirezionale**: Perfezionare `c64extractor` per consentire sia il detokenizing di file `.PRG` in testo leggibile, sia il tokenizing di file di testo in file `.PRG` BASIC pronti per l'esecuzione.
- [ ] **Linter e Analizzatore Branch**: Migliorare il linter statico di `c64validator` per mappare collisioni di variabili BASIC e salti condizionali assembly potenzialmente fuori range prima della compilazione.

### Milestone 4: Debugger & Debugging Agentico (Fase 6)
- [ ] **Inizializzazione Repo C64-Debugger**: Creazione del repository indipendente per il debugger e integrazione come submodule dell'SDK.
- [ ] **Motore di Simulazione Interattiva**: Estensione di `py6502_adapter` nel debugger per supportare step di esecuzione in avanti e all'indietro (time-travel debugging leggero).
- [ ] **Socket Client per VICE Monitor**: Implementazione del client socket per connettersi al monitor binario di VICE, abilitando breakpoint e step sul codice in esecuzione reale.
- [ ] **Agente di Self-Healing Dinamico**: Collegamento dell'agente di validazione di `C64-LLM` con lo stato del debugger per diagnosticare i crash analizzando il dump dei registri e dello stack.

---

## 5. Architettura Target del Futuro

L'obiettivo finale è una struttura modulare, orientata ai servizi, altamente professionale e stabile:

```
                  ┌─────────────────────────────────────┐
                  │          C64-Scrapy (Web)           │
                  └──────────────────┬──────────────────┘
                                     │ (Scraped Data)
                                     ▼
                  ┌─────────────────────────────────────┐
                  │      C64-KB-Agent (RAG/API)         │
                  └──────┬───────────────────────┬──────┘
                         │                       │
                         │ (RAG Context)         │ (Register Tooltips)
                         ▼                       ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│     C64-LLM (Orchestrator)      │     │           PYC64 (IDE)           │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│  Coder / Researcher / Validator │     │  TUI Compiler & Visual Editor   │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 │ (Run / Validate / Debug)              │ (Interactive Run)
                 └───────────────────┬───────────────────┘
                                     ▼
                  ┌─────────────────────────────────────┐
                  │    C64-Debugger-Agent (New Repo)    │
                  ├─────────────────────────────────────┤
                  │ py6502 / VICE Binary Monitor Client │
                  └─────────────────────────────────────┘
```

Con questa struttura, l'ecosistema C64 Intelligence si posiziona come il framework open-source più avanzato, modulare e orientato all'AI per lo sviluppo rétro-computing a 8-bit.
