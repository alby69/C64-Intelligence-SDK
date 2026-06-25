"""C64 ZERO_PAGE Registers"""

# Flag: Subscript Reference to an Array or User-Defined Function Call (FN) This flag is used by the PTRGET routine which finds or creates a variable, at the time it checks whether the name of a variable is valid. If an opening parenthesis is found, this flag is set to indicate that the variable in question is either an array variable or a userdefined function. You should note that it is perfectly legal for a user-defined function (FN) to have the same name as a floating point variable. Moreover, it is also legal to redefine a function. Using a FN name in an already defined function results in the new definition of the function. 10
# Address: $10 (16)
SUBFLG = 16
def set_subflg(val: byte):
    poke(16, val)

def get_subflg() -> byte:
    return peek(16)

# Flag: Is Data Input to GET, READ or INPUT? Since the keywords GET, INPUT, and READ perform similar functions, BASIC executes some of the same instructions for all three. There are also many areas of difference, however, and this flag indicates which of the three keywords is currently being executed, so that BASIC will know whether or not to execute the instructions which relate to the areas in which the commands differ (152 ($98)=READ, 64 ($40)= GET 0=INPUT). As a result, INPUT will show the ? prompt, will echo characters back to the screen, and will wait for a whole line of text ended by a carriage return. GET gives no prompt and accepts one character without waiting. The colon character and the comma are valid data for GET, but are treated as delimiters between data by INPUT and READ. As each command has its own error messages, this flag is used to determine the appropriate message to issue in case of an error. 18 $12 TANSGN Flag: Sign of the Result of the TAN or SIN Function This location is used to determine whether the sign of the value returned by the functions SIN or TAN is positive or negative. Additionally, the string and numeric comparison routines use this location to indicate the outcome of the comparison. For a comparison of variable A to variable B, the value here will be 1 if A is greater than B, 2 if A equals B, and 4 if A is less than B. If more than one comparison operator was used to compare the two variables (e.g., >= or <= ), the value here will be a combination of the above values. 19 $13 CHANNL Current I/O Channel (CMD Logical File) Number Whenever BASIC inputs or outputs data, it looks here to determine which I/O device is currently active for the purpose of prompting or output control. It uses location 184, $B8 for purposes of deciding what device actually to input from or output to. When the default input device (number 0, the keyboard) or output device (number 3, the display screen) is used, the value here will be a zero, and the format of prompting and output will be the standard screen output format. When another device is used, the logical file number (CMD channel number) will be placed here. This lets the system know that it may have to make some subtle changes in the way it performs the I/O operation. For example, if TAB is used with the PRINT command, cursor right characters are used if the device PRINTed to is the screen. Otherwise, spaces are output when the number here is
# Address: $11 (17)
INPFLG = 17
def set_inpflg(val: byte):
    poke(17, val)

def get_inpflg() -> byte:
    return peek(17)

# Pointer to the Next Available Space in the Temporary String Stack This location points to the next available slot in the temporary string descriptor stack located at 25-33 ($19-$21). Since that stack has room for three descriptors of three bytes each, this location will point to 25 r— ) ($19) if the stack is empty, to 28 ($1C) if there is one entry, to 31 ' 1 ($1F) if there are two entries, and to 34 ($22) if the stack is full. If BASIC needs to add an entry to the temporary string descriptor stack, and this location holds a 34, indicating that the stack is full, the FORMULA TOO COMPLEX error message is issued. Otherwise, the entry is added, and three is added to this pointer. 23-24 $17-$ 18 LASTPT Pointer to the Address of the Last String in the Temporary String Stack This pointer indicates the last slot used in the temporary string descriptor stack. Therefore, the value stored at 23 ($17) should be 3 less than that stored at 22 ($16), while 24 ($18) will contain a 0. 25-33 $19-$21 TEMPST Descriptor Stack for Temporary Strings The temporary string descriptor stack contains information about temporary strings which have not yet been assigned to a string variable. An example of such a temporary string is the literal string "HELLO" in the statement PRINT "HELLO". Each three-byte descriptor in this stack contains the length of the string, and its starting and ending locations, expressed as displacements within the BASIC storage area. 34-37 $22-$25 INDEX Miscellaneous Temporary Pointers and Save Area r~) This area is used by many BASIC routines to hold temporary pointI I ers and calculation results. 38-42 $26-$2A SESHO I { Floating Point Multiplication Work Area This location is used by BASIC multiplication and division routines. It is also used by the routines which compute the size of the area ref~| quired to store an array which is being created. 43-44 $2B-$2C TXTTAB I — j Pointer to the Start of BASIC Program Text This two-byte pointer lets BASIC know where program text is stored. Ordinarily, such text is located beginning at 2049 ($801). Using this n 13
# Address: $16 (22)
TEMPPT = 22
def set_temppt(val: byte):
    poke(22, val)

def get_temppt() -> byte:
    return peek(22)

# Pointer to the Start of the BASIC Variable Storage Area This location points to the address which marks the end of the BASIC program text area, and the beginning of the variable storage area. All nonarray variables are stored here, as are string descriptors (for the address of the area where the actual text of strings is stored, see location 51, $33). Seven bytes of memory are allocated for each variable. The first {—^ two bytes are used for the variable name, which consists of the ' I ASCII value of the first two letters of the variable name. If the variable name is a single letter, the second byte will contain a zero. The seventh bit of one or both of these bytes can be set (which would add 128 to the ASCII value of the letter). This indicates the variable type. If neither byte has the seventh bit set, the variable is the regular floating point type. If only the second byte has its seventh 1 bit set, the variable is a string. If only the first byte has its seventh bit set, the variable is a defined function (FN). If both bytes have the seventh bit set, the variable is an integer. "[ The use of the other five bytes depends on the type of variable. ' A floating point variable will use the five bytes to store the value of the variable in floating point format. An integer will have its value ■I ! 15 n
# Address: $2D (45)
VARTAB = 45
def set_vartab(val: word):
    poke16(45, val)

def get_vartab() -> word:
    return peek16(45)

