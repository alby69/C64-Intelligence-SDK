// ═══════════════════════════════════════════════════════════════════════════
//  RENDER LISTING — Tab ASM  (Fase 3 Passo 1)
// ═══════════════════════════════════════════════════════════════════════════
function renderListing(builder, planner) {
  const area = document.getElementById('asm-area');
  area.innerHTML = '';

  const pad = (s,n) => String(s).padEnd(n,' ');
  const line = html => { const d=document.createElement('div'); d.innerHTML=html; area.appendChild(d); };
  const blank= ()   => line('');
  const sep  = t    => line(`<span class="asm-comment">; ── ${t} ${'─'.repeat(Math.max(0,46-t.length))}</span>`);

  const A  = s => `<span class="asm-addr">$${hex4(s)}</span>`;
  const B  = s => `<span class="asm-byte">$${hex2(s)}</span>`;
  const M  = s => `<span class="asm-mnem">${s}</span>`;
  const O  = s => `<span class="asm-op">${s}</span>`;
  const CC = s => s ? `<span class="asm-comment"> ; ${s}</span>` : '';
  const LB = s => `<span style="color:var(--c64-yellow);font-weight:bold">${s}</span>`;
  const TB = t => { const c=typeColor(t); return `<span style="color:${c};font-size:9px">${t}</span>`; };

  // ── Header ───────────────────────────────────────────────────────────
  sep(`C64PY v1.0 — PRG Listing   Fase3·Passo2+CF   (${builder.prgSize()} byte)`);
  line(`<span class="asm-comment">; Load $${hex4(PRG_LOAD_ADDR)}  Code $${hex4(PRG_CODE_OFFSET)}  $01: ${builder.usesFloat?'$37 (BASIC ROM)':'$36 (BASIC→RAM)'}</span>`);
  blank();

  // ── BASIC stub ───────────────────────────────────────────────────────
  sep(`BASIC Stub  $0801–$${hex4(PRG_CODE_OFFSET-1)}  (${builder.STUB.length} byte)`);
  const stubRow = builder.STUB.map(b=>B(b)).join(' ');
  line(`${A(PRG_LOAD_ADDR)}  ${stubRow}${CC('0 SYS2061 → JMP $080D')}`);
  blank();

  // ── Code listing ─────────────────────────────────────────────────────
  const cEnd = PRG_CODE_OFFSET + builder.e.byteCount() - 1;
  sep(`Code  $${hex4(PRG_CODE_OFFSET)}–$${hex4(cEnd)}  (${builder.e.byteCount()} byte)`);

  builder.e.listing.forEach(entry => {
    if (entry.isLabel) {
      blank();
      line(LB(`${entry.labelName}:`));
      return;
    }
    if (entry.isData) {
      const bh = entry.bytes.slice(0,8).map(b=>B(b)).join(' ');
      const ex = entry.bytes.length>8 ? `<span class="asm-comment"> …+${entry.bytes.length-8}</span>` : '';
      line(`${A(entry.addr)}  ${bh}${ex}  ${M(pad('.byte',5))}  ${O(entry.op)}${CC(entry.comment)}`);
      return;
    }
    if (!entry.mnem) return;

    // Hex bytes — sempre 3 slot (9 char) per allineamento colonne
    const bh   = entry.bytes.map(b=>B(b)).join(' ');
    const bpad = '&nbsp;&nbsp;&nbsp;&nbsp;'.repeat(Math.max(0, 3 - entry.bytes.length));
    // Cicli dal mode
    const cyc  = CYCLES[entry.mnem]?.[entry.mode];
    const cycS = cyc !== undefined
      ? `<span style="color:rgba(123,123,255,0.45);font-size:10px;margin-left:4px">[${cyc}]</span>`
      : '';
    // Fixup mark
    const fxS  = entry.fixup
      ? `<span style="color:var(--c64-orange);font-size:9px"> ✎</span>`
      : '';

    line(`${A(entry.addr)}  ${bh}${bpad}  ${M(pad(entry.mnem,4))}  ${O(pad(entry.op,18))}${fxS}${cycS}${CC(entry.comment)}`);
  });
  blank();

  // ── BSS section ──────────────────────────────────────────────────────
  const bss = planner.globals.filter(g => !g.isZP);
  if (bss.length) {
    sep('BSS — Globals (array / string)');
    let ba = PRG_CODE_OFFSET + builder.e.byteCount();
    bss.forEach(g => {
      const arr = g.isArr ? `[${g.arrCount}]` : '';
      line(`${A(ba)}  ${M(pad('.res '+g.size,9))}  ${O(pad(g.name+arr,20))}  ${TB(g.type)}${CC(`global  ${g.size}B`)}`);
      ba += g.size;
    });
    blank();
  }

  // ── Zero page map ─────────────────────────────────────────────────────
  const zpV = planner.globals.filter(g => g.isZP);
  if (zpV.length) {
    sep(`Zero Page  $02–$${hex2(planner.zpNext-1)}  (${planner.zpNext-2} / ${planner.zpEnd-2} byte usati)`);
    zpV.forEach(g => {
      line(`${A(g.addr)}  ${TB(g.type)}  ${O(pad(g.name,20))}${CC(`${g.size}B  ZP global`)}`);
    });
    blank();
  }

  // ── Fixup errors ──────────────────────────────────────────────────────
  if (builder.fixupErrs.length) {
    sep('FIXUP ERRORS');
    builder.fixupErrs.forEach(e => line(`<span class="log-error">  ✕ ${e}</span>`));
    blank();
  }

  // ── Summary ───────────────────────────────────────────────────────────
  sep('Riepilogo');
  const s = planner.summary();
  line(`<span class="asm-comment">; PRG totale   : ${builder.prgSize()} byte  (header 2B + stub ${builder.STUB.length}B + code ${builder.codeSize()}B + BSS ${planner.bssSize}B)</span>`);
  line(`<span class="asm-comment">; ZP globals   : ${s.zpUsed}B  [$02–$${hex2(planner.zpNext-1)}]  (${s.zpFree}B liberi)</span>`);
  line(`<span class="asm-comment">; Func stub    : ${builder.ast.funcs.length}  [${builder.ast.funcs.map(f=>f.name).join(', ')}]</span>`);
  line(`<span class="asm-comment">; $01 config   : ${builder.usesFloat ? '$37 BASIC ROM attiva' : '$36 BASIC ROM → RAM'}</span>`);
  line(`<span class="asm-comment">; Passo 2      : code gen corpi funzioni ✓ ATTIVO</span>`);
  if (builder.fixupErrs.length===0)
    line(`<span class="asm-comment" style="color:var(--c64-green)">; ✓ Tutti i fixup risolti — PRG scaricabile</span>`);
}