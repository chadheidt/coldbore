"""Tests for the license-key validator (app/license.py)."""

import json
from pathlib import Path

import pytest

import license as app_license


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point the config module at a per-test temp dir so save_license() doesn't
    overwrite the developer's real config under ~/Library/Application Support."""
    import config as app_config
    cfg_dir = tmp_path / "Cold Bore"
    cfg_dir.mkdir()
    monkeypatch.setattr(app_config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(app_config, "CONFIG_PATH", cfg_dir / "config.json")
    return cfg_dir


# -- normalize_key -----------------------------------------------------------

def test_normalize_strips_and_uppercases():
    assert app_license.normalize_key("  cbore-aaaa-bbbb-cccc-dddd  ") == "CBORE-AAAA-BBBB-CCCC-DDDD"

def test_normalize_collapses_whitespace_and_alt_separators():
    assert app_license.normalize_key("cbore aaaa  bbbb cccc dddd") == "CBORE-AAAA-BBBB-CCCC-DDDD"
    assert app_license.normalize_key("cbore_aaaa_bbbb_cccc_dddd") == "CBORE-AAAA-BBBB-CCCC-DDDD"

def test_normalize_empty():
    assert app_license.normalize_key("") == ""
    assert app_license.normalize_key(None) == ""


# -- is_well_formed ----------------------------------------------------------

def test_well_formed_accepts_canonical():
    assert app_license.is_well_formed("CBORE-A2BC-DEFG-H3JK-LMNP")

def test_well_formed_rejects_wrong_prefix():
    assert not app_license.is_well_formed("FOO-A2BC-DEFG-H3JK-LMNP")

def test_well_formed_rejects_lowercase_after_normalize_recovers():
    # normalize_key uppercases, so lowercase input is OK
    assert app_license.is_well_formed("cbore-a2bc-defg-h3jk-lmnp")

def test_well_formed_rejects_disallowed_chars():
    # 0, 1, 8, 9 are not in the base32 alphabet
    assert not app_license.is_well_formed("CBORE-AAA0-BBBB-CCCC-DDDD")
    assert not app_license.is_well_formed("CBORE-AAA1-BBBB-CCCC-DDDD")
    assert not app_license.is_well_formed("CBORE-AAA8-BBBB-CCCC-DDDD")

def test_well_formed_rejects_short_blocks():
    assert not app_license.is_well_formed("CBORE-AAA-BBBB-CCCC-DDDD")
    assert not app_license.is_well_formed("CBORE-AAAA-BBBB-CCCC")


# -- is_valid_key ------------------------------------------------------------

def test_valid_key_accepts_member_of_set(monkeypatch):
    test_set = frozenset({"CBORE-AAAA-BBBB-CCCC-DDDD"})
    monkeypatch.setattr(app_license, "VALID_KEYS", test_set)
    assert app_license.is_valid_key("CBORE-AAAA-BBBB-CCCC-DDDD")
    assert app_license.is_valid_key("cbore aaaa bbbb cccc dddd")  # normalizes

def test_valid_key_rejects_non_member(monkeypatch):
    test_set = frozenset({"CBORE-AAAA-BBBB-CCCC-DDDD"})
    monkeypatch.setattr(app_license, "VALID_KEYS", test_set)
    assert not app_license.is_valid_key("CBORE-ZZZZ-YYYY-XXXX-WWWW")

def test_valid_key_rejects_garbage():
    assert not app_license.is_valid_key("")
    assert not app_license.is_valid_key("nope")
    assert not app_license.is_valid_key("CBORE")


# -- license_state and save_license ------------------------------------------

def test_state_missing_when_no_config(isolated_config):
    assert app_license.license_state() == "missing"

def test_state_valid_after_save(isolated_config, monkeypatch):
    test_set = frozenset({"CBORE-AAAA-BBBB-CCCC-DDDD"})
    monkeypatch.setattr(app_license, "VALID_KEYS", test_set)
    app_license.save_license("CBORE-AAAA-BBBB-CCCC-DDDD")
    assert app_license.license_state() == "valid"
    assert app_license.is_licensed()

def test_state_invalid_after_revocation(isolated_config, monkeypatch):
    # Save a key while it's valid
    monkeypatch.setattr(
        app_license, "VALID_KEYS",
        frozenset({"CBORE-AAAA-BBBB-CCCC-DDDD"}),
    )
    app_license.save_license("CBORE-AAAA-BBBB-CCCC-DDDD")
    # Then "ship a release" that drops the key from VALID_KEYS
    monkeypatch.setattr(app_license, "VALID_KEYS", frozenset())
    assert app_license.license_state() == "invalid"
    assert not app_license.is_licensed()

def test_save_license_normalizes(isolated_config, monkeypatch):
    monkeypatch.setattr(
        app_license, "VALID_KEYS",
        frozenset({"CBORE-AAAA-BBBB-CCCC-DDDD"}),
    )
    app_license.save_license("  cbore aaaa bbbb cccc dddd  ")
    import config as app_config
    cfg = app_config.load_config()
    assert cfg["license_key"] == "CBORE-AAAA-BBBB-CCCC-DDDD"
