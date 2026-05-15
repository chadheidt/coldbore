"""Regression tests for the v0.14.4 demo-action fixes.

Bug A (Chad 2026-05-15): a LICENSED user clicking the demo's "Print
This Workbook" / "Print Pocket Range Card" buttons hit "no workbook" —
the fallback to the bundled demo workbook only fired in is_demo_mode().

Bug B (Chad 2026-05-15): clicking those buttons re-opened a same-named
workbook from another path, triggering Excel's blocking modal "can't
open two workbooks with the same name" which froze all automation.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from main import (  # noqa: E402
    resolve_demo_action_workbook,
    build_open_and_print_applescript,
)


# ---- Bug A: demo-aware workbook resolution -----------------------------

def test_prefers_selected_when_it_exists(tmp_path):
    sel = tmp_path / "MyLoads.xlsx"
    sel.write_text("x")
    bundled = tmp_path / "Demo.xlsx"
    bundled.write_text("x")
    assert resolve_demo_action_workbook(str(sel), str(bundled)) == str(sel)


def test_falls_back_to_bundled_when_no_selected(tmp_path):
    # The Bug A scenario: licensed user, no imported workbook (selected
    # is None) -> must still resolve the bundled demo workbook.
    bundled = tmp_path / "Loadscope - Demo Workbook.xlsx"
    bundled.write_text("x")
    assert resolve_demo_action_workbook(None, str(bundled)) == str(bundled)


def test_falls_back_when_selected_path_missing(tmp_path):
    bundled = tmp_path / "Demo.xlsx"
    bundled.write_text("x")
    missing = str(tmp_path / "gone.xlsx")
    assert resolve_demo_action_workbook(missing, str(bundled)) == str(bundled)


def test_returns_none_when_nothing_available(tmp_path):
    assert resolve_demo_action_workbook(None, None) is None
    assert resolve_demo_action_workbook(
        str(tmp_path / "a.xlsx"), str(tmp_path / "b.xlsx")) is None


# ---- Bug B: guarded open-and-print AppleScript -------------------------

def test_applescript_guards_against_double_open():
    osa = build_open_and_print_applescript("/tmp/x/Demo Workbook.xlsx")
    # The reliable existence primitive (NOT a `whose` filter and NOT a
    # `repeat with w in workbooks` — both throw -50 on real Excel).
    assert "(name of every workbook) as list) contains" in osa
    assert "whose name" not in osa
    assert "repeat with" not in osa
    # `open POSIX file` must be INSIDE the `if wbOpen is false` block,
    # never unconditional.
    before_open = osa.split("open POSIX file")[0]
    assert "if wbOpen is false then" in before_open
    assert osa.rstrip().endswith("end tell")
    assert "print active workbook" in osa


def test_applescript_escapes_quotes_in_name_and_path():
    osa = build_open_and_print_applescript('/tmp/wei"rd/Bad "Name".xlsx')
    # A raw unescaped double-quote would break the AppleScript string.
    assert '\\"' in osa
    # The basename (with its quote escaped) is used for the name match.
    assert 'Bad \\"Name\\".xlsx' in osa
