// ═══════════════════════════════════════════════════════════════════════════
//  MEMORY PLANNER — Fase 2b
//  • Alloca variabili globali e locali alla Zero Page con blacklist precisa
//  • Basato sulla tabella ZP ufficiale C64 (Mapping the Commodore 64)
// ═══════════════════════════════════════════════════════════════════════════
//
//  MAPPA ZP SICURA (da tabella ufficiale):
//   $00      CPU direction register        → VIETATO
//   $01      CPU port register             → VIETATO
//   $02      Unused                        → LIBERO (1 byte)
//   $03-$04  Puntatore a $B1AA (QINT)     → VIETATO (float vector BASIC)
//   $05-$06  Puntatore a $B391 (GIVAYF)   → VIETATO (float vector BASIC)
//   $07-$11  Flag BASIC (non usati da math)→ LIBERI per ML
//   $12      Flag segno SIN/COS/TAN        → VIETATO se usesFloat
//   $13-$21  Flag I/O BASIC               → LIBERI per ML
//   $22-$2A  Utility/risultato float BASIC → VIETATI se usesFloat
//   $2B-$53  Puntatori BASIC program       → LIBERI per ML (BASIC non eseguito)
//   $54      Costante opcode JMP ($4C)     → VIETATO (USR function)
//   $55-$56  Pointer function evaluation   → VIETATI se usesFloat
//   $57-$60  FAC3/FAC4 per TAN            → VIETATI se usesFloat
//   $61-$6E  FAC1/FAC2 float accumulators  → VIETATI sempre (float attivi)
//   $6F-$8A  Vari BASIC                   → LIBERI per ML (BASIC non eseguito)
//   $8B-$8F  Seed RND                      → VIETATI se usesFloat
//   $90-$FA  KERNAL (sempre attivo)        → VIETATI sempre
//   $FB-$FE  Unused (liberi per ML)        → riservati a tmp/tmp2/ptr
//   $FF      Temp float→ASCII BASIC        → VIETATO

class MemoryPlanner {
  constructor(ast, semScope, usesFloat) {
    this.ast       = ast;
    this.semScope  = semScope;
    this.usesFloat = usesFloat;

    // ── Blacklist ZP — da tabella ufficiale C64 (Mapping the Commodore 64) ──
    // Con $01=$36 (nostro startup): BASIC ROM è RAM → i suoi flag $07-$2A
    // NON vengono modificati durante l'esecuzione ML. Sono quindi USABILI.
    // Blacklist SEMPRE (indipendente da float/non-float):
    //   $00-$01  CPU port
    //   $03-$06  Vettori BASIC QINT/GIVAYF (BASIC li riscrive al caldo)
    //   $54      Costante opcode JMP ($4C) per USR — BASIC la usa al ritorno
    //   $61-$72  FAC1 + FAC2 + overflow area
    //   $73-$8A  ⚠ CHRGET routine IN ZP (codice eseguito da BASIC al ritorno!)
    //   $90-$FA  KERNAL (IRQ jiffy clock, CHROUT, PLOT, CIA ecc.)
    //   $FB-$FE  Riservati ML (nostri tmp/tmp2/ptr)
    //   $FF      Temporaneo float→ASCII BASIC
    this._zpBlack = new Set();
    const blk = (...args) => args.forEach(a => Array.isArray(a)
      ? a.forEach(x => this._zpBlack.add(x))
      : this._zpBlack.add(a));
    const rng = (a,b) => Array.from({length:b-a+1},(_,i)=>a+i);

    blk(0x00, 0x01);                         // CPU port
    blk(rng(0x03, 0x06));                    // vettori BASIC float
    blk(0x54);                               // costante JMP per USR()
    blk(rng(0x61, 0x72));                    // FAC1, FAC2, overflow, rounding
    blk(rng(0x73, 0x8A));                    // ⚠ CHRGET in ZP — MAI sovrascrivere
    blk(rng(0x90, 0xFA));                    // KERNAL
    blk(0xFB, 0xFC, 0xFD, 0xFE);            // utility ml (nostri)
    blk(0xFF);                               // temp BASIC float→ASCII

    // Blacklist aggiuntiva con float attivi:
    if (usesFloat) {
      blk(0x12);                             // flag segno SIN/COS/TAN
      blk(rng(0x22, 0x2A));                 // utility pointer + risultato float
      blk(0x55, 0x56);                       // pointer function evaluation
      blk(rng(0x57, 0x60));                 // FAC3/FAC4 per TAN
      blk(rng(0x8B, 0x8F));                 // seed RND
    }

    // ── Zone SICURE senza float (con $01=$36) ─────────────────────────────
    // $02       (1B)  Truly unused
    // $07-$21  (27B)  Flag BASIC — scratch, non critici
    // $22-$2A   (9B)  Utility float — liberi senza float
    // $55-$60  (12B)  Pointer eval funzioni — liberi senza float
    // $8B-$8F   (5B)  Seed RND — libero senza float
    // Totale: ~54 byte sicuri per variabili utente
    // EVITATI: $2B-$53 (puntatori programma BASIC — corrompono LIST al ritorno)

    blk(rng(0x2B, 0x53));                    // puntatori programma BASIC (TXTTAB/VARTAB/ecc.)

    this.zpStart = 0x02;
    this.zpEnd   = 0x8B;   // tetto ZP sicuro
    this.zpNext  = this.zpStart;

    // Utility: $FB=tmp $FC=tmp2 $FD/$FE=ptr (mai in conflitto con blacklist)
    this.zpUtility = { tmp: 0xFB, tmp2: 0xFC, ptr: 0xFD };

    this.globals     = [];
    this.funcLayouts = new Map();
    this.bssSize     = 0;
  }

