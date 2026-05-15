"""Smart Setup field widgets (Chad 2026-05-15).

Uniform interface so RifleSetupPanel can treat them like a QLineEdit:
  .value()      -> the string to write to the workbook cell
  .set_value(s) -> load an existing cell value
  .commit()     -> persist anything worth remembering (history)

- LockedCombo  : fixed dropdown, no free text (turret clicks safeguard)
- HistoryCombo : editable combo = curated options + remembered history
- CascadeField : manufacturer -> item cascade (bullets, primers) with an
                 "Other - enter my own" escape to free text
"""

try:
    from PyQt5.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QLineEdit,
        QWidget,
    )
except ImportError:
    QComboBox = QHBoxLayout = QLineEdit = QWidget = None

import component_data as cd

try:
    import config as _config
except Exception:  # pragma: no cover
    _config = None

_OTHER = "Other — enter my own…"


if QComboBox is not None:

    class LockedCombo(QComboBox):
        """Fixed dropdown, NO free text. Used for turret clicks where a
        value outside the accepted set silently breaks click math."""

        def __init__(self, values, parent=None):
            super().__init__(parent)
            self.setEditable(False)
            self._values = list(values)
            self.addItems(self._values)

        def value(self):
            return self.currentText()

        def set_value(self, s):
            s = (s or "").strip()
            i = self.findText(s)
            if i >= 0:
                self.setCurrentIndex(i)
            elif s:
                # Don't silently rewrite the user's data on open — show
                # their existing (out-of-spec) value, but the dropdown
                # still nudges them to a valid one.
                self.insertItem(0, s)
                self.setCurrentIndex(0)

        def commit(self):
            pass

    class HistoryCombo(QComboBox):
        """Editable combo seeded with curated options + per-field
        remembered history. Typing a new value is allowed; commit()
        remembers it."""

        def __init__(self, field_key, options=None, parent=None):
            super().__init__(parent)
            self.setEditable(True)
            self._field = field_key
            self._base = list(options or [])
            self._reload()

        def _reload(self):
            cur = self.currentText() if self.isEditable() else ""
            self.clear()
            hist = (_config.get_field_history(self._field)
                    if _config else [])
            seen, items = set(), []
            for v in hist + self._base:
                k = v.strip().lower()
                if k and k not in seen:
                    seen.add(k)
                    items.append(v)
            self.addItems(items)
            if cur:
                self.setEditText(cur)

        def value(self):
            return self.currentText().strip()

        def set_value(self, s):
            self.setEditText((s or "").strip())

        def commit(self):
            if _config:
                _config.add_field_history(self._field, self.value())

    class CascadeField(QWidget):
        """Manufacturer -> item cascade for bullets / primers, with an
        'Other' escape to free text. value() returns the single
        workbook-cell string ("Hornady 140gr ELD-M" / "CCI BR-2")."""

        def __init__(self, kind, parent=None):
            super().__init__(parent)
            self._kind = kind  # "bullet" | "primer"
            lay = QHBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(8)
            self._mfr = QComboBox()
            self._mfr.setEditable(False)
            self._item = QComboBox()
            self._item.setEditable(False)
            self._free = QLineEdit()
            self._free.setPlaceholderText("Type it exactly…")
            self._free.hide()
            lay.addWidget(self._mfr, 1)
            lay.addWidget(self._item, 2)
            lay.addWidget(self._free, 3)

            if kind == "bullet":
                mfrs = cd.bullet_manufacturers()
            else:
                mfrs = cd.primer_manufacturers()
            self._mfr.addItems(mfrs + [_OTHER])
            self._entries = []  # parallels self._item rows (bullet dicts)
            self._mfr.currentIndexChanged.connect(self._mfr_changed)
            self._item.currentIndexChanged.connect(self._sync_free)
            self._mfr_changed()

        def _mfr_changed(self):
            mfr = self._mfr.currentText()
            self._item.blockSignals(True)
            self._item.clear()
            self._entries = []
            if mfr == _OTHER:
                self._item.hide()
            else:
                self._item.show()
                if self._kind == "bullet":
                    for e in cd.bullets_for(mfr):
                        self._entries.append(e)
                        self._item.addItem(cd.bullet_label(e))
                else:
                    for m in cd.primers_for(mfr):
                        self._entries.append(m)
                        self._item.addItem(m)
                self._item.addItem(_OTHER)
            self._item.blockSignals(False)
            self._sync_free()

        def _sync_free(self):
            other = (self._mfr.currentText() == _OTHER
                     or self._item.currentText() == _OTHER
                     or (self._item.count() == 0))
            self._free.setVisible(other)

        def value(self):
            mfr = self._mfr.currentText()
            if mfr == _OTHER or self._item.currentText() == _OTHER \
                    or self._item.count() == 0:
                return self._free.text().strip()
            idx = self._item.currentIndex()
            if 0 <= idx < len(self._entries):
                e = self._entries[idx]
                if self._kind == "bullet":
                    return cd.compose_bullet(mfr, e)
                return cd.compose_primer(mfr, e)
            return self._free.text().strip()

        def set_value(self, s):
            s = (s or "").strip()
            if self._kind == "bullet":
                mfr, entry = cd.parse_bullet(s)
            else:
                mfr, entry = cd.parse_primer(s)
            if mfr:
                i = self._mfr.findText(mfr)
                if i >= 0:
                    self._mfr.setCurrentIndex(i)
                    self._mfr_changed()
                    if entry is not None:
                        label = (cd.bullet_label(entry)
                                 if self._kind == "bullet" else entry)
                        j = self._item.findText(label)
                        if j >= 0:
                            self._item.setCurrentIndex(j)
                            return
                    # known maker, unknown item -> Other + raw text
                    k = self._item.findText(_OTHER)
                    if k >= 0:
                        self._item.setCurrentIndex(k)
                    self._free.setText(s)
                    self._sync_free()
                    return
            # unmatched entirely -> Other manufacturer + raw text
            oi = self._mfr.findText(_OTHER)
            if oi >= 0:
                self._mfr.setCurrentIndex(oi)
                self._mfr_changed()
            self._free.setText(s)
            self._sync_free()

        def commit(self):
            pass
