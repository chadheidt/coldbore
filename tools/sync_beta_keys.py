#!/usr/bin/env python3
"""Pull current beta-key assignments from the Cloudflare Worker and rewrite
the local beta-keys.txt so it reflects who has which slot.

Why this exists:
    The website's request-access flow auto-assigns the next unused beta key
    when Chad approves a request. Assignments live in Cloudflare KV. The
    in-repo beta-keys.txt is a snapshot used as a quick local reference --
    this script keeps that snapshot current.

Usage:
    python3 tools/sync_beta_keys.py

The script asks for the admin token on first run and saves it to:
    ~/.config/loadscope/admin_token
Subsequent runs read the token from that file silently.

To rotate the token: delete the file and re-run. (And update the
ADMIN_TOKEN encrypted env var in the Worker dashboard.)
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path


WORKER_BASE = "https://coldbore-download.cheidt182.workers.dev"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BETA_KEYS_FILE = PROJECT_ROOT / "beta-keys.txt"
LICENSE_PY = PROJECT_ROOT / "app" / "license.py"
TOKEN_PATH = Path.home() / ".config" / "loadscope" / "admin_token"


HEADER = """# Loadscope beta-key recipient log. NEVER COMMIT (.gitignored).
#
# Format: KEY  # Recipient name, date issued, notes
# This file is rewritten by `python3 tools/sync_beta_keys.py` -- assignments
# live as the source of truth in the Cloudflare Worker's KV namespace and
# this script pulls them down.
#
# Every key here is also in app/license.py's VALID_KEYS frozenset AND the
# Cloudflare Worker's VALID_CODES set in the dashboard. Adding a new slot
# requires editing both of those places (and shipping an app release).
"""


def get_admin_token():
    """Return the admin token, prompting and saving on first run."""
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()

    print(
        "Admin token not found locally. You'll need the value that was set\n"
        "as the ADMIN_TOKEN encrypted env var in the Cloudflare Worker\n"
        "dashboard (Workers & Pages -> coldbore-download -> Settings ->\n"
        "Variables and secrets).\n"
    )
    token = input("Paste admin token: ").strip()
    if not token:
        print("No token entered. Aborting.", file=sys.stderr)
        sys.exit(1)
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(token + "\n")
    TOKEN_PATH.chmod(0o600)
    print(f"Saved to {TOKEN_PATH} (mode 600).\n")
    return token


def fetch_assignments(token):
    """Hit the Worker's /admin/assignments endpoint and return the list."""
    url = f"{WORKER_BASE}/admin/assignments?token={token}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(
                "Worker rejected the token (HTTP 401). Either the local\n"
                f"token in {TOKEN_PATH} is wrong or the ADMIN_TOKEN env\n"
                "var in the Worker has been rotated. Delete the local file\n"
                "and re-run to enter the current token.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"HTTP error from Worker: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Couldn't reach Worker at {WORKER_BASE}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    return data.get("assignments", [])


def read_license_py_keys():
    """Extract the ordered list of keys from app/license.py's VALID_KEYS block.

    Order matters -- we want beta-keys.txt to list slots in the same order they
    appear in the source (Chad first, then slot 1, slot 2, ... slot N).
    """
    text = LICENSE_PY.read_text()
    # Find the VALID_KEYS frozenset block
    match = re.search(r"VALID_KEYS\s*=\s*frozenset\(\s*\{(.+?)\}\s*\)", text, re.DOTALL)
    if not match:
        print("Couldn't find VALID_KEYS in app/license.py", file=sys.stderr)
        sys.exit(1)
    block = match.group(1)
    keys = []
    for line in block.splitlines():
        m = re.search(r'"(CBORE-[A-Z0-9-]+)"\s*,?\s*(?:#\s*(.*))?', line)
        if m:
            key = m.group(1)
            comment = (m.group(2) or "").strip()
            keys.append((key, comment))
    return keys


def main():
    if not LICENSE_PY.exists():
        print(f"Expected {LICENSE_PY} to exist. Are you running this from the project?", file=sys.stderr)
        sys.exit(1)

    token = get_admin_token()
    print("Fetching current assignments from Cloudflare Worker...")
    remote = fetch_assignments(token)
    assignments_by_code = {a["code"]: a for a in remote}

    print(f"  -> {len(remote)} assignments returned.\n")

    # Re-read the canonical key list from license.py to preserve slot order
    license_keys = read_license_py_keys()

    lines = [HEADER, ""]
    for code, source_comment in license_keys:
        assignment = assignments_by_code.get(code)
        if assignment:
            name = assignment.get("name", "").strip()
            email = assignment.get("email", "").strip()
            date = (assignment.get("assigned_at") or "")[:10]  # YYYY-MM-DD
            label = f"{name} <{email}>" if email else name
            comment = f"{label}, {date}".rstrip(", ")
        elif "Chad" in source_comment or "local testing" in source_comment:
            # Preserve Chad's own line verbatim from source
            comment = source_comment
        else:
            comment = "(unassigned)"
        lines.append(f"{code}  # {comment}")

    new_content = "\n".join(lines) + "\n"

    if BETA_KEYS_FILE.exists() and BETA_KEYS_FILE.read_text() == new_content:
        print("beta-keys.txt is already up to date. No changes.")
        return

    BETA_KEYS_FILE.write_text(new_content)
    assigned_count = sum(1 for code, _ in license_keys if code in assignments_by_code)
    unassigned_count = len(license_keys) - assigned_count
    print(f"Wrote {BETA_KEYS_FILE.relative_to(PROJECT_ROOT)}: "
          f"{assigned_count} assigned, {unassigned_count} unassigned.")


if __name__ == "__main__":
    main()
