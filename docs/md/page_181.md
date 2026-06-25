# Memory Page 181

nome: UNKNOWN
descrizione: Check for Most Eligible String to Collect This part of the garbage collection routine checks to see if the current string is the highest in memory. 46598 $B606 Collect a String This part of the garbage collection routine moves the string to high memory and updates the descriptor to point to its new location. 46653 $B63D CAT Concatenate Two Strings This routine is used to add the text of one string onto the end of another (A$-l-B$). Error checking is done to see if the length of the combined string is within range, the allocation routine is called to allocate space, and the new string is built at the bottom of the string text area. 46714 $B67A MOVINS Move a String In Memory This is the routine which is used to move a string to the bottom of the string text area for the above routine. It is generally used as a utility routine to move strings. n 46755 $B6A3 FRESTR Discard a Temporary String /— ) This routine calls the following routine which clears an entry from I 1 the temporary descriptor stack. If the descriptor was on the stack, it exits after setting pointers to the string and its length. If it wasn't on ^ the temporary stack and is at the bottom of string text storage, the j \ pointer to the bottom is moved up to deallocate the string. 46811 $B6DB FRETMS Remove an Entry from the String Descriptor Stack - - If the descriptor of a currently valid string is the same as one of the entries on the temporary string descriptor stack, the stack entry is removed. n 109
indirizzo_memoria_decimale: 46525
indirizzo_memoria_hex: $B5BD
man: Page 123

---
