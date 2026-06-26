# Memory Page 7

nome: UNKNOWN
descrizione: sprite Shape Data Pointers The last eight bytes of the video matrix (whether it is here at the default location, or has been relocated elsewhere) are used as pointers to the data blocks used to define the sprite shapes. Each sprite is 3 bytes wide (24 bits) by 21 lines high. It therefore requires 63 bytes for its shape definition, but it actually uses 64 bytes in order to arrive at an even 256 shape blocks in the 16K area of RAM which the VIC-II chip addresses. Each pointer holds the current data block being used to define the shape of one sprite. The block number used to define the shape of Sprite 0 is held in location 2040 ($7F8), the Sprite 1 shape block is designated by location 2041 ($7F9), etc. The value in the pointer times 64 equals the starting location of the sprite shape data table. For example, a value of 11 in location 2040 indicates that the shape data for Sprite 0 starts at address 704 (11*64), and continues for 63 more bytes to 767. For additional information on sprite graphics, see the entries for individual VIC-II chip sprite graphics locations, and the summary at the beginning of the VIC-II chip section, at 53248 ($D000). 2048-40959 $800-$9FFF BASIC Program Text This is the area where the actual BASIC program text is stored. The text of a BASIC program consists of linked lines of program tokens. Each line contains the following: 1. A two-byte pointer to the address of the next program line (in standard low-byte, high-byte order). After the last program line, a link pointer consisting of two zeros marks the end of ttie program. 82
indirizzo_memoria_decimale: 2040-2047
indirizzo_memoria_hex: $7F8-$7FF
man: Page 96

---
