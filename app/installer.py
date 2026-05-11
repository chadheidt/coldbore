"""
True Zero — in-app installer.

The "Quit and Install" path: the running app calls launch_install_swap(),
which writes a small bash helper script to /tmp, spawns it as a detached
background process, then quits. The helper waits a few seconds for the parent
to exit, swaps the .app bundle in place, and relaunches the new version.

We use a shell script (not Python) on purpose:
  - macOS keeps the running .app bundle's executable held open while Python
    is alive. The swap MUST happen after Python exits.
  - bash is ubiquitous on macOS; no risk that a friend's Python is missing
    a module. The helper has zero dependencies beyond /usr/bin/ditto,
    /bin/mv, /usr/bin/xattr, /usr/bin/open — all preinstalled on macOS.
    (We use ditto, not unzip — unzip drops macOS metadata that codesign
    relies on, and the result trips Gatekeeper's "App is damaged" check.)

What the helper script does, in order:
  1. Wait 3 seconds for the parent app to finish quitting
  2. Detect the running .app bundle path (passed in by Python)
  3. Unzip the downloaded zip to a temp staging folder
  4. Strip macOS quarantine xattr from the new .app (so Gatekeeper doesn't
     hard-block the relaunch with a "downloaded from internet" warning)
  5. Atomically replace the old .app with the new one (mv)
  6. Open the new .app
  7. Clean up the staging folder + the downloaded zip + the helper script

Failure handling: if any step fails, the helper writes a marker file at
~/Library/Application Support/True Zero/last_install_error.log. Python
checks for this on next launch and surfaces a "previous update failed"
message via the existing crash-reporter UI pattern.

If the install location is read-only (rare — would mean True Zero was
launched from a read-only DMG or similar), launch_install_swap() returns
False and the caller should fall back to the manual download flow.
"""

import os
import stat
import subprocess
import sys
from pathlib import Path


# Where errors from the helper script are persisted, so the next launch
# can surface them. Mirrors the crash_reporter's location convention.
ERROR_LOG_NAME = "last_install_error.log"


def _config_support_dir() -> Path:
    """Return the same ~/Library/Application Support/True Zero path used by
    config.py. Duplicated here (instead of imported) to keep installer.py
    free of cross-module imports — it's safer if the helper-spawn flow
    can't pull in PyQt or other heavy modules."""
    return Path.home() / "Library" / "Application Support" / "True Zero"


def _running_app_bundle_path():
    """Locate the .app bundle that's currently running. Returns None if we
    appear to be running in dev mode (i.e., from a Python source tree, not
    a bundled .app)."""
    exe = Path(sys.executable).resolve()
    # py2app structure: <X.app>/Contents/MacOS/<exe>
    # Walk up looking for a directory ending in ".app".
    for parent in exe.parents:
        if parent.suffix == ".app":
            return parent
    return None


def can_self_install() -> bool:
    """Return True if we're a bundled .app and the bundle's parent directory
    is writable by the current user — i.e. we have a chance of doing the
    swap. Returns False in dev mode, on read-only DMGs, and when the .app
    lives in a directory the user can't write to."""
    bundle = _running_app_bundle_path()
    if bundle is None:
        return False  # dev mode — nothing to swap
    parent = bundle.parent
    return os.access(str(parent), os.W_OK)


