# Memory Page 225

nome: OPEN
descrizione: Perform OPEN The BASIC OPEN statement calls the Kemal OPEN routine. 57799 $E1C7 CLOSE Perform CLOSE The BASIC CLOSE statement calls the Kemal CLOSE routine. 57812 $E1D4 Set Parameters for LOAD, VERIFY, and SAVE This routine is used in common by LOAD, SAVE, and VERIFY for setting the filename, the logical file, device number, and secondary address, all of which must be done prior to these operations. 57856 $E200 Skip Comma and Get Integer in .X This subroutine is used to skip the comma between parameters and get the following integer value in the .X register. 57862 $E206 Fetch Current Character and Check for End of Line This subroutine gets the current character, and if it is a 0 (end of line), it pulls its own return address off the stack and returns. This terminates both its own execution and that of the subroutine which called it.
indirizzo_memoria_decimale: 57790
indirizzo_memoria_hex: $E1BE
man: Page 223

---
