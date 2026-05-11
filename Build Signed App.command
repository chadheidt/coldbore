#!/bin/bash
# Build, code-sign, notarize, and DMG-package True Zero for distribution.
#
# Prerequisites (one-time setup):
#   1. Apple Developer Program membership ($99/yr).
#   2. Developer ID Application certificate installed in Keychain Access.
#      Verify with: security find-identity -v -p codesigning
#      Should show a line like:
#        "Developer ID Application: Chad Heidt (XXXXXXXXXX)"
#   3. App-specific password from appleid.apple.com (for notarytool).
#      Stored in keychain via:
#        xcrun notarytool store-credentials "coldbore-notary" \
#          --apple-id "your@apple.id" --team-id XXXXXXXXXX \
#          --password "abcd-efgh-ijkl-mnop"
#   4. create-dmg installed via Homebrew: brew install create-dmg
#
# What this script does:
#   1. Runs Build App.command logic to produce dist/True Zero.app
#   2. Code-signs the .app + every embedded binary with hardened runtime
#   3. Verifies the signature
#   4. Builds a DMG with a drag-to-Applications layout
#   5. Submits the DMG to Apple for notarization (waits for result)
#   6. Staples the notarization ticket to the DMG
#   7. Verifies the final result (spctl assessment)
#
# Output: dist/True.Zero.dmg  (signed, notarized, ready to ship)
#
# Until the prerequisites are set up, this script will fail at the codesign step
# and tell you what's missing.

set -e

PROJECT="$HOME/Projects/Rifle Load Data"
cd "$PROJECT"

# Mirror all output to a log file so failures are diagnosable later.
# Use direct redirection (no `tee` subshell) — the subshell wrapper has been
# observed to interact poorly with py2app's flipwritable step.
LOG_FILE="/tmp/coldbore-build.log"
exec >"$LOG_FILE" 2>&1
echo "Build log: $LOG_FILE"

# ----- Configuration (edit these once your Dev ID is issued) -----------------
# After enrolling in Apple Developer, fill these in:
SIGNING_IDENTITY="Developer ID Application: Chad Heidt (NY3D844C6W)"
NOTARY_PROFILE="coldbore-notary" # name of stored credentials in keychain (see prereqs)
APPLE_TEAM_ID="NY3D844C6W"

ENTITLEMENTS="$PROJECT/entitlements.plist"
APP_NAME="True Zero"
DMG_NAME="True.Zero.dmg"
QUICKSTART="$PROJECT/True Zero — Quick Start.docx"

# ----- Sanity checks ---------------------------------------------------------
echo "============================================================"
echo "True Zero — building SIGNED + NOTARIZED .app + .dmg"
echo "============================================================"
echo ""

if [ -z "$SIGNING_IDENTITY" ]; then
    cat <<'EOF'
ERROR: SIGNING_IDENTITY is not set in this script.

Once your Apple Developer ID Application certificate is issued and installed in
Keychain Access, run:

    security find-identity -v -p codesigning

That'll print a line like:

    1) ABCDEF1234567890ABCDEF1234567890ABCDEF12 "Developer ID Application: Chad Heidt (XXXXXXXXXX)"

Copy the part in quotes (including "Developer ID Application: ...") and paste
it into the SIGNING_IDENTITY variable at the top of this script. Also fill in
APPLE_TEAM_ID (the 10-character code in parentheses).

Then re-run this script.
EOF
    exit 1
fi

if [ -z "$APPLE_TEAM_ID" ]; then
    echo "ERROR: APPLE_TEAM_ID is not set. See the SIGNING_IDENTITY help text above."
    exit 1
fi

if [ ! -f "$ENTITLEMENTS" ]; then
    echo "ERROR: entitlements.plist not found at $ENTITLEMENTS"
    exit 1
fi

if ! command -v create-dmg &> /dev/null; then
    echo "ERROR: create-dmg not installed."
    echo "       Install with: brew install create-dmg"
    exit 1
fi

# ----- Step 1: Clean + build the unsigned .app -------------------------------
# IMPORTANT: build into /tmp/coldbore-build/ NOT into the project's dist/.
# macOS attaches com.apple.provenance xattrs to files copied inside the project
# tree, which then blocks py2app/macholib from rewriting the bundled Python3
# framework binary -- manifests as [Errno 1] Operation not permitted during the
# changefunc phase. Building outside the project tree avoids the xattr entirely.
# We copy the final .dmg + .zip back into the project's dist/ at the end.
# (See "Lessons learned" in Notes for next session.md under the v0.9.0 section.)
BUILD_DIR="/tmp/coldbore-build"
echo "[1/8] Cleaning and building the .app via py2app (out-of-tree at $BUILD_DIR)…"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/dist" "$BUILD_DIR/build"
rm -rf "$PROJECT/dist"
mkdir -p "$PROJECT/dist"
/usr/bin/python3 setup.py py2app --dist-dir "$BUILD_DIR/dist" --bdist-base "$BUILD_DIR/build"

APP_PATH="$BUILD_DIR/dist/$APP_NAME.app"
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: py2app did not produce $APP_PATH"
    exit 1
fi

# ----- Step 2: Code-sign every binary, then the bundle ------------------------
# Order matters: sign inner-most binaries first, then the .app itself.
echo "[2/8] Code-signing the .app and all embedded binaries…"

