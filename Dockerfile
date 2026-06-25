FROM python:3.12-slim

WORKDIR /app

# Install git for version info
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy project modules
COPY pyc64c/ pyc64c/
COPY asm6502.py run_c64.py .
COPY examples/ examples/

# Create output directory
RUN mkdir -p output

# Install optional: c64py emulator
RUN pip install --no-cache-dir c64py 2>/dev/null || echo "c64py emulator not available (optional)"

# Default
CMD ["python3", "-c", "from pyc64c.asm6502 import Asm6502; print('PYC64 v0.1.0 — 6502 Cross Compiler Toolkit ready')"]
