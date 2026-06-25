# Memory Page 192

nome: UNKNOWN
descrizione: BootGEOS The jump vector to the short program used to reboot GEOS This vector is used to restart GEOS by having the user insert the GEOS system disk, as long as the program that calls it has kept the memory area from $C000-$C02F intact. 49155 $C003 ResetHandle The jump vector to the code that initializes GEOS from a cold start Location Range: 49408-49863 ($0100$0207) OS_JUMPTAB GEOS Operating System jump table Just as Commodore maintains a jump table of Kemal routines in order to provide a fixed entry point for certain useful I/O functions, GEOS also maintains a jump table of important GEOS routines. This
indirizzo_memoria_decimale: 49152
indirizzo_memoria_hex: $C000
man: Page 281

---
