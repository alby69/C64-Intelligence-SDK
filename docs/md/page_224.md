# Memory Page 224

nome: UNKNOWN
descrizione: Continuation of EXP Routine This routine is split, with part on the BASIC ROM and the other part here. Since the two ROMs do not occupy contiguous memory as on most Commodore machines, the BASIC ROM ends with a JMP $E000 instmction. Thus, while the BASIC interpreter on the 64 is for the most part the same as on the VIC, the addresses for routines in this ROM are displaced by three bytes from their location on the VIC. 57411 $E043 POLYl Function Series Evaluation Subroutine 1 This routine is used to evaluate more complex expressions, and calls the following routine to do the intermediate evaluatiion. 206
indirizzo_memoria_decimale: 57344
indirizzo_memoria_hex: $E000
man: Page 220

---

nome: POLY2
descrizione: Function Series Evaluation Subroutine 2 This is the main series evaluation routine, which evaluates expressions by using a table of the various values that must be operated on in sequence to obtain the proper result. 57485 $E08D RMULC Multiplicative Constant for RND A five-byte floating point number which is multiplied by the seed value as part of the process of obtaining the next value for RND. 57490 $E092 RADDC Additive Constant for RND The five-byte floating point number stored here is added to the seed as part of the process of obtaining the value for RND. 57495 $E097 RND Perform RND This routine comes up with a random number in one of three ways, depending on the argument X of RND(X). If the argument is positive, the next RND value is obtained by multiplying the seed value in location 139 ($8B) by one of the constants above, adding the other constant, and scrambling the resulting bytes. This produces the next number in a sequence. So many numbers can be produced in this way before the sequence begins to repeat that it can be considered random. If the argument is negative, the argument itself is scrambled, and made the new seed. This allows creation of a sequence that can be duplicated. If the argument is 0, four bytes of the Floating Point Accumulator are loaded from the low and high byte of Timer A, and the tenths of second and second Time of Day Clock registers, all on CIA #1. This provides a somewhat random value determined by the setting of those timers at the moment that the command is executed, which becomes the new seed value. The RND(l) command should then be used to generate further random numbers. The RND(O) implementation on the 64 has serious problems which make it unsuitable for generating a series of random numbers when used by itself. First of etfi, the Time of Day Clock on CIA #1 (see 56328-56331, $DC08-$DC0B) does not start running until you write to the tenth of second register. The Operating System never starts this clock, and therefore the two registers used as part of the floating point RND(O) value always have a value of 0. Even if the dock was started, however, these registers keep time in Binary Coded Decimal (BCD) format, which means that they do not produce a full 207
indirizzo_memoria_decimale: 57433
indirizzo_memoria_hex: $E059
man: Page 221

---

nome: UNKNOWN
descrizione: Call Kernal I/O Routines This section is used when BASIC wants to call the Kernal I/O routines CHROUT, CHRIN, CHKOUT, CHKIN, and GETIN. It handles any errors that result from the call, and creates a 512-byte buffer space at the top of BASIC and executes a CLR if the RS-232 device is opened. 57642 $E12A SYS Perform SYS Before executing the machine language subroutine (JSR) at the address indicated, the .A, .X, .Y, and .P registers are loaded from the storage area at 780-783 ($30C-$30F). After the return from subroutine (RTS), the new values of those registers are stored back at 780783 ($30C-$30F). 57686 $E156 SAVE Perform SAVE This routine sets the range of addresses to be saved from the start of BASIC program text and end of BASIC program text pointers at 43 ($2B) and 45 ($2D), and calls the Kernal SAVE routine. This means that any area of memory can be saved by altering these two pointers to point to the starting and ending address of the desired area, and then changing them back. 57701 $E165 VERIFY Perform VERIFY This routine sets the load/verify flag at 10 ($A), and falls through to the LOAD routine. 57704 $E168 LOAD Perform LOAD This routine sets the load address to the start of BASIC (from pointer at 43, $2B), and calls the Kernal LOAD routine. If the load is successful, it relinks the BASIC program so that the links agree with the address to which it is loaded, and it resets the end of BASIC pointer to reflect the new end of program text. If the LOAD was done while a program was running, the pointers are reset so that the program starts executing all over again from the beginning. A CLR is not performed, so that the variables built so far are retained, and their 208
indirizzo_memoria_decimale: 57593
indirizzo_memoria_hex: $E0F9
man: Page 222

---
