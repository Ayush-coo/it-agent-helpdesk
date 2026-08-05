from __future__ import annotations

import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

import httpx


def main(token: str) -> None:
    url = "http://127.0.0.1:8000/api/v1/ai/suggest-triage"
    headers = {"Authorization": f"Bearer {token}"}
    body = {"description": "My VPN is not connecting and I need access immediately"}
    r = httpx.post(url, json=body, headers=headers, timeout=10)
    print(r.status_code)
    print(r.text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python call_api.py <token>")
        sys.exit(1)
    main(sys.argv[1])
