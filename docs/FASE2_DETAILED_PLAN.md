# Piano di Implementazione Dettagliato — Fase 2 (IDE Core)

## Introduzione
Questo documento definisce il piano di implementazione dettagliato, tecnico e operativo per la **Fase 2 (Mesi 3-6)** dell'evoluzione strategica dell'ecosistema **C64-Intelligence-SDK** (come definito nel Master Roadmap `docs/ROADMAP.md`).
L'obiettivo primario di questa fase è la costruzione della shell desktop unificata (**C64 Intelligence Studio**), basata su Tauri (Rust), React (TypeScript) e Monaco Editor. L'IDE offrirà un'interfaccia ad alte prestazioni, multi-scheda e pronta per l'integrazione con i microservizi asincroni realizzati in Fase 1.

## Indice dei Contenuti
1. **F2.1: Shell Desktop (Tauri + React/TS)**
2. **F2.2: Code Editor (Integrazione Monaco Editor & LSP Client)**
3. **F2.3: File Explorer (Gestione Workspace)**
4. **F2.4: Tab & Terminal System (XTerm.js & Build Logs)**
5. **Milestones e Criteri di Accettazione**

---

### 1. F2.1: Shell Desktop (Tauri + React/TS)

#### Obiettivo
Creare l'applicazione desktop ultra-leggera e reattiva utilizzando Tauri per l'integrazione di sistema con l'OS (Windows, macOS, Linux) e React + TypeScript + Tailwind CSS per il frontend grafico.

#### Architettura e Configurazione di Tauri

##### A. Configurazione Tauri (`src-tauri/tauri.conf.json`)
Il backend in Rust gestirà le chiamate al file system locale, il recupero delle variabili d'ambiente, e l'avvio asincrono dei microservizi Python (`core-service`, `kb-agent`) come "Sidecars".
```json
{
  "build": {
    "distDir": "../dist",
    "devPath": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "package": {
    "productName": "C64 Intelligence Studio",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "fs": {
        "all": true,
        "scope": ["$APPDIR/*", "$USER/*"]
      },
      "path": {
        "all": true
      },
      "shell": {
        "all": true,
        "sidecar": true
      }
    },
    "bundle": {
      "active": true,
      "targets": "all"
    },
    "windows": [
      {
        "title": "C64 Intelligence Studio",
        "width": 1280,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ]
  }
}
```

##### B. Comando Rust custom per avvio Sidecar Python (`src-tauri/src/main.rs`)
```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::api::process::{Command, CommandEvent};
use tauri::Manager;

#[tauri::command]
fn start_backend_services(app_handle: tauri::AppHandle) {
    // Avvia il core-service come sidecar di Tauri
    let (mut rx, mut child) = Command::new_sidecar("c64-core-service")
        .expect("failed to setup core-service sidecar")
        .spawn()
        .expect("failed to spawn core-service sidecar");

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            if let CommandEvent::Stdout(line) = event {
                println!("Backend: {}", line);
            }
        }
    });
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![start_backend_services])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

#### Gestione dello Stato Globale (Zustand)
Utilizzeremo **Zustand** in React per una gestione dello stato performante e reattiva, minimizzando i re-render:
```typescript
import create from 'zustand';

interface IDEState {
  activeProject: string | null;
  openFiles: string[];
  activeFile: string | null;
  isCompiling: boolean;
  terminalLogs: string[];
  setActiveProject: (path: string | null) => void;
  openFile: (path: string) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  setCompiling: (status: boolean) => void;
  addLog: (log: string) => void;
}

