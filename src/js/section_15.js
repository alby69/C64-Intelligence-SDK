// ═══════════════════════════════════════════════════════════════════════════
//  CODE GENERATOR — Fase 3 Passo 2
//  Visita l'AST e genera istruzioni MOS 6510 reali.
//  Convenzione: risultato byte-expr → registro A
//               risultato word-expr → lo in A, hi in planner.zpUtility.tmp2
//  Temporanei:  zpUtility.tmp, tmp2, ptr (già allocati da MemoryPlanner)
// ═══════════════════════════════════════════════════════════════════════════
class CodeGenerator {
  constructor(e, planner, semScope, ast) {
    this.e = e;
    this._ast = ast||null;
    this._inlineExpanding = false;
    this.p = planner;
    this.s = semScope;
    this.frameVars  = new Map();
    this.breakStack = [];
    this.contStack  = [];

    // Costruisci mappa param addr da funcLayouts (già allocati dal MemoryPlanner)
    this._funcParamAddrs = new Map();
    for (const [fname, layout] of planner.funcLayouts) {
      const params = layout.locals
        .filter(v => v.kind==='param' && v.addr != null)
        .map(v => ({name:v.name, addr:v.addr, type:v.type, size:v.size}));
      this._funcParamAddrs.set(fname, params);
    }
  }

  // ── Genera corpo di una funzione ─────────────────────────────────────────
  genFunc(fdecl) {
    this.frameVars = new Map();
    const fname  = fdecl.name;
    const layout = this.p.funcLayouts.get(fname) || {locals:[], ret:'void'};
    layout.locals.filter(v => !v.isArr).forEach(v => {
      // ZP var: usa addr numerico
      // BSS var (float mode, addr==null): usa label _fname_vname
      const label = (v.addr == null) ? `_${fname}_${v.name}` : null;
      this.frameVars.set(v.name, {
        name:  v.name,
        addr:  v.addr,          // null per BSS
        label: label,           // label BSS (es. _main_i)
        type:  v.type,
        size:  v.size,
        isZP:  v.addr != null && v.addr < 0x100
      });
    });
    if (fdecl.isRawIrq) {
      // Prologo raw IRQ: salva A, X, Y sullo stack hardware
      this.e.imp('PHA','save A');
      this.e.imp('TXA','A=X'); this.e.imp('PHA','save X');
      this.e.imp('TYA','A=Y'); this.e.imp('PHA','save Y');
    }
    this.emitBlock(fdecl.body);
    if (!this._inlineExpanding) {
      if (fdecl.isRawIrq) {
        this.e.imp('PLA','restore Y'); this.e.imp('TAY','→Y');
        this.e.imp('PLA','restore X'); this.e.imp('TAX','→X');
        this.e.imp('PLA','restore A');
        this.e.rti(`end ${fname} [RAW IRQ]`);
      } else if (fdecl.isIrq) {
        this.e.jmp(0xEA81, `end ${fname} [IRQ→$EA81]`);
      } else {
        this.e.imp('RTS', `end ${fname}`);
      }
    } // else: inline — nessun epilogo
  }

  // ── Lookup variabile: locale → globale ───────────────────────────────────
  _var(name) {
    if (this.frameVars.has(name)) return this.frameVars.get(name);
    const g = this.p.globals.find(g=>g.name===name);
    if (g && !g.name) g.name = name; // garantisci campo name
    return g || null;
  }
  _is16(node) {
    if (!node) return false;
    if (node.k==='Literal') return (node.value>255&&node.value<=65535) || node._type==='word';
    if (node.k==='Ident')   { const v=this._var(node.name); return v && v.size===2; }
    if (node.k==='BinaryOp') return this._is16(node.left)||this._is16(node.right);
    if (node._type) return ['word','int','uint'].includes(node._type) || isFixedType(node._type);
    return false;
  }
  _is32(node) {
    if (!node) return false;
    if (node.k==='Literal') return node.value > 65535 || node._type==='long' || node._type==='ulong' || node._type==='dword';
    if (node.k==='Ident')   { const v=this._var(node.name); return v && v.size===4; }
    if (node.k==='BinaryOp') return this._is32(node.left)||this._is32(node.right);
    if (node._type) return is32Type(node._type);
    return false;
  }

  // ── LDA / STA helpers — ZP (addr<$100), ABS (addr>=$100), BSS (label) ──
  _lbl(v) {
    // Ritorna il riferimento da usare in e.zp/e.abs: addr numerico o label stringa
    if (v.addr != null) return v.addr;
    return v.label || `_${v.name}`;
  }
  _ldVar(name, cmnt) {
    const e=this.e, v=this._var(name);
    if (!v) { e.imm('LDA',0,`!UNDEF:${name}`); return; }
    const ref=this._lbl(v);
    if (v.addr!=null && v.addr<0x100) e.zp ('LDA',ref,cmnt||name);
    else                              e.abs('LDA',ref,cmnt||name);
  }
  _stVar(name, cmnt) {
    const e=this.e, v=this._var(name);
    if (!v) return;
    const ref=this._lbl(v);
    if (v.addr!=null && v.addr<0x100) e.zp ('STA',ref,cmnt||name);
    else                              e.abs('STA',ref,cmnt||name);
  }

  // ── 16-bit init di una word var (lo, hi) ────────────────────────────────
  _initWord16(v, val16) {
    const e=this.e;
    const lo=val16&0xFF, hi=(val16>>8)&0xFF;
    const isZP  = v.addr!=null && v.addr<0x100;
    const store = (off, cmt) => {
      if (v.addr!=null) {
        if (isZP) e.zp ('STA', v.addr+off, cmt);
        else      e.abs('STA', v.addr+off, cmt);
      } else {
        e.abs('STA', (v.label||`_${v.name}`) + (off?`+${off}`:''), cmt);
      }
    };
    e.imm('LDA',lo,`${v.name}_lo=$${hex2(lo)}`); store(0, `${v.name} lo`);
    e.imm('LDA',hi,`${v.name}_hi=$${hex2(hi)}`); store(1, `${v.name} hi`);
  }

  // ── 32-bit init di una long var (b0..b3) ────────────────────────────────
  _initDWord32(v, val32) {
    const e=this.e;
    // Usa Number: JS mantiene 32 bit interi sicuri
    const b = [(val32>>>0)&0xFF, (val32>>>8)&0xFF, (val32>>>16)&0xFF, (val32>>>24)&0xFF];
    const store = (off, cmt) => {
      if (v.addr!=null) {
        if (v.addr+off < 0x100) e.zp ('STA', v.addr+off, cmt);
        else                    e.abs('STA', v.addr+off, cmt);
      } else {
        e.abs('STA', (v.label||`_${v.name}`) + (off?`+${off}`:''), cmt);
      }
    };
    const hex8 = n => n.toString(16).toUpperCase().padStart(8,'0');
    e.imm('LDA',b[0],`${v.name}=$${hex8(val32)} b0`); store(0);
    e.imm('LDA',b[1],`${v.name} b1`);                  store(1);
    e.imm('LDA',b[2],`${v.name} b2`);                  store(2);
    e.imm('LDA',b[3],`${v.name} b3`);                  store(3);
  }

  // ── Store A (byte) into target lvalue ───────────────────────────────────
  _store(target) {
    const e=this.e, p=this.p;
    if (target.k==='Ident') {
      this._stVar(target.name);
    } else if (target.k==='ArrayAccess') {
      const v=this._var(target.name);
      const base=v?v.addr:null;
      if (target.idx.k==='Literal') {
        const off=target.idx.value;
        if (base!=null) {
          const ea=base+off;
          if (ea<0x100) e.zp ('STA',ea,`${target.name}[${off}]`);
          else          e.abs('STA',ea,`${target.name}[${off}]`);
        } else {
          const lbl=(v&&v.label)||`_${target.name}`;
          const ref=off>0?`${lbl}+${off}`:lbl;
          e.abs('STA',ref,`${target.name}[${off}]`);
        }
      } else {
        e.zp('STA',p.zpUtility.tmp,'save val');
        this.evalExpr(target.idx);
        e.imp('TAX','idx→X');
        e.zp('LDA',p.zpUtility.tmp,'restore val');
        if (base!=null&&base<0x100) e.zpx('STA',base,`${target.name}[X]`);
        else if (base!=null) e.abx('STA',base,`${target.name}[X]`);
        else e.abx('STA',`_${target.name}`,`${target.name}[X]`);
      }
    }
  }

