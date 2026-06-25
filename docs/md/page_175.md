# Memory Page 175

nome: ISVAR
descrizione: Get the Value of a Variable U U u 44967 $AFA7 ISFUN \ , Dispatch and Evaluate a Function ' — ' If a BASIC function (like ASC("A")) is part of an expression, this routine will use the function dispatch table at 42242 ($A502) to set up the address of the proper function routine, and then branch to that routine. 45030 $AFE6 OROP Perform OR The OR routine sets the .Y register as a flag, and falls through to the AND routine, which also performs OR. 45033 $AFE9 ANDOP Perform AND The AND routine changes the parameters to two-byte integer values, and performs the appropriate logical operation (AND or OR). A result of 0 signifies false, while a result of -1 signifies true. 45078 $B016 DOREl Perform Comparisons This routine does the greater than (>), less than (
indirizzo_memoria_decimale: 44843
indirizzo_memoria_hex: $AF2B
man: Page 118

---
