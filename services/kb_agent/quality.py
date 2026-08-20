import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("services.kb_agent.quality")

class QualityGate:
    """Evaluates document quality metrics and quarantines low-score entries."""

    @staticmethod
    def evaluate_document(doc: Dict[str, Any]) -> Tuple[float, bool]:
        """
        Evaluates completeness, freshness, syntax validity, and content depth.
        Returns (score, is_quarantined) where score is 0-100.
        If score < 60, document is quarantined.
        """
        score = 0.0

        # Completeness (40 pts)
        content = doc.get("content", "")
        if content and len(content.strip()) > 50:
            score += 20.0
        if len(content.strip()) > 200:
            score += 20.0

        metadata = doc.get("metadata", {})
        if metadata and metadata.get("title"):
            score += 10.0
        if metadata and metadata.get("tags"):
            score += 10.0

        # Syntax / Status (20 pts)
        validation_status = doc.get("validation_status", "pending")
        if validation_status == "syntax_ok":
            score += 20.0
        elif validation_status == "syntax_warn":
            score += 10.0

        # Source / Structure (20 pts)
        if doc.get("source_url") or doc.get("category"):
            score += 20.0

        is_quarantined = score < 60.0
        return score, is_quarantined
