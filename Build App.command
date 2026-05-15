#!/bin/bash
# Builds Loadscope.app via py2app.
# First run installs py2app + dependencies (~1 minute). Subsequent runs are faster.
#
# Output: dist/Loadscope.app  (fully self-contained .app you can drag to Applications)

set -e

PROJECT="$HOME/Projects/Loadscope"
cd "$PROJECT"

echo "============================================================"
echo "Loadscope — building .app bundle"
echo "============================================================"
echo ""
echo "This will take a few minutes. The .app will end up in:"
echo "    $PROJECT/dist/Loadscope.app"
echo ""

# --- Dependency install --------------------------------------------------
# We show pip output verbosely so any failure (network errors, segfaults,
# version conflicts) is visible. Tries multiple strategies in order.

install_pkg() {
    local pkg="$1"
    if /usr/bin/python3 -c "import $pkg" 2>/dev/null; then
        echo "  [OK] $pkg already installed"
        return 0
    fi

    echo ""
    echo "  >>> installing $pkg (showing full pip output) <<<"
    echo ""

    # Strategy 1: modern pip with --break-system-packages
    if /usr/bin/python3 -m pip install --user --no-cache-dir --break-system-packages "$pkg"; then
        echo ""
        echo "  [OK] $pkg installed (strategy 1)"
        return 0
    fi
    echo ""
    echo "  Strategy 1 failed — trying without --break-system-packages…"
    echo ""

    # Strategy 2: older pip without that flag
    if /usr/bin/python3 -m pip install --user --no-cache-dir "$pkg"; then
        echo ""
        echo "  [OK] $pkg installed (strategy 2)"
        return 0
    fi
    echo ""
    echo "  Strategy 2 failed — trying with upgraded pip first…"
    echo ""

    # Strategy 3: upgrade pip first, then retry
    /usr/bin/python3 -m pip install --user --no-cache-dir --upgrade pip || true
    if /usr/bin/python3 -m pip install --user --no-cache-dir "$pkg"; then
        echo ""
        echo "  [OK] $pkg installed (strategy 3)"
        return 0
    fi

    echo ""
    echo "  ----------------------------------------------------------------"
    echo "  FAILED to install $pkg after multiple attempts."
    echo ""
    echo "  Try this manually in Terminal and paste the output to Claude:"
    echo "      /usr/bin/python3 -m pip install --user --no-cache-dir $pkg"
    echo "  ----------------------------------------------------------------"
    echo ""
    return 1
}

echo "Checking dependencies…"
install_pkg setuptools || exit 1
install_pkg PyQt5 || exit 1
install_pkg openpyxl || exit 1
install_pkg py2app || exit 1

# --- Clean previous build ------------------------------------------------
echo ""
echo "Cleaning previous build…"
rm -rf build dist

# --- Build ---------------------------------------------------------------
echo ""
echo "Building .app — this takes 1-3 minutes…"
echo ""

/usr/bin/python3 setup.py py2app

# --- Done ----------------------------------------------------------------
echo ""
echo "============================================================"
APP_PATH="$PROJECT/dist/Loadscope.app"
if [ -d "$APP_PATH" ]; then
    APP_SIZE=$(du -sh "$APP_PATH" | awk '{print $1}')
    echo "BUILD SUCCEEDED."
    echo ""
    echo "  $APP_PATH"
    echo "  size: $APP_SIZE"
    echo ""
    echo "Try it:  double-click the .app from Finder."
    echo "Ship it: zip the .app and AirDrop/email to a friend."
    echo "============================================================"
    open "$PROJECT/dist"
else
    echo "BUILD FAILED — see errors above."
    echo "============================================================"
    exit 1
fi
