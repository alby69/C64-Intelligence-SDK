// ═══════════════════════════════════════════════════════════════════════════
//  EDITOR SETUP
// ═══════════════════════════════════════════════════════════════════════════
const cm = CodeMirror.fromTextArea(document.getElementById('editor'), {
  mode: 'c64lang', theme: 'default',
  lineNumbers: true, matchBrackets: true, autoCloseBrackets: true,
  indentUnit: 4, tabSize: 4, indentWithTabs: false,
  lineWrapping: false, styleActiveLine: true,
  extraKeys: {
    'F5':             doCompile,
    'Ctrl-S':         () => doCompile(),
    'Ctrl-N':         () => newFile(),
    'Ctrl-E':         () => doExport(),
    'Ctrl-O':         () => openFileDialog(),
    'Ctrl-Shift-S':   () => saveToLocal()
  }
});

// Ctrl+N globale — funziona anche quando il focus non è nell'editor
document.addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'n') { e.preventDefault(); newFile(); }
});

loadExample('hello');

cm.on('change', () => {
  const doc=cm.getDoc(); const lines=doc.lineCount(); const size=doc.getValue().length;
  document.getElementById('sb-lines').textContent = lines;
  document.getElementById('sb-size').textContent  = size < 1024 ? size+'B' : (size/1024).toFixed(1)+'KB';
});
cm.on('cursorActivity', () => {
  const cur=cm.getDoc().getCursor();
  document.getElementById('sb-cursor').textContent = `COL ${cur.ch+1} · ROW ${cur.line+1}`;
});