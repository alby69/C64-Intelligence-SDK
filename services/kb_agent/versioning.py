import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("services.kb_agent.versioning")

class KBVersioning:
    """Manages semantic versioning and dataset releases for C64-KB-Agent."""

    def __init__(self, manifest_path: str = "data/manifest.json"):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading manifest at {self.manifest_path}: {e}")
        return {
            "version": "1.0.0",
            "release_notes": "Initial Knowledge Base release",
            "documents_count": 0,
            "dataset_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "last_sync": time.strftime("%Y-%m-%d %H:%M:%S"),
            "releases": [
                {
                    "version": "1.0.0",
                    "release_notes": "Initial Knowledge Base release",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            ]
        }

    def save_manifest(self):
        os.makedirs(os.path.dirname(self.manifest_path) or ".", exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)

    def bump_version(self, bump_type: str = "patch", release_notes: str = "") -> str:
        current = self.manifest.get("version", "1.0.0").split(".")
        major, minor, patch = int(current[0]), int(current[1]), int(current[2])

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        self.manifest["version"] = new_version
        self.manifest["last_sync"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if release_notes:
            self.manifest["release_notes"] = release_notes

        releases = self.manifest.setdefault("releases", [])
        releases.append({
            "version": new_version,
            "release_notes": release_notes or f"Release {new_version}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_manifest()
        return new_version

    def list_releases(self) -> List[Dict[str, Any]]:
        return self.manifest.get("releases", [])

    def get_current_version(self) -> str:
        return self.manifest.get("version", "1.0.0")
