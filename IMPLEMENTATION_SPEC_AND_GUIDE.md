# Guida di Sviluppo e Specifiche di Implementazione dell'Ecosistema C64

Questa guida risponde alle tue domande su come portare avanti lo sviluppo di questo progetto che si snoda tra molteplici repository collegati (submoduli) e un repository collettore (questo SDK). Inoltre, risponde alla tua domanda sulla struttura dei package Python e fornisce le specifiche tecniche dettagliate per l'evoluzione di ciascun modulo.

---

## 1. Struttura dei Package Python in `packages/`

### Domanda: *"Vedo che nella cartella packages ci sono delle sottocartelle con lo stesso nome, come se ci fosse un doppio sottolivello inutile, è così?"*

**Risposta:** No, non è un errore o un livello superfluo, ma segue lo standard de-facto del packaging in Python (**Setuptools Layout**).

La struttura di ciascun pacchetto è la seguente:
```
packages/c64debugger/        <-- Directory Radice del Progetto (Project Root)
├── setup.py                 <-- Configurazione di installazione (metadata, dipendenze)
└── c64debugger/             <-- Sotto-cartella del Package (Package Source)
    ├── __init__.py          <-- Inizializzatore del modulo Python
    └── debugger_core.py     <-- Codice sorgente effettivo
```

#### Perché è fatta così?
1. **Indipendenza dei moduli**: Questa struttura consente a ciascun pacchetto di essere installato autonomamente tramite `pip` (es. `pip install -e packages/c64debugger`), rendendo il modulo importabile globalmente nell'ambiente virtuale (`import c64debugger`).
2. **Separazione dei file di build**: Se mettessimo `setup.py` direttamente nella cartella con il codice senza la sotto-cartella, la radice del pacchetto si mescolerebbe con file di configurazione, file temporanei di compilazione (`build/`, `dist/`, `.egg-info/`) e file del sistema di testing.
3. **Distribuzione su PyPI**: Questa gerarchia è obbligatoria per impacchettare correttamente il codice e poterlo eventualmente pubblicare su PyPI o consumare come dipendenza esterna in altri repository (ad esempio, importando `c64debugger` in `PYC64` senza dover ricorrere a complessi hack dei percorsi in `sys.path`).

*Consiglio operativo: Quando modifichi il codice sorgente del pacchetto, lavora sempre all'interno della cartella interna (es. `packages/c64debugger/c64debugger/`). Lascia la cartella esterna solo per `setup.py` e configurazioni di build.*

---

## 2. Come Gestire lo Sviluppo Multi-Repo (Workflow dei Submodule)

Poiché l'SDK raccoglie diversi repository collegati tramite sottomoduli Git, lo sviluppo richiede un'attenzione specifica per evitare disallineamenti. Di seguito trovi una guida operativa passo-passo per gestire questo flusso.

### Concetto Fondamentale
Un **Git Submodule** non è altro che un puntatore a un commit specifico di un altro repository.
- Quando fai modifiche dentro una cartella di un sottomodulo (es. `core/` o `tools/`), stai modificando il codice di quel *progetto specifico*.
- Il repository collettore (`C64-Intelligence-SDK`) traccia semplicemente quale specifico commit di `core`, `tools`, `tutorial` e `scraper` deve essere utilizzato.

---

### Scenario A: Vuoi modificare il codice di un sottomodulo (es. C64-LLM in `core/`)

Se esegui modifiche direttamente dentro le cartelle dei sottomoduli sul tuo PC, devi seguire questa sequenza per pubblicarle:

1. **Entra nel sottomodulo:**
   ```bash
   cd core
   ```
2. **Spostati sul branch corretto:**
   I sottomoduli clonati spesso si trovano in uno stato di "detached HEAD" (puntano a un commit fisso anziché a un branch). Prima di fare modifiche, assicurati di essere sul branch principale del sottomodulo (di solito `main` o `master`):
   ```bash
   git checkout main
   ```
3. **Modifica il codice e fai il commit all'interno del sottomodulo:**
   ```bash
   git add file_modificato.py
   git commit -m "Aggiunto supporto al nuovo bridge VICE"
   git push origin main
   ```
   *Nota: Ora le tue modifiche sono online sul repository indipendente `C64-LLM`.*

