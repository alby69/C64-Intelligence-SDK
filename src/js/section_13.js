// ═══════════════════════════════════════════════════════════════════════════
//  CODE EMITTER — Fase 3 Passo 1
//  Buffer di byte con gestione label/fixup e listing annotato
// ═══════════════════════════════════════════════════════════════════════════
class CodeEmitter {
  constructor(baseAddr = PRG_CODE_OFFSET) {
    this.base    = baseAddr;   // indirizzo del primo byte nel buffer ($080D)
    this.buf     = [];         // byte buffer (array of 0-255)
    this.labels  = new Map();  // name → offset in buf
    this.fixups  = [];         // {at, type:'abs'|'rel', label, addrOf, instrEnd}
    this.listing = [];         // [{addr,bytes,mnem,op,comment,mode,isLabel,isData,fixup}]
    this._uid    = 0;
  }

  here()  { return this.buf.length; }          // offset corrente nel buffer
  addr()  { return this.base + this.buf.length; } // indirizzo assoluto corrente

  // ── Emit raw ──────────────────────────────────────────────────────────
  _b(v)   { this.buf.push(v & 0xFF); }
  _w(v)   { this._b(v); this._b((v >> 8) & 0xFF); }

  data(arr, comment='') {
    const a = this.addr();
    arr.forEach(b => this._b(b));
    this.listing.push({ addr:a, bytes:[...arr], mnem:'.byte',
      op:arr.map(b=>`$${hex2(b)}`).join(','), comment, isData:true });
  }

  // ── Labels ───────────────────────────────────────────────────────────
  label(name) {
    if (this.labels.has(name)) throw new Error(`Label doppia: '${name}'`);
    this.labels.set(name, this.here());
    this.listing.push({ addr:this.addr(), bytes:[], mnem:'', op:'',
      comment:name+':', isLabel:true, labelName:name });
  }
  uniq(pfx='_L') { return `${pfx}${this._uid++}`; }

  // ── Instruction emission ──────────────────────────────────────────────
  _getOp(mnem, mode) {
    const op = OPS[mnem]?.[mode];
    if (op === undefined) throw new Error(`Opcode mancante: ${mnem} ${mode}`);
    return op;
  }
  _li(addr, bytes, mnem, op, mode, comment, fixup=false) {
    this.listing.push({ addr, bytes:[...bytes], mnem, op, mode, comment, fixup });
  }

