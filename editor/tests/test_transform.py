import pytest
from readycode_py.transform import CodeMinifier, CodePrettifier

# -- SplitBasicLine --

def test_split_basic_line_parses_line_number_and_code():
    num, code = CodeMinifier.split_basic_line("10 PRINT \"HI\"")
    assert num == "10"
    assert code == "PRINT \"HI\""

def test_split_basic_line_strips_padding_zeros():
    num, _ = CodeMinifier.split_basic_line("0010 PRINT A")
    assert num == "10"

def test_split_basic_line_returns_null_line_num_for_non_basic_line():
    num, _ = CodeMinifier.split_basic_line("PRINT A")
    assert num is None

def test_split_basic_line_handles_line_zero():
    num, code = CodeMinifier.split_basic_line("0 END")
    assert num == "0"
    assert code == "END"

# -- RemoveWhitespace --

def test_remove_whitespace_removes_all_spaces_outside_strings():
    assert CodeMinifier.remove_whitespace("10  PRINT  A") == "10PRINTA"

def test_remove_whitespace_preserves_spaces_inside_strings():
    assert CodeMinifier.remove_whitespace("10 PRINT  \"HELLO   WORLD\"") == "10PRINT\"HELLO   WORLD\""

def test_remove_whitespace_removes_space_between_keyword_and_operands():
    assert CodeMinifier.remove_whitespace("10   FOR   I=1   TO   10") == "10FORI=1TO10"

def test_remove_whitespace_multiple_lines():
    assert CodeMinifier.remove_whitespace("10  PRINT A\n20  END") == "10PRINTA\n20END"

def test_remove_whitespace_removes_space_after_line_number():
    assert CodeMinifier.remove_whitespace("10 PRINT \"HI\"") == "10PRINT\"HI\""

# -- Replace0WithPeriod --

def test_replace_0_with_period_replaces_leading_zero():
    assert CodeMinifier.replace_0_with_period("10 X=0.5") == "10 X=.5"

def test_replace_0_with_period_does_not_replace_non_leading_zero():
    assert CodeMinifier.replace_0_with_period("10 X=10.5") == "10 X=10.5"

def test_replace_0_with_period_replaces_multiple_occurrences():
    assert CodeMinifier.replace_0_with_period("10 X=0.5:Y=0.1") == "10 X=.5:Y=.1"

def test_replace_0_with_period_preserves_inside_strings():
    assert CodeMinifier.replace_0_with_period("10 PRINT \"0.5\"") == "10 PRINT \"0.5\""

def test_replace_0_with_period_does_not_replace_zero_alone():
    assert CodeMinifier.replace_0_with_period("10 X=0") == "10 X=0"

# -- UseScientificNotation --

def test_use_scientific_notation_converts_round_number():
    assert CodeMinifier.use_scientific_notation("10 X=10000") == "10 X=1E4"

def test_use_scientific_notation_converts_multiple_numbers():
    assert CodeMinifier.use_scientific_notation("10 X=20000:Y=100000") == "10 X=2E4:Y=1E5"

def test_use_scientific_notation_leaves_non_round_number_unchanged():
    assert CodeMinifier.use_scientific_notation("10 X=32768") == "10 X=32768"

def test_use_scientific_notation_ignores_small_numbers():
    assert CodeMinifier.use_scientific_notation("10 X=100") == "10 X=100"

def test_use_scientific_notation_preserves_inside_strings():
    assert CodeMinifier.use_scientific_notation("10 PRINT \"10000\"") == "10 PRINT \"10000\""

def test_use_scientific_notation_handles_exact_threshold():
    assert CodeMinifier.use_scientific_notation("10 X=9999") == "10 X=9999"
    assert CodeMinifier.use_scientific_notation("10 X=10000") == "10 X=1E4"

# -- RemoveComments --

def test_remove_comments_removes_pure_rem_line():
    input_text = "10 PRINT \"HI\"\n20 REM this is a comment\n30 END"
    assert CodeMinifier.remove_comments(input_text) == "10 PRINT \"HI\"\n30 END"

def test_remove_comments_removes_inline_rem_after_colon():
    assert CodeMinifier.remove_comments("10 PRINT \"HI\":REM say hello") == "10 PRINT \"HI\""

