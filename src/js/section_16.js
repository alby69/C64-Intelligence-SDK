// ═══════════════════════════════════════════════════════════════════════════
//  FILE MANAGEMENT — Export, Open, Drag&Drop, LocalStorage
// ═══════════════════════════════════════════════════════════════════════════

const LS_PREFIX = 'c64c_file_';

// ── Utilità download testo ─────────────────────────────────────────────────
function downloadTextFile(text, filename) {
  const blob = new Blob([text], { type:'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ── Export sorgente (.c64) ─────────────────────────────────────────────────
function exportSource() {
  const src  = cm.getValue();
  const name = (document.getElementById('filename-display').textContent || 'untitled').replace(/\.prg$/,'');
  const fname = name.endsWith('.c64') ? name : name + '.c64';
  downloadTextFile(src, fname);
  log(`[OK] Sorgente esportato: ${fname}  (${src.length} caratteri)`, 'ok');
  setStatus(`SORGENTE ESPORTATO · ${fname}`, 'ok');
}

// ── Export assembly listing (.asm) ─────────────────────────────────────────
function exportAsm() {
  const asmArea = document.getElementById('asm-area');
  if (!asmArea.children.length) {
    log('[WARN] Nessun listing ASM disponibile — compila prima.', 'warn');
    setStatus('EXPORT ASM: COMPILA PRIMA', 'err');
    return;
  }
  // Estrai il testo puro dalle righe del listing (strip HTML)
  const lines = [];
  for (const ch of asmArea.children) {
    lines.push(ch.textContent);
  }
  const text = lines.join('\n');
  const base = (document.getElementById('filename-display').textContent || 'untitled').replace(/\.c64$|\.prg$/,'');
  const fname = base + '.asm';
  downloadTextFile(text, fname);
  log(`[OK] Assembly listing esportato: ${fname}  (${lines.length} righe)`, 'ok');
  setStatus(`ASM ESPORTATO · ${fname}`, 'ok');
}

// ── Apertura file tramite dialog ───────────────────────────────────────────
function openFileDialog() {
  document.getElementById('file-input').value = '';
  document.getElementById('file-input').click();
}

function onFileInputChange(evt) {
  const file = evt.target.files[0];
  if (file) loadFileObject(file);
}

function loadFileObject(file) {
  const reader = new FileReader();
  reader.onload = e => {
    cm.setValue(e.target.result);
    cm.clearHistory();
    document.getElementById('filename-display').textContent = file.name;
    clearOutput();
    log(`[OK] File caricato: ${file.name}  (${file.size} byte)`, 'ok');
    setStatus(`APERTO · ${file.name}`, 'ok');
  };
  reader.readAsText(file, 'utf-8');
}

// ── Drag & Drop sull'editor ────────────────────────────────────────────────
(function setupDragDrop() {
  const pane    = document.getElementById('editor-pane');
  const overlay = document.getElementById('drop-overlay');
  let  dragCnt  = 0;

  pane.addEventListener('dragenter', e => {
    e.preventDefault();
    dragCnt++;
    overlay.classList.add('active');
  });
  pane.addEventListener('dragleave', e => {
    dragCnt--;
    if (dragCnt <= 0) { dragCnt = 0; overlay.classList.remove('active'); }
  });
  pane.addEventListener('dragover', e => { e.preventDefault(); });
  pane.addEventListener('drop', e => {
    e.preventDefault();
    dragCnt = 0;
    overlay.classList.remove('active');
    const file = e.dataTransfer.files[0];
    if (file) loadFileObject(file);
  });
})();

// ── LocalStorage helpers ───────────────────────────────────────────────────
function lsKey(name) { return LS_PREFIX + name; }

function lsListFiles() {
  const files = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k && k.startsWith(LS_PREFIX)) {
      try {
        const rec = JSON.parse(localStorage.getItem(k));
        files.push(rec);
      } catch(e) {}
    }
  }
  return files.sort((a,b) => b.ts - a.ts);
}

// ── Salvataggio in localStorage (con modal nome) ───────────────────────────
let _modalCallback = null;

function openModal(defaultName, callback, title, confirmLabel) {
  _modalCallback = callback;
  const inp = document.getElementById('modal-input');
  inp.value = defaultName;
  document.getElementById('modal-title').textContent = title || '💾 SALVA FILE';
  document.getElementById('modal-confirm-btn').textContent = confirmLabel || 'SALVA';
  document.getElementById('modal-overlay').classList.add('active');
  setTimeout(() => { inp.focus(); inp.select(); }, 50);
}
function modalClose() {
  document.getElementById('modal-overlay').classList.remove('active');
  _modalCallback = null;
}
function modalConfirm() {
  const name = document.getElementById('modal-input').value.trim();
  if (!name) return;
  const cb = _modalCallback;   // salva ref prima che modalClose la azzeri
  modalClose();
  if (cb) cb(name);
}

function saveToLocal(overrideName) {
  const currentName = overrideName || document.getElementById('filename-display').textContent || 'untitled.c64';
  const defaultName = currentName.endsWith('.c64') ? currentName : currentName + '.c64';
  openModal(defaultName, name => {
    const fname = name.endsWith('.c64') ? name : name + '.c64';
    const rec = {
      name: fname,
      src:  cm.getValue(),
      ts:   Date.now()
    };
    try {
      localStorage.setItem(lsKey(fname), JSON.stringify(rec));
      document.getElementById('filename-display').textContent = fname;
      log(`[OK] Salvato in locale: ${fname}`, 'ok');
      setStatus(`SALVATO · ${fname}`, 'ok');
      // Se il pannello FILES è aperto, aggiorna la lista
      if (document.getElementById('files-area').style.display !== 'none') renderFiles();
    } catch(e) {
      log(`[ERR] Salvataggio fallito: ${e.message}`, 'error');
      setStatus('ERRORE SALVATAGGIO', 'err');
    }
  });
}

function newFile() {
  const current = cm.getValue().trim();
  if (current.length > 0) {
    if (!confirm('L\'editor contiene del codice.\nCreare un nuovo file e perdere le modifiche non salvate?')) return;
  }
  openModal('untitled.c64', name => {
    const fname = name.endsWith('.c64') ? name : name + '.c64';
    const baseName = fname.replace(/\.c64$/, '');
    const skeleton =
`// ─── ${baseName} ───────────────────────────────
// Descrizione del programma

func main() {
    clear_screen();
}
`;
    cm.setValue(skeleton);
    cm.clearHistory();
    cm.setCursor({ line: 4, ch: 4 });
    cm.focus();
    document.getElementById('filename-display').textContent = fname;
    clearOutput();
    log(`[OK] Nuovo file: ${fname}`, 'ok');
    setStatus(`NUOVO · ${fname}`, 'ok');
  }, '✦ NUOVO FILE', 'CREA');
}

function loadLocalFile(name) {
  try {
    const rec = JSON.parse(localStorage.getItem(lsKey(name)));
    if (!rec) return;
    cm.setValue(rec.src);
    cm.clearHistory();
    document.getElementById('filename-display').textContent = rec.name;
    clearOutput();
    log(`[OK] Caricato da locale: ${rec.name}  (${rec.src.length} caratteri)`, 'ok');
    setStatus(`CARICATO · ${rec.name}`, 'ok');
  } catch(e) {
    log(`[ERR] Caricamento fallito: ${e.message}`, 'error');
  }
}

function deleteLocalFile(name, evt) {
  evt.stopPropagation();
  if (!confirm(`Cancellare "${name}"?`)) return;
  localStorage.removeItem(lsKey(name));
  log(`[OK] File cancellato: ${name}`, 'warn');
  renderFiles();
}

function deleteAllFiles() {
  const files = lsListFiles();
  if (!files.length) return;
  if (!confirm(`Cancellare tutti i ${files.length} file salvati?`)) return;
  files.forEach(f => localStorage.removeItem(lsKey(f.name)));
  log('[OK] Tutti i file locali cancellati.', 'warn');
  renderFiles();
}

// ── Render pannello FILES ──────────────────────────────────────────────────
function renderFiles() {
  const list  = document.getElementById('files-list');
  const files = lsListFiles();
  list.innerHTML = '';
  if (!files.length) {
    list.innerHTML = '<div class="files-empty">Nessun file salvato.<br>Usa 💾 SAVE per salvare il sorgente corrente.</div>';
    return;
  }
  files.forEach(f => {
    const fmt = new Date(f.ts).toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML =
      `<span class="file-item-icon">◈</span>` +
      `<span class="file-item-name" onclick="loadLocalFile('${CSS.escape(f.name)}')" title="${f.name}">${f.name}</span>` +
      `<span class="file-item-meta" onclick="loadLocalFile('${CSS.escape(f.name)}')">${fmt}</span>` +
      `<span class="file-item-del" onclick="deleteLocalFile('${CSS.escape(f.name)}', event)" title="Cancella">✕</span>`;
    list.appendChild(item);
  });
}