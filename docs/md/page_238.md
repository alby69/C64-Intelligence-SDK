# Memory Page 238

nome: UNKNOWN
descrizione: ' I Set the Serial Clock Line Low (Active) This subroutine clears the serial bus clock pulse output bit (Bit 4 of CIA #2 Data Port A at 56576, $DDOO). I \ 61070 $EE8E Set the Serial Clock Line High Onactive) This subroutine sets the serial bus clock pulse output bit to 1 (Bit 4 of CIA #2 Data Port A at 56576, $DDOO). 61079 $EE97 Set Serial Bus Data Output Line Low This subroutine clears the serial bus data output bit to 0 (Bit 5 of CIA #2 Data Port A at 56576, $DDOO). 61088 $EEAO Set Serial Bus Data Output Line High This subroutine sets the serial bus data output bit to 1 (Bit 5 of CIA #2 Data Port A at 56576, $DDOO). 61097 $EEA9 Get Serial Bus Data Input Bit and Clock Pulse Input Bit This subroutine reads the serial bus data input bit and clock pulse input bit (Bits 7 and 6 of CIA #2 Data Port A at 56576, $DDOO), and returns the data bit in the Carry flag and the clock bit in the Negative flag. 61107 $EEB3 II Perform a One-Millisecond Delay ^ 61115 $EEBB [[ Send Next RS-232 Bit (NMI) This subroutine is called by the NMI interrupt handler routine to send the next bit of data to the RS-232 device. n 61230 $EF2E Handle RS-232 Errors This subroutine sets the appropriate error bits in the status register at 663 ($297). 225
indirizzo_memoria_decimale: 61061
indirizzo_memoria_hex: $EE85
man: Page 239

---