4. **Torna alla radice del collettore SDK e aggiorna il puntatore:**
   Ora devi dire al repository collettore che `core` è avanzato a un nuovo commit:
   ```bash
   cd ..
   git add core
   git commit -m "Aggiornato sottomodulo core all'ultimo commit"
   git push origin master
   ```

---

### Scenario B: Un altro collaboratore ha aggiornato un sottomodulo, come ottieni le modifiche?

Se qualcuno ha aggiornato i file di un sottomodulo direttamente nel suo repository originale, o se vuoi scaricare gli ultimi aggiornamenti di tutti i sottomoduli:

1. **Esegui l'aggiornamento automatico dei puntatori e dei file:**
   ```bash
   git submodule update --remote --merge
   ```
   Questo comando scaricherà i nuovi commit dai repository originali e aggiornerà il tuo codice locale.

---

### Scenario C: Clonare il repository da zero

Se devi clonare l'SDK su una nuova macchina o se un utente lo clona per la prima volta, i sottomoduli risulteranno inizialmente come cartelle vuote. Per scaricare tutto l'ecosistema in un colpo solo, usa:
```bash
git clone --recursive <URL_REPO_COLLETTORE>
```
Oppure, se hai già clonato senza sottomoduli:
```bash
git submodule update --init --recursive
```

---

## 3. Specifiche Tecniche Differenziate per i Progetti Collegati

Di seguito sono riportate le specifiche dettagliate dei miglioramenti, pronte per essere trasferite o implementate nei rispettivi repository.

### 3.1 C64-LLM (`core/`) — Assistente AI Multi-Agente
**Obiettivo:** Rompere l'isolamento dell'AI, connetterla all'esecuzione runtime, migliorare la qualità delle risposte RAG e ottimizzare le risorse.

*   **Specifica A: Integrazione VICE Headless per Validazione Runtime**
    *   *Descrizione*: Creare un agente `VICEValidatorAgent` (o espandere `ValidatorAgent` in `core/agent/validator.py`) per eseguire dinamicamente il codice assembly generato.
    *   *Flusso operativo*:
        1. Riceve il codice generato, estrae il blocco di codice assembly e lo salva come file `.asm` temporaneo.
        2. Esegue l'assembler ACME per generare un file `.prg` binario.
        3. Esegue l'emulatore VICE in modalità headless usando la porta monitor o i comandi a riga di comando per limitare i cicli di clock (`x64sc -default -autostartprgmode 1 test.prg +sound -limitcycles 10000000`).
        4. Cattura lo stato dei registri ($PC, $A, $X, $Y, $SP) e opzionalmente l'output in memoria RAM (es. dump della Screen RAM `$0400-$07E7`).
        5. Se si verifica un crash o se i registri VIC-II non corrispondono alle aspettative, produce un report di errore strutturato che viene re-iniettato nel loop Self-Healing dell'orchestratore.
*   **Specifica B: Potenziamento RAG (Reranking e Query Expansion)**
    *   *Descrizione*: Migliorare il tasso di accuratezza delle risposte RAG riducendo le allucinazioni tecniche tipiche della programmazione 6502.
    *   *Strumenti*: Integrare un modulo di reranking leggero (es. `BAAI/bge-reranker-base` o un Cross-Encoder analogo via Sentence-Transformers) per riordinare i primi 10 documenti recuperati da FAISS, filtrando quelli non pertinenti.
    *   *Query Expansion*: Espandere le query dell'utente aggiungendo automaticamente sinonimi tecnici e indirizzi di memoria correlati (es. "sprite" -> "VIC-II register $D015, $D000, sprite pointers").
*   **Specifica C: Dataset di Distillazione per Fine-Tuning**
    *   *Descrizione*: Scalare l'attuale dataset di training student (LoRA) da 76 ad almeno 1000+ coppie QA strutturate di alta qualità per la programmazione 6502/C64.
    *   *Tipologia di QA*: Factual, Code Generation, Code Explanation, Bugfix, Optimization.
    *   *Archiviazione*: Unificare i dati in un file `distillation_dataset.json` strutturato.

---

### 3.2 PYC64 (`tools/`) — Compilatore Python-like & TUI
**Obiettivo:** Dare stabilità formale al compilatore, ottimizzare l'output binario e fornire strumenti professionali per l'editing.

