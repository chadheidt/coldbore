"""License-key validation for Loadscope.

Each tester gets a unique key (e.g. CBORE-A2BC-DEFG-H3JK-LMNP). The app
validates the key on first launch via license_dialog and stores it in
config. On every subsequent launch the stored key is re-validated against
VALID_KEYS, so revoking a key in the next release locks the user out
until a new key is issued.

Generate a new key:
    python3 tools/generate_license_key.py

Add the new key to VALID_KEYS below and ship a release. Track recipient
names in beta-keys.txt at the project root (gitignored).

Revoke a key:
    Remove it from VALID_KEYS, ship a release. Auto-update delivers the
    new build; on next launch the now-invalid key is rejected and the
    user is forced back to the license-entry dialog.
"""

import re

import config as app_config


KEY_PATTERN = re.compile(
    r"^CBORE-[A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4}$"
)


# Set of valid license keys for the current release.
# Add keys here as testers are onboarded; remove to revoke.
# Track recipient names in beta-keys.txt at the project root (gitignored).
VALID_KEYS = frozenset({
    "CBORE-DDCX-AEGK-J2FR-2SIB",  # Chad — local testing
    "CBORE-4O4I-YXZR-3VZL-XE74",  # beta slot 1
    "CBORE-ZLXI-SZH2-63DK-KZPX",  # beta slot 2
    "CBORE-LHNF-IMIT-IISA-IXFS",  # beta slot 3
    "CBORE-T7XV-Y7M7-L54X-FOHP",  # beta slot 4
    "CBORE-ROQG-NCQR-CAXN-N53D",  # beta slot 5
    "CBORE-KZYC-TJRE-DAFV-LCOY",  # beta slot 6
    "CBORE-H453-IKCN-2YHY-CPJR",  # beta slot 7
    "CBORE-3LMH-IXAV-JXWT-URJ5",  # beta slot 8
    "CBORE-AADE-RUVG-VLJU-PAWQ",  # beta slot 9
    "CBORE-L5CI-RHZE-FGWP-WXL2",  # beta slot 10
})


def normalize_key(key):
    """Return a canonical-form key from arbitrary user input.

    Trims whitespace, uppercases, and replaces any non-alphanumeric runs
    with a single hyphen so users can paste with extra spaces or odd
    separators and still get the right form.
    """
    if not key:
        return ""
    s = str(key).strip().upper()
    s = re.sub(r"[^A-Z0-9]+", "-", s)
    return s.strip("-")


def is_well_formed(key):
    """True if the key has the right shape (CBORE-XXXX-XXXX-XXXX-XXXX with
    base-32 RFC-4648 characters). Says nothing about whether it's accepted."""
    return bool(KEY_PATTERN.match(normalize_key(key)))


def is_valid_key(key):
    """True if the key is well-formed AND in the allowed set."""
    norm = normalize_key(key)
    return bool(KEY_PATTERN.match(norm)) and norm in VALID_KEYS


def license_state():
    """Return one of:
        'valid'   — config has a key and it's still in VALID_KEYS
        'invalid' — config has a key but it's no longer accepted (revoked)
        'missing' — config has no key (first launch, or config wiped)
    """
    cfg = app_config.load_config()
    stored = cfg.get("license_key", "")
    if not stored:
        return "missing"
    if is_valid_key(stored):
        return "valid"
    return "invalid"


def is_licensed():
    """Convenience wrapper: True iff license_state() == 'valid'."""
    return license_state() == "valid"


def save_license(key):
    """Persist a validated key to config. Caller is expected to have already
    validated via is_valid_key()."""
    cfg = app_config.load_config()
    cfg["license_key"] = normalize_key(key)
    app_config.save_config(cfg)


# ---------------------------------------------------------------------------
# v0.14 demo-mode helpers
#
# Loadscope ships with a built-in trial that doesn't require a license key.
# Anyone without a license key gets the demo workbook + guided tour and CAN'T
# import their own CSVs (drop zone is gated). Buying a license unlocks the
# real app. The helpers below are the high-level surface the rest of the app
# uses to decide demo-vs-licensed behavior, without re-implementing the
# license_state() granularity in every call site.
# ---------------------------------------------------------------------------

APP_MODE_LICENSED = "licensed"
APP_MODE_DEMO = "demo"

# Where the Purchase a License button on the splash + tour panel points.
# Updated when the Lemon Squeezy product page is live. For now, the marketing
# site landing page collects emails for the buyer list.
PURCHASE_URL = "https://loadscope.app/"


def app_mode():
    """High-level mode for the rest of the app.

    Returns one of:
        'licensed' — user has a valid (still-accepted) license key on file
        'demo'     — no key, or key has been revoked; show demo UX
    """
    return APP_MODE_LICENSED if is_licensed() else APP_MODE_DEMO


def is_demo_mode():
    """Convenience: True iff app_mode() == 'demo'."""
    return app_mode() == APP_MODE_DEMO


def should_show_first_launch_splash():
    """True iff: in demo mode AND user hasn't dismissed the splash yet.

    The splash offers Try Demo / Enter License Key / Purchase. Once the user
    picks any of those, mark_first_launch_splash_seen() is called and the
    splash never appears again unless the user explicitly invokes
    "Replay the Demo Tour…" from the Workbook menu.
    """
    if is_licensed():
        return False
    cfg = app_config.load_config()
    return not cfg.get("first_launch_splash_seen", False)


def mark_first_launch_splash_seen():
    """Persist the fact that the splash has been dismissed."""
    cfg = app_config.load_config()
    cfg["first_launch_splash_seen"] = True
    app_config.save_config(cfg)


def reset_first_launch_splash():
    """Re-enable the splash on next launch. Used by 'Replay the Demo Tour…'
    when the user wants the splash again (testing, or showing a buddy)."""
    cfg = app_config.load_config()
    cfg["first_launch_splash_seen"] = False
    app_config.save_config(cfg)