def test_remove_comments_removes_inline_rem_with_spaces():
    assert CodeMinifier.remove_comments("10 PRINT \"HI\" : REM say hello") == "10 PRINT \"HI\""

def test_remove_comments_preserves_colon_that_is_not_rem():
    assert CodeMinifier.remove_comments("10 PRINT A:B=1") == "10 PRINT A:B=1"

def test_remove_comments_strips_inline_rem_but_keeps_earlier_statements():
    input_text = "10 PRINT A:B=1:REM note"
    assert CodeMinifier.remove_comments(input_text) == "10 PRINT A:B=1"

def test_remove_comments_does_not_strip_rem_inside_string():
    assert CodeMinifier.remove_comments("10 PRINT \":REM\"") == "10 PRINT \":REM\""

def test_remove_comments_redirects_goto_to_next_surviving_line():
    input_text = "10 GOTO 20\n20 REM label\n30 END"
    assert CodeMinifier.remove_comments(input_text) == "10 GOTO 30\n30 END"

def test_remove_comments_redirects_gosub_to_next_surviving_line():
    input_text = "10 GOSUB 20\n20 REM label\n30 PRINT A\n40 RETURN"
    assert CodeMinifier.remove_comments(input_text) == "10 GOSUB 30\n30 PRINT A\n40 RETURN"

def test_remove_comments_redirects_then_to_next_surviving_line():
    input_text = "10 IF X>5 THEN 20\n20 REM label\n30 PRINT A"
    assert CodeMinifier.remove_comments(input_text) == "10 IF X>5 THEN 30\n30 PRINT A"

def test_remove_comments_redirects_across_consecutive_rem_lines():
    input_text = "10 GOTO 20\n20 REM label1\n30 REM label2\n40 END"
    assert CodeMinifier.remove_comments(input_text) == "10 GOTO 40\n40 END"

def test_remove_comments_does_not_redirect_goto_to_existing_line():
    input_text = "10 GOTO 30\n20 REM comment\n30 END"
    assert CodeMinifier.remove_comments(input_text) == "10 GOTO 30\n30 END"

def test_remove_comments_redirect_works_with_subsequent_renumber():
    input_text = "600 REM label\n605 PRINT A\n840 IF C=0 GOTO 600"
    removed = CodeMinifier.remove_comments(input_text)
    renumbered = CodeMinifier.renumber_lines(removed)
    assert renumbered == "0 PRINT A\n1 IF C=0 GOTO 0"

# -- SimplifyNextStatements --

def test_simplify_next_statements_removes_single_variable():
    assert CodeMinifier.simplify_next_statements("10 NEXT I") == "10 NEXT"

def test_simplify_next_statements_removes_multiple_variables():
    assert CodeMinifier.simplify_next_statements("10 NEXT I,J") == "10 NEXT"

def test_simplify_next_statements_removes_string_variable():
    assert CodeMinifier.simplify_next_statements("10 NEXT A$") == "10 NEXT"

def test_simplify_next_statements_leaves_bare_next_alone():
    assert CodeMinifier.simplify_next_statements("10 NEXT") == "10 NEXT"

def test_simplify_next_statements_handles_next_in_compound_line():
    assert CodeMinifier.simplify_next_statements("10 NEXT I: PRINT A") == "10 NEXT: PRINT A"

def test_simplify_next_statements_does_not_touch_next_inside_string():
    input_text = "10 PRINT \"NEXT I\""
    assert CodeMinifier.simplify_next_statements(input_text) == input_text

# -- RenumberLines --

def test_renumber_lines_numbers_sequentially_from_0():
    input_text = "10 PRINT \"HI\"\n20 END"
    assert CodeMinifier.renumber_lines(input_text) == "0 PRINT \"HI\"\n1 END"

def test_renumber_lines_updates_goto_target():
    input_text = "100 GOTO 200\n200 END"
    assert CodeMinifier.renumber_lines(input_text) == "0 GOTO 1\n1 END"

