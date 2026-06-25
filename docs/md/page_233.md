# Memory Page 233

nome: UNKNOWN
descrizione: Move Screen Line This subroutine is used by the scroll routine to move one screen line (and its associated Color RAM) up a line. 59872 $E9E0 Set Temporary Color Pointer for Scrolling This subroutine sets up a pointer in 174-175 ($AE-$AF) to the Color RAM address that corresponds to the temporary screen line address in 172-173 ($AC-$AD). 59888 $E9F0 Set Pointer to Screen Address of Start of Line This subroutine puts the address of the first byte of the screen line designated by the .X register into locations 209-210 ($D1-$D2). 59903 $E9FF Clear Screen Line This subroutine writes space characters to an entire line of screen memory, and clears the corresponding line of color memory to color in Background Color Register 0 (53281, $D021). 59923 $EA13 Set Cursor Blink Timing and Color Memory Address for Print to Screen This subroutine sets the cursor blink countdown and sets the pointer to Color RAM. It then falls through to the next routine. 59932 $EA1C Store to Screen This routine stores the character in the .A register to the screen address pointed to by 209 ($D1), and stores the color in the .X register to the address pointed to by 243 ($F3). 59940 $EA24 Synchronize Color RAM Pointer to Screen Line Pointer This subroutine sets the pointer at 243 ($F3) to the address of the beginning of the line of Color RAM which corresponds to the current line of screen RAM (whose pointer is at 209, $D1). 59953 $EA31 IRQ Interrupt Entry This is the entry point to the standard IRQ interrupt handler. Timer A of CIA #1 is set at power-on to cause an IRQ interrupt to occur 219
indirizzo_memoria_decimale: 59848
indirizzo_memoria_hex: $E9C8
man: Page 233

---
