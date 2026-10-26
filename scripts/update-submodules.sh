#!/usr/bin/env bash
# update-submodules.sh - Shell wrapper for submodule-manager.py

set -e

# Detect if running inside Docker
IN_DOCKER=false
if [ -f /.dockerenv ] || grep -q 'docker' /proc/1/cgroup 2>/dev/null; then
    IN_DOCKER=true
fi

# Find python3 or python
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Error: Python is required but was not found in your PATH." >&2
    exit 1
fi

# Find the absolute path to scripts/submodule-manager.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGER_PATH="${SCRIPT_DIR}/submodule-manager.py"

if [ ! -f "${MANAGER_PATH}" ]; then
    echo "Error: '${MANAGER_PATH}' not found." >&2
    exit 1
fi

# Run the python script passing all arguments
if [ "$IN_DOCKER" = true ]; then
    # We are inside the docker container
    exec "$PYTHON_CMD" "${MANAGER_PATH}" "$@"
else
    # We are running natively on the host
    exec "$PYTHON_CMD" "${MANAGER_PATH}" "$@"
fi
