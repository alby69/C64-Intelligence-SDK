// ═══════════════════════════════════════════════════════════════════════════
//  LEXER — Fase 2a
// ═══════════════════════════════════════════════════════════════════════════
class Lexer {
  constructor(src) { this.src=src; this.pos=0; this.line=1; this.col=1; this.tokens=[]; this.errors=[]; }
  peek(off=0) { return this.src[this.pos+off]; }
  eof()       { return this.pos >= this.src.length; }
  advance() {
    const c = this.src[this.pos++];
    if (c==='\n') { this.line++; this.col=1; } else { this.col++; }
    return c;
  }
  tok(type,value,line,col) { return {type,value,line,col}; }
  _err(msg,line,col) { this.errors.push({msg,line,col}); }
  _skipWhitespace() { while (!this.eof() && /[ \t\r\n]/.test(this.peek())) this.advance(); }

  tokenize() {
    while (!this.eof()) {
      this._skipWhitespace();
      if (this.eof()) break;
      const line=this.line, col=this.col;

      if (this.peek()==='/' && this.peek(1)==='/') { while (!this.eof() && this.peek()!=='\n') this.advance(); continue; }
      if (this.peek()==='/' && this.peek(1)==='*') {
        this.advance(); this.advance();
        while (!this.eof()) {
          if (this.peek()==='*' && this.peek(1)==='/') { this.advance(); this.advance(); break; }
          this.advance();
        }
        continue;
      }
      if (this.peek()==='$' || (this.peek()==='0' && (this.peek(1)==='x'||this.peek(1)==='X'))) {
        const start=this.pos;
        if (this.peek()==='$') this.advance(); else { this.advance(); this.advance(); }
        while (/[0-9A-Fa-f]/.test(this.peek())) this.advance();
        const raw=this.src.slice(start,this.pos);
        const val=parseInt(raw.replace(/^\$|^0[xX]/,''),16);
        const t=this.tok(TT.HEX_LIT,val,line,col); t.raw=raw; this.tokens.push(t); continue;
      }
      if (this.peek()==='%') {
        // Disambiguazione contestuale (come fa il compilatore C):
        // Se il token precedente è un valore (numero, ident, ), ]) → operatore modulo
        // Altrimenti                                                → letterale binario
        // Esempi:  %1010  → BIN_LIT(10)
        //          i%16   → OP(%) + INT_LIT(16)
        //          i % 11 → OP(%) + INT_LIT(11)
        //          i % %11 → OP(%) + BIN_LIT(3)    (modulo del binario 11)
        const prev = this.tokens[this.tokens.length - 1];
        const prevIsValue = prev && (
          prev.type === TT.INT_LIT   ||
          prev.type === TT.HEX_LIT   ||
          prev.type === TT.BIN_LIT   ||
          prev.type === TT.FLOAT_LIT ||
          prev.type === TT.IDENT     ||
          prev.type === TT.RPAREN    ||
          prev.type === TT.RBRACK
        );
        if (prevIsValue) {
          // Operatore modulo
          this.advance();
          this.tokens.push(this.tok(TT.OP,'%',line,col));
        } else {
          // Letterale binario
          this.advance(); let bits='';
          while (/[01]/.test(this.peek())) bits+=this.advance();
          if (!bits) { this._err('Letterale binario vuoto dopo %',line,col); }
          else { const t=this.tok(TT.BIN_LIT,parseInt(bits,2),line,col); t.raw='%'+bits; this.tokens.push(t); }
        }
        continue;
      }
      if (/[0-9]/.test(this.peek())) {
        let num='';
        while (/[0-9]/.test(this.peek())) num+=this.advance();
        if (this.peek()==='.' && /[0-9]/.test(this.peek(1))) {
          num+=this.advance();
          while (/[0-9]/.test(this.peek())) num+=this.advance();
          if (this.peek()==='e'||this.peek()==='E') {
            num+=this.advance();
            if (this.peek()==='+'||this.peek()==='-') num+=this.advance();
            while (/[0-9]/.test(this.peek())) num+=this.advance();
          }
          if (this.peek()==='f') this.advance();
          const t=this.tok(TT.FLOAT_LIT,parseFloat(num),line,col); t.raw=num; this.tokens.push(t);
        } else {
          const t=this.tok(TT.INT_LIT,parseInt(num,10),line,col); t.raw=num; this.tokens.push(t);
        }
        continue;
      }
      if (this.peek()==='"') {
        this.advance(); let s='';
        while (!this.eof() && this.peek()!=='"') {
          if (this.peek()==='\\') { this.advance(); s+=this.advance(); } else s+=this.advance();
        }
        if (this.eof()) this._err('Stringa non chiusa',line,col); else this.advance();
        this.tokens.push(this.tok(TT.STR_LIT,s,line,col)); continue;
      }
      if (/[A-Za-z_]/.test(this.peek())) {
        let id='';
        while (/[A-Za-z0-9_]/.test(this.peek())) id+=this.advance();
        let type=TT.IDENT;
        if (C64_KEYWORDS.has(id)) type=TT.KEYWORD;
        else if (C64_TYPES.has(id)) type=TT.TYPE;
        else if (C64_BUILTINS.has(id)) type=TT.BUILTIN;
        this.tokens.push(this.tok(type,id,line,col)); continue;
      }
      const MULTI=['==','!=','<=','>=','&&','||','++','--','<<','>>'];
      let matched=false;
      for (const op of MULTI) {
        if (this.src.startsWith(op,this.pos)) {
          this.pos+=2; this.col+=2;
          const tt={'==':TT.CMP,'!=':TT.CMP,'<=':TT.CMP,'>=':TT.CMP,'&&':TT.AND,'||':TT.OR,'++':TT.INC,'--':TT.DEC,'<<':TT.LSHIFT,'>>':TT.RSHIFT}[op]||TT.OP;
          this.tokens.push(this.tok(tt,op,line,col)); matched=true; break;
        }
      }
      if (matched) continue;
      const c=this.advance();
      const PUNCT={'(':TT.LPAREN,')':TT.RPAREN,'{':TT.LBRACE,'}':TT.RBRACE,'[':TT.LBRACK,']':TT.RBRACK,';':TT.SEMI,',':TT.COMMA,'.':TT.DOT,'=':TT.ASSIGN};
      const SINGLE=new Set(['+','-','*','/','%','&','|','^','~','!','<','>']);
      if (PUNCT[c]!==undefined) this.tokens.push(this.tok(PUNCT[c],c,line,col));
      else if (SINGLE.has(c))  this.tokens.push(this.tok(TT.OP,c,line,col));
      else this._err(`Carattere inatteso: '${c}'`,line,col);
    }
    this.tokens.push(this.tok(TT.EOF,null,this.line,this.col));
    return {tokens:this.tokens, errors:this.errors};
  }
}