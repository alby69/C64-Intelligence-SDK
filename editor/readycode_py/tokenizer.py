# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Commodore 64 BASIC token definitions, tokenizer, and .prg converter logic.
"""

from typing import Optional, Tuple, List, Dict, NamedTuple

class KeywordInfo(NamedTuple):
    token: int
    snippet: Optional[str]
    description: Optional[str]
    category: Optional[str]


class BasicTokens:
    # Single source of truth for every BASIC V2 keyword: its token byte plus the completion
    # snippet, description, and category shown elsewhere in the editor.
    Keywords: Dict[str, KeywordInfo] = {
        # Control Flow
        "END":     KeywordInfo(0x80, "END",       "Ends program execution.",                                                  "Control Flow"),
        "FOR":     KeywordInfo(0x81, "FOR | = ",  "Begins a counted loop. FOR var=start TO end [STEP n]",                     "Control Flow"),
        "NEXT":    KeywordInfo(0x82, "NEXT |",    "Ends a FOR loop. NEXT [var]",                                              "Control Flow"),
        "DATA":    KeywordInfo(0x83, "DATA |",    "Embeds literal values for READ. DATA val[,val,...]",                       "Variables & Data"),
        "INPUT#":  KeywordInfo(0x84, "INPUT# |,", "Reads data from an open file. INPUT# file,var[,var,...]",                  "Input & Output"),
        "INPUT":   KeywordInfo(0x85, "INPUT |",   "Accepts keyboard input. INPUT [\"prompt\";] var[,var,...]",                "Input & Output"),
        "DIM":     KeywordInfo(0x86, "DIM |(|)",  "Declares an array. DIM var(size[,size,...])",                              "Variables & Data"),
        "READ":    KeywordInfo(0x87, "READ |",    "Reads the next DATA value into a variable. READ var[,var,...]",            "Variables & Data"),
        "LET":     KeywordInfo(0x88, "LET | = ",  "Assigns a value to a variable. LET var=expression",                        "Variables & Data"),
        "GOTO":    KeywordInfo(0x89, "GOTO |",    "Jumps to a line number. GOTO line",                                        "Control Flow"),
        "RUN":     KeywordInfo(0x8A, "RUN",       "Executes the program from the beginning, or from a line number.",          "Control Flow"),
        "IF":      KeywordInfo(0x8B, "IF | THEN ","Branches conditionally. IF condition THEN statement/line",                 "Control Flow"),
        "RESTORE": KeywordInfo(0x8C, "RESTORE",   "Resets the DATA pointer to the first DATA statement.",                     "Variables & Data"),
        "GOSUB":   KeywordInfo(0x8D, "GOSUB |",   "Calls a subroutine at a line number. GOSUB line",                          "Control Flow"),
        "RETURN":  KeywordInfo(0x8E, "RETURN",    "Returns from a GOSUB subroutine.",                                         "Control Flow"),
        "REM":     KeywordInfo(0x8F, "REM |",     "Marks a comment; the rest of the line is not executed.",                   "Program Editing"),
        "STOP":    KeywordInfo(0x90, "STOP",      "Pauses execution. Use CONT to resume.",                                    "Control Flow"),

        # Functions & I/O
        "ON":      KeywordInfo(0x91, "ON | GOTO ", "Branches to a line based on a computed value. ON expr GOTO/GOSUB line[,line,...]", "Control Flow"),
        "WAIT":    KeywordInfo(0x92, "WAIT |,",    "Halts until memory bits match a mask. WAIT addr,mask[,inv-mask]",         "System & Memory"),
        "LOAD":    KeywordInfo(0x93, "LOAD \"|\",8", "Loads a program from a device. LOAD \"name\",device[,1]",               "Files & Devices"),
        "SAVE":    KeywordInfo(0x94, "SAVE \"|\",8", "Saves the program to a device. SAVE \"name\",device[,1]",               "Files & Devices"),
        "VERIFY":  KeywordInfo(0x95, "VERIFY \"|\",8", "Verifies a saved program matches memory. VERIFY \"name\",device",     "Files & Devices"),
        "DEF":     KeywordInfo(0x96, "DEF FN |(|)=", "Defines a numeric function. DEF FN name(arg)=expression",               "Variables & Data"),
        "POKE":    KeywordInfo(0x97, "POKE |,",    "Writes a byte to a memory address. POKE addr,value",                      "System & Memory"),
        "PRINT#":  KeywordInfo(0x98, "PRINT# |,",  "Writes data to an open file. PRINT# file,expression",                    "Input & Output"),
        "PRINT":   KeywordInfo(0x99, "PRINT \"|\"", "Displays output on the screen. PRINT [expression][;|,]",                 "Input & Output"),
        "CONT":    KeywordInfo(0x9A, "CONT",       "Continues execution after STOP or END.",                                  "Control Flow"),
        "LIST":    KeywordInfo(0x9B, "LIST",       "Lists program lines. LIST [start[-end]]",                                 "Program Editing"),
        "CLR":     KeywordInfo(0x9C, "CLR",        "Clears all variables, arrays, and the GOSUB stack.",                      "Program Editing"),
        "CMD":     KeywordInfo(0x9D, "CMD |",      "Redirects PRINT output to a device. CMD device[,string]",                 "Input & Output"),
        "SYS":     KeywordInfo(0x9E, "SYS |",      "Executes machine code at an address. SYS addr",                          "System & Memory"),
        "OPEN":    KeywordInfo(0x9F, "OPEN |,",    "Opens a logical file. OPEN file,device[,secondary[,\"name\"]]",           "Files & Devices"),
        "CLOSE":   KeywordInfo(0xA0, "CLOSE |",    "Closes a logical file. CLOSE file",                                       "Files & Devices"),
        "GET":     KeywordInfo(0xA1, "GET |",      "Reads a single keypress without waiting for input. GET var$",             "Input & Output"),
        "NEW":     KeywordInfo(0xA2, "NEW",        "Erases the current program and all variables.",                          "Program Editing"),

        # More Keywords
        "TAB":  KeywordInfo(0xA3, "TAB(|)", "Moves the PRINT cursor to column n. Used with PRINT. TAB(n)", "Input & Output"),
        "TO":   KeywordInfo(0xA4, "TO |",   "Sets the upper bound of a FOR loop. FOR v=start TO end",       "Control Flow"),
        "FN":   KeywordInfo(0xA5, "FN |(|)", "Calls a user-defined function. FN name(arg)",                 "Variables & Data"),
        "SPC":  KeywordInfo(0xA6, "SPC(|)", "Prints n spaces. Used with PRINT. SPC(n)",                     "Input & Output"),
        "THEN": KeywordInfo(0xA7, "THEN |", "Introduces the branch taken when an IF condition is true. IF cond THEN ...", "Control Flow"),
        "NOT":  KeywordInfo(0xA8, "NOT ",   "Reverses a condition's truth value. NOT expression",           "Logical Operators"),
        "STEP": KeywordInfo(0xA9, "STEP |", "Sets the step size in a FOR loop. FOR v=x TO y STEP n",         "Control Flow"),

        # Operators
        "+": KeywordInfo(0xAA, None, None, None),
        "-": KeywordInfo(0xAB, None, None, None),
        "*": KeywordInfo(0xAC, None, None, None),
        "/": KeywordInfo(0xAD, None, None, None),
        "^": KeywordInfo(0xAE, None, None, None),
        "AND": KeywordInfo(0xAF, "AND ", "Combines two conditions; true only if both are true. expression1 AND expression2", "Logical Operators"),
        "OR":  KeywordInfo(0xB0, "OR ",  "Combines two conditions; true if either is true. expression1 OR expression2",     "Logical Operators"),
        ">": KeywordInfo(0xB1, None, None, None),
        "=": KeywordInfo(0xB2, None, None, None),
        "<": KeywordInfo(0xB3, None, None, None),

        # Math/String Functions
        "SGN":    KeywordInfo(0xB4, "SGN(|)",    "Returns the sign of a number: -1, 0, or 1. SGN(n)",             "Math Functions"),
        "INT":    KeywordInfo(0xB5, "INT(|)",    "Rounds a number down to the nearest integer. INT(n)",           "Math Functions"),
        "ABS":    KeywordInfo(0xB6, "ABS(|)",    "Returns the absolute value of a number. ABS(n)",                "Math Functions"),
        "USR":    KeywordInfo(0xB7, "USR(|)",    "Calls a user machine-code function via the $0311 vector. USR(n)", "System & Memory"),
        "FRE":    KeywordInfo(0xB8, "FRE(0)",    "Returns the number of bytes of free memory. FRE(0)",            "System & Memory"),
        "POS":    KeywordInfo(0xB9, "POS(0)",    "Returns the current cursor column (0-based). POS(0)",           "System & Memory"),
        "SQR":    KeywordInfo(0xBA, "SQR(|)",    "Returns the square root of a number. SQR(n)",                   "Math Functions"),
        "RND":    KeywordInfo(0xBB, "RND(1)",    "Returns a random number, 0 <= n < 1. RND(1)  [RND(-n) reseeds]", "Math Functions"),
        "LOG":    KeywordInfo(0xBC, "LOG(|)",    "Returns the natural logarithm of a number. LOG(n)",             "Math Functions"),
        "EXP":    KeywordInfo(0xBD, "EXP(|)",    "Returns e raised to a power. EXP(n)",                           "Math Functions"),
        "COS":    KeywordInfo(0xBE, "COS(|)",    "Returns the cosine of an angle, in radians. COS(n)",            "Math Functions"),
        "SIN":    KeywordInfo(0xBF, "SIN(|)",    "Returns the sine of an angle, in radians. SIN(n)",              "Math Functions"),
        "TAN":    KeywordInfo(0xC0, "TAN(|)",    "Returns the tangent of an angle, in radians. TAN(n)",           "Math Functions"),
        "ATN":    KeywordInfo(0xC1, "ATN(|)",    "Returns the arc-tangent of a number, in radians. ATN(n)",       "Math Functions"),
        "PEEK":   KeywordInfo(0xC2, "PEEK(|)",   "Reads a byte from a memory address. PEEK(addr)",                "System & Memory"),
        "LEN":    KeywordInfo(0xC3, "LEN(|)",    "Returns the length of a string. LEN(str$)",                     "String Functions"),
        "STR$":   KeywordInfo(0xC4, "STR$(|)",   "Converts a number to a string. STR$(n)",                        "String Functions"),
        "VAL":    KeywordInfo(0xC5, "VAL(|)",    "Converts a string to a number. VAL(str$)",                      "String Functions"),
        "ASC":    KeywordInfo(0xC6, "ASC(|)",    "Returns the PETSCII code of a string's first character. ASC(str$)", "String Functions"),
        "CHR$":   KeywordInfo(0xC7, "CHR$(|)",   "Returns the character for a PETSCII code. CHR$(n)",             "String Functions"),
        "LEFT$":  KeywordInfo(0xC8, "LEFT$(|,)", "Returns the leftmost n characters of a string. LEFT$(str$,n)",  "String Functions"),
        "RIGHT$": KeywordInfo(0xC9, "RIGHT$(|,)", "Returns the rightmost n characters of a string. RIGHT$(str$,n)", "String Functions"),
        "MID$":   KeywordInfo(0xCA, "MID$(|,,)", "Returns a substring starting at a position. MID$(str$,start[,len])", "String Functions"),
        "GO":     KeywordInfo(0xCB, "GO TO |",   "Jumps to a line number (alternate form of GOTO). GO TO line",   "Control Flow"),
    }

    TokenMap: Dict[str, int] = {k: v.token for k, v in Keywords.items()}
    ReverseTokenMap: Dict[int, str] = {v: k for k, v in TokenMap.items()}

    WordKeywordsLongestFirst: List[str] = sorted(
        [k for k in Keywords.keys() if k[0].isalpha()],
        key=lambda x: (-len(x), x)
    )

    AllKeywordsLongestFirst: List[str] = sorted(
        list(Keywords.keys()),
        key=lambda x: (-len(x), x)
    )

    @classmethod
    def is_token(cls, word: str) -> bool:
        return word.upper() in cls.TokenMap

    @classmethod
    def try_get_token(cls, word: str) -> Tuple[bool, int]:
        upper = word.upper()
        if upper in cls.TokenMap:
            return True, cls.TokenMap[upper]
        return False, 0

    @classmethod
    def try_match_keyword(cls, text: str, position: int, candidates: List[str]) -> Tuple[bool, str]:
        for candidate in candidates:
            if position + len(candidate) > len(text):
                continue
            if text[position:position + len(candidate)].upper() == candidate:
                return True, candidate
        return False, ""


class BasicKeywordAbbreviations:
    ToKeyword: Dict[str, str] = {
        "Ab":  "ABS",
        "An":  "AND",
        "As":  "ASC",
        "At":  "ATN",
        "Ch":  "CHR$",
        "CLo": "CLOSE",
        "Cl":  "CLR",
        "Cm":  "CMD",
        "Co":  "CONT",
        "Da":  "DATA",
        "De":  "DEF",
        "Di":  "DIM",
        "En":  "END",
        "Ex":  "EXP",
        "Fo":  "FOR",
        "Fr":  "FRE",
        "Ge":  "GET",
        "GOs": "GOSUB",
        "Go":  "GOTO",
        "In":  "INPUT#",
        "LEf": "LEFT$",
        "Le":  "LET",
        "Li":  "LIST",
        "Lo":  "LOAD",
        "Mi":  "MID$",
        "Ne":  "NEXT",
        "No":  "NOT",
        "Op":  "OPEN",
        "Pe":  "PEEK",
        "Po":  "POKE",
        "Pr":  "PRINT#",
        "Re":  "READ",
        "REs": "RESTORE",
        "REt": "RETURN",
        "Ri":  "RIGHT$",
        "Rn":  "RND",
        "Ru":  "RUN",
        "Sa":  "SAVE",
        "Sg":  "SGN",
        "Si":  "SIN",
        "Sp":  "SPC",
        "Sq":  "SQR",
        "STe": "STEP",
        "St":  "STOP",
        "STr": "STR$",
        "Sy":  "SYS",
        "Ta":  "TAB",
        "Us":  "USR",
        "Va":  "VAL",
        "Ve":  "VERIFY",
        "Wa":  "WAIT",
    }

    MaxLength: int = max(len(k) for k in ToKeyword.keys())

    @classmethod
    def try_match_keyword_or_abbreviation(
        cls, text: str, position: int, keyword_candidates: List[str]
    ) -> Tuple[bool, str, int]:
        keyword = ""
        matched_length = 0

        success, full_keyword = BasicTokens.try_match_keyword(text, position, keyword_candidates)
        if success:
            keyword = full_keyword
            matched_length = len(full_keyword)

        for length in range(cls.MaxLength, matched_length, -1):
            if position + length > len(text):
                continue
            sub = text[position:position + length]
            if sub in cls.ToKeyword:
                keyword = cls.ToKeyword[sub]
                matched_length = length
                break

        return matched_length > 0, keyword, matched_length


class TokenizeLineResult:
    def __init__(self, success: bool, tokens: bytes = b"", error_message: Optional[str] = None):
        self.success = success
        self.tokens = tokens
        self.error_message = error_message


class BasicTokenizer:
    _remToken = BasicTokens.TokenMap["REM"]

    def tokenize_line(self, line: str) -> TokenizeLineResult:
        if not line or line.isspace():
            return TokenizeLineResult(success=True, tokens=b"")

        try:
            tokens = bytearray()
            pos = 0

            while pos < len(line):
                # Whitespace: collapse consecutive runs to one space.
                if line[pos].isspace():
                    if len(tokens) > 0 and tokens[-1] != ord(' '):
                        tokens.append(ord(' '))
                    while pos < len(line) and line[pos].isspace():
                        pos += 1
                    continue

                # String literal: emit bytes verbatim until closing quote.
                if line[pos] == '"':
                    tokens.append(ord('"'))
                    pos += 1
                    while pos < len(line) and line[pos] != '"':
                        tokens.append(ord(line[pos]))
                        pos += 1
                    if pos < len(line):
                        tokens.append(ord('"'))
                        pos += 1
                    continue

                # PRINT shortcut "?"
                if line[pos] == '?':
                    tokens.append(BasicTokens.TokenMap["PRINT"])
                    pos += 1
                    continue

                # Greedy keyword or abbreviation scan
                success, keyword, matched_length = BasicKeywordAbbreviations.try_match_keyword_or_abbreviation(
                    line, pos, BasicTokens.AllKeywordsLongestFirst
                )
                if success:
                    token = BasicTokens.TokenMap[keyword]
                    tokens.append(token)
                    pos += matched_length

                    # REM comment block
                    if token == self._remToken:
                        if pos < len(line) and line[pos] == ' ':
                            tokens.append(ord(' '))
                            pos += 1
                        while pos < len(line):
                            tokens.append(ord(line[pos]))
                            pos += 1
                else:
                    # Literal character
                    tokens.append(ord(line[pos].upper()))
                    pos += 1

            return TokenizeLineResult(success=True, tokens=bytes(tokens))
        except Exception as ex:
            return TokenizeLineResult(success=False, error_message=f"Tokenization error: {str(ex)}")

    def tokenize_program(self, source_code: str) -> List[TokenizeLineResult]:
        results = []
        for line in source_code.splitlines():
            results.append(self.tokenize_line(line))
        return results


class PrgConverter:
    _loadAddress = 0x0801

    def __init__(self):
        self.last_debug_info: Optional[str] = None

    def convert_to_prg(self, source_code: str) -> bytes:
        tokenizer = BasicTokenizer()
        # Handle all platform linebreaks
        lines = source_code.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        parsed_lines = []
        debug_lines = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            debug_lines.append(f"Parsing: '{trimmed}'")

            parts = self._parse_line_number_and_code(trimmed)
            if parts is None:
                debug_lines.append("  ERROR: Failed to parse line number")
                continue

            line_number, code = parts

            # Skip lines that have only a line number and no code
            if not code or code.isspace():
                debug_lines.append(f"  SKIP: line {line_number} has no code")
                continue

            debug_lines.append(f"  LineNum: {line_number}, Code: '{code}'")

            token_result = tokenizer.tokenize_line(code)
            if not token_result.success:
                debug_lines.append(f"  ERROR: Tokenization failed - {token_result.error_message}")
                continue

            debug_lines.append(f"  OK: {len(token_result.tokens)} bytes")
            parsed_lines.append((line_number, token_result.tokens))

        self.last_debug_info = "\n".join(debug_lines)

        if not parsed_lines:
            # Minimal valid PRG with load address and end marker
            return bytes([0x01, 0x08, 0x00, 0x00])

        program_data = bytearray()
        # Add load address (little endian)
        program_data.append(self._loadAddress & 0xFF)
        program_data.append((self._loadAddress >> 8) & 0xFF)

        for i, (line_number, tokens) in enumerate(parsed_lines):
            line_bytes = bytearray()
            # Placeholder for next line address
            next_address_offset = len(line_bytes)
            line_bytes.append(0)
            line_bytes.append(0)

            # Line number (little endian)
            line_bytes.append(line_number & 0xFF)
            line_bytes.append((line_number >> 8) & 0xFF)

            # Tokenized code
            line_bytes.extend(tokens)

            # Line terminator
            line_bytes.append(0x00)

            # Current address in memory
            current_line_address = self._loadAddress + len(program_data) - 2
            next_address = current_line_address + len(line_bytes)

            line_bytes[next_address_offset] = next_address & 0xFF
            line_bytes[next_address_offset + 1] = (next_address >> 8) & 0xFF

            program_data.extend(line_bytes)

        # Program end marker
        program_data.append(0x00)
        program_data.append(0x00)

        return bytes(program_data)

    def convert_from_prg(self, data: bytes) -> str:
        if len(data) < 4:
            raise ValueError("File is too small to be a valid C64 program.")

        lines = []
        pos = 2

        while pos + 1 < len(data):
            link = data[pos] | (data[pos + 1] << 8)
            pos += 2

            if link == 0x0000:
                break

            if pos + 1 >= len(data):
                break

            line_number = data[pos] | (data[pos + 1] << 8)
            pos += 2

            tokens = bytearray()
            while pos < len(data) and data[pos] != 0x00:
                tokens.append(data[pos])
                pos += 1

            if pos < len(data):
                pos += 1

            lines.append(f"{line_number} {self._detokenize_line(bytes(tokens))}")

        return "\n".join(lines)

    def is_basic_program(self, data: bytes) -> bool:
        if len(data) < 4 or data[0] != (self._loadAddress & 0xFF) or data[1] != (self._loadAddress >> 8):
            return False

        pos = 2
        while True:
            if pos + 1 >= len(data):
                return False

            link = data[pos] | (data[pos + 1] << 8)
            if link == 0x0000:
                return pos + 2 == len(data)

            pos += 2
            if pos + 1 >= len(data):
                return False
            pos += 2  # Skip line number

            while pos < len(data) and data[pos] != 0x00:
                pos += 1

            if pos >= len(data):
                return False  # Missing line terminator
            pos += 1

            expected_link = self._loadAddress + pos - 2
            if link != expected_link:
                return False

    def _detokenize_line(self, tokens: bytes) -> str:
        chars = []
        in_string = False

        for b in tokens:
            if b == ord('"'):
                in_string = not in_string
                chars.append('"')
                continue

            if not in_string and b in BasicTokens.ReverseTokenMap:
                chars.append(BasicTokens.ReverseTokenMap[b])
            else:
                chars.append(chr(b))

        return "".join(chars)

    def _parse_line_number_and_code(self, line: str) -> Optional[Tuple[int, str]]:
        i = 0
        while i < len(line) and line[i].isdigit():
            i += 1

        if i == 0:
            return None

        try:
            line_number = int(line[0:i])
        except ValueError:
            return None

        if line_number < 0 or line_number > 65535:
            return None

        if i < len(line) and line[i] == ' ':
            i += 1

        return line_number, line[i:] if i < len(line) else ""
