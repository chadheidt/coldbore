"""Tests for the Pocket Range Card generator.

Covers:
 - _fmt formatting helper
 - generate_pocket_card raises with no DOPE data
 - generate_pocket_card writes a valid HTML file when data is present
 - URL dispatcher recognizes 'print-pocket-card' action
"""
import os
import sys
import shutil
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pocket_card


def test_fmt_blank_glyph_for_none():
    assert pocket_card._fmt(None) == "—"


def test_fmt_blank_glyph_for_empty_string():
    assert pocket_card._fmt("") == "—"
    assert pocket_card._fmt("   ") == "—"


def test_fmt_returns_string_unchanged():
    assert pocket_card._fmt("Tikka") == "Tikka"


def test_fmt_int_value_no_decimal():
    # Float that's actually an int → no decimal
    assert pocket_card._fmt(100.0) == "100"
    assert pocket_card._fmt(7) == "7"


def test_fmt_float_trims_trailing_zeros():
    # Trim trailing zeros, keep meaningful digits
    assert pocket_card._fmt(0.30) == "0.3"
    assert pocket_card._fmt(1.4) == "1.4"


# ---------- Generator end-to-end ----------

@pytest.fixture
def workbook_no_dope(tmp_path):
    """Copy the template — no DOPE data filled in. Used for error-case test."""
    src = os.path.join(
        os.path.dirname(__file__), "..",
        "Rifle Loads Template (do not edit).xltx",
    )
    if not os.path.isfile(src):
        pytest.skip("template not available")
    dst = tmp_path / "no_dope.xlsx"
    shutil.copy(src, dst)
    return str(dst)


@pytest.fixture
def workbook_with_dope(tmp_path):
    """Template with sample DOPE data filled in for the generator test."""
    src = os.path.join(
        os.path.dirname(__file__), "..",
        "Rifle Loads Template (do not edit).xltx",
    )
    if not os.path.isfile(src):
        pytest.skip("template not available")
    dst = tmp_path / "with_dope.xlsx"
    shutil.copy(src, dst)
    from openpyxl import load_workbook
    wb = load_workbook(dst, keep_vba=False)
    wb.template = False
    bal = wb["Ballistics"]
    bal["B5"] = "Tikka T3x 6.5 CM"
    bal["E5"] = "140 ELD-M"
    bal["H5"] = 41.5
    bal["K5"] = 2780
    bal["B6"] = "Vortex Razor"
    bal["E6"] = 100
    bal["H6"] = 1.75
    bal["K6"] = "1:8 RH"
    # Scope click value lives on Load Log (single source of truth)
    wb["Load Log"]["G7"] = "1/4 MOA"
    # 3 rows of sample DOPE (enough to satisfy "any data" check)
    sample = [
        (100, 0.0, 0, 0.0, 0, 0.1, 1, 0.3, 1, 0.11),
        (200, 0.3, 3, 1.1, 4, 0.2, 2, 0.6, 2, 0.23),
        (300, 0.8, 8, 2.6, 10, 0.3, 3, 1.0, 4, 0.36),
    ]
    for r, vals in zip(range(9, 12), sample):
        for col, val in zip("ABCDEFGHIJ", vals):
            bal[f"{col}{r}"] = val
    wb.save(dst)
    return str(dst)


def test_generate_raises_without_dope_data(workbook_no_dope):
    with pytest.raises(ValueError, match="no DOPE data"):
        pocket_card.generate_pocket_card(workbook_no_dope, open_after=False)


def test_generate_writes_html_with_data(workbook_with_dope, tmp_path):
    out = pocket_card.generate_pocket_card(workbook_with_dope, open_after=False)
    assert os.path.isfile(out), f"generator should write a file: {out}"
    assert out.endswith(".html")
    with open(out) as f:
        content = f.read()
    # Header content
    assert "Tikka T3x 6.5 CM" in content
    assert "140 ELD-M" in content
    assert "41.5" in content
    # Standard card elements (subtitle uses CSS uppercase, raw text is title-case)
    assert "Pocket Range Card" in content
    assert "Loadscope" in content
    # Trademark mark on the brand
    assert "™" in content
    # @page rule for 4x6 print
    assert "size: 6in 4in" in content


def test_generate_data_rows_count(workbook_with_dope):
    out = pocket_card.generate_pocket_card(workbook_with_dope, open_after=False)
    with open(out) as f:
        content = f.read()
    # Each data row has class "r" on its first td
    import re
    data_rows = re.findall(r"<td class='r'>", content)
    # We populated rows 9, 10, 11 — but DOPE_ROWS iterates 9-18.
    # Rows 12-18 have no elev/wind data so they're empty cells in the table.
    # The render loop currently outputs ALL DOPE_ROWS (after the no-data check
    # on _gather). So count should be 10.
    assert len(data_rows) == 10


# ---------- URL dispatcher ----------

def test_url_dispatcher_recognizes_print_pocket_card():
    from PyQt5.QtCore import QUrl
    from main import parse_loadscope_action
    assert parse_loadscope_action(QUrl("loadscope://print-pocket-card")) == "print-pocket-card"
