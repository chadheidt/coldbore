"""Sanity tests for the Excel-chrome-hide helper.

Can't actually verify Excel UI state from a test runner (no Excel in CI),
but we can confirm:
  - The module imports cleanly.
  - The two helpers exist and are callable.
  - The AppleScript bodies contain the property toggles we promised so a
    silent regression (someone deleting `display full screen` for example)
    fails the test instead of silently leaving the chrome visible.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import excel_chrome  # noqa: E402


def test_module_exposes_helpers():
    assert callable(excel_chrome.minimize_excel_chrome)
    assert callable(excel_chrome.restore_excel_chrome)


def test_minimize_script_hides_each_chrome_element():
    # Excel-for-Mac AppleScript can reliably hide these three properties.
    # The ribbon TABS row is intentionally NOT hidden — see excel_chrome.py
    # docstring for the full audit.
    script = excel_chrome._MINIMIZE_SCRIPT
    assert "set display formula bar to false" in script
    assert "set display status bar to false" in script
    assert "set display headings of active window to false" in script


def test_restore_script_reverses_each_setting():
    script = excel_chrome._RESTORE_SCRIPT
    assert "set display formula bar to true" in script
    assert "set display status bar to true" in script
    assert "set display headings of active window to true" in script


def test_each_property_toggle_is_wrapped_in_try():
    # Defensive: a single property failing on one Excel build shouldn't
    # abort the whole minimise. The script wraps each `set display ...`
    # in its own `try ... end try`.
    for script in (excel_chrome._MINIMIZE_SCRIPT, excel_chrome._RESTORE_SCRIPT):
        lines = [line.strip() for line in script.splitlines()]
        try_opens = sum(1 for line in lines if line == "try")
        try_closes = sum(1 for line in lines if line == "end try")
        assert try_opens == try_closes
        # 3 settable properties, each in its own try block.
        assert try_opens >= 3


# --- prior-state capture / restore -------------------------------------
#
# The ribbon-collapse pref is GLOBAL + persistent, so minimize must capture
# the user's prior value and restore it later. These tests stub the OS
# touchpoints so no real Excel pref is mutated.


class _FakeConfigModule:
    """Stand-in for app.config backed by an in-memory dict."""

    def __init__(self):
        self.store = {}

    def load_config(self):
        return dict(self.store)

    def save_config(self, cfg):
        self.store = dict(cfg)


def _wire_stubs(monkeypatch, *, initial_pref):
    """Patch every OS touchpoint. Returns (calls, fake_config) where calls
    records what was written/deleted so assertions can inspect it."""
    fake_cfg = _FakeConfigModule()
    state = {"pref": initial_pref}  # None == key absent
    calls = {"writes": [], "deletes": 0, "osascript": []}

    monkeypatch.setattr(excel_chrome, "_load_config",
                         lambda: (fake_cfg.load_config(), fake_cfg))
    monkeypatch.setattr(excel_chrome, "_read_ribbon_pref",
                         lambda: state["pref"])

    def _write(b):
        state["pref"] = "1" if b else "0"
        calls["writes"].append(bool(b))
        return True

    def _delete():
        state["pref"] = None
        calls["deletes"] += 1
        return True

    monkeypatch.setattr(excel_chrome, "_write_ribbon_pref_bool", _write)
    monkeypatch.setattr(excel_chrome, "_delete_ribbon_pref", _delete)
    monkeypatch.setattr(excel_chrome, "_run_osascript",
                         lambda *a, **k: calls["osascript"].append(a) or True)
    return calls, fake_cfg, state


def test_minimize_captures_prior_value_and_collapses(monkeypatch):
    calls, fake_cfg, state = _wire_stubs(monkeypatch, initial_pref="0")
    excel_chrome.minimize_excel_chrome()
    # Original value stashed in config, ribbon now collapsed.
    assert fake_cfg.store[excel_chrome._CONFIG_PRIOR_KEY] == "0"
    assert state["pref"] == "1"
    assert calls["writes"] == [True]


def test_double_minimize_does_not_clobber_original(monkeypatch):
    calls, fake_cfg, state = _wire_stubs(monkeypatch, initial_pref="0")
    excel_chrome.minimize_excel_chrome()
    excel_chrome.minimize_excel_chrome()  # second open in same run
    # Still the user's TRUE original ("0"), not our injected "1".
    assert fake_cfg.store[excel_chrome._CONFIG_PRIOR_KEY] == "0"


def test_restore_puts_back_prior_value(monkeypatch):
    calls, fake_cfg, state = _wire_stubs(monkeypatch, initial_pref="0")
    excel_chrome.minimize_excel_chrome()
    excel_chrome.restore_excel_chrome()
    assert state["pref"] == "0"                       # back to original
    assert excel_chrome._CONFIG_PRIOR_KEY not in fake_cfg.store  # marker cleared


def test_restore_deletes_key_if_originally_absent(monkeypatch):
    calls, fake_cfg, state = _wire_stubs(monkeypatch, initial_pref=None)
    excel_chrome.minimize_excel_chrome()
    assert fake_cfg.store[excel_chrome._CONFIG_PRIOR_KEY] == excel_chrome._ABSENT
    excel_chrome.restore_excel_chrome()
    assert calls["deletes"] == 1
    assert state["pref"] is None


def test_restore_is_noop_when_nothing_captured(monkeypatch):
    calls, fake_cfg, state = _wire_stubs(monkeypatch, initial_pref="1")
    excel_chrome.restore_excel_chrome()  # never minimized
    assert calls["writes"] == []
    assert calls["deletes"] == 0
    # AppleScript restore still runs (harmless even if nothing was hidden).
    assert len(calls["osascript"]) == 1
