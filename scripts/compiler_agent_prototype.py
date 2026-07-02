#!/usr/bin/env python3
"""
Prototype Compiler Agent for C64-Intelligence-SDK.
Listens for JSON requests and returns JSON responses.
"""

import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyc64c.sdk import process_sdk_request

def main():
    if len(sys.argv) > 1:
        # Read from file if provided
        with open(sys.argv[1], 'r') as f:
            request_json = f.read()
    else:
        # Read from stdin
        print("Reading JSON request from stdin (Ctrl+D to finish):", file=sys.stderr)
        request_json = sys.stdin.read()

    if not request_json.strip():
        print("Empty request", file=sys.stderr)
        return

    response = process_sdk_request(request_json)
    print(response)

if __name__ == '__main__':
    main()