# Pointer to the Start of the BASIC Array Storage Area This location points to the address of the end of nonarray variable storage, and the beginning of array variable storage. The format for array storage is as follows: The first two bytes hold the array name. The format and highbit patterns are the same as for nonarray variables (see 45, $2D above), except that there is no equivalent to the function definition. Next comes a two-byte offset to the start of the next array, low byte first. Then there is a one-byte value for the number of array dimensions (e.g., 2 for a two-dimensional array like A(x,y)). That byte is followed by pairs of bytes which hold the value of each array dimension-1-1 (DIMensioning an array always makes space for 0, so A(0) can and should be used). Finally come the values of the variables themselves. The format for these values is the same as with nonarray values, but each value only takes up the space required; that is, floating point variables use five bytes each, integers two bytes, and strings descriptors three bytes each. Remember that as with nonarray strings, the actual string text is stored elsewhere, in the area which starts at the location pointed to m 51-52 ($33-$34). 49-50 $31-$32 STREND Pointer to End of the BASIC Array Storage Area (+1), and the Start of Free RAM This location points to the address of the end of BASIC array storage
# Address: $2F (47)
ARYTAB = 47
def set_arytab(val: word):
    poke16(47, val)

def get_arytab() -> word:
    return peek16(47)

# Pointer to the Bottom of the String Text Storage Area This pointer marks the current end of the string text area, and the top of free RAM (strings are built from the top of memory downward). Additional string texts are added to the area below the address pointed to here. After they are added, this pointer is lowered to point below the newly added string text. The garbage collection routine (which is also called by FRE) readjusts this pointer upward. While the power-on/reset routines set this pointer to the top of RAM, the CLR command sets this pointer to the end of BASIC memory, as indicated in location 55 ($37). This allows the user to set aside an area of BASIC memory that will not be disturbed by the program, as detailed at location 55 ($37). 53-54 $35-$36 FRESPC Temporary Pointer for Strings This is used as a temporary pointer to the most current string added by the routines which build strings or move them in memory. 55-56 $37-$38 MEMSIZ Pointer to the Highest Address Used by BASIC The power-on/reset routine tests each byte of RAM until it comes to the BASIC ROM, and sets this pointer to the address of the highest byte of consecutive RAM found (40959, $9FFF). There are two circumstances under which this pointer may be changed after power-up to reflect an address lower than the actual top of consecutive RAM: 1. Users may wish to lower this pointer themselves, in order to set aside an area of free RAM that will not be disturbed by BASIC. For example, to set aside a IK area at the top of BASIC, start your program with the line: POKE 56, PEEK(56)-4:CLR The CLR is necessary to insure that the string text will start below your safe area. 18
# Address: $33 (51)
FRETOP = 51
def set_fretop(val: word):
    poke16(51, val)

def get_fretop() -> word:
    return peek16(51)

# Current BASIC Line Number This location contains the line number of the BASIC statement which is currently being executed, in LSB/MSB format. A value of 255 ($FF) in location 58 ($3 A), which translates to a line number of 65280 or above (well over the 63999 limit for a program line), means that BASIC is currently in immediate mode, rather than RUN mode. BASIC keywords that are illegal in direct mode check 58 ($3 A) to determine whether or not this is the current mode. When in RUN mode, this location is updated as each new BASIC line is fetched for execution. Therefore, a TRACE function could be added by diverting the vector at 776 ($308), which points to the routine that executes the next token, to a user-written routine which prints the line number indicated by this location before jumping to the token execution routine. (LISTing the line itself would be somewhat harder, because LIST uses many Page 0 locations that would have to be preserved and restored afterwards.) This line number is used by BREAK and error messages to show where program execution stopped. The value here is copied to 59 ($3B) by STOP, END and the STOP-key BREAK, and copied back by CONT. 59-60 $3B-$3C OLDLIN Previous BASIC Line Number When program execution ends, the last line number executed is stored here, and restored to location 57 ($39) by CONT. n 19
# Address: $39 (57)
CURLIN = 57
def set_curlin(val: word):
    poke16(57, val)

def get_curlin() -> word:
    return peek16(57)

# Pointer to the Address of the Current BASIC Statement This location contains the address (not the line number) of the text of the BASIC statement that is being executed. The value of TXTPTR (122, $7 A), the pointer to the address of the BASIC text character currently being scanned, is stored here each time a new BASIC line begins execution. END, STOP, and the STOP-key BREAK save the value of TXTPTR here, and CONT restores this value to TXTPTR. CONT will not continue if 62 ($3E) has been changed to a zero by a LOAD, a modification to the program text, or by error routines. 63-64 $3F-$40 DATLIN Current DATA Line Number This location holds the line number of the current DATA statement being READ. It should be noted that this information is not used to determine where the next DATA item is read from (that is the job of the pointer at 65-66 ($41-$42) below). But if an error concerning the DATA occurs, this number will be moved to 57 ($39), so that the error message will show that the error occurred in the line that contains the DATA statement, rather than in the line that contains the READ statement. 65-66 $41-$42 DATPTR Pointer to the Address of the Current DATA Item This location points to the address (not the line number) within the BASIC program text area where DATA is currently being READ. RESTORE sets this pointer back to the address indicated by the start of BASIC pointer at location 43 ($2B). The sample program below shows how the order in which DATA statements are READ can be changed using this pointer. The current address of the statement before the DATA statement is stored in a variable, and then used to change this pointer. 10 A1=PEEK (61): A2=PEEK (62) 20 DATA THIS DATA WILL BE USED SECOND 30 B1=PEEK{61) :B2=PEEK(62) 40 DATA THIS DATA WILL BE USED FIRST 50 C1=PEEK(61) :C2=PEEK(62) 60 DATA THIS DATA WILL BE USED THIRD 70 POKE 65, Bl: POKE 66, B2: READ A$: PRINT A$ 80 POKE 65,A1:P0KE 66, A2: READ A$: PRINT A$ 90 POKE 65, CI: POKE 66, C2: READ A$: PRINT A$ 20
# Address: $3D (61)
OLDTXT = 61
def set_oldtxt(val: word):
    poke16(61, val)

def get_oldtxt() -> word:
    return peek16(61)