def _build_helper_script(zip_path: str, app_bundle_path: str, error_log_path: str) -> str:
    """Build the bash script body that performs the swap. Path arguments
    are inserted via shell-quoted strings so spaces in 'True Zero.app'
    don't break things."""
    # Use shlex.quote-equivalent: wrap each path in single quotes after
    # escaping any embedded single quotes. True Zero paths shouldn't
    # contain single quotes but we belt-and-suspenders.
    def q(s: str) -> str:
        return "'" + s.replace("'", "'\\''") + "'"

    script = f"""#!/bin/bash
# True Zero self-install helper. Generated and spawned by installer.py.
# Logs to {q(error_log_path)} on failure so the next app launch can surface it.

set -u  # treat unset vars as error
ZIP={q(zip_path)}
APP={q(app_bundle_path)}
ERR_LOG={q(error_log_path)}

log_fail() {{
    echo "[$(date)] $1" >> "$ERR_LOG"
    # Give the user a heads-up via osascript - non-blocking, dismissable.
    osascript -e "display notification \\"True Zero update install failed: $1\\" with title \\"True Zero\\"" 2>/dev/null
    exit 1
}}

# Ensure the error log directory exists so log_fail can write
mkdir -p "$(dirname "$ERR_LOG")" 2>/dev/null

# 1. Wait for the parent True Zero process to finish quitting
sleep 3

# 2. Stage the new .app to a temp directory next to the existing one,
#    so the move is on the same filesystem (atomic rename).
APP_DIR="$(dirname "$APP")"
STAGING="$(mktemp -d "$APP_DIR/.truezero-update.XXXXXX")" \\
    || log_fail "Couldn't create staging dir in $APP_DIR (permission denied?)"

# 3. Extract the downloaded zip into staging.
#    NOTE: must be `ditto -x -k`, not `unzip`. unzip is BSD-style and doesn't
#    preserve macOS metadata that codesign relies on; the resulting bundle
#    looks tampered to Gatekeeper and triggers "App is damaged" on relaunch.
#    ditto is macOS-native and the inverse of how we BUILT the zip
#    (ditto -c -k --keepParent), so contents round-trip exactly.
/usr/bin/ditto -x -k "$ZIP" "$STAGING" \\
    || log_fail "Extract failed - zip may be corrupt"

# 4. Find the new .app inside staging (it's typically at the root)
NEW_APP="$(find "$STAGING" -maxdepth 2 -type d -name "*.app" -print -quit)"
if [ -z "$NEW_APP" ] || [ ! -d "$NEW_APP" ]; then
    rm -rf "$STAGING" "$ZIP"
    log_fail "Couldn't find a .app inside the downloaded zip"
fi

# 5. Strip macOS quarantine attribute so Gatekeeper doesn't hard-block on relaunch
/usr/bin/xattr -dr com.apple.quarantine "$NEW_APP" 2>/dev/null || true

# 6. Atomically replace the old .app with the new one.
#    We move the OLD app aside first (rather than removing) so a failed
#    move-in doesn't leave the user with no app at all.
TRASH="$APP_DIR/.truezero-old.$$"
mv "$APP" "$TRASH" || log_fail "Couldn't move old app aside (need admin?)"
if ! mv "$NEW_APP" "$APP"; then
    # Roll back: put the old one back so the user isn't left without an app
    mv "$TRASH" "$APP" 2>/dev/null
    rm -rf "$STAGING" "$ZIP"
    log_fail "Couldn't move new app into place - rolled back to old version"
fi

# 7. Tidy up
rm -rf "$STAGING" "$TRASH" "$ZIP"

# 8. Launch the new app
/usr/bin/open "$APP"

# 9. Self-delete this helper script
rm -- "$0" 2>/dev/null

exit 0
"""
    return script


def launch_install_swap(zip_path: str) -> bool:
    """Spawn the helper script that swaps in the new .app, then return
    True (caller should immediately quit the app — sys.exit / QApplication.quit).
    Returns False if we can't perform a self-install for any reason; caller
    should fall back to the manual download flow.
    """
    bundle = _running_app_bundle_path()
    if bundle is None:
        return False

    if not can_self_install():
        return False

    if not zip_path or not os.path.isfile(zip_path):
        return False

    cfg_dir = _config_support_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    error_log = cfg_dir / ERROR_LOG_NAME

    script_body = _build_helper_script(
        zip_path=zip_path,
        app_bundle_path=str(bundle),
        error_log_path=str(error_log),
    )

    # Write the helper script to /tmp. Using mktemp-style path so we don't
    # collide if two updates ever overlap.
    import tempfile
    fd, helper_path = tempfile.mkstemp(prefix="truezero-install-", suffix=".sh")
    try:
        # Force UTF-8 encoding here. On older macOS Pythons (3.9 system Python)
        # the locale's preferred encoding can default to ASCII, which causes
        # writing any non-ASCII char in the script body to raise UnicodeEncodeError.
        # Even though the helper script is currently pure ASCII, this is cheap
        # insurance — the script may grow over time.
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script_body)
        # Make it executable
        st = os.stat(helper_path)
        os.chmod(helper_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        return False

    # Spawn the helper detached from our process group so it survives our
    # imminent quit. start_new_session=True is the modern equivalent of
    # daemonizing. Stdout/stderr go to /dev/null so we don't tie file
    # descriptors back to the parent.
    try:
        with open(os.devnull, "w") as devnull:
            subprocess.Popen(
                ["/bin/bash", helper_path],
                stdin=devnull,
                stdout=devnull,
                stderr=devnull,
                start_new_session=True,
                close_fds=True,
            )
    except OSError:
        return False

    return True


def consume_last_install_error():
    """Read and remove the last install error log, if one exists. Returns
    its contents (the failure message) or None if there's no recent failure
    to surface. Called once at app startup so we can warn the user that
    their previous update attempt didn't complete."""
    cfg_dir = _config_support_dir()
    log_path = cfg_dir / ERROR_LOG_NAME
    if not log_path.exists():
        return None
    try:
        contents = log_path.read_text(errors="replace").strip()
        log_path.unlink()
        return contents or None
    except OSError:
        return None
