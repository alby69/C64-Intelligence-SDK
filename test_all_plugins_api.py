#!/usr/bin/env python3
"""Comprehensive API test for all 10 C64 Intelligence SDK plugins."""

import json
import os
import sys
import tempfile
import urllib.request
import urllib.error

BASE = os.environ.get("API_BASE", "http://localhost:8000")
SDK_ROOT = os.path.dirname(os.path.abspath(__file__))

results = []
pass_count = 0
fail_count = 0


def api_post(path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()) if e.read() else {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def api_get(path):
    url = f"{BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()) if e.read() else {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def record(plugin, command, status, data, note=""):
    global pass_count, fail_count
    ok = status == 200 and data.get("success", False)
    if ok:
        pass_count += 1
    else:
        fail_count += 1
    stdout = data.get("stdout", data.get("error", "")) or ""
    preview = stdout[:300].replace("\n", "\\n")
    results.append(
        {
            "plugin": plugin,
            "command": command,
            "http_status": status,
            "success": data.get("success", False),
            "preview": preview,
            "note": note,
        }
    )
    tag = "PASS" if ok else "FAIL"
    print(
        f"  [{tag}] {plugin}/{command} -> HTTP {status}, success={data.get('success', False)}"
    )
    if note:
        print(f"        Note: {note}")
    if not ok and preview:
        print(f"        Output: {preview[:200]}")


def test_knowledge():
    print("\n=== 1. KNOWLEDGE ===")
    # search
    _, _ = api_post(
        "/api/v1/plugins/knowledge/exec",
        {
            "command": "search",
            "args": ["sprite"],
            "options": {"max_results": 5},
            "cli_args": ["search", "sprite"],
        },
    )
    status, data = api_post(
        "/api/v1/plugins/knowledge/exec",
        {"command": "search", "cli_args": ["search", "sprite"]},
    )
    record("knowledge", "search", status, data)

    # docs
    status, data = api_post(
        "/api/v1/plugins/knowledge/exec",
        {"command": "docs", "cli_args": ["docs", "sprite"]},
    )
    record("knowledge", "docs", status, data)

    # status
    status, data = api_post(
        "/api/v1/plugins/knowledge/exec", {"command": "status", "cli_args": ["status"]}
    )
    record("knowledge", "status", status, data)

    # list-api
    status, data = api_post(
        "/api/v1/plugins/knowledge/exec",
        {"command": "list-api", "cli_args": ["list-api"]},
    )
    record("knowledge", "list-api", status, data)

    # list-files
    status, data = api_post(
        "/api/v1/plugins/knowledge/exec",
        {"command": "list-files", "cli_args": ["list-files"]},
    )
    record("knowledge", "list-files", status, data)


def test_debugger():
    print("\n=== 2. DEBUGGER ===")
    # status (no VICE connected - expected to fail gracefully)
    status, data = api_post(
        "/api/v1/plugins/debugger/exec", {"command": "status", "cli_args": ["status"]}
    )
    record("debugger", "status", status, data, note="Expected: no VICE connected")

    # attach (will fail without VICE)
    status, data = api_post(
        "/api/v1/plugins/debugger/exec", {"command": "attach", "cli_args": ["attach"]}
    )
    record("debugger", "attach", status, data, note="Expected: VICE not available")


def test_disk_tools():
    print("\n=== 3. DISK-TOOLS ===")
    tmpdir = tempfile.gettempdir()
    d64_path = os.path.join(tmpdir, "c64intel_test.d64").replace("\\", "/")

    # create
    status, data = api_post(
        "/api/v1/plugins/disk-tools/exec",
        {
            "command": "create",
            "cli_args": ["create", "MYDISK", "-o", d64_path, "--label", "MYDISK"],
        },
    )
    record("disk-tools", "create", status, data)

    # list on valid d64
    if os.path.exists(d64_path):
        status, data = api_post(
            "/api/v1/plugins/disk-tools/exec",
            {"command": "list", "cli_args": ["list", d64_path]},
        )
        record("disk-tools", "list", status, data)

    # list on nonexistent file
    status, data = api_post(
        "/api/v1/plugins/disk-tools/exec",
        {"command": "list", "cli_args": ["list", "/nonexistent/test.d64"]},
    )
    record(
        "disk-tools", "list-nonexistent", status, data, note="Expected: file not found"
    )


def test_emulator():
    print("\n=== 4. EMULATOR ===")
    # status (just info)
    status, data = api_post(
        "/api/v1/plugins/emulator/exec",
        {"command": "vice-info", "cli_args": ["vice-info"]},
    )
    record("emulator", "vice-info", status, data)

    # run with --prg - try the test .prg file if available
    prg_path = os.path.join(SDK_ROOT, "test_python.prg")
    if not os.path.exists(prg_path):
        prg_path = os.path.join(SDK_ROOT, "examples", "color_cycle.c64")
    status, data = api_post(
        "/api/v1/plugins/emulator/exec",
        {"command": "run", "cli_args": ["run", prg_path, "--timeout", "5"]},
    )
    record("emulator", "run", status, data, note="May time out or fail gracefully")


def test_compiler():
    print("\n=== 5. COMPILER ===")
    # create a test .c64 file
    test_c64 = os.path.join(tempfile.gettempdir(), "c64intel_test.c64").replace(
        "\\", "/"
    )
    with open(test_c64, "w") as f:
        f.write("""
def main() -> byte:
    poke(53280, 0)
    print("HELLO FROM API TEST")
    return 0
""")

    # compile
    status, data = api_post(
        "/api/v1/plugins/compiler/exec",
        {"command": "compile", "cli_args": ["compile", test_c64]},
    )
    record("compiler", "compile", status, data)

    # basic
    status, data = api_post(
        "/api/v1/plugins/compiler/exec",
        {"command": "basic", "cli_args": ["basic", test_c64]},
    )
    record("compiler", "basic", status, data)


def test_editor():
    print("\n=== 6. EDITOR ===")
    tmpdir = tempfile.gettempdir()

    # Create test BASIC source
    bas_src = os.path.join(tmpdir, "c64intel_test.bas").replace("\\", "/")
    with open(bas_src, "w") as f:
        f.write('10 print "hello"\n20 goto 10\n')
    prg_out = os.path.join(tmpdir, "c64intel_test_out.prg").replace("\\", "/")
    bas_out = os.path.join(tmpdir, "c64intel_test_detoken.bas").replace("\\", "/")
    min_out = os.path.join(tmpdir, "c64intel_test_min.bas").replace("\\", "/")
    prett_out = os.path.join(tmpdir, "c64intel_test_pretty.bas").replace("\\", "/")

    # tokenize
    status, data = api_post(
        "/api/v1/plugins/editor/exec",
        {"command": "tokenize", "cli_args": ["tokenize", bas_src, "--output", prg_out]},
    )
    record("editor", "tokenize", status, data)

    # detokenize
    status, data = api_post(
        "/api/v1/plugins/editor/exec",
        {
            "command": "detokenize",
            "cli_args": ["detokenize", prg_out, "--output", bas_out],
        },
    )
    record("editor", "detokenize", status, data)

    # minify
    status, data = api_post(
        "/api/v1/plugins/editor/exec",
        {"command": "minify", "cli_args": ["minify", bas_src, "--output", min_out]},
    )
    record("editor", "minify", status, data)

    # prettify
    status, data = api_post(
        "/api/v1/plugins/editor/exec",
        {
            "command": "prettify",
            "cli_args": ["prettify", bas_src, "--output", prett_out],
        },
    )
    record("editor", "prettify", status, data)


def test_geckos():
    print("\n=== 7. GECKOS ===")
    # status
    status, data = api_post(
        "/api/v1/plugins/geckos/exec", {"command": "status", "cli_args": ["status"]}
    )
    record("geckos", "status", status, data)

    # build (may fail without make/assembler)
    status, data = api_post(
        "/api/v1/plugins/geckos/exec", {"command": "build", "cli_args": ["build"]}
    )
    record(
        "geckos",
        "build",
        status,
        data,
        note="Expected: may fail without assembler tools",
    )

    # run
    status, data = api_post(
        "/api/v1/plugins/geckos/exec", {"command": "run", "cli_args": ["run"]}
    )
    record("geckos", "run", status, data, note="Expected: will try to launch VICE")


def test_ai_agent():
    print("\n=== 8. AI-AGENT ===")
    # status
    status, data = api_post(
        "/api/v1/plugins/ai-agent/exec", {"command": "status", "cli_args": ["status"]}
    )
    record("ai-agent", "status", status, data)

    # search
    status, data = api_post(
        "/api/v1/plugins/ai-agent/exec",
        {"command": "search", "cli_args": ["search", "sprite"]},
    )
    record("ai-agent", "search", status, data)

    # generate
    status, data = api_post(
        "/api/v1/plugins/ai-agent/exec",
        {"command": "generate", "cli_args": ["generate", "print hello world"]},
    )
    record(
        "ai-agent", "generate", status, data, note="Expected: may fail without AI model"
    )

    # explain
    test_code = os.path.join(tempfile.gettempdir(), "c64intel_explain.c64").replace(
        "\\", "/"
    )
    with open(test_code, "w") as f:
        f.write("def main() -> byte:\n    poke(53280, 5)\n    return 0\n")
    status, data = api_post(
        "/api/v1/plugins/ai-agent/exec",
        {"command": "explain", "cli_args": ["explain", test_code]},
    )
    record(
        "ai-agent", "explain", status, data, note="Expected: may fail without AI model"
    )


def test_project_manager():
    print("\n=== 9. PROJECT-MANAGER ===")
    # create a temp .c64proj file
    proj_path = os.path.join(tempfile.gettempdir(), "c64intel_test.c64proj").replace(
        "\\", "/"
    )
    # Create a minimal valid .c64 source for the project entry point
    proj_src_dir = tempfile.gettempdir()
    entry_path = os.path.join(proj_src_dir, "main.c64").replace("\\", "/")
    with open(entry_path, "w") as f:
        f.write('def main() -> byte:\n    print("hello")\n    return 0\n')

    with open(proj_path, "w") as f:
        json.dump(
            {
                "project_name": "TestProject",
                "version": "1.0",
                "entry_point": "main.c64",
                "output_name": "test_output.prg",
                "assets": [],
            },
            f,
        )

    # load
    status, data = api_post(
        "/api/v1/plugins/project-manager/exec",
        {"command": "load", "cli_args": ["load", proj_path]},
    )
    record("project-manager", "load", status, data)

    # build
    status, data = api_post(
        "/api/v1/plugins/project-manager/exec",
        {"command": "build", "cli_args": ["build", proj_path]},
    )
    record("project-manager", "build", status, data)


def test_tutorial():
    print("\n=== 10. TUTORIAL ===")
    # list
    status, data = api_post(
        "/api/v1/plugins/tutorial/exec", {"command": "list", "cli_args": ["list"]}
    )
    record("tutorial", "list", status, data)

    # show
    status, data = api_post(
        "/api/v1/plugins/tutorial/exec",
        {"command": "show", "cli_args": ["show", "cap01"]},
    )
    record("tutorial", "show", status, data)

    # search
    status, data = api_post(
        "/api/v1/plugins/tutorial/exec",
        {"command": "search", "cli_args": ["search", "sprite"]},
    )
    record("tutorial", "search", status, data)


def print_report():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE API TEST REPORT")
    print("=" * 80)
    print(
        f"\nTotal: {pass_count + fail_count} tests | PASS: {pass_count} | FAIL: {fail_count}"
    )
    print()
    print(f"{'Plugin':20s} {'Command':20s} {'HTTP':6s} {'Success':8s} {'Notes'}")
    print("-" * 80)
    for r in results:
        tag = "OK" if r["http_status"] == 200 and r["success"] else "FAIL"
        http = str(r["http_status"]) if r["http_status"] else "ERR"
        suc = str(r["success"])
        note = r["note"] or ""
        preview = r["preview"][:60]
        print(f"{r['plugin']:20s} {r['command']:20s} {http:6s} {suc:8s} {note}")
        if tag == "FAIL" and preview:
            print(f"{'':20s} {'':20s} {'':6s} {'':8s} >> {preview}")
    print("=" * 80)
    if fail_count == 0:
        print("RESULT: ALL TESTS PASSED")
    else:
        print(f"RESULT: {fail_count} TEST(S) FAILED (expected failures noted)")
    print("=" * 80)


if __name__ == "__main__":
    # First check server is up
    try:
        s, d = api_get("/")
        print(f"Server status: {d}")
    except Exception as e:
        print(f"ERROR: Server not reachable at {BASE}: {e}")
        sys.exit(1)

    test_knowledge()
    test_debugger()
    test_disk_tools()
    test_emulator()
    test_compiler()
    test_editor()
    test_geckos()
    test_ai_agent()
    test_project_manager()
    test_tutorial()

    print_report()

    # Cleanup temp files
    for f in [
        "c64intel_test.d64",
        "c64intel_test.c64",
        "c64intel_test_out.prg",
        "c64intel_test_detoken.bas",
        "c64intel_test_min.bas",
        "c64intel_test_pretty.bas",
        "c64intel_test.c64proj",
        "c64intel_explain.c64",
    ]:
        p = os.path.join(tempfile.gettempdir(), f)
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass
