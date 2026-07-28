"""Plugin loader — discovers and manages plugins from the plugins/ directory."""

import os
import json
import logging
import subprocess
import sys
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

log = logging.getLogger("plugin-loader")

PLUGINS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "plugins")
SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class PluginCommand:
    name: str
    label: str
    description: str
    args: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Plugin:
    name: str
    version: str
    description: str
    category: str
    icon: str
    entry_point: str
    commands: List[PluginCommand] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def parse_output(stdout: str) -> dict:
    """Parse tagged output from CLI tools into structured data."""
    info = {
        "messages": [],
        "errors": [],
        "files": [],
        "prg_size": None,
        "load_address": None,
        "code_address": None,
    }

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("[OK]"):
            info["messages"].append({"type": "ok", "text": line[4:].strip()})
        elif line.startswith("[PRG]"):
            info["messages"].append({"type": "prg", "text": line[5:].strip()})
            m = re.search(r'\((\d+)\s*byte\)', line)
            if m:
                info["prg_size"] = int(m.group(1))
            m = re.search(r'(\S+\.(?:prg|bas|asm|lst))', line)
            if m:
                info["files"].append(m.group(1))
        elif line.startswith("[BASIC]"):
            info["messages"].append({"type": "basic", "text": line[7:].strip()})
            m = re.search(r'(\S+\.bas)', line)
            if m:
                info["files"].append(m.group(1))
        elif line.startswith("[ASM]"):
            info["messages"].append({"type": "asm", "text": line[5:].strip()})
            m = re.search(r'(\S+\.(?:asm|lst))', line)
            if m:
                info["files"].append(m.group(1))
        elif line.startswith("[LOAD]"):
            m = re.search(r'\$([0-9a-fA-F]{4})', line)
            if m:
                info["load_address"] = f"0x{m.group(1)}"
        elif line.startswith("[CODE]"):
            m = re.search(r'\$([0-9a-fA-F]{4})', line)
            if m:
                info["code_address"] = f"0x{m.group(1)}"
        elif line.startswith("[SIZE]"):
            m = re.search(r'(\d+)', line)
            if m:
                info["prg_size"] = int(m.group(1))
        elif line.startswith("[C64]"):
            info["messages"].append({"type": "c64", "text": line[5:].strip()})
        elif line.startswith("[LEXER ERROR]") or line.startswith("[PARSER ERROR]") or line.startswith("[ASM ERROR]"):
            info["errors"].append(line)
        elif line.startswith("[ERROR]"):
            info["errors"].append(line[7:].strip())
        else:
            info["messages"].append({"type": "info", "text": line})

    return info


class PluginLoader:
    def __init__(self, plugins_dir: str = PLUGINS_DIR):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Plugin] = {}

    def discover(self) -> Dict[str, Plugin]:
        self.plugins.clear()
        if not os.path.isdir(self.plugins_dir):
            log.warning(f"Plugins directory not found: {self.plugins_dir}")
            return self.plugins

        for entry in sorted(os.listdir(self.plugins_dir)):
            manifest_path = os.path.join(self.plugins_dir, entry, "plugin.json")
            if not os.path.isfile(manifest_path):
                continue
            try:
                plugin = self._load_manifest(manifest_path)
                self.plugins[plugin.name] = plugin
                log.info(f"Loaded plugin: {plugin.name} v{plugin.version} ({len(plugin.commands)} commands)")
            except Exception as e:
                log.error(f"Failed to load plugin from {manifest_path}: {e}")

        return self.plugins

    def _load_manifest(self, path: str) -> Plugin:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        commands = []
        for cmd_data in data.get("commands", []):
            commands.append(PluginCommand(
                name=cmd_data["name"],
                label=cmd_data.get("label", cmd_data["name"]),
                description=cmd_data.get("description", ""),
                args=cmd_data.get("args", []),
                options=cmd_data.get("options", {}),
            ))

        return Plugin(
            name=data["name"],
            version=data.get("version", "0.0.1"),
            description=data.get("description", ""),
            category=data.get("category", "other"),
            icon=data.get("icon", "🔧"),
            entry_point=data.get("entry_point", ""),
            commands=commands,
        )

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self.plugins.get(name)

    def list_plugins(self) -> List[dict]:
        return [p.to_dict() for p in self.plugins.values()]

    def exec_command(
        self,
        plugin_name: str,
        command_name: str,
        args: List[str] = None,
        options: Dict[str, Any] = None,
        cli_args: List[str] = None,
    ) -> dict:
        """Execute a plugin command.

        Args:
            plugin_name: Plugin identifier
            command_name: Command to execute
            args: Positional arguments (legacy, appended after command)
            options: Key-value options converted to --key value flags (legacy)
            cli_args: Full CLI argument list (overrides args/options when provided)
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {"success": False, "error": f"Plugin '{plugin_name}' not found"}

        cmd = None
        for c in plugin.commands:
            if c.name == command_name:
                cmd = c
                break
        if not cmd:
            return {"success": False, "error": f"Command '{command_name}' not found in plugin '{plugin_name}'"}

        # Build CLI command: python3 <entry_point> <command> <args...>
        full_args = [sys.executable, os.path.join(SDK_ROOT, plugin.entry_point)]

        if cli_args is not None:
            full_args.extend(cli_args)
        else:
            full_args.append(command_name)
            if args:
                full_args.extend(args)
            if options:
                for k, v in options.items():
                    if isinstance(v, bool):
                        if v:
                            full_args.append(f"--{k}")
                    elif v is not None:
                        full_args.extend([f"--{k}", str(v)])

        log.info(f"Executing: {' '.join(full_args)}")

        try:
            result = subprocess.run(
                full_args,
                capture_output=True,
                text=True,
                cwd=SDK_ROOT,
                timeout=60,
            )

            output = parse_output(result.stdout)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "output": output,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out (60s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton
_loader: Optional[PluginLoader] = None


def get_loader() -> PluginLoader:
    global _loader
    if _loader is None:
        _loader = PluginLoader()
        _loader.discover()
    return _loader


def reload() -> Dict[str, Plugin]:
    global _loader
    _loader = PluginLoader()
    return _loader.discover()
