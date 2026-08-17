"""Integration tests for the C64 Intelligence plugin system."""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "core_service"))

from plugin_loader import PluginLoader, parse_output, PLUGINS_DIR, SDK_ROOT


class TestPluginDiscovery:
    def test_discover_plugins(self):
        loader = PluginLoader()
        plugins = loader.discover()
        assert len(plugins) > 0, "No plugins discovered"

    def test_all_expected_plugins_loaded(self):
        loader = PluginLoader()
        plugins = loader.discover()
        expected = ["compiler", "disk-tools", "editor", "emulator", "project-manager",
                     "ai-agent", "debugger", "knowledge", "tutorial", "geckos", "game-dev"]
        for name in expected:
            assert name in plugins, f"Plugin '{name}' not found"

    def test_plugin_metadata(self):
        loader = PluginLoader()
        plugins = loader.discover()
        for name, plugin in plugins.items():
            assert plugin.name == name
            assert plugin.version
            assert plugin.description
            assert plugin.category
            assert plugin.icon
            assert plugin.entry_point

    def test_plugin_commands_not_empty(self):
        loader = PluginLoader()
        plugins = loader.discover()
        for name, plugin in plugins.items():
            assert len(plugin.commands) > 0, f"Plugin '{name}' has no commands"

    def test_plugin_to_dict(self):
        loader = PluginLoader()
        plugins = loader.discover()
        for name, plugin in plugins.items():
            d = plugin.to_dict()
            assert isinstance(d, dict)
            assert d["name"] == name
            assert "commands" in d


class TestPluginExecution:
    def test_compiler_compile(self):
        loader = PluginLoader()
        loader.discover()
        result = loader.exec_command("compiler", "compile", ["nonexistent.c64"])
        assert not result["success"]

    def test_plugin_not_found(self):
        loader = PluginLoader()
        loader.discover()
        result = loader.exec_command("nonexistent", "cmd")
        assert not result["success"]
        assert "not found" in result["error"]

    def test_command_not_found(self):
        loader = PluginLoader()
        loader.discover()
        result = loader.exec_command("compiler", "nonexistent")
        assert not result["success"]
        assert "not found" in result["error"]

    def test_exec_with_cli_args(self):
        loader = PluginLoader()
        loader.discover()
        result = loader.exec_command(
            "compiler", "compile", cli_args=["--help"]
        )
        assert result["success"] or "returncode" in result


class TestParseOutput:
    def test_parse_ok_messages(self):
        output = "[OK] File saved\n[BASIC] output.bas\n[PRG] output.prg (100 byte)"
        parsed = parse_output(output)
        assert len(parsed["messages"]) >= 2
        assert parsed["prg_size"] == 100

    def test_parse_errors(self):
        output = "[LEXER ERROR] unexpected token (3:5)\n[PARSER ERROR] missing colon"
        parsed = parse_output(output)
        assert len(parsed["errors"]) == 2

    def test_parse_load_address(self):
        output = "[LOAD]   $0801\n[CODE]   $1000"
        parsed = parse_output(output)
        assert parsed["load_address"] == "0x0801"
        assert parsed["code_address"] == "0x1000"

    def test_parse_empty(self):
        parsed = parse_output("")
        assert parsed["messages"] == []
        assert parsed["errors"] == []
        assert parsed["prg_size"] is None

    def test_parse_mixed(self):
        output = "[BUILD] Compiling...\n[OK] Done\n[ERROR] Something failed"
        parsed = parse_output(output)
        assert len(parsed["messages"]) == 2
        assert len(parsed["errors"]) == 1

    def test_parse_c64_messages(self):
        output = "[C64]    Starting c64py emulator...\n[C64]    Running..."
        parsed = parse_output(output)
        assert len(parsed["messages"]) == 2
        assert parsed["messages"][0]["type"] == "c64"

    def test_parse_file_paths(self):
        output = "[BASIC] output.bas\n[PRG] output.prg (50 byte)\n[ASM] output.asm"
        parsed = parse_output(output)
        assert "output.bas" in parsed["files"]
        assert "output.prg" in parsed["files"]
        assert "output.asm" in parsed["files"]


class TestSDKRoot:
    def test_sdk_root_exists(self):
        assert os.path.isdir(SDK_ROOT)

    def test_plugins_dir_exists(self):
        assert os.path.isdir(PLUGINS_DIR)

    def test_run_c64_exists(self):
        assert os.path.isfile(os.path.join(SDK_ROOT, "run_c64.py"))

    def test_pyc64_project_exists(self):
        assert os.path.isfile(os.path.join(SDK_ROOT, "pyc64_project.py"))
