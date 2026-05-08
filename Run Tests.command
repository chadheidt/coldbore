#!/bin/bash
# Run the Cold Bore test suite. Auto-installs pytest the first time.
# Use this before shipping a new version to catch regressions.

set -e

PROJECT="$HOME/Projects/Rifle Load Data"
cd "$PROJECT"

echo "============================================================"
echo "Cold Bore — running tests"
echo "============================================================"

# Make sure pytest is installed
if ! /usr/bin/python3 -c "import pytest" 2>/dev/null; then
    echo ""
    echo "Installing pytest (one-time, takes ~10 seconds)…"
    if ! /usr/bin/python3 -m pip install --user --break-system-packages pytest 2>/dev/null; then
        /usr/bin/python3 -m pip install --user pytest
    fi
fi

echo ""
/usr/bin/python3 -m pytest tests/ -v
