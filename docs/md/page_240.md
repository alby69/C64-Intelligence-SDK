# Memory Page 240

nome: GETIN
descrizione: for the RS-232 Device The Kernal GETIN routine calls this subroutine to remove the next j ( byte of data from the RS-232 receive buffer and return it in the Accumulator. The routine checks for the Receive Buffer Empty Error. It is also called by the Kernal CHRIN routine, which essentially does ^ the same thing as GETIN for the RS-232 device. 61604 $F0A4 stop CIA #2 RS-232 NMIs for Serial/Cassette Routines This subroutine turns off the NMIs that drive the RS-232 routines before any I/O is done using the serial bus or cassette device. Such interrupts could throw off the timing of those I/O routines, and interfere with the transmission of data. 61629 $FOBD Kernal Control Messages The ASCII text of the Kernal I/O control messages is stored here. The last byte of every message has Bit 7 set to 1 (ASCII value+128). The messages are: I/O ERROR SEARCHING FOR PRESS PLAY ON TAPE PRESS RECORD & PLAY ON TAPE LOADING SAVING VERIFYING FOUND OK 61739 $F12B Print Kernal Error Message If in Direct Mode This routine first checks location 157 ($9D) to see if the messages are enabled. If they are, it prints the message indexed by the .Y register. 61758 $F13E GETIN Get One Byte from the Input Device This is a documented Kernal routine whose jump table entry point is at 65508 ($FFE4). The routine jumps through a RAM vector at 810 ($32A). Its function is to get a character from the current input device (whose device number is stored at 153, $99). In practice, it operates identically to the CHRIN routine below for all devices except for the keyboard. If the keyboard is the current input device, this routine 227
indirizzo_memoria_decimale: 61574
indirizzo_memoria_hex: $F086
man: Page 241

---