# Sign every Mach-O file anywhere inside the bundle. We walk the WHOLE bundle
# (not just Frameworks/ and Resources/) because py2app places additional
# binaries directly under Contents/MacOS/ -- specifically a `python` launcher
# alongside the main executable, and the Python3 framework binary lives at
# Contents/Frameworks/Python3.framework/Versions/3.9/Python3 with no extension
# to match on. Earlier versions of this script's find loop missed both, and
# notarization rejected the whole submission citing them as adhoc-signed.
#
# We use `file -b` to ask "is this a Mach-O" rather than filtering by name,
# which is robust against py2app adding new binaries in future builds.
find "$APP_PATH" -type f 2>/dev/null | while read -r f; do
    if file -b "$f" 2>/dev/null | grep -q 'Mach-O'; then
        # --timestamp is REQUIRED for notarization; --deep alone reuses the
        # existing adhoc signature on each binary, which Apple rejects.
        codesign --force --options runtime --timestamp \
            --sign "$SIGNING_IDENTITY" \
            "$f" 2>&1 | grep -v "replacing existing signature" || true
    fi
done

# Sign the bundle itself (entitlements only apply to the outer bundle's main exe).
codesign --force --options runtime --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGNING_IDENTITY" \
    "$APP_PATH"

# ----- Step 3: Verify the signature ------------------------------------------
echo "[3/8] Verifying signature…"
codesign --verify --deep --strict --verbose=2 "$APP_PATH" 2>&1 | tail -10
spctl -a -v "$APP_PATH" 2>&1 || true  # may say "rejected" before notarization; that's expected

# ----- Step 4: Build the DMG -------------------------------------------------
# DMG is built in $BUILD_DIR/dist/ alongside the .app, then copied to the
# project's dist/ at the end. Same provenance-xattr reason as Step 1.
echo "[4/8] Building DMG…"
DMG_PATH="$BUILD_DIR/dist/$DMG_NAME"
rm -f "$DMG_PATH"

DMG_STAGE="$BUILD_DIR/dist/dmg-stage"
rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"
cp -R "$APP_PATH" "$DMG_STAGE/"
[ -f "$QUICKSTART" ] && cp "$QUICKSTART" "$DMG_STAGE/"

create-dmg \
    --volname "True Zero" \
    --window-pos 200 120 \
    --window-size 720 460 \
    --icon-size 110 \
    --icon "$APP_NAME.app" 180 200 \
    --hide-extension "$APP_NAME.app" \
    --app-drop-link 540 200 \
    "$DMG_PATH" \
    "$DMG_STAGE/" || true   # create-dmg sometimes returns non-zero on warnings

rm -rf "$DMG_STAGE"

if [ ! -f "$DMG_PATH" ]; then
    echo "ERROR: DMG was not created. Check create-dmg output above."
    exit 1
fi

# Sign the DMG itself (some clients verify this even though Apple notarizes it)
codesign --force --sign "$SIGNING_IDENTITY" "$DMG_PATH"

# ----- Step 5: Submit for notarization ---------------------------------------
echo "[5/8] Submitting DMG to Apple for notarization (this can take 1-15 min)…"
xcrun notarytool submit "$DMG_PATH" \
    --keychain-profile "$NOTARY_PROFILE" \
    --wait

# ----- Step 6: Staple the notarization ticket --------------------------------
echo "[6/8] Stapling notarization ticket to DMG…"
xcrun stapler staple "$DMG_PATH"

# ----- Step 7: Final verification --------------------------------------------
echo "[7/8] Final verification…"
spctl -a -t install -v "$DMG_PATH"
xcrun stapler validate "$DMG_PATH"

# ----- Step 8: Also produce True.Zero.zip for auto-update compatibility ------
# The in-app self-installer (v0.8.x and later) downloads a .zip and swaps the
# .app inside. We keep producing that zip alongside the .dmg so existing users
# can auto-update smoothly while new users from the website download the .dmg.
echo "[8/8] Building True.Zero.zip for v0.8.x auto-update path…"
ZIP_PATH="$BUILD_DIR/dist/True.Zero.zip"
rm -f "$ZIP_PATH"
cd "$BUILD_DIR/dist"
ditto -c -k --keepParent "True Zero.app" "True.Zero.zip"
if [ -f "$QUICKSTART" ]; then
    cp "$QUICKSTART" .
    QS_BASENAME=$(basename "$QUICKSTART")
    zip -j "True.Zero.zip" "$QS_BASENAME"
    rm -f "$QS_BASENAME"
fi
cd "$PROJECT"

# Copy the final, signed/notarized .dmg + .zip back into the project's dist/
# so existing workflow expectations (open dist/, upload from dist/) still work.
cp "$DMG_PATH" "$PROJECT/dist/"
cp "$ZIP_PATH" "$PROJECT/dist/"
DMG_PATH="$PROJECT/dist/$DMG_NAME"
ZIP_PATH="$PROJECT/dist/True.Zero.zip"

DMG_SIZE=$(du -sh "$DMG_PATH" | awk '{print $1}')
ZIP_SIZE=$(du -sh "$ZIP_PATH" | awk '{print $1}')

echo ""
echo "============================================================"
echo "BUILD SUCCEEDED."
echo ""
echo "  $DMG_PATH"
echo "  size: $DMG_SIZE"
echo ""
echo "  $ZIP_PATH"
echo "  size: $ZIP_SIZE"
echo ""
echo "Ship both to the v0.9.0 GitHub release:"
echo "  - .dmg → website download button (new users)"
echo "  - .zip → auto-update path (manifest URL)"
echo "============================================================"
open "$PROJECT/dist"
