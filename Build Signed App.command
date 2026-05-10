#!/bin/bash
# Build, code-sign, notarize, and DMG-package Cold Bore for distribution.
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
#   1. Runs Build App.command logic to produce dist/Cold Bore.app
#   2. Code-signs the .app + every embedded binary with hardened runtime
#   3. Verifies the signature
#   4. Builds a DMG with a drag-to-Applications layout
#   5. Submits the DMG to Apple for notarization (waits for result)
#   6. Staples the notarization ticket to the DMG
#   7. Verifies the final result (spctl assessment)
#
# Output: dist/Cold.Bore.dmg  (signed, notarized, ready to ship)
#
# Until the prerequisites are set up, this script will fail at the codesign step
# and tell you what's missing.

set -e

PROJECT="$HOME/Projects/Rifle Load Data"
cd "$PROJECT"

# ----- Configuration (edit these once your Dev ID is issued) -----------------
# After enrolling in Apple Developer, fill these in:
SIGNING_IDENTITY=""             # e.g. "Developer ID Application: Chad Heidt (XXXXXXXXXX)"
NOTARY_PROFILE="coldbore-notary" # name of stored credentials in keychain (see prereqs)
APPLE_TEAM_ID=""                 # 10-char team ID from your developer portal

ENTITLEMENTS="$PROJECT/entitlements.plist"
APP_NAME="Cold Bore"
DMG_NAME="Cold.Bore.dmg"
QUICKSTART="$PROJECT/Cold Bore — Quick Start.docx"

# ----- Sanity checks ---------------------------------------------------------
echo "============================================================"
echo "Cold Bore — building SIGNED + NOTARIZED .app + .dmg"
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
echo "[1/7] Cleaning and building the .app via py2app…"
rm -rf build dist
/usr/bin/python3 setup.py py2app

APP_PATH="$PROJECT/dist/$APP_NAME.app"
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: py2app did not produce $APP_PATH"
    exit 1
fi

# ----- Step 2: Code-sign every binary, then the bundle ------------------------
# Order matters: sign inner-most binaries first, then the .app itself.
echo "[2/7] Code-signing the .app and all embedded binaries…"

# Sign every executable Mach-O file inside the bundle (frameworks, dylibs, etc.)
# We use --deep at the end as a safety net; signing each leaf-level file first
# avoids "resource fork, Finder information, or similar detritus not allowed"
# errors on some files.

find "$APP_PATH/Contents/Frameworks" "$APP_PATH/Contents/Resources" \
    -type f \( -name "*.dylib" -o -name "*.so" -o -perm -u+x \) 2>/dev/null | while read -r f; do
    if file "$f" | grep -qE 'Mach-O|executable'; then
        codesign --force --options runtime \
            --entitlements "$ENTITLEMENTS" \
            --sign "$SIGNING_IDENTITY" \
            "$f" 2>&1 | grep -v "replacing existing signature" || true
    fi
done

# Sign the bundle itself (with --deep as safety net)
codesign --force --deep --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGNING_IDENTITY" \
    "$APP_PATH"

# ----- Step 3: Verify the signature ------------------------------------------
echo "[3/7] Verifying signature…"
codesign --verify --deep --strict --verbose=2 "$APP_PATH" 2>&1 | tail -10
spctl -a -v "$APP_PATH" 2>&1 || true  # may say "rejected" before notarization; that's expected

# ----- Step 4: Build the DMG -------------------------------------------------
echo "[4/7] Building DMG…"
DMG_PATH="$PROJECT/dist/$DMG_NAME"
rm -f "$DMG_PATH"

DMG_STAGE="$PROJECT/dist/dmg-stage"
rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"
cp -R "$APP_PATH" "$DMG_STAGE/"
[ -f "$QUICKSTART" ] && cp "$QUICKSTART" "$DMG_STAGE/"

create-dmg \
    --volname "Cold Bore" \
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
echo "[5/7] Submitting DMG to Apple for notarization (this can take 1-15 min)…"
xcrun notarytool submit "$DMG_PATH" \
    --keychain-profile "$NOTARY_PROFILE" \
    --wait

# ----- Step 6: Staple the notarization ticket --------------------------------
echo "[6/7] Stapling notarization ticket to DMG…"
xcrun stapler staple "$DMG_PATH"

# ----- Step 7: Final verification --------------------------------------------
echo "[7/7] Final verification…"
spctl -a -t install -v "$DMG_PATH"
xcrun stapler validate "$DMG_PATH"

DMG_SIZE=$(du -sh "$DMG_PATH" | awk '{print $1}')

echo ""
echo "============================================================"
echo "BUILD SUCCEEDED."
echo ""
echo "  $DMG_PATH"
echo "  size: $DMG_SIZE"
echo ""
echo "Ship it: drag the .dmg into a GitHub release."
echo "============================================================"
open "$PROJECT/dist"
