"""First-launch splash dialog.

Shown ONCE on the very first launch of Loadscope (or when a license is missing
and the splash hasn't been dismissed yet). Offers three choices:

    1. Try the Free Demo  — main CTA. Opens demo mode + auto-fires guided tour.
    2. Enter License Key  — opens the existing license dialog.
    3. Purchase a License — opens the website in the user's default browser.

The dialog returns one of these choice strings via its `choice` attribute:
    'demo'      — user picked Try the Free Demo
    'license'   — user picked Enter License Key (caller opens license dialog)
    'purchase'  — user picked Purchase (caller already opened the browser; the
                  splash stays open so user can also choose Demo or License)
    'cancel'    — user closed the dialog without choosing (rare; Esc key)

After 'demo' or 'license' (with a successful key entry), the caller calls
license.mark_first_launch_splash_seen() so this splash never re-appears.
"""

import webbrowser

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

try:
    from . import theme as _theme
    from . import license as _license
except ImportError:
    try:
        import theme as _theme
        import license as _license
    except ImportError:
        _theme = None
        _license = None


CHOICE_DEMO = "demo"
CHOICE_LICENSE = "license"
CHOICE_PURCHASE = "purchase"
CHOICE_CANCEL = "cancel"


class FirstLaunchSplash(QDialog):
    """Modal splash shown on first launch. Caller routes based on `self.choice`."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.choice = CHOICE_CANCEL  # default if user dismisses via Esc/close
        self.setWindowTitle("Welcome to Loadscope™")
        self.setModal(True)
        self.setMinimumSize(560, 620)
        self.setMaximumWidth(640)

        if _theme:
            self.setStyleSheet(
                f"QDialog {{ background-color: {_theme.BG_BASE}; }}"
            )

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 38, 40, 34)
        layout.setSpacing(16)

        # Logo (optional — fallback gracefully if missing)
        logo_label = self._build_logo()
        if logo_label is not None:
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)

        # Headline
        title = QLabel("Welcome to Loadscope™")
        tf = QFont()
        tf.setPointSize(26)
        tf.setWeight(QFont.DemiBold)
        title.setFont(tf)
        title.setAlignment(Qt.AlignCenter)
        if _theme:
            title.setStyleSheet(f"color: {_theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        subtitle = QLabel(
            "Precision rifle load development, automated.\n"
            "Drop your range-day CSVs — get a scored powder ladder, "
            "seating depth, and printable Pocket Range Card."
        )
        sf = QFont()
        sf.setPointSize(13)
        subtitle.setFont(sf)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        if _theme:
            subtitle.setStyleSheet(f"color: {_theme.TEXT_SECONDARY};")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        # --- Three action buttons (vertical stack, big targets) ---
        self.demo_btn = QPushButton("Try the Free Demo")
        self.demo_btn.setObjectName("primary")
        self.demo_btn.setMinimumHeight(56)
        demo_font = QFont()
        demo_font.setPointSize(15)
        demo_font.setWeight(QFont.DemiBold)
        self.demo_btn.setFont(demo_font)
        self.demo_btn.clicked.connect(self._pick_demo)
        layout.addWidget(self.demo_btn)

        demo_sub = QLabel(
            "Walk through a fully-populated 6.5 Creedmoor workbook. "
            "No CSV import yet."
        )
        demo_sub.setAlignment(Qt.AlignCenter)
        demo_sub.setWordWrap(True)
        if _theme:
            demo_sub.setStyleSheet(f"color: {_theme.TEXT_TERTIARY};")
        dsf = QFont()
        dsf.setPointSize(11)
        demo_sub.setFont(dsf)
        layout.addWidget(demo_sub)

        layout.addSpacing(10)

        # Secondary actions side-by-side
        row = QHBoxLayout()
        row.setSpacing(12)

        self.license_btn = QPushButton("Enter License Key")
        self.license_btn.setMinimumHeight(44)
        lf = QFont()
        lf.setPointSize(13)
        self.license_btn.setFont(lf)
        self.license_btn.clicked.connect(self._pick_license)
        row.addWidget(self.license_btn)

        # v0.14: third button asks for beta access during the beta period
        # (Chad picked option B 2026-05-14). When commerce flips on, the
        # label changes back to "Purchase a License" — see
        # [[loadscope-commerce-flip-on]] memory entry for the full checklist.
        self.purchase_btn = QPushButton("Request Beta Access")
        self.purchase_btn.setMinimumHeight(44)
        self.purchase_btn.setFont(lf)
        self.purchase_btn.clicked.connect(self._pick_purchase)
        row.addWidget(self.purchase_btn)

        layout.addLayout(row)

        layout.addStretch(1)

        # Footer disclaimer
        footer = QLabel(
            "Loadscope works with Garmin Xero (chronograph) and BallisticX "
            "(target group) CSVs."
        )
        ff = QFont()
        ff.setPointSize(10)
        footer.setFont(ff)
        footer.setAlignment(Qt.AlignCenter)
        footer.setWordWrap(True)
        if _theme:
            footer.setStyleSheet(f"color: {_theme.TEXT_TERTIARY};")
        layout.addWidget(footer)

    def _build_logo(self):
        """Return a QLabel containing the Loadscope icon, or None if not found."""
        import os
        import sys
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = []
        # py2app: __file__ is inside Contents/Resources/lib/pythonXX.zip;
        # resolve the real Contents/Resources/ via sys.executable first
        # (proven-good pattern from setup_wizard.find_bundled_template()).
        if getattr(sys, "frozen", False):
            try:
                exe = os.path.abspath(sys.executable)
                candidates.append(os.path.join(
                    os.path.dirname(os.path.dirname(exe)), "Resources", "icon.png"))
            except (OSError, ValueError):
                pass
        candidates += [
            os.path.join(here, "resources", "icon.png"),
            os.path.normpath(os.path.join(here, "..", "docs", "assets", "icon.png")),
            os.path.normpath(os.path.join(here, "..", "Resources", "icon.png")),
        ]
        for path in candidates:
            if os.path.isfile(path):
                pix = QPixmap(path)
                if not pix.isNull():
                    scaled = pix.scaled(
                        96, 96,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation,
                    )
                    lbl = QLabel()
                    lbl.setPixmap(scaled)
                    return lbl
        return None

    # --- button handlers ---------------------------------------------------
    def _pick_demo(self):
        self.choice = CHOICE_DEMO
        self.accept()

    def _pick_license(self):
        self.choice = CHOICE_LICENSE
        self.accept()

    def _pick_purchase(self):
        """Open the website in the browser. Splash STAYS OPEN so the user can
        still pick Demo or Enter License after coming back."""
        self.choice = CHOICE_PURCHASE
        purchase_url = (
            _license.PURCHASE_URL if _license else "https://loadscope.app/"
        )
        webbrowser.open(purchase_url)
        # Do NOT call accept() — keep the dialog open. The user might come
        # back and pick demo or license. They can also close manually.


def show_splash_if_needed(parent=None):
    """Show the splash if license.should_show_first_launch_splash() is True.

    Returns the user's choice string (CHOICE_DEMO / CHOICE_LICENSE /
    CHOICE_PURCHASE / CHOICE_CANCEL), or None if no splash was needed
    (already-licensed or already-dismissed).
    """
    if _license is None or not _license.should_show_first_launch_splash():
        return None
    dlg = FirstLaunchSplash(parent=parent)
    dlg.exec_()
    return dlg.choice
