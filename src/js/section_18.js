// ═══════════════════════════════════════════════════════════════════════════
//  RENDER MEMORY MAP — Tab ASM  (legacy Fase 2b, ora sostituita da renderListing)
// ═══════════════════════════════════════════════════════════════════════════
function renderMemoryMap(planner, prg, ast) {
  const area = document.getElementById('asm-area');
  area.innerHTML = '';

  const h16  = n => '$' + n.toString(16).toUpperCase().padStart(4,'0');
  const h8   = n => '$' + n.toString(16).toUpperCase().padStart(2,'0');
  const pad  = (s, n) => s.padEnd(n,' ');
  const line = (html) => { const d=document.createElement('div'); d.innerHTML=html; area.appendChild(d); };
  const sep  = (title) => line(`<span class="asm-comment">; ── ${title} ${'─'.repeat(Math.max(0,44-title.length))}</span>`);
  const blank= () => line('');

  const A = (s,cls='asm-addr')   => `<span class="${cls}">${s}</span>`;
  const M = (s,cls='asm-mnem')   => `<span class="${cls}">${s}</span>`;
  const O = (s,cls='asm-op')     => `<span class="${cls}">${s}</span>`;
  const C = (s,cls='asm-comment')=> `<span class="${cls}"> ; ${s}</span>`;
  const TB = (t) => {
    const col = typeColor(t);
    return `<span class="ast-badge" style="color:${col};border-color:${col}44;font-size:9px;padding:0 3px;border-radius:2px;border:1px solid">${t}</span>`;
  };

  // Header
  sep(`C64PY — Layout Memoria Preliminare (Fase 2b)`);
  line(`<span class="asm-comment">; MOS 6510 · Load ${h16(PRG_LOAD_ADDR)} · Codice @ ${h16(PRG_CODE_OFFSET)}</span>`);
  line(`<span class="asm-comment">; $01 Config: ${prg.memDesc}</span>`);
  blank();

  // ── PRG Startup ──────────────────────────────────────────────────────────
  sep('PRG HEADER & STARTUP');
  const stubHex = prg.stub.map(b=>h8(b)).join(' ');
  line(`${A(h16(PRG_LOAD_ADDR)+'  ')} ${M('.byte')} ${O(stubHex)}${C('BASIC "0 SYS2061"')}`);

  if (!planner.usesFloat) {
    line(`${A(h16(PRG_CODE_OFFSET)+'  ')} ${M('LDA')}  ${O('#$36')}${C('$01: BASIC ROM → RAM (+8KB)')}`);
    line(`${A('      ')} ${M('STA')}  ${O('$01')}`);
  } else {
    line(`${A(h16(PRG_CODE_OFFSET)+'  ')}${C('$01 = $37 (default) — BASIC ROM visibile per float')}`);
  }
  const mainSym = planner.semScope.lookup('main');
  line(`${A('      ')} ${M('JSR')}  ${O('main')}${C('entry point')}`);
  if (!planner.usesFloat) {
    line(`${A('      ')} ${M('LDA')}  ${O('#$37')}${C('ripristina BASIC ROM per KERNAL safety')}`);
    line(`${A('      ')} ${M('STA')}  ${O('$01')}`);
  }
  line(`${A('      ')} ${M('RTS')}${C('ritorno al BASIC')}`);
  blank();

  // ── Zero Page ────────────────────────────────────────────────────────────
  const zpGlobals = planner.globals.filter(g=>g.isZP);
  const bssGlobals= planner.globals.filter(g=>!g.isZP);

  if (zpGlobals.length) {
    sep(`ZERO PAGE  [${'$02'} – ${h8(planner.zpNext-1)}]  (${planner.zpNext-planner.zpStart}/${planner.zpEnd-planner.zpStart} byte usati)`);
    zpGlobals.forEach(g => {
      const dir = g.size===1 ? '.byte' : g.size===2 ? '.word' : `.res ${g.size}`;
      const initHint = '';
      line(`${A(h16(g.addr)+'  ')} ${M(pad(dir,8))} ${O(pad(g.name,16))} ${TB(g.type)}${C(`global  ${g.size}B`)}`);
    });
    // ZP riservate float
    if (planner.usesFloat) {
      blank();
      line(`${A('$0061  ')} ${M('.res 5')}   ${O(pad('FAC1',16))}${C('Float Accumulator 1 (KERNAL)')}`);
      line(`${A('$0069  ')} ${M('.res 5')}   ${O(pad('FAC2',16))}${C('Float Accumulator 2 (KERNAL)')}`);
    }
    blank();
  } else {
    sep('ZERO PAGE  (nessun globale scalare)');
    blank();
  }

  // ── BSS (RAM dopo il codice) ─────────────────────────────────────────────
  if (bssGlobals.length) {
    sep('BSS — Array / Stringhe  (dopo fine codice)');
    line(`<span class="asm-comment">; Indirizzo definitivo assegnato in Fase 3</span>`);
    bssGlobals.forEach(g => {
      const arrDesc = g.isArr ? `[${g.arrCount||'?'}]` : '';
      const dir     = `.res ${g.size}`;
      line(`${A('$????  ')} ${M(pad(dir,8))} ${O(pad(g.name+arrDesc,16))} ${TB(g.type)}${C(`global  ${g.size}B`)}`);
    });
    blank();
  }

  // ── Funzioni ─────────────────────────────────────────────────────────────
  sep('FUNZIONI');
  planner.funcLayouts.forEach((layout, fname) => {
    const sym    = planner.semScope.lookup(fname);
    const params = sym?.params || [];
    const paramStr = params.map(p=>`${p.type} ${p.name}`).join(', ');
    blank();
    line(`<span class="asm-comment">; ┌─ func ${fname}(${paramStr}) → ${layout.ret} ─────────────────</span>`);
    line(`${A('$????  ')} ${M(fname+':')}${C('frame = '+layout.frameBytes+'B ZP')}`);

    // Params
    layout.locals.filter(v=>v.kind==='param').forEach(v => {
      line(`${A('      ')} ${C(`  PARAM  ${TB(v.type)} ${v.name}  (${v.size}B)`)}`);
    });
    // Local vars
    layout.locals.filter(v=>v.kind==='local').forEach(v => {
      const arr = v.isArr ? `[${v.arrCount||'?'}]` : '';
      line(`${A('      ')} ${C(`  LOCAL  ${TB(v.type)} ${v.name}${arr}  (${v.size}B)`)}`);
    });
    line(`<span class="asm-comment">; └──────────────────────────────────────────────────────</span>`);
  });
  blank();

  // ── Riepilogo ─────────────────────────────────────────────────────────────
  const s = planner.summary();
  sep('RIEPILOGO ALLOCAZIONE');
  line(`<span class="asm-comment">; Zero Page usata : ${s.zpUsed}/${s.zpTotal} byte  (${s.zpGlobals} var globali)</span>`);
  line(`<span class="asm-comment">; Zero Page libera: ${s.zpFree} byte  → disponibili per temporanei Fase 3</span>`);
  line(`<span class="asm-comment">; BSS (array/str) : ${planner.bssSize} byte  (${s.bssGlobals} var)</span>`);
  line(`<span class="asm-comment">; Var locali tot  : ${s.totalFuncVars}  (indirizzi ZP assegnati in Fase 3)</span>`);
  line(`<span class="asm-comment">; BASIC ROM       : ${planner.usesFloat ? 'VISIBILE ($37) — richiesta da float' : 'RIMOSSA ($36) — +8KB RAM libera'}</span>`);
  blank();
  line(`<span class="asm-comment">; ════ Dimensione PRG stimata (Fase 3 determinerà il valore esatto) ════</span>`);
  line(`<span class="asm-comment">; Header+stub: 14B  |  Startup: ~6B  |  Codice: TBD  |  BSS: ${planner.bssSize}B</span>`);
}