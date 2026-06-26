# Memory Page 249

nome: UNKNOWN
descrizione: Read Tape Data (IRQ) This is the IRQ handler routine that is used for reading data from the cassette. At the end of the read, the IRQ vector is restored to the normal IRQ routine. n 64096 $FA60 Receive and Store the Next Character from Cassette This is the part of the cassette read IRQ routine that actually gets the next byte of data from the cassette. 64398 $FB8E Move the Tape SAVE/LOAD Address into the Pointer at 172 ($AC) 64407 $FB97 Reset Counters for Reading or Writing a New Byte of Cassette Data 64422 $FBA6 Toggle the Tape Data Output Line This routine sets CIA #1 Timer B, and toggles the Tape Data Output line on the 6510 on-chip I/O port (Bit 3 of location 1). 64456 $FBC8 Write Data to Cassette— Part 2 (IRQ) This IRQ handler routine is one part of the write data to cassette routine. 64618 $FC6A Write Data to Cassette— Part 1 (IRQ) This IRQ handler routine is the other part of the write data to cassette routine. n 64659 $FC93 Restores the Default IRQ Routine At the end of tape I/O operations, this subroutine is used to turn the {I screen back on and stop the cassette motor. It then resets CIA #1 Timer A to generate an interrupt every sixtieth of a second, and restores the IRQ vector to point to the normal interrupt routine that P~! updates the software clock and scans the keyboard. 235
indirizzo_memoria_decimale: 63788
indirizzo_memoria_hex: $F92C
man: Page 249

---
