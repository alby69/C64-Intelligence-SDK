// ═══════════════════════════════════════════════════════════════════════════
//  EXPORT PRG — download effettivo  (Fase 3 Passo 1)
// ═══════════════════════════════════════════════════════════════════════════
function doExport() {
  if (!_lastBuilder || !_lastBuilder.built) {
    // Compila prima di esportare
    doCompile();
    // doCompile è sincrono, quindi _lastBuilder è già disponibile
    if (!_lastBuilder || !_lastBuilder.built) {
      // Non chiamiamo clearOutput(): gli errori di compilazione appena loggati
      // sono la diagnostica più utile — aggiungiamo solo la riga di esito.
      log('', 'info');
      log('[EXPORT] Compilazione fallita — impossibile generare PRG.', 'error');
      setStatus('EXPORT: COMPILA PRIMA', 'err');
      return;
    }
  }

  const b   = _lastBuilder;
  const prg = b.toPRG();

  // Validazione base
  const logTab = document.querySelector('.panel-tab');
  switchTab('log', logTab);

  logSection(`Export PRG — ${_lastFilename}`);
  log(`  Dimensione  : ${prg.length} byte`, 'ok');
  log(`  Load addr   : $${hex4(PRG_LOAD_ADDR)}`, 'info');
  log(`  BASIC stub  : $0801–$${hex4(PRG_CODE_OFFSET-1)}  "0 SYS2061"`, 'info');
  log(`  Code start  : $${hex4(PRG_CODE_OFFSET)}`, 'info');
  log(`  $01 config  : ${b.usesFloat ? '$37 (BASIC ROM)' : '$36 (BASIC ROM→RAM)'}`, b.usesFloat?'warn':'ok');
  log(`  Funzioni    : ${b.ast.funcs.length}  [${b.ast.funcs.map(f=>f.name).join(', ')}] — codice reale`, 'ok');
  log('','info');

  // Header hex dump (prime 16 righe × 8 byte)
  logSection('Hex Dump (prime 128 byte)');
  for (let i=0; i<Math.min(prg.length, 128); i+=8) {
    const chunk  = Array.from(prg.slice(i, i+8));
    const hexStr = chunk.map(b=>`$${hex2(b)}`).join(' ');
    const asc    = chunk.map(b=>(b>=32&&b<127)?String.fromCharCode(b):'.').join('');
    log(`  +${String(i).padStart(3,'0')}  ${hexStr.padEnd(32)}  ${asc}`, 'info');
  }
  if (prg.length > 128) log(`  ... (${prg.length-128} byte rimanenti)`, 'info');
  log('','info');

  // Download
  downloadPRG(prg, _lastFilename);
  log(`[OK] Download avviato: ${_lastFilename}  (${prg.length} byte)`, 'ok');
  log('[OK] Carica su VICE o hardware reale (sd2iec, 1541).', 'ok');
  setStatus(`PRG ESPORTATO · ${prg.length}B · ${_lastFilename}`, 'ok');
}