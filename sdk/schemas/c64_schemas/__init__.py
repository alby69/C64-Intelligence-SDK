import json
from pathlib import Path
from typing import Dict, Any
import jsonschema

SCHEMAS_DIR = Path(__file__).parent.parent

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the sdk/schemas directory."""
    if not schema_name.endswith(".schema.json"):
        schema_name = f"{schema_name}.schema.json"
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_document(document_data: Dict[str, Any]) -> bool:
    """Validate a document against C64Document schema."""
    schema = load_schema("c64_document")
    jsonschema.validate(instance=document_data, schema=schema)
    return True

def validate_manifest(manifest_data: Dict[str, Any]) -> bool:
    """Validate a manifest against C64KBManifest schema."""
    schema = load_schema("c64_kb_manifest")
    jsonschema.validate(instance=manifest_data, schema=schema)
    return True

def validate_event(event_data: Dict[str, Any]) -> bool:
    """Validate an event payload against C64EcosystemEvent schema."""
    schema = load_schema("events")
    jsonschema.validate(instance=event_data, schema=schema)
    return True
