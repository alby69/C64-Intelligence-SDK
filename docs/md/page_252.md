# Memory Page 252

nome: UNKNOWN
descrizione: Terminate Cassette I/O This routine calls the subroutine above and returns from the interrupt. 64714 $FCCA Turn off the Tape Motor 64721 $FCD1 Check the Tape Read/Write Pointer This routine compares the current tape read/write address with the ending read/write address. 64731 $FCDB Advance the Tape Read/Write Pointer This routine is used to move the pointer to the current read/ write address up a byte. 64738 $FCE2 Power-On Reset Routine This is the RESET routine which is pointed to by the 6510 hardware RESET vector at 65532 ($FFFC). This routine is automatically executed when the computer is first turned on. First, it sets the Interrupt disable flag, sets the stack pointer, and clears the Decimal mode flag. Next it tests for an autostart cartridge. If one is found, the routine immediately jumps through the cartridge cold start vector at 32768 ($8000). If no cartridge is found, the Kemal initialization routines lOINIT, RAMTAS, RESTOR, and CINT are called, the Interrupt disable flag is cleared, and the BASIC program is entered through the cold start vector at 40960 ($A000). 64770 $FD02 Check for Autostart Cartridge This routine tests for an autostart cartridge by comparing the characters at locations 32772-6 ($8004-8) to the text below. The Zero flag will be set if they match, and cleared if they don't. 64784 $FD10 Text for Autostart Cartridge Check The characters stored here must be the fifth through ninth characters in the cartridge in order for it to be started on power-up. These characters are the PETASCII values for CBM, each with the high bit set ( + 128), and the characters "80". 236
indirizzo_memoria_decimale: 64696
indirizzo_memoria_hex: $FCB8
man: Page 250

---
