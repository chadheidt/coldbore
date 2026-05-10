"""License-entry dialog. Modal blocker on first launch (and after revocation).

Visual layout (top to bottom):
    1. Cold Bore icon
    2. "Cold Bore" wordmark + version
    3. Screenshot of the main window — so testers see what the app looks like
       even while locked out
    4. Brief description paragraph
    5. License key text field
    6. Quit / Unlock buttons

Without a valid key the user cannot reach the main window. The screenshot
is bundled into the .app via setup.py's data_files (Contents/Resources/).
"""

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

import license as app_license
from version import APP_NAME, APP_VERSION


PROMPT_TEXT = (
    "Cold Bore is in private beta. Each tester has a unique license key. "
    "Enter your key below to unlock the app — without a valid key the "
    "import workflow stays disabled."
)

REVOKED_TEXT = (
    "Your previous license key is no longer valid. Enter a new key to "
    "continue, or contact the developer."
)

DESCRIPTION_TEXT = (
    "Cold Bore turns Garmin Xero (chronograph) and BallisticX (target group) "
    "CSV exports into a structured load development workbook with composite "
    "scoring across SD, mean radius, and vertical dispersion. Drop the CSVs "
    "onto the app; Excel opens with the data ready to read."
)

INVALID_KEY_FEEDBACK = (
    "That key isn't recognized. Check for typos, or contact the developer."
)


def _resource_path(name):
    """Find a bundled resource file. Works in both the bundled .app
    (Contents/Resources/<name>) and dev mode (docs/assets/<name>).
    Returns a Path or None if not found."""
    # Bundled: <App.app>/Contents/MacOS/python -> ../Resources/<name>
    exe_dir = Path(sys.executable).resolve().parent
    if exe_dir.name == "MacOS":
        candidate = exe_dir.parent / "Resources" / name
        if candidate.exists():
            return candidate
    # Dev: walk up to the project root and check docs/assets/
    here = Path(__file__).resolve().parent
    for project_root in (here.parent, here.parent.parent):
        candidate = project_root / "docs" / "assets" / name
        if candidate.exists():
            return candidate
    return None


def _scaled_pixmap(name, max_w=None, max_h=None):
    """Load and optionally scale a bundled PNG. Returns None if not found."""
    path = _resource_path(name)
    if path is None:
        return None
    pix = QPixmap(str(path))
    if pix.isNull():
        return None
    if max_w and pix.width() > max_w:
        pix = pix.scaledToWidth(max_w, Qt.SmoothTransformation)
    if max_h and pix.height() > max_h:
        pix = pix.scaledToHeight(max_h, Qt.SmoothTransformation)
    return pix


class LicenseDialog(QDialog):
    """Modal dialog asking the user to enter a license key, with a preview
    of the app's main window so locked-out testers see what they'll get
    once they unlock."""

    def __init__(self, parent=None, revoked=False):
        super().__init__(parent)
        self.licensed = False

        self.setWindowTitle(f"{APP_NAME} — License Key")
        self.setModal(True)
        # Wider + taller than the bare dialog because we have the screenshot now
        self.setMinimumSize(640, 720)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(12)

        # ----- Icon + wordmark -----
        icon_pix = _scaled_pixmap("icon.png", max_w=72, max_h=72)
        if icon_pix is not None:
            icon_label = QLabel()
            icon_label.setPixmap(icon_pix)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        wordmark = QLabel(APP_NAME)
        f = QFont()
        f.setPointSize(22)
        f.setWeight(QFont.Bold)
        wordmark.setFont(f)
        wordmark.setAlignment(Qt.AlignCenter)
        if self._t:
            wordmark.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(wordmark)

        version = QLabel(f"version {APP_VERSION} — private beta")
        vf = QFont()
        vf.setPointSize(11)
        version.setFont(vf)
        version.setAlignment(Qt.AlignCenter)
        if self._t:
            version.setStyleSheet(f"color: {self._t.TEXT_TERTIARY};")
        layout.addWidget(version)

        # ----- Screenshot preview -----
        screenshot_pix = _scaled_pixmap("screenshot.png", max_w=520)
        if screenshot_pix is not None:
            shot = QLabel()
            shot.setPixmap(screenshot_pix)
            shot.setAlignment(Qt.AlignCenter)
            shot.setFrameShape(QFrame.Box)
            shot.setLineWidth(1)
            shot.setStyleSheet(
                "QLabel { border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0; }"
            )
            layout.addWidget(shot)

        # ----- Description -----
        desc = QLabel(DESCRIPTION_TEXT)
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        df = QFont()
        df.setPointSize(11)
        desc.setFont(df)
        if self._t:
            desc.setStyleSheet(f"color: {self._t.TEXT_SECONDARY}; padding: 6px 8px;")
        layout.addWidget(desc)

        # ----- Key entry prompt + field -----
        prompt = QLabel(REVOKED_TEXT if revoked else PROMPT_TEXT)
        prompt.setWordWrap(True)
        if self._t:
            prompt.setStyleSheet(f"color: {self._t.TEXT_PRIMARY}; padding-top: 8px;")
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
        self.feedback.setStyleSheet("color: #d97706; min-height: 18px;")
        layout.addWidget(self.feedback)

        # ----- Buttons -----
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
