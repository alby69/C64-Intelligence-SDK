"""
mcp/kickass_server.py - KickAssembler MCP Server with Standardized JSON Error Output.

Provides KickAssembler compilation capabilities and error output parsing
conforming to the standardized error schema:
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

KICKASS_JAR_DEFAULT = os.path.join("tutorial", "tools", "KickAss.jar")

class KickAssMCPServer:
    """
    MCP Server for KickAssembler cross-compilation.
    Executes KickAssembler and returns standardized JSON results.
    """

    def __init__(self, jar_path: Optional[str] = None, java_bin: str = "java"):
        self.jar_path = jar_path or os.getenv("KICKASS_JAR_PATH", KICKASS_JAR_DEFAULT)
        self.java_bin = java_bin

    def parse_errors(self, output: str, fallback_filename: str = "main.asm") -> List[Dict[str, Any]]:
        """
        Parses KickAssembler stdout/stderr log into standardized error objects.
        """
        errors: List[Dict[str, Any]] = []
        lines = output.splitlines()

        # Format 1:  (/path/to/file.asm 10:15) Error: Unknown symbol 'FOO'
        pattern1 = re.compile(
            r"^\s*\((?P<file>.+?)\s+(?P<line>\d+):(?P<column>\d+)\)\s+(?P<type>Error|Warning|SyntaxError):\s+(?P<msg>.+)$",
            re.IGNORECASE
        )

        # Format 2:
        # Error: Unknown symbol 'INVALID_MNEMONIC'
        # at line 1, column 18 in test_err.asm
        pattern2_msg = re.compile(r"^\s*(?P<type>Error|Warning|SyntaxError):\s+(?P<msg>.+)$", re.IGNORECASE)
        pattern2_loc = re.compile(r"^\s*at line\s+(?P<line>\d+),\s+column\s+(?P<column>\d+)\s+in\s+(?P<file>.+)$", re.IGNORECASE)

        seen = set()

        i = 0
        while i < len(lines):
            line = lines[i]

            m1 = pattern1.match(line)
            if m1:
                filename = os.path.basename(m1.group("file").strip())
                err_type = m1.group("type").capitalize()
                msg = m1.group("msg").strip()
                line_num = int(m1.group("line"))
                col_num = int(m1.group("column"))

                key = (filename, line_num, col_num, msg)
                if key not in seen:
                    seen.add(key)
                    errors.append({
                        "file": filename,
                        "line": line_num,
                        "column": col_num,
                        "error_type": err_type,
                        "message": msg,
                        "suggestion": self._generate_suggestion(msg, err_type)
                    })
                i += 1
                continue

            m2_msg = pattern2_msg.match(line)
            if m2_msg and i + 1 < len(lines):
                next_line = lines[i + 1]
                m2_loc = pattern2_loc.match(next_line)
                if m2_loc:
                    filename = os.path.basename(m2_loc.group("file").strip())
                    err_type = m2_msg.group("type").capitalize()
                    msg = m2_msg.group("msg").strip()
                    line_num = int(m2_loc.group("line"))
                    col_num = int(m2_loc.group("column"))

                    key = (filename, line_num, col_num, msg)
                    if key not in seen:
                        seen.add(key)
                        errors.append({
                            "file": filename,
                            "line": line_num,
                            "column": col_num,
                            "error_type": err_type,
                            "message": msg,
                            "suggestion": self._generate_suggestion(msg, err_type)
                        })
                    i += 2
                    continue

            i += 1

        # Fallback if errors were reported in output summary but regexes didn't capture line/col details
        if not errors and ("Got " in output and "errors" in output):
            for line in lines:
                if "Error:" in line or "Warning:" in line:
                    err_type = "Error" if "Error:" in line else "Warning"
                    msg_part = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                    key = (fallback_filename, 0, 0, msg_part)
                    if key not in seen:
                        seen.add(key)
                        errors.append({
                            "file": fallback_filename,
                            "line": 0,
                            "column": 0,
                            "error_type": err_type,
                            "message": msg_part,
                            "suggestion": self._generate_suggestion(msg_part, err_type)
                        })

        return errors

    def _generate_suggestion(self, message: str, error_type: str) -> str:
        """Generates AI-assisted suggestions based on common KickAssembler error messages."""
        msg_lower = message.lower()

        if "unknown symbol" in msg_lower or "symbol not found" in msg_lower:
            return "Verify symbol spelling, check label definition, or ensure required source files are imported."
        elif "pseudo command" in msg_lower and "not defined" in msg_lower:
            return "Check pseudo command spelling (e.g., .pc, .var, .const, .byte, .fill, .import)."
        elif "memory" in msg_lower or "overlap" in msg_lower:
            return "Adjust '.pc = $xxxx' memory placement directives to resolve address space collision."
        elif "duplicate" in msg_lower or "already defined" in msg_lower:
            return "Rename the duplicate label/variable or isolate it inside a local scope/zone."
        elif "syntax" in msg_lower or "unexpected" in msg_lower:
            return "Check line syntax against KickAssembler specification (e.g., matching brackets/quotes)."
        else:
            return f"Review line syntax against KickAssembler directives for '{message[:40]}'."

    def compile_file(self, filepath: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles a KickAssembler file and returns a structured JSON result.
        """
        if not os.path.exists(filepath):
            return {
                "success": False,
                "returncode": -1,
                "output_file": None,
                "errors": [{
                    "file": os.path.basename(filepath),
                    "line": 0,
                    "column": 0,
                    "error_type": "FileNotFoundError",
                    "message": f"Source file '{filepath}' does not exist.",
                    "suggestion": "Check file path passed to KickAssembler compiler."
                }],
                "raw_output": ""
            }

        out_dir = os.path.dirname(os.path.abspath(output_path)) if output_path else os.path.dirname(os.path.abspath(filepath))
        cmd = [self.java_bin, "-jar", self.jar_path, "-odir", out_dir]
        if output_path:
            cmd.extend(["-o", output_path])
        cmd.append(filepath)

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            raw_out = res.stdout + "\n" + res.stderr
            parsed_errors = self.parse_errors(raw_out, fallback_filename=os.path.basename(filepath))

            success = (res.returncode == 0) and len([e for e in parsed_errors if e["error_type"] == "Error"]) == 0

            target_prg = output_path
            if success and not target_prg:
                base, _ = os.path.splitext(filepath)
                target_prg = base + ".prg"

            return {
                "success": success,
                "returncode": res.returncode,
                "output_file": target_prg if success else None,
                "errors": parsed_errors,
                "raw_output": raw_out
            }
        except Exception as ex:
            return {
                "success": False,
                "returncode": -1,
                "output_file": None,
                "errors": [{
                    "file": os.path.basename(filepath),
                    "line": 0,
                    "column": 0,
                    "error_type": "ExecutionError",
                    "message": str(ex),
                    "suggestion": "Ensure Java runtime and KickAss.jar path are correctly configured."
                }],
                "raw_output": str(ex)
            }

    def compile_code(self, source_code: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles KickAssembler source code directly from string input.
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
    server = KickAssMCPServer()
    if len(sys.argv) > 1:
        res = server.compile_file(sys.argv[1])
        print(json.dumps(res, indent=2))
    else:
        print("KickAss MCP Server initialized.")