def test_renumber_lines_updates_gosub_target():
    input_text = "10 GOSUB 100\n20 END\n100 PRINT A\n110 RETURN"
    assert CodeMinifier.renumber_lines(input_text) == "0 GOSUB 2\n1 END\n2 PRINT A\n3 RETURN"

def test_renumber_lines_updates_then_target():
    assert CodeMinifier.renumber_lines("10 IF X>5 THEN 20\n20 END\n30 PRINT \"YES\"") == "0 IF X>5 THEN 1\n1 END\n2 PRINT \"YES\""

def test_renumber_lines_updates_on_goto_targets():
    input_text = "10 ON X GOTO 100,200,300\n100 PRINT 1\n200 PRINT 2\n300 PRINT 3"
    assert CodeMinifier.renumber_lines(input_text) == "0 ON X GOTO 1,2,3\n1 PRINT 1\n2 PRINT 2\n3 PRINT 3"

def test_renumber_lines_removes_zero_padding():
    input_text = "0010 PRINT \"HI\"\n0020 END"
    assert CodeMinifier.renumber_lines(input_text) == "0 PRINT \"HI\"\n1 END"

def test_renumber_lines_skips_blank_lines():
    input_text = "10 PRINT A\n\n20 END"
    assert CodeMinifier.renumber_lines(input_text) == "0 PRINT A\n1 END"

# -- DATA statement protection --

def test_remove_whitespace_preserves_spaces_inside_data_statement():
    assert CodeMinifier.remove_whitespace("10 DATA 1, 2, 3") == "10DATA1, 2, 3"

def test_remove_whitespace_preserves_unquoted_string_spaces_in_data():
    assert CodeMinifier.remove_whitespace("10 DATA HELLO WORLD") == "10DATAHELLO WORLD"

def test_remove_whitespace_strips_code_before_data_but_not_data_itself():
    assert CodeMinifier.remove_whitespace("10 X = 1 : DATA 1, 2, 3") == "10X=1:DATA1, 2, 3"

def test_remove_whitespace_strips_all_spaces_immediately_after_data_keyword():
    assert CodeMinifier.remove_whitespace("10 DATA    1,2,3") == "10DATA1,2,3"

def test_remove_whitespace_is_idempotent_on_already_minified_data_statement():
    once_passed = CodeMinifier.remove_whitespace("10 DATA THIS IS A TEST,WITH SPACES")
    assert once_passed == "10DATATHIS IS A TEST,WITH SPACES"
    assert CodeMinifier.remove_whitespace(once_passed) == once_passed

def test_remove_whitespace_strips_space_before_quoted_data_item():
    assert CodeMinifier.remove_whitespace("10 DATA \"THIS IS A TEST\",\"WITH SPACES\"") == "10DATA\"THIS IS A TEST\",\"WITH SPACES\""

def test_remove_whitespace_recognizes_data_abbreviation():
    assert CodeMinifier.remove_whitespace("10 Da    1, 2, 3") == "10Da1, 2, 3"

def test_remove_whitespace_is_idempotent_on_already_minified_data_abbreviation():
    once_passed = CodeMinifier.remove_whitespace("10 Da THIS IS A TEST,WITH SPACES")
    assert once_passed == "10DaTHIS IS A TEST,WITH SPACES"
    assert CodeMinifier.remove_whitespace(once_passed) == once_passed

def test_replace_0_with_period_does_not_touch_data_statement():
    assert CodeMinifier.replace_0_with_period("10 DATA 0.5,0.25") == "10 DATA 0.5,0.25"

def test_use_scientific_notation_does_not_touch_data_statement():
    assert CodeMinifier.use_scientific_notation("10 DATA 10000,20000") == "10 DATA 10000,20000"

def test_simplify_next_statements_does_not_touch_data_statement():
    assert CodeMinifier.simplify_next_statements("10 DATA NEXT I,5") == "10 DATA NEXT I,5"

def test_remove_comments_does_not_strip_inline_rem_inside_data_statement():
    input_text = "10 DATA HELLO:REM WORLD"
    assert CodeMinifier.remove_comments(input_text) == input_text

