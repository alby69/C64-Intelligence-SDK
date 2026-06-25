# Memory Page 188

nome: INT
descrizione: Perform INT This routine removes the fractional part of a floating point number by calling the routine above to change it to an integer, and then changing the integer back to floating point format. 48371 $BCF3 FIN Convert an ASCII String to a Floating Point Number FACl This routine is called by VAL to evaluate and convert an ASCII string to a floating point number. 48510 $BD7E FINLOG Add Signed Integer to FACl This routine is used to add an ASCII digit that has been converted to a signed integer to FACl. 48563 $BDB3 N0999 This table of three floating point constants holds the values 99,999,999.9, 999,999,999.5 and 1,000,000,000. These values are used in converting strings to floating point numbers. 48576 $BDCO INPRT Print IN Followed by a Line Number 48589 $BDCD LINPRT Output a Number in ASCII Decimal Digits This routine is used to output the line number for the routine above. It converts the number whose high byte is in .A and whose low byte is in .X to a floating point number. It also calls the routine below, which converts the floating point number to an ASCII string. 48605 $BDDD FOUT Convert Contents of FACl to ASCII String This routine converts a floating point number to a string of ASCII digits, and sets a pointer to the string in .A and .Y. 48913 $BF11 FHALF The Constant Value 1/2 in Five-Byte Floating Point Notation This constant is used for rounding and SQR. 48924 $BF1C FOUTBL Powers of Minus Ten Constants Table This table contains the powers of -10 expressed as four-byte floating point numbers (that is, -1; +10; -100; +1000; -10,000; +100,000; -1,000,000; +10,000,000; and -100,000,000). 116
indirizzo_memoria_decimale: 48332
indirizzo_memoria_hex: $BCCC
man: Page 130

---
