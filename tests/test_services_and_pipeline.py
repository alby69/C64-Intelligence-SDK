import os
import tempfile
import json
import pytest
from fastapi.testclient import TestClient

# Core Service Imports
from services.core_service.main import app as core_app
from services.core_service.plugins import MockBuildTool, MockDebugger, BuildResult

# KB-Agent Imports
from services.kb_agent.main import app as kb_app

# Compiler Service Imports
from services.compiler_service.main import app as compiler_app

# Project Imports
from pyc64_project import C64Project, ProjectValidationError

def test_mock_plugins():
    # Test MockBuildTool
    bt = MockBuildTool()
    assert bt.name == "mock-compiler"
    res = bt.compile("10 PRINT", {})
    assert res.success is True
    assert res.prg_bytes.startswith(b"\x01\x08")
    assert len(res.errors) == 0

    # Test MockDebugger
    dbg = MockDebugger()
    assert dbg.connect("localhost", 6510) is True
    assert dbg.set_breakpoint(0x1000) is True
    step_info = dbg.step()
    assert step_info["pc"] == 0x0810

def test_core_service_rest():
    client = TestClient(core_app)
    # Test root endpoint
    res = client.get("/")
    assert res.status_code == 200
    assert "running" in res.json()["status"]

    # Test Compile success
    compile_payload = {
        "source_code": "def main() -> byte:\n    return 0",
        "compiler": "c64py",
        "optimize": True,
        "load_address": "0x0801"
    }
    res = client.post("/api/v1/compile", json=compile_payload)
    assert res.status_code == 200
    resp_json = res.json()
    assert resp_json["success"] is True
    assert resp_json["prg_base64"] is not None
    assert resp_json["size_bytes"] > 0

    # Test Compile error (guaranteed syntax error)
    invalid_payload = {
        "source_code": "def main() -> byte:\n    invalid syntax!!!",
        "compiler": "c64py"
    }
    res = client.post("/api/v1/compile", json=invalid_payload)
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert len(res.json()["errors"]) > 0

def test_compiler_service_rest():
    client = TestClient(compiler_app)
    # Test root endpoint
    res = client.get("/")
    assert res.status_code == 200
    assert "running" in res.json()["status"]

    # Test Compile success
    compile_payload = {
        "source_code": "def main() -> byte:\n    return 0",
        "compiler": "c64py"
    }
    res = client.post("/api/v1/compile", json=compile_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_kb_agent_service():
    client = TestClient(kb_app)
    # Test root
    res = client.get("/")
    assert res.status_code == 200
    assert "running" in res.json()["status"]

    # Test indexing
    index_payload = {
        "title": "Custom Sprite Multi-color",
        "content": "To enable multicolor sprites on Commodore 64, set the register $D01C to 255. Background and custom sprite colors are set in $D025 and $D026.",
        "category": "video"
    }
    res = client.post("/kb/index", json=index_payload)
    assert res.status_code == 200
    assert res.json()["success"] is True
    doc_id = res.json()["document_id"]

    # Test search
    search_payload = {
        "query": "multicolor sprite",
        "limit": 3
    }
    res = client.post("/kb/search", json=search_payload)
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) > 0
    assert results[0]["id"] == doc_id or "sprite" in results[0]["content"].lower()

    # Test C64 registers resolution
    res = client.get("/kb/registers/$D020")
    assert res.status_code == 200
    assert res.json()["resolved"] is True
    assert res.json()["details"]["name"] == "VIC-II Border Color"

    # Test decimal address
    res = client.get("/kb/registers/53281")
    assert res.status_code == 200
    assert res.json()["resolved"] is True
    assert res.json()["details"]["name"] == "VIC-II Background Color"

    # Test unregistered address
    res = client.get("/kb/registers/4000")
    assert res.status_code == 200
    assert res.json()["resolved"] is False

def test_c64project_asset_pipeline():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple .c64 source file
        source_content = "def main() -> byte:\n    return 0"
        src_dir = os.path.join(tmpdir, "src")
        os.makedirs(src_dir)
        entry_path = os.path.join(src_dir, "main.c64")
        with open(entry_path, "w", encoding="utf-8") as f:
            f.write(source_content)

        # Asset folder and dummy sprite binary
        asset_dir = os.path.join(tmpdir, "assets")
        os.makedirs(asset_dir)
        sprite_bin_path = os.path.join(asset_dir, "player.spr")
        with open(sprite_bin_path, "wb") as f:
            f.write(b"\x12\x34\x56\x78")

        # Project config with assets
        config = {
            "project_name": "GameWithAssets",
            "entry_point": "src/main.c64",
            "output_name": "game_assets.prg",
            "target": "C64",
            "assets": [
                {
                    "type": "sprite",
                    "path": "assets/player.spr",
                    "build_action": "generate_asm"
                },
                {
                    "type": "sid",
                    "path": "assets/music.sid",
                    "build_action": "inject"
                }
            ]
        }

        # Save and load project
        proj_file = os.path.join(tmpdir, "test.c64proj")
        with open(proj_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(config))

        project = C64Project.load(proj_file)
        assert len(project.assets) == 2

        # Build project - triggers asset pipeline
        prg_bytes = project.build()
        assert prg_bytes is not None

        # Check generate_asm created the corresponding .asm file
        asm_path = os.path.join(asset_dir, "player.spr.asm")
        assert os.path.exists(asm_path)
        with open(asm_path, "r", encoding="utf-8") as f:
            asm_content = f.read()
            assert "Generated ASM" in asm_content
            assert ".byte" in asm_content

        # Check inject action created dummy music.sid and injected its bytes at the end
        sid_path = os.path.join(asset_dir, "music.sid")
        assert os.path.exists(sid_path)
        with open(sid_path, "rb") as f:
            sid_bytes = f.read()
            # The prg_bytes must contain the compiled entry point bytes + injected sid bytes at the end
            assert prg_bytes.endswith(sid_bytes)
