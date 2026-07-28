"""Plugin loader — discovers and manages plugins from the plugins/ directory."""

import os
import json
import logging
import subprocess
import sys
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

    def exec_command(self, plugin_name: str, command_name: str, args: List[str] = None, options: Dict[str, Any] = None) -> dict:
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

        # Build CLI command
        cli_args = [sys.executable, os.path.join(SDK_ROOT, plugin.entry_point), command_name]
        if args:
            cli_args.extend(args)
        if options:
            for k, v in options.items():
                if isinstance(v, bool):
                    if v:
                        cli_args.append(f"--{k}")
                elif v is not None:
                    cli_args.extend([f"--{k}", str(v)])

        log.info(f"Executing: {' '.join(cli_args)}")

        try:
            result = subprocess.run(
                cli_args,
                capture_output=True,
                text=True,
                cwd=SDK_ROOT,
                timeout=60,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
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
