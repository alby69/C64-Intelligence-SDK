const TT = {
  INT_LIT:'INT_LIT', FLOAT_LIT:'FLOAT_LIT', HEX_LIT:'HEX_LIT',
  BIN_LIT:'BIN_LIT', STR_LIT:'STR_LIT',
  KEYWORD:'KEYWORD', TYPE:'TYPE', BUILTIN:'BUILTIN', IDENT:'IDENT',
  LPAREN:'(', RPAREN:')', LBRACK:'[', RBRACK:']', COMMA:',', DOT:'.', COLON:':', ARROW:'->',
  OP:'OP', CMP:'CMP', ASSIGN:'=',
  AND:'and', OR:'or', NOT:'not', NEWLINE:'NEWLINE', INDENT:'INDENT', DEDENT:'DEDENT',
  EOF:'EOF',
};

const C64PY_KEYWORDS = new Set([
    'def', 'if', 'else', 'elif', 'while', 'for', 'in', 'return',
    'pass', 'and', 'or', 'not', 'break', 'continue', 'True', 'False'
]);

const C64PY_TYPES = new Set([
    'byte', 'word', 'int', 'float', 'void', 'q8_8', 'sq8_8'
]);

const C64PY_BUILTINS = new Set([
    'print', 'print_at', 'input', 'clear_screen', 'border_color', 'screen_color',
    'peek', 'poke', 'peekw', 'pokew', 'wait', 'wait_frames', 'rand', 'abs', 'sin', 'cos', 'tan',
    'fp_int', 'fp_frac'
]);