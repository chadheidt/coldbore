"""Native "Range Session" form — UI-change Phase 2 ([[loadscope-appify-scoping]]).

Session date + the DOPE table (elevation/wind you dialed at each
distance) edited in a clean Loadscope grid instead of the Excel cells.
This is THE screen the ballistic solver will later pre-fill with
predicted DOPE (the user then confirms/overwrites at the range).

Writes into the Ballistics DOPE table (rows 9-18 = 100..1000 yd) and
the Load Log session Date (B13). The click columns (C/E/G/I) are
workbook FORMULAS that auto-fill from the click value — never touched.
Only the shooter's unit is shown (Mil OR MOA, from Load Log!G7) — same
principle as the printed Pocket Card.

Field map + read/write helpers are pure (no Qt) and unit-tested.
"""

import os
from datetime import datetime

try:
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QGridLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # allow import for unit tests without PyQt5
    QDialog = QDialogButtonBox = QGridLayout = QLabel = QLineEdit = None
    QMessageBox = QScrollArea = QVBoxLayout = QWidget = QFont = None

from openpyxl import load_workbook

DOPE_ROWS = range(9, 19)          # Ballistics rows 9..18 = 100..1000 yd
_RANGE_COL = "A"
_NOTES_COL = "K"
_CLICK_CELL = ("Load Log", "G7")  # decides Mil vs MOA
_DATE_CELL = ("Load Log", "B13")
_BAL = "Ballistics"
_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d")


def dope_unit(workbook_path):
    """'moa' or 'mil' from the scope click value. Defaults to mil."""
    wb = load_workbook(workbook_path, data_only=False, keep_vba=False)
    sheet, cell = _CLICK_CELL
    v = str(wb[sheet][cell].value or "").lower()
    return "moa" if "moa" in v else "mil"


def _unit_cols(unit):
    """(elevation col, wind col) the USER types into for this unit.
    Mil: B (Mils Dialed) / F (Wind Hold Mils).
    MOA: D (MOA Dialed) / H (Wind Hold MOA)."""
    return ("D", "H") if unit == "moa" else ("B", "F")


def _date_str(v):
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    return "" if v is None else str(v)


def read_dope(workbook_path):
    """Return {'unit', 'date' (YYYY-MM-DD str), 'rows': [{row, range,
    elev, wind, notes}]}. Pure — no Qt."""
    wb = load_workbook(workbook_path, data_only=False, keep_vba=False)
    bal = wb[_BAL]
    unit = "moa" if "moa" in str(
        wb[_CLICK_CELL[0]][_CLICK_CELL[1]].value or "").lower() else "mil"
    ecol, wcol = _unit_cols(unit)
    rows = []
    for r in DOPE_ROWS:
        def s(col):
            v = bal[f"{col}{r}"].value
            return "" if v is None else str(v)
        rows.append({
            "row": r,
            "range": s(_RANGE_COL),
            "elev": s(ecol),
            "wind": s(wcol),
            "notes": s(_NOTES_COL),
        })
    return {
        "unit": unit,
        "date": _date_str(wb[_DATE_CELL[0]][_DATE_CELL[1]].value),
        "rows": rows,
    }


def _coerce(raw):
    """'' -> '' (clears the cell; the click formula yields blank).
    A number -> float. Junk -> None (skip; don't corrupt)."""
    t = raw.strip()
    if t == "":
        return ""
    try:
        return float(t)
    except ValueError:
        return None


def write_dope(workbook_path, unit, rows, date_str=None):
    """Write elevation/wind/notes (unit-appropriate cells) + optional
    session date. Never touches the click formula columns. Returns the
    list of changed cells. Raises PermissionError if open in Excel.
    Pure — no Qt."""
    wb = load_workbook(workbook_path, data_only=False, keep_vba=False)
    bal = wb[_BAL]
    ecol, wcol = _unit_cols(unit)
    changed = []

    def maybe(cell, newval):
        cur = bal[cell].value
        cur_norm = "" if cur is None else cur
        if newval is None:                       # unparseable -> skip
            return
        if newval == cur_norm:
            return
        if isinstance(newval, float):
            try:
                if cur is not None and float(cur) == newval:
                    return
            except (TypeError, ValueError):
                pass
        bal[cell] = newval
        changed.append(cell)

    by_row = {r["row"]: r for r in rows}
    for r in DOPE_ROWS:
        row = by_row.get(r)
        if not row:
            continue
        maybe(f"{ecol}{r}", _coerce(row.get("elev", "")))
        maybe(f"{wcol}{r}", _coerce(row.get("wind", "")))
        n = row.get("notes", "").strip()
        ncur = bal[f"{_NOTES_COL}{r}"].value
        if n != ("" if ncur is None else str(ncur)):
            bal[f"{_NOTES_COL}{r}"] = n
            changed.append(f"{_NOTES_COL}{r}")

    if date_str is not None:
        d = date_str.strip()
        ll = wb[_DATE_CELL[0]]
        cur = ll[_DATE_CELL[1]].value
        if d == "":
            pass  # don't clear a date by blanking the field
        else:
            parsed = None
            for fmt in _DATE_FORMATS:
                try:
                    parsed = datetime.strptime(d, fmt)
                    break
                except ValueError:
                    continue
            if parsed is not None and parsed != cur:
                ll[_DATE_CELL[1]] = parsed
                changed.append(f"{_DATE_CELL[0]}!{_DATE_CELL[1]}")

    if changed:
        wb.save(workbook_path)
    return changed


