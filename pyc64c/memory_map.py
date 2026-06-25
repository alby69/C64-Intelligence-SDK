"""
C64 Memory Map Library
Automatically generated from reference documentation.
"""

# Helper functions (assumed to be available in runtime or as built-ins)
# In C64PY, these are often mapped to native peek/poke instructions

def peek(addr: word) -> byte:
    pass

def poke(addr: word, val: byte):
    pass

def peek16(addr: word) -> word:
    pass

def poke16(addr: word, val: word):
    pass

# Flag: Is Data Input to GET, READ or INPUT? Since the keywords GET, INPUT, and READ perform similar functions, BASIC executes some of the same instructions for all three. There are also many areas of difference, however, and this flag indicates which of the three keywords is currently being executed, so that BASIC will know whether or not to execute the instructions which relate to the areas in which the commands differ (152 ($98)=READ, 64 ($40)= GET 0=INPUT). As a result, INPUT will show the ? prompt, will echo characters back to the screen, and will wait for a whole line of text ended by a carriage return. GET gives no prompt and accepts one character without waiting. The colon character and the comma are valid data for GET, but are treated as delimiters between data by INPUT and READ. As each command has its own error messages, this flag is used to determine the appropriate message to issue in case of an error. 18 $12 TANSGN Flag: Sign of the Result of the TAN or SIN Function This location is used to determine whether the sign of the value returned by the functions SIN or TAN is positive or negative. Additionally, the string and numeric comparison routines use this location to indicate the outcome of the comparison. For a comparison of variable A to variable B, the value here will be 1 if A is greater than B, 2 if A equals B, and 4 if A is less than B. If more than one comparison operator was used to compare the two variables (e.g., >= or <= ), the value here will be a combination of the above values. 19 $13 CHANNL Current I/O Channel (CMD Logical File) Number Whenever BASIC inputs or outputs data, it looks here to determine which I/O device is currently active for the purpose of prompting or output control. It uses location 184, $B8 for purposes of deciding what device actually to input from or output to. When the default input device (number 0, the keyboard) or output device (number 3, the display screen) is used, the value here will be a zero, and the format of prompting and output will be the standard screen output format. When another device is used, the logical file number (CMD channel number) will be placed here. This lets the system know that it may have to make some subtle changes in the way it performs the I/O operation. For example, if TAB is used with the PRINT command, cursor right characters are used if the device PRINTed to is the screen. Otherwise, spaces are output when the number here is
# Address: $11 (17)
def get_inpflg() -> byte:
    return peek(17)

def set_inpflg(val: byte):
    poke(17, val)

# Pointer to the Source of GET, READ, or INPUT Information READ, INPUT, and GET all use this as a pointer to the address of the source of incoming data, such as DATA statements, or the text input buffer at 512 ($200). 69-70 $45-$46 VARNAM Current BASIC Variable Name The current variable name being searched for is stored here, in the same two-byte format as in the variable value storage area located at the address pointed to by 45 ($2D). See that location for an explanation of the format. 71-72 $47-$48 VARPNT Pointer to the Current BASIC Variable Value This location points to the address of the descriptor of the current BASIC variable (see location 45 ($2D) for the format of a variable descriptor). Specifically, it points to the byte just after the twocharacter variable name. During a FN call, this location does not point to the dependent variable (the A of FN A), so that a real variable of the same name will not have its value changed by the call. 73-74 $49-$4A FORPNT Temporary Pointer to the Index Variable Used by FOR The address of the BASIC variable which is the subject of a FOR/ NEXT loop is first stored here, but is then pushed onto the stack. That leaves this location free to be used as a work area by such statements as INPUT, GET, READ, LIST, WAIT, CLOSE, LOAD, SAVE, RETURN, and GOSUB. For a description of the stack entries made by FOR, see location 256 ($100). 75-76 $4B-$4C OPPTR Math Operator Table Displacement This location is used during the evaluation of mathematical expressions to hold the displacement of the current math operator in an operator table. It is also used as a save area for the pointer to the address of program text which is currently being read. 77 $4D OPMASK Mask for Comparison Operation The expression evaluation routine creates a mask here which lets it know whether the current comparison operation is a less-than (1), equals (2), or greater-than comparison.
# Address: $43-$44 (67-68)
def get_inpptr() -> word:
    return peek16(67)

