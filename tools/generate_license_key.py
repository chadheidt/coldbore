#!/usr/bin/env python3
"""Generate one or more random Loadscope license keys.

Usage:
    python3 tools/generate_license_key.py            # one key
    python3 tools/generate_license_key.py 5          # five keys
    python3 tools/generate_license_key.py 3 john     # three keys, all tagged "john" in beta-keys.txt-formatted lines

Format:
    CBORE-XXXX-XXXX-XXXX-XXXX  (base32 RFC-4648 alphabet, no 0/1/8/9)

After generating, add each key to app/license.py's VALID_KEYS set and
record the recipient in beta-keys.txt at the project root (gitignored).
"""

import secrets
import sys

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def _block(n=4):
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def generate_key():
    return f"CBORE-{_block()}-{_block()}-{_block()}-{_block()}"


def main():
    count = 1
    tag = ""
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [count] [tag]", file=sys.stderr)
            sys.exit(1)
    if len(sys.argv) > 2:
        tag = sys.argv[2]

    for _ in range(count):
        key = generate_key()
        if tag:
            print(f"{key}  # {tag}")
        else:
            print(key)


if __name__ == "__main__":
    main()
