# C64 Intelligence Studio — Roadmap

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Tauri Desktop Shell (Rust)             │
│  ┌───────────────────────────────────────────┐   │
│  │        React + TypeScript Frontend        │   │
│  │  Monaco Editor · xterm Terminal · Zustand  │   │
│  └─────────────────┬─────────────────────────┘   │
│                    │ Tauri IPC                    │
│  ┌─────────────────┴─────────────────────────┐   │
│  │     Python Backend (FastAPI / sidecar)     │   │
│  │  Plugin System · Compiler · Editor · Disk  │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

- **Desktop shell**: Tauri (Rust) — already scaffolded in `frontend/src-tauri/`
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + Monaco + xterm — deps in `frontend/package.json`
- **Backend**: Python FastAPI — already exists in `services/core_service/`
- **Plugin system**: Python `plugin.json` manifests + dynamic loader

---

## Phase 1: Plugin Infrastructure

> Plugin discovery, loading, and manifest system.

- [x] Create `plugins/` directory structure (one folder per plugin)
- [x] Define `plugin.json` manifest schema (name, version, description, commands, entry_point, category, icon)
- [x] Implement `services/core_service/plugin_loader.py` — scans `plugins/*/plugin.json`, validates, registers commands
- [x] Add `/api/v1/plugins` endpoint to core_service (list loaded plugins)
- [x] Add `/api/v1/plugins/{name}/exec` endpoint (execute a plugin command)
- [x] Create placeholder `plugin.json` for each existing submodule:
  - [x] `plugins/compiler/plugin.json` → wraps `run_c64.py compile`
  - [x] `plugins/editor/plugin.json` → wraps `run_c64.py tokenize|detokenize|minify|prettify`
  - [x] `plugins/disk-tools/plugin.json` → wraps `run_c64.py disk`
  - [x] `plugins/emulator/plugin.json` → wraps `run_c64.py run`
  - [x] `plugins/project-manager/plugin.json` → wraps `pyc64_project.py`

**Status**: Complete

---

## Phase 2: UI Core

> React app shell with layout, sidebar, tabs, and terminal panel.

- [x] Create `frontend/src/main.tsx` — React entry point with Monaco language init
- [x] Create `frontend/src/App.tsx` — root component with layout + keyboard shortcuts
- [x] Create `frontend/src/components/Sidebar.tsx` — plugin launcher + file tree
- [x] Create `frontend/src/components/TabBar.tsx` — open file tabs with dirty indicators
- [x] Create `frontend/src/components/EditorPanel.tsx` — Monaco editor with C64PY/BASIC syntax
- [x] Create `frontend/src/components/TerminalPanel.tsx` — color-coded terminal output
- [x] Create `frontend/src/components/StatusBar.tsx` — bottom status bar with language info
- [x] Create `frontend/src/components/PluginCard.tsx` — interactive plugin cards with exec
- [x] Extend `frontend/src/store/ideStore.ts` — file state, terminal state, dirty tracking
- [x] Create `frontend/src/store/pluginStore.ts` — plugin list from backend API
- [x] Create `frontend/src/services/pluginService.ts` — fetch + exec via FastAPI
- [x] Create `frontend/src/services/commandService.ts` — compile/run/disk commands
- [x] Style layout with TailwindCSS (dark C64 theme, custom color palette)

**Status**: Complete

---

## Phase 3: Tauri IPC Bridge

> Rust commands that bridge React frontend ↔ Python backend.

- [x] Extend `frontend/src-tauri/src/main.rs` — add Tauri commands:
  - [x] `run_command` — spawn sidecar process, stream stdout/stderr
  - [x] `read_file` — read file content
  - [x] `write_file` — write file content
  - [x] `list_directory` — list directory entries
  - [x] `open_file_dialog` — native file open dialog
  - [x] `save_file_dialog` — native file save dialog
- [x] Create `frontend/src/services/tauriBridge.ts` — TypeScript wrappers for Tauri invoke
- [x] Update `frontend/src-tauri/tauri.conf.json` — ensure shell/sidecar permissions
- [ ] Add `c64py-cli` sidecar binary config (or use `python3 run_c64.py` via shell)

**Status**: Complete (except sidecar binary config)

---

## Phase 4: Command Wrapping

> Each plugin command maps to a real CLI invocation.

- [x] **Compiler plugin**: `compile` → `python3 run_c64.py compile <file>` + `basic` → `run_c64.py basic <file>`
- [x] **Editor plugin**: `tokenize`, `detokenize`, `minify`, `prettify` → `run_c64.py` editor subcommands with `-o` output
- [x] **Disk plugin**: `disk list`, `disk inject`, `disk extract`, `disk create` → `run_c64.py disk` with positional args
- [x] **Emulator plugin**: `run` → `python3 run_c64.py run <file>` with `--sid`, `--resid`, `--timeout` options
- [x] **Project Manager plugin**: `load`, `build` → `pyc64_project.py load/build <path>`
- [x] Map command outputs to UI panels (terminal output, error highlights, PRG size info)
- [x] Implement command history in terminal panel (arrow keys, 50 cmd buffer)
- [x] Enhanced `plugin_loader.py` with `cli_args` override + `parse_output()` for structured output
- [x] Enhanced `commandService.ts` with per-plugin argument builders

**Status**: Complete

---

## Phase 5: Advanced Integration

> Deep integration of all SDK modules into the launcher.