export const useIDEStore = create<IDEState>((set) => ({
  activeProject: null,
  openFiles: [],
  activeFile: null,
  isCompiling: false,
  terminalLogs: [],
  setActiveProject: (path) => set({ activeProject: path }),
  openFile: (path) => set((state) => ({
    openFiles: state.openFiles.includes(path) ? state.openFiles : [...state.openFiles, path],
    activeFile: path
  })),
  closeFile: (path) => set((state) => {
    const nextFiles = state.openFiles.filter(f => f !== path);
    return {
      openFiles: nextFiles,
      activeFile: state.activeFile === path ? (nextFiles[0] || null) : state.activeFile
    };
  }),
  setActiveFile: (path) => set({ activeFile: path }),
  setCompiling: (status) => set({ isCompiling: status }),
  addLog: (log) => set((state) => ({ terminalLogs: [...state.terminalLogs, log] }))
}));
```

---

### 2. F2.2: Code Editor (Integrazione Monaco Editor & LSP Client)

#### Obiettivo
Integrare il potente Monaco Editor (lo stesso motore di VS Code) e connetterlo via WebSocket al Language Server (`core-service`) implementato in Fase 1.

#### Definizione Grammatiche Custom per Grammatica C64PY e BASIC v2
Configurazione Monaco per evidenziare correttamente parole chiave, token, costanti numeriche (es. hex `$D020` o `0xD020`) e commenti:

```typescript
import { Monaco } from '@monaco-editor/react';

export function registerC64Languages(monaco: Monaco) {
  // Registra il linguaggio C64PY (Python-like per 6502)
  monaco.languages.register({ id: 'c64py' });
  monaco.languages.setMonarchTokensProvider('c64py', {
    keywords: [
      'def', 'return', 'byte', 'word', 'if', 'else', 'while', 'for', 'in', 'and', 'or', 'not'
    ],
    builtins: [
      'poke', 'peek', 'wait', 'sys', 'kernal'
    ],
    tokenizer: {
      root: [
        [/[a-z_$][\w$]*/, {
          cases: {
            '@keywords': 'keyword',
            '@builtins': 'predefined',
            '@default': 'identifier'
          }
        }],
        [/#.*/, 'comment'],
        [/\$[0-9a-fA-F]+/, 'number.hex'],
        [/0x[0-9a-fA-F]+/, 'number.hex'],
        [/[0-9]+/, 'number'],
        [/"([^"\\]|\\.)*"/, 'string']
      ]
    }
  });

  // Registra il linguaggio BASIC V2 Commodore
  monaco.languages.register({ id: 'basic64' });
  monaco.languages.setMonarchTokensProvider('basic64', {
    keywords: [
      'PRINT', 'GOTO', 'GOSUB', 'RETURN', 'IF', 'THEN', 'FOR', 'TO', 'STEP', 'NEXT',
      'POKE', 'SYS', 'PEEK', 'DATA', 'READ', 'RESTORE', 'DIM', 'REM', 'END', 'RUN'
    ],
    tokenizer: {
      root: [
        [/^[0-9]+/, 'keyword.line-number'],
        [/[A-Z]+/, {
          cases: {
            '@keywords': 'keyword',
            '@default': 'identifier'
          }
        }],
        [/REM.*/, 'comment'],
        [/"([^"\\]|\\.)*"/, 'string'],
        [/[0-9]+/, 'number']
      ]
    }
  });
}
```

#### Collegamento Client WebSocket LSP
Ogni volta che il documento cambia, il client invia il codice sorgente all'endpoint WebSocket `/ws/lsp` del core-service e visualizza i diagnostici (errori di linter/sintassi) decorando l'editor:

```typescript
export class LSPClient {
  private socket: WebSocket;
  private editor: any;

  constructor(editor: any, uri: string) {
    this.editor = editor;
    this.socket = new WebSocket("ws://localhost:8000/ws/lsp");

    this.socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.method === "textDocument/publishDiagnostics") {
        this.applyDiagnostics(msg.params.diagnostics);
      }
    };
  }

  public notifyChange(content: string) {
    if (this.socket.readyState === WebSocket.OPEN) {
      const payload = {
        jsonrpc: "2.0",
        method: "textDocument/didChange",
        params: {
          textDocument: { uri: "file:///src/main.c64", version: 1 },
          contentChanges: [{ text: content }]
        }
      };
      this.socket.send(JSON.stringify(payload));
    }
  }

  private applyDiagnostics(diagnostics: any[]) {
    const monaco = (window as any).monaco;
    const model = this.editor.getModel();

    const markers = diagnostics.map(d => ({
      startLineNumber: d.range.start.line + 1,
      startColumn: d.range.start.character + 1,
      endLineNumber: d.range.end.line + 1,
      endColumn: d.range.end.character + 1,
      message: d.message,
      severity: monaco.MarkerSeverity.Error
    }));

    monaco.editor.setModelMarkers(model, "owner", markers);
  }
}
```

---

### 3. F2.3: File Explorer (Gestione Workspace)

#### Obiettivo
Offrire un gestore visuale ad albero delle cartelle e dei file di progetto, supportando operazioni di creazione, rinomina, rimozione e sincronizzazione istantanea.

#### Struttura ad Albero e Navigazione
L'esploratore file utilizzerà le API native di Tauri (`tauri::fs`) per scansionare e monitorare ricorsivamente la cartella aperta:

```typescript
import { readDir, FileEntry } from '@tauri-apps/api/fs';

