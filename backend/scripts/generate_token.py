from __future__ import annotations

import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.core.security import create_access_token


def main() -> None:
    # Replace with the demo user's id from the DB if different
    demo_user_id = "456d5c7f-0fc3-44d0-be78-6d164c3905b9"
    token = create_access_token(demo_user_id, "user")
    print(token)


if __name__ == "__main__":
    main()