  // ── Carica un'espressione "indirizzo word" nel puntatore ZP ─────────────
  _evalWordToPtr(expr) {
    const e=this.e, p=this.p;
    const ptr=p.zpUtility.ptr;
    if (expr.k==='Literal') {
      const v=expr.value&0xFFFF;
      e.imm('LDA',v&0xFF,'ptr_lo'); e.zp('STA',ptr);
      e.imm('LDA',(v>>8)&0xFF,'ptr_hi'); e.zp('STA',ptr+1);
    } else if (expr.k==='Ident') {
      const vi=this._var(expr.name);
      if (vi&&vi.size>=2&&vi.addr!=null) {
        e.zp('LDA',vi.addr,`${expr.name}_lo`); e.zp('STA',ptr);
        e.zp('LDA',vi.addr+1,`${expr.name}_hi`); e.zp('STA',ptr+1);
      } else if (vi&&vi.addr!=null) {
        e.zp('LDA',vi.addr,`${expr.name}_lo`); e.zp('STA',ptr);
        e.imm('LDA',0,'hi=0'); e.zp('STA',ptr+1);
      } else {
        e.imm('LDA',0); e.zp('STA',ptr);
        e.imm('LDA',0); e.zp('STA',ptr+1);
      }
    } else if (expr.k==='BinaryOp'&&expr.op==='+') {
      // 16-bit ptr = left + right
      this._evalWordToPtr(expr.left);
      const right=expr.right;
      if (right.k==='Literal') {
        const rv=right.value&0xFFFF;
        e.imp('CLC');
        e.zp('LDA',ptr); e.imm('ADC',rv&0xFF); e.zp('STA',ptr);
        e.zp('LDA',ptr+1); e.imm('ADC',(rv>>8)&0xFF); e.zp('STA',ptr+1);
      } else if (right.k==='Ident') {
        const vi=this._var(right.name);
        if (vi&&vi.size>=2&&vi.addr!=null) {
          // 16+16
          e.imp('CLC');
          e.zp('LDA',ptr); e.zp('ADC',vi.addr); e.zp('STA',ptr);
          e.zp('LDA',ptr+1); e.zp('ADC',vi.addr+1); e.zp('STA',ptr+1);
        } else if (vi&&vi.addr!=null) {
          // 16+8 (zero-extend)
          e.imp('CLC');
          e.zp('LDA',ptr); e.zp('ADC',vi.addr); e.zp('STA',ptr);
          e.zp('LDA',ptr+1); e.imm('ADC',0); e.zp('STA',ptr+1);
        }
      } else {
        // Eval byte expr, add to ptr
        this.evalExpr(right);
        e.zp('STA',p.zpUtility.tmp,'byte offset');
        e.imp('CLC');
        e.zp('LDA',ptr); e.zp('ADC',p.zpUtility.tmp); e.zp('STA',ptr);
        e.zp('LDA',ptr+1); e.imm('ADC',0); e.zp('STA',ptr+1);
      }
    } else {
      // Fallback: eval byte, zero-extend
      this.evalExpr(expr);
      e.zp('STA',ptr); e.imm('LDA',0); e.zp('STA',ptr+1);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  EXPRESSION EVALUATOR — result in A (byte)
  // ═══════════════════════════════════════════════════════════════════════
  evalExpr(node) {
    if (!node) return;
    const e=this.e, p=this.p;
    switch(node.k) {
      case 'Literal':
        e.imm('LDA',node.value&0xFF,`#${node.raw||node.value}`);
        break;
      case 'Ident':
        this._ldVar(node.name);
        break;
      case 'ArrayAccess': {
        const v=this._var(node.name), base=v?v.addr:null;
        if (node.idx.k==='Literal') {
          const off=node.idx.value;
          if (base!=null) {
            // ZP o abs con indirizzo numerico noto
            const ea=base+off;
            if (ea<0x100) e.zp ('LDA',ea,`${node.name}[${off}]`);
            else          e.abs('LDA',ea,`${node.name}[${off}]`);
          } else {
            // BSS array (addr=null): usa label+offset  → risolto da fixup
            const lbl=(v&&v.label)||`_${node.name}`;
            const ref=off>0?`${lbl}+${off}`:lbl;
            e.abs('LDA',ref,`${node.name}[${off}]`);
          }
        } else {
          this.evalExpr(node.idx); e.imp('TAX','idx→X');
          if (base!=null&&base<0x100) e.zpx('LDA',base,`${node.name}[X]`);
          else if (base!=null)        e.abx('LDA',base,`${node.name}[X]`);
          else                        e.abx('LDA',`_${node.name}`,`${node.name}[X]`);
        }
        break;
      }
      case 'BinaryOp': {
        // ── Constant folding: entrambi gli operandi sono letterali ──────
        const lL=node.left, lR=node.right;
        if (lL.k==='Literal' && lR.k==='Literal') {
          const a=lL.value, b=lR.value;
          let res=0;
          switch(node.op){
            case '+': res=(a+b)&0xFFFF; break;
            case '-': res=(a-b)&0xFFFF; break;
            case '*': res=(a*b)&0xFFFF; break;
            case '/': res=b?Math.trunc(a/b)&0xFFFF:0; break;
            case '%': res=b?(a%b)&0xFF:0; break;
            case '&': res=(a&b)&0xFFFF; break;
            case '|': res=(a|b)&0xFFFF; break;
            case '^': res=(a^b)&0xFFFF; break;
            case '<<':res=(a<<(b&7))&0xFFFF; break;
            case '>>':res=(a>>(b&7))&0xFFFF; break;
            case '==':res=a===b?1:0; break;
            case '!=':res=a!==b?1:0; break;
            case '<': res=a<b?1:0;  break;
            case '>': res=a>b?1:0;  break;
            case '<=':res=a<=b?1:0; break;
            case '>=':res=a>=b?1:0; break;
            default:  res=0;
          }
          e.imm('LDA',res&0xFF,`CF:${a}${node.op}${b}=${res}`);
          break;
        }
        // ── Partial folding: un operando è letterale 0 o 1 ─────────────
        if (lR.k==='Literal') {
          if (lR.value===0) {
            if (node.op==='+' || node.op==='-' || node.op==='|' || node.op==='^') {
              this.evalExpr(lL); break; // x+0, x-0, x|0, x^0 → x
            }
            if (node.op==='*') { e.imm('LDA',0,'×0=0'); break; }
            if (node.op==='&') { e.imm('LDA',0,'&0=0'); break; }
            if (node.op==='<<' || node.op==='>>') { this.evalExpr(lL); break; } // x<<0=x
          }
          if (lR.value===1 && node.op==='*') { this.evalExpr(lL); break; } // x*1=x
          if (lR.value===1 && node.op==='>>') { this.evalExpr(lL); e.acc('LSR'); break; }
          if (lR.value===1 && node.op==='<<') { this.evalExpr(lL); e.acc('ASL'); break; }
          if (lR.value===2 && node.op==='*')  { this.evalExpr(lL); e.acc('ASL'); break; }
          if (lR.value===4 && node.op==='*')  { this.evalExpr(lL); e.acc('ASL'); e.acc('ASL'); break; }
          if (lR.value===8 && node.op==='*')  { this.evalExpr(lL); e.acc('ASL'); e.acc('ASL'); e.acc('ASL'); break; }
        }
        if (lL.k==='Literal') {
          if (lL.value===0 && node.op==='+') { this.evalExpr(lR); break; } // 0+x=x
          if (lL.value===0 && node.op==='-') { // 0-x = NEG x
            this.evalExpr(lR); e.imm('EOR',0xFF); e.imp('CLC'); e.imm('ADC',1,'NEG'); break;
          }
          if (lL.value===1 && node.op==='*') { this.evalExpr(lR); break; } // 1*x=x
        }
        // ── Float arithmetic: usa routines KERNAL se un operando è float ──
        const floatL = (node.left._type==='float')  || (node.left.k==='Literal'  && node.left.kind==='float');
        const floatR = (node.right._type==='float') || (node.right.k==='Literal' && node.right.kind==='float');
        if ((floatL||floatR) && ['+','-','*','/','^'].includes(op)) {
          this._evalFloatBinOp(node);
          this._floatGetResult(); // FAC1 → A (byte troncato)
          break;
        }
        this._evalBinOp(node); break;
      }
      case 'UnaryOp':    this._evalUnary(node); break;
      case 'PostfixOp':  this._evalPostfix(node); break;
      case 'Cast': {
        // Cast fp→byte: estrae parte intera (hi byte)
        if (!isFixedType(node.type) && isFixedType(node.expr._type||'')) {
          const fpVar = node.expr.k==='Ident' ? this._var(node.expr.name) : null;
          if (fpVar && fpVar.addr!=null && fpVar.size>=2) {
            if(fpVar.addr+1<0x100) e.zp('LDA',fpVar.addr+1,`int(${fpVar.name})`);
            else e.abs('LDA',fpVar.addr+1,`int(${fpVar.name})`);
          } else { this.evalExpr(node.expr); } // fallback
        } else {
          this.evalExpr(node.expr); // byte truncation implicita; int→fp gestita da Assign/VarDecl
        }
        break;
      }
      case 'Call':       this._evalCall(node); break;
      case 'Assign':
        this.evalExpr(node.value);
        this._store(node.target);
        break;
      default:
        e.imm('LDA',0,`/* ${node.k} */`);
    }
  }

  // ── Operatori binari ──────────────────────────────────────────────────
  _evalBinOp(node) {
    const e=this.e, p=this.p;
    const op=node.op;
    const tmp=p.zpUtility.tmp, tmp2=p.zpUtility.tmp2;

    if (['==','!=','<','>','<=','>='].includes(op)) { this._evalCmp(node); return; }
    if (op==='&&') {
      const lF=e.uniq('_andF'), lE=e.uniq('_andE');
      this.evalExpr(node.left); e.imm('CMP',0); e.branch('BEQ',lF,'&&:L=0');
      this.evalExpr(node.right);e.imm('CMP',0); e.branch('BEQ',lF,'&&:R=0');
      e.imm('LDA',1,'true'); e.jmp(lE);
      e.label(lF); e.imm('LDA',0,'false'); e.label(lE); return;
    }
    if (op==='||') {
      const lT=e.uniq('_orT'), lE=e.uniq('_orE');
      this.evalExpr(node.left); e.imm('CMP',0); e.branch('BNE',lT,'||:L≠0');
      this.evalExpr(node.right);e.imm('CMP',0); e.branch('BNE',lT,'||:R≠0');
      e.imm('LDA',0,'false'); e.jmp(lE);
      e.label(lT); e.imm('LDA',1,'true'); e.label(lE); return;
    }
    if (op==='-') {
      this.evalExpr(node.right); e.zp('STA',tmp,'sub:right');
      this.evalExpr(node.left);
      e.imp('SEC'); e.zp('SBC',tmp,'A=left-right'); return;
    }
    if (op==='*') {
      if (node.right.k==='Literal') { this.evalExpr(node.left); this._mulImm(node.right.value&0xFF); }
      else if (node.left.k==='Literal') { this.evalExpr(node.right); this._mulImm(node.left.value&0xFF); }
      else {
        this.evalExpr(node.right); e.zp('STA',tmp2,'mul:R');
        this.evalExpr(node.left);  e.zp('STA',tmp,'mul:L');
        this._mulZP(tmp,tmp2);
      }
      // Auto-rescaling fixed-point: se ENTRAMBI gli operandi sono tipi fp,
      // il prodotto raw va diviso per la scala (shift >> frac bit).
      // Se solo uno e' fp (es. vel * 2), l'intero e' un coefficiente puro:
      // nessun rescaling - il risultato e' gia' nel range corretto.
      const lt = node.left._type || '';
      const rt = node.right._type || '';
      if (isFixedType(lt) && isFixedType(rt)) {
        const frac = fpFracBits(node._type || lt);
        for (let i = 0; i < frac; i++) e.acc('LSR', i === 0 ? `fp*fp rescale >>${frac}` : '');
      }
      return;
    }
    if (op==='/') {
      this.evalExpr(node.left);  e.zp('STA',tmp,'div:L');
      this.evalExpr(node.right); e.zp('STA',tmp2,'div:R');
      this._divZP(tmp,tmp2); return;
    }
    if (op==='%') {
      this.evalExpr(node.left);  e.zp('STA',tmp,'mod:L');
      this.evalExpr(node.right); e.zp('STA',tmp2,'mod:R');
      this._modZP(tmp,tmp2); return;
    }
    if (op==='<<') {
      this.evalExpr(node.left);
      if (node.right.k==='Literal') { let n=node.right.value&7; for(let i=0;i<n;i++) e.acc('ASL'); }
      else {
        e.zp('STA',tmp);
        this.evalExpr(node.right); e.imp('TAX','shift cnt');
        const lT=e.uniq('_shlT'),lE=e.uniq('_shlE');
        e.imm('CPX',0); e.branch('BEQ',lE);
        e.label(lT); e.zp('ASL',tmp); e.imp('DEX'); e.branch('BNE',lT);
        e.label(lE); e.zp('LDA',tmp);
      }
      return;
    }
    if (op==='>>') {
      this.evalExpr(node.left);
      if (node.right.k==='Literal') { let n=node.right.value&7; for(let i=0;i<n;i++) e.acc('LSR'); }
      else {
        e.zp('STA',tmp);
        this.evalExpr(node.right); e.imp('TAX','shift cnt');
        const lT=e.uniq('_shrT'),lE=e.uniq('_shrE');
        e.imm('CPX',0); e.branch('BEQ',lE);
        e.label(lT); e.zp('LSR',tmp); e.imp('DEX'); e.branch('BNE',lT);
        e.label(lE); e.zp('LDA',tmp);
      }
      return;
    }
    // Commutative: +, &, |, ^
    this.evalExpr(node.right); e.zp('STA',tmp,`${op}:R`);
    this.evalExpr(node.left);
    switch(op) {
      case '+': e.imp('CLC'); e.zp('ADC',tmp,'L+R'); break;
      case '&': e.zp('AND',tmp,'L&R'); break;
      case '|': e.zp('ORA',tmp,'L|R'); break;
      case '^': e.zp('EOR',tmp,'L^R'); break;
      default:  e.imm('LDA',0,`/* ${op} */`);
    }
  }

  // ── Confronto → risultato bool in A ─────────────────────────────────────
  _evalCmp(node) {
    const e=this.e, tmp=this.p.zpUtility.tmp;
    const lT=e.uniq('_cmpT'), lE=e.uniq('_cmpE');
    this.evalExpr(node.right); e.zp('STA',tmp,'cmp:R');
    this.evalExpr(node.left);  e.zp('CMP',tmp,'cmp:L vs R');
    this._branchCmpTrue(node.op, lT);
    e.imm('LDA',0,'false'); e.jmp(lE);
    e.label(lT); e.imm('LDA',1,'true'); e.label(lE);
  }
  _branchCmpTrue(op, label) {
    const e=this.e;
    switch(op) {
      case '==': e.branch('BEQ',label); break;
      case '!=': e.branch('BNE',label); break;
      case '<':  e.branch('BCC',label); break;
      case '>=': e.branch('BCS',label); break;
      case '>': { const lS=e.uniq('_gtS'); e.branch('BEQ',lS); e.branch('BCS',label); e.label(lS); break; }
      case '<=': e.branch('BCC',label); e.branch('BEQ',label); break;
    }
  }

  // ── Operatori unari ──────────────────────────────────────────────────────
  _evalUnary(node) {
    const e=this.e;
    this.evalExpr(node.operand);
    switch(node.op) {
      case '-': e.imm('EOR',0xFF); e.imp('CLC'); e.imm('ADC',1); break;
      case '~': e.imm('EOR',0xFF); break;
      case '!': {
        const lT=e.uniq('_notT'),lE=e.uniq('_notE');
        e.imm('CMP',0); e.branch('BEQ',lT);
        e.imm('LDA',0); e.jmp(lE);
        e.label(lT); e.imm('LDA',1); e.label(lE); break;
      }
      case 'pre++': case 'pre--': {
        const vn=node.operand.name, vi=this._var(vn);
        if (vi&&vi.addr!=null) {
          const ins=node.op==='pre++'?'INC':'DEC';
          if(vi.addr<0x100){e.zp(ins,vi.addr,node.op+vn);e.zp('LDA',vi.addr,vn);}
          else{e.abs(ins,vi.addr,node.op+vn);e.abs('LDA',vi.addr,vn);}
        }
        break;
      }
    }
  }
  _evalPostfix(node) {
    const e=this.e;
    if (node.operand.k!=='Ident') { this.evalExpr(node.operand); return; }
    const vn=node.operand.name, vi=this._var(vn);
    this._ldVar(vn); e.imp('PHA','save pre');
    if (vi&&vi.addr!=null) {
      const ins=node.op==='++'?'INC':'DEC';
      if(vi.addr<0x100) e.zp(ins,vi.addr,`${vn}${node.op}`);
      else e.abs(ins,vi.addr,`${vn}${node.op}`);
    }
    e.imp('PLA','restore pre');
  }

  // ── Moltiplicazione: A × imm → A ────────────────────────────────────────
  _mulImm(n) {
    const e=this.e, tmp=this.p.zpUtility.tmp;
    if (n===0){e.imm('LDA',0,'×0=0');return;}
    if (n===1) return;
    if ((n&(n-1))===0) {let k=Math.log2(n)|0; for(let i=0;i<k;i++) e.acc('ASL',i===0?`×${n}`:''); return;}
    // Loop: counter in X, accumulate
    e.zp('STA',tmp,`mul×${n}`);
    const lT=e.uniq('_mliT');
    e.imm('LDX',n,`count=${n}`); e.imm('LDA',0,'acc=0');
    e.label(lT);
    e.imp('CLC'); e.zp('ADC',tmp,'acc+=val'); e.imp('DEX'); e.branch('BNE',lT,'loop');
  }
  // Moltiplicazione: *mulA × *cntA → A (8×8→8 bit, overflow ignorato)
  _mulZP(mulA, cntA) {
    const e=this.e;
    const lT=e.uniq('_mulT'), lE=e.uniq('_mulE');
    e.zp('LDA',cntA,'mul:cnt'); e.imm('CMP',0); e.branch('BEQ',lE,'×0=0');
    e.imp('TAX','X=cnt'); e.imm('LDA',0,'acc=0');
    e.label(lT); e.imp('CLC'); e.zp('ADC',mulA,'acc+=mul'); e.imp('DEX'); e.branch('BNE',lT,'loop');
    e.label(lE);
  }
  // Divisione: *numA / *denA → A, resto → *numA
  _divZP(numA, denA) {
    const e=this.e;
    const lT=e.uniq('_divT'), lE=e.uniq('_divE');
    e.zp('LDA',numA,'div:num'); e.imm('LDX',0,'quot=0');
    e.label(lT); e.imp('SEC'); e.zp('SBC',denA,'try sub');
    e.branch('BCC',lE,'borrow=done'); e.imp('INX','quot++'); e.branch('BCS',lT,'loop');
    e.label(lE); e.zp('ADC',denA,'restore rem'); e.zp('STA',numA,'save rem'); e.imp('TXA','quot→A');
  }
  // Modulo: *numA % *denA → A
  _modZP(numA, denA) {
    const e=this.e;
    const lT=e.uniq('_modT'), lE=e.uniq('_modE');
    e.zp('LDA',numA,'mod:num');
    e.label(lT); e.imp('SEC'); e.zp('SBC',denA,'try sub');
    e.branch('BCC',lE,'borrow=done'); e.branch('BCS',lT,'loop');
    e.label(lE); e.zp('ADC',denA,'restore rem');  // A = remainder
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  STATEMENT EMITTER
  // ═══════════════════════════════════════════════════════════════════════
  emitBlock(block) {
    if (!block) return;
    if (block.k==='Block') block.stmts.forEach(s=>s&&this.emitStmt(s));
    else this.emitStmt(block);
  }

  emitStmt(node) {
    if (!node) return;
    const e=this.e, p=this.p;
    switch(node.k) {
      case 'VarDecl': {
        const vi=this._var(node.name);
        if (!vi) break;
        // ── Float: valuta init → FAC1 → MOVMF in BSS ───────────────────
        if (vi.type === 'float') {
          if (node.init) {
            this._evalFloatExprToFAC1(node.init);
            this._floatFAC1ToVar(this._floatGetLabel(vi), node.name);
          }
          break;
        }
        if (vi.size===4) {
          // ── 32-bit long/ulong/dword ────────────────────────
          const st32 = (o,c) => { if(vi.addr!=null){ if(vi.addr+o<0x100) e.zp('STA',vi.addr+o,c); else e.abs('STA',vi.addr+o,c); } else e.abs('STA',(vi.label||`_${vi.name}`)+(o?`+${o}`:''),c); };
          if (node.init && node.init.k==='Literal') {
            this._initDWord32(vi, node.init.value>>>0);
          } else if (node.init) {
            this.evalExpr(node.init); // A = byte basso
            st32(0,`${node.name}_b0`); e.imm('LDA',0);
            st32(1,`${node.name}_b1`); st32(2,`${node.name}_b2`); st32(3,`${node.name}_b3`);
          } else {
            this._initDWord32(vi, 0);
          }
        } else if (vi.size>=2) {
          // Variabile word/int/fp: init a 16 bit
          let val16=0;
          const fpT = isFixedType(node.type) ? node.type : null;
          if (node.init&&node.init.k==='Literal') {
            val16 = fpT
              ? (node.init.kind==='hex'||node.init.kind==='bin'
                  ? node.init.value & 0xFFFF                              // hex/bin → raw Q8.8 word
                  : (Math.round(node.init.value * fpScale(fpT))) & 0xFFFF)// int/float → scala
              : node.init.value & 0xFFFF;
          } else if (node.init) {
            this.evalExpr(node.init);
            if (fpT) {
              // int expr → fp: sposta A in hi byte, 0 in lo byte
              if(vi.addr<0x100) e.zp('STA',vi.addr+1,`${node.name}_hi`);
              else e.abs('STA',vi.addr+1,`${node.name}_hi`);
              e.imm('LDA',0);
              if(vi.addr<0x100) e.zp('STA',vi.addr,`${node.name}_lo=0`);
              else e.abs('STA',vi.addr,`${node.name}_lo=0`);
            } else {
              e.zp('STA',vi.addr,`${node.name}_lo`); e.imm('LDA',0); e.zp('STA',vi.addr+1,`${node.name}_hi`);
            }
            break;
          }
          this._initWord16(vi, val16);
        } else {
          if (node.init) this.evalExpr(node.init);
          else e.imm('LDA',0,`${node.name}=0`);
          this._stVar(node.name,`init ${node.name}`);
        }
        // Init array: poke elementi
        if (node.isArr && node.arrInit) {
          const base=vi.addr;
          if (base!=null) {
            node.arrInit.forEach((el,i)=>{
              if (el.k==='Literal') {
                e.imm('LDA',el.value&0xFF,`arr[${i}]`);
                const ea=base+i;
                if (ea<0x100) e.zp('STA',ea); else e.abs('STA',ea);
              }
            });
          }
        }
        break;
      }
      case 'Assign': {
        const target=node.target, val=node.value;
        const vi=target.k==='Ident'?this._var(target.name):null;
        const fpT = vi && isFixedType(vi.type) ? vi.type : null;
        // ── Float target: valuta RHS → FAC1 → MOVMF ─────────────────────
        if (vi && vi.type === 'float') {
          this._evalFloatExprToFAC1(val);
          this._floatFAC1ToVar(this._floatGetLabel(vi), vi.name);
          break;
        }
        if (vi && vi.size===4) {
          // ── Target 32-bit ────────────────────────────────────
          this._emitDWord32Assign(vi, val);
        } else if (vi&&vi.size>=2) {
          // Target è word/int/fp: gestione 16-bit corretta
          if (val.k==='BinaryOp') {
            this._emitWord16Assign(vi, val);
          } else if (val.k==='Literal') {
            // scala il letterale se il target è fp (ma non hex/bin: sono raw word)
            const raw = fpT
              ? (val.kind==='hex'||val.kind==='bin'
                  ? val.value & 0xFFFF                              // hex/bin → raw Q8.8 word
                  : (Math.round(val.value * fpScale(fpT))) & 0xFFFF)// int/float → scala
              : val.value & 0xFFFF;
            this._initWord16(vi, raw);
          } else if (val.k==='Ident') {
            const src=this._var(val.name);
            if (src&&src.size>=2&&src.addr!=null) {
              // word/fp = word/fp: copia entrambi i byte
              const ldSrc = src.addr<0x100 ? (a=>e.zp('LDA',a)) : (a=>e.abs('LDA',a));
              const stDst = vi.addr<0x100  ? (a=>e.zp('STA',a)) : (a=>e.abs('STA',a));
              ldSrc(src.addr);   stDst(vi.addr);
              ldSrc(src.addr+1); stDst(vi.addr+1);
            } else if (src&&src.addr!=null) {
              if (fpT) {
                // fp = byte: scala — byte va in hi, lo=0
                if(src.addr<0x100) e.zp('LDA',src.addr); else e.abs('LDA',src.addr);
                if(vi.addr+1<0x100) e.zp('STA',vi.addr+1,`${vi.name}_hi`); else e.abs('STA',vi.addr+1,`${vi.name}_hi`);
                e.imm('LDA',0);
                if(vi.addr<0x100) e.zp('STA',vi.addr,`${vi.name}_lo=0`); else e.abs('STA',vi.addr,`${vi.name}_lo=0`);
              } else {
                // word = byte: zero-extend
                if(src.addr<0x100) e.zp('LDA',src.addr); else e.abs('LDA',src.addr);
                if(vi.addr<0x100)  e.zp('STA',vi.addr);  else e.abs('STA',vi.addr);
                e.imm('LDA',0);
                if(vi.addr+1<0x100) e.zp('STA',vi.addr+1); else e.abs('STA',vi.addr+1);
              }
            } else {
              this.evalExpr(val); this._stVar(vi.name,'w=b');
              e.imm('LDA',0); if(vi.addr+1<0x100) e.zp('STA',vi.addr+1); else e.abs('STA',vi.addr+1);
            }
          } else if (val.k==='UnaryOp' && val.op==='-' && vi.addr!=null) {
            // ── sq8_8 = -expr: negazione 16-bit (complemento a due) ─────────
            const srcNode=val.operand;
            const srcVar=srcNode.k==='Ident'?this._var(srcNode.name):null;
            if (srcVar&&srcVar.size>=2&&srcVar.addr!=null) {
              if (srcVar.name===vi.name) {
                // vy = -vy: negazione in-place
                this._negWord16InPlace(vi);
              } else {
                // vi = -src: copia src in vi, poi nega in-place
                const ldS=srcVar.addr<0x100?(a=>e.zp('LDA',a)):(a=>e.abs('LDA',a));
                const stD=vi.addr<0x100?(a=>e.zp('STA',a)):(a=>e.abs('STA',a));
                ldS(srcVar.addr);   stD(vi.addr);
                ldS(srcVar.addr+1); stD(vi.addr+1);
                this._negWord16InPlace(vi);
              }
            } else {
              // Fallback: espressione byte → nega come 8-bit e zero-extend hi
              this.evalExpr(srcNode||val);
              e.imm('EOR',0xFF,'neg8 lo'); e.imp('CLC'); e.imm('ADC',1);
              if(vi.addr<0x100)e.zp('STA',vi.addr,`${vi.name}_lo`);else e.abs('STA',vi.addr,`${vi.name}_lo`);
              e.imm('LDA',0);
              if(vi.addr+1<0x100)e.zp('STA',vi.addr+1,`${vi.name}_hi=0`);else e.abs('STA',vi.addr+1,`${vi.name}_hi=0`);
            }
          } else {
            // Cast, Call, ecc.: eval produce A (byte)
            if (fpT) {
              // int→fp: A va in hi byte, lo=0
              this.evalExpr(val);
              if(vi.addr+1<0x100) e.zp('STA',vi.addr+1,`${vi.name}_hi`); else e.abs('STA',vi.addr+1,`${vi.name}_hi`);
              e.imm('LDA',0);
              if(vi.addr<0x100) e.zp('STA',vi.addr,`${vi.name}_lo=0`); else e.abs('STA',vi.addr,`${vi.name}_lo=0`);
            } else {
              this.evalExpr(val); this._stVar(vi.name,'w_lo');
              e.imm('LDA',0);
              if(vi.addr+1<0x100) e.zp('STA',vi.addr+1,'w_hi=0'); else e.abs('STA',vi.addr+1,'w_hi=0');
            }
          }
        } else {
          this.evalExpr(val);
          this._store(target);
        }
        break;
      }
      case 'If': {
        const lElse=e.uniq('_else'), lFi=e.uniq('_fi');
        this._branchIfFalse(node.cond, lElse);
        this.emitBlock(node.then);
        if (node.else) { e.jmp(lFi,'skip else'); e.label(lElse); this.emitBlock(node.else); e.label(lFi); }
        else e.label(lElse);
        break;
      }
      case 'While': {
        const lT=e.uniq('_whlT'), lE=e.uniq('_whlE');
        this.breakStack.push(lE); this.contStack.push(lT);
        e.label(lT);
        const inf=node.cond.k==='Literal'&&node.cond.value!==0;
        if (!inf) this._branchIfFalse(node.cond, lE);
        this.emitBlock(node.body);
        e.jmp(lT,'loop'); e.label(lE);
        this.breakStack.pop(); this.contStack.pop();
        break;
      }
      case 'DoWhile': {
        const lT=e.uniq('_doT'), lE=e.uniq('_doE');
        this.breakStack.push(lE); this.contStack.push(lT);
        e.label(lT); this.emitBlock(node.body);
        this._branchIfTrue(node.cond, lT); e.label(lE);
        this.breakStack.pop(); this.contStack.pop();
        break;
      }
      case 'For': {
        const lT=e.uniq('_forT'), lE=e.uniq('_forE'), lI=e.uniq('_forI');
        this.breakStack.push(lE); this.contStack.push(lI);
        if (node.init) this.emitStmt(node.init);
        e.label(lT);
        if (node.cond) this._branchIfFalse(node.cond, lE);
        this.emitBlock(node.body);
        e.label(lI);
        if (node.incr) { const vi=node.incr.k==='Assign'?this._var(node.incr.target?.name):null;
          if (vi&&vi.size===4&&node.incr.k==='Assign') this._emitDWord32Assign(vi,node.incr.value);
          else if (vi&&vi.size>=2&&node.incr.k==='Assign') this._emitWord16Assign(vi,node.incr.value);
          else this.evalExpr(node.incr); }
        e.jmp(lT,'for'); e.label(lE);
        this.breakStack.pop(); this.contStack.pop();
        break;
      }
      case 'Return':
        if (node.value) this.evalExpr(node.value);
        e.imp('RTS','return');
        break;
      case 'Break':   { const l=this.breakStack[this.breakStack.length-1]; if(l) e.jmp(l,'break'); break; }
      case 'Continue':{ const l=this.contStack[this.contStack.length-1];   if(l) e.jmp(l,'continue'); break; }
      case 'Block':     this.emitBlock(node); break;
      default:          this.evalExpr(node); break;
    }
  }

  // ── 16-bit assignment helper: vi = BinaryOp ────────────────────────────
  _emitWord16Assign(vi, binOp) {
    const e=this.e, op=binOp.op;
    const fpT = isFixedType(vi.type) ? vi.type : null;
    if (op==='+'||op==='-') {
      const left=binOp.left, right=binOp.right;
      // Detect simple: vi = vi +/- literal
      const leftIsVar=left.k==='Ident'&&left.name===vi.name;
      const rightLit =right.k==='Literal';
      if (leftIsVar&&rightLit) {
        // Scala il letterale se fp e il rhs sembra un intero (non già in formato raw)
        // Convenzione: usa il letterale raw — l'utente scrive $0080 per 0.5 in Q8.8
        const rv=right.value&0xFFFF;
        if (op==='+') {
          e.imp('CLC');
          e.zp('LDA',vi.addr,`${vi.name}_lo`); e.imm('ADC',rv&0xFF); e.zp('STA',vi.addr);
          e.zp('LDA',vi.addr+1,`${vi.name}_hi`); e.imm('ADC',(rv>>8)&0xFF); e.zp('STA',vi.addr+1);
        } else {
          e.imp('SEC');
          e.zp('LDA',vi.addr); e.imm('SBC',rv&0xFF); e.zp('STA',vi.addr);
          e.zp('LDA',vi.addr+1); e.imm('SBC',(rv>>8)&0xFF); e.zp('STA',vi.addr+1);
        }
        return;
      }
    }
    // Fallback per op+right non-letterale: gestisci word+byte e word+word
    // Caso: vi = vi OP right (dove right è una variabile/espressione byte)
    const lIsVar = binOp.left.k==='Ident'&&binOp.left.name===vi.name;
    const rVar   = binOp.right.k==='Ident'?this._var(binOp.right.name):null;
    if (lIsVar && (binOp.op==='+'||binOp.op==='-') && rVar && rVar.size===1 && vi.addr!=null) {
      // word = word +/- byte_var (es. i = i + step)
      this.evalExpr(binOp.right); // A = byte
      const e=this.e;
      if (binOp.op==='+') {
        e.imp('CLC');
        if(vi.addr<0x100) e.zp('ADC',vi.addr); else e.abs('ADC',vi.addr);
        if(vi.addr<0x100) e.zp('STA',vi.addr); else e.abs('STA',vi.addr);
        e.imm('LDA',0); if(vi.addr+1<0x100) e.zp('ADC',vi.addr+1); else e.abs('ADC',vi.addr+1);
        if(vi.addr+1<0x100) e.zp('STA',vi.addr+1); else e.abs('STA',vi.addr+1);
      } else {
        e.imp('SEC');
        if(vi.addr<0x100) e.zp('STA',this.p.zpUtility.tmp); // save rhs
        const rhs=this.p.zpUtility.tmp;
        if(vi.addr<0x100) e.zp('LDA',vi.addr); else e.abs('LDA',vi.addr);
        e.zp('SBC',rhs);
        if(vi.addr<0x100) e.zp('STA',vi.addr); else e.abs('STA',vi.addr);
        if(vi.addr+1<0x100) e.zp('LDA',vi.addr+1); else e.abs('LDA',vi.addr+1);
        e.imm('SBC',0);
        if(vi.addr+1<0x100) e.zp('STA',vi.addr+1); else e.abs('STA',vi.addr+1);
      }
      return;
    }
    // word/q8_8 = word/q8_8 +/- word/q8_8_var: 16-bit ADC/SBC con carry corretto
    if (lIsVar && (binOp.op==='+'||binOp.op==='-') && rVar && rVar.size===2 && vi.addr!=null) {
      if (binOp.op==='+') {
        e.imp('CLC');
        if(vi.addr<0x100)     e.zp ('LDA',vi.addr,    `${vi.name}_lo`);     else e.abs('LDA',vi.addr);
        if(rVar.addr<0x100)   e.zp ('ADC',rVar.addr,  `${rVar.name}_lo`);   else e.abs('ADC',rVar.addr);
        if(vi.addr<0x100)     e.zp ('STA',vi.addr);                          else e.abs('STA',vi.addr);
        if(vi.addr+1<0x100)   e.zp ('LDA',vi.addr+1,  `${vi.name}_hi`);     else e.abs('LDA',vi.addr+1);
        if(rVar.addr+1<0x100) e.zp ('ADC',rVar.addr+1,`${rVar.name}_hi`);   else e.abs('ADC',rVar.addr+1);
        if(vi.addr+1<0x100)   e.zp ('STA',vi.addr+1);                       else e.abs('STA',vi.addr+1);
      } else {
        e.imp('SEC');
        if(vi.addr<0x100)     e.zp ('LDA',vi.addr,    `${vi.name}_lo`);     else e.abs('LDA',vi.addr);
        if(rVar.addr<0x100)   e.zp ('SBC',rVar.addr,  `${rVar.name}_lo`);   else e.abs('SBC',rVar.addr);
        if(vi.addr<0x100)     e.zp ('STA',vi.addr);                          else e.abs('STA',vi.addr);
        if(vi.addr+1<0x100)   e.zp ('LDA',vi.addr+1,  `${vi.name}_hi`);     else e.abs('LDA',vi.addr+1);
        if(rVar.addr+1<0x100) e.zp ('SBC',rVar.addr+1,`${rVar.name}_hi`);   else e.abs('SBC',rVar.addr+1);
        if(vi.addr+1<0x100)   e.zp ('STA',vi.addr+1);                       else e.abs('STA',vi.addr+1);
      }
      return;
    }
    // ── vi = vi +/- expr16 (es. vy = vy - (vy >> 2)): RHS come 16-bit ──────
    // Gestisce shift e altri pattern che producono un valore 16-bit non banale.
    if (lIsVar && (binOp.op==='+'||binOp.op==='-') && vi.addr!=null) {
      const tmp=this.p.zpUtility.tmp, tmp2=this.p.zpUtility.tmp2;
      if (this._emitWord16RhsToTmp(binOp.right, tmp, tmp2)) {
        // RHS 16-bit ora in (tmp=lo, tmp2=hi); esegui op a 16-bit
        if (binOp.op==='+') {
          e.imp('CLC');
          if(vi.addr<0x100)   e.zp ('LDA',vi.addr,  `${vi.name}_lo`); else e.abs('LDA',vi.addr);
          e.zp('ADC',tmp,'lo');
          if(vi.addr<0x100)   e.zp ('STA',vi.addr);                   else e.abs('STA',vi.addr);
          if(vi.addr+1<0x100) e.zp ('LDA',vi.addr+1,`${vi.name}_hi`); else e.abs('LDA',vi.addr+1);
          e.zp('ADC',tmp2,'hi');
          if(vi.addr+1<0x100) e.zp ('STA',vi.addr+1);                 else e.abs('STA',vi.addr+1);
        } else {
          e.imp('SEC');
          if(vi.addr<0x100)   e.zp ('LDA',vi.addr,  `${vi.name}_lo`); else e.abs('LDA',vi.addr);
          e.zp('SBC',tmp,'lo');
          if(vi.addr<0x100)   e.zp ('STA',vi.addr);                   else e.abs('STA',vi.addr);
          if(vi.addr+1<0x100) e.zp ('LDA',vi.addr+1,`${vi.name}_hi`); else e.abs('LDA',vi.addr+1);
          e.zp('SBC',tmp2,'hi');
          if(vi.addr+1<0x100) e.zp ('STA',vi.addr+1);                 else e.abs('STA',vi.addr+1);
        }
        return;
      }
    }
    // Fallback generico: eval expr (produce A=lo), zero-extend hi
    this.evalExpr(binOp);
    if(vi.addr<0x100) e.zp('STA',vi.addr,`${vi.name}_lo`); else e.abs('STA',vi.addr);
    e.imm('LDA',0);
    if(vi.addr+1<0x100) e.zp('STA',vi.addr+1,`${vi.name}_hi=0`); else e.abs('STA',vi.addr+1);
  }

  // Prova a emettere node come valore 16-bit in (tmpLo ZP, tmpHi ZP).
  // Supporta:
  //   var16 >> n  — SAR aritmetico per signed (sq*), LSR logico per unsigned
  //   var16       — copia diretta
  // Ritorna true se emesso, false se pattern non supportato (→ fallback).
  _emitWord16RhsToTmp(node, tmpLo, tmpHi) {
    const e = this.e;
    // ── Caso: var16 >> n_letterale ────────────────────────────────────────
    if (node.k==='BinaryOp' && node.op==='>>' && node.right.k==='Literal') {
      const srcVar = node.left.k==='Ident' ? this._var(node.left.name) : null;
      if (srcVar && srcVar.size>=2 && srcVar.addr!=null) {
        const n = node.right.value & 15;
        const signed = isSignedFP(srcVar.type);
        // Copia src in (tmpLo, tmpHi)
        if(srcVar.addr<0x100) e.zp ('LDA',srcVar.addr,  `${srcVar.name}_lo`);
        else                  e.abs('LDA',srcVar.addr,  `${srcVar.name}_lo`);
        e.zp('STA',tmpLo,'rhs_lo');
        if(srcVar.addr+1<0x100) e.zp ('LDA',srcVar.addr+1,`${srcVar.name}_hi`);
        else                    e.abs('LDA',srcVar.addr+1,`${srcVar.name}_hi`);
        e.zp('STA',tmpHi,'rhs_hi');
        // Shift 16-bit: SAR (aritmetico) per signed, LSR (logico) per unsigned
        // SAR: CMP #$80 imposta carry = bit7 (segno), poi ROR preserva il segno
        // LSR: forza carry=0 prima di ROR → inserisce 0 da sinistra
        for (let i=0; i<n; i++) {
          if (signed) {
            e.zp('LDA',tmpHi); e.imm('CMP',0x80,`sar${i}_sign`);
            e.zp('ROR',tmpHi); e.zp('ROR',tmpLo);
          } else {
            e.zp('LSR',tmpHi); e.zp('ROR',tmpLo);
          }
        }
        return true;
      }
    }
    // ── Caso: var16 semplice ──────────────────────────────────────────────
    if (node.k==='Ident') {
      const srcVar = this._var(node.name);
      if (srcVar && srcVar.size>=2 && srcVar.addr!=null) {
        if(srcVar.addr<0x100) e.zp ('LDA',srcVar.addr);   else e.abs('LDA',srcVar.addr);
        e.zp('STA',tmpLo);
        if(srcVar.addr+1<0x100) e.zp ('LDA',srcVar.addr+1); else e.abs('LDA',srcVar.addr+1);
        e.zp('STA',tmpHi);
        return true;
      }
    }
    return false;
  }

  // ══════════════════════════════════════════════════════════════════════
  //  32-BIT (long / ulong / dword) HELPERS
  // ══════════════════════════════════════════════════════════════════════

  // Helper: ld/st per un byte di una variabile 32-bit (offset 0..3)
  _ld32(vi, off, cmt) {
    const a = vi.addr!=null ? vi.addr+off : null;
    const r = vi.addr!=null ? a : (vi.label||`_${vi.name}`)+(off?`+${off}`:'');
    if (a!=null && a<0x100) this.e.zp ('LDA',r,cmt); else this.e.abs('LDA',r,cmt);
  }
  _st32(vi, off, cmt) {
    const a = vi.addr!=null ? vi.addr+off : null;
    const r = vi.addr!=null ? a : (vi.label||`_${vi.name}`)+(off?`+${off}`:'');
    if (a!=null && a<0x100) this.e.zp ('STA',r,cmt); else this.e.abs('STA',r,cmt);
  }

  // ── Assegnamento 32-bit ───────────────────────────────────────────────
  _emitDWord32Assign(vi, val) {
    const e=this.e, tmp=this.p.zpUtility.tmp, tmp2=this.p.zpUtility.tmp2;
    const signed = vi.type==='long';

    if (val.k==='Literal') {
      this._initDWord32(vi, val.value>>>0); return;
    }

    if (val.k==='Ident') {
      const src=this._var(val.name);
      if (src && src.size===4 && src.addr!=null) {
        // long = long: copia 4 byte
        for (let i=0;i<4;i++) { this._ld32(src,i,`${src.name}_b${i}`); this._st32(vi,i,`${vi.name}_b${i}`); }
        return;
      }
      if (src && src.size===2 && src.addr!=null) {
        // long = word: copia 2 byte, zero-extend (o sign-extend per long)
        const isZPsrc = src.addr<0x100;
        isZPsrc ? e.zp('LDA',src.addr) : e.abs('LDA',src.addr);
        this._st32(vi,0,`${vi.name}_b0`);
        isZPsrc ? e.zp('LDA',src.addr+1) : e.abs('LDA',src.addr+1);
        this._st32(vi,1,`${vi.name}_b1`);
        if (signed) {
          // sign-extend: replica il bit 7 del byte hi
          const lPos=e.uniq('_l32sp'), lDn=e.uniq('_l32sd');
          e.imm('CMP',0x80,'sign bit'); e.branch('BCC',lPos,'positive'); e.imm('LDA',0xFF,'neg ext'); e.jmp(lDn);
          e.label(lPos); e.imm('LDA',0,'zero ext'); e.label(lDn);
        } else { e.imm('LDA',0); }
        this._st32(vi,2,`${vi.name}_b2`); this._st32(vi,3,`${vi.name}_b3`);
        return;
      }
      if (src && src.size===1 && src.addr!=null) {
        // long = byte: zero/sign-extend da 1 byte
        const isZPsrc = src.addr<0x100;
        isZPsrc ? e.zp('LDA',src.addr) : e.abs('LDA',src.addr);
        this._st32(vi,0,`${vi.name}_b0`);
        if (signed) {
          const lPos=e.uniq('_l32sp'), lDn=e.uniq('_l32sd');
          e.imm('CMP',0x80); e.branch('BCC',lPos); e.imm('LDA',0xFF); e.jmp(lDn);
          e.label(lPos); e.imm('LDA',0); e.label(lDn);
        } else { e.imm('LDA',0); }
        this._st32(vi,1,`${vi.name}_b1`); this._st32(vi,2,`${vi.name}_b2`); this._st32(vi,3,`${vi.name}_b3`);
        return;
      }
    }

    if (val.k==='BinaryOp' && (val.op==='+'||val.op==='-')) {
      const left=val.left, right=val.right;
      const lIsVar = left.k==='Ident' && left.name===vi.name;
      // Caso ottimizzato: vi = vi +/- literal
      if (lIsVar && right.k==='Literal' && vi.addr!=null) {
        const rv = right.value>>>0;
        const b = [rv&0xFF,(rv>>8)&0xFF,(rv>>16)&0xFF,(rv>>24)&0xFF];
        if (val.op==='+') {
          e.imp('CLC');
          for (let i=0;i<4;i++) {
            this._ld32(vi,i,`${vi.name}_b${i}`);
            e.imm('ADC',b[i],`+$${b[i].toString(16).padStart(2,'0')}`);
            this._st32(vi,i);
          }
        } else {
          e.imp('SEC');
          for (let i=0;i<4;i++) {
            this._ld32(vi,i,`${vi.name}_b${i}`);
            e.imm('SBC',b[i],`-$${b[i].toString(16).padStart(2,'0')}`);
            this._st32(vi,i);
          }
        }
        return;
      }
      // Caso: vi = vi +/- src32
      const rVar = right.k==='Ident' ? this._var(right.name) : null;
      if (lIsVar && rVar && rVar.size===4 && vi.addr!=null && rVar.addr!=null) {
        if (val.op==='+') {
          e.imp('CLC');
          for (let i=0;i<4;i++) {
            this._ld32(vi,i,`${vi.name}_b${i}`);
            this._ld32.call({e,_var:()=>rVar,e:e}, rVar, i); // trick: usa e.zp/abs direttamente
            const ra = rVar.addr+i;
            if (ra<0x100) e.zp('ADC',ra,`+${rVar.name}_b${i}`); else e.abs('ADC',ra,`+${rVar.name}_b${i}`);
            this._st32(vi,i);
          }
        } else {
          e.imp('SEC');
          for (let i=0;i<4;i++) {
            this._ld32(vi,i,`${vi.name}_b${i}`);
            const ra = rVar.addr+i;
            if (ra<0x100) e.zp('SBC',ra,`-${rVar.name}_b${i}`); else e.abs('SBC',ra,`-${rVar.name}_b${i}`);
            this._st32(vi,i);
          }
        }
        return;
      }
    }

    // Shift left: vi = vi << n (letterale)
    if (val.k==='BinaryOp' && val.op==='<<' && val.left.k==='Ident' && val.left.name===vi.name && val.right.k==='Literal' && vi.addr!=null) {
      let n = val.right.value & 31;
      while (n--) {
        e.imp('CLC');
        this._ld32(vi,0); e.acc('ASL'); this._st32(vi,0);
        this._ld32(vi,1); e.acc('ROL'); this._st32(vi,1);
        this._ld32(vi,2); e.acc('ROL'); this._st32(vi,2);
        this._ld32(vi,3); e.acc('ROL'); this._st32(vi,3);
      }
      return;
    }
    // Shift right (logico): vi = vi >> n (letterale)
    if (val.k==='BinaryOp' && val.op==='>>' && val.left.k==='Ident' && val.left.name===vi.name && val.right.k==='Literal' && vi.addr!=null) {
      let n = val.right.value & 31;
      while (n--) {
        this._ld32(vi,3); e.acc('LSR'); this._st32(vi,3);
        this._ld32(vi,2); e.acc('ROR'); this._st32(vi,2);
        this._ld32(vi,1); e.acc('ROR'); this._st32(vi,1);
        this._ld32(vi,0); e.acc('ROR'); this._st32(vi,0);
      }
      return;
    }

    // Fallback: eval espressione (produce byte in A), zero-extend
    this.evalExpr(val);
    this._st32(vi,0,`${vi.name}_b0`); e.imm('LDA',0);
    this._st32(vi,1,`${vi.name}_b1`); this._st32(vi,2,`${vi.name}_b2`); this._st32(vi,3,`${vi.name}_b3`);
  }

  // ── Confronto 32-bit: var32 OP literal32 → branch ─────────────────────
  _cmpDWord32(vi, lit32, lbl, onTrue, op) {
    const e=this.e;
    const b = [(lit32>>>0)&0xFF,(lit32>>>8)&0xFF,(lit32>>>16)&0xFF,(lit32>>>24)&0xFF];
    const lCont=e.uniq('_d32c');
    const bfar=(brOp,inv,dest)=>{ if(dest===lCont){e.branch(brOp,lCont);}else{const lS=e.uniq('_d32s');e.branch(inv,lS);e.jmp(dest);e.label(lS);} };

    if (op==='==' || op==='!=') {
      // Tutti e 4 i byte devono essere uguali (==) o almeno uno diverso (!=)
      const lFail=e.uniq('_d32f');
      for (let i=3;i>=0;i--) {
        this._ld32(vi,i,`${vi.name}_b${i}`); e.imm('CMP',b[i]);
        if (op==='==') bfar('BNE','BEQ', onTrue?lCont:lbl); // != → fallisce
        else           bfar('BNE','BEQ', onTrue?lbl:lCont);  // != → ok
      }
      if (op==='==' && onTrue) e.jmp(lbl,'all equal');
      e.label(lCont); return;
    }
    // Confronto d'ordine: hi byte prima (b3), poi b2, b1, b0
    for (let i=3;i>=0;i--) {
      this._ld32(vi,i,`${vi.name}_b${i}`); e.imm('CMP',b[i]);
      if (i>0) {
        bfar('BCC','BCS', onTrue?lbl:lCont); // sicuramente <
        bfar('BNE','BEQ', onTrue?lCont:lbl); // sicuramente >
      } else {
        // Byte basso: confronto finale con op originale
        if (op==='<')  bfar('BCC','BCS', onTrue?lbl:lCont);
        if (op==='>=') bfar('BCS','BCC', onTrue?lbl:lCont);
        if (op==='>')  { e.branch('BEQ',lCont); bfar('BCS','BCC', onTrue?lbl:lCont); }
        if (op==='<=') { bfar('BCC','BCS', onTrue?lbl:lCont); bfar('BEQ','BNE', onTrue?lbl:lCont); }
      }
    }
    e.label(lCont);
  }

  // ── Condition emitters ────────────────────────────────────────────────
  _branchIfFalse(cond, lbl) {
    const e=this.e;
    if (cond.k==='BinaryOp'&&['==','!=','<','>','<=','>='].includes(cond.op)) {
      this._cmpBranch(cond, lbl, false);
    } else {
      this.evalExpr(cond); e.imm('CMP',0,'test 0'); e.branch('BEQ',lbl,'if false');
    }
  }
  _branchIfTrue(cond, lbl) {
    const e=this.e;
    if (cond.k==='BinaryOp'&&['==','!=','<','>','<=','>='].includes(cond.op)) {
      this._cmpBranch(cond, lbl, true);
    } else {
      this.evalExpr(cond); e.imm('CMP',0); e.branch('BNE',lbl,'if true');
    }
  }
  _cmpBranch(node, lbl, onTrue) {
    const e=this.e, tmp=this.p.zpUtility.tmp;
    const op=node.op;
    const left=node.left, right=node.right;
    const leftVar=left.k==='Ident'?this._var(left.name):null;
    // ── Confronto float: usa FCOMP ($BC5B) ─────────────────────────────
    const lType = left._type  || (leftVar?leftVar.type:'');
    const rType = right._type || (right.k==='Ident'&&this._var(right.name)?this._var(right.name).type:'');
    if (lType==='float' || rType==='float') {
      this._evalFloatCmp(node, lbl, onTrue);
      return;
    }
    // 32-bit comparison: long/ulong/dword var vs literal
    if (leftVar&&leftVar.size===4&&right.k==='Literal') {
      this._cmpDWord32(leftVar, right.value>>>0, lbl, onTrue, op);
      return;
    }
    // 16-bit comparison: word var vs literal
    if (leftVar&&leftVar.size===2&&right.k==='Literal') {
      const signed = isSignedFP(leftVar.type) || leftVar.type==='int';
      if (signed) this._cmpWord16Signed(leftVar, right.value&0xFFFF, lbl, onTrue, op);
      else        this._cmpWord16(leftVar, right.value&0xFFFF, lbl, onTrue, op);
      return;
    }
    // 8-bit comparison
    this.evalExpr(right); e.zp('STA',tmp,'cmpB:R');
    this.evalExpr(left);  e.zp('CMP',tmp,'cmpB:L vs R');
    if (onTrue) this._branchCmpTrue(op, lbl);
    else {
      const lSkip=e.uniq('_cmpS');
      this._branchCmpTrue(op, lSkip);
      e.jmp(lbl,'cmp false'); e.label(lSkip);
    }
  }
  // 16-bit var OP literal (unsigned) — tutti e 6 operatori corretti
  _cmpWord16(vi, lit16, lbl, onTrue, op) {
    const e=this.e;
    const litLo=lit16&0xFF, litHi=(lit16>>8)&0xFF;
    const lCont=e.uniq('_w16c');

    // Regola branch range: i branch verso lbl (loop exit, potenzialmente
    // lontano >127 byte) usano sempre il pattern "branch-inverso + JMP lbl"
    // per range illimitato. I branch verso lCont (pochi byte avanti) restano
    // branch corti diretti.
    //
    // jmpTo(lbl): emette JMP lbl (range illimitato, sempre 3 byte)
    // bfar(brOp, inv, dest): se dest è lbl → branch inv su lS + JMP dest
    //                        se dest è lCont → branch brOp diretto (corto)
    const jmpTo = (target) => e.jmp(target);
    const bfar  = (brOp, inv, dest) => {
      if (dest === lCont) { e.branch(brOp, lCont); }
      else { const lS=e.uniq('_w16s'); e.branch(inv,lS); jmpTo(dest); e.label(lS); }
    };

    if (op==='<') {
      e.zp('LDA',vi.addr+1,'w16 hi'); e.imm('CMP',litHi);
      // hi < litHi → sicuramente < → verso "sì" (onTrue→lbl, !onTrue→lCont)
      bfar('BCC','BCS', onTrue?lbl:lCont);
      // hi != litHi (quindi > litHi) → verso "no"
      bfar('BNE','BEQ', onTrue?lCont:lbl);
      // hi == litHi: confronta lo
      e.zp('LDA',vi.addr,'w16 lo'); e.imm('CMP',litLo);
      bfar('BCC','BCS', onTrue?lbl:lCont); // lo < litLo → sì
      // else → no (caduta su lCont)
      e.label(lCont); return;
    }
    if (op==='>=') {
      e.zp('LDA',vi.addr+1,'w16 hi'); e.imm('CMP',litHi);
      bfar('BCC','BCS', onTrue?lCont:lbl); // hi < litHi → no
      bfar('BNE','BEQ', onTrue?lbl:lCont); // hi > litHi → sì
      e.zp('LDA',vi.addr,'w16 lo'); e.imm('CMP',litLo);
      bfar('BCS','BCC', onTrue?lbl:lCont); // lo >= litLo → sì
      e.label(lCont); return;
    }
    if (op==='>') {
      e.zp('LDA',vi.addr+1,'w16 hi'); e.imm('CMP',litHi);
      bfar('BCC','BCS', onTrue?lCont:lbl); // hi < litHi → no
      bfar('BNE','BEQ', onTrue?lbl:lCont); // hi > litHi → sì
      e.zp('LDA',vi.addr,'w16 lo'); e.imm('CMP',litLo);
      // lo > litLo: lo!=litLo AND carry set (lo >= litLo → lo > litLo)
      e.branch('BEQ', lCont,'lo==→no');      // lo==litLo → not >
      bfar('BCS','BCC', onTrue?lbl:lCont);   // lo > litLo → sì
      e.label(lCont); return;
    }
    if (op==='<=') {
      e.zp('LDA',vi.addr+1,'w16 hi'); e.imm('CMP',litHi);
      bfar('BCC','BCS', onTrue?lbl:lCont); // hi < litHi → sì
      bfar('BNE','BEQ', onTrue?lCont:lbl); // hi > litHi → no
      e.zp('LDA',vi.addr,'w16 lo'); e.imm('CMP',litLo);
      // lo <= litLo: lo < litLo OR lo == litLo
      bfar('BCC','BCS', onTrue?lbl:lCont); // lo < litLo → sì
      bfar('BEQ','BNE', onTrue?lbl:lCont); // lo == litLo → sì
      e.label(lCont); return;
    }
    if (op==='==') {
      e.zp('LDA',vi.addr+1,'w16 hi'); e.imm('CMP',litHi);
      bfar('BNE','BEQ', onTrue?lCont:lbl); // hi != litHi → no
      e.zp('LDA',vi.addr,'w16 lo'); e.imm('CMP',litLo);
      bfar('BEQ','BNE', onTrue?lbl:lCont); // lo == litLo → sì
      e.label(lCont); return;
    }
    if (op==='!=') {
      e.zp('LDA',vi.addr+1,'w16 hi'); e.imm('CMP',litHi);
      bfar('BNE','BEQ', onTrue?lbl:lCont); // hi != litHi → sì (!=)
      e.zp('LDA',vi.addr,'w16 lo'); e.imm('CMP',litLo);
      bfar('BNE','BEQ', onTrue?lbl:lCont); // lo != litLo → sì
      e.label(lCont); return;
    }
    // Fallback 8-bit
    e.zp('LDA',vi.addr,'w16 lo fallback'); e.imm('CMP',litLo);
    if (onTrue) this._branchCmpTrue(op, lbl);
    else { const lS=e.uniq('_w16s'); this._branchCmpTrue(op,lS); e.jmp(lbl); e.label(lS); }
    e.label(lCont);
  }

  // 16-bit SIGNED var OP literal — tutti e 6 gli operatori corretti
  // Usa SEC/SBC + (BVC skip; EOR #$80; skip:) per ottenere N XOR V
  // che implementa il confronto signed a 16 bit sul 6502.
  _cmpWord16Signed(vi, lit16, lbl, onTrue, op) {
    const e=this.e;
    const litLo=lit16&0xFF, litHi=(lit16>>8)&0xFF;
    const lCont=e.uniq('_sw16c');
    const jmpTo=(target)=>e.jmp(target);
    const bfar=(brOp,inv,dest)=>{
      if(dest===lCont){e.branch(brOp,lCont);}
      else{const lS=e.uniq('_sw16s');e.branch(inv,lS);jmpTo(dest);e.label(lS);}
    };
    // == e != non dipendono dal segno
    if(op==='=='||op==='!=') {
      if(vi.addr+1<0x100)e.zp('LDA',vi.addr+1,'sw hi');else e.abs('LDA',vi.addr+1,'sw hi');
      e.imm('CMP',litHi);
      if(op==='=='){
        bfar('BNE','BEQ',onTrue?lCont:lbl);
        if(vi.addr<0x100)e.zp('LDA',vi.addr,'sw lo');else e.abs('LDA',vi.addr,'sw lo');
        e.imm('CMP',litLo); bfar('BEQ','BNE',onTrue?lbl:lCont);
      } else {
        bfar('BNE','BEQ',onTrue?lbl:lCont);
        if(vi.addr<0x100)e.zp('LDA',vi.addr,'sw lo');else e.abs('LDA',vi.addr,'sw lo');
        e.imm('CMP',litLo); bfar('BNE','BEQ',onTrue?lbl:lCont);
      }
      e.label(lCont); return;
    }
    // Confronto d'ordine: SEC; SBC lo; SBC hi -> N XOR V = segno(X-Y)
    // Poi: BVC skip; EOR #$80; skip:  ->  N=1 iff X < Y (signed)
    e.imp('SEC','signed cmp16');
    if(vi.addr<0x100)e.zp('LDA',vi.addr,`${vi.name}_lo`);else e.abs('LDA',vi.addr,`${vi.name}_lo`);
    e.imm('SBC',litLo);
    if(vi.addr+1<0x100)e.zp('LDA',vi.addr+1,`${vi.name}_hi`);else e.abs('LDA',vi.addr+1,`${vi.name}_hi`);
    e.imm('SBC',litHi);
    const lNVskip=e.uniq('_sw16nv');
    e.branch('BVC',lNVskip,'no overflow, N corretto');
    e.imm('EOR',0x80,'flip N su overflow');
    e.label(lNVskip);
    // Ora: N=1 -> X<Y (signed),  N=0 -> X>=Y (signed)
    switch(op) {
      case '<':
        bfar('BMI','BPL',onTrue?lbl:lCont); break;
      case '>=':
        bfar('BPL','BMI',onTrue?lbl:lCont); break;
      case '>': {
        // X>Y: X>=Y (N=0) AND X!=Y
        bfar('BMI','BPL',onTrue?lCont:lbl);         // N=1 -> X<Y -> false
        if(vi.addr+1<0x100)e.zp('LDA',vi.addr+1,'recheck hi');else e.abs('LDA',vi.addr+1,'recheck hi');
        e.imm('CMP',litHi);
        bfar('BNE','BEQ',onTrue?lbl:lCont);          // hi diversi -> X>Y -> true
        if(vi.addr<0x100)e.zp('LDA',vi.addr,'recheck lo');else e.abs('LDA',vi.addr,'recheck lo');
        e.imm('CMP',litLo);
        bfar('BEQ','BNE',onTrue?lCont:lbl);          // uguali -> X==Y -> false
        bfar('BNE','BEQ',onTrue?lbl:lCont);          // lo diversi -> X>Y -> true
        break;
      }
      case '<=': {
        // X<=Y: X<Y (N=1) OR X==Y
        bfar('BMI','BPL',onTrue?lbl:lCont);          // N=1 -> X<Y -> true
        if(vi.addr+1<0x100)e.zp('LDA',vi.addr+1,'recheck hi');else e.abs('LDA',vi.addr+1,'recheck hi');
        e.imm('CMP',litHi);
        bfar('BNE','BEQ',onTrue?lCont:lbl);          // hi diversi -> X>Y -> false
        if(vi.addr<0x100)e.zp('LDA',vi.addr,'recheck lo');else e.abs('LDA',vi.addr,'recheck lo');
        e.imm('CMP',litLo);
        bfar('BEQ','BNE',onTrue?lbl:lCont);          // uguali -> X==Y -> true
        break;                                         // lo diversi -> X>Y -> false
      }
    }
    e.label(lCont);
  }

  // ── Negazione 16-bit in-place: vi = -vi (complemento a due) ─────────────
  // SEC; LDA #0; SBC lo; STA lo; LDA #0; SBC hi; STA hi
  // Preserva il carry frazionario — corretto per sq8_8 fisica.
  _negWord16InPlace(vi) {
    const e=this.e;
    e.imp('SEC','neg16: complemento a due');
    e.imm('LDA',0,'A=0');
    if(vi.addr<0x100){e.zp('SBC',vi.addr,`neg ${vi.name}_lo`);e.zp('STA',vi.addr,`${vi.name}_lo`);}
    else             {e.abs('SBC',vi.addr,`neg ${vi.name}_lo`);e.abs('STA',vi.addr,`${vi.name}_lo`);}
    e.imm('LDA',0,'A=0');
    if(vi.addr+1<0x100){e.zp('SBC',vi.addr+1,`neg ${vi.name}_hi`);e.zp('STA',vi.addr+1,`${vi.name}_hi`);}
    else               {e.abs('SBC',vi.addr+1,`neg ${vi.name}_hi`);e.abs('STA',vi.addr+1,`${vi.name}_hi`);}
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  BUILTIN CALLS
  // ═══════════════════════════════════════════════════════════════════════

  // ── Float helpers: A → FAC1 (GIVAYF) e FAC1 → A (QINT+LDA) ────────────
  // Richiedono $01=$37 (BASIC ROM attivo) — garantito da usesFloat=true.
  // GIVAYF $B391: converte Y:A (intero 0..65535 unsigned) in float FAC1.
  // Per argomenti byte (0..255): Y=0, A=valore.
  // QINT $B1AA: FAC1 → 4-byte integer signed; byte meno significativo in $65.
  _floatLoadArg() {
    // Converte il byte in A -> float FAC1 via GIVAYF ($B391).
    // *** Convenzione CORRETTA GIVAYF: Y=lo byte, A=hi byte (sign extension) ***
    // BUG precedente: passava valore in A, zero in Y -> il byte finiva come HI
    // (moltiplicato x256). Es: k=1->256, k=9->2304, k=2->512.
    // Proof: sin(256)=-.999208, log(512)=6.238, exp(256)=OVERFLOW (esatti!)
    //
    // Fix: TAY sposta il valore in Y (lo byte), poi A = sign extension (hi byte).
    // Esempi: k=0->Y=$00,A=$00->0.0   k=1->Y=$01,A=$00->1.0
    //         k=127->Y=$7F,A=$00->127.0   k=255(-1)->Y=$FF,A=$FF->-1.0
    const e=this.e;
    const lNeg=e.uniq('_flneg'), lGiv=e.uniq('_flgiv');
    e.imp('TAY', 'Y=lo byte (A ancora uguale per CMP)');
    e.imm('CMP', 0x80, 'sign test: A<$80 -> positivo');
    e.branch('BCC', lNeg, 'positivo: hi=$00');
    e.imm('LDA', 0xFF, 'A=$FF: hi byte negativo');
    e.jmp(lGiv);
    e.label(lNeg);
    e.imm('LDA', 0x00, 'A=$00: hi byte positivo');
    e.label(lGiv);
    e.jsr(0xB391, 'GIVAYF: Y=lo, A=hi -> FAC1 float');
  }
  _floatGetResult() {
    const e=this.e;
    // FAC1 contiene il risultato float; QINT lo converte in intero
    // e lascia il LSB (lo byte) in $65 (FAC1+4)
    e.jsr(0xB1AA,'QINT: FAC1→int32 (LSB in $65)');
    e.abs('LDA',0x65,'risultato byte da FAC1');
  }


  // ── Float 5-byte load/store tramite MOVFM/MOVMF del KERNAL ──────────────
  // MOVFM $BBA2 : A=lo, Y=hi → carica 5-byte float da memoria in FAC1
  //               (ROM: STA $22 / STY $23 → legge 5 byte da ($22))
  // MOVMF $BBD4 : X=lo, Y=hi ← salva FAC1 in memoria come 5-byte float
  //               (ROM: STX $22 / STY $23 — usa X, NON A!)
  // FMOVE $BC0C : copia FAC1 → FAC2
  // FADD  $B867 : carica (A=lo,Y=hi) in FAC2, poi FAC2 + FAC1 → FAC1
  // FSUB  $B850 : carica (A=lo,Y=hi) in FAC2, poi FAC2 − FAC1 → FAC1
  //               ($B853 è dentro la routine, NON un entry point "from memory"!)
  // FMUL  $BA28 : carica (A=lo,Y=hi) in FAC2, poi FAC2 × FAC1 → FAC1
  // FDIV  $BB0F : carica (A=lo,Y=hi) in FAC2, poi FAC2 ÷ FAC1 → FAC1
  //               ($BB12 è "divide operator" — FAC2 già caricato, salta il load!)
  // FPWR  $BF78 : FAC2 ^ FAC1 → FAC1  (FAC2=base, FAC1=esponente)
  // FCOMP $BC5B : confronta FAC1 con float a (A=lo,Y=hi) → A: 0=uguale, 1=FAC1>mem, $FF=FAC1<mem
  // FNEG  $BFB4 : cambia segno FAC1

  _floatGetLabel(vi) {
    if (vi.label) return vi.label;
    if (vi.addr !== null) return vi.addr;
    return `_${vi.name}`;
  }

  _floatVarToFAC1(addrOrLabel, comment='') {
    const e = this.e;
    // MOVFM $BBA2: A=lo, Y=hi dell'indirizzo sorgente → carica 5-byte float in FAC1.
    // $BBD0 è SBAGLIATO: è un'entry di MOVMF (store) che legge dest da $49/$4A,
    // ignorando completamente A e Y. La vera MOVFM (load) è a $BBA2.
    if (typeof addrOrLabel === 'number') {
      const lo = addrOrLabel & 0xFF, hi = (addrOrLabel >> 8) & 0xFF;
      e.imm('LDA', hi, `MOVFM hi $${hi.toString(16).padStart(2,'0')} ${comment}`);
      e.imp('TAY', '');
      e.imm('LDA', lo, `MOVFM lo $${lo.toString(16).padStart(2,'0')}`);
    } else {
      e.immHi(addrOrLabel, `MOVFM Y=hi [${addrOrLabel}] ${comment}`);
      e.imp('TAY', '');
      e.immLo(addrOrLabel, 'MOVFM A=lo');
    }
    e.jsr(0xBBA2, `MOVFM: (A:Y)→FAC1 ${comment}`);
  }

  _floatFAC1ToVar(addrOrLabel, comment='') {
    const e = this.e;
    // MOVMF $BBD4: X=lo, Y=hi dell'indirizzo destinazione → salva FAC1 in memoria.
    // La ROM a $BBD4 fa STX $22 / STY $23, quindi vuole X=lo, Y=hi.
    // È necessario TAX dopo aver caricato il byte basso, altrimenti X è garbage.
    if (typeof addrOrLabel === 'number') {
      const lo = addrOrLabel & 0xFF, hi = (addrOrLabel >> 8) & 0xFF;
      e.imm('LDA', hi, `MOVMF hi $${hi.toString(16).padStart(2,'0')} ${comment}`);
      e.imp('TAY', '');
      e.imm('LDA', lo, `MOVMF lo $${lo.toString(16).padStart(2,'0')}`);
    } else {
      e.immHi(addrOrLabel, `MOVMF Y=hi [${addrOrLabel}] ${comment}`);
      e.imp('TAY', '');
      e.immLo(addrOrLabel, 'MOVMF A=lo');
    }
    e.imp('TAX', 'MOVMF: X=lo (BBD4 usa STX $22, non STA)');
    e.jsr(0xBBD4, `MOVMF: FAC1→(X:Y) ${comment}`);
  }

  // ── Carica un float literal (valore JS) in FAC1 ──────────────────────────
  // Per interi 0-255: GIVAYF (più compatto).
  // Per decimali: embeds 5 byte CBM inline con JMP over.
  _floatLitToFAC1(value) {
    const e = this.e;
    if (Number.isInteger(value) && value >= -128 && value <= 255) {
      const v = ((value < 0 ? value + 256 : value)) & 0xFF;
      e.imm('LDA', v, `#${value}`);
      this._floatLoadArg();
      return;
    }
    const bytes = floatToCBM5(value);
    const lbl  = e.uniq('_fcst');
    const lEnd = e.uniq('_fcst_e');
    e.jmp(lEnd, `skip float const ${value}`);
    e.label(lbl);
    e.data(bytes, `CBM5 ${value}`);
    e.label(lEnd);
    this._floatVarToFAC1(lbl, `lit ${value}`);
  }

  // ── Valuta qualsiasi espressione e lascia risultato float in FAC1 ─────────
  _evalFloatExprToFAC1(node) {
    if (!node) return;
    const e = this.e;
    // Letterale numerico
    if (node.k === 'Literal') {
      this._floatLitToFAC1(typeof node.value === 'number' ? node.value : 0);
      return;
    }
    // Identificatore
    if (node.k === 'Ident') {
      const vi = this._var(node.name);
      if (vi && vi.type === 'float') {
        this._floatVarToFAC1(this._floatGetLabel(vi), vi.name);
        return;
      }
      // Variabile intera: carica byte, converti
      this.evalExpr(node);
      this._floatLoadArg();
      return;
    }
    // Chiamata a funzione float (sin/cos/fadd/ecc.) — FAC1 già con float
    if (node.k === 'Call') {
      const KFLOATS = new Set([
        'sin','cos','tan','atn','sqr','log','exp','abs','floor','rnd',
        'fadd','fsub','fmul','fdiv','fpow'
      ]);
      if (KFLOATS.has(node.name)) {
        this._evalFloatKeepFAC(node);
        return;
      }
      this.evalExpr(node);
      this._floatLoadArg();
      return;
    }
    // BinaryOp float
    if (node.k === 'BinaryOp') {
      const lt = node.left._type || '', rt = node.right._type || '';
      const isF = lt==='float' || rt==='float' ||
                  (node.left.k==='Literal'  && node.left.kind==='float') ||
                  (node.right.k==='Literal' && node.right.kind==='float');
      if (isF && ['+','-','*','/','^'].includes(node.op)) {
        this._evalFloatBinOp(node);
        return;
      }
      this.evalExpr(node);
      this._floatLoadArg();
      return;
    }
    // UnaryOp negazione float
    if (node.k === 'UnaryOp' && node.op === '-') {
      this._evalFloatExprToFAC1(node.operand);
      e.jsr(0xBFB4, 'FNEG: nega FAC1');
      return;
    }
    // Fallback: valuta come intero e converti
    this.evalExpr(node);
    this._floatLoadArg();
  }

  // ── Aritmetica float via KERNAL: FAC2 OP FAC1 → FAC1 ────────────────────
  _evalFloatBinOp(node) {
    const e = this.e, op = node.op;
    // Convenzione KERNAL: FADD/FSUB/FMUL/FDIV/FPWR sono entry "from memory":
    //   A=lo, Y=hi dell'indirizzo dell'operando SINISTRO in memoria
    //   FAC1 = operando DESTRO già caricato
    //   la routine carica (Y:A) in ARG/FAC2 e calcola ARG OP FAC1 → FAC1
    //
    // Strategia: salva operando sinistro in _ftmp via MOVMF,
    //            carica destro in FAC1, poi chiama la routine con Y:A = _ftmp.
    //
    // 1. Operando sinistro → FAC1
    this._evalFloatExprToFAC1(node.left);
    // 2. Salva FAC1 in _ftmp (MOVMF $BBD4: X=lo, Y=hi destinazione)
    e.immHi('_ftmp', 'MOVMF Y=hi _ftmp');
    e.imp('TAY', '');
    e.immLo('_ftmp', 'MOVMF A=lo _ftmp');
    e.imp('TAX', 'MOVMF: X=lo (BBD4 usa STX $22)');
    e.jsr(0xBBD4, 'MOVMF: FAC1→_ftmp (salva op. sinistro)');
    // 3. Operando destro → FAC1
    this._evalFloatExprToFAC1(node.right);
    // 4. Imposta Y:A = indirizzo _ftmp, poi chiama routine KERNAL
    //    La routine carica _ftmp in ARG/FAC2, calcola ARG OP FAC1 → FAC1
    e.immHi('_ftmp', `${op} Y=hi _ftmp`);
    e.imp('TAY', '');
    e.immLo('_ftmp', `${op} A=lo _ftmp`);
    switch(op) {
      case '+': e.jsr(0xB867, 'FADD: (A:Y)=_ftmp→FAC2, FAC2+FAC1→FAC1'); break;
      case '-': e.jsr(0xB850, 'FSUB: (A:Y)=_ftmp→FAC2, FAC2−FAC1→FAC1'); break; // $B850 = from-memory; $B853 salta il load!
      case '*': e.jsr(0xBA28, 'FMUL: (A:Y)=_ftmp→FAC2, FAC2×FAC1→FAC1'); break;
      case '/': e.jsr(0xBB0F, 'FDIV: (A:Y)=_ftmp→FAC2, FAC2÷FAC1→FAC1'); break; // $BB0F = from-memory; $BB12 salta il load!
      case '^': e.jsr(0xBF78, 'FPWR: _ftmp^FAC1→FAC1'); break;
      default:  e.imm('LDA', 0, `/* float ${op} n/s */`);
    }
  }

  // ── Confronto float via FCOMP ($BC5B) ────────────────────────────────────
  // FCOMP: confronta FAC1 con float 5-byte a (A=lo,Y=hi)
  // Risultato in A: 0=uguale, 1=FAC1>mem, $FF=FAC1<mem
  _evalFloatCmp(node, lbl, onTrue) {
    const e = this.e, op = node.op;
    // Salva operando destro in un temporaneo inline
    this._evalFloatExprToFAC1(node.right);
    const tmpLbl = e.uniq('_fcmp');
    const tmpEnd = e.uniq('_fcmp_e');
    e.jmp(tmpEnd, 'skip fcmp buf');
    e.label(tmpLbl);
    e.data([0,0,0,0,0], 'fcmp tmp float');
    e.label(tmpEnd);
    this._floatFAC1ToVar(tmpLbl, 'save R');
    // Carica operando sinistro → FAC1
    this._evalFloatExprToFAC1(node.left);
    // FCOMP: confronta FAC1 con (Y:A)=tmpLbl
    e.immHi(tmpLbl, 'FCOMP Y=hi');
    e.imp('TAY', '');
    e.immLo(tmpLbl, 'FCOMP A=lo');
    e.jsr(0xBC5B, 'FCOMP: 0=eq, 1=FAC1>mem, $FF=FAC1<mem');
    switch(op) {
      case '==': e.imm('CMP',0x00); if(onTrue) e.branch('BEQ',lbl); else e.branch('BNE',lbl); break;
      case '!=': e.imm('CMP',0x00); if(onTrue) e.branch('BNE',lbl); else e.branch('BEQ',lbl); break;
      case '>':  e.imm('CMP',0x01); if(onTrue) e.branch('BEQ',lbl); else e.branch('BNE',lbl); break;
      case '<=': e.imm('CMP',0x01); if(onTrue) e.branch('BNE',lbl); else e.branch('BEQ',lbl); break;
      case '<':  e.imm('CMP',0xFF); if(onTrue) e.branch('BEQ',lbl); else e.branch('BNE',lbl); break;
      case '>=': e.imm('CMP',0xFF); if(onTrue) e.branch('BNE',lbl); else e.branch('BEQ',lbl); break;
      default:   e.imm('CMP',0x00); if(onTrue) e.branch('BEQ',lbl); else e.branch('BNE',lbl);
    }
  }

  // ── Constant folder: riduce node a Literal se è espressione costante ───
  // Usato per VarDecl, _emitGlobalInits, confronti.
  _fold(node) {
    if (!node) return node;
    if (node.k==='Literal') return node;
    if (node.k==='BinaryOp') {
      const l=this._fold(node.left), r=this._fold(node.right);
      if (l&&l.k==='Literal'&&r&&r.k==='Literal') {
        let v=0;
        switch(node.op){
          case '+': v=l.value+r.value; break; case '-': v=l.value-r.value; break;
          case '*': v=l.value*r.value; break; case '/': v=r.value?Math.trunc(l.value/r.value):0; break;
          case '%': v=r.value?l.value%r.value:0; break;
          case '&': v=l.value&r.value; break; case '|': v=l.value|r.value; break;
          case '^': v=l.value^r.value; break;
          case '<<': v=l.value<<(r.value&7); break; case '>>': v=l.value>>(r.value&7); break;
          default: return node;
        }
        return {k:'Literal',value:v&0xFFFF,raw:String(v)};
      }
    }
    if (node.k==='UnaryOp'&&node.op==='-') {
      const o=this._fold(node.operand);
      if (o&&o.k==='Literal') return {k:'Literal',value:(-o.value)&0xFFFF,raw:String(-o.value)};
    }
    return node;
  }


  // Float KERNAL senza QINT — FAC1 rimane come float dopo la chiamata.
  // Usato da _emitPrintFloat per preservare i decimali in FAC1.
  _evalFloatKeepFAC(node) {
    const e=this.e, args=node.args||[];
    const JMAP = {
      sin:0xE26B, cos:0xE264, tan:0xE2B4, atn:0xE30E,
      sqr:0xBF71, log:0xB9EA, exp:0xBFED,
      abs:0xBC58, floor:0xBCCC, rnd:0xE097
    };
    // Funzioni aritmetiche float esplicite: fadd/fsub/fmul/fdiv/fpow
    const ARITH_OPS = {fadd:'+',fsub:'-',fmul:'*',fdiv:'/',fpow:'^'};
    if (ARITH_OPS[node.name]) {
      const synthOp = {
        k:'BinaryOp', op:ARITH_OPS[node.name],
        left:  args[0]||{k:'Literal',value:0,raw:'0',kind:'int'},
        right: args[1]||{k:'Literal',value:0,raw:'0',kind:'int'},
        _type:'float'
      };
      // Propaga tipo float agli operandi se nota
      if (args[0]) synthOp.left  = Object.assign({},args[0],{_type: args[0]._type||'float'});
      if (args[1]) synthOp.right = Object.assign({},args[1],{_type: args[1]._type||'float'});
      this._evalFloatBinOp(synthOp);
      return;
    }
    if (args.length>=1 && node.name!=='rnd') {
      const arg0 = args[0];
      // Variabile float: carica direttamente con MOVFM
      if (arg0.k==='Ident') {
        const vi = this._var(arg0.name);
        if (vi && vi.type==='float') {
          this._floatVarToFAC1(this._floatGetLabel(vi), vi.name);
          const addr=JMAP[node.name];
          if (addr) e.jsr(addr,`KERNAL ${node.name.toUpperCase()} (FAC1 float, no QINT)`);
          return;
        }
      }
      // Letterale float decimale
      if (arg0.k==='Literal' && arg0.kind==='float') {
        this._floatLitToFAC1(arg0.value);
        const addr=JMAP[node.name];
        if (addr) e.jsr(addr,`KERNAL ${node.name.toUpperCase()} (FAC1 float, no QINT)`);
        return;
      }
      // BinaryOp float
      if (arg0.k==='BinaryOp' && (arg0.left._type==='float'||arg0.right._type==='float')) {
        this._evalFloatBinOp(arg0);
        const addr=JMAP[node.name];
        if (addr) e.jsr(addr,`KERNAL ${node.name.toUpperCase()} (FAC1 float, no QINT)`);
        return;
      }
      // Intero: converti con GIVAYF
      this.evalExpr(arg0);
      this._floatLoadArg();
    }
    const addr=JMAP[node.name];
    if (addr) e.jsr(addr,`KERNAL ${node.name.toUpperCase()} (FAC1 float, no QINT)`);
    // FAC1 contiene il risultato float — niente QINT
  }

  // ── Helpers stampа polimorfica ──────────────────────────────────────────

  // Stampa il valore float in arg usando FOUT ($BDDD) → CHROUT loop
  _emitPrintFloat(arg) {
    const e=this.e, p=this.p;
    const ptr=p.zpUtility.ptr;
    const FLOAT_FNS=new Set(['sin','cos','tan','atn','sqr','log','exp','abs','floor','rnd',
                              'fadd','fsub','fmul','fdiv','fpow']);
    if (arg.k==='Call' && FLOAT_FNS.has(arg.name)) {
      this._evalFloatKeepFAC(arg);
    } else if (arg.k==='Ident') {
      const vi=this._var(arg.name);
      if (vi && vi.type==='float') this._floatVarToFAC1(this._floatGetLabel(vi), vi.name);
      else { this.evalExpr(arg); this._floatLoadArg(); }
    } else if (arg.k==='BinaryOp' &&
               ((arg.left&&arg.left._type==='float')||(arg.right&&arg.right._type==='float'))) {
      this._evalFloatBinOp(arg);
    } else if (arg.k==='Literal' && arg.kind==='float') {
      this._floatLitToFAC1(arg.value);
    } else {
      this.evalExpr(arg); this._floatLoadArg();
    }
    e.jsr(0xBDDD,'FOUT: FAC1→string (A=lo Y=hi del ptr)');
    e.zp('STA',ptr,'str_ptr lo'); e.imp('TYA','hi byte'); e.zp('STA',ptr+1,'str_ptr hi');
    const lPr=e.uniq('_fpPr'), lDn=e.uniq('_fpDn');
    const charTmp=p.zpUtility.tmp;
    e.imm('LDY',0,'idx=0');
    e.label(lPr);
    e.iny('LDA',ptr,'char=(ptr),Y');
    e.branch('BEQ',lDn,'eos');
    e.zp('STA',charTmp,'char→ZP tmp');
    e.imp('TYA','Y→A'); e.imp('PHA','push Y');
    e.zp('LDA',charTmp,'ricarica char');
    e.jsr(0xFFD2,'CHROUT');
    e.imp('PLA','pop Y'); e.imp('TAY','→Y');
    e.imp('INY');
    e.branch('BNE',lPr,'next char');
    e.label(lDn);
    e.imm('LDA',0x20,'spazio pulisci'); e.jsr(0xFFD2,'CHROUT');
  }

  // Stampa valore 32-bit in w0(LSB)..w3(MSB) come decimale via CHROUT
  _emitDecimalPrint32(isSigned, w0, w1, w2, w3) {
    const e=this.e;
    const lPos=e.uniq('_plPos'), lZero=e.uniq('_plZ'), lNZ=e.uniq('_plNZ');
    const lDiv=e.uniq('_plDiv'), lDivL=e.uniq('_plDL'), lNS=e.uniq('_plNS'), lPrL=e.uniq('_plPL');

    if (isSigned) {
      e.zp('LDA',w3,'MSB (segno)');
      e.branch('BPL',lPos,'positivo → salta');
      e.imm('LDA',0x2D,"'-'"); e.jsr(0xFFD2,'CHROUT -');
      e.imp('SEC');
      e.imm('LDA',0); e.zp('SBC',w0); e.zp('STA',w0,'neg b0');
      e.imm('LDA',0); e.zp('SBC',w1); e.zp('STA',w1,'neg b1');
      e.imm('LDA',0); e.zp('SBC',w2); e.zp('STA',w2,'neg b2');
      e.imm('LDA',0); e.zp('SBC',w3); e.zp('STA',w3,'neg b3');
      e.label(lPos);
    }
    e.zp('LDA',w0); e.zp('ORA',w1); e.zp('ORA',w2); e.zp('ORA',w3);
    e.branch('BNE',lNZ,'non zero');
    e.imm('LDA',0x30,"'0'"); e.jsr(0xFFD2,'CHROUT 0');
    e.jmp(lZero,'fine');
    e.label(lNZ);

    e.imm('LDX',0,'digit_count = 0');
    e.label(lDiv);
    e.imm('LDA',0,'rem = 0'); e.imm('LDY',32,'32 bit');
    e.label(lDivL);
    e.zp('ASL',w0); e.zp('ROL',w1); e.zp('ROL',w2); e.zp('ROL',w3);
    e.acc('ROL');
    e.imm('CMP',10,'rem >= 10?');
    e.branch('BCC',lNS,'no → salta');
    e.imm('SBC',10,'rem -= 10  (C=1 da CMP)');
    e.zp('INC',w0,'quoziente LSB = 1');
    e.label(lNS);
    e.imp('DEY');
    e.branch('BNE',lDivL,'next bit');
    e.imp('CLC'); e.imm('ADC',0x30,"+ '0'"); e.imp('PHA','push cifra');
    e.imp('INX','count++');
    e.zp('LDA',w0); e.zp('ORA',w1); e.zp('ORA',w2); e.zp('ORA',w3);
    e.branch('BNE',lDiv,'altra cifra');

    e.label(lPrL);
    e.imp('PLA','pop cifra'); e.jsr(0xFFD2,'CHROUT');
    e.imp('DEX');
    e.branch('BNE',lPrL,'next');

    e.label(lZero);
  }

  // Stampa il byte in A come decimale (0..255): zero-extend a 32-bit
  _emitDecimalPrint8FromA() {
    const p=this.p;
    const w0=p.zpUtility.tmp, w1=p.zpUtility.tmp2, w2=p.zpUtility.ptr, w3=p.zpUtility.ptr+1;
    this.e.zp('STA',w0,'byte→w0');
    this.e.imm('LDA',0);
    this.e.zp('STA',w1,'w1=0'); this.e.zp('STA',w2,'w2=0'); this.e.zp('STA',w3,'w3=0');
    this._emitDecimalPrint32(false, w0, w1, w2, w3);
  }

  // Stampa polimorfica di un singolo argomento (string, float, long, word, byte)
  _emitPrintArg(arg) {
    const e=this.e, p=this.p;
    const FLOAT_FNS=new Set(['sin','cos','tan','atn','sqr','log','exp','abs','floor','rnd',
                              'fadd','fsub','fmul','fdiv','fpow']);

    // ── String literal ────────────────────────────────────────────────────
    if (arg.k==='Literal' && arg.kind==='str') {
      const s=arg.value;
      for (let i=0;i<s.length;i++) {
        e.imm('LDA',s.charCodeAt(i)&0xFF,`'${s[i]}'`); e.jsr(0xFFD2,'CHROUT');
      }
      return;
    }

    // ── Float ─────────────────────────────────────────────────────────────
    const isFloatArg = (() => {
      if (arg.k==='Literal' && arg.kind==='float') return true;
      if (arg.k==='Ident') { const vi=this._var(arg.name); return vi && vi.type==='float'; }
      if (arg.k==='Call' && FLOAT_FNS.has(arg.name)) return true;
      if (arg.k==='BinaryOp') {
        const lt=arg.left?._type||'', rt=arg.right?._type||'';
        return lt==='float'||rt==='float';
      }
      return arg._type==='float';
    })();
    if (isFloatArg) { this._emitPrintFloat(arg); return; }

    // ── 32-bit: long/ulong/dword ──────────────────────────────────────────
    if (arg.k==='Ident') {
      const vi=this._var(arg.name);
      if (vi && vi.size===4 && vi.addr!=null) {
        const w0=p.zpUtility.tmp, w1=p.zpUtility.tmp2, w2=p.zpUtility.ptr, w3=p.zpUtility.ptr+1;
        for (let i=0;i<4;i++) {
          const src=vi.addr+i;
          if (src<0x100) e.zp('LDA',src,`${vi.name}_b${i}`);
          else           e.abs('LDA',src,`${vi.name}_b${i}`);
          e.zp('STA',w0+i,`work_b${i}`);
        }
        this._emitDecimalPrint32(vi.type==='long', w0, w1, w2, w3);
        return;
      }
    }

    // ── 16-bit: word/int ──────────────────────────────────────────────────
    if (arg.k==='Ident') {
      const vi=this._var(arg.name);
      if (vi && vi.size===2 && !isFixedType(vi.type) && vi.addr!=null) {
        const w0=p.zpUtility.tmp, w1=p.zpUtility.tmp2, w2=p.zpUtility.ptr, w3=p.zpUtility.ptr+1;
        const lo=vi.addr, hi=vi.addr+1;
        if (lo<0x100) e.zp('LDA',lo); else e.abs('LDA',lo);
        e.zp('STA',w0,'word_lo');
        if (hi<0x100) e.zp('LDA',hi); else e.abs('LDA',hi);
        e.zp('STA',w1,'word_hi');
        e.imm('LDA',0); e.zp('STA',w2,'w2=0'); e.zp('STA',w3,'w3=0');
        this._emitDecimalPrint32(vi.type==='int', w0, w1, w2, w3);
        return;
      }
    }

    // ── Literal word (256..65535) ─────────────────────────────────────────
    if (arg.k==='Literal' && typeof arg.value==='number' && arg.value>255 && arg.value<=65535) {
      const v=arg.value&0xFFFF;
      const w0=p.zpUtility.tmp, w1=p.zpUtility.tmp2, w2=p.zpUtility.ptr, w3=p.zpUtility.ptr+1;
      e.imm('LDA',v&0xFF); e.zp('STA',w0,'lit16_lo');
      e.imm('LDA',(v>>8)&0xFF); e.zp('STA',w1,'lit16_hi');
      e.imm('LDA',0); e.zp('STA',w2,'w2=0'); e.zp('STA',w3,'w3=0');
      this._emitDecimalPrint32(false, w0, w1, w2, w3);
      return;
    }

    // ── Default: expr → A → byte decimale ────────────────────────────────
    this.evalExpr(arg);
    this._emitDecimalPrint8FromA();
  }

  _evalCall(node) {
    const e=this.e, p=this.p, name=node.name, args=node.args;
    switch(name) {
      case 'poke': case 'poke16': {
        if (args.length>=2) {
          this._evalWordToPtr(args[0]);
          this.evalExpr(args[1]);
          e.imm('LDY',0,'Y=0'); e.iny('STA',p.zpUtility.ptr,'poke');
        }
        break;
      }
      case 'peek': case 'peek16': {
        if (args.length>=1) {
          this._evalWordToPtr(args[0]);
          e.imm('LDY',0,'Y=0'); e.iny('LDA',p.zpUtility.ptr,'peek');
        }
        break;
      }
      case 'border_color':
        if (args.length>=1) { this.evalExpr(args[0]); e.abs('STA',0xD020,'VIC border'); }
        break;
      case 'screen_color':
        if (args.length>=1) { this.evalExpr(args[0]); e.abs('STA',0xD021,'VIC BG'); }
        break;
      case 'text_color':
        if (args.length>=1) { this.evalExpr(args[0]); e.abs('STA',0x0286,'KERNAL text color'); }
        break;
      case 'clear_screen':
        e.imm('LDA',0x93,'CLR char (147)');
        e.jsr(0xFFD2,'CHROUT clear screen');
        break;
      case 'wait': {
        // wait(n): aspetta n jiffie (~1/60 sec) via jiffy clock $A2
        // Usa elapsed = (jiffy_now - jiffy_start) & $FF — gestisce il wrap
        // wait(60)=1s  wait(200)=3.3s  max affidabile: wait(255)
        if (args.length>=1) {
          const tmp=p.zpUtility.tmp, tmp2=p.zpUtility.tmp2;
          const lW=e.uniq('_wJL');
          this.evalExpr(args[0]);              // A = n
          e.zp('STA',tmp,'wait:n');
          e.abs('LDA',0xA2,'jiffy_start');     // A = jiffy corrente
          e.zp('STA',tmp2,'salva jiffy_start');
          e.label(lW);
          e.abs('LDA',0xA2,'jiffy_now');
          e.imp('SEC');
          e.zp('SBC',tmp2,'elapsed = now - start (unsigned, wrap OK)');
          e.zp('CMP',tmp,'elapsed < n?');
          e.branch('BCC',lW,'attendi');        // BCC: elapsed < n → aspetta
        }
        break;
      }
      case 'wait_frames': {
        if (args.length>=1) {
          const tmp=p.zpUtility.tmp;
          const lO=e.uniq('_wfO'), lA=e.uniq('_wfA'), lB=e.uniq('_wfB');
          this.evalExpr(args[0]); e.zp('STA',tmp,'frames');
          e.label(lO);
          e.label(lA); e.abs('LDA',0xD012,'raster'); e.imm('CMP',0xFF); e.branch('BNE',lA,'wait 255');
          e.label(lB); e.abs('LDA',0xD012); e.imm('CMP',0xFF); e.branch('BEQ',lB,'wait leave');
          e.zp('DEC',tmp); e.branch('BNE',lO,'next frame');
        }
        break;
      }
      case 'print_at': {
        // print_at(col, row, arg1, arg2, …)
        // I primi 2 argomenti sono le coordinate; i successivi vengono stampati
        // uno dopo l'altro con la stessa logica polimorfa di print().
        if (args.length>=3) {
          const colA=args[0], rowA=args[1];
          if (rowA.k==='Literal') e.imm('LDX',rowA.value&0xFF,`row=${rowA.value}`);
          else { this.evalExpr(rowA); e.imp('TAX','row→X'); }
          if (colA.k==='Literal') e.imm('LDY',colA.value&0xFF,`col=${colA.value}`);
          else { this.evalExpr(colA); e.imp('TAY','col→Y'); }
          e.imp('CLC','CLC=set cursor'); e.jsr(0xFFF0,'KERNAL PLOT');
          // Stampa tutti gli argomenti dal terzo in poi
          for (let i=2; i<args.length; i++) this._emitPrintArg(args[i]);
        }
        break;
      }
      case 'print': case 'println': {
        // Polimorfa: stampa tutti gli argomenti uno dopo l'altro.
        // Tipi supportati: string literal, float (FOUT), long/ulong/dword (div32),
        //                  word/int (div32 16-bit), byte (div32 8-bit).
        for (let i=0; i<args.length; i++) this._emitPrintArg(args[i]);
        if (name==='println') { e.imm('LDA',0x0D,'CR'); e.jsr(0xFFD2,'CHROUT CR'); }
        break;
      }
      case 'float_to_str': {
        // Mantiene comportamento originale: stampa float come stringa via FOUT
        if (args.length>=1) this._emitPrintFloat(args[0]);
        break;
      }
      case 'memset': {
        if (args.length>=3) {
          const tmp=p.zpUtility.tmp, tmp2=p.zpUtility.tmp2;
          this._evalWordToPtr(args[0]);
          this.evalExpr(args[1]); e.zp('STA',tmp,'val');
          this.evalExpr(args[2]); e.zp('STA',tmp2,'count');
          const lT=e.uniq('_msT'); const lE=e.uniq('_msE');
          e.imm('LDY',0,'Y=0');
          e.label(lT); e.zp('LDA',tmp); e.iny('STA',p.zpUtility.ptr,'memset');
          e.imp('INY'); e.zp('CPY',tmp2); e.branch('BCC',lT,'loop');
          e.label(lE);
        }
        break;
      }
      // ── Float KERNAL ──────────────────────────────────────────────────────
      // Convenzione CBM: argomento in FAC1 ($61-$65), risultato in FAC1.
      // GIVAYF $B391: Y:A (int 0..65535) → FAC1   [richiede BASIC ROM $37]
      // QINT   $B1AA: FAC1 → int32 al ritorno; LSB in $65
      // _floatCall(arg, jsr_addr): carica FAC1, chiama routine, estrae byte
      case 'sqr':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xBF71,'KERNAL SQR  FAC1=sqrt(FAC1)');
        this._floatGetResult(); break;
      case 'log':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xB9EA,'KERNAL LOG  FAC1=ln(FAC1)');
        this._floatGetResult(); break;
      case 'exp':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xBFED,'KERNAL EXP  FAC1=e^FAC1');
        this._floatGetResult(); break;
      case 'sin':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xE26B,'KERNAL SIN  FAC1=sin(FAC1)');
        this._floatGetResult(); break;
      case 'cos':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xE264,'KERNAL COS  FAC1=cos(FAC1)');
        this._floatGetResult(); break;
      case 'tan':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xE2B4,'KERNAL TAN  FAC1=tan(FAC1)');
        this._floatGetResult(); break;
      case 'atn':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xE30E,'KERNAL ATN  FAC1=atan(FAC1)');
        this._floatGetResult(); break;
      case 'abs':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xBC58,'KERNAL ABS  FAC1=|FAC1|');
        this._floatGetResult(); break;
      case 'floor':
        if(args.length>=1){this.evalExpr(args[0]);this._floatLoadArg();}
        e.jsr(0xBCCC,'KERNAL INT  FAC1=floor(FAC1)');
        this._floatGetResult(); break;
      case 'rnd':
        e.jsr(0xE097,'KERNAL RND  FAC1=rnd()');
        this._floatGetResult(); break;
      // ── Aritmetica float esplicita ────────────────────────────────────────
      // fadd(a,b), fsub(a,b), fmul(a,b), fdiv(a,b), fpow(a,b)
      // Emette FAC2 OP FAC1 → FAC1, poi QINT → A (byte)
      case 'fadd': case 'fsub': case 'fmul': case 'fdiv': case 'fpow': {
        const _fops = {fadd:'+',fsub:'-',fmul:'*',fdiv:'/',fpow:'^'};
        const synthNode = {
          k:'BinaryOp', op:_fops[name], _type:'float',
          left:  args[0]||{k:'Literal',value:0,raw:'0',kind:'int'},
          right: args[1]||{k:'Literal',value:0,raw:'0',kind:'int'}
        };
        if (args[0]) synthNode.left  = Object.assign({},args[0],{_type:args[0]._type||'float'});
        if (args[1]) synthNode.right = Object.assign({},args[1],{_type:args[1]._type||'float'});
        this._evalFloatBinOp(synthNode);
        this._floatGetResult();
        break;
      }
      case 'min': {
        if (args.length>=2) {
          const tmp=p.zpUtility.tmp;
          const lT=e.uniq('_minT');
          this.evalExpr(args[0]); e.zp('STA',tmp);
          this.evalExpr(args[1]); e.zp('CMP',tmp); e.branch('BCC',lT,'A<tmp=A smaller');
          e.zp('LDA',tmp,'tmp is smaller'); e.label(lT);
        }
        break;
      }
      case 'max': {
        if (args.length>=2) {
          const tmp=p.zpUtility.tmp;
          const lT=e.uniq('_maxT');
          this.evalExpr(args[0]); e.zp('STA',tmp);
          this.evalExpr(args[1]); e.zp('CMP',tmp); e.branch('BCS',lT,'A>=tmp=A bigger');
          e.zp('LDA',tmp,'tmp is bigger'); e.label(lT);
        }
        break;
      }
      case 'kernal_chrout':
        if (args.length>=1) { this.evalExpr(args[0]); e.jsr(0xFFD2,'CHROUT'); }
        break;
      case 'kernal_chrin':
        e.jsr(0xFFCF,'CHRIN'); break;
      // ── sgn(n) ───────────────────────────────────────────────────────────
      // sgn(byte n) → byte: 0→0, >0→1  (unsigned / byte)
      // sgn(int n)  → byte: <0→255($FF), 0→0, >0→1  (signed, uses bit 7)
      case 'sgn': {
        if (args.length >= 1) {
          const lDone = e.uniq('_sgnD'), lNeg = e.uniq('_sgnN');
          const argType = (args[0]._type || 'byte');
          const isSigned = (argType === 'int' || argType === 'long');
          this.evalExpr(args[0]);
          if (isSigned) {
            // signed: check bit 7 for negative (result $FF = -1 in 6510 convention)
            e.zp('STA', p.zpUtility.tmp, 'sgn_val_lo');
            e.branch('BMI', lNeg, 'negative → sgn=-1');
            e.imm('LDA', 0, 'sgn_check_zero');
            e.zp('ORA', p.zpUtility.tmp);
            e.branch('BEQ', lDone, 'zero → sgn=0');
            e.imm('LDA', 1, 'positive → sgn=+1');
            e.branch('BEQ', lDone, ''); // BEQ not taken, acts as BRA
            e.label(lNeg);
            e.imm('LDA', 0xFF, 'negative → sgn=-1 ($FF)');
          } else {
            // unsigned byte: 0→0, any>0→1
            e.branch('BEQ', lDone, 'zero → sgn=0 (A already 0)');
            e.imm('LDA', 1, '>0 → sgn=1');
          }
          e.label(lDone);
        }
        break;
      }
      // ── input() → byte ───────────────────────────────────────────────────
      // Blocca finché l'utente preme un tasto; ritorna il codice PETSCII in A.
      // Usa GETIN ($FFE4): non-blocking, ripete finché A≠0.
      case 'input': {
        const lWait = e.uniq('_inpW');
        e.label(lWait);
        e.jsr(0xFFE4, 'GETIN: keyboard buffer → A');
        e.branch('BEQ', lWait, 'no key → loop');
        // A = PETSCII key code
        break;
      }
      // ── plot(x, y, ch) → void ────────────────────────────────────────────
      // Scrive il carattere ch nella screen RAM ($0400) alla colonna x, riga y.
      // Screen addr = $0400 + y*40 + x.
      // y*40 = y*8 + y*32:  entrambi calcolati come 16-bit tramite ptr.
      case 'plot': {
        if (args.length >= 3) {
          const ptr = p.zpUtility.ptr, tmp = p.zpUtility.tmp, tmp2 = p.zpUtility.tmp2;
          // Eval e salva ch in tmp2 prima del calcolo indirizzo
          this.evalExpr(args[2]); e.zp('STA', tmp2, 'ch');
          // Eval y → calcola y*40 (16-bit) in ptr
          this.evalExpr(args[1]);
          // y in A: calcola y*8 → ptr (hi=0 per y≤24)
          e.zp('STA', ptr, 'y'); e.imm('LDA', 0); e.zp('STA', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);   // y*2
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);   // y*4
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);   // y*8 → ptr
          // Salva y*8 in tmp, poi calcola y*32 e somma
          e.zp('LDA', ptr); e.zp('STA', tmp, 'y8_lo');
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);   // y*16
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);   // y*32 → ptr
          // ptr += y*8
          e.imp('CLC'); e.zp('LDA', ptr); e.zp('ADC', tmp); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          // ptr += $0400
          e.imp('CLC'); e.zp('LDA', ptr); e.imm('ADC', 0); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0x04, '$0400 hi'); e.zp('STA', ptr+1);
          // ptr += x
          this.evalExpr(args[0]);
          e.imp('CLC'); e.zp('ADC', ptr); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          // Scrivi ch
          e.imm('LDY', 0); e.zp('LDA', tmp2, 'ch'); e.iny('STA', ptr, 'screen write');
        }
        break;
      }
      // ── draw_line(x, y, len, ch) → void ──────────────────────────────────
      // Disegna una riga orizzontale di len caratteri ch a partire da (x, y).
      // Usa stessa logica di plot per l'indirizzo iniziale, poi INC ptr a ogni step.
      case 'draw_line': {
        if (args.length >= 4) {
          const ptr = p.zpUtility.ptr, tmp = p.zpUtility.tmp, tmp2 = p.zpUtility.tmp2;
          const lLoop = e.uniq('_dlL');
          // Save len in X, ch in tmp2 subito
          this.evalExpr(args[3]); e.zp('STA', tmp2, 'ch');
          this.evalExpr(args[2]); e.imp('TAX', 'X=len');
          // Calcola indirizzo start in ptr (stessa logica di plot)
          this.evalExpr(args[1]);
          e.zp('STA', ptr); e.imm('LDA', 0); e.zp('STA', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('LDA', ptr); e.zp('STA', tmp, 'y8_lo');
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.imp('CLC'); e.zp('LDA', ptr); e.zp('ADC', tmp); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          e.imp('CLC'); e.zp('LDA', ptr); e.imm('ADC', 0); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0x04, '$0400 hi'); e.zp('STA', ptr+1);
          this.evalExpr(args[0]);
          e.imp('CLC'); e.zp('ADC', ptr); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          // Loop: X = counter (len), Y = 0 (colonna relativa)
          e.imm('LDY', 0);
          e.label(lLoop);
          e.zp('LDA', tmp2, 'ch');
          e.iny('STA', ptr, 'write char');
          e.imp('INY', 'next col');
          e.imp('DEX'); e.branch('BNE', lLoop, 'len-- → loop');
        }
        break;
      }
      // ── fill_box(x, y, w, h, ch) → void ──────────────────────────────────
      // Riempie un rettangolo di w×h caratteri ch a partire da (x, y).
      // Usa PHA/PLA per salvare h sullo stack 6510 durante il calcolo dell'indirizzo.
      // Nota: non sicuro dentro raw irq func (stack occupato dal KERNAL).
      case 'fill_box': {
        if (args.length >= 5) {
          const ptr = p.zpUtility.ptr, tmp = p.zpUtility.tmp, tmp2 = p.zpUtility.tmp2;
          const lOuter = e.uniq('_fbO'), lInner = e.uniq('_fbI');
          // ch → tmp2, h → stack via PHA, w → tmp (temporaneo fino a calcolo addr)
          this.evalExpr(args[4]); e.zp('STA', tmp2, 'ch');
          this.evalExpr(args[3]); e.imp('PHA', 'push h'); // h sullo stack
          this.evalExpr(args[2]); e.imp('TAX', 'X=w (ricaricato ogni riga)');
          // Calcola indirizzo start in ptr
          this.evalExpr(args[1]);
          e.zp('STA', ptr); e.imm('LDA', 0); e.zp('STA', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('LDA', ptr); e.zp('STA', tmp, 'y8_lo');
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.zp('ASL', ptr); e.zp('ROL', ptr+1);
          e.imp('CLC'); e.zp('LDA', ptr); e.zp('ADC', tmp); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          e.imp('CLC'); e.zp('LDA', ptr); e.imm('ADC', 0); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0x04, '$0400 hi'); e.zp('STA', ptr+1);
          this.evalExpr(args[0]);
          e.imp('CLC'); e.zp('ADC', ptr); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          // Salva w in tmp (tmp2 = ch è già salvato)
          this.evalExpr(args[2]); e.zp('STA', tmp, 'w');
          // Recupera h dallo stack in A, poi X = w per il loop interno
          e.imp('PLA', 'pull h → A'); e.imp('TAX', 'X=h (outer counter)');
          // Loop esterno: X = righe rimanenti
          e.label(lOuter);
          e.imm('LDY', 0, 'Y=col index');
          // Loop interno: Y < w
          e.label(lInner);
          e.zp('LDA', tmp2, 'ch');
          e.iny('STA', ptr, 'write');
          e.imp('INY');
          e.zp('CPY', tmp, 'compare Y vs w');
          e.branch('BCC', lInner, 'Y<w → continua');
          // Avanza ptr di 40 (prossima riga)
          e.imp('CLC');
          e.zp('LDA', ptr); e.imm('ADC', 40, 'next row +40'); e.zp('STA', ptr);
          e.zp('LDA', ptr+1); e.imm('ADC', 0); e.zp('STA', ptr+1);
          // Ricarica w in X interno... no: DEX outer loop
          e.imp('DEX'); e.branch('BNE', lOuter, 'h-- → continua');
        }
        break;
      }
      // ── draw_box(x, y, w, h, ch) → void ──────────────────────────────────
      // Perimetro di un box w×h con il carattere ch.
      // Top/bottom: righe orizzontali di w char. Lati: colonne sx (Y=0) e dx (Y=w-1).
      // emitRowAddr(xArg): A=y → calcola ptr=$0400+y*40+x (usa tmp come scratch y8).
      // ch in tmp2. y_side salvato in tmp, protetto da PHA/PLA attorno a emitRowAddr.
      case 'draw_box': {
        if (args.length >= 5) {
          const ptr=p.zpUtility.ptr, tmp=p.zpUtility.tmp, tmp2=p.zpUtility.tmp2;
          // ch → tmp2 (persiste per tutta la funzione; emitRowAddr usa solo tmp e ptr)
          this.evalExpr(args[4]); e.zp('STA',tmp2,'ch');
          // emitRowAddr: A=y_value all'entrata → ptr = $0400 + y*40 + xArg
          const emitRowAddr = (xArg) => {
            // A = y
            e.zp('STA',ptr); e.imm('LDA',0); e.zp('STA',ptr+1);
            e.zp('ASL',ptr); e.zp('ROL',ptr+1);                   // y*2
            e.zp('ASL',ptr); e.zp('ROL',ptr+1);                   // y*4
            e.zp('ASL',ptr); e.zp('ROL',ptr+1);                   // y*8
            e.zp('LDA',ptr); e.zp('STA',tmp,'y8_lo');             // salva y*8.lo
            e.zp('ASL',ptr); e.zp('ROL',ptr+1);                   // y*16
            e.zp('ASL',ptr); e.zp('ROL',ptr+1);                   // y*32
            e.imp('CLC');
            e.zp('LDA',ptr); e.zp('ADC',tmp); e.zp('STA',ptr);   // y*40 lo
            e.zp('LDA',ptr+1); e.imm('ADC',0); e.zp('STA',ptr+1); // carry
            e.imp('CLC');
            e.zp('LDA',ptr+1); e.imm('ADC',0x04,'$0400 hi'); e.zp('STA',ptr+1);
            if (xArg !== null) {
              this.evalExpr(xArg);
              e.imp('CLC'); e.zp('ADC',ptr); e.zp('STA',ptr);
              e.zp('LDA',ptr+1); e.imm('ADC',0); e.zp('STA',ptr+1);
            }
          };
          // helper: riga orizzontale di w char (X=w, Y=0→w-1)
          const emitHLine = () => {
            const lH=e.uniq('_dbH'); e.imm('LDY',0); e.label(lH);
            e.zp('LDA',tmp2); e.iny('STA',ptr,'hline'); e.imp('INY');
            e.imp('DEX'); e.branch('BNE',lH,'');
          };
          // ── Top row: y, w char
          this.evalExpr(args[1]); emitRowAddr(args[0]);
          this.evalExpr(args[2]); e.imp('TAX','X=w'); emitHLine();
          // ── Bottom row: y+h-1, w char
          this.evalExpr(args[1]); e.zp('STA',tmp,'y_tmp');
          this.evalExpr(args[3]);                              // A=h
          e.imp('CLC'); e.zp('ADC',tmp);                       // A=y+h
          e.imp('SEC'); e.imm('SBC',1,'y+h-1');
          emitRowAddr(args[0]);
          this.evalExpr(args[2]); e.imp('TAX','X=w'); emitHLine();
          // ── Colonne laterali: y+1 → y+h-2 (skip se h<=2)
          this.evalExpr(args[3]); e.imp('SEC'); e.imm('SBC',2,'h-2');
          e.imp('TAX','X=h-2');
          const lSkip=e.uniq('_dbSK'); e.branch('BEQ',lSkip,'h<=2: no sides');
          // tmp = y_side (parte da y+1). emitRowAddr sovrascrive tmp con y8_lo
          // → salviamo y_side sullo stack (PHA) prima di emitRowAddr, recuperiamo dopo (PLA)
          this.evalExpr(args[1]); e.imp('CLC'); e.imm('ADC',1); e.zp('STA',tmp,'y_side=y+1');
          const lSide=e.uniq('_dbS');
          e.label(lSide);
          // -- Carica y_side, emetti indirizzo, poi recupera
          e.zp('LDA',tmp,'y_side'); e.imp('PHA','save y_side');
          emitRowAddr(args[0]); // sovrascrive tmp con y8_lo
          // -- Colonna sinistra (Y=0)
          e.imm('LDY',0); e.zp('LDA',tmp2,'ch'); e.iny('STA',ptr,'left col');
          // -- Colonna destra (Y=w-1): ptr già punta a riga+x, Y=w-1 → col x+w-1
          this.evalExpr(args[2]); e.imp('SEC'); e.imm('SBC',1); e.imp('TAY','Y=w-1');
          e.zp('LDA',tmp2,'ch'); e.iny('STA',ptr,'right col');
          // -- Ripristina y_side e incrementa
          e.imp('PLA','restore y_side'); e.imp('CLC'); e.imm('ADC',1);
          e.zp('STA',tmp,'y_side++');
          e.imp('DEX'); e.branch('BNE',lSide,'prossima riga');
          e.label(lSkip);
        }
        break;
      }
      // ── Fixed-Point builtins ──────────────────────────────────────────────
      // fp_int(x) : parte intera di q8_8/sq8_8 — estrae il byte hi (signed/unsigned)
      //             su sq8_8: byte hi è intero signed (-128..+127), ma come valore
      //             in A viene trattato come $00..$FF — l'ADC/SBC a 8 bit di 'by'
      //             funziona correttamente per wrap (es. -2 = $FE → by -= 2 ✓)
      // fp_frac(x): parte frazionaria (byte basso) — valori 0..255 = 0..255/256
      case 'fp_int': {
        if (args.length>=1) {
          const a=args[0], fpVar=a.k==='Ident'?this._var(a.name):null;
          if (fpVar&&fpVar.addr!=null&&fpVar.size>=2) {
            const hiAddr=fpVar.addr+1;
            if(hiAddr<0x100) e.zp('LDA',hiAddr,`fp_int(${fpVar.name})`);
            else             e.abs('LDA',hiAddr,`fp_int(${fpVar.name})`);
          } else {
            this.evalExpr(a);
          }
        }
        break;
      }
      case 'fp_frac': {
        if (args.length>=1) {
          const a=args[0], fpVar=a.k==='Ident'?this._var(a.name):null;
          if (fpVar&&fpVar.addr!=null&&fpVar.size>=2) {
            if(fpVar.addr<0x100) e.zp('LDA',fpVar.addr,`fp_frac(${fpVar.name})`);
            else e.abs('LDA',fpVar.addr,`fp_frac(${fpVar.name})`);
          } else {
            this.evalExpr(a);
          }
        }
        break;
      }
      // ── IRQ / CPU control ─────────────────────────────────────────────────
      case 'sei': e.imp('SEI','disable IRQ'); break;
      case 'cli': e.imp('CLI','enable IRQ');  break;
      case 'ack_raster_irq':
        // Ack VIC-II raster IRQ soltanto.
        // Non chiamare $EA31: siamo già stati chiamati da esso via ($0314).
        // Il KERNAL ha già fatto jiffy/CIA prima di chiamarci.
        e.imm('LDA',1,'ack VIC IRQ'); e.abs('STA',0xD019,'VIC $D019 ack');
        break;
      case 'pass_irq_to_kernal':
        // Per handler che vogliono cedere il controllo al KERNAL
        // (es. handler multipli). NON usare se sei l'unico handler.
        e.jmp(0xEA81,'JMP $EA81: KERNAL IRQ return (ripristina reg, RTI)');
        break;
      case 'ack_raster_irq_fast':
        e.imm('LDA',1); e.abs('STA',0xD019,'VIC IRQ ack (fast, no KERNAL)');
        break;
      case 'enable_raster_irq':
        if (args.length>=1) {
          e.imp('SEI','--- setup raster IRQ ---');
          this.evalExpr(args[0]);
          e.abs('STA',0xD012,'raster line $D012');
          e.abs('LDA',0xD011,'$D011'); e.imm('AND',0x7F,'clear raster bit8'); e.abs('STA',0xD011);
          e.imm('LDA',1); e.abs('STA',0xD01A,'enable VIC raster IRQ');
          e.imm('LDA',0xFF); e.abs('STA',0xD019,'clear pending IRQ flags');
          e.imp('CLI','--- raster IRQ attivo ---');
        }
        break;
      case 'disable_raster_irq':
        e.imm('LDA',0); e.abs('STA',0xD01A,'disable VIC raster IRQ'); break;
      case 'raster_sync': {
        // raster_sync(line): aspetta il raster esatto — tecnica stable-raster
        // Usato all'inizio dell'handler per sincronizzare dopo il jitter KERNAL.
        // Algoritmo: loop until D012 < line, poi loop until D012 == line.
        if (args.length >= 1) {
          const lBef=e.uniq('_rsB'), lEq=e.uniq('_rsE');
          this.evalExpr(args[0]);     // A = target line
          e.zp('STA',p.zpUtility.tmp,'sync_line');
          // Fase 1: aspetta che D012 sia strettamente < target
          // (gestisce il caso in cui siamo già sulla linea o l'abbiamo appena passata)
          e.label(lBef);
          e.abs('LDA',0xD012,'raster now');
          e.zp ('CMP',p.zpUtility.tmp,'vs target');
          e.branch('BCS',lBef,'>= target: aspetta che passi');
          // Fase 2: aspetta == target
          e.label(lEq);
          e.abs('LDA',0xD012,'raster now');
          e.zp ('CMP',p.zpUtility.tmp,'vs target');
          e.branch('BNE',lEq,'non ancora: aspetta');
        }
        break;
      }
      case 'raster_sync_exact': {
        // raster_sync_exact(line): versione a ciclo singolo senza fase 1
        // Usare quando si è CERTI di non aver ancora raggiunto la linea.
        if (args.length >= 1) {
          const lEq=e.uniq('_rxE');
          this.evalExpr(args[0]);
          e.zp('STA',p.zpUtility.tmp,'sync_line');
          e.label(lEq);
          e.abs('LDA',0xD012);
          e.zp ('CMP',p.zpUtility.tmp);
          e.branch('BNE',lEq,'aspetta linea esatta');
        }
        break;
      }
      case 'next_raster':
        if (args.length>=1) {
          this.evalExpr(args[0]); e.abs('STA',0xD012,'next raster line $D012');
        }
        break;
      case 'set_irq_vector':
        // Installa handler all'IRQ KERNAL vector $0314/$0315
        if (args.length>=1 && args[0].k==='Ident') {
          const hname=args[0].name;
          e.imp('SEI','install IRQ vector');
          e.immLo(hname,`${hname} lo`); e.abs('STA',0x0314,'KERNAL IRQ vector lo');
          e.immHi(hname,`${hname} hi`); e.abs('STA',0x0315,'KERNAL IRQ vector hi');
          e.imp('CLI','IRQ vector installed');
        }
        break;
      case 'set_nmi_vector':
        if (args.length>=1 && args[0].k==='Ident') {
          const hname=args[0].name;
          e.immLo(hname,`${hname} lo`); e.abs('STA',0x0318,'NMI vector lo');
          e.immHi(hname,`${hname} hi`); e.abs('STA',0x0319,'NMI vector hi');
        }
        break;
      case 'sys': case 'jsr':
        if (args.length>=1&&args[0].k==='Literal') e.jsr(args[0].value,'sys/jsr');
        break;
      default: {
        // Chiamata a funzione definita dall'utente
        const funcSym=this.s.lookup(name);
        if (funcSym&&funcSym.kind==='func') {
          // Controlla se è inline
          const fdecl=this._ast&&this._ast.funcs.find(f=>f.name===name);
          if (fdecl&&fdecl.isInline&&args.length===0) {
            // True inline expansion: emetti il corpo senza JSR/RTS.
            // Salva frameVars corrente, espandi, ripristina.
            const savedFrame = new Map(this.frameVars);
            const savedInline = this._inlineExpanding;
            this._inlineExpanding = true;   // flag: genFunc non emette RTS
            // Reinizializza frameVars per la funzione inlineata
            const layout = this.p.funcLayouts.get(name) || {locals:[]};
            this.frameVars = new Map();
            layout.locals.filter(v=>!v.isArr&&v.addr!=null).forEach(v=>{
              this.frameVars.set(v.name,{name:v.name,addr:v.addr,
                label:v.label||null,type:v.type,size:v.size,isZP:v.addr<0x100});
            });
            this.emitBlock(fdecl.body); // corpo senza RTS
            this._inlineExpanding = savedInline;
            this.frameVars = savedFrame;
          } else {
            const params=this._funcParamAddrs.get(name)||[];
            args.forEach((arg,i)=>{
              this.evalExpr(arg);
              if (i<params.length) {
                const pa=params[i].addr;
                if(pa<0x100) e.zp('STA',pa,`arg${i}:${params[i].name}`);
                else e.abs('STA',pa,`arg${i}:${params[i].name}`);
              }
            });
            e.jsr(name,`call ${name}()`);
          }
        } else {
          e.imp('NOP',`/* unknown: ${name} */`);
        }
        break;
      }
    }
  }
}

// Stato globale: ultimo builder (per doExport senza ricompilare)
let _lastBuilder  = null;
let _lastFilename = 'untitled.prg';

// ── Download PRG ──────────────────────────────────────────────────────────
function downloadPRG(bytes, filename) {
  const blob = new Blob([bytes], { type:'application/octet-stream' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}