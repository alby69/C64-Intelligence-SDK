// ═══════════════════════════════════════════════════════════════════════════
//  EXAMPLES LOADER
// ═══════════════════════════════════════════════════════════════════════════
function loadExample(name) {
  if (!EXAMPLES[name]) return;
  cm.setValue(EXAMPLES[name]); cm.clearHistory();
  const fnames = { hello:'hello_world.c64', screen:'fill_screen.c64', loop:'color_loop.c64', border:'border_anim.c64', raster:'raster_bars.c64', floatmath:'float_kernal.c64', floatarith:'float_arith.c64', sid:'sid_jingle.c64', sprite:'sprite_bounce.c64', charset:'charset_map.c64', sidspr:'sid_sprite.c64', irq_mplex:'irq_mplex.c64', sprite_mplex:'sprite_mplex.c64', sine_sprites:'sine_sprites.c64', pong:'pong.c64', plasma:'plasma.c64', music:'arpeggio.c64', starfield:'starfield.c64', fpbasic:'fp_colors.c64', fpsmooth:'fp_smooth.c64', fpgravity:'fp_gravity.c64' };
  document.getElementById('filename-display').textContent = fnames[name]||'untitled.c64';
  clearOutput();
  log(`[INFO] Caricato esempio: ${fnames[name]||name}`,'info');
}