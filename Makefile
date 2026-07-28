VENV := $(CURDIR)/.venv
VENV_PIP := $(VENV)/bin/pip
VENV_PYTHON := $(VENV)/bin/python3
VENV_PYTEST := $(VENV)/bin/pytest

.PHONY: all build run compile asm clean venv
.PHONY: editor-build editor-test editor-install editor-run
.PHONY: geckos-build geckos-clean

all: build

# Virtual environment
venv: $(VENV)/bin/activate
$(VENV)/bin/activate:
	python3 -m venv $(VENV)

# Builds the Docker image
build:
	docker compose build

# Starts the TUI (engine + UI)
run:
	docker compose run --rm pyc64

# Compiles test_python.c64 to PRG
compile:
	docker compose run --rm compile

# Assembles examples/hello.asm to PRG
asm:
	docker compose run --rm asm

# Cleans output directory
clean:
	rm -rf output/*

# GeckOS targets
geckos-build: venv
	$(VENV_PYTHON) geckos/os/build.py

geckos-clean:
	rm -rf geckos/dist geckos/os/bin

# Editor (READYCode-Py) targets
editor-build: venv
	$(VENV_PIP) install -e "editor[test]"

editor-test: venv
	cd editor && $(VENV_PYTEST) tests/ -v

editor-install: venv
	$(VENV_PIP) install -e "editor"

editor-run: venv
	$(VENV_PYTHON) -m readycode_py --help
