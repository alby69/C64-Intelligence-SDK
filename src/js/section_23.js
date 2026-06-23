// ═══════════════════════════════════════════════════════════════════════════
//  LOGGING
// ═══════════════════════════════════════════════════════════════════════════
function log(msg, cls='info') {
  const out=document.getElementById('output-area');
  const line=document.createElement('div');
  line.className=`log-line log-${cls}`; line.textContent=msg;
  out.appendChild(line); out.scrollTop=out.scrollHeight;
}
function logSection(msg) {
  const out=document.getElementById('output-area');
  const line=document.createElement('div');
  line.className='log-line log-section'; line.textContent='── '+msg+' ──';
  out.appendChild(line); out.scrollTop=out.scrollHeight;
}
function clearOutput() {
  document.getElementById('output-area').innerHTML='';
  document.getElementById('ast-area').innerHTML='';
  document.getElementById('asm-area').innerHTML='';
  document.getElementById('bytes-area').innerHTML='';
  setStatus('READY','');
}
function setStatus(msg,state) {
  document.getElementById('sb-status').textContent=msg;
  const dot=document.getElementById('sb-status-dot');
  dot.className='sb-dot'+(state?' '+state:'');
}