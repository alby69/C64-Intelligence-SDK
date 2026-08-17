"""Test di integrazione end-to-end (Epic F).

Scenario 2 — KB pipeline smoke test: il dataset prodotto da C64-Scrapy
e consolidato in C64-KB-Agent rispetta il contratto dati condiviso.
"""

import json
import os
import sys
from pathlib import Path

import pytest

SDK_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    import jsonschema
    from jsonschema import validate
except ImportError:  # pragma: no cover
    pytest.skip("jsonschema non installato", allow_module_level=True)

KB_AGENT = SDK_ROOT / "kb-agent"
SCHEMAS = KB_AGENT / "schemas"
DATASET = KB_AGENT / "data" / "dataset"


@pytest.fixture(scope="module")
def schemas():
    return {
        "document": json.loads((SCHEMAS / "document.schema.json").read_text()),
        "dataset": json.loads((SCHEMAS / "dataset.schema.json").read_text()),
        "kg": json.loads((SCHEMAS / "knowledge_graph.schema.json").read_text()),
        "api": json.loads((SCHEMAS / "api_index.schema.json").read_text()),
    }


class TestKbDatasetContract:
    def test_jsonl_valid(self, schemas):
        path = DATASET / "scraped_dataset.jsonl"
        if not path.is_file():
            pytest.skip("dataset non sincronizzato")
        n = 0
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                validate(instance=json.loads(line), schema=schemas["dataset"])
                n += 1
        assert n > 0

    def test_knowledge_graph_valid(self, schemas):
        path = DATASET / "knowledge_graph.json"
        if not path.is_file():
            pytest.skip("knowledge_graph.json non presente")
        data = json.loads(path.read_text(encoding="utf-8"))
        validate(instance=data, schema=schemas["kg"])
        assert data["nodes"] and data["edges"]

    def test_api_index_valid(self, schemas):
        path = DATASET / "api_index.json"
        if not path.is_file():
            pytest.skip("api_index.json non presente")
        data = json.loads(path.read_text(encoding="utf-8"))
        validate(instance=data, schema=schemas["api"])
        assert data