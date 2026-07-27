# Copyright (c) 2026 Moonspace Labs, LLC
# Licensed under the MIT License. See LICENSE in the project root for license information.

"""
Optimizes and formats C64 BASIC source code (Minify and Prettify transformations).
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Set
from .tokenizer import BasicTokens, BasicKeywordAbbreviations

class CodeMinifier:
    @staticmethod
    def minify(
        source: str,
        remove_whitespace: bool,
        replace_0_with_period: bool,
        use_scientific_notation: bool,
        remove_comments: bool,
        simplify_next_statements: bool,
        renumber_lines: bool
    ) -> str:
        """
        Applies size-reduction transformations to C64 BASIC source code in a fixed order.
        """
        if remove_comments:
            source = CodeMinifier.remove_comments(source)
        if replace_0_with_period:
            source = CodeMinifier.replace_0_with_period(source)
        if use_scientific_notation:
            source = CodeMinifier.use_scientific_notation(source)
        if simplify_next_statements:
            source = CodeMinifier.simplify_next_statements(source)
        if renumber_lines:
            source = CodeMinifier.renumber_lines(source)
        if remove_whitespace:
            source = CodeMinifier.remove_whitespace(source)
        return source

    @staticmethod
    def remove_whitespace(source: str) -> str:
        """
        Removes all whitespace outside string literals and DATA statements from each line.
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            before, data_part = CodeMinifier._split_at_data(code.strip())
            compact = CodeMinifier._transform_outside_strings(
                before, lambda s: s.replace(" ", "")
            ) + CodeMinifier._trim_data_leading_space(data_part)
            result.append(line_num + compact)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def replace_0_with_period(source: str) -> str:
        """
        Replaces a leading zero before a decimal point (e.g. "0.5" -> ".5") outside strings.
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            transformed = CodeMinifier._transform_outside_strings_and_data(
                code, lambda s: re.sub(r'(?<!\d)0\.(\d)', r'.\1', s)
            )
            result.append(line_num + " " + transformed)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def use_scientific_notation(source: str) -> str:
        """
        Shortens large integer literals to scientific (E) notation where strictly shorter.
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            transformed = CodeMinifier._transform_outside_strings_and_data(
                code, CodeMinifier._shorten_integers
            )
            result.append(line_num + " " + transformed)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def remove_comments(source: str) -> str:
        """
        Removes REM statements and trailing comments, redirecting jump references.
        """
        lines = CodeMinifier._split_lines(source)

        # First pass: build redirect map
        parsed = []
        for line in lines:
            if not line or line.isspace():
                continue
            line_num_str, code = CodeMinifier.split_basic_line(line)
            if line_num_str is not None:
                try:
                    parsed.append((int(line_num_str), code))
                except ValueError:
                    pass

        redirect_map = {}
        pending_nums = []
        for num, code in parsed:
            if CodeMinifier._is_rem_statement(code):
                pending_nums.append(num)
            else:
                for rem_num in pending_nums:
                    redirect_map[rem_num] = num
                pending_nums.clear()

        # Second pass: emit surviving lines
        result = []
        for line in lines:
            if not line or line.isspace():
                continue
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            if CodeMinifier._is_rem_statement(code):
                continue

            stripped = CodeMinifier._strip_inline_rem_outside_data(code).rstrip()

            if redirect_map:
                stripped = CodeMinifier._update_line_references(stripped, redirect_map)

            result.append(line_num + " " + stripped)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def simplify_next_statements(source: str) -> str:
        """
        Strips variable names from NEXT statements (e.g. "NEXT I" -> "NEXT").
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            simplified = CodeMinifier._transform_outside_strings_and_data(
                code,
                lambda s: re.sub(
                    r'\bNEXT\s+[A-Z][A-Z0-9$]*(?:\s*,\s*[A-Z][A-Z0-9$]*)*',
                    'NEXT',
                    s,
                    flags=re.IGNORECASE
                )
            )
            result.append(line_num + " " + simplified)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def renumber_lines(source: str) -> str:
        """
        Renumbers all BASIC line numbers sequentially starting at 0.
        """
        numbered = []
        for line in CodeMinifier._split_lines(source):
            if not line or line.isspace():
                continue
            line_num_str, code = CodeMinifier.split_basic_line(line)
            if line_num_str is not None:
                try:
                    numbered.append((int(line_num_str), code))
                except ValueError:
                    pass

        mapping = {old_num: i for i, (old_num, _) in enumerate(numbered)}

        result = []
        for old_num, code in numbered:
            new_num = mapping[old_num]
            updated_code = CodeMinifier._update_line_references(code, mapping)
            result.append(f"{new_num} {updated_code}")
        return CodeMinifier._join_lines(result)

    @staticmethod
    def split_basic_line(line: str) -> Tuple[Optional[str], str]:
        """
        Splits a source line into its line number and code, stripping leading zeros.
        """
        if not line or line.isspace():
            return None, line
        i = 0
        while i < len(line) and line[i] == ' ':
            i += 1
        if i >= len(line) or not line[i].isdigit():
            return None, line
        num_start = i
        while i < len(line) and line[i].isdigit():
            i += 1
        line_num = line[num_start:i].lstrip('0')
        if not line_num:
            line_num = "0"
        while i < len(line) and line[i] == ' ':
            i += 1
        code = line[i:] if i < len(line) else ""
        return line_num, code

    # Private Helpers

    @staticmethod
    def _transform_outside_strings_and_data(code: str, transform_func) -> str:
        before, data_part = CodeMinifier._split_at_data(code)
        return CodeMinifier._transform_outside_strings(before, transform_func) + data_part

    @staticmethod
    def _split_at_data(code: str) -> Tuple[str, str]:
        idx = CodeMinifier._find_data_keyword_start(code)
        return (code, "") if idx < 0 else (code[:idx], code[idx:])

    @staticmethod
    def _trim_data_leading_space(data_part: str) -> str:
        if not data_part:
            return data_part
        keyword_length = 4 if len(data_part) >= 4 and data_part[:4].upper() == "DATA" else 2
        i = keyword_length
        while i < len(data_part) and data_part[i] == ' ':
            i += 1
        return data_part[:keyword_length] + data_part[i:]

    @staticmethod
    def _find_data_keyword_start(code: str) -> int:
        in_string = False
        i = 0
        while i < len(code):
            c = code[i]
            if c == '"':
                in_string = not in_string
                i += 1
                continue
            if in_string:
                i += 1
                continue

            is_data = False
            if i + 4 <= len(code) and code[i:i+4].upper() == "DATA":
                is_data = True
            elif i + 2 <= len(code) and code[i:i+2] == "Da":
                is_data = True

            if is_data:
                preceded_ok = i == 0 or not code[i - 1].isalnum()
                if preceded_ok:
                    return i
            i += 1
        return -1

    @staticmethod
    def _transform_outside_strings(code: str, transform_func) -> str:
        parts = []
        i = 0
        while i < len(code):
            if code[i] == '"':
                start = i
                i += 1
                while i < len(code) and code[i] != '"':
                    i += 1
                if i < len(code):
                    i += 1
                parts.append(code[start:i])
            else:
                start = i
                while i < len(code) and code[i] != '"':
                    i += 1
                parts.append(transform_func(code[start:i]))
        return "".join(parts)

    @staticmethod
    def _is_rem_statement(code: str) -> bool:
        trimmed = code.lstrip()
        if not trimmed.upper().startswith("REM"):
            return False
        return len(trimmed) == 3 or trimmed[3] in (' ', '\t')

    @staticmethod
    def _strip_inline_rem_outside_data(code: str) -> str:
        before, data_part = CodeMinifier._split_at_data(code)
        return CodeMinifier._strip_inline_rem(before) + data_part

    @staticmethod
    def _strip_inline_rem(code: str) -> str:
        in_string = False
        i = 0
        while i < len(code):
            c = code[i]
            if c == '"':
                in_string = not in_string
                i += 1
                continue
            if not in_string and c == ':':
                colon_pos = i
                i += 1
                while i < len(code) and code[i] == ' ':
                    i += 1
                # Check for REM
                if i + 3 <= len(code) and code[i:i+3].upper() == "REM":
                    if i + 3 >= len(code) or not code[i+3].isalnum():
                        return code[:colon_pos]
                continue
            i += 1
        return code

    @staticmethod
    def _shorten_integers(segment: str) -> str:
        def repl(m):
            original = m.group(0)
            try:
                value = int(original)
            except ValueError:
                return original
            if value < 10000:
                return original

            temp = value
            zeros = 0
            while temp % 10 == 0:
                temp //= 10
                zeros += 1

            if zeros == 0:
                return original

            e_form = f"{temp}E{zeros}"
            return e_form if len(e_form) < len(original) else original

        return re.sub(r'(?<!\d)\d+(?!\d)', repl, segment)

    @staticmethod
    def _update_line_references(code: str, mapping: Dict[int, int]) -> str:
        def repl_outer(m):
            keyword = m.group(1)
            nums_part = m.group(2)

            def repl_inner(num_match):
                try:
                    old = int(num_match.group(0))
                except ValueError:
                    return num_match.group(0)
                if old in mapping:
                    return str(mapping[old])
                return num_match.group(0)

            updated_nums = re.sub(r'\d+', repl_inner, nums_part)
            return keyword + " " + updated_nums

        return re.sub(
            r'(GOTO|GOSUB|THEN|RESTORE|RUN)\s*(\d+(?:\s*,\s*\d+)*)',
            repl_outer,
            code,
            flags=re.IGNORECASE
        )

    @staticmethod
    def _split_lines(source: str) -> List[str]:
        return source.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    @staticmethod
    def _join_lines(lines: List[str]) -> str:
        return "\n".join(lines)


class CodePrettifier:
    _functionKeywords: Set[str] = {
        "SGN", "INT", "ABS", "USR", "FRE", "POS", "SQR", "RND", "LOG", "EXP",
        "COS", "SIN", "TAN", "ATN", "PEEK", "LEN", "STR$", "VAL", "ASC",
        "CHR$", "LEFT$", "RIGHT$", "MID$", "FN", "TAB", "SPC",
        "PRINT#", "INPUT#", "GET#"
    }

    @staticmethod
    def prettify(
        source: str,
        add_whitespace: bool,
        replace_period_with_zero: bool,
        use_standard_notation: bool,
        add_next_variables: bool,
        renumber_lines: bool,
        line_number_increment: int = 10,
        line_number_padding: int = 0
    ) -> str:
        """
        Applies readability-oriented transformations in a fixed order.
        """
        if add_next_variables:
            source = CodePrettifier.add_next_variables(source)
        if replace_period_with_zero:
            source = CodePrettifier.replace_period_with_zero(source)
        if use_standard_notation:
            source = CodePrettifier.use_standard_notation(source)
        if renumber_lines:
            source = CodePrettifier.renumber_lines(
                source, line_number_increment, line_number_increment, line_number_padding
            )
        if add_whitespace:
            source = CodePrettifier.add_whitespace(source)
        return source

    @staticmethod
    def add_whitespace(source: str) -> str:
        """
        Inserts spaces around BASIC keywords outside string literals.
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            # Parse line number manually to preserve padding
            j = 0
            while j < len(line) and line[j] == ' ':
                j += 1
            if j >= len(line) or not line[j].isdigit():
                result.append(line)
                continue
            num_start = j
            while j < len(line) and line[j].isdigit():
                j += 1
            raw_line_num = line[num_start:j]
            while j < len(line) and line[j] == ' ':
                j += 1
            code = line[j:] if j < len(line) else ""

            result.append(raw_line_num + " " + CodePrettifier._space_keywords(code))
        return CodeMinifier._join_lines(result)

    @staticmethod
    def replace_period_with_zero(source: str) -> str:
        """
        Replaces bare periods (e.g. ".5" -> "0.5", "." -> "0") outside strings.
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            def repl(m):
                if m.group(1) is not None:
                    return "0." + m.group(1)
                return "0"

            transformed = CodeMinifier._transform_outside_strings(
                code, lambda s: re.sub(r'(?<![0-9])\.(\d)?', repl, s)
            )
            result.append(line_num + " " + transformed)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def use_standard_notation(source: str) -> str:
        """
        Expands scientific (E) notation integer literals back to full decimal form.
        """
        result = []
        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            transformed = CodeMinifier._transform_outside_strings(code, CodePrettifier._expand_e_notation)
            result.append(line_num + " " + transformed)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def add_next_variables(source: str) -> str:
        """
        Adds the matching FOR loop variable to bare NEXT statements.
        """
        for_stack = []
        result = []

        for line in CodeMinifier._split_lines(source):
            line_num, code = CodeMinifier.split_basic_line(line)
            if line_num is None:
                result.append(line)
                continue

            updated_code = CodePrettifier._process_statements(code, for_stack)
            result.append(line_num + " " + updated_code)
        return CodeMinifier._join_lines(result)

    @staticmethod
    def renumber_lines(source: str, start: int, increment: int, padding: int) -> str:
        """
        Renumbers all BASIC line numbers sequentially.
        """
        numbered = []
        for line in CodeMinifier._split_lines(source):
            if not line or line.isspace():
                continue
            line_num_str, code = CodeMinifier.split_basic_line(line)
            if line_num_str is not None:
                try:
                    numbered.append((int(line_num_str), code))
                except ValueError:
                    pass

        mapping = {old_num: start + i * increment for i, (old_num, _) in enumerate(numbered)}

        result = []
        for old_num, code in numbered:
            new_num = mapping[old_num]
            num_str = str(new_num).zfill(padding) if padding > 0 else str(new_num)
            updated = CodeMinifier._update_line_references(code, mapping)
            result.append(f"{num_str} {updated}")
        return CodeMinifier._join_lines(result)

    # Internal helper for processing statements
    @staticmethod
    def _split_statements(code: str) -> List[str]:
        statements = []
        current = []
        in_string = False

        for c in code:
            if c == '"':
                in_string = not in_string
                current.append(c)
            elif not in_string and c == ':':
                statements.append("".join(current))
                current.clear()
            else:
                current.append(c)
        statements.append("".join(current))
        return statements

    # Private Helpers

    @staticmethod
    def _space_keywords(code: str) -> str:
        sb = []
        i = 0
        prev_is_space = True
        last_was_operand = False

        while i < len(code):
            c = code[i]

            # String literal
            if c == '"':
                prev_is_space = False
                sb.append(c)
                i += 1
                while i < len(code) and code[i] != '"':
                    sb.append(code[i])
                    i += 1
                if i < len(code):
                    sb.append(code[i])
                    i += 1
                last_was_operand = True
                continue

            # Statement separator
            if c == ':':
                sb.append(c)
                i += 1
                prev_is_space = True
                last_was_operand = False
                continue

            # Operators
            if c in '=+-*/^<>':
                op = CodePrettifier._match_operator_token(code, i)
                is_unary_minus = (op == "-" and not last_was_operand)

                if is_unary_minus:
                    sb.append(op)
                    i += len(op)
                    prev_is_space = False
                else:
                    if not prev_is_space:
                        sb.append(' ')
                    sb.append(op)
                    sb.append(' ')
                    i += len(op)
                    prev_is_space = True
                    last_was_operand = False
                continue

            # Existing space
            if c == ' ':
                if not prev_is_space:
                    sb.append(' ')
                prev_is_space = True
                i += 1
                continue

            # Try to match keyword
            success, kw = BasicTokens.try_match_keyword(code, i, BasicTokens.WordKeywordsLongestFirst)
            if success:
                if not prev_is_space:
                    sb.append(' ')

                sb.append(kw.upper())
                i += len(kw)
                prev_is_space = False
                last_was_operand = False

                if kw.upper() == "REM":
                    if i < len(code) and code[i] != ' ':
                        sb.append(' ')
                    sb.append(code[i:])
                    break

                if kw.upper() == "DATA":
                    while i < len(code) and code[i] == ' ':
                        i += 1
                    if i < len(code):
                        sb.append(' ')
                    sb.append(code[i:])
                    break

                is_func = kw.upper() in CodePrettifier._functionKeywords
                next_ch = code[i] if i < len(code) else '\0'
                needs_space = (
                    not is_func
                    and next_ch != '\0'
                    and next_ch not in '::,;('
                    and next_ch != ' '
                )

                if needs_space:
                    sb.append(' ')
                    prev_is_space = True
            else:
                sb.append(c)
                prev_is_space = False
                last_was_operand = c.isalnum() or c in '$%)'
                i += 1

        return "".join(sb)

    @staticmethod
    def _match_operator_token(code: str, pos: int) -> str:
        c = code[pos]
        next_c = code[pos + 1] if pos + 1 < len(code) else '\0'

        if c == '<' and next_c == '>':
            return "<>"
        if c == '<' and next_c == '=':
            return "<="
        if c == '>' and next_c == '=':
            return ">="

        return c

    @staticmethod
    def _process_statements(code: str, for_stack: List[str]) -> str:
        statements = CodePrettifier._split_statements(code)
        result = []

        for stmt in statements:
            trimmed = stmt.lstrip()
            indent = len(stmt) - len(trimmed)
            prefix = stmt[:indent]

            # FOR loop
            for_match = re.match(r'^FOR\s*([A-Z][A-Z0-9$]?)\s*=', trimmed, re.IGNORECASE)
            if for_match:
                for_stack.append(for_match.group(1).upper())
                result.append(stmt)
                continue

            # Bare NEXT
            if re.match(r'^NEXT\s*$', trimmed, re.IGNORECASE):
                if for_stack:
                    result.append(prefix + "NEXT " + for_stack.pop())
                else:
                    result.append(stmt)
                continue

            # NEXT with vars
            next_var_match = re.match(
                r'^NEXT\s*(?:[A-Z][A-Z0-9$]*\s*,\s*)*[A-Z][A-Z0-9$]*', trimmed, re.IGNORECASE
            )
            if next_var_match:
                var_count = len(trimmed[4:].split(','))
                for _ in range(var_count):
                    if for_stack:
                        for_stack.pop()
                result.append(stmt)
                continue

            result.append(stmt)

        return ":".join(result)

    @staticmethod
    def _expand_e_notation(segment: str) -> str:
        def repl(m):
            try:
                mantissa = float(m.group(1))
                exponent = int(m.group(2))
            except ValueError:
                return m.group(0)

            value = mantissa * (10 ** exponent)
            if value != math.floor(value) or value > 1e15 or value < 0:
                return m.group(0)

            return str(int(value))

        return re.sub(r'(?<![A-Z0-9\.])(\d+(?:\.\d+)?)E(\d+)(?![A-Z0-9])', repl, segment, flags=re.IGNORECASE)
