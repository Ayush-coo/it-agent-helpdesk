from __future__ import annotations

import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

import httpx


def main() -> None:
    base = "http://127.0.0.1:8000"
    login = httpx.post(f"{base}/api/v1/auth/login", json={"email": "demo.user@example.com", "password": "Password123"}, timeout=10)
    print("login status", login.status_code)
    if login.status_code != 200:
        print(login.text)
        return
    token = login.json().get("access_token")
    print("token:", token)

    headers = {"Authorization": f"Bearer {token}"}
    body = {"description": "My VPN is not connecting and I need access immediately"}
    resp = httpx.post(f"{base}/api/v1/ai/suggest-triage", json=body, headers=headers, timeout=10)
    print("suggest-triage status", resp.status_code)
    print(resp.text)


if __name__ == "__main__":
    main()
