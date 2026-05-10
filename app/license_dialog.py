"""License-entry dialog. Modal blocker on first launch (and after revocation).

Mirrors the architecture of disclaimer.py: a QDialog with an
"enter key, validate, proceed" flow. Without a valid key the user
cannot reach the main window.
"""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

import license as app_license
from version import APP_NAME


PROMPT_TEXT = (
    "Cold Bore is in private beta. Enter the license key that was emailed "
    "to you to unlock it.\n\n"
    "If you don't have a key, please contact the developer."
)

REVOKED_TEXT = (
    "Your previous license key is no longer valid. Enter a new key to "
    "continue, or contact the developer."
)

INVALID_KEY_FEEDBACK = (
    "That key isn't recognized. Check for typos, or contact the developer."
)


class LicenseDialog(QDialog):
    """Modal dialog asking the user to enter a license key."""

    def __init__(self, parent=None, revoked=False):
        super().__init__(parent)
        self.licensed = False

        self.setWindowTitle(f"{APP_NAME} — License Key")
        self.setModal(True)
        self.setMinimumSize(560, 280)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 22)
        layout.setSpacing(14)

        title = QLabel(f"{APP_NAME} — License Key")
        f = QFont()
        f.setPointSize(17)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        if self._t:
            title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(title)

        prompt = QLabel(REVOKED_TEXT if revoked else PROMPT_TEXT)
        prompt.setWordWrap(True)
        if self._t:
            prompt.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        layout.addWidget(prompt)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("CBORE-XXXX-XXXX-XXXX-XXXX")
        edit_font = QFont("Menlo", 14)
        self.key_edit.setFont(edit_font)
        self.key_edit.returnPressed.connect(self._submit)
        layout.addWidget(self.key_edit)

        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        # Orange accent for error feedback (matches the app's accent color)
        self.feedback.setStyleSheet("color: #d97706; min-height: 20px;")
        layout.addWidget(self.feedback)

        layout.addStretch(1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.reject)
        button_row.addWidget(quit_btn)

        unlock_btn = QPushButton("Unlock Cold Bore")
        unlock_btn.setObjectName("primary")
        unlock_btn.setDefault(True)
        unlock_btn.clicked.connect(self._submit)
        button_row.addWidget(unlock_btn)

        layout.addLayout(button_row)

        self.key_edit.setFocus()

    def _submit(self):
        key = self.key_edit.text()
        if app_license.is_valid_key(key):
            app_license.save_license(key)
            self.licensed = True
            self.accept()
        else:
            self.feedback.setText(INVALID_KEY_FEEDBACK)
            self.key_edit.selectAll()
            self.key_edit.setFocus()


def show_license_dialog(parent=None, revoked=False):
    """Show the dialog. Returns True if the user entered a valid key,
    False if they clicked Quit (or closed the window)."""
    dlg = LicenseDialog(parent=parent, revoked=revoked)
    dlg.exec_()
    return dlg.licensed
