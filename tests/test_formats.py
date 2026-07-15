import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyc64c.formats.basic_tokens import (
    detokenize_basic,
    is_basic_prg,
    hex_dump,
    BASIC_TOKENS,
)
from pyc64c.formats.d64 import D64Image
from pyc64c.formats.g64 import G64Error, G64Image
from pyc64c.formats.prg import PRGFile

BASIC_PRG = b"\x01\x08\x0c\x08\x0a\x00\x99\x22\x48\x45\x4c\x4c\x4f\x22\x00\x00\x00"


class TestBasicTokens:
    def test_basic_tokens_dict_not_empty(self):
        assert len(BASIC_TOKENS) > 0

    def test_detokenize_returns_string(self):
        result = detokenize_basic(BASIC_PRG)
        assert isinstance(result, str)

    def test_is_basic_prg_true(self):
        assert is_basic_prg(BASIC_PRG)

    def test_is_basic_prg_false_too_short(self):
        assert not is_basic_prg(b"\x00")

    def test_is_basic_prg_false_all_zeroes(self):
        assert not is_basic_prg(b"\x00" * 10)

    def test_hex_dump(self):
        dump = hex_dump(b"\x00\x01\x02ABCDEFGH\x03\x04\x05")
        assert len(dump) > 0


class TestPRGFile:
    def test_load_address(self):
        prg = PRGFile(BASIC_PRG)
        assert prg.load_address() == 0x0801

    def test_is_basic(self):
        prg = PRGFile(BASIC_PRG)
        assert prg.is_basic()

    def test_to_basic(self):
        prg = PRGFile(BASIC_PRG)
        src = prg.to_basic()
        assert "10" in src
        assert "PRINT" in src

    def test_to_hex_dump(self):
        prg = PRGFile(BASIC_PRG)
        dump = prg.to_hex_dump()
        assert "$0801" in dump

    def test_extract_creates_files(self):
        prg = PRGFile(BASIC_PRG)
        with tempfile.TemporaryDirectory() as tmp:
            results = prg.extract(tmp)
            assert len(results) >= 1
            assert all(os.path.exists(r) for r in results)

    def test_load_classmethod(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.prg")
            with open(path, "wb") as f:
                f.write(BASIC_PRG)
            prg = PRGFile.load(path)
            assert prg.load_address() == 0x0801


class TestD64Image:
    def test_list_files_empty_image(self):
        data = b"\x00" * 174848
        img = D64Image(data)
        files = img.list_files()
        assert isinstance(files, list)

    def test_load_classmethod_raises_on_missing(self):
        with pytest.raises(FileNotFoundError):
            D64Image.load("/tmp/nonexistent.d64")


class TestG64Image:
    def test_load_classmethod_raises_on_missing(self):
        with pytest.raises(FileNotFoundError):
            G64Image.load("/tmp/nonexistent.g64")