# Pointer to the Source of GET, READ, or INPUT Information READ, INPUT, and GET all use this as a pointer to the address of the source of incoming data, such as DATA statements, or the text input buffer at 512 ($200). 69-70 $45-$46 VARNAM Current BASIC Variable Name The current variable name being searched for is stored here, in the same two-byte format as in the variable value storage area located at the address pointed to by 45 ($2D). See that location for an explanation of the format. 71-72 $47-$48 VARPNT Pointer to the Current BASIC Variable Value This location points to the address of the descriptor of the current BASIC variable (see location 45 ($2D) for the format of a variable descriptor). Specifically, it points to the byte just after the twocharacter variable name. During a FN call, this location does not point to the dependent variable (the A of FN A), so that a real variable of the same name will not have its value changed by the call. 73-74 $49-$4A FORPNT Temporary Pointer to the Index Variable Used by FOR The address of the BASIC variable which is the subject of a FOR/ NEXT loop is first stored here, but is then pushed onto the stack. That leaves this location free to be used as a work area by such statements as INPUT, GET, READ, LIST, WAIT, CLOSE, LOAD, SAVE, RETURN, and GOSUB. For a description of the stack entries made by FOR, see location 256 ($100). 75-76 $4B-$4C OPPTR Math Operator Table Displacement This location is used during the evaluation of mathematical expressions to hold the displacement of the current math operator in an operator table. It is also used as a save area for the pointer to the address of program text which is currently being read. 77 $4D OPMASK Mask for Comparison Operation The expression evaluation routine creates a mask here which lets it know whether the current comparison operation is a less-than (1), equals (2), or greater-than comparison.
# Address: $43 (67)
INPPTR = 67
def set_inpptr(val: word):
    poke16(67, val)

def get_inpptr() -> word:
    return peek16(67)

# Pointer to the Current FN Descriptor During function definition (DEF FN) this location is used as a pointer to the descriptor that is created. During function execution (FN) it points to the FN descriptor in which the evaluation results should be saved. 80-82 $50-$52 DSCPNT Temporary Pointer to the Current String Descriptor The string assignment and handling routines use the first two bytes as a temporary pointer to the current string descriptor, and the third to hold the value of the string length. 83 $53 F0UR6 Constant for Garbage Collection The constant contained here lets the garbage collection routines know whether a three- or seven-byte string descriptor is being collected. 84-86 $54-$56 JMPER Jump to Function Instruction The first byte is the 6502 JMP instruction ($4C), followed by the address of the required function taken from the table at 41042 ($A052). 87-96 $57-$60 BASIC Numeric Work Area This is a very busy work area, used by many routines. 97-102 $61-$66 FACl Floating Point Accumulator #1 The Floating Point Accumulator is central to the execution of any BASIC mathematical operation. It is used in the conversion of integers to floating point numbers, strings to floating point numbers, and vice versa. The results of most evaluations are stored in this location. The internal format of floating point numbers is not particularly easy to understand (or explain). Generally speaking, the number is broken into the normalized mantissa, which represents a number between 1 and 1.99999..., and an exponent value, which represents a power of 2. Multiplying the mantissa by 2 raised to the value of the exponent gives you the value of the floating point number. Fortunately, the BASIC interpreter contains many routines for the manipulation and conversion of floating point numbers, and these routines can be called by the user. See the entries for locations 3 and 5. Floating Point Accumulator #1 can be further divided into the following locations: 22
# Address: $4E (78)
DEFPNT = 78
def set_defpnt(val: word):
    poke16(78, val)

def get_defpnt() -> word:
    return peek16(78)

# Floating Point Accumulator #1: Exponent This exponent represents the closest power of two to the number, with 129 added to take care of the sign problem for negative exponents. An exponent of 128 is used for the value 0; an exponent of 129 represents 2 to the 0 power, or 1; an exponent of 130 represents n2 to the first power, or 2; 131 is 2 squared, or 4; 132 is 2 cubed, or 8; and so on. 98-101 $62-$65 FACHO Floating Point Accumulator #1: Mantissa The most significant digit can be assumed to be a 1 (remember that the range of the mantissa is from 1 to 1.99999...) when a floating point number is stored to a variable. The first bit is used for the sign of the number, and the other 31 bits of the four-byte mantissa hold the other significant digits. The first two bytes (98-99, $62-$63) of this location will hold the signed integer result of a floating point to integer conversion, in high-byte, low-byte order. 102 $66 FACSGN Floating Point Accumulator #1: Sign A value of 0 here indicates a positive number, while a value of 255 ($FF) indicates a negative number. 103 $67 SGNFLG Number of Terms in a Series Evaluation This location is used by mathematical formula evaluation routines. It indicates the number of separate evaluations that must be done to resolve a complex expression down to a single term. p 104 $68 BITS ' I Floating Point Accumulator #1: Overflow Digit This location contains the overflow byte. The overflow byte is used in an intermediate step of conversion from an integer or text string to a floating point number. n □ 105-110 $69-$6E FAC2 Floating Point Accumulator #2 A second Floating Point Accumulator, used in conjunction with Floating Point Accumulator #1 in the evaluation of products, sums, differences — in short, any operation requiring more than one value. The format of this accumulator is the same as FACl. 23
# Address: $61 (97)
FACEXP = 97
def set_facexp(val: byte):
    poke(97, val)

def get_facexp() -> byte:
    return peek(97)

# Floating Point Accumulator #2: Exponent 106-109 $6A-$6D ARGHO Floating Point Accumulator #2: Mantissa 110 $6E ARGSGN Floating Point Accumulator #2: Sign 111 $6F ARISGN Result of a Sign Comparison of Accumulator #1 to Accumulator #2 Used to indicate whether the two Floating Point Accumulators have like or unlike signs. A 0 indicates like signs, a 255 ($FF) indicates unlike signs. 112 $70 FACOV Low Order Mantissa Byte of Floating Point Accumulator #1 (For Rounding) If the mantissa of the floating point number has more significant figures than can be held in four bytes, the least significant figures are placed here. They are used to extend the accuracy of intermediate mathematical operations and to round the final figure. 113-114 $71-$72 FBUFPT Series Evaluation Pointer This location points to the address of a temporary table of values built in the free RAM area for the evaluation of formulas. It is also used for such various purposes as a TI$ work area, string setup pointer, and work space for the determination of the size of an array. Although this is labeled a pointer to the tape buffer in the Programmer's Reference Guide, disassembly of the BASIC ROM reveals no reference to this location for that purpose (see 178, $B2 for pointer to tape buffer). 115-138 $73-$8A CHRGET Subroutine: Get Next BASIC Text Character This is actually a machine language subroutine, which at the time of a BASIC cold start (such as when the power is turned on) is copied from MOVCHG (58274, $E3A2) in the ROM to this zero page location. CHRGET is a crucial routine which BASIC uses to read text characters, such as the text of the BASIC program which is being interpreted. It is placed on zero page to make the routine run faster. Since it keeps track of the address of the character being read within 24
# Address: $69 (105)
ARGEXP = 105
def set_argexp(val: byte):
    poke(105, val)

def get_argexp() -> byte:
    return peek(105)

