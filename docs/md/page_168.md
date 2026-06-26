# Memory Page 168

nome: GOSUB
descrizione: Perform GOSUB This statement pushes the pointers to the current text character and current line onto the stack, along with a constant 141 ($8D) which identifies the block as saved GOSUB information to be used by RETURN. The GOTO is called. 43168 $A8A0 GOTO Perform GOTO This statement scans BASIC for the target line number (the scan starts with the current line if the target line number is higher, otherwise it starts with the first line). When the line is found, the pointers to the current statement and text character are changed, so that the target statement will be executed next. 43218 $A8D2 RETURN Perform RETURN The RETURN statement finds the saved GOSUB data on the stack, and uses it to restore the pointers to the current line and current character. This will cause execution to continue where it left off when GOSUB was executed. 43256 $A8F8 DATA Perform DATA DATA uses the next subroutine to find the offset to the next statement, and adds the offset to the current pointers so that the next statement will be executed. In effect, it skips the statement, much like REM. 43270 $A906 DATAN Search Program Text for the End of the Current BASIC Statement This routine starts at the current byte of program text and searches until it finds a zero character (line delimiter) or a colon character that is not in quotes (statement delimiter). 43304 $A928 IF Perform IF IF uses the FRMEVL routine at 44446 ($AD9E) to reduce the expression which follows to a single term. If the expression evaluates to 0 (false), the routine falls through to REM. If it is not 0, GOTO or the statement following THEN is executed. 99
indirizzo_memoria_decimale: 43139
indirizzo_memoria_hex: $A883
man: Page 113

---
