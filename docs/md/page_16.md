# Memory Page 16

nome: UNKNOWN
descrizione: Character ROM Image for VIC-II Chip When Using Memory Bank 0 (Default) Though the VIC-II chip shares memory with the 6510 processor chip, it does not always see that memory in exactly the same way as the main microprocessor. Although the 6510 accesses RAM at these locations, when the VIC-II is banked to use the first 16K of RAM (which is the default condition), it sees the character ROM here (the 6510 cannot access this ROM unless it is switched into its memory at 49152 ($C000)). This solves the riddle of how the VIC-II chip can use the character ROM at 49152 ($C000) for character shape data and RAM at 1024 ($400), when it can only address memory within a 16K range. It also means that the RAM at 4096-8192 cannot be used for screen display memory or user-defined character dot data, and sprite data blocks 64-127 are not accessible.
indirizzo_memoria_decimale: 4096-8191
indirizzo_memoria_hex: $1000-$1FFF
man: Page 97

---
