# Memory Page 226

nome: UNKNOWN
descrizione: Check for Comma This subroutine checks for a comma, moves the text pointer past it if found, and returns an error if it is not found. 57881 $E219 Set Parameters for OPEN and CLOSE This routine is used in common by OPEN and CLOSE for setting the filename, the logical file, device number, and secondary address, all of which must be done prior to these operations. 57956 $E264 COS Perform COS COS is executed by adding PI/2 to the contents of FACl and dropping through to SIN. 57963 $E26B SIN Perform SIN This routine evaluates the SIN of the number in FACl (which represents the angle in radians), and leaves the result there. 58036 $E2B4 TAN Perform TAN This routine evaluates the tangent of the number in FACl (which represents the angle in radians) by dividing its sine by its cosine. Location Range: 58080-58125 ($E2E0$E30D) Table of Constants for Evaluation of SIN, COS, and TAN 58080 $E2E0 PI2 The Five-Byte Floating Point Representation of the Constant PI/2 58085 $E2E5 TWOPI The Five-Byte Floating Point Representation of the Constant 2*PI 58090 $E2EiV FR4 The Five-Byte Floating Point Representation of the Constant 1/4 58095 $E2EF SINCON Table of Constants for Evaluation of SIN, COS, and TAN This table starts with a counter byte of 5, indicating that there are sbc entries in the table. This is followed by the sbc floating point constants of five bytes each. 210
indirizzo_memoria_decimale: 57870
indirizzo_memoria_hex: $E20E
man: Page 224

---
