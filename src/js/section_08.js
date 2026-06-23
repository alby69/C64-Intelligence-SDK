// ═══════════════════════════════════════════════════════════════════════════
//  SISTEMA DEI TIPI — Fase 2b
// ═══════════════════════════════════════════════════════════════════════════

// Dimensione in byte per tipo
const TYPE_SIZE = { byte:1, word:2, int:2, uint:2, bool:1, float:5, string:2, void:0, unknown:0,
  long:4, ulong:4, dword:4,
  // Fixed-point unsigned Q<int>.<frac>
  q8_8:2, q16_8:3, q8_16:3, q16_16:4,
  // Fixed-point signed SQ<int>.<frac>
  sq8_8:2, sq16_8:3, sq8_16:3, sq16_16:4 };

// ── Fixed-Point helpers ──────────────────────────────────────────────────────
// Riconosce tipi fixed-point (q* e sq*)
function isFixedType(t) { return /^s?q\d+_\d+$/.test(t||''); }
// Numero di bit frazionari (es. q8_8 → 8, q16_8 → 8)
function fpFracBits(t)  { const m=(t||'').match(/_(\d+)$/); return m ? +m[1] : 8; }
// Fattore di scala (es. q8_8 → 256, q16_8 → 256)
function fpScale(t)     { return 1 << fpFracBits(t); }
// Colore AST badge per tipi fp
function fpColor(t)     { return /^sq/.test(t) ? '#FF88FF' : '#FFAA44'; }
// Tipo fixed-point con segno (sq*)
function isSignedFP(t)  { return /^sq/.test(t||''); }

// Riconosce tipi a 32 bit
function is32Type(t) { return t==='long'||t==='ulong'||t==='dword'; }

// Promozione implicita: dato tipo A e tipo B, ritorna il tipo del risultato
function promoteTypes(a, b) {
  if (a==='unknown' || b==='unknown') return 'unknown';
  if (a==='float'   || b==='float')   return 'float';
  // 32-bit: prevale long/ulong
  if (is32Type(a) && is32Type(b))     return (a==='long'||b==='long') ? 'long' : 'ulong';
  if (is32Type(a)) return a;
  if (is32Type(b)) return b;
  // Fixed-point: prevale il tipo fp; se entrambi fp, prevale quello con più bit fraz.
  if (isFixedType(a) && isFixedType(b))
    return fpFracBits(a) >= fpFracBits(b) ? a : b;
  if (isFixedType(a)) return a;
  if (isFixedType(b)) return b;
  if (a==='int'     || b==='int')     return 'int';
  if (a==='word'    || b==='word')    return 'word';
  if (a==='uint'    || b==='uint')    return 'word';
  if (a==='string'  || b==='string')  return 'string';
  return 'byte';   // byte OP byte
}

// Tipo di ritorno dei builtin C64
// args: array di nodi già annotati con _type (opzionale)
function builtinRetType(name, args=[]) {
  const F  = new Set(['sqr','log','exp','floor','sin','cos','tan','atn','rnd','fadd','fsub','fmul','fdiv','fpow']);
  const B  = new Set(['peek','kernal_chrin','fp_int','fp_frac','input','sgn']);
  const W  = new Set(['peek16']);
  const S  = new Set(['float_to_str']);
  if (F.has(name)) return 'float';
  // abs/sgn/min/max: tipo polimorfico — segue il tipo dell'argomento
  if (name==='abs' || name==='sgn' || name==='min' || name==='max') {
    const argTypes = args.map(a => a._type || 'int');
    return argTypes.includes('float') ? 'float' : 'int';
  }
  if (W.has(name)) return 'word';
  if (S.has(name)) return 'string';
  if (B.has(name)) return 'byte';
  return 'void';   // poke, print, border_color, clear_screen, wait, ecc.
}

// Colore CSS per tipo (usato in badge AST)
function typeColor(t) {
  if (isFixedType(t)) return fpColor(t);
  switch(t) {
    case 'byte':  return '#70DCFF';
    case 'word':  return '#55EEFF';
    case 'int':   return '#70DCFF';
    case 'long':  return '#AAFFDD';
    case 'ulong': return '#88FFBB';
    case 'dword': return '#88FFBB';
    case 'float': return '#FF99CC';
    case 'bool':  return '#AAFFAA';
    case 'string':return '#FF8844';
    case 'void':  return '#8888CC';
    default:      return '#FF5555';
  }
}