# INC TXTPTR , 117 $75 BNE CHRGOT , 119 $77 INC TXTPTR +1 ; 121 $79 CHRGOT LDA ; 122 $7A TXTPTR $0207 ; n 124 $7C POINTB CMP #$3A ; 126 $7E BCS EXIT 128 $80 CMP #$20 130 $82 BEQ CHRGET ; 132 $84 SEC 133 $85 SBC #$30 ; 135 $87 SEC ; 1—1 136 $88 SBC #$D0 ; i t 138 $8A Exrr RTS increment low byte of TXTPTR if low byte isn't 0, skip next increment high byte of TXTPTR load byte from where TXTPTR points entry here does not update TXTPTR, allowing you to read the old byte again pointer is really the LDA operand TXTPTR+1 points to 512-580 ($200$250) when reading from the input buffer in direct mode. carry flag set if >ASCn numeral 9 character is not a numeral—exit if it is an ASCII space... ignore it and get next character prepare to subtract ASCn 0-9 are between 48-57 ($30-39) prepare to subtract again if
# Address: $73 (115)
CHRGET = 115
def set_chrget(val: byte):
    poke(115, val)

def get_chrget() -> byte:
    return peek(115)

# RND Function Seed Value This location holds the five-byte floating point value returned by the RND function. It is initially set to a seed value copied from ROM (the five bytes are 128, 79, 199, 82, 88— $80, $4F, $C7, $52, $58). When the function RND(X) is called, the numeric value of X does not affect the number returned, but its sign does. If X is equal to 0, RND generates a seed value from chip-level hardware timers. If X is a positive number, RND(X) will return the next number in an arithmetic sequence. This sequence continues for such a long time without repeating itself, and gives such an even distribution of numbers, that it can be considered random. If X is negative, the seed value is changed to a number that corresponds to a scrambled floating point representation of the number X itself. Given a particular seed value, the same pseudorandom series of numbers will always be returned. This can be handy for debugging purposes, but not where you wish to have truly random numbers. The traditional Commodore method of selecting a random seed is by using the expression RND (-TI), mostly because RND(O) didn't function correctly on early PETs. While the RND(O) form doesn't really work right on the 64 either (see location 57495, $E097), the expression RND(-RND(0)) may produce a more random seed value. Location Range: 144-255 ($90-$FF) Kemal Work Storage Area This is the zero-page storage area for the Kemal. The user should take into account what effect changing a location here will have on the operation of Kemal functions before making any such changes. At power-on, this range of locations is first filled with zeros, and then initialized from values stored in ROM as needed. 26
# Address: $8B (139)
RNDX = 139
def set_rndx(val: byte):
    poke(139, val)

def get_rndx() -> byte:
    return peek(139)

# Kernal I/O Status Word (ST) The Kernal routines which open I/O channels or perform input/output functions check and update this location. The value here is almost always the same as that returned to BASIC by use of the reserved variable ST. Note that BASIC syntax will not allow an assignment such as ST =4. A table of status codes for cassette and serial devices follows below. Cassette: Bit 2 (Bit Value of 4) = Short Block Bit 3 (Bit Value of 8) = Long Block Bit 4 (Bit Value of 16) = Unrecoverable error (Read), mismatch Bit 5 (Bit Value of 32) = Checksum error Bit 6 (Bit Value of 64) = End of file Bit 7 (Bit Value of 128) = End of tape Serial Devices: Bit 0 (Bit Value of 1) = Time out (Write) Bit 1 (Bit Value of 2) = Time out (Read) Bit 6 (Bit Value of 64) = EOI (End or Identify) Bit 7 (Bit Value of 128) = Device not present Probably the most useful bit to test is Bit 6 (end of file). When using the GET statement to read in individual bytes from a file, the statement IF ST AND 64 will be true if you have got to the end of the file. For status codes for the RS-232 device, see the entry for location 663 ($297). 145 $91 STKEY Flag: Was STOP Key Pressed? This location is updated every 1/60 second during the execution of the IRQ routine that reads the keyboard and updates the jiffy clock. The value of the last row of the keyboard matrix is placed here. That row contains the STOP key, and although this location is used primarily to detect when that key has been pressed, it can also detect when any of the other keys in that row of the matrix have been pressed. In reading the keyboard matrix, a bit set to 1 means that no key has been pressed, while a, bit reset to 0 indicates that a key is pressed. Therefore, the following values indicate the keystrokes detailed below: 255 $FF = no key pressed 254 $FE = 1 key pressed 253 $FD = «- key pressed 251 $FB = CTRL key pressed 27
# Address: $90 (144)
STATUS = 144
def set_status(val: byte):
    poke(144, val)

def get_status() -> byte:
    return peek(144)

# 47149 $B82D 147 $93 LOAD 57704 $E168 148 $94 SAVE 57686 $E156 149 $95 VERIFY 57701 $E165 150 $96 DEF 46003 $B3B3 151 $97 POKE 47140 $B824 152 $98 PRINT* 43648 $AA80 153 $99 PRINT 43680 $AAAO 154 $9A CONT 43095 $A857 155 $9B LIST 42652 $A69C 156 $9C CLR 42590 $A65E 157 $9D CMD 43654 $AA86 158 $9E SYS 57642 $E12A 159 $9F OPEN 57790 $E1BE 160 $A0 CLOSE 57799 $E1C7 161 $A1 GET 43899 $AB7B 162 $A2 NEW 42562 $A642 41042-41087 $A052-$A07F FUNDSP TABLE Function Dispatch Vector Table This table contains two-byte vectors, each of which points to the address of one of the routines that perform a BASIC function. A function is distinguished by a following argument, in parentheses. The expression in the parentheses is first evaluated by the routines which begin at 44446 ($AD9E). Then this table is used to find the address of the function that corresponds to the token number of the function to be executed. The substance of this table, which can be used for locating the addresses of these routines, is reproduced below. Note that the address for the USR function is 784 ($310), which is the address of the JMP instruction which precedes the user-supplied vector. Token # Function Routine Address 180 $B4 SGN 48185 $BC39 181 $B5 INT 48332 $BCCC 182 $B6 ABS 48216 $BC58 183 $B7 USR 784 $0310 184 $B8 FRE 45949 $B37D 185 $B9 POS 45982 $B39E 186 $BA SQR 49009 $BF71 187 $BB RND 57495 $E097 188 $BC LOG 47594 $B9EA 189 $BD EXP 49133 $BFED 190 $BE COS 57956 $E264 90
# Address: $92 (146)
WAIT = 146
def set_wait(val: byte):
    poke(146, val)

