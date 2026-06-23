// ═══════════════════════════════════════════════════════════════════════════
//  SEMANTIC ANALYZER — Fase 2b
//  • Costruisce la tabella dei simboli (Scope globale + locale per funzione)
//  • Annota ogni nodo espressione con _type
//  • Emette errori semantici e warning
// ═══════════════════════════════════════════════════════════════════════════
class SemanticAnalyzer {
  constructor(ast) {
    this.ast       = ast;
    this.errors    = [];
    this.warnings  = [];
    this.global    = new Scope(null, 'global');
    this.cur       = this.global;
    this.curFunc   = null;
    this.loopDepth = 0;    // contatore cicli annidati — per validare break/continue
    this.annotated = 0;   // nodi con _type assegnato
  }

  // ── entry point ──────────────────────────────────────────────────────────
  analyze() {
    this._pass1();
    this._check(this.ast);
    return {
      errors:    this.errors,
      warnings:  this.warnings,
      global:    this.global,
      annotated: this.annotated
    };
  }

  _err(msg, node) {
    const line = node?.line ?? 0;
    this.errors.push({ msg, line, col: 0 });
  }
  _warn(msg, node) {
    const line = node?.line ?? 0;
    this.warnings.push({ msg, line, col: 0 });
  }

  // ── Primo passaggio: registra globali e firme funzioni ──────────────────
  _pass1() {
    this.ast.globals.forEach(g => {
      if (this.global.symbols.has(g.name))
        this._err(`'${g.name}' già dichiarato globalmente`, g);
      else {
        const arrCount = g.isArr ? this._constEval(g.arrSize) : null;
        this.global.define(g.name, {
          type: g.type, kind: 'var', isArr: g.isArr, arrCount, line: g.line
        });
      }
    });
    this.ast.funcs.forEach(f => {
      if (this.global.symbols.has(f.name))
        this._err(`Funzione '${f.name}' già dichiarata`, f);
      else
        this.global.define(f.name, {
          type: f.ret||'void', kind: 'func', params: f.params, line: f.line
        });
    });
    if (!this.global.symbols.has('main'))
      this._warn("Funzione 'main' non trovata — entry point mancante");
  }

  // Valutazione costante a compile-time (solo per arrSize)
  _constEval(node) {
    if (!node) return null;
    if (node.k === 'Literal') return node.value;
    if (node.k === 'Ident') {
      const s = this.global.lookup(node.name);
      return (s && s.constVal != null) ? s.constVal : null;
    }
    return null;
  }

  _pushScope(name) { this.cur = new Scope(this.cur, name); return this.cur; }
  _popScope()      { this.cur = this.cur.parent; }

  // Annota un nodo con il suo tipo e incrementa il contatore
  _ann(node, type) {
    if (node && node._type === undefined) { node._type = type; this.annotated++; }
    return type;
  }

