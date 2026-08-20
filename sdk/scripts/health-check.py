#!/usr/bin/env python3
import sys
import requests

ENDPOINTS = [
    ("Core Service", "http://localhost:8000/"),
    ("Scrapy API Service", "http://localhost:8001/"),
    ("KB Agent Service", "http://localhost:8002/"),
]

def main():
    print("=== C64 Ecosystem Service Health Check ===")
    all_ok = True
    for name, url in ENDPOINTS:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                print(f"[OK] {name} at {url} is UP (HTTP 200)")
            else:
                print(f"[WARN] {name} at {url} returned HTTP {resp.status_code}")
                all_ok = False
        except Exception as e:
            print(f"[OFFLINE] {name} at {url} is unreachable: {e}")
            all_ok = False

    if all_ok:
        print("All ecosystem services are online.")
    else:
        print("Note: Some background microservices may not be running locally.")
    sys.exit(0)

if __name__ == "__main__":
    main()