def get_wait() -> byte:
    return peek(146)

# Number of Open I/O Files/Index to the End of File Tables The number of currently open I/O files is stored here. The maxiI \ mum number that can be open at one time is ten. The number stored here is used as the index to the end of the tables that hold the file numbers, device numbers, and secondary address numbers (see locations 601-631, $259-$277, for more information about these tables). CLOSE decreases this number and removes entries from the tables referred to above, while OPEN increases it and adds the appropriate information to the end of the tables. The Kemal routine CLALL closes all files by setting this number to 0, which effrectively empties the tables. 153 $99 DFLTN Default Input Device (Set to 0 for the Keyboard) The default value of this location is 0, which designates the keyboard as the current input device. That value can be changed by the Kemal routine CHBQN (61966, $F20E), which uses this location to store the device number of the device whose file it defines as an input channel. BASIC calls CHKIN whenever the command INPUT# or GET# is executed, but clears the channel after the input operation has been completed. 154 $9A DFLTO Default Output (CMD) Device (Set to 3 for the Screen) The default value of this location is 3, which designates the screen as the current output device. That value can be changed by the Kemal routine CHKOUT (62032, $F250), which uses this location to store the device number of the device whose file it defines as an output channel. BASIC calls CHKOUT whenever the command PRINT# or CMD is executed, but clears the channel after the PRINT* operation has been completed. n 155 $9B PRTY Tape Character Parity This location is used to help detect when bits of information have been lost during transmission of tape data. n 29
# Address: $98 (152)
LDTND = 152
def set_ldtnd(val: byte):
    poke(152, val)

def get_ldtnd() -> byte:
    return peek(152)

# Flag: Tape Byte Received This location is used as a flag to indicate whether a complete byte of tape data has been received, or whether it has only been partially received. 157 $9D MSGFLG Flag: Kernal Message Control This flag is set by the Kernal routine SETMSG (65048, $FE18), and it controls whether or not Kernal error messages or control messages will be displayed. A value of 192 ($C0) here means that both Kernal error and control messages will be displayed. This will never normally occur when using BASIC, which prefers its own plain text error messages over the Kemal's perfunctory I/O ERROR (number). The Kernal error messages might be used, however, when you are SAVEing or LOADing with a machine language monitor. A 128 ($80) means that control messages only will be displayed. Such will be the case when you are in the BASIC direct or immediate mode. These messages include SEARCHING, SAVING, FOUND, etc. A value of 64 means that Kernal error messages only are on. A 0 here suppresses the display of all Kernal messages. This is the value placed here when BASIC enters the program or RUN mode. 158 $9E PTRl Tape Pass 1 Error Log Index This location is used in setting up an error log of bytes in which transmission parity errors occur the first time that the block is received (each tape block is sent twice to minimize data loss from transmission error). 159 $9F PTR2 Tape Pass 2 Error Log Correction Index This location is used in correcting bytes of tape data which were transmitted incorrectly on the first pass. 160-162 $A0-$A2 TIME Software Jiffy Clock These three locations are updated 60 times a second, and serve as a software clock which counts the number of jiffies (sixtieths of a second) that have elapsed since the computer was turned on. The value of location 162 ($A2) is increased every jiffy (.01667 second), 161 ($A1) is updated every 256 jiffies (4.2267 seconds), and 160 ($A0) changes every 65536 jiffies (or every 18.2044 minutes). 30
# Address: $9C (156)
DPSW = 156
def set_dpsw(val: byte):
    poke(156, val)

def get_dpsw() -> byte:
    return peek(156)

# RS-232 Input Bit Count/Cassette Temporary Storage This location is used to count the number of bits of serial data that has been received. This is necessary so that the serial routines will know when a full word has been received. It is also used as an error flag during tape loads. 169 $A9 RINONE RS-232 Flag: Check for Start Bit This flag is used when checking for a start bit. A 144 ($90) here indicates that no start bit was received, while a 0 means that a start bit was received. 170 $AA SIDATA RS-232 Input Byte Buffer/Cassette Temporary Storage Serial routines use this area to reassemble the bits received into a byte that will be stored in the receiving buffer pointed to by 247 ($F7). Tape routines use this as a flag to help determine whether a received character should be treated as data or as a S5mchronization character. 171 $AB RIPRTY RS-232 Input Parity/Cassette Leader Counter This location is used to help detect if data was lost during RS-232 transmission, or if a tape leader is completed. 172-173 $AC-$AD SAL Pointer to the Starting Address of a Load/Screen Scrolling The pointer to the start of the RAM area to be SAVEd or LOADed at 193 ($C1) is copied here. This pointer is used as a working version, to be increased as the data is received or transmitted. At the end of the operation, the initial value is restored here. Screen management routines temporarily use this as a work pointer. 174-175 $AE-$AF EAL Pointer to Ending Address of Load (End of Program) This location is set by the Kemal routine SAVE to point to the ending address for SAVE, LOAD, or VERIFY. 176-177 $B0-$B1 CMPO Tape Timing Location 176 ($B0) is used to determine the value of the adjustable timing constant at 146 ($92). Location 177 is also used in the timing of tape reads. 32
# Address: $A8 (168)
BITCI = 168
def set_bitci(val: byte):
    poke(168, val)

def get_bitci() -> byte:
    return peek(168)

# 174 $AE 175 $AF 176 $B0 177 $B1 178 $B2 179 $B3 Operator / (DIVIDE) t (EXPONENTIATE) AND (LOGICAL AND) OR (LOGICAL OR) > (GREATER THAN) = (EQUAL TO) < (LESS THAN) Routine Address 47890 $BB12 49019 $BF7B 45033 $AFE9 45030 $AFE6 49076 $BFB4 44756 $AED4 45078 $B016 41118-41373 $A09E-$A19D RESLST List of Keywords This table contains a complete list of the reserved BASIC keywords (those combinations of ASCII text characters that cause BASIC to do something). The ASCII text characters of these words are stored in token number order. Bit 7 of the last letter of each word is set to indicate the end of the word (the last letter has 128 added to its true ASCII value). When the BASIC program text is stored, this list of words is used to reduce any keywords to a single-byte value called a token. The command PRINT, for example, is not stored in a program as five ASCII bytes, but rather as the single token 153 ($99). When the BASIC program is listed, this table is used to convert these tokens back to ASCII text. The entries in this table consist of the following: 1. The statements found in STMDSP at 40972 ($AOOC), in the token number order indicated (token numbers 128-162). 2. Some miscellaneous keywords which never begin a BASIC statement: Token # Keyword 163 $A3 TAB( 164 $A4 TO 165 $A5 FN 166 $A6 SPC( 167 $A7 THEN 168 $A8 NOT 169 $A9 STEP 3. The math operators found in OPTAB at 41088 ($A080), in the token number order indicated (token numbers 170-179). 4. The functions found in FUNDSP at 41042 ($A052), in the token number order indicated (token numbers 180-202). 5. The word GO (token number 203, $CB). This word was added to the table to make the statement GO TO legal, to afford some compatibility with the very first PET BASIC, which allowed spaces within keywords. 92
# Address: $AD (173)
174 = 173
def set__174(val: byte):
    poke(173, val)

