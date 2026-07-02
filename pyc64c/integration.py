"""Integration — Bridge between PYC64 and other SDK components."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

class IntegrationBridge:
    """
    Handles integration with C64-Intelligence-SDK, C64-LLM, and C64GameTutorial.
    """

    def __init__(self, sdk_root: str = None):
        # Look for SDK root in environment or parent directories
        if sdk_root:
            self.sdk_root = Path(sdk_root)
        else:
            # Default assumption: we are in a submodule or peer directory
            self.sdk_root = self._find_sdk_root()

    def _find_sdk_root(self) -> Path:
        current = Path.cwd()
        # Search upwards for a directory containing .git or known SDK markers
        for parent in [current] + list(current.parents):
            if (parent / "core/c64-llm").exists() or (parent / "tutorial/C64GameTutorial").exists():
                return parent
        return current.parent # Fallback to parent

    def get_tutorial_examples(self) -> List[Dict[str, Any]]:
        """Fetch example code from C64GameTutorial if available."""
        tutorial_path = self.sdk_root / "tutorial/C64GameTutorial"
        examples = []

        if tutorial_path.exists():
            # Recursively find .c64 or .py files in tutorial
            for ext in ['*.c64', '*.py']:
                for p in tutorial_path.rglob(ext):
                    try:
                        examples.append({
                            "name": p.name,
                            "path": str(p),
                            "content": p.read_text()
                        })
                    except Exception:
                        pass
        return examples

    def notify_llm_of_result(self, engine_result: Any):
        """
        Send compilation result back to C64-LLM (mocked for now).
        In a real scenario, this would post to a local endpoint or write to a shared volume.
        """
        output_file = Path("/tmp/pyc64_llm_feedback.json")
        try:
            feedback = {
                "success": engine_result.success,
                "metrics": engine_result.metrics,
                "diagnostics": engine_result.diagnostics
            }
            output_file.write_text(json.dumps(feedback, indent=2))
        except Exception:
            pass

def get_bridge() -> IntegrationBridge:
    return IntegrationBridge()
