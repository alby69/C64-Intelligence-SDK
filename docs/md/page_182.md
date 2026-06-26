# Memory Page 182

nome: CHRD
descrizione: Perform CHR$ The CHR$ routine creates a descriptor on the temporary string stack for the one-byte string whose value is specified in the command, and sets a pointer to that string. 46848 $B700 LEFTD Perform LEFT$ LEFTS creates a temporary string descriptor for a new string which contains the number of characters from the left side of the string that is specified in the command. 46892 $B72C RIGHTD Perform RIGHTS RIGHTS manipulates its parameters so that the tail end of LEFTS can be used to create a temporary string descriptor for a new string. This new string contains the number of characters from the right side of the string that is specified in the command. 46903 $B737 MIDD Perform MID$ MIDS manipulates its parameters so that the tail end of LEFTS can be used to create a temporary string descriptor for a new string. This new string contains the number of characters from the position in the middle of the string that is specified in the command. 46945 $B761 PREAM Pull string Function Parameters from Stack for LEFTS, RIGHTS, and MIDS This routine is used to obtain the first two parameters for all three of these commands. 46972 $B77C LEN Perform LEN The LEN function is performed by obtaining the string length from the descriptor and converting it to a floating point number. 46987 $B78B ASC Perform ASC This routine gets the first character of the string in the .Y register (if it's not a null string). Then it calls the part of POS that converts a one-byte integer in .Y to a floating point number. 110
indirizzo_memoria_decimale: 46828
indirizzo_memoria_hex: $B6EC
man: Page 124

---
