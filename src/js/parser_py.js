class ParseError extends Error {
  constructor(msg, line, col) { super(msg); this.line=line; this.col=col; }
}

class Parser {
  constructor(tokens) { this.tokens=tokens; this.pos=0; this.errors=[]; this.nodeCount=0; }
  peek(off=0) { const i=this.pos+off; return i<this.tokens.length?this.tokens[i]:this.tokens[this.tokens.length-1]; }
  cur() { return this.peek(0); }
  isEOF() { return this.cur().type===TT.EOF; }
  check(type, val=null) { const t=this.cur(); return t.type===type && (val===null || t.value===val); }
  checkKw(kw) { return this.check(TT.KEYWORD, kw); }
  checkType() { return this.cur().type===TT.TYPE; }
  advance() { const t=this.cur(); if (!this.isEOF()) this.pos++; return t; }
  expect(type, val=null) {
    if (!this.check(type, val)) { const t=this.cur(); throw new ParseError(`Atteso ${val||type}, trovato ${t.value||t.type}`, t.line, t.col); }
    return this.advance();
  }
  expectKw(kw) { return this.expect(TT.KEYWORD, kw); }
  tryEat(type, val=null) { if (this.check(type, val)) { this.advance(); return true; } return false; }
  mk(n) { this.nodeCount++; return n; }
  _err(msg, tok) { tok=tok||this.cur(); this.errors.push({ msg, line: tok.line||0, col: tok.col||0 }); }
  sync() { while (!this.isEOF()) { const t=this.cur(); if (t.type===TT.NEWLINE || t.type===TT.DEDENT) return; if (t.type===TT.KEYWORD && ['if','elif','else','while','def','for'].includes(t.value)) return; this.advance(); } }
  parse() {
    const globals=[], funcs=[];
    while (!this.isEOF()) {
      while (this.tryEat(TT.NEWLINE)); if (this.isEOF()) break;
      try {
        if (this.checkKw('def')) { funcs.push(this.parseFuncDecl()); }
        else if (this.check(TT.IDENT) && this.peek(1).type===TT.COLON) { globals.push(this.parseVarDecl()); }
        else { this._err("Dichiarazione globale attesa (def o var:type)"); this.advance(); }
      } catch(e) { if (e instanceof ParseError) { this.errors.push({msg:e.message, line:e.line, col:e.col}); this.sync(); } else throw e; }
    }
    return { globals, funcs, errors:this.errors, nodeCount:this.nodeCount };
  }
  parseSuite() {
    if (this.check(TT.NEWLINE) || this.check(TT.INDENT)) {
      while (this.tryEat(TT.NEWLINE));
      return this.parseBlock();
    }
    const s = this.parseStmt();
    return s ? [s] : [];
  }
  parseBlock() {
    this.expect(TT.INDENT); const stmts=[];
    while (!this.isEOF() && !this.check(TT.DEDENT)) {
      while (this.tryEat(TT.NEWLINE)); if (this.check(TT.DEDENT)) break;
      const s=this.parseStmt(); if (s) stmts.push(s);
      while (this.tryEat(TT.NEWLINE));
    }
    this.expect(TT.DEDENT); return stmts;
  }
  parseStmt() {
    const t=this.cur();
    if (this.checkKw('if')) return this.parseIf();
    if (this.checkKw('while')) return this.parseWhile();
    if (this.checkKw('for')) return this.parseFor();
    if (this.checkKw('return')) { const l=t.line; this.advance(); let val=null; if (!this.check(TT.NEWLINE) && !this.check(TT.DEDENT)) val=this.parseExpr(); return this.mk(N.Return(val, l)); }
    if (this.checkKw('pass')) { this.advance(); return null; }
    if (this.check(TT.IDENT) && this.peek(1).type===TT.COLON) return this.parseVarDecl();
    const e=this.parseExpr();
    if (this.tryEat(TT.ASSIGN)) { const val=this.parseExpr(); return this.mk(N.Assign(e, val, t.line)); }
    return this.mk(N.ExprStmt(e, t.line));
  }
  parseFuncDecl() {
    const line=this.cur().line; this.expectKw('def'); const name=this.expect(TT.IDENT).value;
    this.expect(TT.LPAREN); const params=[];
    if (!this.check(TT.RPAREN)) {
      do { const pName=this.expect(TT.IDENT).value; this.expect(TT.COLON); const pType=this.advance().value; params.push({name:pName, type:pType}); } while (this.tryEat(TT.COMMA));
    }
    this.expect(TT.RPAREN); let ret='void'; if (this.tryEat(TT.ARROW)) ret=this.advance().value;
    this.expect(TT.COLON); const body=this.parseSuite();
    return this.mk(N.FuncDecl(name, params, ret, {stmts:body}, line));
  }
  parseVarDecl() {
    const line=this.cur().line;
    const name=this.expect(TT.IDENT).value; this.expect(TT.COLON); const type=this.advance().value;
    let isArr=false; let arrSize=0;
    if (this.tryEat(TT.LBRACK)) {
        arrSize = this.expect(TT.INT_LIT).value;
        this.expect(TT.RBRACK); isArr=true;
    }
    let init=null; if (this.tryEat(TT.ASSIGN)) init=this.parseExpr();
    return this.mk(N.VarDecl(type, name, init, isArr, arrSize, null, line));
  }
  parseIf() {
    const line=this.cur().line; this.expectKw('if'); const cond=this.parseExpr(); this.expect(TT.COLON);
    const thenB=this.parseSuite(); let elseB=null;
    if (this.checkKw('elif')) elseB = [this.parseIf()];
    else if (this.checkKw('else')) { this.expectKw('else'); this.expect(TT.COLON); elseB=this.parseSuite(); }
    return this.mk(N.If(cond, {stmts:thenB}, elseB?{stmts:elseB}:null, line));
  }
  parseWhile() {
    const line=this.cur().line; this.expectKw('while'); const cond=this.parseExpr(); this.expect(TT.COLON);
    const body=this.parseSuite(); return this.mk(N.While(cond, {stmts:body}, line));
  }
  parseFor() {
    const line=this.cur().line; this.expectKw('for'); const id=this.expect(TT.IDENT).value; this.expectKw('in');
    this.expect(TT.BUILTIN, 'range'); this.expect(TT.LPAREN);
    const start=this.parseExpr(); this.expect(TT.COMMA); const end=this.parseExpr(); this.expect(TT.RPAREN);
    this.expect(TT.COLON); const body=this.parseSuite();
    const init=N.Assign(N.Ident(id, line), start, line);
    const cond=N.BinaryOp('<', N.Ident(id, line), end);
    const incr=N.Assign(N.Ident(id, line), N.BinaryOp('+', N.Ident(id, line), N.Literal('int', 1, '1')), line);
    return this.mk(N.For(init, cond, incr, {stmts:body}, line));
  }
  parseExpr() { return this.parseLogical(); }
  parseLogical() {
    let e=this.parseCmp();
    while (this.check(TT.AND) || this.check(TT.OR)) { const op=this.advance().value; const r=this.parseCmp(); e=this.mk(N.BinaryOp(op,e,r)); }
    return e;
  }
  parseCmp() {
    let e=this.parseBitwise();
    while (this.check(TT.CMP)) { const op=this.advance().value; const r=this.parseBitwise(); e=this.mk(N.BinaryOp(op,e,r)); }
    return e;
  }
  parseBitwise() {
    let e=this.parseShift();
    while (this.check(TT.OP) && ['&','|','^'].includes(this.cur().value)) { const op=this.advance().value; const r=this.parseShift(); e=this.mk(N.BinaryOp(op,e,r)); }
    return e;
  }
  parseShift() {
    let e=this.parseAdditive();
    while (this.check(TT.OP) && ['<<','>>'].includes(this.cur().value)) { const op=this.advance().value; const r=this.parseAdditive(); e=this.mk(N.BinaryOp(op,e,r)); }
    return e;
  }
  parseAdditive() {
    let e=this.parseMultiplicative();
    while (this.check(TT.OP) && (this.cur().value==='+'||this.cur().value==='-')) { const op=this.advance().value; const r=this.parseMultiplicative(); e=this.mk(N.BinaryOp(op,e,r)); }
    return e;
  }
  parseMultiplicative() {
    let e=this.parseUnary();
    while (this.check(TT.OP) && (this.cur().value==='*'||this.cur().value==='/'||this.cur().value==='%')) { const op=this.advance().value; const r=this.parseUnary(); e=this.mk(N.BinaryOp(op,e,r)); }
    return e;
  }
  parseUnary() {
    if (this.check(TT.NOT) || (this.check(TT.OP) && this.cur().value==='-')) { const op=this.advance().value; const r=this.parseUnary(); return this.mk(N.UnaryOp(op,r)); }
    return this.parsePrimary();
  }
  parsePrimary() {
    const t=this.cur();
    if (this.tryEat(TT.LPAREN)) { const e=this.parseExpr(); this.expect(TT.RPAREN); return e; }
    if (this.check(TT.INT_LIT)) return this.mk(N.Literal('int', this.advance().value, t.value.toString()));
    if (this.check(TT.HEX_LIT)) return this.mk(N.Literal('int', this.advance().value, t.raw));
    if (this.check(TT.FLOAT_LIT)) return this.mk(N.Literal('float', this.advance().value, t.value.toString()));
    if (this.check(TT.STR_LIT)) return this.mk(N.Literal('str', this.advance().value, '"'+t.value+'"'));
    if (this.checkKw('True')) { this.advance(); return this.mk(N.Literal('bool', 1, 'True')); }
    if (this.checkKw('False')) { this.advance(); return this.mk(N.Literal('bool', 0, 'False')); }
    if (this.check(TT.IDENT)) {
      const name=this.advance().value;
      if (this.tryEat(TT.LPAREN)) {
        const args=[]; if (!this.check(TT.RPAREN)) { do { args.push(this.parseExpr()); } while (this.tryEat(TT.COMMA)); }
        this.expect(TT.RPAREN); return this.mk(N.Call(name, args, t.line));
      }
      return this.mk(N.Ident(name, t.line));
    }
    if (this.check(TT.BUILTIN)) {
      const name=this.advance().value; this.expect(TT.LPAREN);
      const args=[]; if (!this.check(TT.RPAREN)) { do { args.push(this.parseExpr()); } while (this.tryEat(TT.COMMA)); }
      this.expect(TT.RPAREN); return this.mk(N.Call(name, args, t.line));
    }
    throw new ParseError(`Espressione non valida: ${t.value||t.type}`, t.line, t.col);
  }
}