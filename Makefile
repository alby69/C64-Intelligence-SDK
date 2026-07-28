.PHONY: all build run compile asm clean

all: build

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
geckos-build:
	python3 geckos/os/build.py

geckos-clean:
	rm -rf geckos/dist geckos/os/bin
