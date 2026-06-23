// ═══════════════════════════════════════════════════════════════════════════
//  PRG BUILDER — Fase 3 Passo 1
//  Costruisce il PRG completo: BASIC stub + startup + stub funzioni + BSS
// ═══════════════════════════════════════════════════════════════════════════
//
//  Layout file PRG:
//    [0-1]  $01 $08          load address $0801
//    [2-13] BASIC stub       "0 SYS2061" → entry point $080D
//    [14..] CodeEmitter buf  startup + funzioni + BSS
//
//  Startup emesso (no-float):
//    $080D  LDA #$36       ; BASIC ROM → RAM
//    $080F  STA $01        ; CPU port
//    $0811  JSR main
//    $0814  LDA #$37       ; ripristina BASIC ROM
//    $0816  STA $01
//    $0818  RTS
//
//  Startup emesso (float):
//    $080D  JSR main       ; $01 invariato (default $37)
//    $0810  RTS

class PRGBuilder {
  constructor(ast, planner, usesFloat, semScope) {
    this.ast       = ast;
    this.planner   = planner;
    this.usesFloat = usesFloat;
    this._semScope = semScope || {lookup:()=>null};
    // BASIC stub: 12 byte caricati a $0801
    this.STUB = [0x0B,0x08, 0x00,0x00, 0x9E,
                 0x32,0x30,0x36,0x31, 0x00, 0x00,0x00];
    // Code emitter: indirizzo base $080D
    this.e         = new CodeEmitter(PRG_CODE_OFFSET);
    this.fixupErrs = [];
    this.built     = false;
  }

  build() {
    try {
      this._emitStartup();
      this._emitFuncBodies();
      this._emitBSS();
      this.fixupErrs = this.e.resolveFixups();
      this.built = true;
    } catch(err) {
      this.fixupErrs.push(`Build error: ${err.message}`);
    }
    return this;
  }

  _emitStartup() {
    const e = this.e;
    if (!this.usesFloat) {
      e.imm('LDA', 0x36, 'BASIC ROM → RAM  ($A000-$BFFF libera)');
      e.zp ('STA', 0x01, 'CPU port  LORAM=0 HIRAM=1 CHAREN=1');
    }
    this._emitGlobalInits();   // init variabili globali prima di main()
    const hasMain = this.ast.funcs.some(f => f.name === 'main');
    if (hasMain) {
      e.jsr('main', 'call main()');
    } else {
      // main() non definita — il SemanticAnalyzer ha già emesso un warning.
      // Emettiamo BRK ($00) così il programma si ferma in modo visibile
      // invece di saltare a un indirizzo KERNAL casuale.
      e.imp('BRK', '!!! main() non definita — halt');
    }
    if (!this.usesFloat) {
      e.imm('LDA', 0x37, 'ripristina BASIC ROM (default $37)');
      e.zp ('STA', 0x01, 'CPU port → $37');
    }
    e.imp('RTS', 'ritorno al BASIC  (SYS return)');
  }

  _emitGlobalInits() {
    // Emette le istruzioni LDA/STA per inizializzare le variabili globali
    // con un valore esplicito prima di chiamare main().
    // Le variabili senza init partono a 0 (ZP non inizializzata = 0 al reset).
    const e = this.e;
    const initialized = new Set(); // evita duplicati (warn "ridichiarato")
    this.ast.globals.forEach(g => {
      // Gli array usano g.arrInit (non g.init) — il check è separato
      const _hasInit = g.isArr ? (g.arrInit && g.arrInit.length > 0) : !!g.init;
      if (!_hasInit || initialized.has(g.name)) return;
      initialized.add(g.name);
      // Array inizializzati: emetti LDA/STA per ogni elemento
      if (g.isArr) {
        if (!g.arrInit || g.arrInit.length === 0) return;
        const sym = this.planner.globals.find(p => p.name === g.name);
        if (!sym || sym.addr == null) return;
        g.arrInit.forEach((el, idx) => {
          if (!el || el.k !== 'Literal') return;
          const v = el.value & 0xFF;
          const ea = sym.addr + idx;
          e.imm('LDA', v, `${g.name}[${idx}]=$${v.toString(16).toUpperCase().padStart(2,'0')}`);
          if (ea < 0x100) e.zp('STA', ea, `${g.name}[${idx}]`);
          else            e.abs('STA', ea, `${g.name}[${idx}]`);
        });
        return;
      }
      const sym = this.planner.globals.find(p => p.name === g.name);
      if (!sym || sym.addr == null) return;

      const isZP  = sym.isZP;
      const addr  = sym.addr;
      const store = (a, comment) => {
        if (isZP) e.zp('STA', a, comment);
        else      e.abs('STA', a, comment);
      };

      if (g.type === 'long' || g.type === 'ulong' || g.type === 'dword') {
        if (g.init.k !== 'Literal') return;
        const v32 = g.init.value >>> 0;
        const b = [v32&0xFF,(v32>>8)&0xFF,(v32>>16)&0xFF,(v32>>24)&0xFF];
        const hex8 = n => n.toString(16).toUpperCase().padStart(8,'0');
        e.imm('LDA',b[0],`${g.name}=$${hex8(v32)} b0`); store(addr,   `${g.name} b0`);
        e.imm('LDA',b[1],`${g.name} b1`);                store(addr+1, `${g.name} b1`);
        e.imm('LDA',b[2],`${g.name} b2`);                store(addr+2, `${g.name} b2`);
        e.imm('LDA',b[3],`${g.name} b3`);                store(addr+3, `${g.name} b3`);
      } else if (g.type === 'word' || g.type === 'int' || g.type === 'uint' || isFixedType(g.type)) {
        if (g.init.k !== 'Literal') return; // expr complessa: skip (raro)
        // Per fixed-point: hex/bin → valore raw Q8.8; intero → scalato
        const fpT = isFixedType(g.type) ? g.type : null;
        let v;
        if (fpT) {
          v = (g.init.kind === 'hex' || g.init.kind === 'bin')
              ? g.init.value & 0xFFFF
              : (Math.round(g.init.value * fpScale(fpT))) & 0xFFFF;
        } else {
          v = g.init.value & 0xFFFF;
        }
        const lo  = v & 0xFF, hi = (v >> 8) & 0xFF;
        e.imm('LDA', lo, `${g.name}=$${hex4(v)} lo`);
        store(addr,     `${g.name} lo`);
        e.imm('LDA', hi, `${g.name} hi`);
        store(addr + 1, `${g.name} hi`);
      } else if (g.type === 'byte' || g.type === 'bool') {
        if (g.init.k !== 'Literal') return;
        const v = g.init.value & 0xFF;
        e.imm('LDA', v, `${g.name}=$${hex2(v)}`);
        store(addr, g.name);
      } else if (g.type === 'float') {
        // Float: 5 byte CBM emessi in BSS con floatToCBM5() — nessun init runtime
      }
    });
  }

