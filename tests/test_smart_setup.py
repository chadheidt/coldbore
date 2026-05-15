"""Smart Setup: component data, history, smart widgets, panel round-trip."""
import os
import shutil
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import component_data as cd  # noqa: E402

DEMO = os.path.join(os.path.dirname(__file__), "..", "app", "resources",
                    "Loadscope - Demo Workbook.xlsx")


# ---- component data (pure) --------------------------------------------

def test_turret_clicks_are_the_exact_formula_strings():
    assert cd.turret_clicks() == ["0.1 Mil", "0.05 Mil",
                                  "1/4 MOA", "1/8 MOA"]


def test_data_file_loads_with_makers():
    assert "Hornady" in cd.bullet_manufacturers()
    assert "CCI" in cd.primer_manufacturers()
    assert cd.brass_options() and cd.chronographs()


def test_bullet_compose_parse_roundtrip():
    e = cd.bullets_for("Hornady")[0]
    s = cd.compose_bullet("Hornady", e)
    mfr, back = cd.parse_bullet(s)
    assert mfr == "Hornady" and back == e


def test_primer_compose_parse_roundtrip():
    s = cd.compose_primer("CCI", "BR-2")
    assert cd.parse_primer(s) == ("CCI", "BR-2")


def test_parse_unknown_returns_none():
    assert cd.parse_bullet("Acme Frisbee 999") == (None, None)
    assert cd.parse_primer("") == (None, None)


# ---- per-field history (pure) -----------------------------------------

def test_history_dedupe_and_order(tmp_path, monkeypatch):
    import config
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "c.json")
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    config.add_field_history("shooter", "Chad")
    config.add_field_history("shooter", "Guest")
    config.add_field_history("shooter", "chad")  # dupe (case-insensitive)
    assert config.get_field_history("shooter") == ["chad", "Guest"]
    config.add_field_history("shooter", "")  # blank no-op
    assert config.get_field_history("shooter") == ["chad", "Guest"]


# ---- smart widgets (headless) -----------------------------------------

@pytest.fixture(scope="module")
def qapp():
    from PyQt5.QtWidgets import QApplication
    return QApplication.instance() or QApplication(sys.argv)


def test_locked_combo_safeguard(qapp):
    import smart_fields as sf
    c = sf.LockedCombo(cd.turret_clicks())
    c.set_value("1/4 MOA")
    assert c.value() == "1/4 MOA"
    # an out-of-spec existing value is shown (not silently rewritten)
    c.set_value("0.2 Mil")
    assert c.value() == "0.2 Mil"


def test_cascade_bullet_roundtrip(qapp):
    import smart_fields as sf
    f = sf.CascadeField("bullet")
    f.set_value("Hornady 140gr ELD-M")
    assert f.value() == "Hornady 140gr ELD-M"


def test_cascade_other_freetext(qapp):
    import smart_fields as sf
    f = sf.CascadeField("primer")
    f.set_value("Obscure Custom Primer X")
    assert f.value() == "Obscure Custom Primer X"


# ---- panel round-trip (headless, temp workbook) -----------------------

def test_panel_smart_fields_save(qapp, tmp_path):
    import rifle_setup_dialog as rs
    wb = str(tmp_path / "wb.xlsx")
    shutil.copy(DEMO, wb)
    p = rs.RifleSetupPanel(wb, with_save=True)
    # turret prefilled from the demo's "0.1 Mil"
    assert p._edits["G7"].value() == "0.1 Mil"
    # bullet cascade prefilled from "Hornady 140gr ELD-M"
    assert p._edits["B9"].value() == "Hornady 140gr ELD-M"
    # change turret + shooter, save, read back
    p._edits["G7"].set_value("1/4 MOA")
    p._edits["G5"].set_value("Test Shooter")
    status, changed = p.save()
    assert status == "ok"
    back = rs.read_rifle_setup(wb)
    assert back["G7"] == "1/4 MOA"
    assert back["G5"] == "Test Shooter"
