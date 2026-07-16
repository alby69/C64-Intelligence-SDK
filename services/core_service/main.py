import base64
import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from pyc64c.compiler import compile_to_prg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core-service")

app = FastAPI(
    title="C64 Intelligence Core Service",
    description="Backend API and LSP for the C64 Intelligence Studio",
    version="1.0.0"
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
        # Parse load address
        try:
            load_addr = int(req.load_address, 16) if req.load_address.startswith("0x") else int(req.load_address)
        except ValueError:
            load_addr = 0x0801

        # Run compilation
        prg_bytes, result = compile_to_prg(req.source_code)

        if result.success:
            prg_b64 = base64.b64encode(prg_bytes).decode("utf-8")
            return CompileResponse(
                success=True,
                prg_base64=prg_b64,
                load_address=load_addr,
                size_bytes=len(prg_bytes),
                errors=[]
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
                errors=errors_list
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

                if method == "textDocument/didChange" or method == "textDocument/didOpen":
                    params = msg.get("params", {})
                    text_document = params.get("textDocument", {})
                    uri = text_document.get("uri", "file:///src/main.c64")

                    # Grab content
                    content = ""
                    if "contentChanges" in params and len(params["contentChanges"]) > 0:
                        content = params["contentChanges"][0].get("text", "")
                    else:
                        content = text_document.get("text", "")

                    # Run compiler to get diagnostics
                    diagnostics = []
                    if content:
                        _, result = compile_to_prg(content)
                        if not result.success:
                            for err in result.lex_errors + result.parse_errors:
                                line = err.get("line", 1) - 1  # 0-based index for Monaco/LSP
                                if line < 0:
                                    line = 0
                                diagnostics.append({
                                    "range": {
                                        "start": {"line": line, "character": 0},
                                        "end": {"line": line, "character": 80}
                                    },
                                    "severity": 1, # Error
                                    "message": err.get("msg", "Syntax error")
                                })

                    # Publish diagnostics response
                    resp = {
                        "jsonrpc": "2.0",
                        "method": "textDocument/publishDiagnostics",
                        "params": {
                            "uri": uri,
                            "diagnostics": diagnostics
                        }
                    }
                    await websocket.send_text(json.dumps(resp))

                elif msg_id is not None:
                    # Echo standard jsonrpc response
                    resp = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": "processed"
                    }
                    await websocket.send_text(json.dumps(resp))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None
                }))
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
                action = msg.get("action")
                prompt = msg.get("prompt", "")

                # Simple retro-style intelligent inline completion suggestions
                tokens = []
                if "10 PRINT" in prompt.upper() or "PRINT" in prompt.upper():
                    tokens = ["20 ", "GOTO ", "10", "\n"]
                elif "FOR" in prompt.upper():
                    tokens = ["\n", "    PRINT I\n", "NEXT I\n"]
                elif "POKE" in prompt.upper() or "53280" in prompt:
                    tokens = ["POKE ", "53281, ", "0", "\n"]
                else:
                    tokens = ["# AI Suggested routine\n", "def main() -> byte:\n", "    return 0\n"]

                for token in tokens:
                    await websocket.send_text(json.dumps({
                        "token": token,
                        "done": False
                    }))

                # Signal completion
                await websocket.send_text(json.dumps({
                    "token": "",
                    "done": True
                }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON", "done": True}))
            except Exception as e:
                logger.error(f"AI Copilot WebSocket error: {e}")
                await websocket.send_text(json.dumps({"error": str(e), "done": True}))
    except WebSocketDisconnect:
        logger.info("AI Copilot WebSocket disconnected")
