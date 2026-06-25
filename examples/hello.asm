; hello.asm — Hello World per Commodore 64
; Assembla: python3 asm6502.py hello.asm -l
; Carica:   LOAD "hello",8,1  poi  SYS 2061

        .org $0801

; BASIC stub: SYS 2061 ($080D)
basic:  .word basic_end
        .word 10
        .null " sys2061"
basic_end:

main:   sei
        lda #$93        ; PETSCII clear screen
        jsr $ffd2       ; CHROUT
        ldx #0
loop:   lda hello_msg,x
        beq done
        jsr $ffd2
        inx
        bne loop
done:   cli
        rts

hello_msg:
        .null "HELLO WORLD! from PYC64"