  _emitFuncBodies() {
    // Fase 3 Passo 2: emette il corpo reale di ogni funzione tramite CodeGenerator
    const cg = new CodeGenerator(this.e, this.planner, this._semScope, this.ast);
    this.ast.funcs.forEach(f => {
      const layout = this.planner.funcLayouts.get(f.name);
      const info   = `ret=${f.ret||'void'}  frame=${layout?.frameBytes||0}B  params=${f.params.length}`;
      this.e.label(f.name);
      // Commento funzione
      const commentEntry = this.e.listing[this.e.listing.length-1];
      if (commentEntry) commentEntry.comment = `${f.name}()  ${info}`;
      try {
        cg.genFunc(f);
      } catch(err) {
        this.e.imp('NOP', `[CODEGEN ERR] ${f.name}: ${err.message}`);
        this.e.imp('RTS', '');
      }
    });
  }

  _emitBSS() {
    const astByName = new Map(this.ast.globals.map(g => [g.name, g]));

    // ── Globali BSS ────────────────────────────────────────────────────────
    const bssVars = this.planner.globals.filter(g => !g.isZP);
    if (bssVars.length || this.planner.usesFloat) this.e.label('__bss');

    // Buffer temporaneo 5 byte per operazioni float binarie (_evalFloatBinOp)
    if (this.planner.usesFloat) {
      this.e.label('_ftmp');
      this.e.data([0,0,0,0,0], 'float tmp buf (BinOp)');
    }

    bssVars.forEach(g => {
      this.e.label(`_${g.name}`);
      const ast   = astByName.get(g.name);
      const inits = ast?.arrInit;
      const bytes = new Array(g.size).fill(0);
      if (inits && inits.length) {
        inits.forEach((el,i) => {
          if (el && el.k==='Literal' && i<bytes.length) bytes[i]=el.value&0xFF;
        });
      }
      // Float globale: prova a risolvere il valore init a compile-time
      if (ast && ast.type === 'float') {
        let val = null;
        if (ast.init && ast.init.k === 'Literal') {
          val = ast.init.value;
        } else if (ast.init && ast.init.k === 'UnaryOp' && ast.init.op === '-' &&
                   ast.init.operand && ast.init.operand.k === 'Literal') {
          val = -ast.init.operand.value;
        }
        if (val !== null) {
          const cbm5 = floatToCBM5(val);
          this.e.data(cbm5, `float ${g.name}=${val}`);
          return;
        }
      }
      this.e.data(bytes, `${g.type}${g.isArr?`[${g.arrCount}]`:''} ${g.name}`);
    });

    // ── Locali funzioni (solo in modalità float: addr==null) ───────────────
    if (this.planner.usesFloat) {
      for (const [fname, layout] of this.planner.funcLayouts) {
        layout.locals.filter(v => !v.isArr && v.addr==null).forEach(v => {
          const lbl = `_${fname}_${v.name}`;
          this.e.label(lbl);
          this.e.data(new Array(v.size).fill(0),
            `${v.type} ${fname}::${v.name}`);
          // Aggiorna addr in layout per riferimento futuro (word hi = lbl+1)
          v.bssLabel = lbl;
        });
      }
    }
  }

  prgSize()  { return 2 + this.STUB.length + this.e.byteCount(); }
  codeSize() { return this.e.byteCount(); }

  toPRG() {
    const code = this.e.toBytes();
    const prg  = new Uint8Array(2 + this.STUB.length + code.length);
    prg[0] = PRG_LOAD_ADDR & 0xFF;
    prg[1] = (PRG_LOAD_ADDR >> 8) & 0xFF;
    this.STUB.forEach((b,i) => prg[2+i] = b);
    code.forEach((b,i) => prg[2+this.STUB.length+i] = b);
    return prg;
  }
}