FROM python:3.12-slim

WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy all project modules from tools/ submodule
COPY tools/pyc64c/ pyc64c/
COPY tools/pyc64_ui/ pyc64_ui/
COPY tools/run_c64.py .
COPY tools/scripts/ scripts/
COPY tools/examples/ examples/

# Create output directory
RUN mkdir -p output

# Install Python dependencies
RUN pip install --no-cache-dir textual c64py 2>/dev/null || true

# Default: launch the TUI
CMD ["python3", "-m", "pyc64_ui.app"]
