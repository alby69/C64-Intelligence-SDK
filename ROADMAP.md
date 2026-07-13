# C64 Ecosystem Master Roadmap & Guida di Integrazione

Questo documento rappresenta la guida di riferimento architetturale e operativa dell'intero ecosistema **C64 Intelligence SDK**. Consolida l'analisi dello stato dell'arte, le specifiche tecniche dei sottomoduli, i workflow multi-repo e la pianificazione strategica a lungo termine.

---

## 1. Analisi dello Stato dell'Arte per Modulo

L'SDK raccoglie diversi repository collegati tramite sottomoduli Git. Di seguito viene dettagliato lo stato di maturità e implementazione di ciascun modulo.

### 1.1 C64-LLM (`core/`) — Stato: Beta Avanzata
*   **Componenti implementati**:
    *   **Architettura Multi-Agente**: Flusso di ragionamento strutturato (Researcher → Coder → Validator → Orchestrator) con meccanismo di Self-Healing ricorsivo.
    *   **Pipeline RAG**: Indicizzazione locale tramite FAISS + `sentence-transformers` (all-MiniLM). Indicizzazione di manuali `.md` e scraping proattivo da oltre 25 fonti tecniche. Filtraggio basato su parole chiave per mitigare il rumore OCR.
    *   **Validatore statico**: Integrazione con ACME assembler e linter sintattico BASIC v2.
    *   **Knowledge Distillation**: Pipeline pre-generata di 76 coppie QA per LoRA training su modelli Qwen2.5-Coder (0.5B/1.5B).
    *   **UI di Controllo**: Interfaccia Gradio interattiva su porta `:7860` con Wiki Grafo SVG dinamico dei concetti chiave.
*   **Gap critici riscontrati**:
    *   **Assenza di validazione dinamica**: Mancanza di un ponte con un emulatore headless (VICE) per validare a runtime il comportamento logico del codice generato.
    *   **Dimensioni modello ridotte**: Il modello predefinito da 1.5B (GGUF) fatica su compiti di ottimizzazione complessi.
    *   **Assenza di Reranking**: Il retrieval RAG manca di una fase di ri-punteggio semantico (es. Cross-Encoder) per queries complesse o ambigue.
    *   **Memoria persistente**: Mancanza di un memory layer conversazionale persistente per tracciare sessioni di programmazione lunghe.

### 1.2 PYC64 (`tools/`) — Stato: Alpha/Beta
*   **Componenti implementati**:
    *   Lexer, Parser e generatore di codice che compila un dialetto Python-like in Assembly 6502.
    *   Assembler interno custom per produrre file `.PRG`.
    *   TUI (Textual User Interface) con editor, tabulazione multipla ed evidenziazione base.
    *   Integrazione in ambiente Docker.
*   **Gap critici riscontrati**:
    *   **Mancanza di Specifica Formale**: Il sottoinsieme di Python supportato non è formalizzato, creando ambiguità nell'uso da parte dell'utente o dell'AI.
    *   **Rischio di Bug dell'Assembler Custom**: L'assembler interno non ha una suite di test comparativa con assembler standard (es. ACME, KickAss), esponendo a potenziali difetti silenziosi nella codifica binaria.
    *   **Mancanza di Ottimizzatore IR**: Assenza di meccanismi di ottimizzazione statici (constant folding, dead code elimination, register/Zero-Page allocation).
    *   **Mancanza di Language Server (LSP)**: Difficoltà nell'integrazione con IDE moderni come VS Code.

### 1.3 C64GameTutorial (`tutorial/`) — Stato: Production-Ready
*   **Componenti implementati**:
    *   27 capitoli completi in Italiano e 27 in Inglese (~12.000 righe di contenuto).
    *   28 soluzioni in puro assembly 6502 e template di gioco completo con architettura modulare a 3 layer.
    *   Pipeline CI/CD con GitHub Actions (`validate.yml`), controllo dimensioni del codice (`size-report`) e test headless in VICE con screenshot.
    *   Script di utilità: `png2sprite.py` per conversione asset e generatori di grafi delle dipendenze.
*   **Gap critici riscontrati**:
    *   **Fase 3 Incompleta**: Mancano i capitoli conclusivi riguardanti la definizione di Custom Charset/Tiles e la creazione guidata di file immagine disco `.D64`.
    *   **Esperienza utente statica**: Il sito MkDocs utilizza un tema base; manca un'interfaccia interattiva e moderna (MkDocs Material) con ricerca avanzata e dark mode.
    *   **Assenza di test funzionali complessi**: Gli screenshot nei test di VICE non sono associati a librerie di computer vision o OCR per verificare che lo sprite si sia effettivamente mosso o che l'interrupt sia stabile.