def get__174() -> byte:
    return peek(173)

# l Pointer: Start of Tape Buffer On power-on, this pointer is set to the address of the cassette buffer r~| (828, $33C). This pointer must contain an address greater than or '- equal to 512 ($200), or an ILLEGAL DEVICE NUMBER error will be sent when tape I/O is tried. n I ! n 180 $B4 BITTS RS-232 Output Bit Count/Cassette Temporary Storage RS-232 routines use this to count the number of bits transmitted, and for parity and stop bit manipulation. Tape load routines use this location to flag when they are ready to receive data bytes. 181 $B5 NXTBIT RS-232 Next Bit to Send/Tape EOT Flag This location is used by the RS-232 routines to hold the next bit to be sent, and by the tape routines to indicate what part of a block the read routine is currendy reading. 182 $B6 RODATA RS-232 Output Byte Buffer RS-232 routines use this area to disassemble each byte to be sent from the transmission buffer pointed to by 249 ($F9). 183 $B7 FNLEN Length of Current Filename This location holds the number of characters in the current filename. Disk filenames may have from 1 to 16 characters, while tape filenames range from 0 to 187 characters in length. If the tape name is longer than 16 characters, the excess will be truncated by the SEARCHING and FOUND messages, but will still be present on the tape. This means that machine language programs meant to run in the cassette buffer may be saved as tape filenames. A disk file is always referred to by a name, whether full or generic (containing the wildcard characters * or ? ). This location will always be greater than 0 if the current file is a disk file. Tape LOAD, SAVE, and VERIFY operations do not require that a name be specified, and this location can therefore contain a 0. If this is the case, the contents of the pointer to the filename at 187 will be irrelevant. An RS-232 OPEN command may specify a filename of up to four characters. These characters are copied to locations 659-662 ($293-$296), and determine baud rate, word length, and parity. n 33
# Address: $B2 (178)
TAPE = 178
def set_tape(val: word):
    poke16(178, val)

def get_tape() -> word:
    return peek16(178)

# Current Logical File Number This location holds the logical file number of the device currently being used. A maximum of five disk files, and ten files in total, may be open at any one time. File numbers range from 1 to 255 (a 0 is used to indicate system defaults). When printing to a device with a file number greater than 127, an ASCII linefeed character will be sent following each carriage return, which is useful for devices like serial printers that require linefeeds in addition to carriage returns. The BASIC OPEN command calls the Kernal OPEN routine, which sets the value of this location. In the BASIC statement OPEN 4,8,15, the logical file number corresponds to the first parameter, 4. 185 $B9 SA Current Secondary Address This location holds the secondary address of the device currently being used. The range of valid secondary address numbers is 0 through 31 for serial devices, and 0 through 127 for other devices. Secondary device numbers mean something different to each device that they are used with. The keyboard and screen devices ignore the secondary address completely. But any device which can have more than one file open at the same time, such as the disk drive, distinguishes between these files by using the secondary address. Therefore, it is necessary to specify a secondary address when opening a disk file. Secondary address numbers 0, 1, and 15-31 have a special significance to the disk drive, and therefore device numbers 2-14 only should be used as secondary addresses when opening a disk file. OPENing a disk file with a secondary address of 15 enables the user to communicate with the Disk Operating System through that channel. A LOAD command which specifies a secondary address of 0 (for example, LOAD "AT BASIC", 8,0) results in the program being loaded not to the address specified on the file as the starting address, but rather to the address pointed to by the start of BASIC pointer (43, $2B). A LOAD with a secondary address of 1 (for example, LOAD "HERE", 8,1) results in the contents of the file being loaded to the address specified in the file. A disk file that has been LOADed using a secondary address of 1 can be successfully SAVEd in the same manner (SAVE "DOS 5.1", 8,1). LOADs and SAVEs that do not specify a secondary address will default to a secondary address of 0. When OPENing a Datassette recorder file, a secondary address of 0 signifies that the file will be read, while a secondary address of 1 signifies that the file will be written to. A value of 2 can be added 34
# Address: $B8 (184)
LA = 184
def set_la(val: byte):
    poke(184, val)

def get_la() -> byte:
    return peek(184)

# Current Device Number This location holds the number of the device that is currently being used. Device number assignments are as follows: 0= Keyboard; 1= Datassette Recorder; 2=RS-232/User Port; 3=Screen; 4-5=Printer, 8-ll=Disk. 187-188 $BB-$BC FNADR Pointer: Current Filename This location holds a pointer to the address of the current filename. If an operation which OPENs a tape file does not specify a filename, this pointer is not used. When a disk filename contains a shifted space character, the remainder of the name will appear outside the quotes in the directory, and may be used for comments. For example, if you SAVE "ML[shifted space]SYS 828", the directory entry will read "ML"SYS 828. You may reference the program either by the portion of the name that appears within quotes, or by the full name, including the shifted space. A program appearing later in the directory as "ML"SYS 900 would not be found just by reference to "ML", however. A filename of up to four characters may be used when opening the RS-232 device. These four characters wUl be copied to 659-662 ($293-$296), where they are used to control such parameters as baud rate, parity, and word length. 189 $BD ROPRTY RS-232 Output Parity/Cassette Temporary Storage This location is used by the RS-232 routines as an output parity work byte, and by the tape as temporary storage for the current character being read or sent. 35
# Address: $BA (186)
FA = 186
def set_fa(val: byte):
    poke(186, val)

def get_fa() -> byte:
    return peek(186)

