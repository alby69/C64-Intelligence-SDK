import re

BASIC_TOKENS = {
    0x80: "END",
    0x81: "FOR",
    0x82: "NEXT",
    0x83: "DATA",
    0x84: "INPUT#",
    0x85: "INPUT",
    0x86: "DIM",
    0x87: "READ",
    0x88: "LET",
    0x89: "FOR",
    0x8A: "RUN",
    0x8B: "IF",
    0x8C: "RESTORE",
    0x8D: "GOSUB",
    0x8E: "RETURN",
    0x8F: "REM",
    0x90: "STOP",
    0x91: "ON",
    0x92: "WAIT",
    0x93: "LOAD",
    0x94: "SAVE",
    0x95: "VERIFY",
    0x96: "DEF",
    0x97: "POKE",
    0x98: "PRINT#",
    0x99: "PRINT",
    0x9A: "CONT",
    0x9B: "LIST",
    0x9C: "CLR",
    0x9D: "CMD",
    0x9E: "SYS",
    0x9F: "OPEN",
    0xA0: "CLOSE",
    0xA1: "GET",
    0xA2: "NEW",
    0xA3: "TAB(",
    0xA4: "TO",
    0xA5: "FN",
    0xA6: "SPC(",
    0xA7: "IF",
    0xA8: "NOT",
    0xA9: "STEP",
    0xAA: "+",
    0xAB: "-",
    0xAC: "*",
    0xAD: "/",
    0xAE: "^",
    0xAF: "AND",
    0xB0: "OR",
    0xB1: ">",
    0xB2: "=",
    0xB3: "<",
    0xB4: "SGN",
    0xB5: "INT",
    0xB6: "ABS",
    0xB7: "USR",
    0xB8: "FRE",
    0xB9: "POS",
    0xBA: "SQR",
    0xBB: "RND",
    0xBC: "LOG",
    0xBD: "EXP",
    0xBE: "COS",
    0xBF: "SIN",
    0xC0: "TAN",
    0xC1: "ATN",
    0xC2: "PEEK",
    0xC3: "LEN",
    0xC4: "STR$",
    0xC5: "VAL",
    0xC6: "ASC",
    0xC7: "CHR$",
    0xC8: "LEFT$",
    0xC9: "RIGHT$",
    0xCA: "MID$",
    0xCB: "GO",
}


def detokenize_basic(prg_data: bytes) -> str:
    if len(prg_data) < 2:
        return ""
    lines: list[str] = []
    offset = 2
    while offset < len(prg_data) - 4:
        next_line = prg_data[offset] + (prg_data[offset + 1] << 8)
        line_num = prg_data[offset + 2] + (prg_data[offset + 3] << 8)
        if next_line == 0 or line_num == 0:
            break
        line_data = prg_data[offset + 4 : offset + 4 + (next_line - offset - 4)]
        if not line_data:
            break
        tokens_parts: list[str] = []
        i = 0
        while i < len(line_data):
            b = line_data[i]
            if b == 0x00:
                break
            if b == 0x22:
                i += 1
                while i < len(line_data) and line_data[i] != 0x22:
                    tokens_parts.append(chr(line_data[i]))
                    i += 1
                if i < len(line_data):
                    tokens_parts.append('"')
                    i += 1
            elif b >= 0x80 and b in BASIC_TOKENS:
                word = BASIC_TOKENS[b]
                if word in (
                    "+",
                    "-",
                    "*",
                    "/",
                    "^",
                    ">",
                    "=",
                    "<",
                    "THEN",
                    "STEP",
                    "TO",
                    "GO",
                ):
                    tokens_parts.append(f" {word} ")
                else:
                    tokens_parts.append(word)
                i += 1
            elif b == ord(":"):
                tokens_parts.append(":")
                i += 1
            elif b == ord(";"):
                tokens_parts.append(";")
                i += 1
            elif b == ord(","):
                tokens_parts.append(",")
                i += 1
            elif b == ord(" "):
                tokens_parts.append(" ")
                i += 1
            elif b == 0x0E:
                tokens_parts.append("{SW lowercase}")
                i += 1
            elif b == 0x0F:
                tokens_parts.append("{SW uppercase}")
                i += 1
            elif b >= 0x90:
                tokens_parts.append(f"[${b:02X}]")
                i += 1
            else:
                tokens_parts.append(chr(b))
                i += 1
        lines.append(str(line_num) + " " + "".join(tokens_parts))
        offset = next_line
    return "\n".join(lines)


def is_basic_prg(prg_data: bytes) -> bool:
    if len(prg_data) < 7:
        return False
    if prg_data[0] == 0 and prg_data[1] == 0:
        return False
    next_line = prg_data[2] + (prg_data[3] << 8)
    line_num = prg_data[4] + (prg_data[5] << 8)
    return 0 < next_line < len(prg_data) + 4 and 0 <= line_num <= 63999


def hex_dump(data: bytes, bytes_per_line: int = 16) -> str:
    lines: list[str] = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i : i + bytes_per_line]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:06X}  {hex_part:<48}  {ascii_part}")
    return "\n".join(lines)
