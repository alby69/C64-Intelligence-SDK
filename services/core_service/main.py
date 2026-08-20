import asyncio
import base64
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_project_root = str(Path(__file__).resolve().parent.parent.parent)
_core_service = str(Path(__file__).resolve().parent)
for p in [_project_root, _core_service]:
    if p not in sys.path:
        sys.path.insert(0, p)

from pyc64c.compiler import compile_to_prg
from plugin_loader import get_loader, reload as reload_plugins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core-service")

app = FastAPI(
    title="C64 Intelligence Core Service",
    description="Backend API and LSP for the C64 Intelligence Studio",
    version="1.0.0",
)

# Allow CORS for Vite dev server and Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST Models
class CompileRequest(BaseModel):
    source_code: str
    compiler: str = "c64py"
    optimize: bool = True
    load_address: str = "0x0801"


class CompileResponse(BaseModel):
    success: bool
    prg_base64: Optional[str] = None
    load_address: int
    size_bytes: int
    errors: List[str] = []


@app.get("/")
def read_root():
    return {"status": "running", "service": "C64 Intelligence Core Service"}


@app.post("/api/v1/compile", response_model=CompileResponse)
def compile_code(req: CompileRequest):
    try:
        try:
            load_addr = (
                int(req.load_address, 16)
                if req.load_address.startswith("0x")
                else int(req.load_address)
            )
        except ValueError:
            load_addr = 0x0801

        prg_bytes, result = compile_to_prg(req.source_code)

        if result.success:
            prg_b64 = base64.b64encode(prg_bytes).decode("utf-8")
            return CompileResponse(
                success=True,
                prg_base64=prg_b64,
                load_address=load_addr,
                size_bytes=len(prg_bytes),
                errors=[],
            )
        else:
            errors_list = []
            for err in result.lex_errors + result.parse_errors:
                msg = err.get("msg", str(err))
                line = err.get("line", "?")
                errors_list.append(f"Line {line}: {msg}")

            return CompileResponse(
                success=False,
                prg_base64=None,
                load_address=load_addr,
                size_bytes=0,
                errors=errors_list,
            )
    except Exception as e:
        logger.exception("Compilation failed with exception")
        raise HTTPException(status_code=500, detail=str(e))


# LSP WebSocket Endpoint
@app.websocket("/ws/lsp")
async def websocket_lsp(websocket: WebSocket):
    await websocket.accept()
    logger.info("LSP WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                method = msg.get("method")
                msg_id = msg.get("id")

                if (
                    method == "textDocument/didChange"
                    or method == "textDocument/didOpen"
                ):
                    params = msg.get("params", {})
                    text_document = params.get("textDocument", {})
                    uri = text_document.get("uri", "file:///src/main.c64")

                    content = ""
                    if "contentChanges" in params and len(params["contentChanges"]) > 0:
                        content = params["contentChanges"][0].get("text", "")
                    else:
                        content = text_document.get("text", "")

                    diagnostics = []
                    if content:
                        _, result = compile_to_prg(content)
                        if not result.success:
                            for err in result.lex_errors + result.parse_errors:
                                line = err.get("line", 1) - 1
                                if line < 0:
                                    line = 0
                                diagnostics.append(
                                    {
                                        "range": {
                                            "start": {"line": line, "character": 0},
                                            "end": {"line": line, "character": 80},
                                        },
                                        "severity": 1,
                                        "message": err.get("msg", "Syntax error"),
                                    }
                                )

                    resp = {
                        "jsonrpc": "2.0",
                        "method": "textDocument/publishDiagnostics",
                        "params": {"uri": uri, "diagnostics": diagnostics},
                    }
                    await websocket.send_text(json.dumps(resp))

                elif msg_id is not None:
                    resp = {"jsonrpc": "2.0", "id": msg_id, "result": "processed"}
                    await websocket.send_text(json.dumps(resp))
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "error": {"code": -32700, "message": "Parse error"},
                            "id": None,
                        }
                    )
                )
            except Exception as e:
                logger.error(f"Error processing LSP message: {e}")
    except WebSocketDisconnect:
        logger.info("LSP WebSocket disconnected")


