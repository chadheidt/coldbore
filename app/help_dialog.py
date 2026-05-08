"""
Tools → How to Use Cold Bore…

A friendly in-app help dialog that covers the basics: label format, workflow,
workbook tabs, and the minimum-data requirement for scoring. Designed for new
users who installed the app and aren't sure what to do next.

The text is structured so users can scroll through and find what they need.
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

from version import APP_NAME


HELP_TEXT = """\
QUICK START

1. Label your range sessions before exporting CSVs.
   Use the format:    <tag> <number> <powder>
   Examples:
       P1 45.5 H4350         (Powder Ladder Load 1, 45.5 grains, H4350)
       S7 0.070 H4350        (Seating Test 7, 0.070 inch jump)
       CONFIRM-1 41.5 H4350  (Confirmation group at 41.5 grains)

   • Garmin Xero: label the session inside the ShotView app before exporting.
   • BallisticX: rename the exported CSV file itself to your label
     (e.g. "P1 45.5 H4350.csv") — BallisticX's in-app label field is
     unreliable, so the FILENAME is what Cold Bore reads.

2. Drag your CSVs onto Cold Bore.
   Two ways:
       • Drag onto the Cold Bore icon (Dock or Applications) — auto-imports.
       • Drag into the Cold Bore window — you click Run Import when ready.

3. Cold Bore opens your workbook with everything filled in.
   Update the green Test Session bar (date / temperature / notes), save (Cmd+S).


HOW THE LABELS WORK

Cold Bore reads the FIRST word of your label as the row tag, the FIRST
number as the charge weight or jump distance, and the next word as the
powder name.

   <tag>     The row in the workbook this load belongs to.
             P1 through P10  =  Powder Ladder rows
             S1 through S10  =  Seating Depth rows
             CONFIRM-1+      =  Confirmation groups (free-form)

   <number>  For P-tags: powder charge in grains.
             For S-tags: bullet jump distance in inches.

   <powder>  The powder name (optional). If included, it auto-fills the
             Powder field in the Load Components info bar.


WHAT'S IN THE WORKBOOK

   Load Log         Powder ladder. Charge weight per row. Shots, Avg, SD,
                    Group, Vertical, Mean Radius all auto-populate.
                    The red SUGGESTED CHARGE bar at top picks the winning
                    charge based on a composite score.

   Seating Depth    Same layout, but jump distance varies instead of charge.
                    Red SUGGESTED JUMP bar picks the winning seating depth.

   Charts           Where the scoring math runs. You can tune the weights
                    here (default 30 % velocity spread, 20 % SD, 20 % mean
                    radius, 30 % vertical).

   Ballistics       DOPE tables for confirmed loads (manual entry).

   Load Library     A list of confirmed loads you've kept after testing.

   Garmin Xero      Auto-populated from your Garmin CSV imports — shows
   Import           what Cold Bore actually parsed (handy for debugging).

   BallisticX       Same idea for BallisticX CSV imports.
   Import

   After Range Day  A printable single-page cheat sheet covering the basic
                    workflow.


MINIMUM DATA REQUIREMENT

Cold Bore's scoring uses a sliding window of 3 consecutive charges to find
a velocity node, so you need to test AT LEAST 3 loads (different charge
weights) before the SUGGESTED CHARGE bar will pick a winner.

   • 1–2 loads:  Cold Bore shows the data but no suggested winner.
   • 3 loads:    Suggested winner picks the middle charge of the three.
   • 4+ loads:   Multiple sliding windows are evaluated; cleaner result.

For best results, plan a powder ladder with 5–8 loads spaced about
0.3–0.5 grains apart.

The same applies to Seating Depth — at least 3 different jump distances
before the SUGGESTED JUMP bar will recommend one.


TIPS THAT WILL SAVE YOU TIME

• Close Excel BEFORE you click Run Import. The script can't write to a
  workbook that Excel has open.

• To import a whole range trip's worth of files at once, select all the
  CSVs in Finder (Cmd-click each) and drag the WHOLE batch onto the Cold
  Bore icon. Cold Bore waits 2 seconds after the last file lands, then
  imports them all together.

• If you change your mind about an import, just close Cold Bore — the
  files in the import folders won't be re-processed until you click
  Run Import again.

• If something goes wrong, look at .backups/ in your project folder.
  Cold Bore saves recent versions of your workbook before each import
  (count is configurable in Tools → Settings…). Or use Tools → Restore
  From Backup… to roll back from inside the app.

• If a friend has a different chronograph (LabRadar, MagnetoSpeed, etc.),
  contact the developers (Tools → About → click here) and send a sample
  CSV — we'll add support.


SAFETY REMINDER

Cold Bore is an analysis tool. It does NOT provide load data. Always
cross-reference loads against published reloading manuals from powder,
bullet, and cartridge manufacturers. Watch for pressure signs. Start
below maximum loads and work up. See Tools → View Disclaimer for the
full text.
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} — How to Use")
        self.setModal(False)  # non-modal — users can keep it open while they work
        self.setMinimumSize(640, 580)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(10)

        # Title
        title = QLabel(f"How to use {APP_NAME}")
        f = QFont()
        f.setPointSize(18)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        if self._t:
            title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(title)

        sub = QLabel(
            "A short guide to labels, workflow, and what's in the workbook."
        )
        if self._t:
            sub.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        layout.addWidget(sub)

        # Body — scrollable text panel
        body = QLabel(HELP_TEXT)
        body.setTextFormat(Qt.PlainText)
        body.setWordWrap(True)
        body_font = QFont()
        body_font.setFamily("Menlo")
        body_font.setPointSize(11)
        body.setFont(body_font)
        if self._t:
            body.setStyleSheet(
                f"color: {self._t.TEXT_PRIMARY}; "
                f"background-color: {self._t.BG_INPUT}; "
                f"padding: 12px; border-radius: 6px;"
            )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        scroll.setFrameShape(QScrollArea.NoFrame)
        layout.addWidget(scroll, stretch=1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Got it")
        close_btn.setObjectName("primary")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)


def show_help(parent=None):
    dlg = HelpDialog(parent)
    dlg.exec_()
