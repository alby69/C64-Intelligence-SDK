// ═══════════════════════════════════════════════════════════════════════════
//  RENDER BYTES — Tab BYTES  hex dump PRG completo (Fase 3 Passo 2)
// ═══════════════════════════════════════════════════════════════════════════
function renderBytes(builder) {
  const area = document.getElementById('bytes-area');
  area.innerHTML = '';
  if (!builder || !builder.built) return;

  const prg = builder.toPRG();
  const h2  = n => (n&0xFF).toString(16).toUpperCase().padStart(2,'0');
  const h4  = n => (n&0xFFFF).toString(16).toUpperCase().padStart(4,'0');

  // Header
  const hdr = document.createElement('div');
  hdr.className = 'hex-hdr';
  hdr.textContent = `PRG ${prg.length} byte  ·  Load $${h4(PRG_LOAD_ADDR)}  ·  Code $${h4(PRG_CODE_OFFSET)}  ·  $01: ${builder.usesFloat?'$37 BASIC ROM':'$36 BASIC→RAM'}`;
  area.appendChild(hdr);

  const COL_ADDR  = 56;
  const BYTES_PER_ROW = 8;

  // Map addr→label from emitter labels
  const labelByOff = new Map(); // offset in buf → label name
  builder.e.labels.forEach((off,name) => labelByOff.set(off + builder.e.base, name));

  // Salta i primi 2 byte (indirizzo di caricamento PRG, non codice)
  for (let i = 2; i < prg.length; i += BYTES_PER_ROW) {
    const baseAddr = PRG_LOAD_ADDR + (i - 2);

    // Label row?
    const lbl = labelByOff.get(baseAddr);
    if (lbl) {
      const ld = document.createElement('div');
      ld.style.cssText = 'color:var(--c64-yellow);font-size:10px;margin-top:4px;opacity:0.8;';
      ld.textContent = lbl + ':';
      area.appendChild(ld);
    }

    const row = document.createElement('div');
    row.className = 'hex-row';

    const addrSpan = document.createElement('span');
    addrSpan.className = 'hex-addr';
    addrSpan.textContent = '$' + h4(baseAddr) + '  ';
    row.appendChild(addrSpan);

    const chunk = Array.from(prg.slice(i, i + BYTES_PER_ROW));
    const bytesSpan = document.createElement('span');
    bytesSpan.className = 'hex-bytes';
    bytesSpan.textContent = chunk.map(b=>`$${h2(b)}`).join(' ').padEnd(BYTES_PER_ROW*5-1,' ');
    row.appendChild(bytesSpan);

    const sep = document.createElement('span');
    sep.className = 'hex-sep'; sep.textContent = ' │ ';
    row.appendChild(sep);

    const ascii = chunk.map(b=>(b>=0x20&&b<0x7F)?String.fromCharCode(b):'.').join('');
    const asciiSpan = document.createElement('span');
    asciiSpan.className = 'hex-ascii';
    asciiSpan.textContent = ascii;
    row.appendChild(asciiSpan);

    area.appendChild(row);
  }

  // Footer
  const ftr = document.createElement('div');
  ftr.style.cssText = 'margin-top:8px;font-size:10px;color:var(--tok-comment);font-style:italic;';
  ftr.textContent = `Totale: ${prg.length}B  (header 2B + stub ${builder.STUB.length}B + code ${builder.codeSize()}B)`;
  area.appendChild(ftr);
}