def set_inpptr(val: word):
    poke16(67, val)

# Kernal I/O Status Word (ST) The Kernal routines which open I/O channels or perform input/output functions check and update this location. The value here is almost always the same as that returned to BASIC by use of the reserved variable ST. Note that BASIC syntax will not allow an assignment such as ST =4. A table of status codes for cassette and serial devices follows below. Cassette: Bit 2 (Bit Value of 4) = Short Block Bit 3 (Bit Value of 8) = Long Block Bit 4 (Bit Value of 16) = Unrecoverable error (Read), mismatch Bit 5 (Bit Value of 32) = Checksum error Bit 6 (Bit Value of 64) = End of file Bit 7 (Bit Value of 128) = End of tape Serial Devices: Bit 0 (Bit Value of 1) = Time out (Write) Bit 1 (Bit Value of 2) = Time out (Read) Bit 6 (Bit Value of 64) = EOI (End or Identify) Bit 7 (Bit Value of 128) = Device not present Probably the most useful bit to test is Bit 6 (end of file). When using the GET statement to read in individual bytes from a file, the statement IF ST AND 64 will be true if you have got to the end of the file. For status codes for the RS-232 device, see the entry for location 663 ($297). 145 $91 STKEY Flag: Was STOP Key Pressed? This location is updated every 1/60 second during the execution of the IRQ routine that reads the keyboard and updates the jiffy clock. The value of the last row of the keyboard matrix is placed here. That row contains the STOP key, and although this location is used primarily to detect when that key has been pressed, it can also detect when any of the other keys in that row of the matrix have been pressed. In reading the keyboard matrix, a bit set to 1 means that no key has been pressed, while a, bit reset to 0 indicates that a key is pressed. Therefore, the following values indicate the keystrokes detailed below: 255 $FF = no key pressed 254 $FE = 1 key pressed 253 $FD = «- key pressed 251 $FB = CTRL key pressed 27
# Address: $90 (144)
def get_status() -> byte:
    return peek(144)

def set_status(val: byte):
    poke(144, val)

# 56325 Timer A (high byte) $DC05 TIMAHI 56326 Timer B (low byte) $DC06 TIMBLO 56327 Timer B (high byte) $DC07 TIMBHI Location Range: 56328-56331 ($DC08$DCOB) Time of Day Clock (TOD) In addition to the two general-purpose timers, the 6526 CIA chip has a special-purpose Time of Day Clock, which keeps time in a format that humans can understand a little more easily than miaoseconds. This Time of Day Clock even has an alarm, which can cause an interrupt at a specific time. It is organized in four registers, one each for hours, minutes, seconds, and tenths of seconds. Each register reads out in Binary Coded Decimal (BCD) format, for easier conversion to ASCII digits. A BCD byte is divided into two nybbleS, each . of which represents a single digit in base 10. Even though a four-bit nybble can hold a number from 0 to 15, only the base 10 digits of 09 are used. Therefore, 10 o'clock would be represented by a hyte in the hours register with the nybbles 0001 and 0000, which stand for the digits 1 and 0. The binary value of this byte would be 16 (16 times the high nybble plus the low nybble). Each of the other registers operates in the same manner. In addition. Bit 7 of the hours register is used as an AM/PM flag. If that bit is set to 1, it indicates PM, and if it is set to 0, the time is AM. The Time of Day Clock Registers can be used for two purposes, depending on whether you are reading them or writing to them. If you are reading them, you will always be reading the time. There is a latching feature associated with reading the hours register in order to solve the problem of the time changing while you are reading the registers. For example, if you were reading the hours register just as the time was changing from 10:59 to 11:00, it is possible that you would read the 10 in the hours register, and by the time you read the minutes register it would have changed from 59 to 00. Therefore, you would read 10:00 instead of either 10:59 or 11:00. To prevent this kind of mistake, the Time of Day Clock Registers stop updating as soon as you read the hours register, and do not start again until you read the tenths of seconds register. Of course. 180
# Address: $DC04 (56324)
def get_timalo() -> byte:
    return peek(56324)

def set_timalo(val: byte):
    poke(56324, val)
