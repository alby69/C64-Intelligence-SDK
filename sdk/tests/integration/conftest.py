import sys
from pathlib import Path

# Automatically adjust sys.path for integration tests
root_dir = Path(__file__).resolve().parent.parent.parent
paths_to_add = [
    str(root_dir),
    str(root_dir / "scraper"),
    str(root_dir / "kb-agent"),
    str(root_dir / "core"),
    str(root_dir / "sdk" / "schemas"),
    str(root_dir / "tools"),
]

for p in paths_to_add:
    if p not in sys.path:
        sys.path.insert(0, p)
