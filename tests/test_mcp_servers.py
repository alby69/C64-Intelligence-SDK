"""
tests/test_mcp_servers.py - Unit tests for KickAss and ACME MCP servers.
Verifies compilation error parsing and standardized JSON schema output.
"""

import os
import pytest
from mcp.kickass_server import KickAssMCPServer
from mcp.acme_server import ACMEMCPServer


def test_kickass_parse_errors_format1():
    server = KickAssMCPServer()
    raw_output = """
Output dir: /tmp/test
parsing
Got 2 errors and 0 warnings while executing:
  (/path/to/main.asm 12:5) Error: Unknown symbol 'MY_VAR'
  (/path/to/main.asm 20:1) Warning: Unused label 'UNUSED_LBL'
"""
    errors = server.parse_errors(raw_output, fallback_filename="main.asm")

    assert len(errors) == 2

    e0 = errors[0]
    assert e0["file"] == "main.asm"
    assert e0["line"] == 12
    assert e0["column"] == 5
    assert e0["error_type"] == "Error"
    assert e0["message"] == "Unknown symbol 'MY_VAR'"
    assert "symbol" in e0["suggestion"].lower() or "label" in e0["suggestion"].lower()

    e1 = errors[1]
    assert e1["file"] == "main.asm"
    assert e1["line"] == 20
    assert e1["column"] == 1
    assert e1["error_type"] == "Warning"
    assert e1["message"] == "Unused label 'UNUSED_LBL'"


def test_kickass_parse_errors_format2():
    server = KickAssMCPServer()
    raw_output = """
Error: Pseudo command 'foo' not defined
at line 5, column 10 in test.asm
"""
    errors = server.parse_errors(raw_output, fallback_filename="test.asm")

    assert len(errors) == 1
    err = errors[0]
    assert err["file"] == "test.asm"
    assert err["line"] == 5
    assert err["column"] == 10
    assert err["error_type"] == "Error"
    assert err["message"] == "Pseudo command 'foo' not defined"
    assert "pseudo command" in err["suggestion"].lower()


def test_kickass_compile_code_invalid():
    server = KickAssMCPServer()
    invalid_code = "INVALID_COMMAND 12345"
    result = server.compile_code(invalid_code)

    assert result["success"] is False
    assert isinstance(result["errors"], list)
    assert len(result["errors"]) > 0

    err = result["errors"][0]
    for key in ["file", "line", "column", "error_type", "message", "suggestion"]:
        assert key in err


def test_kickass_compile_code_valid():
    server = KickAssMCPServer()
    valid_code = """
.pc = $0801
:BasicUpstart(main)
.pc = $0810
main:
    lda #$01
    sta $d020
    rts
"""
    result = server.compile_code(valid_code)
    assert result["success"] is True
    assert len(result["errors"]) == 0


def test_acme_parse_errors():
    server = ACMEMCPServer()
    raw_output = """
Error - File test_code.asm, line 14 (Zone default): Mnemonic or directive unknown.
Warning - File test_code.asm, line 22: Label 'foo' not defined.
"""
    errors = server.parse_errors(raw_output, fallback_filename="test_code.asm")

    assert len(errors) == 2

    e0 = errors[0]
    assert e0["file"] == "test_code.asm"
    assert e0["line"] == 14
    assert e0["column"] == 0
    assert e0["error_type"] == "Error"
    assert e0["message"] == "Mnemonic or directive unknown."
    assert "opcode" in e0["suggestion"].lower() or "mnemonic" in e0["suggestion"].lower() or "directive" in e0["suggestion"].lower()

    e1 = errors[1]
    assert e1["file"] == "test_code.asm"
    assert e1["line"] == 22
    assert e1["column"] == 0
    assert e1["error_type"] == "Warning"
    assert e1["message"] == "Label 'foo' not defined."


def test_acme_compile_code_invalid():
    server = ACMEMCPServer()
    invalid_code = """
lbl1:
    lda #$00
lbl1:
    INVALID_OPCODE $10
"""
    result = server.compile_code(invalid_code)

    assert result["success"] is False
    assert isinstance(result["errors"], list)
    assert len(result["errors"]) > 0

    for err in result["errors"]:
        for key in ["file", "line", "column", "error_type", "message", "suggestion"]:
            assert key in err


def test_acme_compile_code_valid():
    server = ACMEMCPServer()
    valid_code = """
* = $0801
    !byte $0c, $08, $0a, $00, $9e, $20, $32, $30, $36, $34, $00, $00, $00
* = $0810
main:
    lda #$01
    sta $d020
    rts
"""
    result = server.compile_code(valid_code)
    assert result["success"] is True
    assert len([e for e in result["errors"] if e["error_type"] == "Error"]) == 0
