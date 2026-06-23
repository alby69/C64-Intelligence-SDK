class Lexer {
  constructor(src) {
    this.src = src; this.pos = 0; this.line = 1; this.col = 1;
    this.tokens = []; this.errors = []; this.indentStack = [0]; this.atStartOfLine = true;
  }
  peek(off=0) { return this.src[this.pos+off]; }
  eof()       { return this.pos >= this.src.length; }
  advance() {
    const c = this.src[this.pos++];
    if (c==='\n') { this.line++; this.col=1; this.atStartOfLine = true; } else { this.col++; }
    return c;
  }
  tok(type,value,line,col) { return {type,value,line,col}; }
  _err(msg,line,col) { this.errors.push({msg,line,col}); }
  tokenize() {
    while (!this.eof()) {
      const line=this.line, col=this.col;
      if (this.atStartOfLine) {
        this.atStartOfLine = false; let indent = 0;
        while (!this.eof() && (this.peek() === ' ' || this.peek() === '\t')) {
            if (this.advance() === '\t') indent += 4; else indent++;
        }
        if (this.eof()) break;
        if (this.peek() === '\n') { this.advance(); this.atStartOfLine = true; continue; }
        if (this.peek() === '#') {
            while (!this.eof() && this.peek() !== '\n') this.advance();
            if (this.peek() === '\n') { this.advance(); this.atStartOfLine = true; }
            continue;
        }
        if (indent > this.indentStack[this.indentStack.length - 1]) {
          this.indentStack.push(indent); this.tokens.push(this.tok(TT.INDENT, null, line, col));
        } else {
          while (indent < this.indentStack[this.indentStack.length - 1]) {
            this.indentStack.pop(); this.tokens.push(this.tok(TT.DEDENT, null, line, col));
          }
        }
      }
      while (!this.eof() && (this.peek() === ' ' || this.peek() === '\t')) this.advance();
      if (this.eof()) break;
      if (this.peek() === '\n') { this.tokens.push(this.tok(TT.NEWLINE, '\n', this.line, this.col)); this.advance(); continue; }
      if (this.peek() === '#') { while (!this.eof() && this.peek() !== '\n') this.advance(); continue; }
      const c = this.peek();
      if (c==='$' || (c==='0' && (this.peek(1)==='x'||this.peek(1)==='X'))) {
        const start=this.pos; if (this.peek()==='$') this.advance(); else { this.advance(); this.advance(); }
        while (/[0-9A-Fa-f]/.test(this.peek())) this.advance();
        const raw=this.src.slice(start,this.pos); const val=parseInt(raw.replace(/^\$|^0[xX]/,''),16);
        const t=this.tok(TT.HEX_LIT,val,line,col); t.raw=raw; this.tokens.push(t); continue;
      }
      if (/[0-9]/.test(c)) {
        let num=''; while (/[0-9]/.test(this.peek())) num+=this.advance();
        if (this.peek()==='.') {
          num+=this.advance(); while (/[0-9]/.test(this.peek())) num+=this.advance();
          if (this.peek()==='e'||this.peek()==='E') { num+=this.advance(); if (this.peek()==='+'||this.peek()==='-') num+=this.advance(); while (/[0-9]/.test(this.peek())) num+=this.advance(); }
          this.tokens.push(this.tok(TT.FLOAT_LIT,parseFloat(num),line,col)); continue;
        }
        this.tokens.push(this.tok(TT.INT_LIT,parseInt(num,10),line,col)); continue;
      }
      if (c==='"') {
        this.advance(); let s=''; while (!this.eof() && this.peek()!=='"') { if (this.peek()==='\\') { this.advance(); s+=this.advance(); } else s+=this.advance(); }
        this.advance(); this.tokens.push(this.tok(TT.STR_LIT,s,line,col)); continue;
      }
      if (/[A-Za-z_]/.test(c)) {
        let id=''; while (/[A-Za-z0-9_]/.test(this.peek())) id+=this.advance();
        if (C64PY_KEYWORDS.has(id)) this.tokens.push(this.tok(TT.KEYWORD,id,line,col));
        else if (C64PY_TYPES.has(id)) this.tokens.push(this.tok(TT.TYPE,id,line,col));
        else if (C64PY_BUILTINS.has(id)) this.tokens.push(this.tok(TT.BUILTIN,id,line,col));
        else this.tokens.push(this.tok(TT.IDENT,id,line,col));
        continue;
      }
      const two = c + (this.peek(1)||'');
      if (two==='->') { this.advance(); this.advance(); this.tokens.push(this.tok(TT.ARROW,'->',line,col)); continue; }
      if (['==','!=','<=','>=','&&','||','<<','>>'].includes(two)) {
        this.advance(); this.advance();
        if (['&&','||'].includes(two)) this.tokens.push(this.tok(two==='&&'?TT.AND:TT.OR,two,line,col));
        else this.tokens.push(this.tok(TT.CMP,two,line,col));
        continue;
      }
      if (['<','>'].includes(c)) { this.advance(); this.tokens.push(this.tok(TT.CMP,c,line,col)); continue; }
      if ('+-*/%&|^'.includes(c)) { this.advance(); this.tokens.push(this.tok(TT.OP,c,line,col)); continue; }
      if (c === '=') { this.advance(); this.tokens.push(this.tok(TT.ASSIGN,'=',line,col)); continue; }
      const PUNCT={'(':TT.LPAREN,')':TT.RPAREN,'[':TT.LBRACK,']':TT.RBRACK,',':TT.COMMA,'.':TT.DOT,':':TT.COLON};
      if (PUNCT[c]) { this.advance(); this.tokens.push(this.tok(PUNCT[c],c,line,col)); continue; }
      this._err(`Carattere inatteso: ${c}`,line,col); this.advance();
    }
    while (this.indentStack.length > 1) { this.indentStack.pop(); this.tokens.push(this.tok(TT.DEDENT, null, this.line, this.col)); }
    this.tokens.push(this.tok(TT.EOF, null, this.line, this.col));
    return {tokens:this.tokens, errors:this.errors};
  }
}