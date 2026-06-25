# Memory Page 133

nome: UNKNOWN
descrizione: random - Holds a random number that is incremented during each interrupt 34060-34068 $850C-$8514 saveFontTab GEOS saves the user's active font table here when going into menu display mode. 34069 $8515 dblCUckCount Variable used to determine when the user has double-clicked on an icon It is loaded with a value when the mouse button is pressed while the pointer is over an icon, and this value is decremented during each interrupt. If it has not counted down to zero when the icon is selected again, then the double-click flag in the high byte of pseudoregister rO is set to TRUE when the service routine is called. Otherwise, rO is set to FALSE. 34070 $8516 year The year value for the time of day dock 34071 $8517 month The month value for the time of day clock 34072 $8518 day The day value for the time of day clock n 34073 $8519 hour The hour value for the time of day clock n 34074 $851 A minutes The minutes value for the time of day clock ri 34075 $85 IB seconds The seconds value for the time of day clock i — , 34076 $8510 alarmSetFlag I _ j Variable used to implement the alarm If an alarm is set which GEOS should monitor, this value is set to 255 ($FF). If no alarm is set, the value stored here should be zero. 265
indirizzo_memoria_decimale: 34058-34059
indirizzo_memoria_hex: $850A-$850B
man: Page 279

---

nome: UNKNOWN
descrizione: sysDBData Variable used internally to indicate which command terminated a dialog, causing a return to the application The default screen colors 34079-34495 $851F-$86BF dlgBoxRamBuf Area used to save all of the system RAM variables that define the state of an application These include zero-page global variables, non-zero-page global variables, and information about menus, processes, and sprites. Location Range: 35328-35839 ($8A00$8BFF) SPRITE_PICS Sprite image data 35328-35391 $8A00-$8A3F sprOpic 35392-35455 $8A40-$8A7F sprlpic 35456-35519 $8A80-$8ABF spr2pic 35520-35583 $8AC0-$8AFF spr3pic 35584-35647 $8B00-$8B3F spr4pic 35648-35711 $8B40-$8B7F spr5plc 35712-35775 $8B80-$8BBF spr6pic 35776-35839 $8BC0-$8BFF spr7pic Location Range: 35840-36823 ($8C00$8FD7) COLOR-MATRIX Video color matrix 36824-36855 $8FD8-$8FF7 GEOS free RAM Location Range: 36856-36863 ($8FF8$8FFF) Sprite shape data pointers (For more information, see location 2040, page 82.) 34078 $851E screencolors 266
indirizzo_memoria_decimale: 34077
indirizzo_memoria_hex: $851D
man: Page 280

---
