# Memory Page 243

nome: UNKNOWN
descrizione: Find the File in the Logical File Table This subroutine is used by many Kernal routines to find the position of the logical file in the logical file table at 601 ($259). 62239 $F31F Set Current Logical File, Current Device, and Current Secondary Address This subroutine is used to update the Kernal variables at 184-186 ($B8-$BA) which hold the current logical file number, current device number, and current secondary address number. 62255 $F32F CLALL Close All Logical I/O Files CLALL is a documented Kernal routine whose entry point in the jump table is 65511 ($FFE7). The routine jumps through a RAM vector at 812 ($32C). It closes all open files, by resetting the index into open files at 152 ($98) to zero. It then falls through to the next routine, which restores the default I/O devices. 62259 $F333 CLRCHN Restore Current Input and Output Devices to the Default Devices This is a documented Kernal Routine which can be entered at location 65484 ($FFCC) in the jump table. The routine jumps through a RAM vector at 802 ($322). It sets the current input device to the keyboard, and the current output device to the screen. Also, if the current input device was formerly a serial device, the routine sends it an UNTALK command on the serial bus, and if a serial device was formerly the current output device, the routine sends it an UNLISTEN command. 62282 $F34A OPEN open a Logical I/O File OPEN is a documented Kernal I/O routine. It can be entered from the jump table at 65472 ($FFCO). The routine jumps through a RAM vector at 794 ($31 A). This routine assigns a logical file to a device, so that it can be used for 230
indirizzo_memoria_decimale: 62223
indirizzo_memoria_hex: $F30F
man: Page 244

---
