import logging
import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kb-agent")

app = FastAPI(
    title="C64 Knowledge Base Agent Service",
    description="Microservice exposing document indexing, semantic search, and C64 hardware register resolution",
    version="1.0.0"
)

# Shared memory/documents DB for search
documents_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "VIC-II Color Register Setup",
        "content": "To change the background color in Commodore 64, write to memory location 53281 ($D021). To change the border color, write to location 53280 ($D020). For example: POKE 53280, 2 makes the border red.",
        "category": "video"
    },
    {
        "id": 2,
        "title": "Raster Interrupts",
        "content": "Raster interrupts allow running code at specific screen lines. Register $D012 is used to read or set the target raster line. Register $D011 (MSB of raster line) and $D019/$D01A (Interrupt status/mask) are crucial for configuring raster splits.",
        "category": "interrupts"
    },
    {
        "id": 3,
        "title": "SID Voice 1 Audio Programming",
        "content": "The SID chip begins at $D400 (54272). Voice 1 control register is at $D404. Setting the Gate bit (bit 0) starts the envelope (Attack, Decay, Sustain). Setting attack/decay at $D405 and sustain/release at $D406 defines the audio shape.",
        "category": "audio"
    },
    {
        "id": 4,
        "title": "C64 Zero Page Allocation",
        "content": "Zero Page ($0000-$00FF) is highly optimized for 6502 processing. Addresses $FB-$FE are commonly free for user indirect pointer address-mode indexing, while other registers are reserved for BASIC and KERNAL routines.",
        "category": "memory"
    }
]

# Register Mapping Database
REGISTERS_DB: Dict[int, Dict[str, Any]] = {
    0xD020: {
        "name": "VIC-II Border Color",
        "hex": "D020",
        "decimal": 53280,
        "group": "VIC-II (Video Controller)",
        "description": "Sets the color of the screen border (0-15 standard C64 colors)."
    },
    0xD021: {
        "name": "VIC-II Background Color",
        "hex": "D021",
        "decimal": 53281,
        "group": "VIC-II (Video Controller)",
        "description": "Sets the primary background color of the screen."
    },
    0xD011: {
        "name": "VIC-II Control Register 1",
        "hex": "D011",
        "decimal": 53265,
        "group": "VIC-II (Video Controller)",
        "description": "Screen control register 1. Manages vertical scroll, screen blanking, 25/24 row select, bitmap/character mode, and contains the 8th bit (MSB) of the current raster line."
    },
    0xD012: {
        "name": "VIC-II Raster Counter",
        "hex": "D012",
        "decimal": 53266,
        "group": "VIC-II (Video Controller)",
        "description": "Reads current horizontal raster line, or writes target raster line for interrupt triggering."
    },
    0xD015: {
        "name": "VIC-II Sprite Enable",
        "hex": "D015",
        "decimal": 53269,
        "group": "VIC-II (Video Controller)",
        "description": "Enables/disables sprites 0 through 7. Each bit corresponds to one sprite."
    },
    0xD016: {
        "name": "VIC-II Control Register 2",
        "hex": "D016",
        "decimal": 53270,
        "group": "VIC-II (Video Controller)",
        "description": "Screen control register 2. Manages horizontal scroll, 40/38 column select, and multicolor character mode."
    },
    0xD018: {
        "name": "VIC-II Memory Pointers",
        "hex": "D018",
        "decimal": 53272,
        "group": "VIC-II (Video Controller)",
        "description": "Sets memory base pointers for video screen RAM and character generator ROM/RAM within the active VIC-II memory bank."
    },
    0xD019: {
        "name": "VIC-II Interrupt Register",
        "hex": "D019",
        "decimal": 53273,
        "group": "VIC-II (Video Controller)",
        "description": "Interrupt status register. Bits indicate which VIC source (raster line, sprite collision, etc.) triggered the interrupt. Must be acknowledged by writing 1s."
    },
    0xD01A: {
        "name": "VIC-II Interrupt Mask",
        "hex": "D01A",
        "decimal": 53274,
        "group": "VIC-II (Video Controller)",
        "description": "Enables or disables VIC-II interrupt sources: raster line matching, sprite-sprite collision, sprite-background collision, or light pen."
    },
    0xD800: {
        "name": "Color RAM Start",
        "hex": "D800",
        "decimal": 55296,
        "group": "Memory (RAM)",
        "description": "Start of the 1024-byte Color RAM area, mapping character foreground colors to screen locations."
    },
    0x0400: {
        "name": "Screen RAM Start",
        "hex": "0400",
        "decimal": 1024,
        "group": "Memory (RAM)",
        "description": "Default start address of the 1000-byte video screen text RAM matrix."
    },
    0xDC00: {
        "name": "CIA 1 Port A (Joystick 2 / Keyboard)",
        "hex": "DC00",
        "decimal": 56320,
        "group": "CIA 1 (Input/Output)",
        "description": "Complex Interface Adapter 1 Port A. Primarily used to read Joystick 2 inputs and keyboard row matrix scans."
    },
    0xDC01: {
        "name": "CIA 1 Port B (Joystick 1 / Keyboard)",
        "hex": "DC01",
        "decimal": 56321,
        "group": "CIA 1 (Input/Output)",
        "description": "Complex Interface Adapter 1 Port B. Primarily used to read Joystick 1 inputs and keyboard column matrix scans."
    },
    0xD400: {
        "name": "SID Voice 1 Frequency Low",
        "hex": "D400",
        "decimal": 54272,
        "group": "SID (Sound Interface Device)",
        "description": "Sets low byte of oscillator frequency for Voice 1."
    },
    0xD401: {
        "name": "SID Voice 1 Frequency High",
        "hex": "D401",
        "decimal": 54273,
        "group": "SID (Sound Interface Device)",
        "description": "Sets high byte of oscillator frequency for Voice 1."
    },
    0xD404: {
        "name": "SID Voice 1 Control Register",
        "hex": "D404",
        "decimal": 54276,
        "group": "SID (Sound Interface Device)",
        "description": "Voice 1 control register: Noise, Pulse, Sawtooth, Triangle waveform selection, test bit, ring modulation, synchronization, and gate control."
    },
    0xD405: {
        "name": "SID Voice 1 Attack/Decay",
        "hex": "D405",
        "decimal": 54277,
        "group": "SID (Sound Interface Device)",
        "description": "Sets attack rate (bits 4-7) and decay rate (bits 0-3) of Voice 1 envelope."
    },
    0xD406: {
        "name": "SID Voice 1 Sustain/Release",
        "hex": "D406",
        "decimal": 54278,
        "group": "SID (Sound Interface Device)",
        "description": "Sets sustain volume (bits 4-7) and release rate (bits 0-3) of Voice 1 envelope."
    },
    0xD418: {
        "name": "SID Volume & Filter Select",
        "hex": "D418",
        "decimal": 54296,
        "group": "SID (Sound Interface Device)",
        "description": "Master volume (bits 0-3), and highpass, bandpass, lowpass filter settings, plus Voice 3 disable."
    }
}

