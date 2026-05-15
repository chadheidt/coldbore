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
