# Memory Page 184

nome: FUWAIT
descrizione: Perform WAIT WAIT gets an address parameter and an integer parameter to use as a mask. WAIT then looks for an optional parameter to use as a pattern for the exclusive OR. Then, the address location is read, its value is exclusive ORed with the optional pattern value (or 0 if there is none). This value is ANDed with the mask value. The command loops continuously until the result is not-zero. The purpose of this command is to allow the program to watch a location which can be changed by the system or by outside hardware (such as the software clock or keycode value locations). The AND function lets you check if a bit changes from 0 to 1, while the EOR function allows you to check if a bit changes from 1 to 0. For more information see the article "All About the Wait Instruction," by Louis Sander and Doug Ferguson, in COMPUTEl's First Book of Commodore 64. 47177 $B849 FADDH Add .5 to Contents of Floating Point Accumulator #1 47184 $B850 FSUB Subtract FACl from a Number in Memory This routine is used to subtract the Floating Point Accumulator from a number in memory. It moves the number in memory into FAC2, and falls through to the next routine. 47187 $B853 FSUBT BASIC'S Subtraction Operation This routine subtracts the contents of FAC2 from FACl by complementing its sign and adding. 47207 $B867 FADD Add FACl to a Number in Memory This routine is used to add the contents of the Floating Point Accumulator (FACl) to a number in memory, by moving that number into FAC2, and falling through to the next routine. 47210 $B86A FADDT Perform BASIC'S Addition Operation This routine adds the contents of FACl and FAC2 and stores the results in FACl. 47271 $B8il7 FADD4 Make the Result Negative If a Borrow Was Done 112
indirizzo_memoria_decimale: 47149
indirizzo_memoria_hex: $B82D
man: Page 126

---

nome: NORMAL
descrizione: Normalize Floating Point Accumulator #1 47431 $B947 NEGFAC Replace FACl with Its 2's Complement 47486 $B97E OVERR Print Overflow Error Message 47491 $B983 MULSHF SHIFT Routine 47548 $B9BC FONE Floating Point Constant with a Value of 1 The five-byte floating point representation of the number 1 is stored here for use by the floating point routines. It is also used as the default STEP value for the FOR statement. 47553 $B9C1 LOGCN2 Table of Floating Point Constants for the LOG function This table of eight numeric constants in five-byte floating point representation is used by the LOG function. 47594 $B9EA LOG Perform LOG to Base E The LOG to the base e of the number in FACl is performed here, and the result left in FACl. 47656 $BA28 FMULT Multiply FACl by Value in Memory This routine is used to multiply the Floating Point Accumulator (FACl) by a number in memory. It moves the number in memory into FAC2, and falls through to the next routine. 47667 $BA33 FMULT Multiply FACl with FAC2 This routine multiplies the contents of FACl by the contents of FAC2 and stores the result in FACl. 47705 $BA59 MLTPLY Multiply a Byte Subroutine This subroutine is used to repetitively add a mantissa byte of FAC2 to FACl the number of times specified in the .A register.
indirizzo_memoria_decimale: 47358
indirizzo_memoria_hex: $B8FE
man: Page 127

---