*   **Specifica A: Definizione formale del linguaggio (`LANGUAGE_SPEC.md`)**
    *   *Descrizione*: Scrivere una specifica formale del subset di codice Python supportato, definendo chiaramente i tipi primitivi (`byte`/`u8`, `word`/`u16`), le strutture di controllo supportate (`if`/`else`, `while`, `for` su range costanti) e i limiti delle funzioni (divieto di ricorsione a causa dello stack limitato di 256 byte del 6502).
*   **Specifica B: Backend di Compilazione Robusto**
    *   *Descrizione*: Offrire la possibilità di delegare l'assemblaggio finale a un tool standard consolidato come ACME o cc65 (compilatore C/ASM), producendo un file sorgente `.asm` standardizzato anziché affidarsi esclusivamente a un parser binario custom che rischia incompatibilità.
*   **Specifica C: Ottimizzatore a livello di IR (Intermediate Representation)**
    *   *Descrizione*: Implementare passaggi di ottimizzazione intermedi prima della generazione del codice macchina:
        *   *Constant Folding*: Sostituire espressioni matematiche costanti con un singolo valore (es. `LDA #5 + 3` -> `LDA #8`).
        *   *Dead Store Elimination*: Rimuovere scritture in memoria che vengono immediatamente sovrascritte prima di essere lette.
        *   *Zero Page Allocation*: Allocare automaticamente le variabili globali usate più frequentemente nei primi 256 byte di memoria (Zero Page `$00-$FF`) per generare istruzioni più corte e veloci (2 cicli invece di 3).
*   **Specifica D: LSP (Language Server Protocol) e TUI**
    *   *Descrizione*: Fornire l'auto-completamento dei registri hardware Commodore 64 all'interno dell'editor TUI ed esportare un protocollo LSP base per l'integrazione con VS Code.

---

### 3.3 C64GameTutorial (`tutorial/`) — Manuale e Risorse Didattiche
**Obiettivo:** Completare la parte didattica rimanente e rendere l'apprendimento interattivo ed evoluto.

*   **Specifica A: Completamento Capitoli Fase 3**
    *   *Capitolo 33 (Custom Charset & Tiles)*: Spiegare l'uso dei font ridefiniti caricati in RAM (`$2000-$2FFF`) e la creazione di mappe grafiche basate su tile 16x16. Fornire un convertitore Python `png2charset.py`.
    *   *Capitolo 34 (Creazione Immagini .D64)*: Aggiungere un tutorial pratico sull'uso del tool standard `c1541` (fornito con VICE) o un tool Python equivalente per generare file di immagine disco `.d64` pronti per l'emulatore.
*   **Specifica B: Gamification e Sito Web con MkDocs Material**
    *   *Descrizione*: Aggiornare il sito web statico del tutorial adottando il tema **MkDocs Material** configurando:
        *   La ricerca full-text nativa.
        *   La suddivisione per tag tecnici (`VIC-II`, `SID`, `Raster`, `Sprites`).
        *   Un sistema di tracciamento progressi dell'utente salvato in locale nel browser (`progress.json`).
*   **Specifica C: Integrazione Emulatore Web (jsVICE / WASM)**
    *   *Descrizione*: Integrare un emulatore Commodore 64 scritto in Javascript/WASM direttamente nelle pagine web del manuale statico, per consentire ai lettori di eseguire gli esempi di codice Assembly/BASIC con un clic senza dover installare nulla sul proprio computer.

---

### 3.4 C64-Scrapy (`scraper/`) — Scraper Centralizzato
**Obiettivo:** Diventare il fornitore unico di conoscenza aggiornata per il sistema RAG dell'ecosistema.

*   **Specifica A: Integrazione con l'API di C64-KB-Agent**
    *   *Descrizione*: Modificare le pipeline dello scraper per non scrivere semplicemente i risultati su file locali, ma inviarli strutturati (metadata + markdown/testo) direttamente agli endpoint di indicizzazione del nuovo microservizio KB-Agent via chiamate HTTP POST.

---

### 3.5 Shared Packages (`packages/`)
**Obiettivo:** Fornire le librerie di base per garantire che l'AI (`core`), l'IDE (`tools`) e i test del manuale (`tutorial`) operino sulle stesse identiche logiche di computazione del 6502.

