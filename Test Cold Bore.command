#!/bin/bash
# Run the Cold Bore GUI in dev mode for testing.
# Auto-installs PyQt5 the first time it runs.

set -e

PROJECT="$HOME/Projects/Rifle Load Data"
cd "$PROJECT"

echo "============================================================"
echo "Cold Bore — dev test run"
echo "============================================================"

# Check PyQt5
if ! /usr/bin/python3 -c "import PyQt5" 2>/dev/null; then
    echo ""
    echo "Installing PyQt5 (one-time, takes ~30 seconds)…"
    # Try the modern flag first; fall back to plain --user for older pip versions.
    if ! /usr/bin/python3 -m pip install --user --break-system-packages PyQt5 2>/dev/null; then
        /usr/bin/python3 -m pip install --user PyQt5
    fi
fi

echo ""
echo "Launching window… (close it when done testing)"
echo ""

/usr/bin/python3 "$PROJECT/app/main.py"