# Cassette Read/Write Block Count Used by the tape routines to count the number of copies of a data block remaining to be read or written. 191 $BF MYCH Tape Input Byte Buffer This is used by the tape routines as a work area in which incoming characters are assembled. 192 $C0 CASl Tape Motor Interlock This location is maintained by the IRQ interrupt routine that scans the keyboard. Whenever a button is pressed on the recorder, this location is checked. If it contains a 0, the motor is turned on by setting Bit 5 of location 1 to 0. When the button is let up, the tape motor is turned off, and this location is set to 0. Since the interrupt routine is executed 60 times per second, you will not be able to keep the motor bit set to keep the motor on if no buttons are pushed. Likewise, if you try to turn the motor off when a button is pressed and this location is set to 0, the interrupt routine will turn it back on. To control the motor via software, you must set this location to a nonzero value after one of the buttons on the recorder has been pressed. 193-194 $C1-$C2 STAL I/O start Address This location points to the beginning address of the area in RAM which is currently being LOADed or SAVEd. For tape I/O, it will point to the cassette buffer, which is used for the first block, while the rest of the I/O operation uses the area of RAM pointed to by location 195 ($C3). 195-196 $C3-$C4 MEMUSS Tape Load Temporary Addresses During a tape LOAD or SAVE, the first block, which contains the header, is loaded to or from the cassette buffer, and the rest of the data is LOADed or SAVEd directly to or from RAM. This location points to the beginning address of the area of RAM to be used for the blocks of data that come after the initial header. 197 $C5 LSTX Matrix Coordinate of Last Key Pressed, 64= None Pressed During every normal IRQ interrupt this location is set with the value 36
# Address: $BE (190)
FSBLK = 190
def set_fsblk(val: byte):
    poke(190, val)

def get_fsblk() -> byte:
    return peek(190)

# 57963 SE26B 192 $C0 TAN 58036 SE2B4 193 $C1 ATN 58126 SE30E 194 $C2 PEEK 47117 SB80D 195 $C3 LBN 46972 SB77C 196 $C4 STR$ 46181 SB465 197 $C5 VAL 47021 $B7AD 198 $C6 ASC 46987 $B78B 199 $C7 CHR$ 46828 SB6EC 200 $C8 LEFTS 46848 SB700 201 $C9 RIGHTS 46892 SB72C 202 $CA MIDS 46903 $B737 41088-41117 $A080-$A09D OPTAB Operator Dispatch Vector Table This table contains two-byte vectors, each of which points to an address which is one byte before the address of one of the routines that perform a BASIC math operation. For the reasoning behind the one-byte offset to the true address, see the entry for location 40972 ($A00C). In addition, each entry has a one-byte number which indicates the degree of precedence that operation takes. Operations with a higher degree of precedence are performed before operations of a lower degree (for example, in the expression A=3+4*6, the 4*6 operation is performed first, and 3 is added to the total). The order in which they are performed is: 1. Expressions in parentheses 2. Exponentiation (raising to a power, using the up-arrow symbol) 3. Negation of an expression (-5,-A) 4. Multiplication and division 5. Addition and subtraction 6. Relation tests (=, <>, ,<=,>= all have the same precedence) 7. NOT (logical operation) 8. AND (logical operation) 9. OR (logical operation) The substance of this table, which can be used to locate the addresses of the math routines, is given below. Note that the less than, equal, and greater than operators all use the same routines, though they have different token numbers. Token # 170 SAA 171 SAB 172 SAC Operator -I- (ADD) -(SUBTRACT) • (MULTIPLY) Routine Address 47210 SB86A 47187 $B853 47659 $BA2B 91
# Address: $BF (191)
SIN = 191
def set_sin(val: byte):
    poke(191, val)

def get_sin() -> byte:
    return peek(191)

# Number of Characters in Keyboard Buffer (Queue) The value here indicates the number of characters waiting in the keyboard buffer at 631 ($277). The maximum number of characters in the keyboard buffer at any one time is determined by the value in location 649 ($289), which defaults to 10. If INPUT or GET is executed while there are already characters in the buffer, those characters will be read as part of the data stream. You can prevent this by POKEing a 0 to this location before those operations, which will always cause any character in the buffer to be ignored. This technique can be handy when using the joystick in Controller Port #1, which sometimes causes false keypresses to be registered, placing unwanted characters in the keyboard buffer. Not only is this location handy for taking unwanted characters out of the keyboard buffer, but it can also be used to put desired characters into the buffer, and thus to program the keyboard buffer. This technique (dynamic keyboard) allows you to simulate keyboard input in direct mode from a program. The dynamic keyboard technique is an extremely useful one, as it enables you to add, delete, or modify program lines while the program is running. The basic scheme is to POKE the PETASCII character values that you wish to be printed (including cursor control characters and carriage returns) into the buffer, and POKE this location with the number of characters in the buffer. Then, when an END statement is executed, the characters in the buffer will be printed, and entered by the carriage returns. This technique can help with the problem of trying to use data separator and terminator characters with INPUT statements. If you try to INPUT a string that has a comma or colon, the INPUT \W11 read only up to that character and issue an EXTRA IGNORED error message. You can avoid this by entering the input string in quotes, but this places on the user the burden of remembering the quote marks. One solution is to use the statement POKE 198,3: POKE 631,34: POKE 632,34: POKE 633,20 before the input. This will force two quote marks and a delete into the buffer. The first quote mark allows the comma or colon to be INPUT, the second is used to get the editor out of quote mode, and the delete removes that second quote.
# Address: $C6 (198)
NDX = 198
def set_ndx(val: byte):
    poke(198, val)

def get_ndx() -> byte:
    return peek(198)

# Flag: Print Reverse Characters? 0=No When the [CTRL] [RVS-ON] characters are printed {CHR$(18)), this flag is set to 18 ($12), and the print routines will add 128 ($80) to the screen code of each character which is printed, so that the character will appear on the screen with its colors inverted. POKEing this location directly with a nonzero number will achieve the same results. You should remember, however, that the contents of this location are returned to 0 not only upon entry of a [CTRL] [RVS-OFF] character (CHR$(146)), but also at every carriage return. When this happens, characters printed thereafter appear with the normal combination of colors. 200 $C8 INDX Pointer: End of Logical Line for Input This pointer indicates the column number of the last nonblank character on the logical line that is to be input. Since a logical line can be up to 80 characters long, this number can range from 0-79. 201-202 $C9-$CA LXSP Cursor X,Y Position at Start of Input These locations keep track of the logical line that the cursor is on, and its column position on that logical line (in line, column format). Each logical line may contain one or two 40-column physical lines. Thus there may be as many as 25 logical lines, or as few as 13 at any one time. Therefore, the logical line number might be anywhere from 1-25. Depending on the length of the logical line, the cursor column may be from 1-40 or 1-80. For a more detailed explanation of logical lines, see the description of the screen line link table, 217 ($D9). 203 $CB SFDX Matrix Coordinate of Current Key Pressed The keyscan interrupt routine uses this location to indicate which key is currently being pressed. The value here is then used as an index into the appropriate keyboard table to determine which character to print when a key is struck. The correspondence between the key pressed and the number stored here is as follows: 0 =INSERT/DELETE 4= fl 1= RETURN 5= f3 2= CURSOR RIGHT 6= £5 3= f7 7= CURSOR DOWN 38
# Address: $C7 (199)
RVS = 199
def set_rvs(val: byte):
    poke(199, val)

