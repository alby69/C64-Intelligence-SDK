# Memory Page 248

nome: UNKNOWN
descrizione: Check Cassette Switch This subroutine is used to check if a button on the recorder has been pressed. 63544 $F838 Test Cassette Buttons and Handle Messages for Tape Write This routine tests the sense switch, and if no buttons are depressed it prints the PRESS PLAY & RECORD message, and loops until a cassette button is pressed, or until the STOP key is pressed. If a button is pressed, it prints the message OK. These messages cannot be suppressed by changing the flag at 157 ($9D). See the entiry for 63511 ($F817) for more information. 63553 $F841 Start Reading a Block of Data from the Cassette This subroutine tests the cassette switch and initializes various flags for reading a block of data from cassette. 63588 $F864 start Writing a Block of Data to the Cassette This subroutine tests the cassette switch and initializes various flags for writing a block of data to cassette. 63605 $F875 Common Code for Reading a Data Block from Tape and Writing a Block to Tape This routine sets the actual reading or writing of a block of data. It sets CIA #1 Timer B to call the IRQ which drives the actual reading or writing routine, saves the old IRQ vector, and sets the new IRQ vector to the read or write routine. It also blanks the screen so that the video chip's memory addressing (which normally takes away some of the 6510 microprocessor's addressing time) will not interfere with the timing of the routines. 63696 $F8D0 Test the STOP Key during Cassette I/O Operations This subroutine is used to test the STOP key during tape I/O operations, and to stop I/O if it is pressed. 63714 $F8E2 Adjust CIA #1 Timer A for Tape Bit Timing 234
indirizzo_memoria_decimale: 63534
indirizzo_memoria_hex: $F82E
man: Page 248

---
