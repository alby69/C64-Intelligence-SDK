# C64 Ecosystem Roadmap & Guida di Integrazione

Questo documento definisce l'analisi dello stato dell'arte, le criticità trasversali e la pianificazione strategica per il consolidamento e l'evoluzione a lungo termine del **C64 Intelligence SDK** e dei suoi componenti.

---

## 1. Analisi dello Stato dell'Arte (Stato di Implementazione per Modulo)

L'SDK funge da collettore e orchestratore per l'intero ecosistema C64. Di seguito è analizzato lo stato di maturità di ciascun componente integrato e dei relativi sottomoduli.

### 1.1 C64-LLM (`core/`) — Stato: Beta Avanzata
*   **Componenti implementati**:
    *   **Architettura Multi-Agente**: Flusso di ragionamento strutturato (Researcher → Coder → Validator → Orchestrator) con meccanismo di Self-Healing ricorsivo.
    *   **Pipeline RAG**: Indicizzazione locale tramite FAISS + `sentence-transformers` (all-MiniLM). Indicizzazione di 9 manuali `.md` e scraping proattivo da oltre 25 fonti tecniche. Filtraggio basato su parole chiave per mitigare il rumore OCR.
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

---

## 2. Criticità Trasversali dell'Ecosistema

| Criticità | Impatto | Descrizione | Moduli Coinvolti |
| :--- | :--- | :--- | :--- |
| **Nessun bridge emulatore ↔ AI** | **Critico** | L'AI genera codice senza poterlo testare in esecuzione, dipendendo da loop di correzione manuali dell'utente. | `core`, `tools` |
| **Dataset di distillazione insufficiente** | **Alto** | 76 coppie QA non bastano per addestrare un modello LoRA affidabile sulle peculiarità dell'architettura C64. | `core` |
| **Assembler custom non validato** | **Alto** | Possibili divergenze binarie rispetto agli standard consolidati della scena C64. | `tools` |
| **Linguaggio non specificato** | **Medio** | Ambiguità su quali costrutti Python siano effettivamente supportati dal compilatore. | `tools` |
| **Isolamento dei moduli** | **Medio** | I sottomoduli lavorano in silos, riducendo l'esperienza d'uso integrata tutorial → editor → AI. | SDK globale |

---

## 3. Analisi di Progetti Complementari ed Esterni

Durante lo sviluppo sono stati analizzati due progetti rilevanti nella comunità per arricchire l'architettura dell'SDK:

### 3.1 VibeC64 (by bbence84)
*   **Punti di forza**:
    *   Integrazione con hardware reale (KungFu Flash, REST API di Ultimate C64) e cattura video via OpenCV.
    *   Supporto multi-provider per LLM (Anthropic, OpenAI, OpenRouter, Google AI) tramite astrazione.
*   **Azioni per l'SDK**:
    *   Adottare l'architettura `LLMProvider` astratta per connettersi ad API esterne di grandi dimensioni (es. Claude 3.5 Sonnet) quando il modello locale da 1.5B fallisce.
    *   Pianificare un tab "Hardware" per consentire l'invio diretto del `.PRG` generato a cartucce o emulatori fisici.

### 3.2 C64AIToolChain (by dexmac221)
*   **Punti di forza**:
    *   Integrazione nativa con la suite standard **cc65** (C e Assembly).
    *   Connessione socket bidirezionale al Remote Monitor di VICE (porta 6510).
    *   Feedback visivo tramite VLM (Vision-Language Models) inviando screenshot a modelli di Computer Vision.
*   **Azioni per l'SDK**:
    *   Implementare il protocollo del Remote Monitor di VICE in Python (strutturato come modulo condiviso in `packages/c64debugger`).
    *   Integrare agenti di validazione visiva (VLM) leggeri per analizzare gli screenshot generati dalle simulazioni.

---

## 4. Specifiche di Miglioramento (Piano d'Azione)

### 4.1 C64-LLM (AI Core)
1.  **VICE Headless Bridge**: Sviluppare un modulo per lanciare x64sc, caricare il codice compilato tramite ACME, connettersi via socket monitor, estrarre lo stato dei registri ed evidenziare i crash in un report strutturato per l'orchestratore.
2.  **RAG con Reranking**: Inserire una pipeline Cross-Encoder (Sentence-Transformers) per ponderare i risultati estratti dal database FAISS prima dell'iniezione nel prompt.
3.  **Scale-up Dataset**: Espandere le coppie QA di distillazione da 76 a 1000+ esempi, focalizzandosi su ottimizzazioni, interrupt grafici, manipolazione del SID e programmazione BASIC v2.