  // ── Allocatore ZP con blacklist ─────────────────────────────────────────
  // Ritorna l'indirizzo di inizio di n byte contigui liberi, o null.
  _zpAlloc(n) {
    let start = this.zpNext;
    outer: while (start + n <= this.zpEnd) {
      for (let i = 0; i < n; i++) {
        if (this._zpBlack.has(start + i)) {
          start = start + i + 1;
          continue outer;
        }
      }
      this.zpNext = start + n;
      return start;
    }
    return null; // ZP esaurita → variabile andrà in BSS
  }

  plan() {
    this.ast.globals.forEach(g => this._planGlobal(g));
    this.ast.funcs.forEach(f  => this._planFunc(f));
    return this;
  }

  _planGlobal(g) {
    const sym   = this.semScope.lookup(g.name);
    const type  = sym?.type || g.type;
    const isArr = g.isArr;
    const arrCount = sym?.arrCount
      || (g.arrSize?.k==='Literal' ? g.arrSize.value : null)
      || (g.arrInit?.length) || 0;
    const baseSize = TYPE_SIZE[type] || 1;
    const size  = isArr ? baseSize * Math.max(arrCount, 1) : baseSize;

    let addr = null, isZP = false;
    // Con float attivi: NIENTE ZP per variabili utente — tutto in BSS.
    // Senza float: scalari non-string → ZP se spazio disponibile.
    if (!this.usesFloat && !isArr && type !== 'string') {
      addr = this._zpAlloc(size);
      if (addr !== null) isZP = true;
    }
    if (!isZP) this.bssSize += size;

    this.globals.push({ name:g.name, type, size, addr, isZP, isArr, arrCount, kind:'global' });
  }

  _planFunc(f) {
    const locals = [];
    f.params.forEach(p => {
      const size = TYPE_SIZE[p.type] || 1;
      // Con float: parametri in BSS, senza float: ZP
      const addr = this.usesFloat ? null : this._zpAlloc(size);
      locals.push({ name:p.name, type:p.type, size, kind:'param', addr, isZP: addr!==null });
    });
    this._collectLocals(f.body, locals);
    locals.filter(v => v.kind==='local' && !v.isArr && v.addr==null).forEach(v => {
      // Con float: tutte le locali in BSS (assoluto), senza float: ZP
      if (!this.usesFloat) {
        v.addr = this._zpAlloc(v.size);
        v.isZP = v.addr !== null;
      }
    });
    const frameBytes = locals.filter(v=>!v.isArr).reduce((a,v)=>a+v.size, 0);
    if (this.usesFloat) this.bssSize += frameBytes; // locali float → BSS
    this.funcLayouts.set(f.name, { locals, frameBytes, ret: f.ret||'void' });
  }

  _collectLocals(node, out) {
    if (!node) return;
    if (node.k === 'VarDecl') {
      const baseSize = TYPE_SIZE[node.type] || 1;
      const arrCount = node.isArr
        ? (node.arrSize?.k==='Literal' ? node.arrSize.value : null)
          || (node.arrInit?.length) || 0
        : 0;
      const size = node.isArr ? baseSize * Math.max(arrCount,1) : baseSize;
      out.push({ name:node.name, type:node.type, size, kind:'local',
                 isArr:node.isArr, arrCount, addr:null, isZP:false });
      return;
    }
    if (node.k === 'Block')   { node.stmts.forEach(s => s && this._collectLocals(s, out)); return; }
    if (node.k === 'If')      { this._collectLocals(node.then, out); this._collectLocals(node.else, out); return; }
    if (node.k === 'While' || node.k === 'DoWhile') { this._collectLocals(node.body, out); return; }
    if (node.k === 'For')     { this._collectLocals(node.init, out); this._collectLocals(node.body, out); return; }
  }

  summary() {
    // Conta byte ZP effettivamente usati (evitando buchi della blacklist)
    const zpUsed = this.globals.filter(g=>g.isZP).reduce((a,g)=>a+g.size,0)
                 + [...this.funcLayouts.values()].flatMap(l=>l.locals)
                     .filter(v=>v.isZP).reduce((a,v)=>a+v.size,0);
    const zpFree  = this.zpEnd - this.zpNext;
    const zpTotal = this.zpEnd - this.zpStart;
    const globalCount   = this.globals.length;
    const zpGlobals     = this.globals.filter(g=>g.isZP).length;
    const bssGlobals    = this.globals.filter(g=>!g.isZP).length;
    const totalFuncVars = [...this.funcLayouts.values()].reduce((a,f)=>a+f.locals.length,0);
    return { zpUsed, zpFree, zpTotal, globalCount, zpGlobals, bssGlobals, totalFuncVars };
  }
}