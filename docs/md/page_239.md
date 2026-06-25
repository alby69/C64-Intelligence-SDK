# Memory Page 239

nome: UNKNOWN
descrizione: Set the Word Length For the Current RS-232 Character This routine takes the number of data bits to send per RS-232 character from the control register and puts it into the .X register for use by the RS-232 routines. 61273 $EF59 Receive Next RS-232 Bit (NMI) This routine is called by the NMI interrupt handler routine to receive the next bit of data from the RS-232 device. 61310 $EF7E Setup to Receive a New Byte from RS-232 61328 $EF90 Test If Start Bit Received from RS-232 61335 #EF97 Put a Byte of Received Data into RS-232 Receive Buffer This routine checks for a Receive Buffer Overrun, stores the byte just received in the RS-232 receive buffer, and checks for Parity Error, Framing Error, or Break Detected Error. It then sets up to receive the next byte. 61409 #EFE1 CHKOUT for the RS-232 Device The Kemal CHKOUT routine calls this subroutine to define the RS232 device's logical file as an output channel. Before this can be done, the logical file must first be OPENed. 61460 $F014 CHROUT for the RS-232 Device The Kemal CHROUT routine calls this subroutine to output a character to the RS-232 device. After the logical file has been OPENed and set for output using CHKOUT, the CHROUT routine is used to actually send a byte of data. 61517 $F04D CHKIN for the RS-232 Device The Kemal CHKIN routine calls this subroutine to define the RS-232 device's logical file as an input channel. A prerequisite for this is that the logical file first be OPENed. 226
indirizzo_memoria_decimale: 61258
indirizzo_memoria_hex: $EF4A
man: Page 240

---
