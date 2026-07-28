VENV := $(CURDIR)/.venv
VENV_PIP := $(VENV)/bin/pip
VENV_PYTHON := $(VENV)/bin/python3
VENV_PYTEST := $(VENV)/bin/pytest
BACKEND_PORT := 8000
FRONTEND_DIR := frontend

.PHONY: all help
.PHONY: build run compile asm clean
.PHONY: venv setup plugins
.PHONY: editor-build editor-test editor-install editor-run
.PHONY: geckos-build geckos-clean geckos-status
.PHONY: backend backend-deps backend-start
.PHONY: frontend frontend-deps frontend-start
.PHONY: ide tauri-dev
.PHONY: docker-run docker-build docker-compile docker-asm

all: help

# ── AIUTO ──────────────────────────────────────────────────────

help:
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║   C64 Intelligence Studio — Comandi Rapidi          ║"
	@echo "╠══════════════════════════════════════════════════════╣"
	@echo "║  SETUP                                              ║"
	@echo "║    make setup         Installa TUTTO (venv, editor, ║"
	@echo "║                      backend, frontend)             ║"
	@echo "║    make venv          Crea .venv virtual environment║"
	@echo "║    make backend-deps  Installa dipendenze backend   ║"
	@echo "║    make frontend-deps Installa dipendenze frontend  ║"
	@echo "║    make editor-build  Installa editor in .venv      ║"
	@echo "║                                                    ║"
	@echo "║  IDE (C64 Intelligence Studio - consigliato)       ║"
	@echo "║    make ide           Avvia backend + frontend      ║"
	@echo "║    make ide-backend   Solo backend (FastAPI)        ║"
	@echo "║    make ide-frontend  Solo frontend (Vite dev)      ║"
	@echo "║    make tauri-dev     IDE completa (Tauri + Rust)   ║"
	@echo "║                                                    ║"
	@echo "║  PLUGIN CLI (usa i plugin da terminale)            ║"
	@echo "║    make plugins       Mostra tutti i plugin         ║"
	@echo "║    python3 plugins/tutorial/wrapper.py list         ║"
	@echo "║    python3 plugins/knowledge/wrapper.py status      ║"
	@echo "║    python3 plugins/disk-tools/wrapper.py create ... ║"
	@echo "║                                                    ║"
	@echo "║  DOCKER (ambiente legacy terminale)                ║"
	@echo "║    make docker-build  Build immagini Docker         ║"
	@echo "║    make docker-run    Avvia TUI legacy (pyc64_ui)   ║"
	@echo "║                                                    ║"
	@echo "║  GECKOS                                             ║"
	@echo "║    make geckos-build  Compila GeckOS-NG OS          ║"
	@echo "║    make geckos-status Mostra stato build            ║"
	@echo "║                                                    ║"
	@echo "║  TEST                                                ║"
	@echo "║    make editor-test   Test editor (pytest)            ║"
	@echo "║    make plugin-test   Test plugin system              ║"
	@echo "╚══════════════════════════════════════════════════════╝"

# ── SETUP COMPLETO ─────────────────────────────────────────────

setup: venv editor-build backend-deps frontend-deps

# Virtual environment
venv: $(VENV)/bin/activate
$(VENV)/bin/activate:
	python3 -m venv $(VENV)

# ── DOCKER (ambiente legacy TUI) ──────────────────────────────

docker-build:
	docker compose build

docker-run:
	docker compose run --rm pyc64

docker-compile:
	docker compose run --rm compile

docker-asm:
	docker compose run --rm asm

# Alias retrocompatibili
build: docker-build
run: docker-run
compile: docker-compile
asm: docker-asm

clean:
	rm -rf output/*

# ── GECKOS ────────────────────────────────────────────────────

geckos-build: venv
	$(VENV_PYTHON) plugins/geckos/wrapper.py build

geckos-status: venv
	$(VENV_PYTHON) plugins/geckos/wrapper.py status

geckos-clean:
	rm -rf geckos/dist geckos/os/bin

# ── EDITOR (READYCode-Py) ─────────────────────────────────────

editor-build: venv
	$(VENV_PIP) install -e "editor[test]"

editor-test: venv
	$(VENV_PYTHON) -m pytest editor/tests/ -v

editor-install: venv
	$(VENV_PIP) install -e "editor"

editor-run: venv
	$(VENV_PYTHON) -m readycode_py --help

# ── BACKEND (FastAPI) ─────────────────────────────────────────

backend-deps: venv
	$(VENV_PIP) install -r services/core_service/requirements.txt 2>/dev/null || \
	$(VENV_PIP) install fastapi uvicorn pydantic

backend-start: venv
	@echo "╔═══════════════════════════════════════════════╗"
	@echo "║  Backend in ascolto su http://localhost:8000  ║"
	@echo "║  API docs: http://localhost:8000/docs         ║"
	@echo "╚═══════════════════════════════════════════════╝"
	cd services/core_service && $(VENV_PYTHON) -m uvicorn main:app --host 0.0.0.0 --port $(BACKEND_PORT) --reload

# ── FRONTEND (React + Vite) ──────────────────────────────────

frontend-deps:
	cd $(FRONTEND_DIR) && npm install

frontend-start:
	@echo "╔═══════════════════════════════════════════════╗"
	@echo "║  Frontend in ascolto su http://localhost:5173 ║"
	@echo "╚═══════════════════════════════════════════════╝"
	cd $(FRONTEND_DIR) && npm run dev

# ── IDE COMPLETO (backend + frontend) ─────────────────────────

ide-backend: backend-deps
	@$(MAKE) backend-start

ide-frontend: frontend-deps
	@echo "⚠️  Avvia PRIMA il backend in un altro terminale: make ide-backend"
	@$(MAKE) frontend-start

# Avvia backend e frontend in finestre tmux. Se non hai tmux, usa terminali separati.
ide:
	@echo "╔════════════════════════════════════════════════════════╗"
	@echo "║  Avvio C64 Intelligence Studio                        ║"
	@echo "║                                                       ║"
	@echo "║   Terminal 1: make ide-backend  (FastAPI :8000)      ║"
	@echo "║   Terminal 2: make ide-frontend (Vite    :5173)      ║"
	@echo "║                                                       ║"
	@echo "║  Poi apri http://localhost:5173 nel browser            ║"
	@echo "║  Oppure fai make tauri-dev per l'app desktop           ║"
	@echo "╚════════════════════════════════════════════════════════╝"
	@$(MAKE) -j2 backend-start frontend-start 2>/dev/null || \
	(echo "Usa due terminali separati:"; echo "  make ide-backend"; echo "  make ide-frontend")

# Tauri (desktop app) — richiede Rust + Cargo + Tauri CLI
tauri-dev: frontend-deps
	@echo "╔═══════════════════════════════════════════════╗"
	@echo "║  Avvio C64 Intelligence Studio (Tauri)        ║"
	@echo "║  Assicurati che il backend sia in esecuzione: ║"
	@echo "║    make ide-backend                           ║"
	@echo "╚═══════════════════════════════════════════════╝"
	cd $(FRONTEND_DIR) && npx tauri dev

# ── PLUGIN CLI ────────────────────────────────────────────────

plugins: venv
	$(VENV_PYTHON) scripts/list_plugins.py

plugin-test: venv
	$(VENV_PYTHON) -m pytest test_plugin_system.py -v
