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
    """True if the key is well-formed AND in the local allowed set OR was
    previously verified against the Worker's /verify endpoint (cached in
    config). Local-first so the app stays usable offline once a license
    has been activated.
    """
    norm = normalize_key(key)
    if not bool(KEY_PATTERN.match(norm)):
        return False
    if norm in VALID_KEYS:
        return True
    # Commercial key cached after a successful /verify
    cfg = app_config.load_config()
    cached = cfg.get("activated_purchased_keys") or []
    return norm in cached


# Lemon Squeezy commerce: when a user pastes a key bought on
# loadscope.lemonsqueezy.com, the app calls /verify on the Worker. If the
# Worker says the key is active, we cache it in config so the user can
# launch offline afterwards.
VERIFY_ENDPOINT = "https://coldbore-download.cheidt182.workers.dev/verify"


def verify_key_remote(key, timeout_seconds=8):
    """Call the Worker's /verify endpoint. Returns one of:
        ('active', None)    — commercial purchase, accepted
        ('beta', None)      — legacy beta key (also acceptable)
        ('revoked', msg)    — was valid, refunded
        ('invalid', msg)    — never valid
        ('offline', msg)    — couldn't reach the server
    The caller should cache 'active'/'beta' results in config so subsequent
    launches don't need network.
    """
    import json as _json
    import urllib.request as _ur
    import urllib.error as _ue
    norm = normalize_key(key)
    if not KEY_PATTERN.match(norm):
        return ("invalid", "Key isn't formatted correctly.")
    body = _json.dumps({"key": norm}).encode("utf-8")
    req = _ur.Request(
        VERIFY_ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _ur.urlopen(req, timeout=timeout_seconds) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
    except (_ue.URLError, _ue.HTTPError, TimeoutError, OSError) as e:
        return ("offline", f"Couldn't reach the license server: {e}")
    except _json.JSONDecodeError:
        return ("offline", "Server returned an unexpected response.")
    if data.get("valid"):
        return (data.get("status") or "active", None)
    status = data.get("status") or "invalid"
    msg = {
        "revoked": "This key was refunded and is no longer active.",
        "missing": "No key was provided.",
        "invalid": "We don't recognize this key.",
    }.get(status, "Key not accepted.")
    return (status, msg)


def cache_purchased_key(key):
    """Persist a Worker-verified commercial key to config so future
    is_valid_key() checks pass without network."""
    norm = normalize_key(key)
    cfg = app_config.load_config()
    cached = list(cfg.get("activated_purchased_keys") or [])
    if norm not in cached:
        cached.append(norm)
        cfg["activated_purchased_keys"] = cached
        app_config.save_config(cfg)


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

# During beta the third splash button is "Request Beta Access" and points
# at the marketing site (which hosts the Request Access modal). When
# commerce flips on, change this back to the Lemon Squeezy checkout URL
# (https://loadscope.lemonsqueezy.com/buy/1656422). See
# [[loadscope-commerce-flip-on]] memory for the full checklist.
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