def test_minify_does_not_minify_data_statements():
    input_text = "10 X = 0.5\n20 DATA 1, 2, 3\n30 NEXT I"
    result = CodeMinifier.minify(input_text,
        remove_whitespace=True,
        replace_0_with_period=True,
        use_scientific_notation=False,
        remove_comments=False,
        simplify_next_statements=True,
        renumber_lines=False)
    assert result == "10X=.5\n20DATA1, 2, 3\n30NEXT"

# -- Minify (orchestrator) --

def test_minify_applies_all_passes():
    input_text = "0010  REM header\n0020  X=0.5\n0030  NEXT I\n0040  GOTO 0020"
    result = CodeMinifier.minify(input_text,
        remove_whitespace=True,
        replace_0_with_period=True,
        use_scientific_notation=False,
        remove_comments=True,
        simplify_next_statements=True,
        renumber_lines=True)
    assert result == "0X=.5\n1NEXT\n2GOTO0"

def test_minify_no_passes_returns_same_content():
    input_text = "10 PRINT \"HI\"\n20 END"
    result = CodeMinifier.minify(input_text, False, False, False, False, False, False)
    assert result == input_text


# -- Prettifier Tests --

# -- AddWhitespace --

def test_add_whitespace_adds_space_after_line_number():
    assert CodePrettifier.add_whitespace("10PRINT\"HI\"") == "10 PRINT \"HI\""

def test_add_whitespace_spaces_keywords_in_compact_code():
    assert CodePrettifier.add_whitespace("10FORI=1TO10") == "10 FOR I = 1 TO 10"

def test_add_whitespace_preserves_leading_zeros_on_line_number():
    assert CodePrettifier.add_whitespace("0010PRINT\"HI\"") == "0010 PRINT \"HI\""

def test_add_whitespace_preserves_string_contents():
    assert CodePrettifier.add_whitespace("10PRINT\"FOR I=1 TO 10\"") == "10 PRINT \"FOR I=1 TO 10\""

def test_add_whitespace_function_keyword_no_space_before_paren():
    assert CodePrettifier.add_whitespace("10IFPEEK(49152)=1THEN20") == "10 IF PEEK(49152) = 1 THEN 20"

def test_add_whitespace_handles_conditional():
    assert CodePrettifier.add_whitespace("10IFX>5ANDX<10THEN30") == "10 IF X > 5 AND X < 10 THEN 30"

def test_add_whitespace_no_space_before_semicolon():
    assert CodePrettifier.add_whitespace("10PRINT;") == "10 PRINT;"

def test_add_whitespace_rem_content_copied_verbatim():
    assert CodePrettifier.add_whitespace("10REMFOOANDBAR") == "10 REM FOOANDBAR"

def test_add_whitespace_data_values_spacing_preserved():
    assert CodePrettifier.add_whitespace("10 DATA 0, 12, 68, 96") == "10 DATA 0, 12, 68, 96"

def test_add_whitespace_data_from_minified_has_one_space_before_values():
    assert CodePrettifier.add_whitespace("10DATA0,12,68") == "10 DATA 0,12,68"

def test_add_whitespace_data_space_before_comma_preserved():
    assert CodePrettifier.add_whitespace("10 DATA 56 , 120 , 124") == "10 DATA 56 , 120 , 124"

def test_add_whitespace_data_unquoted_string_spaces_preserved():
    assert CodePrettifier.add_whitespace("10 DATA THIS IS A TEST,WITH SPACES") == "10 DATA THIS IS A TEST,WITH SPACES"

def test_add_whitespace_data_string_literal_spaces_preserved():
    assert CodePrettifier.add_whitespace("10 DATA 1, \"HELLO WORLD\" ,2") == "10 DATA 1, \"HELLO WORLD\" ,2"

def test_add_whitespace_handles_compound_statement():
    assert CodePrettifier.add_whitespace("10PRINT\"A\":GOTO20") == "10 PRINT \"A\":GOTO 20"

def test_add_whitespace_multiple_lines():
    assert CodePrettifier.add_whitespace("10PRINT\"HI\"\n20END") == "10 PRINT \"HI\"\n20 END"

def test_add_whitespace_is_idempotent():
    once = CodePrettifier.add_whitespace("10FORI=1TO10:NEXTI")
    twice = CodePrettifier.add_whitespace(once)
    assert once == twice

