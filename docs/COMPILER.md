# Specifiche del Linguaggio C64PY e del Compilatore PYC64

Il modulo **`PYC64`** (`tools/`) compila sorgenti scritti in **`C64PY`** (un sottoinsieme tipizzato di Python) in codice macchina 6502 nativo per il Commodore 64.

---

## 1. Specifiche del Linguaggio C64PY

`C64PY` adotta la sintassi pulita di Python, ma richiede annotazioni di tipo esplicite per consentire una generazione di codice assembly efficiente per la CPU a 8-bit 6510.

### 1.1 Tipi di Dati Supportati

*   **`byte`**: Intero a 8 bit senza segno (valori da `0` a `255`). Rappresenta il tipo nativo e più veloce per la CPU.
*   **`word`**: Intero a 16 bit senza segno (valori da `0` a `65535`). Usato principalmente per indirizzi di memoria e contatori estesi.
*   **`int`**: Intero a 16 bit con segno (valori da `-32768` a `32767`).
*   **`bool`**: Tipo booleano (può assumere i valori `True` o `False`).
*   **`str`**: Stringa letterale (stringa di caratteri racchiusa tra apici singoli o doppi).

### 1.2 Sintassi e Struttura del Codice

*   **Indentazione**: La definizione dei blocchi e degli scope è basata sull'indentazione (rigorosamente a 4 spazi), esattamente come in Python.
*   **Dichiarazione Funzioni**: Definite tramite la parola chiave `def`, specificando i tipi dei parametri e del valore di ritorno:
    ```python
    def calcola_colore(offset: byte) -> byte:
        return offset + 1
    ```
*   **Strutture di Controllo**:
    *   **Condizionali**: supporta `if`, `elif`, ed `else`.
    *   **Cicli**:
        *   `while cond:`: Esegue il ciclo finché la condizione è vera.
        *   `for i in range(start, end):`: Ciclo for ottimizzato per contatori di tipo `byte` o `word`.

---

## 2. Funzioni Hardware Integrate (Built-ins)

Il linguaggio espone funzioni native per interagire direttamente con i chip VIC-II, SID e la memoria RAM del Commodore 64:

| Funzione | Descrizione |
|---|---|
| `poke(address, value)` | Scrive un byte (`value`) all'indirizzo specificato (`address`). |
| `peek(address)` | Legge e restituisce il byte memorizzato all'indirizzo `address`. |
| `print(value)` | Stampa una stringa o un valore numerico a schermo. |
| `println(value)` | Stampa un valore seguito da un carattere di a capo. |
| `clear_screen()` | Pulisce lo schermo PETSCII riempiendolo di spazi. |
| `wait_frames(n)` | Sospende l'esecuzione per un numero `n` di quadri video. |

---

## 3. Il Processo di Compilazione

Il flusso operativo eseguito da `PYC64` è suddiviso nei passaggi seguenti:

```
Codice Sorgente (.c64)
    ▼
Analizzatore Lessicale (Lexer) ──► Estrae i token e riconosce gli scope
    ▼
Analizzatore Sintattico (Parser) ──► Costruisce l'AST (Albero Sintattico)
    ▼
Pianificatore di Memoria ──► Determina la mappa di memoria e alloca le variabili
    ▼
Ottimizzatore AST ──► Applica semplificazioni ed ottimizzazioni
    ▼
Generatore di Codice ──► Genera le istruzioni Assembly 6502
    ▼
PRG Builder ──► Crea il binario finale .PRG (inclusivo di stub BASIC SYS 2061)
```
