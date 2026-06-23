// ═══════════════════════════════════════════════════════════════════════════
//  SCOPE — tabella simboli a catena
// ═══════════════════════════════════════════════════════════════════════════
class Scope {
  constructor(parent=null, name='') {
    this.parent  = parent;
    this.name    = name;
    this.symbols = new Map();
  }
  define(name, info) { this.symbols.set(name, { ...info, scopeName: this.name }); }
  lookup(name) {
    if (this.symbols.has(name)) return this.symbols.get(name);
    return this.parent ? this.parent.lookup(name) : null;
  }
  ownNames() { return [...this.symbols.keys()]; }
}