if QDialog is not None:

    class DopeEntryDialog(QDialog):
        """Themed Range Session editor: session date + unit-aware DOPE
        grid. Mirrors rifle_setup_dialog's structure."""

        def __init__(self, workbook_path, parent=None):
            super().__init__(parent)
            self._wb_path = workbook_path
            self.saved = False
            try:
                import theme
                self._t = theme
            except ImportError:
                self._t = None

            self.setWindowTitle("Loadscope — Range Session & DOPE")
            self.setModal(True)
            self.setMinimumWidth(620)

            try:
                data = read_dope(workbook_path)
            except Exception as e:
                QMessageBox.critical(
                    self, "Couldn't read workbook",
                    f"Loadscope couldn't read the workbook:\n\n{e}")
                data = {"unit": "mil", "date": "", "rows": []}
            self._unit = data["unit"]
            ulabel = "MOA" if self._unit == "moa" else "Mils"

            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 20, 24, 16)
            layout.setSpacing(10)

            title = QLabel("Range Session & DOPE")
            tf = QFont()
            tf.setPointSize(17)
            tf.setWeight(QFont.DemiBold)
            title.setFont(tf)
            if self._t:
                title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
            layout.addWidget(title)

            intro = QLabel(
                f"Enter what you dialed at the range, in {ulabel} "
                "(your scope's unit). Click counts auto-fill in the "
                "workbook. Leave a row blank if you didn't shoot it.")
            intro.setWordWrap(True)
            if self._t:
                intro.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
            layout.addWidget(intro)

            date_row = QGridLayout()
            date_row.addWidget(QLabel("Session date (YYYY-MM-DD):"), 0, 0)
            self._date_edit = QLineEdit(data.get("date", ""))
            self._date_edit.setMaximumWidth(160)
            date_row.addWidget(self._date_edit, 0, 1)
            date_row.setColumnStretch(2, 1)
            layout.addLayout(date_row)

            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(6)
            for col, head in enumerate(
                    ["Range (yd)", f"Elev ({ulabel})",
                     f"Wind/10mph ({ulabel})", "Notes"]):
                h = QLabel(head)
                if self._t:
                    h.setStyleSheet(
                        f"color: {self._t.TEXT_TERTIARY}; "
                        f"font-weight: bold;")
                grid.addWidget(h, 0, col)

            self._row_edits = {}  # row_num -> (elev, wind, notes)
            for i, row in enumerate(data["rows"], start=1):
                rnum = row["row"]
                rng = QLabel(str(row["range"]))
                if self._t:
                    rng.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
                e_el = QLineEdit(row["elev"])
                e_wd = QLineEdit(row["wind"])
                e_nt = QLineEdit(row["notes"])
                for w in (e_el, e_wd):
                    w.setMaximumWidth(120)
                grid.addWidget(rng, i, 0)
                grid.addWidget(e_el, i, 1)
                grid.addWidget(e_wd, i, 2)
                grid.addWidget(e_nt, i, 3)
                self._row_edits[rnum] = (e_el, e_wd, e_nt)

            # Pool any extra vertical space BELOW the last row so the
            # header + rows stay packed together at the top (otherwise
            # the QScrollArea stretches the grid and leaves a big gap
            # between the headers and the first row).
            grid.setRowStretch(len(data["rows"]) + 2, 1)

            holder = QWidget()
            holder.setLayout(grid)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(holder)
            layout.addWidget(scroll, stretch=1)

            btns = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            ok = btns.button(QDialogButtonBox.Ok)
            if ok is not None:
                ok.setObjectName("primary")
                ok.setText("Save")
            btns.accepted.connect(self._save)
            btns.rejected.connect(self.reject)
            layout.addWidget(btns)

        def _save(self):
            rows = [{"row": rn,
                     "elev": el.text(),
                     "wind": wd.text(),
                     "notes": nt.text()}
                    for rn, (el, wd, nt) in self._row_edits.items()]
            try:
                changed = write_dope(self._wb_path, self._unit, rows,
                                     self._date_edit.text())
            except PermissionError:
                QMessageBox.warning(
                    self, "Workbook is open",
                    "Close the workbook in Excel and try again so "
                    "Loadscope can save your DOPE.")
                return
            except Exception as e:
                QMessageBox.critical(
                    self, "Couldn't save",
                    f"Loadscope couldn't write to the workbook:\n\n{e}")
                return
            self.saved = bool(changed)
            self.accept()


def show_dope_entry(workbook_path, parent=None):
    """Open the Range Session & DOPE editor modally. True if saved."""
    dlg = DopeEntryDialog(workbook_path, parent=parent)
    dlg.exec_()
    return dlg.saved