*   **Mantenere l'indipendenza**: Continuare a usare solo import relativi all'interno dei pacchetti e assicurarsi che non importino nulla al di fuori del proprio package o da cartelle sorelle.
*   **Espansione Mappatura Memoria**: Estendere `py6502_adapter.py` nel pacchetto `c64validator` per simulare l'accesso in scrittura e lettura ai registri più comuni (VIC-II `$D000-$D02F`, SID `$D400-$D41C`, CIA `$DC00-$DD0F`) in modo che il simulatore possa gestire semplici cicli grafici o di input durante i test di validazione.

---

## 4. Nuovi Componenti Architetturali (Proposte Standalone)

Per rendere l'SDK pulito e leggero, i due grandi sistemi complessi discussi nella ROADMAP dovranno nascere come progetti separati, richiamati dall'SDK.

### 4.1 C64-KB-Agent (RAG & Knowledge Base Centralizzata) [Stato: COMPLETATO]
Questo servizio centralizza l'uso dei modelli semantici di embedding e del database vettoriale, evitando che `core/` (C64-LLM) debba caricare in memoria locale le librerie Sentence-Transformers e FAISS/ChromaDB ogni volta, abbattendo drasticamente l'uso di RAM della UI.
*   **Architettura**: Microservizio standalone in **FastAPI**, fully dockerized e pronto all'uso.
*   **Endpoint principali implementati**:
    *   `POST /kb/index`: Indicizza nuovi documenti (markdown, testo, json) generando embedding e aggiornando il database vettoriale FAISS con persistenza automatica su disco.
    *   `GET /kb/search` / `POST /kb/search`: Esegue la ricerca semantica tramite similarità vettoriale e restituisce i contesti rilevanti ordinati per score.
    *   `GET /kb/registers/{address}`: Restituisce all'istante la descrizione dettagliata, la mappatura bit-a-bit e l'esempio d'uso di qualsiasi indirizzo di memoria I/O del C64 (es. `$D011`, `$D020`, `$D400`, `$DC00`), accettando formati multipli (esadecimale, decimale, prefissi). Questo alimenta l'assistente AI e i tooltip dinamici della TUI di `PYC64`.

### 4.2 C64-Debugger-Agent (Agentic Debugging & VICE Connection)
Questo sottomodulo agirà da bridge a basso livello per guidare la correzione degli errori.
*   **Architettura**: Sottomodulo Python indipendente installabile come package.
*   **Caratteristiche**:
    *   *VICE Remote Monitor Client*: Implementa la connessione socket binary monitor con VICE (porta 6510). Permette di inviare comandi binari di stop, step, visualizzazione registri, e lettura memoria dell'emulatore in esecuzione.
    *   *Crash Diagnostician*: Analizza i registri dopo un crash per identificare bug complessi del 6502 (Stack sbilanciati, cicli infiniti) e passa il report all'LLM per auto-guarire il codice.

*Nota: Una prima implementazione prototipale di questo bridge di comunicazione binaria con VICE è stata scritta e resa disponibile direttamente all'interno dell'SDK nel pacchetto `packages/c64debugger/c64debugger/vice_bridge.py` per darti un punto di partenza concreto.*

---

## 5. Come Procedere: Roadmap Operativa per Te

Sei pronto per portare avanti il progetto ma non sai come coordinare le modifiche tra il collettore e i repository sottomoduli. Ecco il piano d'azione consigliato per i prossimi passi:

1. **Studia e testa il prototipo di comunicazione con VICE** che ho aggiunto nel pacchetto `c64debugger` (`packages/c64debugger/c64debugger/vice_bridge.py`). Questo ti darà la comprensione di come l'AI può controllare l'emulatore.
2. **Crea i branch di sviluppo nei singoli repository** seguendo le istruzioni del paragrafo 2 di questo documento. Ad esempio, entra in `core/` e crea un branch `feature/vice-validation`.
3. **Applica le modifiche modulo per modulo**:
    *   *Inizia da C64-LLM (`core/`)*: implementa l'agente che chiama l'interfaccia di validazione.
    *   *Passa a PYC64 (`tools/`)*: formalizza la sintassi e integra l'ottimizzatore.
4. **Mantieni sincronizzato l'SDK collettore**: Man mano che i sottomoduli avanzano, aggiorna il repository collettore eseguendo `git add core` (o la cartella corrispondente) ed effettua un commit sul collettore per registrare l'avanzamento dei sottomoduli.
5. **Rilascia versioni coordinate**: Usa tag Git allineati (es. `sdk-v1.2.0`, `core-v1.2.0`) per tenere traccia delle release stabili dell'intero ecosistema.
