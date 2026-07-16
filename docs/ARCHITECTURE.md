# Architettura del Compilatore PYC64

Questa sezione descrive l'architettura interna del compilatore **`PYC64`** (`pyc64c`), il motore di compilazione integrato nel **`C64-Intelligence-SDK`** per compilare programmi scritti nel linguaggio **`C64PY`** (Python-like) in binari nativi Commodore 64 (`.PRG`).

---

## 1. La Pipeline di Compilazione

La compilazione si sviluppa lungo 6 fasi sequenziali:

```
Sorgente (.c64)
    │
    ▼
1. Lexer (lexer.py) ────────► Genera token e gestisce scope basati su indentazione
    │
    ▼
2. Parser (parser.py) ──────► Genera l'AST (Abstract Syntax Tree)
    │
    ▼
3. Memory Planner ──────────► Alloca locazioni globali/locali in Zero Page o RAM
    │
    ▼
4. Optimizer (optimizer.py) ► Svolge Constant Folding, Dead Code Elimination, ecc.
    │
    ▼
5. Code Generator ──────────► Converte l'AST ottimizzato in istruzioni assembly 6502
    │
    ▼
6. PRG Builder ─────────────► Assembla con il BASIC stub (SYS 2061) e la Runtime Library
    │
    ▼
File Binario (.PRG)
```

### Dettaglio dei Componenti

1. **Lexer (`lexer.py`)**: Converte il codice sorgente testuale in token sintattici. Gestisce l'indentazione tipica di Python inserendo token fittizi `INDENT` e `DEDENT` per definire i blocchi di codice.
2. **Parser (`parser.py`)**: Costruisce l'Albero Sintattico Astratto (AST) applicando regole grammaticali sui token generati dal lexer.
3. **Memory Planner (`compiler.py` / `memory_map.py`)**: Analizza le variabili globali e locali per mappare gli indirizzi di memoria fisica sul Commodore 64. Ottimizza l'uso della Zero Page (indirizzi veloci da `$02` a `$FF`) e della RAM libera (generalmente a partire da `$080D` / `$0801`).
4. **Optimizer (`optimizer.py`)**: Svolge passaggi di ottimizzazione sul codice per garantire un'elevata efficienza dell'assembly generato (ad esempio, pre-calcolo delle costanti).
5. **Code Generator (`code_gen.py` / `code_emitter.py`)**: Esegue il traversal dell'AST ed emette le corrispondenti istruzioni macchina 6502.
6. **Runtime Library (`runtime.py`)**: Fornisce macro e subroutine 6502 pre-compilate per facilitare operazioni ricorrenti come matematica avanzata, manipolazione dello schermo PETSCII, ed entrate/uscite hardware.
7. **PRG Builder (`prg_builder.py`)**: Unisce il codice generato, la libreria di runtime e un blocco BASIC iniziale (es. `10 SYS 2061`) in un unico file `.PRG` direttamente caricabile su Commodore 64 o emulatore VICE.

---

## 2. Funzioni Built-in del Linguaggio `C64PY`

Il compilatore offre out-of-the-box diverse funzioni built-in per interfacciarsi con l'hardware del C64:

*   `print(val)`: Stampa a schermo una stringa o un valore numerico (byte).
*   `println(val)`: Stampa il valore seguito da un carattere di a capo.
*   `print_at(x, y, testo)`: Posiziona il cursore alle coordinate specificate (0-39, 0-24) e stampa il testo.
*   `poke(addr, val)`: Scrive direttamente un byte in memoria.
*   `peek(addr)`: Legge direttamente un byte dalla memoria.
*   `clear_screen()`: Pulisce lo schermo PETSCII.
*   `border_color(color)`: Cambia il colore del bordo del C64 (registro `$D020`).
*   `screen_color(color)`: Cambia il colore dello sfondo dello schermo (registro `$D021`).
*   `wait_frames(n)`: Sospende l'esecuzione per `n` quadri video (sfrutta l'interrupt raster).
*   `sei()` / `cli()`: Disabilita/Abilita gli interrupt della CPU 6510.