export async function fetchWorkspaceTree(dirPath: string): Promise<FileEntry[]> {
  try {
    const entries = await readDir(dirPath, { recursive: true });
    return entries;
  } catch (error) {
    console.error("Errore di caricamento del file explorer:", error);
    return [];
  }
}
```

#### Operazioni tramite Context Menu
Componente visuale per click destro che offre opzioni:
- `Nuovo File`: Crea un file vuoto (`.c64`, `.asm`, `.bas`) scrivendo su disco tramite Tauri.
- `Nuova Cartella`: Crea una sottocartella.
- `Elimina`: Mostra dialogo di conferma nativo e rimuove permanentemente.
- `Rinomina`: Input inline per modificare il nome.

---

### 4. F2.4: Tab & Terminal System (XTerm.js & Build Logs)

#### Obiettivo
Fornire un'esperienza multi-scheda per l'editing simultaneo di più sorgenti e un terminale integrato reattivo basato su XTerm.js per mostrare in tempo reale i log di compilazione ed esecuzione dei simulatori.

#### Gestione Multi-Tab
L'utente può aprire file multipli; ciascun tab memorizza lo stato di editing ("dirty" se ci sono modifiche non salvate) e permette lo switch istantaneo:
- **Interfaccia Grafica**: Schede orizzontali stile VS Code con pulsante di chiusura (X) e indicatore cerchio in caso di file non salvato.
- **Integrazione con Scorciatoie**: `Ctrl+S` per salvare il file corrente tramite Tauri, aggiornando lo store Zustand e rimuovendo lo stato "dirty".

#### Integrazione XTerm.js per Console di Output
Un terminale virtuale integrato nella sezione inferiore dell'IDE cattura e stampa formattato l'output testuale ANSI dei compilatori e dei messaggi di diagnostica dell'AI:

```typescript
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';

export function initializeTerminal(container: HTMLDivElement): Terminal {
  const term = new Terminal({
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#f0f0f0'
    },
    cursorBlink: true,
    fontSize: 13,
    fontFamily: 'Consolas, Courier New, monospace'
  });

  const fitAddon = new FitAddon();
  term.loadAddon(fitAddon);
  term.open(container);
  fitAddon.fit();

  term.writeln("\x1b[1;32m=== C64 Intelligence Studio Terminal ===\x1b[0m");
  term.writeln("Pronto per ricevere log di build e debug...\r\n");

  return term;
}
```

---

## 5. Milestones e Criteri di Accettazione (Fase 2)

| ID | Milestone | Criterio di Accettazione |
|----|-----------|--------------------------|
| **M2.1** | Shell Desktop Tauri | L'app desktop si avvia su tutte le piattaforme; lo store Zustand sincronizza correttamente i percorsi di progetto e file aperti. |
| **M2.2** | Monaco Editor & LSP | Monaco visualizza l'evidenziazione sintattica custom per C64PY e BASIC. Modifiche al codice inviano frame LSP e mostrano gli errori con evidenziatori rossi (Markers) in tempo reale. |
| **M2.3** | File Explorer Funzionante | L'albero visualizza la struttura di cartelle reale. Click destro e creazione file scrive istantaneamente sul filesystem tramite Tauri. |
| **M2.4** | Terminale & Build Integrati | L'utente compila premendo un tasto rapido; il terminale XTerm.js si apre in basso e mostra i byte o eventuali errori ANSI del compilatore, catturando lo stream in uscita. |
