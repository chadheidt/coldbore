#!/bin/bash
# Diagnostic script — fetches the manifest URL using the same Python+urllib
# the app uses, and prints the actual response for inspection.
#
# Helps us figure out why update-check is failing even though the URL works
# in the browser.

set -e

PROJECT="$HOME/Documents/Claude/Projects/Rifle Load Data"
cd "$PROJECT"

URL="https://raw.githubusercontent.com/chadheidt/coldbore/main/manifest.json"

echo "============================================================"
echo "Cold Bore — manifest URL diagnostic"
echo "============================================================"
echo ""
echo "Fetching: $URL"
echo ""

/usr/bin/python3 <<PYEOF
import json
import urllib.request
import urllib.error

url = "$URL"

print("Step 1: Opening connection…")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "ColdBore/0.6.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        status = resp.getcode()
        ctype = resp.headers.get("Content-Type")
        raw_bytes = resp.read()
    print(f"  Status: {status}")
    print(f"  Content-Type: {ctype}")
    print(f"  Bytes received: {len(raw_bytes)}")
    print(f"  First 16 bytes (hex): {raw_bytes[:16].hex()}")
    print(f"  First 60 bytes (repr): {raw_bytes[:60]!r}")
except urllib.error.URLError as e:
    print(f"  NETWORK ERROR: {e.reason}")
    raise
except Exception as e:
    print(f"  ERROR: {e}")
    raise

print()
print("Step 2: Decoding…")
try:
    decoded = raw_bytes.decode("utf-8-sig").strip()
    print(f"  Decoded length: {len(decoded)}")
    print(f"  First 100 chars: {decoded[:100]!r}")
except Exception as e:
    print(f"  DECODE ERROR: {e}")
    raise

print()
print("Step 3: Parsing JSON…")
try:
    manifest = json.loads(decoded)
    print(f"  Parsed OK!")
    print(f"  Keys: {list(manifest.keys())}")
    print(f"  app_version: {manifest.get('app_version')}")
    print(f"  app_download_url: {manifest.get('app_download_url')}")
except json.JSONDecodeError as e:
    print(f"  JSON ERROR: {e}")
    print(f"  Full decoded content:")
    print(f"  ---")
    print(decoded)
    print(f"  ---")
    raise

print()
print("============================================================")
print("All steps succeeded. The manifest URL is fine.")
print("If the app still fails, you may be running an old .app build.")
print("Make sure you dragged dist/Cold Bore.app to Applications,")
print("replacing the old one.")
print("============================================================")
PYEOF
