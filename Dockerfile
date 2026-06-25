FROM python:3.12-slim

WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy all project modules
COPY pyc64c/ pyc64c/
COPY pyc64_ui/ pyc64_ui/
COPY run_c64.py .
COPY scripts/ scripts/
COPY examples/ examples/

# Create output directory
RUN mkdir -p output

# Install Python dependencies
RUN pip install --no-cache-dir textual c64py 2>/dev/null || true

# Default: launch the TUI
CMD ["python3", "-m", "pyc64_ui.app"]
