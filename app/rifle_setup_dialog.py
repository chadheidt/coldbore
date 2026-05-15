"""Native "Rifle & Setup" form — UI-change Phase 1 ([[loadscope-appify-scoping]]).

The first slice of bringing the clean Loadscope format to the REAL
workbook: a themed form for the hand-typed identity/setup data, so the
user edits it in Loadscope instead of hunting cells in the Excel grid.
It reads from and writes back into the workbook's Load Log header (the
single source of truth — its formulas propagate to the Ballistics
header), exactly the openpyxl pattern apply_workbook_repairs already
uses. Excel stays the calc engine.

The field -> Load Log cell map + the read/write helpers are pure
(no Qt), so they're unit-testable without a display.

Deliberately EXCLUDED from Phase 1 (handled elsewhere / Phase 2):
  - Powder (Load Log!G9) is a FORMULA auto-derived from the Garmin
    import — writing a literal would clobber it.
  - Date (Load Log!B13) is a datetime-typed cell feeding formulas;
    typed-widget editing comes in Phase 2 to avoid format corruption.
"""

import os

try:
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QVBoxLayout,
    )
except ImportError:  # allow import for unit tests without PyQt5
    QDialog = QDialogButtonBox = QFormLayout = QLabel = QLineEdit = None
    QMessageBox = QVBoxLayout = QFont = None

from openpyxl import load_workbook

# (section, label, Load Log value-cell, kind). kind: "text" | "number".
# Verified against the demo workbook's Load Log header layout.
RIFLE_SETUP_FIELDS = [
    ("Rifle & Shooter", "Rifle",     "B5",  "text"),
    ("Rifle & Shooter", "Shooter",   "G5",  "text"),
    ("Rifle & Shooter", "Cartridge", "L5",  "text"),
    ("Rifle & Shooter", "Barrel",    "B6",  "text"),
    ("Rifle & Shooter", "Optic",     "G6",  "text"),
    ("Rifle & Shooter", "Chrono",    "L6",  "text"),
    ("Rifle & Shooter", "Scope click (turret)", "G7", "text"),
    ("Load Components", "Bullet",    "B9",  "text"),
    ("Load Components", "Primer",    "L9",  "text"),
    ("Load Components", "Brass",     "O9",  "text"),
    ("Load Components", "CBTO (in)", "B10", "number"),
    ("Load Components", "OAL (in)",  "G10", "number"),
    ("Load Components", "Distance (yd)", "L10", "number"),
    ("Test Session",    "Temp (°F)", "G13", "number"),
    ("Test Session",    "Conditions / notes", "L13", "text"),
]

_SHEET = "Load Log"


def read_rifle_setup(workbook_path):
    """Return {cell: current value as str} for every RIFLE_SETUP_FIELDS
    cell. Pure — no Qt. Empty string for blank cells."""
    wb = load_workbook(workbook_path, data_only=False, keep_vba=False)
    ws = wb[_SHEET]
    out = {}
    for _section, _label, cell, _kind in RIFLE_SETUP_FIELDS:
        v = ws[cell].value
        out[cell] = "" if v is None else str(v)
    return out


def write_rifle_setup(workbook_path, values):
    """Write edited values back to the Load Log header cells.

    `values` is {cell: str}. "number" fields are coerced to float when
    parseable (so they keep feeding the workbook's numeric formulas);
    an unparseable number is skipped rather than corrupting the cell.
    Only cells whose value actually changed are touched. Pure — no Qt.
    Returns the list of changed cells. Raises PermissionError if the
    workbook is open in Excel (caller surfaces a friendly message).
    """
    wb = load_workbook(workbook_path, data_only=False, keep_vba=False)
    ws = wb[_SHEET]
    kinds = {cell: kind for _s, _l, cell, kind in RIFLE_SETUP_FIELDS}
    changed = []
    for cell, raw in values.items():
        if cell not in kinds:
            continue
        new = raw.strip()
        if kinds[cell] == "number":
            if new == "":
                continue
            try:
                new = float(new)
            except ValueError:
                continue  # don't corrupt a numeric cell with junk
        cur = ws[cell].value
        cur_norm = "" if cur is None else cur
        if new == cur_norm or (isinstance(new, float)
                                and _as_float(cur) == new):
            continue
        ws[cell] = new
        changed.append(cell)
    if changed:
        wb.save(workbook_path)
    return changed


def _as_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


if QDialog is not None:

    class RifleSetupDialog(QDialog):
        """Themed Rifle & Setup editor. Mirrors new_cycle_dialog's
        QDialog + theme + QFormLayout + Ok/Cancel pattern."""

        def __init__(self, workbook_path, parent=None):
            super().__init__(parent)
            self._wb_path = workbook_path
            self.saved = False
            try:
                import theme
                self._t = theme
            except ImportError:
                self._t = None

            self.setWindowTitle("Loadscope — Rifle & Setup")
            self.setModal(True)
            self.setMinimumWidth(560)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 20, 24, 16)
            layout.setSpacing(12)

            title = QLabel("Rifle & Setup")
            tf = QFont()
            tf.setPointSize(17)
            tf.setWeight(QFont.DemiBold)
            title.setFont(tf)
            if self._t:
                title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
            layout.addWidget(title)

            intro = QLabel(
                "Edit your rifle, shooter, components, and session info "
                "here — Loadscope writes it straight into your workbook."
            )
            intro.setWordWrap(True)
            if self._t:
                intro.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
            layout.addWidget(intro)

            try:
                current = read_rifle_setup(workbook_path)
            except Exception as e:
                QMessageBox.critical(
                    self, "Couldn't read workbook",
                    f"Loadscope couldn't read the workbook:\n\n{e}")
                current = {c: "" for _s, _l, c, _k in RIFLE_SETUP_FIELDS}

            self._edits = {}
            last_section = None
            form = None
            for section, label, cell, _kind in RIFLE_SETUP_FIELDS:
                if section != last_section:
                    hdr = QLabel(section.upper())
                    if self._t:
                        hdr.setStyleSheet(
                            f"color: {self._t.TEXT_TERTIARY}; "
                            f"font-size: {self._t.FONT_SIZE_TINY}px; "
                            f"text-transform: uppercase; letter-spacing: 1px; "
                            f"font-weight: bold; padding-top: 8px;")
                    layout.addWidget(hdr)
                    form = QFormLayout()
                    form.setSpacing(8)
                    layout.addLayout(form)
                    last_section = section
                edit = QLineEdit(current.get(cell, ""))
                self._edits[cell] = edit
                form.addRow(label + ":", edit)

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
            values = {c: e.text() for c, e in self._edits.items()}
            try:
                changed = write_rifle_setup(self._wb_path, values)
            except PermissionError:
                QMessageBox.warning(
                    self, "Workbook is open",
                    "Close the workbook in Excel and try again so "
                    "Loadscope can save your changes.")
                return
            except Exception as e:
                QMessageBox.critical(
                    self, "Couldn't save",
                    f"Loadscope couldn't write to the workbook:\n\n{e}")
                return
            self.saved = bool(changed)
            self.accept()


def show_rifle_setup(workbook_path, parent=None):
    """Open the Rifle & Setup editor modally. Returns True if saved."""
    dlg = RifleSetupDialog(workbook_path, parent=parent)
    dlg.exec_()
    return dlg.saved
