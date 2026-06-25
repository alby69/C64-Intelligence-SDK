# PYC64 — Python-to-C64 Cross-Compiler & 6502 Assembler Toolkit

> Compila codice Python-like in codice macchina nativo per il **Commodore 64**.
> Assembla codice 6502 in file `.PRG` eseguibili.
> Tutto in Python puro, senza JavaScript, senza browser.

PYC64 è un toolkit completo per lo sviluppo C64:
- **`pyc64c/`** — Compiler Python → PRG: trasforma codice Python-like (`def`, `if`, `while`, `for`) in codice macchina 6502
- **`asm6502.py`/`pyc64c/asm6502.py`** — Assembler 6502 standalone: assembla codice assembly 6502 in file .PRG
- **`run_c64.py`** — CLI: compila, genera BASIC, esegui in c64py emulator
- **Docker** — Ambiente riproducibile, build con un comando

---

## Quick Start

### Con Python (locale)

```bash
# 1. Compila un sorgente Python-like (.c64) in PRG
python3 run_c64.py test_python.c64

# 2. Assembla un sorgente assembly 6502 (.asm) in PRG
python3 asm6502.py examples/hello.asm -l
```

### Con Docker

```bash
# Build
docker build -t pyc64 .

# Compila il test
docker run --rm -v "$(pwd)/output:/app/output" pyc64 \
  python3 /app/asm6502.py /app/examples/hello.asm -o /app/output/hello.prg

# Compila un sorgente Python-like (.c64)
docker run --rm -v "$(pwd):/app" -v "$(pwd)/output:/app/output" pyc64 \
  python3 -c "
from pyc64c.compiler import compile_to_prg
with open('/app/test_python.c64') as f: src = f.read()
prg, res = compile_to_prg(src)
if prg:
    with open('/app/output/test_python.prg', 'wb') as f: f.write(prg)
    print(f'OK: {len(prg)} byte')
"
```

---

## Componenti

### 1. Python-to-C64 Compiler (`pyc64c/`)

Linguaggio Python-like (`def`, `if`/`elif`/`else`, `while`, `for … in range`, `and`/`or`/`not`, `True`/`False`, `#` commenti) compilato in codice 6502.

| File | Ruolo |
|------|-------|
| `token_types.py` | Token e vocabolario del linguaggio |
| `lexer.py` | Lexer indentation-based (Python-style) |
| `parser.py` | Parser ricorsivo discendente |
| `ast_nodes.py` | Nodi AST e helper type-system |
| `code_emitter.py` | Emitter 6502: opcodes, label, fixup |
| `code_gen.py` | Code generator: da AST a 6502 |
| `basic_gen.py` | BASIC generator (fallback BASIC listing) |
| `prg_builder.py` | Builder: BASIC stub + code + runtime + BSS |
| `runtime.py` | Runtime library: print, cls, wait, mul |
| `compiler.py` | Pipeline orchestrator |
| `asm6502.py` | **Assembler 6502 standalone** (vedi sotto) |

**Builtin supportate:**
`print`, `println`, `print_at`, `poke`, `peek`, `clear_screen`, `border_color`, `screen_color`, `wait_frames`, `sei`, `cli`

### 2. 6502 Assembler (`asm6502.py`)

Assembler dual-pass per MOS 6502/6510, completamente in Python.

**Caratteristiche:**
- Tutti gli opcode standard 6502 con tutti i modi di indirizzamento
- Label globali e locali (`.local` con scope)
- Direttive: `.org`, `.byte`/`.db`, `.word`/`.dw`, `.text`/`.asc`, `.null` (null-terminated), `.fill`/`.ds`/`.res`, `.align`, `.include`/`.incbin`
- Espressioni numeriche con `+`, `-`, `*`, `/`, `&`, `|`, `^`, `<<`, `>>`, `<` (low byte), `>` (high byte)
- Letterali: decimali, hex (`$` o `0x`), binari (`%`), char (`'X'`)
- Forward reference (due passate)
- Branch relativi con risoluzione automatica
- Output: PRG (load-address + dati) o raw binary
- Listing annotato con indirizzi e byte emessi

**CLI:**
```bash
python3 asm6502.py sorgente.asm          # Compila → sorgente.prg
python3 asm6502.py sorgente.asm -l       # Mostra listing
python3 asm6502.py sorgente.asm --labels # Mostra tabella simboli
python3 asm6502.py sorgente.asm -o out.prg --org $1000
python3 asm6502.py sorgente.asm --raw    # Output raw binary
```

**Esempio di sorgente assembly:**
```asm
; hello.asm — Hello World per C64
        .org $0801

basic:  .word basic_end
        .word 10
        .null " sys2061"
basic_end:

main:   lda #$93        ; clear screen
        jsr $ffd2       ; CHROUT
        ldx #0
loop:   lda msg,x
        beq done
        jsr $ffd2
        inx
        bne loop
done:   rts

msg:    .null "HELLO WORLD!"
```

### 3. Runtime Library (`pyc64c/runtime.py`)

Routines pre-assembled in 6502 incluse automaticamente nel PRG:

