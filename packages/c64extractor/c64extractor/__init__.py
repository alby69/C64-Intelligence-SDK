# c64extractor shared library

from pyc64c.formats.basic_tokens import detokenize_basic, is_basic_prg
from pyc64c.formats.prg import PRGFile

class C64Extractor:
    """Helper class to parse Commodore 64 files and extract contents."""
    @staticmethod
    def extract_prg(prg_data: bytes) -> dict:
        prg = PRGFile(prg_data)
        return {
            "load_address": prg.load_address(),
            "is_basic": prg.is_basic(),
            "basic_source": prg.to_basic() if prg.is_basic() else None,
            "hex_dump": prg.to_hex_dump()
        }
