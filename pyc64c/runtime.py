"""Runtime library — pre-assembled 6502 helper routines for generated code."""


def runtime_labels_and_bytes(base_addr):
    """Return dict of {label: offset} and bytearray of runtime code.

    All offsets are relative to the runtime start (which gets appended
    after user code). Labels are resolved by the PRGBuilder.
    """
    # Pre-calculate labels to allow cross-references
    labels = {
        '_cls': 0,
        '_print_str': 6,
        '_ps_loop': 12,
        '_ps_done': 29,
        '_ps_ret': 35,
        '_print_byte': 42,
        '_pb_hun': 47,
        '_pb_tens': 84,
        '_pb_ten': 61,
        '_pb_ones': 68,
        '_pb_do_tens': 92,
        '_pb_one': 100,
        '_wait_frames': 109,
        '_wf_loop': 111,
        '_wf_outer': 115,
        '_wf_inner': 117,
        '_mul_byte': 129,
        '_mul_loop': 139,
        '_mul_done': 145,
        '_bitmap_clear': 146,
        '_bc_loop': 158,
        '_set_sprite_pos': 169,
        '_ssp_off': 202,
        '_set_sprite_bit': 214,
        '_ssb_off': 238,
        '_get_mask': 255,
        '_gm_loop': 264,
        '_gm_done': 269
    }
    buf = bytearray()
    CHROUT = 0xFFD2

    def b(v): buf.append(v & 0xFF)
    def w(v): b(v); b((v >> 8) & 0xFF)
    def label(name):
        if name not in labels:
            labels[name] = len(buf)
        elif labels[name] != len(buf):
             # For now let's just update it to be sure
             labels[name] = len(buf)

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
    b(0xF0); b(0x09)           # BEQ _ps_done
    b(0x20); w(CHROUT)         # JSR $FFD2
    b(0xE6); b(0xFB)           # INC $FB
    b(0xD0); b(0xF3)           # BNE _ps_loop (-13)
    b(0xE6); b(0xFC)           # INC $FC
    b(0xD0); b(0xEE)           # BNE _ps_loop (-18)
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
    b(0x30); b(0x02)           # BMI _pb_tens
    b(0xE8)                     # INX
    b(0xD0); b(0xF8)           # BNE _pb_hun
    label('_pb_tens')
    b(0x69); b(0x64)           # ADC #100 (restore)
    b(0x86); b(0xFE)           # STX $FE (hundreds digit)
    # tens
    b(0xA2); b(0x00)           # LDX #0
    b(0x38)                     # SEC
    label('_pb_ten')
    b(0xE9); b(0x0A)           # SBC #10
    b(0x30); b(0x02)           # BMI _pb_ones
    b(0xE8)                     # INX
    b(0xD0); b(0xF8)           # BNE _pb_ten
    label('_pb_ones')
    b(0x69); b(0x0A)           # ADC #10 (restore)
    b(0x86); b(0xFF)           # STX $FF (tens digit)
    b(0x85); b(0xFB)           # STA $FB (save ones digit)
    # Print hundreds if non-zero
    b(0xA5); b(0xFE)           # LDA $FE
    b(0xF0); b(0x05)           # BEQ _pb_tens
    b(0x18); b(0x69); b(0x30)  # CLC / ADC #$30 -> PETSCII '0'-'9'
    b(0x20); w(CHROUT)         # JSR $FFD2
    label('_pb_tens')
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
    # Each "frame" is ~20000 CPU cycles (approx 1 PAL frame at 1MHz).
    label('_wait_frames')
    b(0x85); b(0xFD)           # STA $FD (frame count)
    label('_wf_loop')
    b(0xA9); b(0x10)           # LDA #16 outer iterations (~20576 cycles per frame)
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
    b(0xA2); b(0x20)                   # LDX #32 (32 * 256 = 8192 bytes, enough for 8000)
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
    b(0x68); b(0x20); w(base_addr + labels['_get_mask']) # PLA / JSR _get_mask
    b(0x85); b(0xFD)                   # STA $FD (mask)
    b(0xA5); b(0xFC); b(0xF0); b(0x0A)  # LDA $FC / BEQ _ssp_off
    # X > 255
    b(0xAD); w(0xD010); b(0x05); b(0xFD) # LDA $D010 / ORA $FD
    b(0x8D); w(0xD010); b(0x60)         # STA $D010 / RTS
    label('_ssp_off')
    b(0xA5); b(0xFD); b(0x49); b(0xFF)  # LDA $FD / EOR #$FF
    b(0x2D); w(0xD010); b(0x8D); w(0xD010) # AND $D010 / STA $D010
    b(0x60)                             # RTS

    # --- _set_sprite_bit: A=idx, X=on, $FC/FD=reg_addr ---
    label('_set_sprite_bit')
    b(0x48)                             # PHA (idx)
    b(0x20); w(base_addr + labels['_get_mask']) # JSR _get_mask
    b(0x85); b(0xFE)                   # STA $FE (mask)
    b(0x8A); b(0xF0); b(0x0E)           # TXA / BEQ _ssb_off
    # ON
    b(0xA0); b(0x00); b(0xB1); b(0xFC)  # LDY #0 / LDA ($FC),Y
    b(0x05); b(0xFE)                   # ORA $FE
    b(0x91); b(0xFC)                   # STA ($FC),Y
    b(0x68); b(0x60)                   # PLA / RTS
    label('_ssb_off')
    # OFF
    b(0xA5); b(0xFE); b(0x49); b(0xFF)  # LDA $FE / EOR #$FF
    b(0x85); b(0xFE)                   # STA $FE (inv mask)
    b(0xA0); b(0x00); b(0xB1); b(0xFC)  # LDY #0 / LDA ($FC),Y
    b(0x25); b(0xFE)                   # AND $FE
    b(0x91); b(0xFC)                   # STA ($FC),Y
    b(0x68); b(0x60)                   # PLA / RTS

    # --- _get_mask: A = 1 << A (0-7) ---
    label('_get_mask')
    b(0x48)                             # PHA
    b(0xA9); b(0x01)                   # LDA #1
    b(0x85); b(0xFB)                   # STA $FB
    b(0x68); b(0xAA)                   # PLA / TAX
    b(0xF0); b(0x07)                   # BEQ _gm_done
    label('_gm_loop')
    b(0x06); b(0xFB)                   # ASL $FB
    b(0xCA); b(0xD0); b(0xFA)           # DEX / BNE _gm_loop
    label('_gm_done')
    b(0xA5); b(0xFB)                   # LDA $FB
    b(0x60)                             # RTS

    return labels, bytes(buf)
