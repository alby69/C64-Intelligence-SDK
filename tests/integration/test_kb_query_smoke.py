"""Test di integrazione end-to-end (Epic F).

Scenario 4 — LLM query smoke test: verifica il path di retrieval di C64-LLM
(C64KnowledgeBase) usando un embedder fittizio, senza scaricare modelli reali.
"""

import os
import sys

import pytest

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_kb_query_path_with_fake_embedder(tmp_path):
    core_dir = os.path.join(SDK_ROOT, "core")
    sys.path.insert(0, core_dir)
    from agent.knowledge_base import C64KnowledgeBase

    # Crea una mini knowledge base con documenti reali del contratto
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "d020.md").write_text(
        "---\ntitle: Border Color\ntopics: [vic-ii]\n---\n$D020: Border Color register.\n",
        encoding="utf-8",
    )
    (kb_dir / "sid.md").write_text(
        "---\ntitle: SID\ntopics: [audio]\n---\nSID sound chip registers.\n",
        encoding="utf-8",
    )

    kb = C64KnowledgeBase.__new__(C64KnowledgeBase)
    kb.kb_path = str(kb_dir)
    kb.db_path = str(tmp_path / "vectorstore")
    kb.use_reranker = False

    class FakeEmbedder:
        dim = 8
        texts = [kb_dir / "d020.md", kb_dir / "sid.md"]
        idx = 0

        def encode(self, batch, **kwargs):
            import numpy as np
            out = np.zeros((len(batch), self.dim), dtype=np.float32)
            for i, t in enumerate(batch):
                out[i, 0] = 1.0 if "D020" in t or "border" in t.lower() else 0.5
            return out

    kb._model = FakeEmbedder()
    kb._dim = FakeEmbedder.dim
    kb._load_reranker = lambda: setattr(kb, "reranker", None)

    kb.build_index()

    results = kb.query("border color register", k=2)
    assert results, "nessun risultato dalla query"
    assert "D020" in results[0].page_content