"""
First-launch disclaimer dialog.

Shows the legal disclaimer with "I understand and accept" / "Quit" buttons.
Tracks acceptance in the config file via the field
`disclaimer_accepted_version` so subsequent launches don't re-prompt unless
the disclaimer text changes (in which case DISCLAIMER_VERSION is bumped in
version.py and the user gets re-prompted).
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import config as app_config
from version import APP_NAME, DISCLAIMER_TEXT, DISCLAIMER_VERSION


class DisclaimerDialog(QDialog):
    """Modal dialog showing the disclaimer. User must click 'I understand'
    to proceed; clicking 'Quit' (or closing the window) cancels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.accepted_disclaimer = False
        self.setWindowTitle(f"{APP_NAME} — Notice & Disclaimer")
        self.setModal(True)
        self.setMinimumSize(600, 540)

        # Try to apply the app's theme if available
        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        # Title
        title = QLabel(f"{APP_NAME} — Notice & Disclaimer")
        f = QFont()
        f.setPointSize(17)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        if self._t:
            title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(title)

        intro = QLabel("Please read carefully before using True Zero.")
        if self._t:
            intro.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        layout.addWidget(intro)

        # Body — scrollable so it works on small screens
        body = QLabel(DISCLAIMER_TEXT)
        body.setWordWrap(True)
        body.setTextFormat(Qt.PlainText)
        body_font = QFont()
        body_font.setPointSize(12)
        body.setFont(body_font)
        if self._t:
            body.setStyleSheet(f"color: {self._t.TEXT_PRIMARY}; padding: 8px 0;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        scroll.setFrameShape(QScrollArea.NoFrame)
        layout.addWidget(scroll, stretch=1)

        # Action buttons
        button_row = QHBoxLayout()
        button_row.addStretch(1)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.reject)
        button_row.addWidget(quit_btn)

        accept_btn = QPushButton("I understand and accept")
        accept_btn.setObjectName("primary")  # picks up the orange accent
        accept_btn.setDefault(True)
        accept_btn.clicked.connect(self._accept)
        button_row.addWidget(accept_btn)

        layout.addLayout(button_row)

    def _accept(self):
        self.accepted_disclaimer = True
        # Persist acceptance to config so we don't re-prompt
        cfg = app_config.load_config()
        cfg["disclaimer_accepted_version"] = DISCLAIMER_VERSION
        app_config.save_config(cfg)
        self.accept()


def needs_disclaimer():
    """Return True if the user hasn't yet accepted the current disclaimer."""
    cfg = app_config.load_config()
    accepted_version = cfg.get("disclaimer_accepted_version", 0)
    try:
        accepted_version = int(accepted_version)
    except (TypeError, ValueError):
        accepted_version = 0
    return accepted_version < DISCLAIMER_VERSION


def show_disclaimer(parent=None):
    """Show the disclaimer dialog. Returns True if the user accepted, False if they quit."""
    dlg = DisclaimerDialog(parent)
    dlg.exec_()
    return dlg.accepted_disclaimer


class DisclaimerViewer(QDialog):
    """Read-only variant of the disclaimer dialog used by Tools → View Disclaimer.
    Same scrollable layout, but a single 'Close' button — no accept/quit
    semantics, since the user has already accepted on first launch."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — Notice & Disclaimer")
        self.setModal(True)
        self.setMinimumSize(600, 540)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        title = QLabel(f"{APP_NAME} — Notice & Disclaimer")
        f = QFont()
        f.setPointSize(17)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        if self._t:
            title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(title)

        body = QLabel(DISCLAIMER_TEXT)
        body.setWordWrap(True)
        body.setTextFormat(Qt.PlainText)
        body_font = QFont()
        body_font.setPointSize(12)
        body.setFont(body_font)
        if self._t:
            body.setStyleSheet(f"color: {self._t.TEXT_PRIMARY}; padding: 8px 0;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        scroll.setFrameShape(QScrollArea.NoFrame)
        layout.addWidget(scroll, stretch=1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)


def view_disclaimer(parent=None):
    """Show a read-only, scrollable view of the disclaimer (no accept/quit)."""
    dlg = DisclaimerViewer(parent)
    dlg.exec_()
