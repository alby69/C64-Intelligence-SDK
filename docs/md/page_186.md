# Memory Page 186

nome: CONUPK
descrizione: Move a Floating Point Number from Memory into FAC2 This subroutine loads FAC2 from the four-byte number (three mantissa and one sign) pointed to by the .A and .Y registers. 47799 $BAB7 MULDIV Add Exponent of FACl to Exponent of FAC2 47828 $BAD4 MLDVEX Handle Underflow or Overflow 47842 $BAE2 MULIO Multiply FACl by 10 This subroutine is called to help convert a floating point number to a series of ASCII numerals. 47865 $BAF9 TENC The Constant 10 in Five-Byte Floating Format 47870 $BAFE DIVIO Divide FACl by 10 47887 $BBOF FDIV Divide a Number in Memory by FACl This number in memory is stored to FAC2, and this routine falls through to the next. 47890 $BB12 FDIVT Divide FAC2 by FACl This routine is used to divide the contents of FAC2 by the contents of FACl, with the result being stored in FACl. A check for division by 0 is made before dividing. 48034 $BBA2 MOVFM Move a Floating Point Number from Memory to FACl This routine loads FACl with the five-byte floating point number pointed to by the address stored in the Accumulator (low byte) and the .Y register (high byte). 48071 $BBC7 MOV2F Move a Floating Point Number from FACl to Memory This routine is used to move a number from the Floating Point Accumulator (FACl) to memory at either 92-96 ($5C-$60) or 87-91 ($57$5B), depending on the entry point to the routine. 114
indirizzo_memoria_decimale: 47756
indirizzo_memoria_hex: $BA8C
man: Page 128

---
