"""Render the Gate-4 predicted-vs-confirmed Range & DOPE panel to PNGs.

Two outputs (offscreen, real app theme applied):
  dope-preview-1-predicted.png  — pre-range: every cell is a grey/
      italic PREDICTED estimate from the solver (the "card before you
      leave the truck" state).
  dope-preview-2-confirmed.png  — after the shooter types a few
      confirmed values: those cells turn solid (white), the rest stay
      predicted.

Used for (a) Chad's pre-ship review of Gate 4 and (b) the demo beat
screenshot. Dev/offscreen only — not bundled, not run in the app.
"""
import os
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP)

from openpyxl import load_workbook  # noqa: E402
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout  # noqa: E402

import theme  # noqa: E402
from dope_entry_dialog import DopeEntryPanel  # noqa: E402

DEMO = os.path.join(APP, "resources", "Loadscope - Demo Workbook.xlsx")
OUT = os.path.join(APP, "resources", "demo_screenshots")


def _fresh_workbook(dst):
    """Demo with the DOPE table cleared = realistic pre-range state."""
    shutil.copy(DEMO, dst)
    wb = load_workbook(dst)
    bal = wb["Ballistics"]
    for r in range(9, 19):
        for col in ("B", "D", "F", "H"):
            bal[f"{col}{r}"] = None
    wb.save(dst)
    return dst


def _shot(app, wb_path, out_path, confirm=None):
    panel = DopeEntryPanel(wb_path, with_save=True)
    if confirm:
        for rnum, field, val in confirm:
            st = panel._cells[(rnum, field)]
            st["w"].setText(val)
            panel._on_edit(rnum, field)
    holder = QWidget()
    holder.setStyleSheet("background: %s;" % theme.BG_BASE)
    lay = QVBoxLayout(holder)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(panel)
    holder.resize(960, 1040)
    app.processEvents()
    holder.grab().save(out_path)
    print("wrote", out_path)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(theme.application_stylesheet())
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp()

    wb1 = _fresh_workbook(os.path.join(tmp, "pre_range.xlsx"))
    _shot(app, wb1, os.path.join(OUT, "dope-preview-1-predicted.png"))

    wb2 = _fresh_workbook(os.path.join(tmp, "mixed.xlsx"))
    _shot(app, wb2, os.path.join(OUT, "dope-preview-2-confirmed.png"),
          confirm=[(9, "elev", "0.0"), (9, "wind", "0.1"),
                   (13, "elev", "2.7"), (13, "wind", "0.8")])


if __name__ == "__main__":
    main()