def test_add_whitespace_already_spaced_line_unchanged():
    input_text = "10 PRINT \"HELLO\""
    assert CodePrettifier.add_whitespace(input_text) == input_text

# -- AddWhitespace: operator spacing --

@pytest.mark.parametrize("op", ["=", "+", "-", "*", "/", "^", "<", ">", "<>", "<=", ">="])
def test_add_whitespace_spaces_binary_operator(op):
    assert CodePrettifier.add_whitespace(f"10X{op}Y") == f"10 X {op} Y"

def test_add_whitespace_no_space_after_unary_minus_on_assignment():
    assert CodePrettifier.add_whitespace("10DY=-DY") == "10 DY = -DY"

def test_add_whitespace_no_space_after_unary_minus_in_parens():
    assert CodePrettifier.add_whitespace("10Y=SGN(-5)") == "10 Y = SGN(-5)"

def test_add_whitespace_no_space_after_unary_minus_after_comma():
    assert CodePrettifier.add_whitespace("10PRINTA,-B") == "10 PRINT A,-B"

def test_add_whitespace_spaces_binary_minus_between_operands():
    assert CodePrettifier.add_whitespace("10X=Y-5") == "10 X = Y - 5"

def test_add_whitespace_bouncing_ball_example():
    assert CodePrettifier.add_whitespace("10X=X+DX") == "10 X = X + DX"
    assert CodePrettifier.add_whitespace("10IFX>255THENX=255:DX=-DX") == "10 IF X > 255 THEN X = 255:DX = -DX"

# -- ReplacePeriodWithZero --

def test_replace_period_with_zero_replaces_leading_period():
    assert CodePrettifier.replace_period_with_zero("10 X=.5") == "10 X=0.5"

def test_replace_period_with_zero_does_not_affect_normal_decimal():
    assert CodePrettifier.replace_period_with_zero("10 X=10.5") == "10 X=10.5"

def test_replace_period_with_zero_replaces_multiple_occurrences():
    assert CodePrettifier.replace_period_with_zero("10 X=.5:Y=.1") == "10 X=0.5:Y=0.1"

def test_replace_period_with_zero_preserves_string_contents():
    assert CodePrettifier.replace_period_with_zero("10 PRINT \".5\"") == "10 PRINT \".5\""

def test_replace_period_with_zero_integer_unchanged():
    assert CodePrettifier.replace_period_with_zero("10 X=5") == "10 X=5"

# -- UseStandardNotation --

def test_use_standard_notation_expands_simple_e_notation():
    assert CodePrettifier.use_standard_notation("10 X=1E4") == "10 X=10000"

def test_use_standard_notation_expands_decimal_mantissa():
    assert CodePrettifier.use_standard_notation("10 X=1.5E3") == "10 X=1500"

def test_use_standard_notation_leaves_non_integer_result_unchanged():
    assert CodePrettifier.use_standard_notation("10 X=1.23E1") == "10 X=1.23E1"

def test_use_standard_notation_preserves_string_contents():
    assert CodePrettifier.use_standard_notation("10 PRINT \"1E4\"") == "10 PRINT \"1E4\""

def test_use_standard_notation_expands_multiple_numbers():
    assert CodePrettifier.use_standard_notation("10 X=2E4:Y=1E5") == "10 X=20000:Y=100000"

# -- AddNextVariables --

def test_add_next_variables_adds_variable_to_bare_next():
    input_text = "10 FOR I=1 TO 10\n20 NEXT"
    expected = "10 FOR I=1 TO 10\n20 NEXT I"
    assert CodePrettifier.add_next_variables(input_text) == expected

def test_add_next_variables_leaves_next_with_variable_unchanged():
    input_text = "10 FOR I=1 TO 10\n20 NEXT I"
    assert CodePrettifier.add_next_variables(input_text) == input_text

def test_add_next_variables_handles_nested_loops():
    input_text = "10 FOR I=1 TO 10\n20 FOR J=1 TO 10\n30 NEXT\n40 NEXT"
    expected = "10 FOR I=1 TO 10\n20 FOR J=1 TO 10\n30 NEXT J\n40 NEXT I"
    assert CodePrettifier.add_next_variables(input_text) == expected

