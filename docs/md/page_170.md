# Memory Page 170

nome: UNKNOWN
descrizione: O PRINT Perform PRINT The PRINT routine has many segments, which are required for the various options which can be added to it: TAB, SPC, comma, semicolon, variables, PI, ST, TI, and TI$. Eventually, all output is converted to strings, and the Kemal CHROUT routine is called to print each character. 43806 $AB1E STROUT Print Message from a String Whose Address Is in the .Y and .A Registers This part of the PRINT routine outputs a string whose address is in the Accumulator (low byte) and .Y register (high byte), and which ends in a zero byte. 43853 $AB4D DOAGIN Error Message Formatting Routines for GET, INPUT, and READ 43899 $AB7B GET Perform GET and GET# The GET routine first makes sure that the program is not in direct mode. It opens an input channel using the Kemal CHKIN routine (61966, $F20E) if a number sign was added to make GET#. Then it calls the common I/O routines in READ to get a single character, and causes the input channel to be closed if one was opened. 43941 $ABA5 INPUTN Perform INPUT* This routine opens an input channel with the Kemal CHKIN routine, calls INPUT, and then closes the channel with a CHKOUT routine (62032, $F250). Extra data is discarded without an EXTRA IGNORED message, and a FILE DATA ERROR message is issued when the data type is not suitable for the type of variable used. 43967 $ABBF INPUT Perform INPUT The INPUT routine checks to make sure that direct mode is not active, prints prompts, receives a line of input from the device, and jumps to the common code in READ that assigns the input to the variables which were named. 44038 $AC06 READ Perform READ This routine includes the READ command and common code for
indirizzo_memoria_decimale: 43680
indirizzo_memoria_hex: $AAA
man: Page 115

---
