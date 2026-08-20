#!/usr/bin/env bash
set -e

echo "=== C64 Intelligence Ecosystem Bootstrap ==="
echo "1. Initializing and updating submodules..."
git submodule update --init --recursive

echo "2. Installing editable schemas package..."
python3 -m pip install -e sdk/schemas/

echo "3. Running ecosystem health checks..."
python3 sdk/scripts/health-check.py || true

echo "=== Ecosystem Bootstrap Complete ==="
