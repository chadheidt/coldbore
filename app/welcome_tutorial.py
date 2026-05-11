"""
First-launch welcome tutorial.

Multi-step modal dialog that shows once on the user's first launch (after
they've accepted the disclaimer and finished the setup wizard). Walks new
users through what Loadscope does, how to label range sessions, and how to
import. Final step points them at the Tools → How to Use Loadscope… menu
item for deeper details.

Acceptance is tracked in config (`tutorial_seen_version`) so users only see
this once. Bump the version constant if the tutorial content changes
substantively and we want users to see the new content.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import config as app_config
from version import APP_NAME


# Bump this if the tutorial content meaningfully changes and you want
# returning users to see the new version
TUTORIAL_VERSION = 1


# Each entry: (title, body)
STEPS = [
    (
        f"Welcome to {APP_NAME}",
        f"{APP_NAME} turns your range data into a recommended load — "
        "automatically.\n\n"
        "Drop in CSVs from your Garmin Xero chronograph and your "
        "BallisticX target groups. Loadscope organizes everything into "
        "your workbook, scores each load, and tells you which charge "
        "weight and seating depth shot best.\n\n"
        "This tour takes about 60 seconds. Click Next to start."
    ),
    (
        "Step 1 — Label your range sessions",
        "Before exporting CSVs, label each range session in your "
        "chronograph and target apps using this format:\n\n"
        "    <tag> <number> <powder>\n\n"
        "Examples:\n"
        "    P1 45.5 H4350     (Powder Ladder Load 1, 45.5 grains, H4350)\n"
        "    S7 0.070 H4350    (Seating Test 7, 0.070 inch jump, H4350)\n"
        "    CONFIRM-1 41.5 H4350    (Confirmation group, 41.5 grains, H4350)\n\n"
        "The first word is the row tag. P-tags are powder ladder rows, "
        "S-tags are seating depth rows, CONFIRM-tags are confirmation groups."
    ),
    (
        "Step 2 — Export your CSVs",
        "Garmin Xero (ShotView app):\n"
        "    Tap a session → Share → Save to Files →\n"
        "    save somewhere you can find it on your Mac\n"
        "    (Desktop, Downloads, or AirDrop from your phone all work).\n\n"
        "BallisticX:\n"
        "    Export each group as a CSV and get it to your Mac the same way.\n"
        "    Then RENAME the file to your label\n"
        "    (e.g., 'P1 45.5 H4350.csv').\n\n"
        "BallisticX's in-app label field is unreliable, so the FILENAME is "
        "what Loadscope reads. This is the most common new-user trip-up — "
        "remember to rename!"
    ),
    (
        "Step 3 — Drop CSVs onto Loadscope",
        "Two ways:\n\n"
        "Drag onto the Loadscope icon (in the Dock or Applications)\n"
        "    Loadscope launches if it isn't running, auto-imports the files, "
        "and opens your workbook in Excel. One step.\n\n"
        "Drag into the Loadscope window\n"
        "    Files stage. The status bar updates as you drop. Click "
        "Run Import when you've added everything from this range trip."
    ),
    (
        "Step 4 — A few things to know",
        "• You need at least 3 different charges (or jumps) before "
        "Loadscope picks a suggested winner. Plan for 5–8 loads in a "
        "powder ladder for cleaner results.\n\n"
        "• Close Excel BEFORE clicking Run Import. The script can't write "
        "to a workbook that Excel has open.\n\n"
        "• Loadscope creates a backup of your workbook before each import. "
        "You can restore via Tools → Restore From Backup.\n\n"
        "• When you finish a cycle, use Tools → Start New Cycle to wrap up "
        "and start fresh."
    ),
    (
        "You're all set",
        f"That's the basics. Drop your CSVs into the box on the {APP_NAME} "
        "window and you're off.\n\n"
        "For more details — label format, what each workbook tab does, tips, "
        "the safety reminder — open Tools → How to Use "
        f"{APP_NAME}… in the menu bar above this window. You can come back "
        "to that guide anytime.\n\n"
        "Happy load development. Click Got it to start using Loadscope."
    ),
]


class WelcomeTutorial(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Welcome to {APP_NAME}")
        self.setModal(True)
        self.setMinimumSize(640, 540)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        self.current_step = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 18)
        layout.setSpacing(14)

        # Step indicator
        self.indicator = QLabel()
        if self._t:
            self.indicator.setStyleSheet(
                f"color: {self._t.TEXT_TERTIARY}; "
                f"font-size: {self._t.FONT_SIZE_TINY}px; "
                f"text-transform: uppercase; letter-spacing: 1.5px; "
                f"font-weight: bold;"
            )
        layout.addWidget(self.indicator)

        # Stacked content
        self.stack = QStackedWidget()
        for (title, body) in STEPS:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(10)

            tl = QLabel(title)
            tl_font = QFont()
            tl_font.setPointSize(18)
            tl_font.setWeight(QFont.DemiBold)
            tl.setFont(tl_font)
            if self._t:
                tl.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
            page_layout.addWidget(tl)

            body_label = QLabel(body)
            body_label.setWordWrap(True)
            body_label.setTextFormat(Qt.PlainText)
            body_font = QFont()
            body_font.setPointSize(13)
            body_label.setFont(body_font)
            if self._t:
                body_label.setStyleSheet(
                    f"color: {self._t.TEXT_PRIMARY}; "
                    f"line-height: 1.5;"
                )
            body_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            page_layout.addWidget(body_label, stretch=1)

            self.stack.addWidget(page)
        layout.addWidget(self.stack, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        self.skip_btn = QPushButton("Skip tour")
        self.skip_btn.clicked.connect(self._finish)
        btn_row.addWidget(self.skip_btn)
        btn_row.addStretch(1)
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self._back)
        btn_row.addWidget(self.back_btn)
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("primary")
        self.next_btn.setDefault(True)
        self.next_btn.clicked.connect(self._next)
        btn_row.addWidget(self.next_btn)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        n = len(STEPS)
        self.indicator.setText(f"Step {self.current_step + 1} of {n}")
        self.stack.setCurrentIndex(self.current_step)
        self.back_btn.setEnabled(self.current_step > 0)
        if self.current_step == n - 1:
            self.next_btn.setText("Got it")
        else:
            self.next_btn.setText("Next")

    def _back(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._refresh()

    def _next(self):
        if self.current_step < len(STEPS) - 1:
            self.current_step += 1
            self._refresh()
        else:
            self._finish()

    def _finish(self):
        # Mark tutorial as seen so we don't show it again
        cfg = app_config.load_config()
        cfg["tutorial_seen_version"] = TUTORIAL_VERSION
        app_config.save_config(cfg)
        self.accept()


def needs_tutorial():
    """Return True if the user hasn't seen the current tutorial yet."""
    cfg = app_config.load_config()
    seen = cfg.get("tutorial_seen_version", 0)
    try:
        seen = int(seen)
    except (TypeError, ValueError):
        seen = 0
    return seen < TUTORIAL_VERSION


def show_tutorial(parent=None):
    dlg = WelcomeTutorial(parent)
    dlg.exec_()
