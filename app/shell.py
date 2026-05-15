"""Unified single-window app shell ([[loadscope-shell-scoping]]).

A left-sidebar nav + a QStackedWidget content area. The pivot Chad
chose 2026-05-15: instead of menu-launched modal dialogs, Loadscope
becomes ONE window the user lives in — Setup / Import / Results / DOPE
/ Card as panels — so the real app feels like the loved Path-B demo.

Built in isolation first (this module + panelized forms) so an
unattended build can't break the shipped app; the small MainWindow
integration is staged for Chad's review (it's the UX-defining moment).

LoadscopeShell is a plain QWidget — embeddable as a MainWindow central
widget, and unit-testable headless.
"""

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # importable for unit tests without PyQt5
    Qt = QFont = None
    QHBoxLayout = QLabel = QPushButton = QStackedWidget = None
    QVBoxLayout = QWidget = None

try:
    import theme as _theme
except ImportError:
    _theme = None


if QWidget is not None:

    class LoadscopeShell(QWidget):
        """Sidebar nav + stacked panels.

        add_panel(key, label, widget) registers a panel; switch_to(key)
        / clicking the nav selects it. mark_complete(key, done) toggles
        a ✓ on the nav item so the workflow shows progress.
        """

        NAV_WIDTH = 184

        def __init__(self, parent=None):
            super().__init__(parent)
            self._keys = []                 # order
            self._buttons = {}              # key -> QPushButton
            self._labels = {}               # key -> base label text
            self._complete = {}             # key -> bool
            self._pages = {}                # key -> stack index

            root = QHBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            self._nav = QWidget()
            self._nav.setFixedWidth(self.NAV_WIDTH)
            if _theme:
                self._nav.setStyleSheet(
                    f"background-color: {_theme.BG_ELEVATED};")
            self._nav_layout = QVBoxLayout(self._nav)
            self._nav_layout.setContentsMargins(12, 18, 12, 18)
            self._nav_layout.setSpacing(6)

            brand = QLabel("Loadscope")
            bf = QFont()
            bf.setPointSize(15)
            bf.setWeight(QFont.DemiBold)
            brand.setFont(bf)
            if _theme:
                brand.setStyleSheet(
                    f"color: {_theme.ACCENT}; padding: 0 4px 14px 4px;")
            self._nav_layout.addWidget(brand)

            self._stack = QStackedWidget()
            if _theme:
                # The embedded panels are built for Loadscope's dark
                # theme (the standalone dialogs get this bg from the
                # window). Without it the content area is light and the
                # panels' light text disappears.
                self._stack.setStyleSheet(
                    f"background-color: {_theme.BG_BASE};")
            root.addWidget(self._nav)
            root.addWidget(self._stack, stretch=1)
            self._nav_layout.addStretch(1)  # nav items insert above this

        # --- public API ----------------------------------------------------
        def add_panel(self, key, label, widget, complete=False):
            if key in self._buttons:
                raise ValueError(f"duplicate panel key: {key!r}")
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda _=False, k=key: self.switch_to(k))
            self._style_button(btn, selected=False)
            # insert before the trailing stretch
            self._nav_layout.insertWidget(
                self._nav_layout.count() - 1, btn)
            idx = self._stack.addWidget(widget)

            self._keys.append(key)
            self._buttons[key] = btn
            self._labels[key] = label
            self._complete[key] = complete
            self._pages[key] = idx
            self._refresh_button(key)
            if len(self._keys) == 1:
                self.switch_to(key)
            return widget

        def switch_to(self, key):
            if key not in self._pages:
                return
            self._stack.setCurrentIndex(self._pages[key])
            for k, b in self._buttons.items():
                sel = (k == key)
                b.setChecked(sel)
                self._style_button(b, selected=sel)
            self._current = key

        def current_key(self):
            return getattr(self, "_current", self._keys[0] if self._keys else None)

        def mark_complete(self, key, done=True):
            if key in self._complete:
                self._complete[key] = done
                self._refresh_button(key)

        def panel_widget(self, key):
            idx = self._pages.get(key)
            return None if idx is None else self._stack.widget(idx)

        def keys(self):
            return list(self._keys)

        # --- internals -----------------------------------------------------
        def _refresh_button(self, key):
            check = "✓  " if self._complete.get(key) else ""
            # Escape '&' so Qt doesn't eat it as a keyboard mnemonic
            # ("Rifle & Setup" -> "Rifle_Setup" without this).
            text = f"{check}{self._labels[key]}".replace("&", "&&")
            self._buttons[key].setText(text)

        def _style_button(self, btn, selected):
            if not _theme:
                return
            if selected:
                btn.setStyleSheet(
                    f"QPushButton {{ text-align: left; padding: 8px 12px; "
                    f"border: none; border-radius: 6px; "
                    f"color: {_theme.TEXT_PRIMARY}; "
                    f"background-color: {_theme.ACCENT}; "
                    f"font-weight: bold; }}")
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ text-align: left; padding: 8px 12px; "
                    f"border: none; border-radius: 6px; "
                    f"color: {_theme.TEXT_SECONDARY}; "
                    f"background-color: transparent; }}"
                    f"QPushButton:hover {{ color: {_theme.TEXT_PRIMARY}; "
                    f"background-color: {_theme.BG_BASE}; }}")
