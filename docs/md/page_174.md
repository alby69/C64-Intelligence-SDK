# Memory Page 174

nome: EVAL
descrizione: Convert a Single Numeric Term from ASCII Text to a Floating Point Number This routine reduces a single arithmetic term which is part of an expression from ASCII text to its floating point equivalent. If the term is a constant, the routine sets the data type flag to number, sets the text pointer to the first ASCII numeric character, and jumps to the routine which converts the ASCII string to a floating point number. If the term is a variable, the variable value is retrieved. If it is the PI character, the value of PI is moved into the Floating Point Accumulator. This routine is vectored through RAM at 778 ($30A). 44712 $AEA8 PIVAL PI Expressed as a Five-Byte Floating Point Number The value of PI is stored here as a five-byte floating point number. 44785 $AEF1 PARCHK Evaluate Expression Within Parentheses This routine evaluates an expression within parentheses by calling the S3mtax checking routines that look for opening and closing parentheses, and then calling FRMEVL 44446 ($AD9E) for each level of parentheses. 44791 $AEF7 CHKCLS Check for and Skip Closing Parentheses 44794 $AEFA CHKOPN Check for and Skip Opening Parentheses 44799 $AEFF CHKCOM Check for and Skip Comma This syntax checking device is the same in substance as the two checking routines above. It is used when the next character should rn be a comma. If it is not, a SYNTAX ERROR results. If it is, the char1 \ acter is skipped and the next character is read. Any character can be checked for and skipped this way by loading the character into the Accumulator and entering this routine from SYNCHR at 44799 n ($AEFF). 44808 $AF08 SNERR I I Print Syntax Error Message n 103
indirizzo_memoria_decimale: 44675
indirizzo_memoria_hex: $AE83
man: Page 117

---
