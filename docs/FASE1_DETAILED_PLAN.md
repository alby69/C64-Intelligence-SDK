# Piano di Implementazione Dettagliato — Fase 1 (Fondamenta e Architettura)

## Introduzione
Questo documento definisce il piano di implementazione dettagliato, tecnico e operativo per la **Fase 1 (Mesi 1-3)** dell'evoluzione strategica dell'ecosistema **C64-Intelligence-SDK** (come definito nel Master Roadmap `docs/ROADMAP.md`).
L'obiettivo primario di questa fase è stabilire un'architettura modulare multi-servizio solida, disaccoppiando l'interfaccia utente (Frontend) dalla logica computazionale e di intelligenza artificiale (Backend).

## Indice dei Contenuti
1. **F1.1: Re-architecture (Separazione Backend/Frontend)**
2. **F1.2: Plugin System (Protocolli Strumenti)**
3. **F1.3: Project Format (`.c64proj`)**
4. **F1.4: Monorepo Reorganization (Workspace)**
5. **F1.5: CI/CD Pipeline**
6. **Milestones e Criteri di Accettazione**

---

### 1. F1.1: Re-architecture (Separazione Backend/Frontend)

#### Obiettivo
Disaccoppiare l'interfaccia grafica Tauri/React (Frontend) dalla logica Python (Backend), trasformando quest'ultimo in un Language Server integrato con un motore AI asincrono.

#### Architettura di Comunicazione
La comunicazione tra il Frontend e il Backend avverrà tramite due canali principali:
- **WebSocket (per canali bidirezionali in tempo reale)**: Utilizzato per lo streaming di dati del Debugger (VICE monitor), aggiornamenti del processo di compilazione e risposte dell'AI Copilot (streaming dei token).
- **REST API (HTTP)**: Utilizzato per chiamate sincrone/asincrone classiche (es. gestione file di progetto, salvataggio preferenze, chiamate spot a singoli endpoint).

#### Definizione degli Endpoint (Contratti API)

##### A. FastAPI WebSocket: `/ws/lsp` (Language Server Protocol)
Fornisce servizi di linter, autocompletamento (non AI) ed evidenziazione di errori.
- **Request (JSON-RPC 2.0)**:
  ```json
  {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
      "textDocument": {
        "uri": "file:///src/main.c64",
        "version": 2
      },
      "contentChanges": [
        {
          "text": "10 PRINT \"HELLO WORLD\"\n20 GOTO 10"
        }
      ]
    },
    "id": 101
  }
  ```
- **Response (JSON-RPC 2.0)**:
  ```json
  {
    "jsonrpc": "2.0",
    "method": "textDocument/publishDiagnostics",
    "params": {
      "uri": "file:///src/main.c64",
      "diagnostics": []
    }
  }
  ```

##### B. FastAPI REST Endpoint: POST `/api/v1/compile`
Esegue la compilazione di un codice sorgente (BASIC o C64PY).
- **Request Body**:
  ```json
  {
    "source_code": "10 PRINT \"HELLO\"\n20 GOTO 10",
    "compiler": "c64py",
    "optimize": true,
    "load_address": "0x0801"
  }
  ```
- **Response Body**:
  ```json
  {
    "success": true,
    "prg_base64": "AYgMCgCZIkhFTExPIgAAAAA=",
    "load_address": 2049,
    "size_bytes": 17,
    "errors": []
  }
  ```

##### C. FastAPI WebSocket Endpoint: `/ws/ai-copilot`
Fornisce completamento di codice in tempo reale e chat interattiva.
- **Messaggio in Ingresso**:
  ```json
  {
    "action": "inline_completion",
    "prompt": "10 PRINT \"STAMPA IN CORSO\"\n20 ",
    "context_files": ["main.c64"]
  }
  ```
- **Messaggio in Uscita (Streaming di token)**:
  ```json
  {
    "token": "FOR I = 1 TO 10",
    "done": false
  }
  ```

---

### 2. F1.2: Plugin System (Protocolli Strumenti)

#### Obiettivo
Definire contratti astratti e interfacce standardizzate in Python e TypeScript per garantire che nuovi compiler, debugger o moduli di editing possano essere integrati senza toccare il codice core dell'IDE.

#### Interfacce Backend (Python ABC)

##### `IBuildTool`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

class BuildResult:
    def __init__(self, success: bool, prg_bytes: bytes, errors: list):
        self.success = success
        self.prg_bytes = prg_bytes
        self.errors = errors

class IBuildTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def compile(self, source: str, options: Dict[str, Any]) -> BuildResult:
        """Compila il codice sorgente in formato binario PRG."""
        pass
```

##### `IDebugger`
```python
from abc import ABC, abstractmethod
from typing import Callable, Dict, Any

class IDebugger(ABC):
    @abstractmethod
    def connect(self, host: str, port: int) -> bool:
        """Connette il debugger all'emulatore."""
        pass

    @abstractmethod
    def set_breakpoint(self, address: int) -> bool:
        """Imposta un breakpoint."""
        pass

    @abstractmethod
    def step(self) -> Dict[str, Any]:
        """Esegue una singola istruzione."""
        pass

    @abstractmethod
    def register_on_break_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Registra una callback richiamata quando l'esecuzione si interrompe."""
        pass
