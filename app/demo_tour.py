"""Demo tour — guided walk-through that drives Excel via AppleScript while
Loadscope shows a narration panel beside it.

User clicks "Replay the Demo Tour" (from the Workbook menu, or auto-fires once
on first launch in demo mode). Loadscope positions itself on the left half of
the screen, positions Excel on the right half with the demo workbook open,
then steps through six tour stops. Each stop activates a sheet, scrolls to an
interesting range, and shows a paragraph of narration in the panel. User
controls pacing via Next / Previous / Pause / Skip buttons.

The Pocket Range Card stop is special: it generates the printable HTML card
via pocket_card.py and opens it in the browser so the user sees the real
printable artifact rather than a workbook tab.

Module is self-contained: subclass-free QWidget + a TourController that wraps
osascript subprocess calls. No PyQt5 dependency on the controller, so it's
unit-testable.
"""

import os
import subprocess
import sys

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    # Allow module import for unit tests without PyQt5
    Qt = QTimer = QFont = None
    QHBoxLayout = QLabel = QProgressBar = QPushButton = QSizePolicy = QVBoxLayout = QWidget = None

try:
    from . import theme as _theme
except ImportError:
    try:
        import theme as _theme
    except ImportError:
        _theme = None


# Tour content — each stop is a dict with the sheet to activate, what range to
# select/scroll into view, the narration shown in the panel, and how long the
# Next button stays disabled to enforce a comprehension floor.
TOUR_STOPS = [
    {
        "title": "Load Log — your powder ladder",
        "sheet": "Load Log",
        "select_range": "A1:P25",
        "narration": (
            "This is the Load Log. You drop your range-day CSVs onto Loadscope "
            "and it fills in every velocity, group size, and SD from your "
            "chronograph and target software. The highlighted suggested winner "
            "shows the charge that scored best across all the metrics — "
            "no manual math, no spreadsheet wrangling."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Charts — heat-mapped scoring",
        "sheet": "Charts",
        "select_range": "A1:Q25",
        "narration": (
            "Here's where the scoring lives. Every candidate load gets a "
            "color-coded score for vertical dispersion, velocity, SD, and group "
            "size — green is best, red is worst. The composite winner at the "
            "bottom uses adjustable weights you can tune to match your goal "
            "(group size, low SD, vertical, or a mix)."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Seating Depth — find your jump",
        "sheet": "Seating Depth",
        "select_range": "A1:P30",
        "narration": (
            "Once you've found your charge, this tab helps you find your "
            "bullet jump — the distance between the bullet and the rifling. "
            "Same workflow as Load Log: drop in your CSVs and it scores each "
            "jump distance. The winner becomes your final OAL for the season."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Ballistics — your DOPE table",
        "sheet": "Ballistics",
        "select_range": "A1:K30",
        "narration": (
            "Your rifle setup and DOPE table lives here. After you've confirmed "
            "your load, you fill in the elevation and wind values from 100 yards "
            "all the way out to 1000. Then you get something genuinely cool — "
            "click 'Next' to see it."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Range Card — your printable DOPE",
        "sheet": "Range Card",
        "select_range": "A1:J17",
        "narration": (
            "This is your Pocket Range Card. Loadscope builds it automatically "
            "from your Ballistics tab data — rifle, bullet, charge, velocity "
            "across the top, then your full DOPE table from 100 to 1000 yards. "
            "Click 'Print Pocket Range Card' from the Ballistics tab to open "
            "the polished printable version in your browser — print it on "
            "cardstock or save as a 4×6 PDF. It folds into your shirt pocket "
            "for the firing line."
        ),
        "min_dwell_seconds": 10,
        "special": None,  # Card preview lives on this tab — no need to open HTML
    },
    {
        "title": "Load Library — your winners over time",
        "sheet": "Load Library",
        "select_range": "A1:P25",
        "narration": (
            "Every winning load you confirm gets saved here when you click "
            "'Save Suggested Load to Library.' Build it up over the years — "
            "every cartridge, every rifle, every winning recipe in one place. "
            "Next season starts where this season ended."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
]


# Screen layout — assumes 1440x900 main display. The TourController calls
# screen-dimensions detection at runtime to adapt to other display sizes.
DEFAULT_SCREEN_WIDTH = 1440
DEFAULT_SCREEN_HEIGHT = 900
MENU_BAR_HEIGHT = 25  # macOS menu bar


def get_bundled_demo_workbook_path():
    """Return the absolute path to the bundled demo workbook, or None if not found.

    Looks in three candidate locations (dev vs py2app bundle vs older layouts):
        1. app/resources/Loadscope - Demo Workbook.xlsx (dev tree)
        2. Contents/Resources/Loadscope - Demo Workbook.xlsx (py2app .app bundle)
        3. ../Resources/Loadscope - Demo Workbook.xlsx (alt py2app layout)
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "resources", "Loadscope - Demo Workbook.xlsx"),
        os.path.normpath(os.path.join(here, "..", "Resources",
                                       "Loadscope - Demo Workbook.xlsx")),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class TourController:
    """Drives Excel through tour stops via osascript. No PyQt5 dependency.

    Each method runs an AppleScript and returns either the script's stdout or
    an empty string on failure. Failures are non-fatal — the tour can continue
    even if one step's positioning didn't take.

    If `workbook_path` is None, falls back to the bundled demo workbook so the
    tour can run even before the user has selected a project workbook.
    """

    def __init__(self, workbook_path):
        if not workbook_path or not os.path.isfile(workbook_path):
            fallback = get_bundled_demo_workbook_path()
            workbook_path = fallback or workbook_path
        self.workbook_path = workbook_path
        self._screen = self._detect_screen()

    def _detect_screen(self):
        """Return (width, height) of the main display, or defaults on failure."""
        try:
            out = subprocess.run(
                ["osascript", "-e",
                 'tell application "Finder" to get bounds of window of desktop'],
                capture_output=True, text=True, timeout=5,
            )
            parts = [int(p.strip()) for p in out.stdout.strip().split(",")]
            if len(parts) == 4:
                return parts[2], parts[3]
        except Exception:
            pass
        return DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT

    def _run_script(self, script, timeout=15):
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=timeout,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except Exception:
            return ""

    def ensure_workbook_open(self):
        """Open the demo workbook in Excel if not already open.

        Tries Excel's native `open workbook` verb first (most reliable). Falls
        back to shell `open -a Microsoft Excel <path>` if AppleScript times out
        on a cold start.
        """
        script = f'''
            with timeout of 30 seconds
                tell application "Microsoft Excel"
                    activate
                    try
                        if (count of workbooks) > 0 then
                            -- check if our workbook is already active
                            if (name of active workbook) is equal to "{os.path.basename(self.workbook_path)}" then
                                return "already_open"
                            end if
                        end if
                        open workbook workbook file name "{self.workbook_path}"
                        delay 1
                        return "opened"
                    on error errMsg
                        return "ERROR:" & errMsg
                    end try
                end tell
            end timeout
        '''
        result = self._run_script(script, timeout=35)
        if result and not result.startswith("ERROR"):
            return True
        # Fallback: shell open
        try:
            subprocess.run(["open", "-a", "Microsoft Excel", self.workbook_path],
                           timeout=5, capture_output=True)
            # Give Excel time to load
            import time
            for _ in range(12):
                time.sleep(1)
                check = self._run_script(
                    'tell application "Microsoft Excel" to count of workbooks',
                    timeout=5,
                )
                if check and int(check or "0") > 0:
                    return True
        except Exception:
            pass
        return False

    def position_excel_right_half(self):
        """Position Excel's main window to the right half of the screen."""
        w, h = self._screen
        x = w // 2
        y = MENU_BAR_HEIGHT
        width = w // 2
        height = h - MENU_BAR_HEIGHT
        script = f'''
            tell application "Microsoft Excel" to activate
            delay 0.3
            tell application "System Events"
                tell process "Microsoft Excel"
                    if (count of windows) > 0 then
                        repeat with win in windows
                            if (name of win) is not "" then
                                set position of win to {{{x}, {y}}}
                                delay 0.2
                                set size of win to {{{width}, {height}}}
                                exit repeat
                            end if
                        end repeat
                    end if
                end tell
            end tell
        '''
        self._run_script(script)

    def goto_stop(self, stop):
        """Activate a tour stop — switch sheet, scroll, optionally select range."""
        sheet = stop["sheet"]
        select_range = stop.get("select_range")
        scripts = [
            f'tell application "Microsoft Excel" to activate object sheet "{sheet}" of active workbook',
        ]
        if select_range:
            scripts.append(
                f'tell application "Microsoft Excel" to select (range "{select_range}" of active sheet)'
            )
        # Always scroll to row 1 for a consistent top-anchored view
        scripts.append(
            'tell application "Microsoft Excel" to set ScrollRow of active window to 1'
        )
        for s in scripts:
            self._run_script(s, timeout=8)

        special = stop.get("special")
        if special == "open_pocket_range_card":
            self._open_pocket_range_card()

    def _open_pocket_range_card(self):
        """Generate the Pocket Range Card HTML and open in browser."""
        try:
            # Import here so module is importable for tests without all deps
            from . import pocket_card  # noqa: F401
            generator = pocket_card.generate_pocket_card
        except ImportError:
            try:
                import pocket_card
                generator = pocket_card.generate_pocket_card
            except ImportError:
                return
        try:
            generator(self.workbook_path, open_after=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# PyQt5 panel — only loaded when PyQt5 is importable. The widget below is the
# "Demo Tour" sidebar Loadscope shows on the left half of the screen during a
# tour. It owns the TourController and orchestrates the step-by-step advance.
# ---------------------------------------------------------------------------


if QWidget is not None:

    class DemoTourPanel(QWidget):
        """Left-half sidebar that narrates the tour and controls pacing.

        Constructor takes the workbook path so the controller can drive Excel
        on the right half. The panel is non-modal; user can pause / skip /
        navigate via the buttons. End of tour shows a "Purchase a License"
        CTA prominent enough to convert.
        """

        def __init__(self, workbook_path, on_purchase=None, parent=None):
            super().__init__(parent)
            self._stops = TOUR_STOPS
            self._index = 0
            self._controller = TourController(workbook_path)
            self._on_purchase = on_purchase  # callback when user clicks Purchase
            self._dwell_timer = QTimer(self)
            self._dwell_timer.setSingleShot(True)
            self._dwell_timer.timeout.connect(self._on_dwell_complete)
            self._paused = False

            self.setWindowTitle("Loadscope — Demo Tour")
            self.setMinimumSize(620, 720)

            self._build_ui()
            # Don't auto-start; caller invokes start() so they can position
            # both windows first.

        # --- UI construction ----------------------------------------------------
        def _build_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(28, 24, 28, 22)
            layout.setSpacing(14)

            # Header
            self.title_label = QLabel("")
            tf = QFont()
            tf.setPointSize(22)
            tf.setWeight(QFont.DemiBold)
            self.title_label.setFont(tf)
            self.title_label.setWordWrap(True)
            if _theme:
                self.title_label.setStyleSheet(f"color: {_theme.TEXT_PRIMARY};")
            layout.addWidget(self.title_label)

            # Progress indicator + bar
            self.progress_label = QLabel("")
            pf = QFont()
            pf.setPointSize(11)
            self.progress_label.setFont(pf)
            if _theme:
                self.progress_label.setStyleSheet(f"color: {_theme.TEXT_SECONDARY};")
            layout.addWidget(self.progress_label)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self._stops))
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(6)
            layout.addWidget(self.progress_bar)

            # Narration body
            self.narration_label = QLabel("")
            nf = QFont()
            nf.setPointSize(14)
            self.narration_label.setFont(nf)
            self.narration_label.setWordWrap(True)
            self.narration_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.narration_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            if _theme:
                self.narration_label.setStyleSheet(
                    f"color: {_theme.TEXT_PRIMARY}; "
                    f"background-color: {_theme.BG_ELEVATED}; "
                    f"padding: 22px; border-radius: 10px; line-height: 1.5;"
                )
            layout.addWidget(self.narration_label, stretch=1)

            # End-of-tour CTA (hidden until last step done)
            self.cta_label = QLabel(
                "Liked what you saw? Loadscope is ready to use with YOUR data."
            )
            cf = QFont()
            cf.setPointSize(15)
            cf.setWeight(QFont.DemiBold)
            self.cta_label.setFont(cf)
            self.cta_label.setWordWrap(True)
            self.cta_label.setAlignment(Qt.AlignCenter)
            if _theme:
                self.cta_label.setStyleSheet(f"color: {_theme.ACCENT};")
            self.cta_label.hide()
            layout.addWidget(self.cta_label)

            self.purchase_btn = QPushButton("Purchase a License")
            self.purchase_btn.setObjectName("primary")
            self.purchase_btn.setMinimumHeight(48)
            pbf = QFont()
            pbf.setPointSize(14)
            pbf.setWeight(QFont.DemiBold)
            self.purchase_btn.setFont(pbf)
            self.purchase_btn.clicked.connect(self._on_purchase_clicked)
            self.purchase_btn.hide()
            layout.addWidget(self.purchase_btn)

            # Button row
            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)

            self.prev_btn = QPushButton("← Previous")
            self.prev_btn.clicked.connect(self.previous_stop)
            btn_row.addWidget(self.prev_btn)

            self.pause_btn = QPushButton("Pause")
            self.pause_btn.clicked.connect(self._toggle_pause)
            btn_row.addWidget(self.pause_btn)

            self.skip_btn = QPushButton("Skip tour")
            self.skip_btn.clicked.connect(self.skip)
            btn_row.addWidget(self.skip_btn)

            btn_row.addStretch(1)

            self.next_btn = QPushButton("Next →")
            self.next_btn.setObjectName("primary")
            self.next_btn.setMinimumWidth(120)
            self.next_btn.clicked.connect(self.next_stop)
            btn_row.addWidget(self.next_btn)

            layout.addLayout(btn_row)

        # --- public API ---------------------------------------------------------
        def start(self):
            """Open the workbook, position Excel, render the first stop."""
            ok = self._controller.ensure_workbook_open()
            if ok:
                self._controller.position_excel_right_half()
            self._render_stop(0)

        def next_stop(self):
            if self._index < len(self._stops) - 1:
                self._render_stop(self._index + 1)
            else:
                self._show_end_of_tour()

        def previous_stop(self):
            if self._index > 0:
                self._render_stop(self._index - 1)

        def skip(self):
            self._dwell_timer.stop()
            self._show_end_of_tour()

        # --- internals ----------------------------------------------------------
        def _render_stop(self, index):
            self._index = index
            stop = self._stops[index]
            self.title_label.setText(stop["title"])
            self.progress_label.setText(f"Step {index + 1} of {len(self._stops)}")
            self.progress_bar.setValue(index + 1)
            self.narration_label.setText(stop["narration"])

            # Drive Excel to this stop
            self._controller.goto_stop(stop)

            # Enforce min dwell — disable Next until timer fires
            self.next_btn.setEnabled(False)
            self.next_btn.setText(f"Next → (wait {stop['min_dwell_seconds']}s)")
            self._dwell_timer.start(stop["min_dwell_seconds"] * 1000)

            # Previous always available except on first stop
            self.prev_btn.setEnabled(index > 0)

        def _on_dwell_complete(self):
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Next →")

        def _toggle_pause(self):
            self._paused = not self._paused
            if self._paused:
                self.pause_btn.setText("Resume")
                self._dwell_timer.stop()
                self.next_btn.setEnabled(False)
                self.next_btn.setText("Next → (paused)")
            else:
                self.pause_btn.setText("Pause")
                # Resume timer with remaining time (approximate — restart full window)
                stop = self._stops[self._index]
                self._dwell_timer.start(stop["min_dwell_seconds"] * 1000)
                self.next_btn.setText(f"Next → (wait {stop['min_dwell_seconds']}s)")

        def _show_end_of_tour(self):
            self.title_label.setText("Tour complete")
            self.progress_label.setText(f"Step {len(self._stops)} of {len(self._stops)}")
            self.progress_bar.setValue(len(self._stops))
            self.narration_label.setText(
                "That's the full tour. The demo workbook you just walked through "
                "is fully featured — only thing it doesn't have is your data. "
                "Purchase a license to import your own Garmin Xero and BallisticX "
                "CSVs and start building your own load development library."
            )
            self.next_btn.hide()
            self.prev_btn.hide()
            self.pause_btn.hide()
            self.skip_btn.setText("Close")
            self.cta_label.show()
            self.purchase_btn.show()

        def _on_purchase_clicked(self):
            if self._on_purchase:
                self._on_purchase()


def show_tour(workbook_path, parent=None, on_purchase=None):
    """Convenience entry point — creates and starts the panel."""
    if QWidget is None:
        raise RuntimeError("PyQt5 not available")
    panel = DemoTourPanel(workbook_path, on_purchase=on_purchase, parent=parent)
    panel.show()
    panel.start()
    return panel
