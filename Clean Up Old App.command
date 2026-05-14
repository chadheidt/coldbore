#!/bin/bash
# Clean Up Old App.command
#
# One-time migration cleanup after the rename from "Rifle Load Importer" to
# "Loadscope". Safe to run multiple times — every step checks first whether
# there's anything to do.
#
# Will NOT touch your project folder, workbooks, CSVs, templates, or
# Garmin/BallisticX import folders.

set -e

PROJECT="$HOME/Projects/Loadscope"
OLD_APP="/Applications/Rifle Load Importer.app"
OLD_CONFIG_DIR="$HOME/Library/Application Support/Rifle Load Importer"
NEW_CONFIG_DIR="$HOME/Library/Application Support/Loadscope"
DIST_DIR="$PROJECT/dist"
BUILD_DIR="$PROJECT/build"

# ---- helpers ----
remove_path() {
    local p="$1"
    local label="$2"
    if [ -e "$p" ]; then
        if rm -rf "$p" 2>/dev/null; then
            echo "   ✓ Removed: $label"
        else
            echo "   ✗ Couldn't remove $label (permission denied)"
            echo "     Try moving it to the Trash manually from Finder."
        fi
    else
        echo "   - Already gone: $label"
    fi
}

# ---- summary + confirmation ----
echo "============================================================"
echo "Loadscope — cleanup of old Rifle Load Importer artifacts"
echo "============================================================"
echo ""
echo "This will:"
echo "  1. Copy your old config to the new Loadscope location (if needed)"
echo "  2. Remove the old 'Rifle Load Importer' Library folder"
echo "  3. Remove the old 'Rifle Load Importer.app' from /Applications"
echo "  4. Delete the build/ and dist/ folders so the next build is fresh"
echo ""
echo "Your project folder, workbooks, CSVs, and templates will NOT be touched."
echo ""
echo "Items it'll act on (only those that actually exist):"
[ -f "$OLD_CONFIG_DIR/config.json" ] && echo "  • $OLD_CONFIG_DIR/config.json"
[ -d "$OLD_CONFIG_DIR" ] && echo "  • $OLD_CONFIG_DIR (folder)"
[ -d "$OLD_APP" ] && echo "  • $OLD_APP"
[ -d "$DIST_DIR" ] && echo "  • $DIST_DIR"
[ -d "$BUILD_DIR" ] && echo "  • $BUILD_DIR"
echo ""

read -p "Proceed? [y/N] " confirm
case "$confirm" in
    y|Y|yes|YES) ;;
    *)
        echo "Cancelled. Nothing changed."
        exit 0
        ;;
esac

# ---- 1. config migration ----
echo ""
echo "1. Migrating config…"
if [ -f "$OLD_CONFIG_DIR/config.json" ]; then
    if [ ! -f "$NEW_CONFIG_DIR/config.json" ]; then
        mkdir -p "$NEW_CONFIG_DIR"
        cp "$OLD_CONFIG_DIR/config.json" "$NEW_CONFIG_DIR/config.json"
        echo "   ✓ Copied old config to: $NEW_CONFIG_DIR/config.json"
    else
        echo "   - New config already exists; old one not copied (yours is safe)"
    fi
else
    echo "   - No old config found, nothing to migrate"
fi

# ---- 2. remove old config dir ----
echo ""
echo "2. Removing old config folder…"
remove_path "$OLD_CONFIG_DIR" "Rifle Load Importer config folder"

# ---- 3. remove old .app ----
echo ""
echo "3. Removing old .app…"
remove_path "$OLD_APP" "Rifle Load Importer.app from /Applications"

# ---- 4. clean build artifacts ----
echo ""
echo "4. Cleaning build artifacts…"
remove_path "$DIST_DIR" "dist/ folder"
remove_path "$BUILD_DIR" "build/ folder"

# ---- done ----
echo ""
echo "============================================================"
echo "Cleanup complete."
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Double-click 'Build App.command' to build the new Loadscope.app"
echo "  2. Drag the new Loadscope.app from dist/ to Applications"
echo "  3. Right-click → Open the first time (one-time Gatekeeper prompt)"
echo ""
