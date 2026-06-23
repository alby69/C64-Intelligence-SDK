// ═══════════════════════════════════════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════════════════════════════════════
function switchTab(name, el) {
  document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  document.getElementById('output-area').style.display = name==='log'   ? 'block' : 'none';
  document.getElementById('ast-area').style.display    = name==='ast'   ? 'block' : 'none';
  document.getElementById('asm-area').style.display    = name==='asm'   ? 'block' : 'none';
  document.getElementById('basic-area').style.display  = name==='basic' ? 'block' : 'none';
  document.getElementById('info-area').style.display   = name==='info'  ? 'block' : 'none';
  document.getElementById('bytes-area').style.display  = name==='bytes' ? 'block' : 'none';
  const fa = document.getElementById('files-area');
  fa.style.display = name==='files' ? 'flex' : 'none';
  if (name==='info')  renderInfo();
  if (name==='files') renderFiles();
}