// ═══════════════════════════════════════════════════════════════════════════
//  REFERENCE PANEL
// ═══════════════════════════════════════════════════════════════════════════
function renderInfo() {
  const area = document.getElementById('info-area');
  if (area._rendered) return;
  area._rendered = true;

  const keywords = [...C64_KEYWORDS].sort();
  const builtins = [...C64_BUILTINS].sort();

  area.innerHTML = `
  <div class="info-section">
    <div class="info-title">Mappa Memoria Runtime PRG</div>
    <div class="info-mem">
      <div class="info-mem-row"><span class="info-mem-addr">$0002-$00FF</span><span class="info-mem-desc">Zero Page — variabili byte/word</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$0100-$01FF</span><span class="info-mem-desc">Stack 6510</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$0200-$03FF</span><span class="info-mem-desc">Area sistema / KERNAL buffer</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$0400-$07FF</span><span class="info-mem-desc">Screen RAM (40×25 = 1000 celle)</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$0801-$xxxx</span><span class="info-mem-desc info-mem-active">PRG → BASIC stub + codice compilato</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$A000-$BFFF</span><span class="info-mem-desc info-mem-active">BASIC ROM [float] → RAM [no-float]</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$C000-$CFFF</span><span class="info-mem-desc">RAM libera (4 KB)</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$D000-$DFFF</span><span class="info-mem-desc">I/O: VIC-II · SID · CIA1/2</span></div>
      <div class="info-mem-row"><span class="info-mem-addr">$E000-$FFFF</span><span class="info-mem-desc">KERNAL ROM (sempre attivo)</span></div>
    </div>
    <div style="margin-top:6px;font-size:10px;color:var(--c64-border)">
      $01 CPU Port: <span style="color:var(--c64-yellow)">$36</span> = BASIC ROM→RAM (+8KB) &nbsp;|&nbsp;
      <span style="color:var(--c64-yellow)">$37</span> = BASIC ROM visibile (float)
    </div>
  </div>
  <div class="info-section">
    <div class="info-title">PRG Header / Startup</div>
    <div class="info-row"><span class="info-key">Load addr</span><span class="info-val">$0801</span></div>
    <div class="info-row"><span class="info-key">BASIC stub</span><span class="info-val">$0801-$080C</span></div>
    <div class="info-row"><span class="info-key">Codice @ </span><span class="info-val">$080D (SYS 2061)</span></div>
    <div class="info-row"><span class="info-key">Startup no-float</span><span class="info-val warn">LDA #$36 · STA $01</span></div>
    <div class="info-row"><span class="info-key">Startup float</span><span class="info-val">(default $37 — nessun cambio)</span></div>
  </div>
  <div class="info-section">
    <div class="info-title">Float KERNAL ROM ($A000-$BFFF)</div>
    <div class="info-row"><span class="info-key">Formato</span><span class="info-val">5 byte (esponente + mantissa 32bit)</span></div>
    <div class="info-row"><span class="info-key">FAC1</span><span class="info-val">$61-$65 (accumulatore 1)</span></div>
    <div class="info-row"><span class="info-key">FAC2</span><span class="info-val">$69-$6D (accumulatore 2)</span></div>
    <div class="info-row"><span class="info-key">a + b</span><span class="info-val">FADD $B867</span></div>
    <div class="info-row"><span class="info-key">a - b</span><span class="info-val">FSUB $B850</span></div>
    <div class="info-row"><span class="info-key">a * b</span><span class="info-val">FMUL $BA28</span></div>
    <div class="info-row"><span class="info-key">a / b</span><span class="info-val">FDIV $BB0F</span></div>
    <div class="info-row"><span class="info-key">a ^ b</span><span class="info-val">FPOW $BF78</span></div>
    <div class="info-row"><span class="info-key">sqr(x)</span><span class="info-val">√x  JSR $BF71</span></div>
    <div class="info-row"><span class="info-key">log(x)</span><span class="info-val">ln(x)  JSR $B9EA</span></div>
    <div class="info-row"><span class="info-key">exp(x)</span><span class="info-val">eˣ  JSR $BFED</span></div>
    <div class="info-row"><span class="info-key">sin(x)</span><span class="info-val">radianti  JSR $E26B</span></div>
    <div class="info-row"><span class="info-key">cos(x)</span><span class="info-val">radianti  JSR $E264</span></div>
    <div class="info-row"><span class="info-key">tan(x)</span><span class="info-val">radianti  JSR $E2B4</span></div>
    <div class="info-row"><span class="info-key">atn(x)</span><span class="info-val">arctan  JSR $E30E</span></div>
    <div class="info-row"><span class="info-key">abs(x)</span><span class="info-val">|x|  JSR $BC58</span></div>
    <div class="info-row"><span class="info-key">floor(x)</span><span class="info-val">JSR $BCCC</span></div>
    <div class="info-row"><span class="info-key">rnd()</span><span class="info-val">0.0..1.0  JSR $E097</span></div>
  </div>
  <div class="info-section">
    <div class="info-title">Tipi di dato</div>
    <div class="info-row"><span class="info-key">byte</span><span class="info-val">uint8, 0-255, 1 byte</span></div>
    <div class="info-row"><span class="info-key">word</span><span class="info-val">uint16, 0-65535, 2 byte</span></div>
    <div class="info-row"><span class="info-key">int</span><span class="info-val">int16, -32768..32767, 2 byte</span></div>
    <div class="info-row"><span class="info-key">float</span><span class="info-val">5 byte KERNAL (~9 cifre)</span></div>
    <div class="info-row"><span class="info-key">bool</span><span class="info-val">0/1, 1 byte</span></div>
    <div class="info-row"><span class="info-key">string</span><span class="info-val">PETSCII null-terminated</span></div>
  </div>
  <div class="info-section">
    <div class="info-title">Nodi AST (Fase 2b)</div>
    <div class="info-row"><span class="info-key" style="color:var(--c64-yellow)">FuncDecl</span><span class="info-val">def name(params): body</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--c64-cyan)">VarDecl</span><span class="info-val">name: type = init</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--c64-bright)">Assign</span><span class="info-val">lvalue = expr</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--tok-keyword)">If</span><span class="info-val">if (cond) then [else]</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--tok-keyword)">While</span><span class="info-val">while (cond) body</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--tok-builtin)">Call</span><span class="info-val">name(arg, arg, ...)</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--tok-operator)">BinaryOp</span><span class="info-val">left op right</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--tok-number)">Literal</span><span class="info-val">int/float/hex/bin/str</span></div>
    <div class="info-row"><span class="info-key" style="color:var(--tok-type)">Cast</span><span class="info-val">type(expr)</span></div>
    <div class="info-row"><span class="info-key">+Block/For/Do…</span><span class="info-val">nodi aggiuntivi</span></div>
  </div>
  <div class="info-section">
    <div class="info-title">Keywords</div>
    ${keywords.map(k=>`<span class="info-kw">${k}</span>`).join('')}
  </div>
  <div class="info-section">
    <div class="info-title">Builtin C64</div>
    ${builtins.map(b=>`<span class="info-bi">${b}</span>`).join('')}
  </div>
  <div class="info-section">
    <div class="info-title">Costanti Memory-Mapped</div>
    <div class="info-row"><span class="info-key">Screen RAM</span><span class="info-val">$0400</span></div>
    <div class="info-row"><span class="info-key">Color RAM</span><span class="info-val">$D800</span></div>
    <div class="info-row"><span class="info-key">VIC Border</span><span class="info-val">$D020</span></div>
    <div class="info-row"><span class="info-key">VIC BG</span><span class="info-val">$D021</span></div>
    <div class="info-row"><span class="info-key">VIC Raster</span><span class="info-val">$D012</span></div>
    <div class="info-row"><span class="info-key">SID Base</span><span class="info-val">$D400</span></div>
    <div class="info-row"><span class="info-key">CIA 1</span><span class="info-val">$DC00</span></div>
    <div class="info-row"><span class="info-key">CPU Port</span><span class="info-val">$01</span></div>
  </div>
  <div class="info-section">
    <div class="info-title">Shortcuts</div>
    <div class="info-row"><span class="info-key">Compile</span><span class="info-val">F5 / Ctrl+S</span></div>
    <div class="info-row"><span class="info-key">Nuovo file</span><span class="info-val">Ctrl+N</span></div>
    <div class="info-row"><span class="info-key">Export PRG</span><span class="info-val">Ctrl+E</span></div>
    <div class="info-row"><span class="info-key">Apri file</span><span class="info-val">Ctrl+O</span></div>
    <div class="info-row"><span class="info-key">Salva locale</span><span class="info-val">Ctrl+Shift+S</span></div>
    <div class="info-row"><span class="info-key">Drag & Drop</span><span class="info-val">trascina .c64/.txt sull'editor</span></div>
  </div>
  `;
}

// ─── Init ─────────────────────────────────────────────────────────────────
log('╔═══════════════════════════════════════════════╗','info');
log('║         C64PY IDE — MOS 6510 Compiler          ║','ok');
log('║  Lexer · Parser · Semantica · MemPlanner      ║','info');
log('║  CodeGenerator · PRGBuilder · File I/O        ║','info');
log('╚═══════════════════════════════════════════════╝','info');
log('','info');
log('[OK]  Lexer        caricato.','ok');
log('[OK]  Parser       caricato.','ok');
log('[OK]  Semantica    caricata.','ok');
log('[OK]  MemPlanner   caricato.','ok');
log('[OK]  CodeEmitter  caricato.','ok');
log('[OK]  CodeGenerator caricato.','ok');
log('[OK]  PRGBuilder   caricato.','ok');
log('[OK]  File I/O     attivo.','ok');
log('','info');
log('Premi F5 — LOG = report  |  AST = albero  |  ASM = listing  |  BYTES = hex  |  FILES = locale.','info');
setStatus('PRONTO','ok');