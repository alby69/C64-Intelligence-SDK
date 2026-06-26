# Memory Page 160

nome: UNKNOWN
descrizione: Cold Start Vector This vector points to the address of the routine used to initialize BASIC. After the Operating System finishes its power-on activities, it enters the BASIC program through this vector. The most visible effect of the BASIC initialization routine is that the screen is cleared, and the words COMMODORE 64 BASIC V2 **** are printed along with the BYTES FREE message. For details of the steps taken during the initialization of BASIC, see the entry for 58260 ($E394), the current cold start entry point. 40962-40963 $A002-$A003 Warm Start Vector The warm start vector points to the address of the routine used to reset BASIC after the STOP/RESTORE key combination is pressed. This is the same address to which the BRK instruction is vectored. 88
indirizzo_memoria_decimale: 40960-40961
indirizzo_memoria_hex: $A000-$A001
man: Page 102

---

nome: STMDSP
descrizione: Statement Dispatch Vector Table This table contains two-byte vectors, each of which points to an address which is one byte before the address of one of the routines that perform a BASIC statement. The statements are in token number order. When it comes time to execute a statement, the NEWSTT routine at 42926 ($A7AE) places this address-1 on the stack and jumps to the CHRGET routine. The RTS instruction at the end of that routine causes the statement address to be pulled off the stack, incremented, and placed in the Program Counter, just as if it were the actual return address. This table is handy for locating the address of the routine that performs a BASIC statement, so that the routine can be disassembled and examined. To aid in this purpose, the table is reproduced below with the actual target addresses, and not in the address-1 format used by BASIC. Token # Statement Routine Address 128 $80 END 43057 $A831 129 $81 FOR 42818 $A742 130 $82 NEXT 44318 $AD1E 131 $83 DATA 43256 $A8F8 132 $84 INPUT* 43941 $ABA5 133 $85 INPUT 43967 $ABBF 134 $86 DIM 45185 $B081 135 $87 READ 44038 $AC06 136 $88 LET 43429 $A9A5 137 $89 GOTO 43168 $A8A0 138 $8A RUN 43121 $A871 139 $8B IF 43304 $A928 140 $8C RESTORE 43037 $A8D 141 $8D GOSUB 43139 $A883 142 $8E RETURN 43218 $A8D2 143 $8F REM 43323 $A93B 144 $90 STOP 43055 $A82F 145 $92 ON 43339 $A94B 89
indirizzo_memoria_decimale: 40972-41041
indirizzo_memoria_hex: $A00C-$A051
man: Page 103

---
