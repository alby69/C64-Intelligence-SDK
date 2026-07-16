# API Audio del Linguaggio C64PY (Chip SID)

Questo documento descrive le funzioni integrate nel linguaggio **`C64PY`** (gestite dal compilatore **`PYC64`** nell'ecosistema **`C64-Intelligence-SDK`**) per programmare suoni e musica sul chip SID (MOS 6581/8580) del Commodore 64.

---

## 1. Controlli Globali del Chip SID

### `sid_volume(vol: byte)`
Imposta il volume principale (*Master Volume*) del chip per tutte e tre le voci.
*   `vol`: Valore da `0` (silenzio) a `15` (volume massimo).

### `sid_random()`
Legge e restituisce un byte casuale generato dall'oscillatore della Voce 3 del chip SID.

### `sid_filter(cutoff: word, resonance: byte, mode: byte)`
Configura il filtro analogico globale del SID.
*   `cutoff`: Valore a 11 bit (da `0` a `2047`) per impostare la frequenza di taglio.
*   `resonance`: Valore a 4 bit (da `0` a `15`) per la risonanza.
*   `mode`: Maschera di bit per selezionare il tipo di filtro e le voci da filtrare:
    *   Bit 0-2: Voci da filtrare (1 = Voce 1, 2 = Voce 2, 4 = Voce 3).
    *   Bit 4: Filtro Passa-Basso (Low Pass).
    *   Bit 5: Filtro Passa-Banda (Band Pass).
    *   Bit 6: Filtro Passa-Alto (High Pass).

---

## 2. Controlli Individuali per Voce (Voci 0, 1, 2)

### `sid_setup(voice: byte, attack: byte, decay: byte, sustain: byte, release: byte)`
Configura l'inviluppo ADSR (*Attack, Decay, Sustain, Release*) per la voce selezionata.
*   `voice`: L'indice della voce da configurare (`0`, `1`, o `2`).
*   `attack`, `decay`, `sustain`, `release`: Valori da `0` a `15` per impostare i rispettivi stadi dell'inviluppo.

### `sid_freq(voice: byte, freq: word)`
Imposta la frequenza dell'oscillatore per la voce specificata.
*   `voice`: L'indice della voce (`0`, `1`, o `2`).
*   `freq`: Valore a 16 bit (da `0` a `65535`) da scrivere nei registri di frequenza del SID.

### `sid_pw(voice: byte, width: word)`
Imposta la larghezza dell'impulso (*Pulse Width*) per la forma d'onda quadra.
*   `voice`: L'indice della voce (`0`, `1`, o `2`).
*   `width`: Valore a 12 bit (da `0` a `4095`).

### `sid_gate(voice: byte, waveform: byte, on: byte)`
Abilita o disabilita il bit di Gate per avviare o arrestare l'inviluppo, e seleziona contemporaneamente la forma d'onda desiderata.
*   `voice`: L'indice della voce (`0`, `1`, o `2`).
*   `waveform`: Il valore corrispondente alla forma d'onda da generare:
    *   `16`: Triangolare (Triangle)
    *   `32`: Dente di sega (Sawtooth)
    *   `64`: Impulso/Quadra (Pulse)
    *   `128`: Rumore bianco (Noise)
*   `on`: Impostare a `1` per attivare il Gate (avvia la sequenza Attack-Decay-Sustain), impostare a `0` per disattivarlo (avvia la fase di Release).