def test_add_next_variables_handles_next_in_compound_line():
    input_text = "10 FOR I=1 TO 10:NEXT"
    expected = "10 FOR I=1 TO 10:NEXT I"
    assert CodePrettifier.add_next_variables(input_text) == expected

def test_add_next_variables_detects_for_without_space_after_keyword():
    input_text = "10 FORI=1 TO 10\n20 NEXT"
    expected = "10 FORI=1 TO 10\n20 NEXT I"
    assert CodePrettifier.add_next_variables(input_text) == expected

def test_add_next_variables_handles_minified_compound_line_with_for():
    input_text = "10 C=1:FORI=2 TO S\n20 NEXT"
    expected = "10 C=1:FORI=2 TO S\n20 NEXT I"
    assert CodePrettifier.add_next_variables(input_text) == expected

def test_add_next_variables_leaves_bare_next_with_empty_stack():
    input_text = "10 NEXT"
    assert CodePrettifier.add_next_variables(input_text) == input_text

def test_add_next_variables_does_not_modify_string_contents():
    input_text = "10 PRINT \"NEXT I\""
    assert CodePrettifier.add_next_variables(input_text) == input_text

def test_renumber_lines_updates_goto_immediately_after_variable_in_minified_code():
    input_text = "21 IFR%<=SGOTO24\n24 END"
    expected = "10 IFR%<=SGOTO 20\n20 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == expected

# -- RenumberLines --

def test_prettifier_renumber_lines_renumbers_with_increment():
    input_text = "1 PRINT \"HI\"\n2 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == "10 PRINT \"HI\"\n20 END"

def test_prettifier_renumber_lines_updates_goto_target():
    input_text = "100 GOTO 200\n200 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == "10 GOTO 20\n20 END"

def test_prettifier_renumber_lines_updates_gosub_target():
    input_text = "10 GOSUB 100\n20 END\n100 PRINT A\n110 RETURN"
    expected = "10 GOSUB 30\n20 END\n30 PRINT A\n40 RETURN"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == expected

def test_prettifier_renumber_lines_updates_then_target():
    input_text = "10 IF X THEN 100\n100 END"
    expected = "10 IF X THEN 20\n20 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == expected

def test_prettifier_renumber_lines_applies_padding_to_line_numbers():
    input_text = "10 PRINT \"HI\"\n20 END"
    expected = "0010 PRINT \"HI\"\n0020 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 4) == expected

def test_prettifier_renumber_lines_does_not_pad_line_references():
    input_text = "10 GOTO 20\n20 END"
    expected = "0010 GOTO 20\n0020 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 4) == expected

def test_prettifier_renumber_lines_skips_blank_lines():
    input_text = "10 PRINT A\n\n20 END"
    expected = "10 PRINT A\n20 END"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == expected

def test_prettifier_renumber_lines_updates_on_goto_targets():
    input_text = "10 ON X GOTO 100,200,300\n100 PRINT 1\n200 PRINT 2\n300 PRINT 3"
    expected = "10 ON X GOTO 20,30,40\n20 PRINT 1\n30 PRINT 2\n40 PRINT 3"
    assert CodePrettifier.renumber_lines(input_text, 10, 10, 0) == expected

# -- Prettify (orchestrator) --

def test_prettify_no_passes_returns_same_content():
    input_text = "10 FOR I=1 TO 10\n20 END"
    assert CodePrettifier.prettify(input_text, False, False, False, False, False) == input_text

def test_prettify_applies_all_passes():
    input_text = "1 FOR I=1 TO 5\n2 PRINT .5\n3 X=1E3\n4 NEXT\n5 GOTO 2"
    expected = "10 FOR I = 1 TO 5\n20 PRINT 0.5\n30 X = 1000\n40 NEXT I\n50 GOTO 20"
    result = CodePrettifier.prettify(input_text,
        add_whitespace=True, replace_period_with_zero=True, use_standard_notation=True,
        add_next_variables=True, renumber_lines=True,
        line_number_increment=10, line_number_padding=0)
    assert result == expected