  rti(comment='') {
    const a=this.addr(); this._b(0x40);
    this._li(a,[0x40],'RTI','','imp',comment);
  }
  immLo(label, comment='') {
    // LDA #<label — lo byte dell'indirizzo, risolto da fixup
    const a=this.addr(), op=this._getOp('LDA','imm');
    this._b(op); this._b(0);
    this.fixups.push({at:this.here()-1,type:'lo',label,addrOf:a,instrEnd:null});
    this._li(a,[op,0],'LDA',`#<${label}`,'imm',comment,true);
  }
  immHi(label, comment='') {
    // LDA #>label — hi byte dell'indirizzo
    const a=this.addr(), op=this._getOp('LDA','imm');
    this._b(op); this._b(0);
    this.fixups.push({at:this.here()-1,type:'hi',label,addrOf:a,instrEnd:null});
    this._li(a,[op,0],'LDA',`#>${label}`,'imm',comment,true);
  }
  imp(mnem, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'imp');
    this._b(op); this._li(a,[op],mnem,'','imp',comment);
  }
  acc(mnem, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'acc');
    this._b(op); this._li(a,[op],mnem,'A','acc',comment);
  }
  imm(mnem, val, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'imm');
    const v=val&0xFF;
    this._b(op); this._b(v);
    this._li(a,[op,v],mnem,`#$${hex2(v)}`,'imm',comment);
  }
  zp(mnem, zpA, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'zp');
    const v=zpA&0xFF;
    this._b(op); this._b(v);
    this._li(a,[op,v],mnem,`$${hex2(v)}`,'zp',comment);
  }
  zpx(mnem, zpA, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'zpx');
    const v=zpA&0xFF;
    this._b(op); this._b(v);
    this._li(a,[op,v],mnem,`$${hex2(v)},X`,'zpx',comment);
  }
  zpy(mnem, zpA, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'zpy');
    const v=zpA&0xFF;
    this._b(op); this._b(v);
    this._li(a,[op,v],mnem,`$${hex2(v)},Y`,'zpy',comment);
  }
  abs(mnem, target, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'abs');
    this._b(op);
    if (typeof target==='string') {
      this.fixups.push({at:this.here(),type:'abs',label:target,addrOf:a});
      this._b(0); this._b(0);
      this._li(a,[op,0,0],mnem,target,'abs',comment,true);
    } else {
      const v=target&0xFFFF; this._w(v);
      this._li(a,[op,v&0xFF,v>>8],mnem,`$${hex4(v)}`,'abs',comment);
    }
  }
  abx(mnem, target, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'abx');
    this._b(op);
    if (typeof target==='string') {
      this.fixups.push({at:this.here(),type:'abs',label:target,addrOf:a});
      this._b(0); this._b(0);
      this._li(a,[op,0,0],mnem,`${target},X`,'abx',comment,true);
    } else {
      const v=target&0xFFFF; this._w(v);
      this._li(a,[op,v&0xFF,v>>8],mnem,`$${hex4(v)},X`,'abx',comment);
    }
  }
  aby(mnem, target, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'aby');
    this._b(op);
    if (typeof target==='string') {
      this.fixups.push({at:this.here(),type:'abs',label:target,addrOf:a});
      this._b(0); this._b(0);
      this._li(a,[op,0,0],mnem,`${target},Y`,'aby',comment,true);
    } else {
      const v=target&0xFFFF; this._w(v);
      this._li(a,[op,v&0xFF,v>>8],mnem,`$${hex4(v)},Y`,'aby',comment);
    }
  }
  inx(mnem, zpA, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'inx'), v=zpA&0xFF;
    this._b(op); this._b(v);
    this._li(a,[op,v],mnem,`($${hex2(v)},X)`,'inx',comment);
  }
  iny(mnem, zpA, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'iny'), v=zpA&0xFF;
    this._b(op); this._b(v);
    this._li(a,[op,v],mnem,`($${hex2(v)}),Y`,'iny',comment);
  }
  jsr(target, comment='') {
    const a=this.addr(), op=OPS.JSR.abs;
    this._b(op);
    if (typeof target==='string') {
      this.fixups.push({at:this.here(),type:'abs',label:target,addrOf:a});
      this._b(0); this._b(0);
      this._li(a,[op,0,0],'JSR',target,'abs',comment,true);
    } else {
      const v=target&0xFFFF; this._w(v);
      this._li(a,[op,v&0xFF,v>>8],'JSR',`$${hex4(v)}`,'abs',comment);
    }
  }
  jmp(target, comment='') {
    const a=this.addr(), op=OPS.JMP.abs;
    this._b(op);
    if (typeof target==='string') {
      this.fixups.push({at:this.here(),type:'abs',label:target,addrOf:a});
      this._b(0); this._b(0);
      this._li(a,[op,0,0],'JMP',target,'abs',comment,true);
    } else {
      const v=target&0xFFFF; this._w(v);
      this._li(a,[op,v&0xFF,v>>8],'JMP',`$${hex4(v)}`,'abs',comment);
    }
  }
  branch(mnem, lbl, comment='') {
    const a=this.addr(), op=this._getOp(mnem,'rel');
    this._b(op);
    const instrEnd = this.here()+1;
    this.fixups.push({at:this.here(),type:'rel',label:lbl,addrOf:a,instrEnd});
    this._b(0);
    this._li(a,[op,0],mnem,lbl,'rel',comment,true);
  }

  // ── Fixup resolution ─────────────────────────────────────────────────
  resolveFixups() {
    const errs = [];
    this.fixups.forEach(f => {
      // Supporta "label+N" per accesso a byte N-esimo di una variabile BSS
      let lbl = f.label, offset = 0;
      const plus = typeof lbl === 'string' ? lbl.indexOf('+') : -1;
      if (plus > 0) { offset = parseInt(lbl.slice(plus+1))||0; lbl = lbl.slice(0,plus); }
      if (!this.labels.has(lbl)) { errs.push(`Label non risolta: '${f.label}'`); return; }
      const tgt     = this.labels.get(lbl);
      const tgtAddr = this.base + tgt + offset;
      if (f.type==='lo' || f.type==='hi') {
        const tgtAddr = this.base + tgt + offset;
        const byte_ = f.type==='lo' ? (tgtAddr&0xFF) : ((tgtAddr>>8)&0xFF);
        this.buf[f.at] = byte_;
        const le = this.listing.find(l => l.fixup && l.addr===f.addrOf);
        if (le) { le.bytes[1]=byte_; le.op=`#$${hex2(byte_)}`; le.fixup=false; }
        return;
      }
      if (f.type==='abs') {
        this.buf[f.at]   = tgtAddr & 0xFF;
        this.buf[f.at+1] = (tgtAddr >> 8) & 0xFF;
        const le = this.listing.find(l => l.fixup && l.addr === f.addrOf);
        if (le) {
          le.bytes[1] = tgtAddr & 0xFF;
          le.bytes[2] = (tgtAddr >> 8) & 0xFF;
          le.op       = `$${hex4(tgtAddr)}`;
          le.fixup    = false;
        }
      } else { // rel
        const delta = tgt - f.instrEnd;
        if (delta < -128 || delta > 127) { errs.push(`Branch fuori range: '${f.label}' (Δ=${delta})`); return; }
        this.buf[f.at] = delta & 0xFF;
        const le = this.listing.find(l => l.fixup && l.addr === f.addrOf);
        if (le) { le.bytes[1] = delta & 0xFF; le.fixup = false; }
      }
    });
    return errs;
  }

  toBytes()   { return Uint8Array.from(this.buf); }
  byteCount() { return this.buf.length; }
}