  // ── Inferenza del tipo di un'espressione ────────────────────────────────
  _typeOf(node) {
    if (!node)         return 'void';
    if (node._type !== undefined) return node._type;

    switch(node.k) {
      case 'Literal': {
        let t;
        if      (node.kind==='float')               t = 'float';
        else if (node.kind==='str')                 t = 'string';
        else if (node.kind==='bool')                t = 'bool';
        else {  // int / hex / bin
          const v = node.value;
          t = (v <= 255) ? 'byte' : (v <= 65535) ? 'word' : 'long';
        }
        return this._ann(node, t);
      }
      case 'Ident': {
        const s = this.cur.lookup(node.name);
        if (!s) { this._err(`Variabile non dichiarata: '${node.name}'`, node); return this._ann(node,'unknown'); }
        if (s.kind === 'func') { this._warn(`'${node.name}' è una funzione — mancano le parentesi?`, node); }
        return this._ann(node, s.type);
      }
      case 'ArrayAccess': {
        const s = this.cur.lookup(node.name);
        if (!s) { this._err(`'${node.name}' non dichiarato`, node); return this._ann(node,'unknown'); }
        if (!s.isArr) this._warn(`'${node.name}' non è un array`, node);
        this._typeOf(node.idx);
        return this._ann(node, s.type);
      }
      case 'Cast':
        this._typeOf(node.expr);
        return this._ann(node, node.type);
      case 'Call': {
        node.args.forEach(a => this._typeOf(a));
        const sym = this.global.lookup(node.name);
        if (sym && sym.kind === 'func') {
          if (sym.params && node.args.length !== sym.params.length)
            this._err(`'${node.name}': attesi ${sym.params.length} argomenti, trovati ${node.args.length}`, node);
          return this._ann(node, sym.type||'void');
        }
        if (C64_BUILTINS.has(node.name)) return this._ann(node, builtinRetType(node.name, node.args));
        this._err(`Funzione '${node.name}' non dichiarata`, node);
        return this._ann(node, 'unknown');
      }
      case 'BinaryOp': {
        const lt = this._typeOf(node.left);
        const rt = this._typeOf(node.right);
        // '^' su float = FPOW; su int = XOR bit — lo stesso nodo, distinto a codegen
        return this._ann(node, promoteTypes(lt, rt));
      }
      case 'UnaryOp':
      case 'PostfixOp':
        return this._ann(node, this._typeOf(node.operand));
      case 'Assign': {
        const lt = this._typeOf(node.target);
        const rt = this._typeOf(node.value);
        if (lt !== 'unknown' && rt !== 'unknown') {
          if (rt === 'float' && lt !== 'float')
            this._warn(`Assegnamento float→${lt}: possibile perdita di precisione`, node);
          if (rt === 'string' && lt !== 'string')
            this._warn(`Assegnamento string→${lt}: tipo incompatibile`, node);
          if (is32Type(lt) && !is32Type(rt) && !isFixedType(rt) && rt !== 'unknown')
            this._warn(`Assegnamento ${rt}→${lt}: zero-extend a 32 bit`, node);
          // Warning informativo per conversioni fp ↔ intero
          if (isFixedType(lt) && !isFixedType(rt) && rt !== 'unknown')
            this._warn(`Assegnamento ${rt}→${lt}: valore trattato come parte intera`, node);
          if (isFixedType(rt) && !isFixedType(lt) && lt !== 'unknown')
            this._warn(`Assegnamento ${rt}→${lt}: estratta parte intera (fp_int)`, node);

          // ── Warning: valore negativo assegnato a tipo unsigned ─────────
          const UNSIGNED = new Set(['byte','word','uint','ulong','dword']);
          if (UNSIGNED.has(lt)) {
            const isNegLit = node.value.k==='UnaryOp' && node.value.op==='-' &&
                             node.value.operand?.k==='Literal';
            if (isNegLit) {
              const v = node.value.operand.value;
              const tgt = node.target.k==='Ident' ? node.target.name : '?';
              this._warn(
                `'${tgt}': valore negativo (−${v}) assegnato a tipo unsigned '${lt}' — verrà memorizzato come ${
                  lt==='byte'  ? (256-v)&0xFF :
                  (lt==='word'||lt==='uint') ? (65536-v)&0xFFFF :
                  ((4294967296-v)>>>0)
                }`, node);
            }
            const isPosLit = node.value.k==='Literal' && typeof node.value.value==='number';
            if (isPosLit) {
              const v = node.value.value;
              const over =
                (lt==='byte'  && v>255)        ? {max:255,       stored:v&0xFF} :
                (lt==='word'  && v>65535)       ? {max:65535,     stored:v&0xFFFF} :
                (lt==='uint'  && v>65535)       ? {max:65535,     stored:v&0xFFFF} :
                (lt==='ulong' && v>4294967295)  ? {max:4294967295,stored:v>>>0} :
                (lt==='dword' && v>4294967295)  ? {max:4294967295,stored:v>>>0} :
                null;
              if (over) {
                const tgt = node.target.k==='Ident' ? node.target.name : '?';
                this._warn(
                  `'${tgt}': valore ${v} eccede il range di '${lt}' (0–${over.max}) — verrà troncato a ${over.stored}`, node);
              }
            }
          }
          // ── Warning: overflow signed ───────────────────────────────────
          const SIGNED = { int:[-32768,32767], long:[-2147483648,2147483647] };
          if (SIGNED[lt]) {
            const [mn,mx] = SIGNED[lt];
            let v = null;
            if (node.value.k==='Literal') v = node.value.value;
            else if (node.value.k==='UnaryOp' && node.value.op==='-' &&
                     node.value.operand?.k==='Literal') v = -node.value.operand.value;
            if (v!==null && (v<mn || v>mx)) {
              const tgt = node.target.k==='Ident' ? node.target.name : '?';
              this._warn(
                `'${tgt}': valore ${v} fuori range di '${lt}' (${mn}–${mx})`, node);
            }
          }
        }
        return this._ann(node, lt);
      }
      default:
        return 'void';
    }
  }