def get_rvs() -> byte:
    return peek(199)

# Cursor Blink Enable: 0= Flash Cursor When this flag is set to a nonzero value, it indicates to the routine that normally flashes the cursor not to do so. The cursor blink is turned off when there are characters in the keyboard buffer, or when the program is running. You can use this location to turn the cursor on during a program (for a series of GET operations, for example, to show the user that input is expected) by using the statement POKE 204,0. 205 $CD BLNCT Timer: Countdown to Blink Cursor The interrupt routine that blinks the cursor uses this location to tell when it's time for a blink. First the number 20 is put here, and every jiffy (1/60 second) the value here is decreased by one, until it 39
# Address: $CC (204)
BLNSW = 204
def set_blnsw(val: byte):
    poke(204, val)

def get_blnsw() -> byte:
    return peek(204)

# Character under Cursor The cursor is formed by printing the inverse of the character that occupies the cursor position. If that character is the letter A, for example, the flashing cursor merely alternates between printing an A and a reverse-A. This location keeps track of the normal screen code of the character that is located at the cursor position, so that it may be restored when the cursor moves on. 207 $CF BLNON Flag: Was Last Cursor Blink on or off? This location keeps track of whether, during the current cursor blink, the character under the cursor was reversed, or was restored to normal. This location '"ill contain a 0 if the character is reversed, and a 1 if the character is restored to its nonreversed status. 208 $D0 CRSW Flag: Input from Keyboard or Screen This flag is used by the Kemal CHRIN (61783, $F157) routine to indicate whether input is available from the screen (3), or whether a new line should be obtained from the keyboard (0). 209-210 $D1-$D2 PNT Pointer to the Address of the Current Screen Line This location points to the address in screen RAM of the first column of the logical line upon which the cursor is currently positioned. 211 $D3 PNTR Cursor Column on Current Line The number contained here is the cursor column position within the logical line pointed to by 209 ($D1). Since a logical line can contain up to two physical lines, this value may be from 0 to 79 (the number here is the value returned by the POS function). 212 $D4 CkTSW Flag: Editor in Quote Mode? 0=No A nonzero value in this location indicates that the editor is in quote mode. Quote mode is toggled every time that you type in a quotation mark on a given line — the first quote mark turns it on, the second turns it off, the third turns it back on, etc. If the editor is in this mode when a cursor control character or 40
# Address: $CE (206)
GDBLN = 206
def set_gdbln(val: byte):
    poke(206, val)

def get_gdbln() -> byte:
    return peek(206)

# Maximum Length of Physical Screen Line The line editor uses this location when the end of a line has been reached to determine whether another physical line can be added to the current logical line, or if a new logical line must be started. 214 $D6 TBLX Current Cursor Physical Line Number This location contains the current physical screen line position of the cursor (0-24). It can be used in a fashion to move the cursor vertically, by POKEing the target screen line (1-25) minus 1 here, followed by a PRINT command. For example, POKE 214,9:PRINT:PRINT "WE'RE ON LINE ELEVEN" prints the message on line 11. The first PRINT statement allows the system to update the other screen editor variables so that they will 41
# Address: $D5 (213)
LNMX = 213
def set_lnmx(val: byte):
    poke(213, val)

def get_lnmx() -> byte:
    return peek(213)

# Pointer to the Address of the Current Screen Color RAM Location This pointer is synchronized with the pointer to the address of the first byte of screen RAM for the current line kept in location 209 ($D1). It holds the address of the first byte of color RAM for the corresponding screen line. 245-246 $F5-$F6 KEYTAB Vector: Keyboard Decode Table KEYTAB points to the address of the keyboard matrix lookup table currently being used. Although there are only 64 keys on the keyboard matrix, each key can be used to print up to four different characters, depending on whether it is struck by itself or in combination with the SHIFT, CONTROL, or Commodore logo keys. The tables pointed to by this address hold the ASCII value of each of the 64 keys for one of these possible combinations of keypresses. When it comes time to print the character, the table that is used determines which character is printed. The addresses of the four tables are: 60289 ($EB81) = default uppercase/graphics characters (unshifted) 60354 ($EBC2) = shifted characters 60419 ($EC03) = Commodore logo key characters 60536 ($EC78) = CONTROL characters The concept of the keyboard matrix tables should not be confused with changing the character sets from uppercase/graphics to upper/lowercase. The former involves determining what character is to be placed into screen memory, while the latter involves determining which character data table is to be used to decode the screen memory into individual dots for the display of characters on the screen. That character base is determined by location 53272 ($D018) of the VIC-II chip. 247-248 $F7-$F8 RIBUF Pointer: RS-232 Input Buffer When device number 2 (the RS-232 channel) is opened, two buffers of 256 bytes each are created at the top of memory. This location points to the address of the one which is used to store characters as 43
# Address: $F3 (243)
USER = 243
def set_user(val: word):
    poke16(243, val)

def get_user() -> word:
    return peek16(243)

# Pointer: RS-232 Output Buffer ^ , This location points to the address of the 256-byte output buffer L_J which is used for transmitting data to RS-232 devices (device number 2). 251-254 $FB-$FE Four Free Bytes of Zero Page for User Programs These locations were specifically set aside for user-written ML routines that require zero-page addressing. While other zero-page locations can be used on a noninterference basis, it is guaranteed that BASIC will not alter these locations. 255 $FF BASZPT BASIC Temporary Data for Floating Point to ASCII Conversion This location is used for temporary storage in the process of converting floating point numbers to ASCII characters. U u u
# Address: $F9 (249)
ROBUF = 249
def set_robuf(val: word):
    poke16(249, val)

def get_robuf() -> word:
    return peek16(249)
