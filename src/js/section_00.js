// ═══════════════════════════════════════════════════════════════════════════
//  C64C CodeMirror Mode
// ═══════════════════════════════════════════════════════════════════════════

const C64_KEYWORDS = new Set([
  'if','else','while','for','return','func',
  'break','continue','do','void','irq','raw','inline'
]);
const C64_TYPES = new Set([
  'byte','word','int','uint','bool','string','float',
  'long','ulong','dword',
  // Fixed-point unsigned: Q<int>.<frac>
  'q8_8','q16_8','q8_16','q16_16',
  // Fixed-point signed: SQ<int>.<frac>
  'sq8_8','sq16_8','sq8_16','sq16_16'
]);
const C64_BUILTINS = new Set([
  'print','println','print_at','input',
  'poke','peek','poke16','peek16','memset','memcpy',
  'screen_color','border_color','text_color','clear_screen',
  'plot','draw_line','draw_box','fill_box',
  'wait','wait_frames','sys','jsr',
  'sprite_enable','sprite_pos','sprite_color','sprite_data',
  'sid_note','sid_freq','sid_vol','sid_waveform',
  'abs','sgn','min','max','rnd',
  'sqr','log','exp','floor',
  'sin','cos','tan','atn',
  'float_to_str',
  'fadd','fsub','fmul','fdiv','fpow',
  'fp_int','fp_frac',
  'kernal_chrout','kernal_chrin',
  'sei','cli',
  'enable_raster_irq','disable_raster_irq','ack_raster_irq','ack_raster_irq_fast',
  'next_raster','set_irq_vector','set_nmi_vector',
  'ack_raster_irq_fast', 'pass_irq_to_kernal',
  'raster_sync', 'raster_sync_exact', 'set_raw_irq_vector'
]);
const C64_REGISTERS = new Set(['A','X','Y','SP','PC']);

// Float builtins that require BASIC ROM ($A000-$BFFF)
const FLOAT_KERNAL_BUILTINS = new Set([
  'sqr','log','exp','floor','sin','cos','tan','atn','float_to_str','rnd',
  'fadd','fsub','fmul','fdiv','fpow'
]);

// ─── Conversione float JS → 5 byte formato CBM BASIC ─────────────────────
// Formato: [exp, m1, m2, m3, m4]
//   exp = floor(log2(|x|)) + 129  (biased)
//   m1..m4 = mantissa [0.5,1) × 2^32, bit7 di m1 = segno
function floatToCBM5(val) {
  if (val === 0 || !isFinite(val)) return [0, 0, 0, 0, 0];
  const negative = val < 0;
  const abs = Math.abs(val);
  const e = Math.floor(Math.log2(abs));
  const biasedExp = (e + 129) & 0xFF;
  const M = abs / Math.pow(2, e + 1);   // normalizza in [0.5, 1)
  let m32 = Math.round(M * 4294967296); // mantissa come uint32
  if (m32 > 0xFFFFFFFF) m32 = 0xFFFFFFFF;
  const b1 = (m32 / 16777216) & 0xFF;
  const b2 = (m32 / 65536)    & 0xFF;
  const b3 = (m32 / 256)      & 0xFF;
  const b4 =  m32             & 0xFF;
  // MSB di b1 è sempre 1 (mantissa normalizzata) → sostituito dal bit segno
  return [biasedExp, (b1 & 0x7F) | (negative ? 0x80 : 0x00), b2, b3, b4];
}

CodeMirror.defineMode('c64lang', function() {
  return {
    startState: () => ({ inString: false, strChar: null, inComment: false }),
    token: function(stream, state) {
      if (state.inComment) {
        if (stream.match('*/')) { state.inComment = false; return 'c64-comment'; }
        stream.next(); return 'c64-comment';
      }
      if (state.inString) {
        if (stream.eat(state.strChar)) { state.inString = false; return 'c64-string'; }
        if (stream.eat('\\')) stream.next(); else stream.next();
        return 'c64-string';
      }
      if (stream.eatSpace()) return null;
      if (stream.match('//')) { stream.skipToEnd(); return 'c64-comment'; }
      if (stream.match('/*')) { state.inComment = true; return 'c64-comment'; }
      if (stream.match(/^\$[0-9A-Fa-f]+/) || stream.match(/^0[xX][0-9A-Fa-f]+/)) return 'c64-hex';
      if (stream.match(/^%[01]+/)) return 'c64-number';
      if (stream.match(/^[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?f?/)) return 'c64-float';
      if (stream.match(/^[0-9]+/)) return 'c64-number';
      if (stream.peek() === '"' || stream.peek() === "'") {
        state.strChar = stream.next(); state.inString = true; return 'c64-string';
      }
      if (stream.match(/^[A-Za-z_][A-Za-z0-9_]*/)) {
        const w = stream.current();
        if (C64_KEYWORDS.has(w))  return 'c64-keyword';
        if (C64_TYPES.has(w))     return 'c64-type';
        if (C64_BUILTINS.has(w))  return 'c64-builtin';
        if (C64_REGISTERS.has(w)) return 'c64-register';
        return 'c64-variable';
      }
      if (stream.match(/^(==|!=|<=|>=|&&|\|\||<<|>>|\+\+|--|[=+\-*\/%&|^~!<>])/)) return 'c64-operator';
      if (stream.match(/^@\$[0-9A-Fa-f]+/)) return 'c64-address';
      stream.next(); return null;
    }
  };
});