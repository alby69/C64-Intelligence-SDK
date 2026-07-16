import base64
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pyc64c.compiler import compile_to_prg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compiler-service")

app = FastAPI(
    title="C64 Compiler Service",
    description="Stand-alone microservice for compiling C64PY code and assembly",
    version="1.0.0"
)

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
    return {"status": "running", "service": "C64 Compiler Service"}

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
        logger.exception("Compilation failed in compiler-service")
        raise HTTPException(status_code=500, detail=str(e))
