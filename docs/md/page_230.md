# Memory Page 230

nome: UNKNOWN
descrizione: Test for Quote Marks This subroutine checks if the current character is a quotation mark, and if it is, toggles the quote switch at 212 ($D4). 59025 $E691 Add a Character to the Screen This is part of the routine that outputs a character to the screen. It puts printable characters into screen memory. 59048 $E6A8 Return from Outputting a Character to the Screen This is the common exit point for the screen portion of the CHROUT routine. 59062 $E6B6 Advance the Cursor This routine advances the cursor, and provides for such things as scrolling at the end of the screen, and inserting a blank line in order to add another physical line to the current logical line. 59137 $E701 Move Cursor Back over a 40-Colunui Line Boundary 59158 $E716 Output to the Screen This is the main entry point for the part of CHROUT that handles output to the screen device. It takes the ASCII character number, and tests if the character is printable. If it is, it prints it (taking into consideration the reverse flag, if any inserts are left, etc.). If it is a nonprinting character, the routine performs the appropriate cursor movement, color change, screen clearing, or whatever else might be indicated. 59516 $E87C Move Cursor to Next Line This subroutine moves the cursor down to the next line if possible, or scrolls the screen if the cursor is on the last line. 59537 $E891 Output a Carriage Return A carriage return is performed by clearing insert mode, reverse video, and quote mode, and moving the cursor to the next line.
indirizzo_memoria_decimale: 59012
indirizzo_memoria_hex: $E684
man: Page 231

---