### 4.2 PYC64 (Compiler & TUI)
1.  **LANGUAGE_SPEC.md**: Redigere e pubblicare la specifica dettagliata dei tipi supportati (`byte`, `word`, `bool`), dei limiti dello stack e dei costrutti.
2.  **Backend ACME/cc65**: Consentire l'utilizzo di ACME/cc65 come motori alternativi stabili per la generazione binaria partendo dal codice compilato.
3.  **Ottimizzatore IR**: Integrare constant folding, dead store elimination e allocazione automatica in Zero Page (`$00-$FF`) per incrementare la velocità d'esecuzione del codice generato.

### 4.3 C64GameTutorial (Didattica)
1.  **Custom Charset & D64**: Completare la Fase 3 del manuale scrivendo i capitoli inerenti i font personalizzati in RAM e la creazione guidata di dischi virtuali `.D64`.
2.  **MkDocs Material**: Aggiornare la veste grafica del tutorial includendo dark mode, tag semantici, tracciamento locale dei progressi utente ed emulatore Commodore 64 integrato in WebAssembly (WASM).

---

## 5. Roadmap Tecnica (6 Mesi)

```
 Mese 1-2: SDK & VICE Bridge    Mese 3-4: PYC64 & Dataset      Mese 5-6: Tutorial v2 & VLM
┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
│ • Docker Compose Unificato│  │ • Rilascio LANGUAGE_SPEC  │  │ • MkDocs Material + WASM  │
│ • Sviluppo VICE Bridge    │  │ • Ottimizzatore IR        │  │ • Completamento Fase 3    │
│ • Integrazione Validator  │  │ • Dataset QA a 1000+ coppie│ │ • Validazione visiva VLM   │
│ • Reranker su RAG         │  │ • Fine-tuning su Qwen 7B  │  │ • Connessione Hardware   │
└───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘
```

*   **Mese 1 - 2: Consolidamento SDK & Connettività Emulatore**
    *   Rifinitura della suite Docker Compose per orchestrare l'intero SDK in un unico comando.
    *   Integrazione del modulo `vice_bridge` nel loop di validazione dell'agente AI in `core/`.
    *   Integrazione del Reranker semantico nella pipeline RAG.
*   **Mese 3 - 4: Consolidamento Compilatore e Dataset di Addestramento**
    *   Pubblicazione della specifica formale del compilatore PYC64.
    *   Integrazione dell'ottimizzatore a livello IR e migrazione del backend di assemblaggio ad ACME.
    *   Espansione proattiva del dataset di training ed esecuzione di LoRA fine-tuning su modelli Qwen2.5-Coder-7B.
*   **Mese 5 - 6: Interattività e Validazione Visiva**
    *   Upgrade del manuale didattico con MkDocs Material ed emulatore WASM locale.
    *   Completamento dei capitoli didattici su Custom Charset e immagini D64.
    *   Sperimentazione di validazione automatica del comportamento grafico del codice tramite modelli di visione (VLM) ed estrazione della Screen RAM.

---

## 6. Azioni Immediate (Quick Wins)

1.  **Unificazione dei file README**: Semplificare i README interni dei sottomoduli facendoli puntare alla documentazione dell'SDK principale per i passaggi di setup globale, lasciando solo le specificità del modulo.
2.  **GitHub Actions Cross-Repo**: Configurare un workflow centralizzato nella radice dell'SDK che cloni ricorsivamente i sottomoduli e ne verifichi i test in sequenza.
3.  **Benchmark delle Performance**: Creare un file `BENCHMARK.md` per tracciare il tempo medio di generazione del codice da parte dell'LLM, l'efficienza binaria (byte) del codice generato da PYC64 rispetto ad ACME scritto a mano, e l'accuratezza delle risposte del RAG.
4.  **Uso dei Package Condivisi**: Verificare che `core`, `tools` e `tutorial` utilizzino esclusivamente i moduli ospitati in `packages/` (come `c64validator`, `c64extractor`, `c64debugger`) evitando ridondanze.