### 1.4 C64-Scrapy (`scraper/`) — Stato: Production-Ready
*   **Componenti implementati**:
    *   Crawler basato su Scrapy per raccogliere documenti tecnici, sorgenti e metadati da C64-Wiki, Codebase64 e Archive.org.
*   **Gap critici riscontrati**:
    *   Invia i dati solo a file locali anziché inoltrarli in streaming al microservizio centralizzato di Knowledge Base.

### 1.5 C64-KB-Agent (`kb-agent/`) — Stato: Rilascio Completo (Production-Ready)
*   **Componenti implementati**:
    *   **Architettura Microservizio**: Implementazione autonoma in FastAPI, Docker compatibile, con supporto CORS e standardizzazione OpenAPI.
    *   **Motore RAG integrato**: Embeddings semantici (SentenceTransformers) e database vettoriale FAISS per indicizzare (`/kb/index`) e ricercare (`/kb/search`) con persistenza locale automatica.
    *   **Database dei Registri Hardware**: Mappatura completa e normalizzazione di oltre 60 registri hardware (VIC-II, SID, CIA 1, CIA 2). Supporta formati esadecimale (`$D011`, `0xD011`), decimale (`53265`) e fornisce descrizione bit-a-bit ed esempi in Assembly 6502.
    *   **Automazione dei Test**: Suite di test integrata (pytest + TestClient) con il 100% di pass rate.
*   **Gap critici riscontrati**:
    *   Nessuno. Pronto per fungere da hub semantico centralizzato.

### 1.6 C64-Debugger-Agent (`debugger/`) — Stato: Scheletro / Inizializzato
*   **Componenti implementati**:
    *   Submodule inizializzato in Git e tracciato dall'SDK parent.
*   **Gap critici riscontrati**:
    *   Richiede il porting o l'estensione del bridge monitor di VICE (`packages/c64debugger/c64debugger/vice_bridge.py`) per abilitare il debug interattivo da parte di agenti LLM.

---

## 2. Criticità Trasversali dell'Ecosistema

| Criticità | Impatto | Descrizione | Moduli Coinvolti |
| :--- | :--- | :--- | :--- |
| **Nessun bridge emulatore ↔ AI** | **Critico** | L'AI genera codice senza poterlo testare in esecuzione, dipendendo da loop di correzione manuali dell'utente. | `core`, `tools`, `debugger` |
| **Dataset di distillazione insufficiente** | **Alto** | 76 coppie QA non bastano per addestrare un modello LoRA affidabile sulle peculiarità dell'architettura C64. | `core` |
| **Assembler custom non validato** | **Alto** | Possibili divergenze binarie rispetto agli standard consolidati della scena C64. | `tools` |
| **Linguaggio non specificato** | **Medio** | Ambiguità su quali costrutti Python siano effettivamente supportati dal compilatore. | `tools` |
| **Isolamento dei moduli** | **Medio** | I sottomoduli lavoravano in silos prima dell'introduzione dei pacchetti condivisi e del RAG centralizzato. | SDK globale |

---

## 3. Analisi di Progetti Complementari ed Esterni

### 3.1 VibeC64 (by bbence84)
*   **Punti di forza**: Integrazione con hardware reale (KungFu Flash, REST API di Ultimate C64), cattura video via OpenCV, astrazione multi-provider per LLM (Anthropic, OpenAI, OpenRouter, Google AI).
*   **Azioni per l'SDK**: Adottare l'architettura `LLMProvider` astratta per connettersi ad API esterne quando il modello locale da 1.5B fallisce.

### 3.2 C64AIToolChain (by dexmac221)
*   **Punti di forza**: Integrazione con la suite standard cc65, connessione socket bidirezionale al Remote Monitor di VICE (porta 6510), feedback visivo tramite VLM.
*   **Azioni per l'SDK**: Sfruttare il protocollo di Remote Monitor di VICE in Python (strutturato as modulo condiviso in `packages/c64debugger`).

---

## 4. Specifiche Tecniche di Evoluzione e Piani d'Azione