| Routine | Descrizione |
|---------|-------------|
| `_cls` | Clear screen via KERNAL CHROUT ($FFD2) |
| `_print_str` | Stampa stringa null-terminata inline (dopo JSR) |
| `_print_byte` | Stampa byte A come decimale (3 cifre, leading zero soppressi) |
| `_wait_frames` | Delay loop (~20576 cicli/frame, 1 frame PAL ≈ 1/50s) |
| `_mul_byte` | Moltiplicazione: A × $FC → A (8-bit) |

---

## Architettura

```
Sorgente (.c64 / .asm)
    │
    ├── Python-like (.c64) → Lexer → Parser → AST → CodeGen → PRGBuilder → .PRG
    │                                                          └→ BASICGenerator → .BAS
    │
    └── Assembly (.asm)   → Asm6502 (dual-pass) → .PRG
```

### Flusso di compilazione PRG

1. **BASIC stub** automatico: `0 SYS2061` (12 byte)
2. **Codice macchina** a `$080D`: startup (set $01/$36), chiamata `main()`, restore $37, RTS
3. **Runtime library** (selezionata in base ai builtin usati)
4. **BSS** (variabili globali non-zero-page)

### Wait frame (dettaglio critico)

`_wait_frames` usa un **delay loop** invece del raster sync (`$D012`). Questo perché la modalità batch Rust di `c64py` (`cpu_step_quantum` → `step_fast_batch`) **non avanza il raster register**. Il delay loop funziona in entrambe le modalità (batch e step).

```
LDA #16           ; outer loop
STA $FE
inner: LDX #0
       DEX : BNE inner    ; 256 × 5 cicli
       DEC $FE : BNE outer
       DEC $FD : BNE loop
RTS                         ; ~20576 cicli/frame
```

---

## Docker

```bash
# Build
docker build -t pyc64 .

# Assembla
docker run --rm -v "$(pwd)/output:/app/output" pyc64 \
  python3 /app/asm6502.py /app/examples/hello.asm -o /app/output/hello.prg

# Compila Python-like
docker run --rm -v "$(pwd):/app" -v "$(pwd)/output:/app/output" pyc64 \
  python3 -c "
from pyc64c.compiler import compile_to_prg
prg, res = compile_to_prg(open('/app/test_python.c64').read())
if prg: open('/app/output/test.prg','wb').write(prg)
"

# Shell interattiva
docker run --rm -it -v "$(pwd):/app" pyc64 /bin/bash
```

### docker-compose

```bash
docker compose up pyc64    # Compila test_python.c64
```

---

## Documentazione C64

Nella cartella `docs/`:

- **`Compute's Mapping the Commodore 64.pdf`** — Mappa completa della memoria: VIC-II, SID, CIA, KERNAL, BASIC
- **`C64 Programmer's Reference Guide.pdf`** — Guida di riferimento del programmatore C64
- **`Complete Commodore Inner Space Anthology.pdf`** — Raccolta di articoli tecnici sul C64

---

## Struttura del repository

```
├── pyc64c/              # Compilatore Python puro
│   ├── __init__.py
│   ├── token_types.py, lexer.py, parser.py
│   ├── ast_nodes.py, ops.py
│   ├── code_emitter.py, code_gen.py, basic_gen.py
│   ├── prg_builder.py, runtime.py, compiler.py
│   └── asm6502.py       # Assembler 6502 standalone
├── asm6502.py            # CLI assembler
├── run_c64.py            # CLI compilatore
├── test_python.c64       # Esempio: sprite + score + joystick
├── test_python.prg       # PRG compilato
├── examples/
│   └── hello.asm         # Hello World 6502
├── docs/                 # Documentazione C64 (PDF)
├── c64/                  # Emulatore WASM
├── c64py.html            # IDE browser originale (JS)
├── c64py_preview.html    # IDE + emulatore (JS)
├── src/                  # Sorgenti JS originali
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Esempi

### Python-like → PRG

```python
# test_python.c64
score: byte = 0
px: byte = 200
py: byte = 100
vx: byte = 1
vy: byte = 1

def main():
    clear_screen()
    while True:
        # Leggi joystick port 2
        joy = peek($DC00)
        if joy & 16 == 0:  # fire premuto
            score = score + 10
            print_at 0, 0
            print "SCORE: "
            print score
        wait_frames 1
```

### Assembly 6502 → PRG

```asm
; OScilloscopio VIC-II border
        .org $0801
basic:  .word basic_end, 10
        .null " sys2061"
basic_end:
loop:   inc $d020
        jmp loop
```

---

## Requisiti

- **Python 3.10+**
- **Docker** (opzionale)
- **VICE** (opzionale, per eseguire i PRG)
- **c64py** (opzionale: `pip install c64py`) — emulatore C64 in Python

---

## Licenza

GNU General Public License v3.0 — Copyright © Leonardo Boselli

---

## Link

- **YouDev** — [youdev.it](https://www.youdev.it)
- Progetto realizzato con [Claude](https://claude.ai) di Anthropic
