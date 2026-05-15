#!/bin/bash
# Run the Loadscope test suite. Auto-installs pytest the first time.
# Use this before shipping a new version to catch regressions.

set -e

PROJECT="$HOME/Projects/Loadscope"
cd "$PROJECT"

echo "============================================================"
echo "Loadscope — running tests"
echo "============================================================"

# Make sure pytest is installed
if ! /usr/bin/python3 -c "import pytest" 2>/dev/null; then
    echo ""
    echo "Installing pytest (one-time, takes ~10 seconds)…"
    if ! /usr/bin/python3 -m pip install --user --break-system-packages pytest 2>/dev/null; then
        /usr/bin/python3 -m pip install --user pytest
    fi
fi

# Make sure pyflakes is installed -- used by tests/test_main_smoke.py to
# statically detect undefined-name bugs (the regression class that shipped
# in v0.11.0's auto-updater and crashed on first Install Update click).
if ! /usr/bin/python3 -c "import pyflakes" 2>/dev/null; then
    echo ""
    echo "Installing pyflakes (one-time, takes ~5 seconds)…"
    if ! /usr/bin/python3 -m pip install --user --break-system-packages pyflakes 2>/dev/null; then
        /usr/bin/python3 -m pip install --user pyflakes
    fi
fi

echo ""
/usr/bin/python3 -m pytest tests/ -v
