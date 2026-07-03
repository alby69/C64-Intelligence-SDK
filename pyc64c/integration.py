"""Integration — Bridge between PYC64 and other SDK components."""

import os
import json
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional

class IntegrationBridge:
    """
    Handles integration with C64-Intelligence-SDK, C64-LLM, and C64GameTutorial.
    Implements a decoupled strategy where dependencies are discovered at runtime.
    """

    def __init__(self, sdk_root: Optional[str] = None):
        # Configuration via priority: 1. constructor, 2. Env var, 3. Autodiscovery
        env_root = os.environ.get("C64_SDK_ROOT")
        if sdk_root:
            self.sdk_root = Path(sdk_root)
        elif env_root:
            self.sdk_root = Path(env_root)
        else:
            self.sdk_root = self._find_sdk_root()

        self._shared_packages_path = self.sdk_root / "packages"
        self._setup_python_path()

    def _find_sdk_root(self) -> Path:
        """Search upwards for a directory containing .git or known SDK markers."""
        current = Path.cwd().absolute()
        # Search upwards
        for parent in [current] + list(current.parents):
            # Check for the hub README or specific structure
            if (parent / "core/c64-llm").exists() or (parent / "tutorial/C64GameTutorial").exists():
                return parent
            if (parent / "ROADMAP.md").exists() and "C64-Intelligence-SDK" in parent.name:
                return parent

        # Fallback to parent if no SDK markers found, assuming we are in tools/PYC64
        return current.parent

    def _setup_python_path(self):
        """Add SDK shared packages to sys.path if they exist."""
        if self._shared_packages_path.exists() and str(self._shared_packages_path) not in sys.path:
            sys.path.insert(0, str(self._shared_packages_path))

    def has_package(self, package_name: str) -> bool:
        """Check if a shared package (e.g. 'c64validator') is available."""
        return importlib.util.find_spec(package_name) is not None

    def get_validator(self):
        """Dynamic import of c64validator if available."""
        if self.has_package("c64validator"):
            import c64validator
            return c64validator
        return None

    def get_tutorial_examples(self) -> List[Dict[str, Any]]:
        """Fetch example code from C64GameTutorial if available."""
        tutorial_path = self.sdk_root / "tutorial/C64GameTutorial"
        if not tutorial_path.exists():
            # Try alternative path if it's a sibling
            tutorial_path = self.sdk_root.parent / "C64GameTutorial"

        examples = []
        if tutorial_path.exists():
            for ext in ['*.c64', '*.py', '*.asm']:
                for p in tutorial_path.rglob(ext):
                    try:
                        examples.append({
                            "name": p.name,
                            "path": str(p),
                            "content": p.read_text(encoding='utf-8', errors='replace')
                        })
                    except Exception:
                        pass
        return examples

    def notify_llm_of_result(self, engine_result: Any, session_id: Optional[str] = None):
        """
        Send compilation result back to C64-LLM feedback loop.
        In Docker environment, it typically uses a shared volume or a local API.
        """
        feedback_dir = Path(os.environ.get("C64_FEEDBACK_DIR", "/tmp/c64_feedback"))
        feedback_dir.mkdir(parents=True, exist_ok=True)

        filename = f"feedback_{session_id if session_id else 'latest'}.json"
        output_file = feedback_dir / filename

        try:
            import time
            feedback = {
                "success": engine_result.success,
                "metrics": engine_result.metrics,
                "diagnostics": engine_result.diagnostics,
                "timestamp": time.time()
            }
            output_file.write_text(json.dumps(feedback, indent=2))
        except Exception:
            pass

def get_bridge() -> IntegrationBridge:
    """Singleton-like accessor for the bridge."""
    if not hasattr(get_bridge, "_instance"):
        get_bridge._instance = IntegrationBridge()
    return get_bridge._instance
