from dataclasses import dataclass
from typing import Any


class TT:
    INT_LIT = 'INT_LIT'
    FLOAT_LIT = 'FLOAT_LIT'
    HEX_LIT = 'HEX_LIT'
    BIN_LIT = 'BIN_LIT'
    STR_LIT = 'STR_LIT'
    KEYWORD = 'KEYWORD'
    TYPE = 'TYPE'
    BUILTIN = 'BUILTIN'
    IDENT = 'IDENT'
    LPAREN = '('
    RPAREN = ')'
    LBRACK = '['
    RBRACK = ']'
    COMMA = ','
    DOT = '.'
    COLON = ':'
    ARROW = '->'
    OP = 'OP'
    CMP = 'CMP'
    ASSIGN = '='
    AND = 'and'
    OR = 'or'
    NOT = 'not'
    NEWLINE = 'NEWLINE'
    INDENT = 'INDENT'
    DEDENT = 'DEDENT'
    EOF = 'EOF'


C64PY_KEYWORDS = frozenset({
    'def', 'if', 'else', 'elif', 'while', 'for', 'in', 'return',
    'pass', 'and', 'or', 'not', 'break', 'continue', 'True', 'False'
})

C64PY_TYPES = frozenset({
    'byte', 'word', 'int', 'float', 'void', 'q8_8', 'sq8_8',
    'uint', 'long', 'ulong', 'dword', 'bool', 'string',
    'q16_8', 'q8_16', 'q16_16',
    'sq16_8', 'sq8_16', 'sq16_16',
})

C64PY_BUILTINS = frozenset({
    'print', 'println', 'print_at', 'input',
    'clear_screen', 'border_color', 'screen_color', 'text_color',
    'peek', 'peek16', 'poke', 'poke16',
    'memset', 'memcpy',
    'wait', 'wait_frames', 'rand', 'abs', 'sgn', 'min', 'max',
    'sin', 'cos', 'tan', 'atn', 'sqr', 'log', 'exp', 'floor',
    'float_to_str', 'rnd',
    'fadd', 'fsub', 'fmul', 'fdiv', 'fpow',
    'fp_int', 'fp_frac',
    'kernal_chrout', 'kernal_chrin',
    'sei', 'cli',
    'enable_raster_irq', 'disable_raster_irq', 'ack_raster_irq',
    'next_raster', 'set_irq_vector', 'set_nmi_vector',
    'raster_sync', 'sys', 'jsr',
    'sprite_enable', 'sprite_pos', 'sprite_color', 'sprite_data',
    'sid_note', 'sid_freq', 'sid_vol', 'sid_waveform',
    'plot', 'draw_line', 'draw_box', 'fill_box',
})

FLOAT_KERNAL_BUILTINS = frozenset({
    'sqr', 'log', 'exp', 'floor', 'sin', 'cos', 'tan', 'atn',
    'float_to_str', 'rnd', 'fadd', 'fsub', 'fmul', 'fdiv', 'fpow'
})


@dataclass
class Token:
    type: str
    value: Any
    line: int = 0
    col: int = 0
    raw: str = ''