# AI Copilot WebSocket Endpoint
@app.websocket("/ws/ai-copilot")
async def websocket_ai_copilot(websocket: WebSocket):
    await websocket.accept()
    logger.info("AI Copilot WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                prompt = msg.get("prompt", "")
                prompt_lower = prompt.lower()

                if any(w in prompt_lower for w in ["print", "10 print"]):
                    tokens = [
                        "# Routine di output\n",
                        "def main() -> byte:\n",
                        "    poke(53280, 0)\n",
                        "    poke(53281, 0)\n",
                        '    print("HELLO WORLD!")\n',
                        "    return 0\n",
                    ]
                else:
                    tokens = [
                        f"# Suggerito per: {prompt}\n",
                        "def main() -> byte:\n",
                        "    poke(53280, 0)\n",
                        "    poke(53281, 0)\n",
                        "    return 0\n",
                    ]

                for token in tokens:
                    await websocket.send_text(
                        json.dumps({"token": token, "done": False})
                    )
                    await asyncio.sleep(0.03)

                await websocket.send_text(json.dumps({"token": "", "done": True}))

            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"error": "Invalid JSON", "done": True})
                )
            except Exception as e:
                logger.error(f"AI Copilot WebSocket error: {e}")
                await websocket.send_text(json.dumps({"error": str(e), "done": True}))
    except WebSocketDisconnect:
        logger.info("AI Copilot WebSocket disconnected")


# ── Acquisition Proxy API ──

class ScrapeRequest(BaseModel):
    url: Optional[str] = None
    spider_name: Optional[str] = "generic"

@app.post("/api/v1/acquisition/scrape")
def acquisition_scrape(req: ScrapeRequest):
    try:
        from core.pipeline.acquisition.scrapy_client import ScrapyClient
        client = ScrapyClient()
        if req.url:
            return client.scrape_url(req.url, spider_name=req.spider_name or "generic")
        else:
            return client.run_spider(req.spider_name or "generic")
    except Exception as e:
        logger.error(f"Acquisition scrape error: {e}")
        return {"status": "failed", "error": str(e)}

@app.get("/api/v1/acquisition/status/{job_id}")
def acquisition_job_status(job_id: str):
    try:
        from core.pipeline.acquisition.scrapy_client import ScrapyClient
        client = ScrapyClient()
        return client.get_job_status(job_id)
    except Exception as e:
        logger.error(f"Acquisition job status error: {e}")
        return {"status": "unknown", "job_id": job_id, "error": str(e)}


# ── Disk Browser API ──

class DiskCreateRequest(BaseModel):
    path: str
    format: str = "d64"
    label: str = "UNTITLED"


@app.get("/api/v1/disk/list")
def disk_list(path: str):
    loader = get_loader()
    result = loader.exec_command("disk-tools", "list", cli_args=["list", path])
    return result


@app.post("/api/v1/disk/create")
def disk_create(req: DiskCreateRequest):
    loader = get_loader()
    result = loader.exec_command(
        "disk-tools",
        "create",
        cli_args=["create", req.label, "-o", req.path, "--format", req.format],
    )
    return result


# ── Plugin API ──

class PluginExecRequest(BaseModel):
    command: str
    args: List[str] = []
    options: Dict[str, Any] = {}
    cli_args: Optional[List[str]] = None


@app.get("/api/v1/plugins")
def list_plugins():
    loader = get_loader()
    return {"plugins": loader.list_plugins()}


@app.post("/api/v1/plugins/reload")
def reload_all_plugins():
    plugins = reload_plugins()
    return {"plugins": [p.to_dict() for p in plugins.values()]}


@app.get("/api/v1/plugins/{plugin_name}")
def get_plugin(plugin_name: str):
    loader = get_loader()
    plugin = loader.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")
    return plugin.to_dict()


# ── Settings API ──

SETTINGS_DIR = Path(__file__).resolve().parent.parent.parent / "config"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def _load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_settings(data: dict):
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


@app.get("/api/v1/settings")
def get_settings():
    return _load_settings()


class SettingsUpdate(BaseModel):
    key: str
    value: Any


@app.put("/api/v1/settings")
def update_settings(req: SettingsUpdate):
    settings = _load_settings()
    settings[req.key] = req.value
    _save_settings(settings)
    return {"ok": True, "key": req.key, "value": req.value}


@app.post("/api/v1/plugins/{plugin_name}/exec")
def exec_plugin_command(plugin_name: str, req: PluginExecRequest):
    loader = get_loader()
    result = loader.exec_command(
        plugin_name, req.command, req.args, req.options, cli_args=req.cli_args
    )
    if not result["success"]:
        if "not found" in result.get("error", "") or "not found" in result.get(
            "stderr", ""
        ):
            raise HTTPException(
                status_code=404,
                detail=result.get("error", result.get("stderr", "Not found")),
            )
        if result.get("returncode") is not None:
            return result
    return result