- [x] **Monaco Editor** with C64PY + BASIC V2 syntax highlighting (registered in `monacoLanguages.ts`)
- [x] **LSP integration** via WebSocket — wired into `EditorPanel.tsx`, real-time diagnostics on `.c64` files
- [x] **AI Copilot** via WebSocket — `AiCopilotPanel.tsx` with prompt input, streaming tokens, insert-to-editor
  - Templates: PRINT, FOR loops, POKE/colors, SPRITE, SID sound, disk, custom
  - Context-aware: sends last 500 chars of active file
- [x] **Disk image browser** — `DiskBrowser.tsx` with D64/D81 directory viewer, extract, create new disk
  - Backend endpoints: `GET /api/v1/disk/list`, `POST /api/v1/disk/create`
- [x] **C64 screen preview** — `C64ScreenPreview.tsx` with C64 color palette, cursor, READY. prompt
- [ ] **Memory map viewer** — for debugger integration (deferred to Phase 6)
- ] **Sprite/char editor** — basic visual asset editor (deferred to Phase 6)
- [x] **Project wizard** — `ProjectWizard.tsx` with templates (Hello World, Blinking Screen, Sprite Demo, Empty)

**Status**: Complete

---

## Phase 6: Polish & Distribution

> Build system, packaging, documentation.

- [x] Tauri build config for Linux (.deb, .AppImage), macOS (.dmg), Windows (.nsis/.msi)
  - Platform-specific bundle settings (deb depends, nsis installer, macOS min version)
  - Window constraints: min 800x600, centered on launch
- [x] Icons and branding (C64 Intelligence Studio logo — placeholder icons in `icons/`)
- [x] First-run setup wizard (`FirstRunWizard.tsx`) — detects Python + VICE, guides setup
  - Accessible via F1 shortcut
  - Steps: Welcome → Python detection → VICE detection → Done
- [x] Auto-update mechanism (Tauri updater configured in `tauri.conf.json`)
- [x] Keyboard shortcuts (Ctrl+B compile, Ctrl+S save, F5 run, Ctrl+O open, F1 help)
- [x] User preferences persistence
  - Rust backend: `load_preferences`/`save_preferences` commands (JSON in config dir)
  - Frontend: `preferencesService.ts` bridge
  - Auto-saves last project, font size, theme, VICE path, window size
  - Window state restored on launch
- [x] Integration tests for plugin system (`test_plugin_system.py`)
  - Plugin discovery, metadata, commands
  - Command execution (success + error paths)
  - Output parsing (messages, errors, PRG size, addresses, file paths)
  - SDK root and file existence checks
- [x] Documentation: setup guide embedded in FirstRunWizard, keyboard shortcuts on welcome screen

**Status**: Complete

---

## Existing Components (already implemented)

| Component | Location | Status |
|---|---|---|
| C64PY Compiler | `pyc64c/` | Complete |
| ASM 6502 Assembler | `pyc64c/asm6502.py` | Complete |
| PRG Code Emitter | `pyc64c/code_emitter.py` | Complete |
| READYCode Tokenizer | `editor/readycode_py/tokenizer.py` | Complete |
| BASIC Minifier/Prettifier | `editor/readycode_py/transform.py` | Complete |
| D64/D81 Disk Images | `editor/readycode_py/diskimage.py` | Complete |
| PETSCII Converter | `editor/readycode_py/petscii.py` | Complete |
| CLI Wrapper | `run_c64.py` | Complete |
| Project Manager | `pyc64_project.py` | Complete |
| FastAPI Core Service | `services/core_service/main.py` | Complete |
| Plugin Interfaces | `services/core_service/plugins.py` | Complete (abstract) |
| Plugin Loader | `services/core_service/plugin_loader.py` | Complete |
| Tauri IPC Bridge | `frontend/src-tauri/src/main.rs` | Complete |
| User Preferences | `frontend/src-tauri/src/main.rs` + `preferencesService.ts` | Complete |
| React IDE Shell | `frontend/src/App.tsx` | Complete |
| Sidebar + File Tree | `frontend/src/components/Sidebar.tsx` | Complete |
| Monaco + BASIC Lang | `frontend/src/services/monacoLanguages.ts` | Complete |
| LSP Client | `frontend/src/services/lspClient.ts` | Complete |
| AI Copilot | `frontend/src/components/AiCopilotPanel.tsx` | Complete |
| Disk Browser | `frontend/src/components/DiskBrowser.tsx` | Complete |
| C64 Screen Preview | `frontend/src/components/C64ScreenPreview.tsx` | Complete |
| Project Wizard | `frontend/src/components/ProjectWizard.tsx` | Complete |
| First Run Wizard | `frontend/src/components/FirstRunWizard.tsx` | Complete |
| Zustand Stores | `frontend/src/store/` | Complete |
| Plugin/Command Svc | `frontend/src/services/` | Complete |
| Plugin System Tests | `test_plugin_system.py` | Complete |
| Docker Build | `Dockerfile` + `docker-compose.yml` | Complete |

---

## Submodules

| Submodule | Path | Description |
|---|---|---|
| core | `core/` | C64PY compiler core |
| tools | `tools/` | Utility tools |
| tutorial | `tutorial/` | C64PY tutorial/examples |
| scraper | `scraper/` | Web scraper module |
| kb-agent | `kb-agent/` | Knowledge base agent |
| debugger | `debugger/` | C64 debugger |
| geckos | `geckos/` | GeckOS microkernel |
| editor | `editor/` | READYCode (Python) |