# Index Pydantic Models
class IndexRequest(BaseModel):
    title: str
    content: str
    category: Optional[str] = "general"

class IndexResponse(BaseModel):
    success: bool
    document_id: int
    message: str

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

class SearchResultItem(BaseModel):
    id: int
    title: str
    content: str
    category: str
    score: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

# REST API Endpoints
@app.get("/")
def read_root():
    return {"status": "running", "service": "C64 Knowledge Base Agent Service"}

@app.post("/kb/index", response_model=IndexResponse)
def index_document(doc: IndexRequest):
    new_id = len(documents_db) + 1
    new_doc = {
        "id": new_id,
        "title": doc.title,
        "content": doc.content,
        "category": doc.category
    }
    documents_db.append(new_doc)
    logger.info(f"Indexed document: '{doc.title}' as ID {new_id}")
    return IndexResponse(
        success=True,
        document_id=new_id,
        message="Document indexed successfully"
    )

@app.get("/kb/search", response_model=SearchResponse)
@app.post("/kb/search", response_model=SearchResponse)
def search_kb(req: Optional[SearchRequest] = None, q: Optional[str] = None, limit: int = 5):
    query_str = ""
    result_limit = limit

    if req is not None:
        query_str = req.query
        if req.limit is not None:
            result_limit = req.limit
    elif q is not None:
        query_str = q

    if not query_str:
        return SearchResponse(query=query_str, results=[])

    # Simple TF-IDF score approximation for robust semantic matching
    # Rank documents by word overlaps and term occurrence
    query_words = set(re.findall(r'\w+', query_str.lower()))
    results = []

    for doc in documents_db:
        doc_content_lower = doc["content"].lower()
        doc_title_lower = doc["title"].lower()

        # Calculate overlap score
        score = 0.0
        for word in query_words:
            if word in doc_title_lower:
                score += 2.0  # Higher weight for title match
            if word in doc_content_lower:
                score += 1.0  # Normal weight for body match

        if score > 0:
            results.append(SearchResultItem(
                id=doc["id"],
                title=doc["title"],
                content=doc["content"],
                category=doc["category"],
                score=score
            ))

    # Sort results by score descending
    results.sort(key=lambda x: x.score, reverse=True)
    return SearchResponse(query=query_str, results=results[:result_limit])

@app.get("/kb/registers/{address}")
def resolve_register(address: str):
    # Normalize address string: hex, dec, prefix $ or 0x
    addr_val: Optional[int] = None

    # Check for hex prefix $ or 0x or plain hex string
    clean_addr = address.strip()
    try:
        if clean_addr.startswith("$"):
            addr_val = int(clean_addr[1:], 16)
        elif clean_addr.lower().startswith("0x"):
            addr_val = int(clean_addr[2:], 16)
        elif re.match(r'^[0-9a-fA-F]{4}$', clean_addr):
            addr_val = int(clean_addr, 16)
        else:
            # Assume decimal
            addr_val = int(clean_addr)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid register address format: '{address}'. Use hex (e.g. $D020, 0xD020, D020) or decimal (e.g. 53280)"
        )

    # Query database
    if addr_val in REGISTERS_DB:
        reg_info = REGISTERS_DB[addr_val]
        return {
            "address_hex": f"${addr_val:04X}",
            "address_dec": addr_val,
            "resolved": True,
            "details": reg_info
        }
    else:
        return {
            "address_hex": f"${addr_val:04X}",
            "address_dec": addr_val,
            "resolved": False,
            "details": {
                "name": f"Unknown Register ${addr_val:04X}",
                "hex": f"{addr_val:04X}",
                "decimal": addr_val,
                "group": "Unknown/Custom IO",
                "description": f"No detailed documentation found for address ${addr_val:04X} in the standard register profile."
            }
        }
