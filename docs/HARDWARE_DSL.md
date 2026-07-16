# Architettura del DSL Hardware C64PY

Questo documento descrive lo schema di astrazione hardware a 4 livelli implementato nel linguaggio **`C64PY`** all'interno dell'ecosistema **`C64-Intelligence-SDK`**.

L'obiettivo di questo DSL (Domain Specific Language) è consentire agli sviluppatori e agli agenti AI di programmare l'hardware del Commodore 64 (i chip video VIC-II, audio SID, e di I/O CIA) a vari livelli di astrazione, coniugando efficienza a basso livello e leggibilità ad alto livello.

---

## Livello 0: Operazioni Native e Assembly Diretto
Rappresenta il livello più basso. Coinvolge l'accesso diretto alla memoria e la scrittura di istruzioni assembly in-line.
*   `poke(53280, 0)` (scrive direttamente nel registro del colore del bordo).
*   `peek(53280)` (legge il colore del bordo).
*   `asm("LDA #$00")` (inserisce codice assembly diretto).

## Livello 1: Simboli Nominativi (Named Symbols)
Sostituisce i numeri magici con costanti simboliche descrittive, derivate dai manuali ufficiali del Commodore 64, migliorando la leggibilità.
*   `from pyc64c.lib.hw.vic import BORDER_COLOR, BLACK`
*   `poke(BORDER_COLOR, BLACK)`

## Livello 2: Operazioni Hardware Funzionali
Fornisce funzioni di astrazione che nascondono i dettagli implementativi (come la gestione dei valori a 16 bit o le maschere di bit per i singoli registri).
*   `from pyc64c.lib.hw.vic import set_border, set_sprite_expand_y`
*   `set_border(RED)`
*   `set_sprite_expand_y(0xFF)`

## Livello 3: Astrazioni a Componenti (Oggetti ad Alto Livello)
Espone classi Python di alto livello per gestire stati complessi e coordinare più registri hardware contemporaneamente (ad esempio, posizionare uno sprite gestendo automaticamente il bit MSB per le coordinate X maggiori di 255).
*   `from pyc64c.lib.hw.high_level import Sprite`
*   `s = Sprite(0)`
*   `s.enable()`
*   `s.pos(300, 100)` *(La classe si occupa internamente di attivare il bit X-MSB nel registro del VIC-II)*

## Livello 4: Framework di Sistema Dichiarativo (Evoluzione Futura)
Abilita la programmazione dichiarativa tramite context manager di Python per gestire cicli di interrupt o configurazioni temporanee dell'hardware.
*   `with RasterIRQ(line=100): vic.border = RED`
*   `with SID.Voice(1) as v: v.play_note(C4)`

---

*Nota: Questo DSL hardware viene parzialmente generato automaticamente a partire dai dataset di documentazione (es. "Mapping the 64") indicizzati ed elaborati dall'agente `C64-KB-Agent`.*
