// ═══════════════════════════════════════════════════════════════════════════
//  PARSER — Fase 2b
// ═══════════════════════════════════════════════════════════════════════════
class ParseError extends Error {
  constructor(msg, line, col) { super(msg); this.line=line; this.col=col; }
}

class Parser {
  constructor(tokens) {
    this.tokens  = tokens;
    this.pos     = 0;
    this.errors  = [];
    this.nodeCount = 0;
  }

  // ── Helpers ──────────────────────────────────────────────────────────────
  peek(off=0) {
    const i = this.pos + off;
    return i < this.tokens.length ? this.tokens[i] : this.tokens[this.tokens.length-1];
  }
  cur()  { return this.peek(0); }
  isEOF(){ return this.cur().type === TT.EOF; }

  check(type, val=null) {
    const t = this.cur();
    return t.type === type && (val === null || t.value === val);
  }
  checkKw(kw)  { return this.check(TT.KEYWORD, kw); }
  checkType()  { return this.cur().type === TT.TYPE; }

  advance() { const t=this.cur(); if (!this.isEOF()) this.pos++; return t; }

  expect(type, val=null) {
    if (!this.check(type, val)) {
      const t = this.cur();
      const what = val ? `'${val}'` : type;
      throw new ParseError(`Atteso ${what}, trovato '${t.value ?? t.type}'`, t.line, t.col);
    }
    return this.advance();
  }
  expectKw(kw) { return this.expect(TT.KEYWORD, kw); }

  tryEat(type, val=null) {
    if (this.check(type, val)) { this.advance(); return true; }
    return false;
  }

  mk(n) { this.nodeCount++; return n; }

  _err(msg, tok) {
    tok = tok || this.cur();
    this.errors.push({ msg, line: tok.line||0, col: tok.col||0 });
  }

