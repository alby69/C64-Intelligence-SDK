// ═══════════════════════════════════════════════════════════════════════════
//  COMPILE — 5 fasi: Lexer → Parser → Semantica → MemPlan → PRGBuilder
// ═══════════════════════════════════════════════════════════════════════════
function doCompile() {
  clearOutput();
  const logTab = document.querySelector('.panel-tab');
  switchTab('log', logTab);
  _lastBuilder = null;

  const src = cm.getValue();
  logSection('C64PY Compiler v0.6 — Fase 3 · Passo 2 — Code Gen');
  log(`[SRC]  ${src.split('\n').length} linee · ${src.length} caratteri`, 'info');
  log(`[TGT]  MOS 6510 · Load $0801 · PRG`, 'info');
  log('', 'info');

  // ── [1/5] Lexer ────────────────────────────────────────────────────────
  const t0 = performance.now();
  let tokens, lexErrors;
  try {
    ({tokens, errors: lexErrors} = new Lexer(src).tokenize());
  } catch(e) {
    log(`[FATAL] Lexer: ${e.message}`, 'error');
    setStatus('ERRORE LEXER','err'); return;
  }
  const lexMs = (performance.now()-t0).toFixed(2);
  const real  = tokens.filter(t=>t.type!==TT.EOF);
  document.getElementById('sb-tokens').textContent = real.length;
  if (lexErrors.length) {
    logSection(`Errori Lexer (${lexErrors.length})`);
    lexErrors.forEach(e=>log(`  ✕ [${e.line}:${e.col}] ${e.msg}`,'error'));
    setStatus(`LEXER: ${lexErrors.length} ERRORI`,'err'); return;
  }
  log(`[1/5] Lexer     : ${real.length} token  (${lexMs}ms)`, 'ok');

  // ── [2/5] Parser ───────────────────────────────────────────────────────
  const t1 = performance.now();
  let ast, parseErrors;
  try {
    const parser = new Parser(tokens);
    ast          = parser.parse();
    parseErrors  = parser.errors;
    const parseMs = (performance.now()-t1).toFixed(2);
    document.getElementById('sb-nodes').textContent = parser.nodeCount;
    if (parseErrors.length) {
      logSection(`Errori Parser (${parseErrors.length})`);
      parseErrors.forEach(e=>log(`  ✕ [${e.line}:${e.col}] ${e.msg}`,'error'));
      log('','info');
    }
    log(`[2/5] Parser    : ${parser.nodeCount} nodi  (${parseMs}ms)  `
      + `${ast.funcs.length} func · ${ast.globals.length} glob`, parseErrors.length?'warn':'ok');
  } catch(e) {
    log(`[FATAL] Parser: ${e.message}`,'error');
    setStatus('ERRORE PARSER','err'); return;
  }

  // ── [3/5] Semantica ────────────────────────────────────────────────────
  const t2 = performance.now();
  let sem;
  try {
    sem = new SemanticAnalyzer(ast).analyze();
    const semMs = (performance.now()-t2).toFixed(2);
    const errC = sem.errors.length, warnC = sem.warnings.length;
    if (errC || warnC) {
      logSection(`Semantica — ${errC} errori · ${warnC} warning`);
      sem.errors  .forEach(e=>log(`  ✕ [${e.line}] ${e.msg}`,'error'));
      sem.warnings.forEach(w=>log(`  ⚠ [${w.line}] ${w.msg}`,'warn'));
      log('','info');
    }
    log(`[3/5] Semantica : ${sem.annotated} nodi tipizzati  (${semMs}ms)  ${errC}err · ${warnC}warn`, errC?'warn':'ok');
  } catch(e) {
    log(`[FATAL] SemanticAnalyzer: ${e.message}`,'error');
    setStatus('ERRORE SEMANTICO','err'); return;
  }

  // ── [4/5] Memory Planner ──────────────────────────────────────────────
  const t3 = performance.now();
  const qk = analyzeAST(ast);
  const usesFloat = qk.usesFloat;
  const prg = makePRGHeaderPreview(usesFloat);
  let planner;
  try {
    planner = new MemoryPlanner(ast, sem.global, usesFloat).plan();
    const planMs = (performance.now()-t3).toFixed(2);
    const s = planner.summary();
    log(`[4/5] MemPlan   : ZP ${s.zpUsed}/${s.zpTotal}B  BSS ${planner.bssSize}B  (${planMs}ms)`, 'ok');
  } catch(e) {
    log(`[FATAL] MemoryPlanner: ${e.message}`,'error');
    setStatus('ERRORE MEMORY PLAN','err'); return;
  }

  // ── [5/5] PRG Builder — Fase 3 Passo 1 ────────────────────────────────
  const t4 = performance.now();
  let builder;
  try {
    builder = new PRGBuilder(ast, planner, usesFloat, sem.global).build();
    try {
      const basicGen = new BASICGenerator(ast);
      document.getElementById('basic-code').textContent = basicGen.generate();
    } catch(e) { console.error("BASIC Gen error:", e); }
    const buildMs = (performance.now()-t4).toFixed(2);
    _lastBuilder  = builder;
    _lastFilename = (document.getElementById('filename-display').textContent || 'out').replace(/\.c64$/,'') + '.prg';

    if (builder.fixupErrs.length) {
      logSection(`Fixup errors (${builder.fixupErrs.length})`);
      builder.fixupErrs.forEach(e=>log(`  ✕ ${e}`,'error'));
      log('','info');
    }
    log(`[5/5] PRGBuilder: ${builder.prgSize()} byte  stub+code  (${buildMs}ms)  ${builder.fixupErrs.length ? builder.fixupErrs.length+'err' : 'OK'}`,
        builder.fixupErrs.length ? 'warn' : 'ok');
  } catch(e) {
    log(`[FATAL] PRGBuilder: ${e.message}`,'error');
    setStatus('ERRORE CODEGEN','err'); return;
  }

  const totalMs = (performance.now()-t0).toFixed(2);
  log('', 'info');

  // ── Riepilogo ──────────────────────────────────────────────────────────
  logSection('AST');
  log(`  Funzioni:    ${ast.funcs.length}  [${ast.funcs.map(f=>f.name).join(', ')}]`, 'info');
  log(`  Glob/Loc:    ${ast.globals.length} / ${qk.localVars}`, 'info');
  log(`  Chiamate:    ${qk.callCount}`, 'info');
  log('','info');

  logSection('Tabella Simboli');
  [...sem.global.symbols.entries()].forEach(([name,sym])=>{
    const k = sym.kind==='func' ? '⨍' : sym.isArr ? '[]' : '·';
    const v = sym.kind==='func'
      ? `(${(sym.params||[]).map(p=>p.type).join(',')}) → ${sym.type}`
      : `${sym.type}${sym.isArr?'['+( sym.arrCount||'?')+']':''}`;
    log(`  ${k} ${name.padEnd(18)} ${v}`, 'info');
  });
  log('','info');

  logSection('Memory / PRG');
  log(`  $01 config : ${usesFloat ? '$37  BASIC ROM visibile' : '$36  BASIC ROM → RAM (+8KB)'}`, usesFloat?'warn':'ok');
  log(`  ZP usata   : $02–$${(planner.zpNext-1).toString(16).toUpperCase().padStart(2,'0')}  (${planner.summary().zpUsed}B)`, 'ok');
  if (planner.bssSize) log(`  BSS        : ${planner.bssSize}B`, 'info');
  log('','info');
  log(`  PRG size   : ${builder.prgSize()} byte  (header 2 + stub 12 + code ${builder.codeSize()} + BSS ${planner.bssSize})`, 'ok');
  log(`  BASIC stub : $0801–$080C  "0 SYS2061"`, 'info');
  log(`  Code start : $${hex4(PRG_CODE_OFFSET)}`, 'info');
  log(`  Funzioni   : ${ast.funcs.length}  [${ast.funcs.map(f=>f.name).join(', ')}] — codice reale`, 'ok');
  if (builder.fixupErrs.length===0)
    log(`  Fixup      : tutti risolti ✓`, 'ok');

  document.getElementById('sb-mem').textContent = usesFloat ? '$37' : '$36';

  // ── Render ─────────────────────────────────────────────────────────────
  renderAST(ast);
  renderListing(builder, planner);
  renderBytes(builder);

  // ── Conclusione ────────────────────────────────────────────────────────
  log('','info');
  const totErr = lexErrors.length + parseErrors.length + sem.errors.length + builder.fixupErrs.length;
  if (totErr === 0) {
    log(`[OK] Compilazione completata in ${totalMs}ms — nessun errore.`, 'ok');
    log(`[OK] PRG scaricabile: ${builder.prgSize()} byte  (↓ EXPORT PRG)`, 'ok');
    log(`[OK] Code gen funzioni: ATTIVO — corpi reali generati.`, 'ok');
    log(`[OK] Tab BYTES: hex dump PRG disponibile.`, 'ok');
    setStatus(`OK · ${builder.prgSize()}B · $${usesFloat?'37':'36'} · Passo2`, 'ok');
  } else {
    log(`[!!] Completato con ${totErr} errori.`, 'warn');
    setStatus(`${totErr} ERRORI`, 'err');
  }
}