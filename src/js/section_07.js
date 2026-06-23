// ═══════════════════════════════════════════════════════════════════════════
//  PRG HEADER INFO — Fase 2b (preview, code gen in Fase 3)
// ═══════════════════════════════════════════════════════════════════════════
// Layout PRG standard con BASIC stub:
//
//  $0801  0B 08 00 00 9E 32 30 36 31 00 00 00  ← BASIC "0 SYS2061"
//  $080D  [codice compilato]
//
//  Startup code (Fase 3 lo genererà):
//    LDA #$36 (o $37)   ; configura $01: BASIC ROM on/off
//    STA $01
//    [corpo di main()]
//    LDA #$37           ; ripristina se avevamo cambiato
//    STA $01
//    RTS

const PRG_LOAD_ADDR   = 0x0801;
const PRG_CODE_OFFSET = 0x080D;  // byte 12 nel file (dopo header 2B + stub 10B)

function makePRGHeaderPreview(usesFloat) {
  const memCfg  = usesFloat ? 0x37 : 0x36;
  const memDesc = usesFloat
    ? '$37 — BASIC ROM visibile (float KERNAL attivo)'
    : '$36 — BASIC ROM → RAM (+8 KB liberi)';
  return { memCfg, memDesc,
    stub: [0x0B,0x08, 0x00,0x00, 0x9E,
           0x32,0x30,0x36,0x31, 0x00, 0x00,0x00],
    startupAsm: usesFloat
      ? '; BASIC ROM rimane visibile — nessuna modifica a $01'
      : 'LDA #$36\nSTA $01   ; BASIC ROM → RAM: 8 KB extra ($A000-$BFFF)'
  };
}