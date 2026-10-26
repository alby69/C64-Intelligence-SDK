"""
mcp/acme_server.py - ACME Cross-Assembler MCP Server with Standardized JSON Error Output.

Provides ACME cross-assembler compilation and linting capabilities,
returning standardized error logs conforming to the error schema:
{
    "file": "...",
    "line": N,
    "column": M,
    "error_type": "...",
    "message": "...",
    "suggestion": "..."
}
"""

import os
import re
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional

try:
    from core.utils.acme_linter import ACMELinter
except ImportError:
    ACMELinter = None


class ACMEMCPServer:
    """
    MCP Server for ACME (6502) cross-assembler and linter.
    """

    def __init__(self, acme_bin: str = "acme"):
        self.acme_bin = acme_bin
        self.linter = ACMELinter() if ACMELinter else None

    def parse_errors(self, output: str, fallback_filename: str = "main.asm") -> List[Dict[str, Any]]:
        """
        Parses ACME output stdout/stderr into standardized JSON error objects.
        """
        errors: List[Dict[str, Any]] = []
        lines = output.splitlines()

        # ACME CLI output patterns:
        # Error - File main.asm, line 12 (Zone default): Mnemonic or directive unknown.
        # Warning - File main.asm, line 15: Symbol 'foo' not defined.
        pattern = re.compile(
            r"^\s*(?P<type>Error|Warning)\s*-\s*File\s+(?P<file>[^,]+),\s+line\s+(?P<line>\d+)(?:\s+\([^)]+\))?:\s*(?P<msg>.+)$",
            re.IGNORECASE
        )

        seen = set()

        for line in lines:
            m = pattern.match(line)
            if m:
                filename = os.path.basename(m.group("file").strip())
                line_num = int(m.group("line"))
                err_type = m.group("type").capitalize()
                msg = m.group("msg").strip()

                key = (filename, line_num, 0, msg)
                if key not in seen:
                    seen.add(key)
                    errors.append({
                        "file": filename,
                        "line": line_num,
                        "column": 0,
                        "error_type": err_type,
                        "message": msg,
                        "suggestion": self._generate_suggestion(msg, err_type)
                    })
            elif "error" in line.lower() or "warning" in line.lower():
                # Generic fallback if line contains error/warning details
                err_type = "Error" if "error" in line.lower() else "Warning"
                msg_part = line.strip()

                # Search for line number inside string if present
                line_match = re.search(r"line\s+(\d+)", line, re.IGNORECASE)
                line_num = int(line_match.group(1)) if line_match else 0

                key = (fallback_filename, line_num, 0, msg_part)
                if key not in seen:
                    seen.add(key)
                    errors.append({
                        "file": fallback_filename,
                        "line": line_num,
                        "column": 0,
                        "error_type": err_type,
                        "message": msg_part,
                        "suggestion": self._generate_suggestion(msg_part, err_type)
                    })

        return errors

    def _generate_suggestion(self, message: str, error_type: str) -> str:
        """Generates AI-assisted suggestions based on common ACME error messages."""
        msg_lower = message.lower()

        if "mnemonic" in msg_lower or "directive unknown" in msg_lower:
            return "Check 6502 opcode syntax or ACME pseudo-directives (!byte, !word, !zone, !to, !src)."
        elif "label" in msg_lower and "duplicat" in msg_lower:
            return "Rename duplicate label or isolate scope using '!zone <zone_name>'."
        elif "not defined" in msg_lower or "symbol" in msg_lower:
            return "Ensure label or variable is declared or included via '!src'."
        elif "out of range" in msg_lower or "branch" in msg_lower:
            return "Branch destination target is beyond -128/+127 byte limit. Use JMP for distant targets."
        elif "zone" in msg_lower:
            return "Check zone opening/closing syntax."
        else:
            return f"Review ACME 6502 assembly source around '{message[:40]}'."

    def lint_code(self, source_code: str, filename: str = "main.asm") -> List[Dict[str, Any]]:
        """
        Uses ACMELinter static analysis to check source code for errors.
        """
        if not self.linter:
            return []

        raw_errors = self.linter.lint(source_code)
        parsed_errors: List[Dict[str, Any]] = []

        for e in raw_errors:
            msg = e.get("message", "")
            severity = e.get("severity", "error").capitalize()
            line_num = e.get("line", 0)

            parsed_errors.append({
                "file": filename,
                "line": line_num,
                "column": 0,
                "error_type": severity,
                "message": msg,
                "suggestion": self._generate_suggestion(msg, severity)
            })

        return parsed_errors

    def compile_file(self, filepath: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles an ACME assembly file using acme binary if available, or fallback linting.
        """
        filename = os.path.basename(filepath)
        if not os.path.exists(filepath):
            return {
                "success": False,
                "returncode": -1,
                "output_file": None,
                "errors": [{
                    "file": filename,
                    "line": 0,
                    "column": 0,
                    "error_type": "FileNotFoundError",
                    "message": f"Source file '{filepath}' does not exist.",
                    "suggestion": "Check file path passed to ACME compiler."
                }],
                "raw_output": ""
            }

        out_prg = output_path or (os.path.splitext(filepath)[0] + ".prg")
        cmd = [self.acme_bin, "-o", out_prg, filepath]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            raw_out = res.stdout + "\n" + res.stderr
            parsed_errors = self.parse_errors(raw_out, fallback_filename=filename)

            success = (res.returncode == 0) and len([e for e in parsed_errors if e["error_type"] == "Error"]) == 0

            return {
                "success": success,
                "returncode": res.returncode,
                "output_file": out_prg if success else None,
                "errors": parsed_errors,
                "raw_output": raw_out
            }
        except FileNotFoundError:
            # ACME binary not found on PATH - fallback to static lint analysis
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()

            lint_errors = self.lint_code(code, filename=filename)
            has_errors = any(e["error_type"] == "Error" for e in lint_errors)

            return {
                "success": not has_errors,
                "returncode": 1 if has_errors else 0,
                "output_file": None,
                "errors": lint_errors,
                "raw_output": f"ACME binary '{self.acme_bin}' not found; executed fallback static linter."
            }
        except Exception as ex:
            return {
                "success": False,
                "returncode": -1,
                "output_file": None,
                "errors": [{
                    "file": filename,
                    "line": 0,
                    "column": 0,
                    "error_type": "ExecutionError",
                    "message": str(ex),
                    "suggestion": "Verify system environment and ACME executable installation."
                }],
                "raw_output": str(ex)
            }

    def compile_code(self, source_code: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles ACME source code directly from string input.
        """
        with tempfile.NamedTemporaryFile(suffix=".asm", mode="w", delete=False) as tmp:
            tmp.write(source_code)
            tmp_path = tmp.name

        try:
            return self.compile_file(tmp_path, output_path=output_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    import sys
    server = ACMEMCPServer()
    if len(sys.argv) > 1:
        res = server.compile_file(sys.argv[1])
        print(json.dumps(res, indent=2))
    else:
        print("ACME MCP Server initialized.")
