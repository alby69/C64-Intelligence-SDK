"""Runtime library — pre-assembled 6502 helper routines for generated code."""


def runtime_labels_and_bytes(base_addr):
    """Return dict of {label: offset} and bytearray of runtime code.

    All offsets are relative to the runtime start (which gets appended
    after user code). Labels are resolved by the PRGBuilder.
    """
    buf = bytearray()
    labels = {}
    CHROUT = 0xFFD2

    def b(v): buf.append(v & 0xFF)
    def w(v): b(v); b((v >> 8) & 0xFF)
    def label(name): labels[name] = len(buf)

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
    # A now holds the ones digit
    # Print hundreds if non-zero
    b(0xA5); b(0xFE)           # LDA $FE
    b(0xF0); b(0x05)           # BEQ _pb_pt
    b(0x18); b(0x69); b(0x30)  # CLC / ADC #$30 -> PETSCII '0'-'9'
    b(0x20); w(CHROUT)         # JSR $FFD2
    label('_pb_pt')
    b(0xA5); b(0xFF)           # LDA $FF (tens)
    b(0x18); b(0x69); b(0x30)
    b(0x20); w(CHROUT)
    b(0xA5); b(0xFD)           # LDA original
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

    return labels, bytes(buf)
