# C64PY — MOS 6510 Cross Compiler

> Scrivi codice C-like nel browser. Compila in codice macchina reale per il **Commodore 64**.

C64PY è un IDE e compilatore interamente browser-based che traduce un linguaggio di alto livello ispirato al C in file **.PRG** eseguibili sul Commodore 64 (o in emulatori come VICE). Nessuna installazione, nessuna dipendenza esterna: un singolo file HTML.

---

## Funzionalità

- **Linguaggio C-like** con tipi statici: `byte`, `word`, `int`, `long/ulong/dword`, `bool`, `float`, tipi fixed-point `q8_8`…`sq16_16`
- **Generazione PRG nativa** — output direttamente caricabile con `LOAD "f",8,1` + `RUN`
- **Pipeline completa in JS**: Lexer → Parser → Analizzatore Semantico → Memory Planner → Code Generator 6510 → PRG Builder
- **Accesso diretto all'hardware**: VIC-II (schermo, sprite, disegno caratteri), SID (audio), CIA, KERNAL
- **Float via BASIC ROM** (`sin`, `cos`, `exp`, `sqr`, `log`, `atn`, `rnd`, …)
- **Fixed-Point senza ROM** — tipi Q e SQ per fisica e animazioni senza consumare la BASIC ROM
- **Raster IRQ** — handler `irq func` con prologo/epilogo automatici, stable raster, multi-split
- **IDE integrato**: syntax highlighting, AST viewer interattivo, listing ASM annotato, hex dump PRG, gestione file in localStorage
- **21 esempi pronti** — da Hello World a Pong, plasma effect, SID jingle, sprite multiplexer, fisica con gravità

---

## Avvio rapido

Sono disponibili due versioni del file:

| File | Preview emulatore | Come aprirlo |
|------|:-----------------:|-------------|
| `c64py.html` | ✗ | Doppio clic sul file — funziona direttamente dal filesystem |
| `c64py_preview.html` | ✓ | Richiede un server HTTP (anche locale) |

### `c64py.html` — versione standalone

Nessuna build richiesta. Basta aprire il file direttamente nel browser:

```bash
# Clona il repository
git clone https://github.com/tuo-utente/c64c.git

# Apri direttamente nel browser (doppio clic, o da terminale)
open c64py.html
```

### `c64py_preview.html` — versione con emulatore integrato

Questa versione include la preview del programma compilato in un emulatore C64 embedded. Poiché carica il modulo **WASM** dell'emulatore, il browser richiede che il file venga servito tramite HTTP (i browser bloccano il caricamento di WASM da `file://` per ragioni di sicurezza).

Avvia un server locale nella cartella del progetto:

```bash
# Python 3 (il più comodo — nessuna installazione aggiuntiva)
python -m http.server 8080

# oppure Node.js
npx serve .

# oppure PHP
php -S localhost:8080
```

Poi apri nel browser:

```
http://localhost:8080/c64py_preview.html
```

---

Premi **F5** (o `Ctrl+S`) per compilare. Usa **↓ PRG** per scaricare il binario e caricarlo in VICE o su hardware reale. Nella versione preview, il pulsante **▶ RUN** avvia direttamente il programma nell'emulatore integrato.

---

## Il linguaggio in breve

```c
// Raster split con IRQ e sprite in sub-pixel Q8.8
q8_8 px = $6400;   // posizione X = 100.0
q8_8 vx = $0180;   // velocità  = 1.5 pixel/frame

irq func mio_raster() {
    ack_raster_irq();
    border_color(2);
    next_raster(150);
}

def main():
    clear_screen();
    set_irq_vector(mio_raster);
    enable_raster_irq(100);

    while (1) {
        px = px + vx;
        poke($D000, byte(px >> 8));   // VIC-II — parte intera
        wait_frames(1);
    }
}
```

---

## Struttura del repository

```
c64py.html          — IDE + compilatore (file unico, self-contained, nessun server richiesto)
c64py_preview.html  — IDE + compilatore + emulatore C64 integrato (richiede server HTTP)
c64py-docs.html     — Documentazione completa del linguaggio
README.md          — Questo file
```

---

## Documentazione

La documentazione completa è in `c64py-docs.html` e copre:

- Tutti i tipi di dato e il loro layout in memoria
- Operatori, precedenza, casting
- Variabili globali, locali, array
- Controllo del flusso: `if/else`, `while`, `do…while`, `for`, `break/continue`
- Funzioni: `func`, `inline func`, `irq func`, `raw irq func`
- Builtin I/O, VIC-II, SID, timing, memoria, matematica intera e float
- Tipi Fixed-Point Q/SQ: concetti, operazioni, esempi pratici
- Modello di memoria e mappa degli indirizzi hardware
- Shortcuts IDE e gestione file

Aprire `c64py-docs.html` direttamente nel browser, oppure usare il pulsante **? HELP** nell'IDE.

---

## Requisiti

- Browser moderno con JavaScript abilitato (Chrome, Firefox, Safari, Edge)
- Per la versione con emulatore (`c64py_preview.html`): qualsiasi server HTTP locale (vedi sopra)
- Per eseguire i PRG generati: [VICE emulator](https://vice-emu.sourceforge.io/) oppure hardware reale con sd2iec / 1541

---

## Licenza

Copyright © Leonardo Boselli

Questo progetto è rilasciato sotto licenza **GNU General Public License v3.0**.

Sei libero di usare, studiare, modificare e distribuire il software, a condizione che le versioni derivate vengano rilasciate sotto la stessa licenza.

Testo completo della licenza: <https://www.gnu.org/licenses/gpl-3.0.html>

---

## Link

- 🌐 **YouDev** — [youdev.it](https://www.youdev.it)
- 🤖 Progetto realizzato con [Claude](https://claude.ai) di Anthropic
