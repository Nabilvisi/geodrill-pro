"""Create a team-mode user from the command line (use this for the first admin).

    .venv\\Scripts\\python.exe tools\\create_user.py --username alice --name "Alice N." --role admin

The password is prompted for and never echoed or placed on the command line.
Uses GEODRILL_DATA_DIR if set, otherwise ./data.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api import auth  # noqa: E402
from services.api.storage import Store  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--username", required=True)
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--role", required=True, choices=auth.ROLES)
    args = parser.parse_args()
    password = getpass.getpass("Password (min 12 chars): ")
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.", file=sys.stderr)
        return 1
    store = Store(Path(os.environ.get("GEODRILL_DATA_DIR", ROOT / "data")))
    try:
        user = auth.create_user(store, args.username, args.name, args.role, password, actor="cli")
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Created {user['role']} '{user['username']}' ({user['id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
