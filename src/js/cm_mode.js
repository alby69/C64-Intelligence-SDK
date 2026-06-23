CodeMirror.defineMode('c64py-lang', function() {
  return {
    token: function(stream, state) {
      if (stream.eatSpace()) return null;
      if (stream.match('#')) { stream.skipToEnd(); return 'c64-comment'; }
      if (stream.match(/^\$[0-9A-Fa-f]+/) || stream.match(/^0[xX][0-9A-Fa-f]+/)) return 'c64-hex';
      if (stream.match(/^[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?/)) return 'c64-float';
      if (stream.match(/^[0-9]+/)) return 'c64-number';
      if (stream.match(/^"[^"]*"/)) return 'c64-string';
      if (stream.match(/^[A-Za-z_][A-Za-z0-9_]*/)) {
        const w = stream.current();
        if (C64PY_KEYWORDS.has(w)) return 'c64-keyword';
        if (C64PY_TYPES.has(w)) return 'c64-type';
        if (C64PY_BUILTINS.has(w)) return 'c64-builtin';
        return 'c64-variable';
      }
      stream.next(); return null;
    }
  };
});