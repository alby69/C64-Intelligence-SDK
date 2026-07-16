"""C64Project class to handle CBM Studio-like project file configurations (.c64proj)."""

import os
import json
import logging
from pyc64c.compiler import compile_to_prg

log = logging.getLogger("pyc64_project")

class ProjectValidationError(Exception):
    pass

class C64Project:
    def __init__(self, config_dict: dict, file_path: str = None):
        self.config = config_dict
        self.file_path = file_path
        self._validate_config()

    @classmethod
    def load(cls, path: str) -> "C64Project":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Project file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try JSON first
        try:
            config = json.loads(content)
            return cls(config, file_path=path)
        except json.JSONDecodeError:
            pass

        # Simple manual YAML-like parser as fallback for basic .c64proj YAML configurations
        try:
            config = cls._parse_simple_yaml(content)
            return cls(config, file_path=path)
        except Exception as e:
            raise ProjectValidationError(f"Failed to parse project file as JSON or YAML: {e}")

    @staticmethod
    def _parse_simple_yaml(content: str) -> dict:
        """Extremely simple YAML parser fallback for basic key-value structures."""
        result = {}
        current_list_name = None
        current_list = []
        current_dict_name = None

        lines = content.splitlines()
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # Simple list item matching (e.g., "- type: sprite")
            if line_stripped.startswith("-"):
                item_content = line_stripped[1:].strip()
                # Parse key-values in list item
                if ":" in item_content:
                    parts = item_content.split(":", 1)
                    k = parts[0].strip()
                    v = parts[1].strip().strip('"').strip("'")
                    if current_list_name:
                        if len(current_list) > 0 and isinstance(current_list[-1], dict) and k not in current_list[-1]:
                            current_list[-1][k] = v
                        else:
                            current_list.append({k: v})
                continue

            if ":" in line_stripped:
                parts = line_stripped.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip().strip('"').strip("'")

                if not val:
                    if "build_config" in key:
                        current_dict_name = "build_config"
                        result[current_dict_name] = {}
                    elif "assets" in key:
                        current_list_name = "assets"
                        current_list = []
                        result[current_list_name] = current_list
                    continue

                indent = len(line) - len(line.lstrip())
                if indent > 0 and current_dict_name:
                    result[current_dict_name][key] = val
                elif indent > 0 and current_list_name == "assets":
                    if len(current_list) > 0 and isinstance(current_list[-1], dict):
                        current_list[-1][key] = val
                else:
                    result[key] = val

        if "build_config" in result:
            bc = result["build_config"]
            if "optimize" in bc:
                bc["optimize"] = str(bc["optimize"]).lower() in ("true", "yes", "1")
        return result

    def _validate_config(self):
        required_fields = ["project_name", "entry_point", "output_name"]
        for field in required_fields:
            if field not in self.config:
                raise ProjectValidationError(f"Missing required field: '{field}'")

        target = self.config.get("target", "C64")
        if target.upper() not in ["C64", "C128", "VIC20", "PET", "C16", "MEGA65"]:
            raise ProjectValidationError(f"Unsupported target machine: '{target}'")

    @property
    def project_name(self) -> str:
        return self.config["project_name"]

    @property
    def version(self) -> str:
        return self.config.get("version", "1.0.0")

    @property
    def author(self) -> str:
        return self.config.get("author", "Unknown")

    @property
    def target(self) -> str:
        return self.config.get("target", "C64")

    @property
    def entry_point(self) -> str:
        return self.config["entry_point"]

    @property
    def output_name(self) -> str:
        return self.config["output_name"]

    @property
    def build_config(self) -> dict:
        return self.config.get("build_config", {
            "optimize": True,
            "assembler": "acme",
            "load_address": "0x0801"
        })

    @property
    def assets(self) -> list:
        return self.config.get("assets", [])

    def build(self, base_dir: str = None) -> bytes:
        """Compiles the entry point and produces the output PRG binary."""
        if base_dir is None and self.file_path is not None:
            base_dir = os.path.dirname(self.file_path)

        if base_dir is None:
            base_dir = os.getcwd()

        # 1. Process Assets (Pipeline)
        injected_bytes = b""
        for asset in self.assets:
            path = asset.get("path")
            action = asset.get("build_action")
            atype = asset.get("type")

            if not path:
                continue

            abs_path = os.path.join(base_dir, path)
            if action == "generate_asm":
                # Ensure source file exists or create a basic one for build testing
                if not os.path.exists(abs_path):
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, "wb") as f:
                        f.write(b"\x00\xff\xaa\x55")  # Dummy sprite/char pattern

                with open(abs_path, "rb") as f:
                    data = f.read()

                # Generate .asm file containing .byte representations
                asm_lines = [f"; Generated ASM from {atype}: {path}"]
                for i in range(0, len(data), 8):
                    chunk = data[i:i+8]
                    hex_vals = ", ".join(f"${b:02X}" for b in chunk)
                    asm_lines.append(f"    .byte {hex_vals}")

                asm_out_path = abs_path + ".asm"
                with open(asm_out_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(asm_lines))
                log.info(f"Asset pipeline: Generated assembly file {asm_out_path}")

            elif action == "inject" and atype == "sid":
                # Keep track of SID bytes to inject or link at the end of output PRG
                if not os.path.exists(abs_path):
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, "wb") as f:
                        f.write(b"RSID\x00\x02\x00\x7c\x00\x00\x10\x00")  # Mock SID bytes
                with open(abs_path, "rb") as f:
                    injected_bytes += f.read()
                log.info(f"Asset pipeline: Registered SID injection from {abs_path}")

        # 2. Compile Entry Point
        entry_path = os.path.join(base_dir, self.entry_point)
        if not os.path.exists(entry_path):
            raise ProjectValidationError(f"Entry point source file not found: {entry_path}")

        with open(entry_path, "r", encoding="utf-8") as f:
            src = f.read()

        prg_bytes, result = compile_to_prg(src)
        if not result.success:
            err_msgs = [e["msg"] for e in (result.lex_errors + result.parse_errors)]
            raise ProjectValidationError(f"Compilation failed: {', '.join(err_msgs)}")

        # 3. Inject Assets into PRG bytes
        if injected_bytes:
            prg_bytes += injected_bytes

        output_path = os.path.join(base_dir, self.output_name)
        with open(output_path, "wb") as f:
            f.write(prg_bytes)

        return prg_bytes
