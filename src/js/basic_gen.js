class BASICGenerator {
  constructor(ast) { this.ast=ast; this.lines=[]; this.curLine=10; this.vars=new Map(); this.nextVarId=0; this.funcLines=new Map(); }
  _genVar(name) { if (this.vars.has(name)) return this.vars.get(name); let bName=(name.length<=2&&!/^[0-9]/.test(name))?name.toUpperCase():'V'+(this.nextVarId++); if(['IF','TO','ON','OR','AS'].includes(bName)) bName='V'+(this.nextVarId++); this.vars.set(name,bName); return bName; }
  generate() {
    this.lines=[]; this.curLine=10; this.funcLines.clear(); this.ast.funcs.forEach(f=>{ if(f.name==='main') this.funcLines.set(f.name,1000); else this.funcLines.set(f.name,2000+([...this.funcLines.keys()].length*500)); });
    this.ast.globals.forEach(g=>{ if(g.init) this.add(this._genVar(g.name)+' = '+this._expr(g.init)); });
    if(this.funcLines.has('main')) this.add('GOSUB '+this.funcLines.get('main')); this.add('END');
    this.ast.funcs.forEach(f=>{ this.curLine=this.funcLines.get(f.name); this.add('REM FUNCTION '+f.name); this._block(f.body); this.add('RETURN'); });
    return this.lines.join('\n');
  }
  add(cmd) { this.lines.push(this.curLine+' '+cmd); this.curLine+=10; }
  _block(block) { block.stmts.forEach(s=>this._stmt(s)); }
  _stmt(s) {
    if(!s) return;
    if(s.k === 'ExprStmt') { this._stmt(s.expr); return; }
    switch(s.k) {
      case 'VarDecl': this.add(this._genVar(s.name)+' = '+(s.init?this._expr(s.init):'0')); break;
      case 'Assign': this.add(this._expr(s.target)+' = '+this._expr(s.value)); break;
      case 'If':
        let ifLine=this.curLine; this.add('IF NOT ('+this._expr(s.cond)+') THEN GOTO '+(ifLine+1000)); this._block(s.then); let endThen=this.curLine;
        if(s.else) { this.add('GOTO '+(endThen+1000)); let startElse=this.curLine; this.lines=this.lines.map(l=>l.startsWith(ifLine+' IF NOT')?l.replace((ifLine+1000).toString(),startElse):l); this._block(s.else); let endElse=this.curLine; this.lines=this.lines.map(l=>l.startsWith(endThen+' GOTO')?l.replace((endThen+1000).toString(),endElse):l); }
        else { let endIf=this.curLine; this.lines=this.lines.map(l=>l.startsWith(ifLine+' IF NOT')?l.replace((ifLine+1000).toString(),endIf):l); }
        break;
      case 'While':
        let startW=this.curLine; this.add('REM WHILE '+this._expr(s.cond)); let condLine=this.curLine-10; this._block(s.body); this.add('GOTO '+startW); let endW=this.curLine;
        this.lines=this.lines.map(l=>l.startsWith(condLine+' REM WHILE')?l.replace('REM WHILE','IF NOT ('+this._expr(s.cond)+') THEN GOTO '+endW+' : REM'):l);
        break;
      case 'For':
        this._stmt(s.init); let startF=this.curLine; this.add('IF NOT ('+this._expr(s.cond)+') THEN GOTO '+(startF+1000)); let loopCond=this.curLine-10; this._block(s.body); this._stmt(s.incr); this.add('GOTO '+startF); let endF=this.curLine;
        this.lines=this.lines.map(l=>l.startsWith(loopCond+' IF NOT')?l.replace((startF+1000).toString(),endF):l);
        break;
      case 'Call':
        if(s.name==='print'||s.name==='println') { this.add('PRINT '+s.args.map(a=>this._expr(a)).join(';')+(s.name==='println'?'':';')); }
        else if(this.funcLines.has(s.name)) { this.add('GOSUB '+this.funcLines.get(s.name)); }
        else if(s.name==='poke') { this.add('POKE '+this._expr(s.args[0])+','+this._expr(s.args[1])); }
        else if(s.name==='wait') { this.add('FOR TI=1 TO '+this._expr(s.args[0])+':NEXT'); }
        else if(s.name==='wait_frames') { this.add('FOR TI=1 TO '+this._expr(s.args[0])+':WAIT 53266,128:NEXT'); }
        else if(s.name==='clear_screen') { this.add('PRINT CHR$(147)'); }
        else if(s.name==='border_color') { this.add('POKE 53280,'+this._expr(s.args[0])); }
        else if(s.name==='screen_color') { this.add('POKE 53281,'+this._expr(s.args[0])); }
        else if(s.name==='print_at') { this.add('POKE 211,'+this._expr(s.args[0])+':POKE 214,'+this._expr(s.args[1])+':SYS 58732:PRINT '+this._expr(s.args[2])+';'); }
        else { this.add('REM CALL '+s.name); }
        break;
      case 'Return': this.add('RETURN'); break;
    }
  }
  _expr(e) {
    if(!e) return '0';
    if(e.k==='Literal') {
      if(e.kind==='str') return '"'+e.value+'"';
      if(e.kind==='bool') return e.value === 1 ? '-1' : '0';
      return e.value;
    }
    if(e.k==='Ident') return this._genVar(e.name);
    if(e.k==='Call') {
      if(e.name==='peek') return 'PEEK('+this._expr(e.args[0])+')';
      return '0';
    }
    if(e.k==='BinaryOp') {
      let op=e.op;
      if(op==='&&') op='AND';
      if(op==='||') op='OR';
      if(op==='&')  op='AND';
      if(op==='|')  op='OR';
      if(op==='!=') op='<>';
      if(op==='%') return '('+this._expr(e.left)+'-INT('+this._expr(e.left)+'/'+this._expr(e.right)+')*'+this._expr(e.right)+')';
      return '('+this._expr(e.left)+' '+op+' '+this._expr(e.right)+')';
    }
    if(e.k==='UnaryOp') { if(e.op==='!') return 'NOT ('+this._expr(e.operand)+')'; return e.op+'('+this._expr(e.operand)+')'; }
    return '0';
  }
}