### 4.1 C64-LLM (AI Core)
*   **VICE Headless Bridge**: Sviluppare un modulo per lanciare x64sc, caricare il codice compilato tramite ACME, connettersi via socket monitor, estrarre lo stato dei registri ed evidenziare i crash in un report strutturato per l'orchestratore.
*   **RAG con Reranking**: Inserire una pipeline Cross-Encoder (Sentence-Transformers) per ponderare i risultati estratti dal database FAISS prima dell'iniezione nel prompt.
*   **Scale-up Dataset**: Espandere le coppie QA di distillazione da 76 a 1000+ esempi.

### 4.2 PYC64 (Compiler & TUI)
*   **LANGUAGE_SPEC.md**: Redigere e pubblicare la specifica dettagliata dei tipi supportati (`byte`, `word`, `bool`), dei limiti dello stack e dei costrutti.
*   **Backend ACME/cc65**: Consentire l'utilizzo di ACME/cc65 come motori alternativi stabili per la generazione binaria.
*   **Ottimizzatore IR**: Integrare constant folding, dead store elimination e allocazione automatica in Zero Page (`$00-$FF`).

### 4.3 C64GameTutorial (Didattica)
*   **Custom Charset & D64**: Completare la Fase 3 del manuale (capitolo 33 e 34).
*   **MkDocs Material**: Aggiornare la veste grafica del tutorial includendo dark mode, tag semantici ed emulatore Commodore 64 integrato in WebAssembly (WASM).

### 4.4 C64-Scrapy (Data Acquisition)
*   **Integrazione API**: Modificare le pipeline per inoltrare i documenti estratti direttamente all'endpoint `/kb/index` del microservizio `C64-KB-Agent`.

---

## 5. Struttura dei Package Python in `packages/`

I moduli condivisi utilizzano la gerarchia standard **Setuptools Layout**:
```
packages/c64debugger/        <-- Directory Radice del Progetto (Project Root)
├── setup.py                 <-- Configurazione di installazione
└── c64debugger/             <-- Sotto-cartella del Package (Package Source)
    ├── __init__.py          <-- Inizializzatore del modulo
    └── vice_bridge.py       <-- Codice sorgente effettivo
```

### Perché questa struttura?
1. **Indipendenza**: Consente di installare ciascun pacchetto in modo isolato (`pip install -e packages/c64debugger`), rendendolo importabile ovunque (`import c64debugger`).
2. **Separazione**: Evita che file temporanei di compilazione (`build/`, `dist/`, `.egg-info/`) si mescolino con il codice sorgente o il sistema di test.

---

## 6. Guida allo Sviluppo Multi-Repo (Workflow Submodule)

I sottomoduli Git tengono traccia di un commit specifico. Per effettuare modifiche ed evitare disallineamenti:

### Scenario A: Modifica locale di un sottomodulo
1. Entra nella cartella (es. `cd core`).
2. Spostati sul branch corretto: `git checkout main`.
3. Modifica i file, effettua il commit e invia:
   ```bash
   git add .
   git commit -m "feat: nuova feature"
   git push origin main
   ```
4. Torna alla radice del collettore e aggiorna il puntatore:
   ```bash
   cd ..
   git add core
   git commit -m "chore: aggiornato sottomodulo core"
   git push origin master
   ```

### Scenario B: Ottenere modifiche remote nel collettore
```bash
git submodule update --remote --merge
```

### Scenario C: Clonazione da zero con sottomoduli
```bash
git clone --recursive <URL_REPO>
```

---

## 7. Roadmap Tecnica (6 Mesi)

```
 Mese 1-2: SDK & VICE Bridge    Mese 3-4: PYC64 & Dataset      Mese 5-6: Tutorial v2 & VLM
┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
│ • Docker Compose Unificato│  │ • Rilascio LANGUAGE_SPEC  │  │ • MkDocs Material + WASM  │
│ • Sviluppo VICE Bridge    │  │ • Ottimizzatore IR        │  │ • Completamento Fase 3    │
│ • Integrazione Validator  │  │ • Dataset QA a 1000+ coppie│ │ • Validazione visiva VLM   │
│ • Reranker su RAG         │  │ • Fine-tuning su Qwen 7B  │  │ • Connessione Hardware   │
└───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘
```

---

## 8. Azioni Immediate (Quick Wins)

1. **RAG Centralizzato**: Completato l'avvio e l'implementazione del microservizio `C64-KB-Agent`.
2. **Standardizzazione README**: Verificato e semplificato l'hub documentale per far convergere la documentazione di tutti i sottomoduli sul collettore principale.
3. **Uso dei Package Condivisi**: Verificare che `core`, `tools` e `tutorial` utilizzino esclusivamente i moduli ospitati in `packages/` per evitare codice ridondante.
