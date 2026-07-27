import pytest
from readycode_py.tokenizer import BasicTokenizer, PrgConverter, BasicTokens

def tokenize(code: str) -> bytes:
    return BasicTokenizer().tokenize_line(code).tokens

# -- Keyword tokens --

def test_tokenize_line_for_keyword_is_tokenized():
    bytes_out = tokenize("FORI=1TO10")
    assert bytes_out[0] == 0x81

def test_tokenize_line_to_keyword_is_tokenized():
    bytes_out = tokenize("FORI=1TO10")
    # Expected: FOR(0x81) I(0x49) =(0xB2) 1(0x31) TO(0xA4) 1(0x31) 0(0x30)
    assert bytes_out[4] == 0xA4

def test_tokenize_line_for_loop_full_byte_sequence():
    bytes_out = tokenize("FORI=1TO5")
    expected = bytes([0x81, 0x49, 0xB2, 0x31, 0xA4, 0x35])
    assert bytes_out == expected

def test_tokenize_line_minified_code_has_no_space_bytes():
    minified = tokenize("FORI=1TO10")
    assert ord(' ') not in minified

def test_tokenize_line_spaced_code_preserves_space_bytes():
    spaced = tokenize("FOR I=1 TO 10")
    assert ord(' ') in spaced

def test_tokenize_line_print_keyword_is_tokenized():
    bytes_out = tokenize("PRINT\"HI\"")
    assert bytes_out[0] == 0x99

def test_tokenize_line_goto_keyword_is_tokenized():
    bytes_out = tokenize("GOTO10")
    assert bytes_out[0] == 0x89

def test_tokenize_line_if_then_keywords_are_tokenized():
    bytes_out = tokenize("IFX>5THEN10")
    assert bytes_out[0] == 0x8B
    assert 0xA7 in bytes_out

def test_tokenize_line_print_hash_takes_precedence_over_print():
    bytes_out = tokenize("PRINT#1,A")
    assert bytes_out[0] == 0x98

def test_tokenize_line_operators_are_tokenized():
    bytes_out = tokenize("X=A+B")
    assert 0xB2 in bytes_out
    assert 0xAA in bytes_out

# -- String literals --

def test_tokenize_line_keywords_inside_strings_not_tokenized():
    bytes_out = tokenize("PRINT\"FOR\"")
    assert bytes_out[0] == 0x99
    assert bytes_out[1] == ord('"')
    assert bytes_out[2] == ord('F')
    assert bytes_out[3] == ord('O')
    assert bytes_out[4] == ord('R')

# -- REM --

def test_tokenize_line_rem_tokenized_and_comment_copied_verbatim():
    bytes_out = tokenize("REM THIS IS A COMMENT")
    assert bytes_out[0] == 0x8F
    comment = bytes_out[1:].decode('ascii')
    assert "COMMENT" in comment.upper()

def test_tokenize_line_rem_preserves_exactly_one_leading_space():
    bytes_out = tokenize("REM LEGO BATMAN")
    comment = bytes_out[1:].decode('ascii')
    assert comment == " LEGO BATMAN"

def test_tokenize_line_rem_tokenize_is_idempotent():
    once = tokenize("REM LEGO BATMAN")
    once_text = "REM" + once[1:].decode('ascii')
    twice = tokenize(once_text)
    assert once == twice

# -- Keyword abbreviations --

def test_tokenize_line_list_abbreviation_is_tokenized():
    bytes_out = tokenize("Li")
    assert bytes_out[0] == 0x9B

def test_tokenize_line_three_letter_abbreviation_is_tokenized():
    bytes_out = tokenize("CLo1")
    assert bytes_out[0] == 0xA0

def test_tokenize_line_shorter_abbreviation_not_confused_with_longer_one():
    assert tokenize("St")[0] == 0x90
    assert tokenize("STe")[0] == 0xA9

def test_tokenize_line_abbreviation_inside_string_not_tokenized():
    bytes_out = tokenize("PRINT\"Li\"")
    assert bytes_out[2] == ord('L')
    assert bytes_out[3] == ord('i')

def test_tokenize_line_question_mark_is_print_synonym():
    bytes_out = tokenize("?\"HI\"")
    assert bytes_out[0] == 0x99


# -- PrgConverter Tests --

def test_convert_to_prg_starts_with_standard_load_address():
    prg = PrgConverter().convert_to_prg("10 PRINT \"HI\"")
    assert prg[0] == 0x01
    assert prg[1] == 0x08

def test_convert_to_prg_ends_with_zero_link_marker():
    prg = PrgConverter().convert_to_prg("10 PRINT \"HI\"")
    assert prg[-2] == 0x00
    assert prg[-1] == 0x00

def test_convert_to_prg_empty_source_returns_minimal_valid_prg():
    prg = PrgConverter().convert_to_prg("")
    assert prg == bytes([0x01, 0x08, 0x00, 0x00])

def test_convert_to_prg_line_number_only_no_code_produces_no_output_line():
    converter = PrgConverter()
    prg = converter.convert_to_prg("10\n20 PRINT \"HI\"")
    listing = converter.convert_from_prg(prg)
    assert "10 " not in listing
    assert "20 PRINT" in listing

@pytest.mark.parametrize("source", [
    "10 PRINT \"HELLO WORLD\"",
    "10 FOR I=1 TO 10\n20 PRINT I\n30 NEXT I",
    "10 IF X=1 THEN GOTO 30\n20 PRINT \"NO\"\n30 PRINT \"YES\""
])
def test_convert_to_prg_then_convert_from_prg_retokenizes_to_identical_bytes(source):
    converter = PrgConverter()
    prg = converter.convert_to_prg(source)
    listing = converter.convert_from_prg(prg)
    prg_again = converter.convert_to_prg(listing)
    assert prg == prg_again

def test_convert_from_prg_too_short_throws():
    with pytest.raises(ValueError):
        PrgConverter().convert_from_prg(bytes([0x01, 0x08]))

def test_convert_from_prg_includes_line_number_prefix():
    prg = PrgConverter().convert_to_prg("100 PRINT \"HI\"")
    listing = PrgConverter().convert_from_prg(prg)
    assert listing.startswith("100 ")

def test_convert_from_prg_keeps_string_literal_content_unexpanded():
    converter = PrgConverter()
    prg = converter.convert_to_prg("10 PRINT \"PRINT THIS\"")
    listing = converter.convert_from_prg(prg)
    assert "\"PRINT THIS\"" in listing

def test_is_basic_program_genuine_tokenized_program_returns_true():
    prg = PrgConverter().convert_to_prg("10 PRINT \"HI\"\n20 GOTO 10")
    assert PrgConverter().is_basic_program(prg) is True

def test_is_basic_program_empty_program_returns_true():
    prg = PrgConverter().convert_to_prg("")
    assert PrgConverter().is_basic_program(prg) is True

def test_is_basic_program_wrong_load_address_returns_false():
    data = bytes([0x00, 0x10, 0x00, 0x00])
    assert PrgConverter().is_basic_program(data) is False

def test_is_basic_program_machine_language_stub_returns_false():
    data = bytes([0x01, 0x08, 0xA9, 0x00, 0x8D, 0x20, 0xD0, 0x60])
    assert PrgConverter().is_basic_program(data) is False

def test_is_basic_program_truncated_program_returns_false():
    prg = PrgConverter().convert_to_prg("10 PRINT \"HI\"")
    truncated = prg[:-3]
    assert PrgConverter().is_basic_program(truncated) is False

def test_is_basic_program_too_short_returns_false():
    assert PrgConverter().is_basic_program(bytes([0x01])) is False
