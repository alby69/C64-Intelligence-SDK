# C64PY Sound API

This document describes the high-level Python functions for programming sound and music on the Commodore 64 using the SID chip (MOS 6581).

## Global Controls

### `sid_volume(vol: byte)`
Sets the master volume for all voices.
- `vol`: 0 (silence) to 15 (maximum volume).

### `sid_random()`
Returns a random byte from Oscillator 3.

### `sid_filter(cutoff: word, resonance: byte, mode: byte)`
Configures the global filter.
- `cutoff`: 11-bit value (0-2047).
- `resonance`: 4-bit value (0-15).
- `mode`: Bitmask for filter mode and voices to filter.
  - Bits 0-2: Voices to filter (1=Voice 1, 2=Voice 2, 4=Voice 3).
  - Bit 4: Low Pass.
  - Bit 5: Band Pass.
  - Bit 6: High Pass.

## Voice Controls (Voice 0, 1, or 2)

### `sid_setup(voice: byte, attack: byte, decay: byte, sustain: byte, release: byte)`
Sets up the ADSR envelope for a specific voice.
- `voice`: 0, 1, or 2.
- `attack`, `decay`, `sustain`, `release`: 0-15.

### `sid_freq(voice: byte, freq: word)`
Sets the frequency for a specific voice.
- `voice`: 0, 1, or 2.
- `freq`: 16-bit register value (0-65535).

### `sid_pw(voice: byte, width: word)`
Sets the pulse width for the pulse waveform.
- `voice`: 0, 1, or 2.
- `width`: 12-bit value (0-4095).

### `sid_gate(voice: byte, waveform: byte, on: byte)`
Controls the gate bit and selects the waveform.
- `voice`: 0, 1, or 2.
- `waveform`:
  - 16: Triangle
  - 32: Sawtooth
  - 64: Pulse
  - 128: Noise
- `on`: 1 to start attack/decay/sustain, 0 to start release.