```

#### Interfacce Frontend (TypeScript)
```typescript
interface IEditorTool {
  id: string;
  name: string;
  onActivate(): void;
  onDeactivate(): void;
}

interface IDocumentContext {
  uri: string;
  languageId: 'c64py' | 'basic' | 'assembly';
  content: string;
}
```

---

### 3. F1.3: Project Format (`.c64proj`)

#### Obiettivo
Standardizzare la gestione dei progetti multi-file tramite un file di configurazione strutturato `.c64proj` in formato JSON/YAML.

#### Schema JSON Dettagliato
```json
{
  "$schema": "https://raw.githubusercontent.com/C64-Intelligence-SDK/schemas/main/c64proj.schema.json",
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

#### Gestione Pipeline Asset
Il compilatore/project manager deve supportare i seguenti convertitori di asset predefiniti:
- **`generate_asm` (per sprite e character set)**: Converte file binari o immagini pixel in costanti `.byte` pronte per l'assemblatore.
- **`inject` (per file musicali SID)**: Riserva spazio nella memoria RAM ed esegue il linking del file SID all'indirizzo di caricamento specificato.

---

### 4. F1.4: Monorepo Reorganization (Workspace)

#### Obiettivo
Riorganizzare l'ecosistema in un monorepo strutturato che utilizzi workspace nativi per gestire le dipendenze in modo pulito ed evitare collisioni di namespace.

#### Albero delle Directory Target
```
C64-Intelligence-SDK/ (Root)
├── packages/                  # Librerie Python condivise e indipendenti
│   ├── c64validator/          # Simulazione e validazione 6502
│   ├── c64extractor/          # Detokenizzazione BASIC e disassemblatore
│   └── c64debugger/           # Breakpoints e connessione socket a VICE
├── services/                  # Microservizi asincroni autonomi
│   ├── core-service/          # C64-LLM Core, RAG orchestrator, FastAPI backend
│   ├── kb-agent/              # C64-KB-Agent (FAISS, Sentence-Transformers)
│   └── compiler-service/      # Servizio di compilazione (PYC64, ACME)
├── frontend/                  # Tauri + React + Monaco Editor (C64 Intelligence Studio)
│   ├── src/
│   ├── src-tauri/             # Codice Rust per integrazione OS
│   └── package.json
├── tools/                     # PYC64 CLI, TUI Textual
├── docs/                      # Documentazione centrale dell'ecosistema
├── tests/                     # Suite di test di integrazione cross-modulo
├── .gitmodules                # Gestione sottomoduli Git (loose coupling)
├── pyproject.toml             # Gestione workspace Poetry/Pip
└── docker-compose.yml         # Orchestrazione per test e deploy locali
```

---

### 5. F1.5: CI/CD Pipeline

#### Obiettivo
Automatizzare i processi di test, linting e compilazione cross-piattaforma per garantire la stabilità dell'intero ecosistema.

#### Workflow GitHub Actions

##### A. `backend-tests.yml`
Esegue i test di integrazione Python per tutti i moduli e i servizi.
```yaml
name: Backend Tests & Linting

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run Pytest
      run: |
        PYTHONPATH=tools python -m pytest tests/
```

##### B. `frontend-build.yml` (Tauri Cross-Compilation)
Compila l'applicazione desktop Tauri per Windows, macOS e Linux.
```yaml
name: Frontend Desktop Build

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    strategy:
      fail-fast: false
      matrix:
        platform: [macos-latest, windows-latest, ubuntu-22.04]
    runs-on: ${{ matrix.platform }}
    steps:
    - uses: actions/checkout@v3
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: 18
    - name: Install Rust
      uses: dtolnay/rust-toolchain@stable
    - name: Install Ubuntu Dependencies
      if: matrix.platform == 'ubuntu-22.04'
      run: |
        sudo apt-get update
        sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.0-dev libjavascriptcoregtk-4.0-dev build-essential curl wget libssl-dev libayatana-appindicator3-dev librsvg2-dev
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm install
    - name: Build Tauri App
      uses: tauri-apps/tauri-action@v0
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tagName: app-v__VERSION__
        releaseName: "C64 Intelligence Studio v__VERSION__"
```

---

## 6. Milestones e Criteri di Accettazione (Fase 1)

| ID | Milestone | Criterio di Accettazione |
|----|-----------|--------------------------|
| **M1.1** | Separazione Backend/Frontend | Il backend espone un server FastAPI con WebSocket LSP funzionante; la compilazione asincrona via JSON è testata al 100%. |
| **M1.2** | Definizione dei Plugin | Le interfacce astratte `IBuildTool` e `IDebugger` sono scritte e documentate. Un mock compilatore ne dimostra l'implementazione. |
| **M1.3** | Parser di Progetto Esteso | La classe `C64Project` valida con successo file di configurazione sia in formato JSON che YAML e gestisce correttamente la build dell'entry_point. |
| **M1.4** | Workspace Riorganizzato | Tutti i pacchetti e servizi risiedono nelle directory descritte in F1.4. Nessun file esterno sporca i sottomoduli. |
| **M1.5** | CI/CD Completamente Funzionante | Le GitHub Actions eseguono con successo i test del backend su ogni Pull Request e creano una bozza di release con i binari Tauri compilati per Windows/macOS/Linux sui tag di versione. |
