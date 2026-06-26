# Memory Page 187

nome: MOVFA
descrizione: Move a Floating Point Number from FAC2 to FACl n 48140 $BCOC MOVAF Round and Move a Floating Point Number from FACl to FAC2 m 48143 $BCOF MOVEF '. i Copy FACl to FAC2 Without Rounding 48155 $BCIB ROUND Round Accumulator #1 by Adjusting the Rounding Byte If doubling the rounding byte at location 112 ($70) makes it greater than 128, the value of FACl is increased by 1. 48171 $BC2B SIGN Put the Sign of Accumulator #1 into .A Register On exit from this routine the Accumulator will hold a 0 if FACl is 0, a 1 if it is positive, and a value of 255 ($FF) if it is negative. 48185 $BC39 SGN Perform SGN The SGN routine calls the above routine to put the sign of FACl into .A, and then converts that value to a floating point number in FACl. 48216 $BC58 ABS Perform ABS The FACl sign byte at 102 ($66) is shifted right by this command, so that the top bit is a 0 (positive). ^ 48219 $BC5B FCOMP f [ Compare FACl to Memory On entry to this routine, .A and .Y point to a five-byte floating point ^^^^ number to be compared to FACl. After the comparison, .A holds a 0 if the two are equal, a 1 if the value of FACl is greater than that in the memory location, and 255 ($FF) if the value in FACl is less than that in the memory location. n 48283 $BC9B €aNT Convert FACl into Integer Within FACl /_ 1 This routine converts the value in FACl into a four-byte signed integer in 98-101 ($62-$65), with the most significant byte first. ( I 115
indirizzo_memoria_decimale: 48124
indirizzo_memoria_hex: $BBFC
man: Page 129

---
