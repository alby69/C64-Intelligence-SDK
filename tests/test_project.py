import os
import tempfile
import pytest
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyc64_project import C64Project, ProjectValidationError

def test_project_init_and_properties():
    config = {
        "project_name": "TestGame",
        "version": "1.2.3",
        "author": "C64Dev",
        "target": "C128",
        "entry_point": "src/main.c64",
        "output_name": "game.prg",
        "build_config": {
            "optimize": True,
            "assembler": "kick",
            "load_address": "0x1000"
        },
        "assets": [
            {"type": "sprite", "path": "assets/hero.spr"}
        ]
    }
    project = C64Project(config)
    assert project.project_name == "TestGame"
    assert project.version == "1.2.3"
    assert project.author == "C64Dev"
    assert project.target == "C128"
    assert project.entry_point == "src/main.c64"
    assert project.output_name == "game.prg"
    assert project.build_config["optimize"] is True
    assert project.assets[0]["type"] == "sprite"

def test_project_validation_missing_fields():
    config = {
        "project_name": "TestGame",
        "entry_point": "src/main.c64"
        # missing output_name
    }
    with pytest.raises(ProjectValidationError) as excinfo:
        C64Project(config)
    assert "Missing required field: 'output_name'" in str(excinfo.value)

def test_project_validation_invalid_target():
    config = {
        "project_name": "TestGame",
        "entry_point": "src/main.c64",
        "output_name": "game.prg",
        "target": "GameBoy" # unsupported
    }
    with pytest.raises(ProjectValidationError) as excinfo:
        C64Project(config)
    assert "Unsupported target machine: 'GameBoy'" in str(excinfo.value)

def test_project_load_and_build():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple .c64 source file
        source_content = "def main() -> byte:\n    poke(53280, 2)\n    return 0"
        src_dir = os.path.join(tmpdir, "src")
        os.makedirs(src_dir)
        entry_path = os.path.join(src_dir, "main.c64")
        with open(entry_path, "w", encoding="utf-8") as f:
            f.write(source_content)

        # Create a project configuration JSON
        project_config = {
            "project_name": "MySimpleGame",
            "entry_point": "src/main.c64",
            "output_name": "game.prg",
            "target": "C64"
        }
        import json
        proj_path = os.path.join(tmpdir, "game.c64proj")
        with open(proj_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(project_config))

        # Load and Build
        project = C64Project.load(proj_path)
        assert project.project_name == "MySimpleGame"

        prg_bytes = project.build()
        assert prg_bytes is not None
        assert len(prg_bytes) > 2 # Load address + some bytes

        # Check that output PRG file exists
        out_path = os.path.join(tmpdir, "game.prg")
        assert os.path.exists(out_path)

def test_project_load_simple_yaml():
    yaml_content = """# C64 Project Config
project_name: AwesomeGame
version: 2.0.0
entry_point: src/hero.c64
output_name: hero.prg
target: VIC20
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_path = os.path.join(tmpdir, "game.c64proj")
        with open(proj_path, "w", encoding="utf-8") as f:
            f.write(yaml_content)

        project = C64Project.load(proj_path)
        assert project.project_name == "AwesomeGame"
        assert project.version == "2.0.0"
        assert project.entry_point == "src/hero.c64"
        assert project.output_name == "hero.prg"
        assert project.target == "VIC20"
