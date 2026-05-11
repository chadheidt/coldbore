"""
Persistent config for the Loadscope app.

Stores a small JSON file at:
    ~/Library/Application Support/Loadscope/config.json

Format:
    {
        "project_folder": "/Users/<name>/Documents/Loadscope Loads",
        "version_seen": "0.6.0"
    }

The app reads this on startup. If no config exists (or the project_folder no
longer points at a valid set-up folder), the first-run wizard kicks in.

Migrates legacy config from the old app name ("Rifle Load Importer") on first
launch so existing users don't lose their settings during the rename.
"""

import json
import os
import shutil
from pathlib import Path

from version import APP_NAME, LEGACY_APP_NAMES


CONFIG_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
CONFIG_PATH = CONFIG_DIR / "config.json"


def _migrate_legacy_config():
    """If we find an old config under a legacy app name (e.g., the previous
    "Rifle Load Importer" path) and no config under the new app name yet,
    copy the old one over so settings carry across the rename.
    Idempotent — safe to call repeatedly.
    """
    if CONFIG_PATH.exists():
        return  # already on the new path
    for legacy in LEGACY_APP_NAMES:
        legacy_path = (
            Path.home() / "Library" / "Application Support" / legacy / "config.json"
        )
        if legacy_path.exists():
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(legacy_path, CONFIG_PATH)
            except OSError:
                pass
            return


def load_config():
    """Return the saved config dict, or {} if missing/corrupt."""
    _migrate_legacy_config()
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(cfg):
    """Write the config dict to disk, creating the parent dir if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# Generic locations a returning user might already have a project folder in.
# Intentionally does NOT include any developer-specific paths — those would
# silently auto-adopt on a beta tester's machine if they happen to have a
# matching folder for unrelated reasons.
CANDIDATE_LEGACY_LOCATIONS = (
    "~/Documents/Loadscope Loads",
    "~/Documents/Loadscope",
    # Legacy paths from the Cold Bore -> Loadscope rename in v0.12.0.
    # Returning users whose project folder lived under the old brand name
    # auto-adopt their existing data instead of being sent through the wizard.
    "~/Documents/Cold Bore Loads",
    "~/Documents/Cold Bore",
    "~/Documents/Rifle Loads",
    "~/Documents/Rifle Load Data",
)


def find_existing_project_folder():
    """Look for an existing valid project folder at known locations.
    Used on first launch to avoid making users redo setup if they already
    have a folder from a prior version (or from their existing dev setup).
    Returns the first valid Path found, or None.
    """
    for loc in CANDIDATE_LEGACY_LOCATIONS:
        p = Path(loc).expanduser()
        if p.is_dir() and is_setup_valid(p):
            return p
    return None


def get_project_folder():
    """Return Path to the configured project folder, or None if not set / invalid.

    Behavior:
      1. If config has a saved path AND that folder still exists, use it.
      2. Otherwise, scan known legacy locations and adopt the first valid one,
         saving it to config so we don't scan again next launch.
      3. Otherwise return None (caller will run the wizard).
    """
    cfg = load_config()
    p = cfg.get("project_folder")
    if p:
        path = Path(p).expanduser()
        if path.is_dir():
            return path

    # No config or stale config — try legacy auto-detect.
    found = find_existing_project_folder()
    if found is not None:
        set_project_folder(found)
        return found

    return None


def set_project_folder(path):
    """Update the saved project folder."""
    cfg = load_config()
    cfg["project_folder"] = str(path)
    save_config(cfg)


def is_setup_valid(project_folder):
    """Check that a folder has the bare-minimum structure to be a valid project folder.
    A 'valid' folder has the two import subfolders and at least one .xltx or .xlsx."""
    p = Path(project_folder)
    if not (p / "Garmin Imports").is_dir():
        return False
    if not (p / "BallisticX Imports").is_dir():
        return False
    has_workbook = any(p.glob("*.xltx")) or any(p.glob("*.xlsx"))
    if not has_workbook:
        return False
    return True
