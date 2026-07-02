"""Runtime library — pre-assembled 6502 helper routines for generated code."""


def runtime_labels_and_bytes(base_addr):
    """Return dict of {label: offset} and bytearray of runtime code.

    All offsets are relative to the runtime start (which gets appended
    after user code). Labels are resolved by the PRGBuilder.

    ZP Usage:
    $FB, $FC : Primary Word / Pointer (used for inputs and print_str)
    $FD, $FE : Secondary Word / Temps
    $FF      : Temp / Mask
    """
    buf = bytearray()
    labels = {}
    fixups = []
    CHROUT = 0xFFD2

    def b(v): buf.append(v & 0xFF)
    def w(v): b(v); b((v >> 8) & 0xFF)
    def label(name): labels[name] = len(buf)

    def jsr_internal(name):
        fixups.append({'at': len(buf) + 1, 'label': name})
        b(0x20); w(0) # JSR $0000 placeholder

    def build():
        nonlocal buf
        buf = bytearray()
        labels.clear()
        fixups.clear()

        # --- _cls: clear screen via KERNAL CHROUT ---
        label('_cls')
        b(0xA9); b(0x93)           # LDA #$93 (PETSCII CLR/HOME)
        b(0x20); w(CHROUT)         # JSR $FFD2 (CHROUT)
        b(0x60)                     # RTS

        # --- _print_str: print null-terminated string inline after JSR ---
        label('_print_str')
        # Pop return address -> $FB/$FC (string start)
        b(0x68); b(0x85); b(0xFB)  # PLA / STA $FB
        b(0x68); b(0x85); b(0xFC)  # PLA / STA $FC
        label('_ps_loop')
        b(0xA0); b(0x00)           # LDY #0
        b(0xB1); b(0xFB)           # LDA ($FB),Y
        b(0xF0); b(0x0A)           # BEQ _ps_done
        b(0x20); w(CHROUT)         # JSR $FFD2
        b(0xE6); b(0xFB)           # INC $FB
        b(0xD0); b(0xF2)           # BNE _ps_loop (-14)
        b(0xE6); b(0xFC)           # INC $FC
        b(0xD0); b(0xED)           # BNE _ps_loop (-19)
        label('_ps_done')
        b(0xE6); b(0xFB)           # INC $FB (skip null)
        b(0xD0); b(0x02)           # BNE _ps_ret
        b(0xE6); b(0xFC)           # INC $FC (carry)
        label('_ps_ret')
        b(0xA5); b(0xFC)           # LDA $FC
        b(0x48)                     # PHA (push return hi)
        b(0xA5); b(0xFB)           # LDA $FB
        b(0x48)                     # PHA (push return lo)
        b(0x60)                     # RTS

        # --- _print_byte: print A as decimal ---
        label('_print_byte')
        b(0x85); b(0xFD)           # STA $FD (save original)
        # hundreds
        b(0xA2); b(0x00)           # LDX #0
        b(0x38)                     # SEC
        label('_pb_hun')
        b(0xE9); b(0x64)           # SBC #100
        b(0x30); b(0x03)           # BMI _pb_tens_sub
        b(0xE8)                     # INX
        b(0xD0); b(0xF8)           # BNE _pb_hun
        label('_pb_tens_sub')
        b(0x69); b(0x64)           # ADC #100 (restore)
        b(0x86); b(0xFE)           # STX $FE (hundreds digit)
        # tens
        b(0xA2); b(0x00)           # LDX #0
        b(0x38)                     # SEC
        label('_pb_ten')
        b(0xE9); b(0x0A)           # SBC #10
        b(0x30); b(0x03)           # BMI _pb_ones
        b(0xE8)                     # INX
        b(0xD0); b(0xF8)           # BNE _pb_ten
        label('_pb_ones')
        b(0x69); b(0x0A)           # ADC #10 (restore)
        b(0x86); b(0xFF)           # STX $FF (tens digit)
        b(0x85); b(0xFB)           # STA $FB (save ones digit)
        # Print hundreds if non-zero
        b(0xA5); b(0xFE)           # LDA $FE
        b(0xF0); b(0x05)           # BEQ _pb_tens_skip
        b(0x18); b(0x69); b(0x30)  # CLC / ADC #$30 -> PETSCII '0'-'9'
        b(0x20); w(CHROUT)         # JSR $FFD2
        label('_pb_tens_skip')
        # Print tens only if hundreds was non-zero OR tens is non-zero
        b(0xA5); b(0xFE)           # LDA $FE
        b(0xD0); b(0x04)           # BNE _pb_do_tens
        b(0xA5); b(0xFF)           # LDA $FF
        b(0xF0); b(0x05)           # BEQ _pb_one
        label('_pb_do_tens')
        b(0xA5); b(0xFF)
        b(0x18); b(0x69); b(0x30)
        b(0x20); w(CHROUT)
        label('_pb_one')
        b(0xA5); b(0xFB)           # LDA ones digit
        b(0x18); b(0x69); b(0x30)
        b(0x20); w(CHROUT)
        b(0x60)                     # RTS

        # --- _wait_frames: delay-based frame wait (no raster sync needed) ---
        label('_wait_frames')
        b(0x85); b(0xFD)           # STA $FD (frame count)
        label('_wf_loop')
        b(0xA9); b(0x10)           # LDA #16 outer iterations
        b(0x85); b(0xFE)           # STA $FE
        label('_wf_outer')
        b(0xA2); b(0x00)           # LDX #0 (256 inner iterations)
        label('_wf_inner')
        b(0xCA)                     # DEX
        b(0xD0); b(0xFD)           # BNE _wf_inner (-3)
        b(0xC6); b(0xFE)           # DEC $FE
        b(0xD0); b(0xF6)           # BNE _wf_outer (-10)
        b(0xC6); b(0xFD)           # DEC $FD
        b(0xD0); b(0xEE)           # BNE _wf_loop (-18)
        b(0x60)                     # RTS

        # --- _mul_byte: A * $FC -> A (8-bit, repeated addition) ---
        label('_mul_byte')
        b(0x85); b(0xFB)           # STA $FB (multiplicand)
        b(0xA6); b(0xFC)           # LDX $FC (multiplier)
        b(0xA9); b(0x00)           # LDA #0 (result)
        b(0xE0); b(0x00)           # CPX #0
        b(0xF0); b(0x06)           # BEQ _mul_done
        label('_mul_loop')
        b(0x18)                     # CLC
        b(0x65); b(0xFB)           # ADC $FB
        b(0xCA)                     # DEX
        b(0xD0); b(0xF9)           # BNE _mul_loop
        label('_mul_done')
        b(0x60)                     # RTS

        # --- _bitmap_clear: clear 8000 bytes at $2000 ---
        label('_bitmap_clear')
        b(0xA9); b(0x20); b(0x85); b(0xFC) # LDA #$20 / STA $FC (HI)
        b(0xA9); b(0x00); b(0x85); b(0xFB) # LDA #$00 / STA $FB (LO)
        b(0xA2); b(0x20)                   # LDX #32 (32 * 256 = 8192 bytes)
        b(0xA0); b(0x00)                   # LDY #0
        label('_bc_loop')
        b(0x91); b(0xFB)                   # STA ($FB),Y
        b(0xC8)                             # INY
        b(0xD0); b(0xFB)                   # BNE _bc_loop
        b(0xE6); b(0xFC)                   # INC $FC
        b(0xCA)                             # DEX
        b(0xD0); b(0xF6)                   # BNE _bc_loop
        b(0x60)                             # RTS

        # --- _set_sprite_pos: set sprite pos (idx=A, x=$FB/FC, y=X) ---
        label('_set_sprite_pos')
        b(0x48)                             # PHA (idx)
        b(0x0A); b(0xA8)                   # ASL / TAY
        b(0x8A); b(0x99); w(0xD001)         # TXA / STA $D001,Y
        b(0xA5); b(0xFB); b(0x99); w(0xD000) # LDA $FB / STA $D000,Y
        b(0x68)                             # PLA (idx)
        jsr_internal('_get_mask')           # Returns mask in A
        b(0x85); b(0xFF)                   # STA $FF (mask)
        b(0xA5); b(0xFC); b(0xF0); b(0x0A)  # LDA $FC / BEQ _ssp_off
        # X > 255
        b(0xAD); w(0xD010); b(0x05); b(0xFF) # LDA $D010 / ORA $FF
        b(0x8D); w(0xD010); b(0x60)         # STA $D010 / RTS
        label('_ssp_off')
        b(0xA5); b(0xFF); b(0x49); b(0xFF)  # LDA $FF / EOR #$FF
        b(0x2D); w(0xD010); b(0x8D); w(0xD010) # AND $D010 / STA $D010
        b(0x60)                             # RTS

        # --- _set_sprite_bit: A=idx, X=on, $FC/FD=reg_addr ---
        label('_set_sprite_bit')
        b(0x48)                             # PHA (idx)
        jsr_internal('_get_mask')           # Returns mask in A
        b(0x85); b(0xFF)                   # STA $FF (mask)
        b(0x8A); b(0xF0); b(0x0E)           # TXA / BEQ _ssb_off
        # ON
        b(0xA0); b(0x00); b(0xB1); b(0xFC)  # LDY #0 / LDA ($FC),Y
        b(0x05); b(0xFF)                   # ORA $FF
        b(0x91); b(0xFC)                   # STA ($FC),Y
        b(0x68); b(0x60)                   # PLA / RTS
        label('_ssb_off')
        # OFF
        b(0xA5); b(0xFF); b(0x49); b(0xFF)  # LDA $FF / EOR #$FF
        b(0x85); b(0xFF)                   # STA $FF (inv mask)
        b(0xA0); b(0x00); b(0xB1); b(0xFC)  # LDY #0 / LDA ($FC),Y
        b(0x25); b(0xFF)                   # AND $FF
        b(0x91); b(0xFC)                   # STA ($FC),Y
        b(0x68); b(0x60)                   # PLA / RTS

        # --- _get_mask: A = 1 << A (0-7) ---
        label('_get_mask')
        b(0x48)                             # PHA
        b(0xA9); b(0x01)                   # LDA #1
        b(0x85); b(0xFF)                   # STA $FF
        b(0x68); b(0xAA)                   # PLA / TAX
        b(0xF0); b(0x07)                   # BEQ _gm_done
        label('_gm_loop')
        b(0x06); b(0xFF)                   # ASL $FF
        b(0xCA); b(0xD0); b(0xFA)           # DEX / BNE _gm_loop
        label('_gm_done')
        b(0xA5); b(0xFF)                   # LDA $FF
        b(0x60)                             # RTS

        # --- _set_sid_reg: A=voice, X=offset, Y=val ---
        label('_set_sid_reg')
        b(0x85); b(0xFD)                   # STA $FD (voice)
        b(0x0A); b(0x0A); b(0x0A)           # ASL/ASL/ASL (v*8)
        b(0x38); b(0xE5); b(0xFD)           # SEC / SBC $FD (v*7)
        b(0x85); b(0xFD)                   # STA $FD (v*7)
        b(0x8A); b(0x18); b(0x65); b(0xFD) # TXA / CLC / ADC $FD (offset)
        b(0xAA)                             # TAX
        b(0xA5); b(0xFD)                   # LDA $FD (clobber A with voice*7? No, need val from Y)
        # Wait, I need val in A. Caller puts val in Y.
        b(0x98)                             # TYA (val)
        b(0x9D); w(0xD400)                 # STA $D400,X
        b(0x60)                             # RTS

    # First pass to get label offsets
    build()

    # Second pass to patch fixups
    for f in fixups:
        name = f['label']
        if name in labels:
            addr = base_addr + labels[name]
            buf[f['at']] = addr & 0xFF
            buf[f['at'] + 1] = (addr >> 8) & 0xFF

    return labels, bytes(buf)