  // Sincronizzazione su errore: salta fino a ';' o '}'
  sync() {
    while (!this.isEOF()) {
      const t = this.cur();
      if (t.type === TT.SEMI)   { this.advance(); return; }
      if (t.type === TT.RBRACE) { return; }
      if (t.type === TT.KEYWORD && ['if','while','return','func','break','continue','do','for'].includes(t.value)) return;
      if (t.type === TT.TYPE)   return;
      this.advance();
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  DICHIARAZIONI GLOBALI
  // ═══════════════════════════════════════════════════════════════════════
  parse() {
    const globals = [], funcs = [];
    while (!this.isEOF()) {
      try {
        if (this.checkKw('inline')) {
          this.advance(); // consuma 'inline'
          const fd = this.parseFuncDecl(); fd.isInline = true; funcs.push(fd);
        } else if (this.checkKw('raw')) {
          this.advance(); // consuma 'raw'
          this.expectKw('irq');
          const fd = this.parseFuncDecl(); fd.isIrq = true; fd.isRawIrq = true; funcs.push(fd);
        } else if (this.checkKw('irq')) {
          this.advance(); // consuma 'irq'
          const fd = this.parseFuncDecl(); fd.isIrq = true; funcs.push(fd);
        } else if (this.checkKw('func')) {
          funcs.push(this.parseFuncDecl());
        } else if (this.checkType()) {
          globals.push(this.parseVarDecl());
        } else {
          const t = this.cur();
          this._err(`Token inatteso a livello globale: '${t.value ?? t.type}'`, t);
          this.advance();
        }
      } catch(e) {
        if (e instanceof ParseError) this._err(e.message, {line:e.line, col:e.col});
        else this._err(String(e.message));
        this.sync();
      }
    }
    return this.mk(N.Program(globals, funcs));
  }

  // func [TYPE] IDENT '(' params ')' block
  parseFuncDecl() {
    const line = this.cur().line;
    this.expectKw('func');
    let ret = 'void';
    if (this.checkType()) ret = this.advance().value;
    const name = this.expect(TT.IDENT).value;
    this.expect(TT.LPAREN);
    const params = this.parseParams();
    this.expect(TT.RPAREN);
    const body = this.parseBlock();
    return this.mk(N.FuncDecl(name, params, ret, body, line));
  }

  parseParams() {
    const params = [];
    if (this.check(TT.RPAREN)) return params;
    do {
      if (!this.checkType()) break;
      const type = this.advance().value;
      const name = this.expect(TT.IDENT).value;
      let isArr = false;
      if (this.check(TT.LBRACK)) { this.advance(); this.tryEat(TT.RBRACK); isArr = true; }
      params.push({ type, name, isArr });
    } while (this.tryEat(TT.COMMA));
    return params;
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  BLOCCO E STATEMENT
  // ═══════════════════════════════════════════════════════════════════════
  parseBlock() {
    this.expect(TT.LBRACE);
    const stmts = [];
    while (!this.isEOF() && !this.check(TT.RBRACE)) {
      try {
        const s = this.parseStmt();
        if (s) stmts.push(s);
      } catch(e) {
        if (e instanceof ParseError) this._err(e.message, {line:e.line, col:e.col});
        else this._err(String(e.message));
        this.sync();
      }
    }
    this.expect(TT.RBRACE);
    return this.mk(N.Block(stmts));
  }

  parseStmt() {
    const t = this.cur();

    // VarDecl: TYPE ident ...
    if (this.checkType()) return this.parseVarDecl();

    if (t.type === TT.KEYWORD) {
      switch(t.value) {
        case 'if':       return this.parseIf();
        case 'while':    return this.parseWhile();
        case 'do':       return this.parseDoWhile();
        case 'for':      return this.parseFor();
        case 'return':   return this.parseReturn();
        case 'break':    { const l=t.line; this.advance(); this.expect(TT.SEMI); return this.mk(N.Break(l)); }
        case 'continue': { const l=t.line; this.advance(); this.expect(TT.SEMI); return this.mk(N.Continue(l)); }
      }
    }

    // Punto e virgola solitario
    if (this.check(TT.SEMI)) { this.advance(); return null; }

    // Espressione (call, assignment, postfix)
    const expr = this.parseExpr();
    this.expect(TT.SEMI);
    return expr;
  }

  // TYPE IDENT ('[' size ']')? ('=' (expr | '[' list ']'))? ';'
  parseVarDecl() {
    const line = this.cur().line;
    const type = this.advance().value;
    const name = this.expect(TT.IDENT).value;
    let isArr=false, arrSize=null, arrInit=null, init=null;

    if (this.check(TT.LBRACK)) {
      isArr = true; this.advance();
      if (!this.check(TT.RBRACK)) arrSize = this.parseExpr();
      this.expect(TT.RBRACK);
    }
    if (this.check(TT.ASSIGN)) {
      this.advance();
      if (isArr && this.check(TT.LBRACK)) {
        this.advance(); arrInit = [];
        while (!this.isEOF() && !this.check(TT.RBRACK)) {
          arrInit.push(this.parseExpr());
          if (!this.tryEat(TT.COMMA)) break;
        }
        this.expect(TT.RBRACK);
      } else {
        init = this.parseExpr();
      }
    }
    this.expect(TT.SEMI);
    return this.mk(N.VarDecl(type, name, init, isArr, arrSize, arrInit, line));
  }

  // VarDecl senza ';' finale (per ciclo for)
  parseVarDeclInline() {
    const line = this.cur().line;
    const type = this.advance().value;
    const name = this.expect(TT.IDENT).value;
    let init = null;
    if (this.check(TT.ASSIGN)) { this.advance(); init = this.parseExpr(); }
    return this.mk(N.VarDecl(type, name, init, false, null, null, line));
  }

  parseIf() {
    const line = this.cur().line;
    this.expectKw('if');
    this.expect(TT.LPAREN);
    const cond = this.parseExpr();
    this.expect(TT.RPAREN);
    const then_ = this.parseBlock();
    let else_ = null;
    if (this.checkKw('else')) {
      this.advance();
      else_ = this.checkKw('if') ? this.parseIf() : this.parseBlock();
    }
    return this.mk(N.If(cond, then_, else_, line));
  }

  parseWhile() {
    const line = this.cur().line;
    this.expectKw('while');
    this.expect(TT.LPAREN);
    const cond = this.parseExpr();
    this.expect(TT.RPAREN);
    const body = this.parseBlock();
    return this.mk(N.While(cond, body, line));
  }

  parseDoWhile() {
    const line = this.cur().line;
    this.expectKw('do');
    const body = this.parseBlock();
    this.expectKw('while');
    this.expect(TT.LPAREN);
    const cond = this.parseExpr();
    this.expect(TT.RPAREN);
    this.expect(TT.SEMI);
    return this.mk(N.DoWhile(body, cond, line));
  }

  parseFor() {
    const line = this.cur().line;
    this.expectKw('for');
    this.expect(TT.LPAREN);
    let init = null;
    if (!this.check(TT.SEMI)) {
      init = this.checkType() ? this.parseVarDeclInline() : this.parseExpr();
    }
    this.expect(TT.SEMI);
    let cond = null;
    if (!this.check(TT.SEMI)) cond = this.parseExpr();
    this.expect(TT.SEMI);
    let incr = null;
    if (!this.check(TT.RPAREN)) incr = this.parseExpr();
    this.expect(TT.RPAREN);
    const body = this.parseBlock();
    return this.mk(N.For(init, cond, incr, body, line));
  }

  parseReturn() {
    const line = this.cur().line;
    this.expectKw('return');
    let value = null;
    if (!this.check(TT.SEMI)) value = this.parseExpr();
    this.expect(TT.SEMI);
    return this.mk(N.Return(value, line));
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  ESPRESSIONI  (precedenza crescente verso il basso)
  // ═══════════════════════════════════════════════════════════════════════
  parseExpr()   { return this.parseAssign(); }

  // Assegnamento (associativo a destra): lvalue '=' expr
  parseAssign() {
    const left = this.parseOr();
    if (this.check(TT.ASSIGN)) {
      if (left.k !== 'Ident' && left.k !== 'ArrayAccess') {
        this._err('Lvalue non valido nell\'assegnamento');
      }
      const line = this.cur().line;
      this.advance();
      return this.mk(N.Assign(left, this.parseAssign(), line));
    }
    return left;
  }

  parseOr() {
    let l = this.parseAnd();
    while (this.check(TT.OR)) { const op=this.advance().value; l=this.mk(N.BinaryOp(op,l,this.parseAnd())); }
    return l;
  }
  parseAnd() {
    let l = this.parseCmp();
    while (this.check(TT.AND)) { const op=this.advance().value; l=this.mk(N.BinaryOp(op,l,this.parseCmp())); }
    return l;
  }
  parseCmp() {
    let l = this.parseBitOr();
    while (this.check(TT.CMP) || (this.check(TT.OP) && (this.cur().value==='<'||this.cur().value==='>'))) {
      const op=this.advance().value; l=this.mk(N.BinaryOp(op,l,this.parseBitOr()));
    }
    return l;
  }
  parseBitOr() {
    let l = this.parseBitXor();
    while (this.check(TT.OP,'|')) { this.advance(); l=this.mk(N.BinaryOp('|',l,this.parseBitXor())); }
    return l;
  }
  parseBitXor() {
    let l = this.parseBitAnd();
    while (this.check(TT.OP,'^')) { this.advance(); l=this.mk(N.BinaryOp('^',l,this.parseBitAnd())); }
    return l;
  }
  parseBitAnd() {
    let l = this.parseShift();
    while (this.check(TT.OP,'&')) { this.advance(); l=this.mk(N.BinaryOp('&',l,this.parseShift())); }
    return l;
  }
  parseShift() {
    let l = this.parseAdd();
    while (this.cur().type===TT.LSHIFT || this.cur().type===TT.RSHIFT) {
      const op=this.advance().value; l=this.mk(N.BinaryOp(op,l,this.parseAdd()));
    }
    return l;
  }
  parseAdd() {
    let l = this.parseMul();
    while (this.check(TT.OP,'+') || this.check(TT.OP,'-')) {
      const op=this.advance().value; l=this.mk(N.BinaryOp(op,l,this.parseMul()));
    }
    return l;
  }
  parseMul() {
    let l = this.parseUnary();
    while (this.check(TT.OP,'*') || this.check(TT.OP,'/') || this.check(TT.OP,'%')) {
      const op=this.advance().value; l=this.mk(N.BinaryOp(op,l,this.parseUnary()));
    }
    return l;
  }

  parseUnary() {
    if (this.check(TT.OP,'!') || this.check(TT.OP,'~') || this.check(TT.OP,'-')) {
      const op=this.advance().value; return this.mk(N.UnaryOp(op, this.parseUnary()));
    }
    if (this.cur().type===TT.INC || this.cur().type===TT.DEC) {
      const op=this.advance().value; return this.mk(N.UnaryOp('pre'+op, this.parseUnary()));
    }
    return this.parsePostfix();
  }

  parsePostfix() {
    let expr = this.parsePrimary();
    if (this.cur().type===TT.INC || this.cur().type===TT.DEC) {
      const op=this.advance().value; expr=this.mk(N.PostfixOp(op,expr));
    }
    return expr;
  }

  parsePrimary() {
    const t = this.cur();

    // Letterali
    if (t.type===TT.INT_LIT)   { this.advance(); return this.mk(N.Literal('int',   t.value, t.raw)); }
    if (t.type===TT.FLOAT_LIT) { this.advance(); return this.mk(N.Literal('float', t.value, t.raw)); }
    if (t.type===TT.HEX_LIT)   { this.advance(); return this.mk(N.Literal('hex',   t.value, t.raw)); }
    if (t.type===TT.BIN_LIT)   { this.advance(); return this.mk(N.Literal('bin',   t.value, t.raw)); }
    if (t.type===TT.STR_LIT)   { this.advance(); return this.mk(N.Literal('str',   t.value, t.raw ?? `"${t.value}"`)); }

    // Cast: TYPE '(' expr ')'   — es. float(n)  int(x)
    if (t.type===TT.TYPE && this.peek(1).type===TT.LPAREN) {
      const castType = this.advance().value;
      this.advance(); // '('
      const inner = this.parseExpr();
      this.expect(TT.RPAREN);
      return this.mk(N.Cast(castType, inner, t.line));
    }

    // '(' expr ')'
    if (t.type===TT.LPAREN) {
      this.advance();
      const expr = this.parseExpr();
      this.expect(TT.RPAREN);
      return expr;
    }

    // IDENT o BUILTIN: call, array access, o semplice ident
    if (t.type===TT.IDENT || t.type===TT.BUILTIN) {
      const name = this.advance().value;

      // Chiamata: name '(' args ')'
      if (this.check(TT.LPAREN)) {
        const line = t.line;
        this.advance();
        const args = [];
        if (!this.check(TT.RPAREN)) {
          do { args.push(this.parseExpr()); } while (this.tryEat(TT.COMMA) && !this.check(TT.RPAREN));
        }
        this.expect(TT.RPAREN);
        return this.mk(N.Call(name, args, line));
      }

      // Array access: name '[' expr ']'
      if (this.check(TT.LBRACK)) {
        const line = t.line;
        this.advance();
        const idx = this.parseExpr();
        this.expect(TT.RBRACK);
        return this.mk(N.ArrayAccess(name, idx, line));
      }

      return this.mk(N.Ident(name, t.line));
    }

    throw new ParseError(
      `Token inatteso in espressione: '${t.value ?? t.type}'`,
      t.line, t.col
    );
  }
}