  // ── Secondo passaggio: visita ricorsiva completa ─────────────────────────
  _check(node) {
    if (!node) return;
    switch(node.k) {
      case 'Program':
        node.globals.forEach(g => this._check(g));
        node.funcs.forEach(f => this._check(f));
        break;

      case 'FuncDecl': {
        this.curFunc = node;
        const scope = this._pushScope(`func:${node.name}`);
        node.params.forEach(p =>
          scope.define(p.name, { type:p.type, kind:'param', isArr:p.isArr })
        );
        this._check(node.body);
        this._popScope();
        this.curFunc = null;
        break;
      }
      case 'VarDecl': {
        const alreadyGlobal = this.cur === this.global && this.cur.symbols.has(node.name);
        if (!alreadyGlobal) {
          if (this.cur.symbols.has(node.name))
            this._warn(`'${node.name}' ridichiarato nello stesso scope`, node);
          this.cur.define(node.name, {
            type: node.type, kind: 'var', isArr: node.isArr,
            arrCount: node.isArr ? this._constEval(node.arrSize) : null,
            line: node.line
          });
        }
        this._ann(node, node.type);
        if (node.init) {
          const it = this._typeOf(node.init);
          if (it==='float' && node.type!=='float')
            this._warn(`Inizializzatore float→${node.type} (troncamento)`, node);

          // ── Warning: valore negativo assegnato a tipo unsigned ─────────
          const UNSIGNED = new Set(['byte','word','uint','ulong','dword']);
          if (UNSIGNED.has(node.type)) {
            // Caso 1: letterale negativo diretto  → byte z = -123
            const isNegLit = node.init.k === 'UnaryOp' && node.init.op === '-' &&
                             node.init.operand && node.init.operand.k === 'Literal';
            if (isNegLit) {
              const v = node.init.operand.value;
              this._warn(
                `'${node.name}': valore negativo (−${v}) assegnato a tipo unsigned '${node.type}' — verrà memorizzato come ${
                  node.type === 'byte'  ? (256 - v) & 0xFF :
                  node.type === 'word' || node.type === 'uint' ? (65536 - v) & 0xFFFF :
                  ((4294967296 - v) >>> 0)
                }`, node);
            }
            // Caso 2: overflow letterale positivo  → byte z = 300
            const isPosLit = node.init.k === 'Literal' && typeof node.init.value === 'number';
            if (isPosLit) {
              const v = node.init.value;
              const over =
                (node.type === 'byte'  && v > 255)   ? { max: 255,       stored: v & 0xFF } :
                (node.type === 'word'  && v > 65535)  ? { max: 65535,     stored: v & 0xFFFF } :
                (node.type === 'uint'  && v > 65535)  ? { max: 65535,     stored: v & 0xFFFF } :
                (node.type === 'ulong' && v > 4294967295) ? { max: 4294967295, stored: v >>> 0 } :
                (node.type === 'dword' && v > 4294967295) ? { max: 4294967295, stored: v >>> 0 } :
                null;
              if (over) {
                this._warn(
                  `'${node.name}': valore ${v} eccede il range di '${node.type}' (0–${over.max}) — verrà troncato a ${over.stored}`, node);
              }
            }
          }
          // ── Warning: overflow signed ───────────────────────────────────
          const SIGNED = { int: [-32768, 32767], long: [-2147483648, 2147483647] };
          if (SIGNED[node.type]) {
            const [mn, mx] = SIGNED[node.type];
            let v = null;
            if (node.init.k === 'Literal') v = node.init.value;
            else if (node.init.k === 'UnaryOp' && node.init.op === '-' &&
                     node.init.operand?.k === 'Literal') v = -node.init.operand.value;
            if (v !== null && (v < mn || v > mx))
              this._warn(
                `'${node.name}': valore ${v} fuori range di '${node.type}' (${mn}–${mx})`, node);
          }
        }
        if (node.arrInit) node.arrInit.forEach(x => this._typeOf(x));
        break;
      }
      case 'Block':
        this._pushScope('block');
        node.stmts.forEach(s => s && this._check(s));
        this._popScope();
        break;

      // Espressioni
      case 'Assign': case 'BinaryOp': case 'UnaryOp': case 'PostfixOp':
      case 'Cast': case 'Ident': case 'ArrayAccess': case 'Literal': case 'Call':
        this._typeOf(node);
        break;

      case 'If':
        this._typeOf(node.cond);
        this._check(node.then);
        if (node.else) this._check(node.else);
        break;

      case 'While': case 'DoWhile':
        this._typeOf(node.cond);
        this.loopDepth++;
        this._check(node.body);
        this.loopDepth--;
        break;

      case 'For':
        if (node.init) this._check(node.init);
        if (node.cond) this._typeOf(node.cond);
        if (node.incr) this._typeOf(node.incr);
        this.loopDepth++;
        this._check(node.body);
        this.loopDepth--;
        break;

      case 'Break':
        if (this.loopDepth === 0)
          this._err(`'break' fuori da un ciclo`, node);
        break;

      case 'Continue':
        if (this.loopDepth === 0)
          this._err(`'continue' fuori da un ciclo`, node);
        break;

      case 'Return': {
        if (node.value) {
          const rt = this._typeOf(node.value);
          if (this.curFunc && this.curFunc.ret !== 'void' && rt !== 'unknown') {
            const expected = this.curFunc.ret;
            if (promoteTypes(rt, expected) !== expected)
              this._warn(`Return '${rt}' in funzione '${this.curFunc.name}' (ret=${expected})`, node);
          }
        } else if (this.curFunc && this.curFunc.ret && this.curFunc.ret !== 'void') {
          this._warn(`Return senza valore in '${this.curFunc.name}' (ret=${this.curFunc.ret})`, node);
        }
        break;
      }
    }
  }
}