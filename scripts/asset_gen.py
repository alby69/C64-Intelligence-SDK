#!/usr/bin/env python3
import sys
import os

def to_asm_bytes(data, bytes_per_line=8):
    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        hex_vals = ', '.join(f'${b:02x}' for b in chunk)
        lines.append(f"    .byte {hex_vals}")
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: asset_gen.py <binary_file> [label_name]")
        sys.exit(1)

    filepath = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(filepath).split('.')[0].upper()

    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        sys.exit(1)

    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"; Generated from {filepath}")
    print(f"{label}:")
    print(to_asm_bytes(data))

if __name__ == "__main__":
    main()
