// ═══════════════════════════════════════════════════════════════════════════
//  FASE 3 — PASSO 1 : INFRASTRUTTURA CODE GENERATION
// ═══════════════════════════════════════════════════════════════════════════

const hex2 = n => (n & 0xFF).toString(16).toUpperCase().padStart(2,'0');
const hex4 = n => (n & 0xFFFF).toString(16).toUpperCase().padStart(4,'0');

// ── Tabella opcode MOS 6510 completa ─────────────────────────────────────
// Modes: imp acc imm zp zpx zpy abs abx aby inx iny ind rel
const OPS = {
  ADC:{ imm:0x69,zp:0x65,zpx:0x75,abs:0x6D,abx:0x7D,aby:0x79,inx:0x61,iny:0x71 },
  AND:{ imm:0x29,zp:0x25,zpx:0x35,abs:0x2D,abx:0x3D,aby:0x39,inx:0x21,iny:0x31 },
  ASL:{ acc:0x0A,zp:0x06,zpx:0x16,abs:0x0E,abx:0x1E },
  BCC:{ rel:0x90 }, BCS:{ rel:0xB0 }, BEQ:{ rel:0xF0 }, BIT:{ zp:0x24,abs:0x2C },
  BMI:{ rel:0x30 }, BNE:{ rel:0xD0 }, BPL:{ rel:0x10 }, BRK:{ imp:0x00 },
  BVC:{ rel:0x50 }, BVS:{ rel:0x70 },
  CLC:{ imp:0x18 }, CLD:{ imp:0xD8 }, CLI:{ imp:0x58 }, CLV:{ imp:0xB8 },
  CMP:{ imm:0xC9,zp:0xC5,zpx:0xD5,abs:0xCD,abx:0xDD,aby:0xD9,inx:0xC1,iny:0xD1 },
  CPX:{ imm:0xE0,zp:0xE4,abs:0xEC }, CPY:{ imm:0xC0,zp:0xC4,abs:0xCC },
  DEC:{ zp:0xC6,zpx:0xD6,abs:0xCE,abx:0xDE },
  DEX:{ imp:0xCA }, DEY:{ imp:0x88 },
  EOR:{ imm:0x49,zp:0x45,zpx:0x55,abs:0x4D,abx:0x5D,aby:0x59,inx:0x41,iny:0x51 },
  INC:{ zp:0xE6,zpx:0xF6,abs:0xEE,abx:0xFE },
  INX:{ imp:0xE8 }, INY:{ imp:0xC8 },
  JMP:{ abs:0x4C,ind:0x6C }, JSR:{ abs:0x20 },
  LDA:{ imm:0xA9,zp:0xA5,zpx:0xB5,abs:0xAD,abx:0xBD,aby:0xB9,inx:0xA1,iny:0xB1 },
  LDX:{ imm:0xA2,zp:0xA6,zpy:0xB6,abs:0xAE,aby:0xBE },
  LDY:{ imm:0xA0,zp:0xA4,zpx:0xB4,abs:0xAC,abx:0xBC },
  LSR:{ acc:0x4A,zp:0x46,zpx:0x56,abs:0x4E,abx:0x5E },
  NOP:{ imp:0xEA },
  ORA:{ imm:0x09,zp:0x05,zpx:0x15,abs:0x0D,abx:0x1D,aby:0x19,inx:0x01,iny:0x11 },
  PHA:{ imp:0x48 }, PHP:{ imp:0x08 }, PLA:{ imp:0x68 }, PLP:{ imp:0x28 },
  ROL:{ acc:0x2A,zp:0x26,zpx:0x36,abs:0x2E,abx:0x3E },
  ROR:{ acc:0x6A,zp:0x66,zpx:0x76,abs:0x6E,abx:0x7E },
  RTI:{ imp:0x40 }, RTS:{ imp:0x60 },
  SBC:{ imm:0xE9,zp:0xE5,zpx:0xF5,abs:0xED,abx:0xFD,aby:0xF9,inx:0xE1,iny:0xF1 },
  SEC:{ imp:0x38 }, SED:{ imp:0xF8 }, SEI:{ imp:0x78 },
  STA:{ zp:0x85,zpx:0x95,abs:0x8D,abx:0x9D,aby:0x99,inx:0x81,iny:0x91 },
  STX:{ zp:0x86,zpy:0x96,abs:0x8E }, STY:{ zp:0x84,zpx:0x94,abs:0x8C },
  TAX:{ imp:0xAA }, TAY:{ imp:0xA8 }, TSX:{ imp:0xBA },
  TXA:{ imp:0x8A }, TXS:{ imp:0x9A }, TYA:{ imp:0x98 },
};

// Cicli per opcode+mode (utile per raster/timing, usato nel listing)
const CYCLES = {
  ADC:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  AND:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  ASL:{acc:2,zp:5,zpx:6,abs:6,abx:7},
  BCC:{rel:2},BCS:{rel:2},BEQ:{rel:2},BMI:{rel:2},
  BNE:{rel:2},BPL:{rel:2},BVC:{rel:2},BVS:{rel:2},
  BIT:{zp:3,abs:4}, BRK:{imp:7},
  CLC:{imp:2},CLD:{imp:2},CLI:{imp:2},CLV:{imp:2},
  CMP:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  CPX:{imm:2,zp:3,abs:4}, CPY:{imm:2,zp:3,abs:4},
  DEC:{zp:5,zpx:6,abs:6,abx:7}, DEX:{imp:2}, DEY:{imp:2},
  EOR:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  INC:{zp:5,zpx:6,abs:6,abx:7}, INX:{imp:2}, INY:{imp:2},
  JMP:{abs:3,ind:5}, JSR:{abs:6},
  LDA:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  LDX:{imm:2,zp:3,zpy:4,abs:4,aby:4},
  LDY:{imm:2,zp:3,zpx:4,abs:4,abx:4},
  LSR:{acc:2,zp:5,zpx:6,abs:6,abx:7}, NOP:{imp:2},
  ORA:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  PHA:{imp:3},PHP:{imp:3},PLA:{imp:4},PLP:{imp:4},
  ROL:{acc:2,zp:5,zpx:6,abs:6,abx:7},
  ROR:{acc:2,zp:5,zpx:6,abs:6,abx:7},
  RTI:{imp:6}, RTS:{imp:6},
  SBC:{imm:2,zp:3,zpx:4,abs:4,abx:4,aby:4,inx:6,iny:5},
  SEC:{imp:2},SED:{imp:2},SEI:{imp:2},
  STA:{zp:3,zpx:4,abs:4,abx:5,aby:5,inx:6,iny:6},
  STX:{zp:3,zpy:4,abs:4}, STY:{zp:3,zpx:4,abs:4},
  TAX:{imp:2},TAY:{imp:2},TSX:{imp:2},
  TXA:{imp:2},TXS:{imp:2},TYA:{imp:2},
};