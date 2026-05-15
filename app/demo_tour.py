"""Demo tour — a single self-contained guided walk-through window.

v0.14.5 (Path B): the demo is now ONE Loadscope window that shows a
narration band on top and a pre-rendered, pixel-perfect image of each
workbook tab / the pretty Pocket Range Card below it. There is NO Excel,
NO browser, NO window positioning, and NO macOS permission prompt at
runtime — the demo works even if the user doesn't have Excel installed.
The images are produced at build time by tools/render_demo_screenshots.py
(developer Mac with Excel) and shipped in Contents/Resources/
demo_screenshots/.

User reaches it via "Replay the Demo Tour" (Workbook menu) or the
first-launch splash. DemoTourPanel steps through TOUR_STOPS with
Next / Previous / Pause / Skip and a min-dwell timer.

The old Excel-driven path (TourController + get_bundled_demo_workbook_path
+ goto_stop) is retained below only because get_bundled_demo_workbook_path
is still used by main.py for the in-app Print / Pocket-Card actions.
TourController itself is now DEAD for the demo (kept to avoid churn /
breaking its unit tests; remove in a dedicated cleanup pass).
"""

import os
import subprocess
import sys

try:
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont, QPixmap
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
    Qt = QTimer = QFont = QPixmap = None
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
        "image": "01-load-log.png",
        "sheet": "Load Log",
        "select_range": "A1:P25",
        "narration": (
            "This is the Load Log — every powder charge you tested, one row "
            "each. Loadscope filled in your velocities and group sizes from "
            "the CSVs you dropped in. The 🥇 medal marks Loadscope's "
            "suggested winner: the charge that scored best across velocity "
            "SD, group size, mean radius, and vertical dispersion."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Charts — heat-mapped scoring",
        "image": "02-charts.png",
        "sheet": "Charts",
        "select_range": "A1:Q25",
        "narration": (
            "Charts shows you HOW Loadscope picked the winner. Each load "
            "gets graded across four metrics — green is best, red is worst — "
            "then a composite score combines all four. You can change the "
            "weights up top if you care more about one metric (say, group "
            "size for hunting, or SD for long range)."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Seating Depth — find your jump",
        "image": "03-seating-depth.png",
        "sheet": "Seating Depth",
        "select_range": "A1:P30",
        "narration": (
            "Once you've picked your powder charge, the next test is seating "
            "depth — how far the bullet sits from the rifling. Same workflow "
            "as Load Log: each row is a different jump distance, and "
            "Loadscope ranks them. The winning jump becomes your final "
            "cartridge length."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Ballistics — your DOPE table",
        "image": "04-ballistics.png",
        "sheet": "Ballistics",
        "select_range": "A1:K30",
        # ⚠️ PLACEHOLDER NARRATION — UPDATE WHEN v0.15 BALLISTIC SOLVER SHIPS.
        # Today the user types every DOPE value manually. v0.15
        # ([[loadscope-ballistic-solver-v015]]) auto-predicts elevation
        # and wind from BC + atmospherics. Rewrite this stop to mention
        # the predicted DOPE + the predicted-vs-confirmed visual
        # distinction. See [[loadscope-tour-narration-v015-update]].
        "narration": (
            "Once you've nailed down your load, the Ballistics tab is where "
            "you record your DOPE — the elevation and wind clicks at every "
            "distance. Type in what you dialed at the range; Loadscope "
            "auto-converts to clicks. Click 'Next' to see what we do with "
            "all that data."
        ),
        "min_dwell_seconds": 8,
        "special": None,
    },
    {
        "title": "Pocket Range Card — printable DOPE",
        "image": "05-pocket-card.png",
        "sheet": "Ballistics",  # stays on Ballistics; opens HTML in browser
        "select_range": None,
        "narration": (
            "This is your Pocket Range Card — a clean 4×6 DOPE card "
            "Loadscope builds straight from your load. In the full app one "
            "click prints it to cardstock or saves it as a PDF; it folds "
            "into your shirt pocket for the firing line. No more squinting "
            "at notes on your phone in the wind."
        ),
        "min_dwell_seconds": 10,
        "special": None,
    },
    {
        "title": "Load Library — your winners over time",
        "image": "06-load-library.png",
        "sheet": "Load Library",
        "select_range": "A1:P25",
        "narration": (
            "Every winning load you confirm gets saved here with one click — "
            "'Save Suggested Load to Library' on the Charts tab. Build it up "
            "over the years: every cartridge, every rifle, every winning "
            "recipe in one place. Next season picks up where this one left off."
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
    fname = "Loadscope - Demo Workbook.xlsx"
    here = os.path.dirname(os.path.abspath(__file__))
    # py2app loads modules from Contents/Resources/lib/pythonXX.zip, so
    # __file__-relative paths land INSIDE the zip and miss the real
    # Contents/Resources/ where DATA_FILES live. Resolve via sys.executable
    # (Contents/MacOS/<exe> -> ../Resources/) — the proven-good pattern
    # from setup_wizard.find_bundled_template().
    if getattr(sys, "frozen", False):
        try:
            exe = os.path.abspath(sys.executable)
            res = os.path.join(os.path.dirname(os.path.dirname(exe)),
                               "Resources", fname)
            if os.path.isfile(res):
                return res
        except (OSError, ValueError):
            pass
    candidates = [
        os.path.join(here, "resources", fname),                          # dev tree
        os.path.normpath(os.path.join(here, "..", "Resources", fname)),   # legacy
        os.path.normpath(os.path.join(here, "..", "..", "Resources", fname)),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def get_demo_screenshot(filename):
    """Absolute path to a bundled demo screenshot (Path B), or None.

    Same py2app pitfall as get_bundled_demo_workbook_path: __file__ is
    inside Contents/Resources/lib/pythonXX.zip in the .app, so resolve
    the real Contents/Resources/demo_screenshots/ via sys.executable.
    Build-time tool: tools/render_demo_screenshots.py.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        try:
            exe = os.path.abspath(sys.executable)
            res = os.path.join(os.path.dirname(os.path.dirname(exe)),
                               "Resources", "demo_screenshots", filename)
            if os.path.isfile(res):
                return res
        except (OSError, ValueError):
            pass
    candidates = [
        os.path.join(here, "resources", "demo_screenshots", filename),
        os.path.normpath(os.path.join(here, "..", "Resources",
                                      "demo_screenshots", filename)),
        os.path.normpath(os.path.join(here, "..", "..", "Resources",
                                      "demo_screenshots", filename)),
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
        """Position Excel's main window to the right half of the screen.

        DEPRECATED 2026-05-14: Chad asked for the tour panel on TOP and
        the workbook BELOW maximized — see position_excel_bottom_band.
        Kept for any code path that still calls it.
        """
        w, h = self._screen
        x = w // 2
        y = MENU_BAR_HEIGHT
        width = w // 2
        height = h - MENU_BAR_HEIGHT
        self._set_excel_window_geometry(x, y, width, height)

    def position_excel_bottom_band(self, panel_height):
        """Position Excel below the tour panel — full screen width, takes
        every pixel below `panel_height` (Chad's preferred layout
        2026-05-14). Maximizes the workbook real estate."""
        w, h = self._screen
        x = 0
        y = MENU_BAR_HEIGHT + panel_height
        width = w
        height = h - MENU_BAR_HEIGHT - panel_height
        self._set_excel_window_geometry(x, y, width, height)

    def enter_excel_fullscreen_view(self):
        """Toggle Excel's built-in 'Full Screen' view (Cmd+Ctrl+F equivalent).
        Hides the ribbon, formula bar, and other chrome — just shows the
        worksheet. Chad asked 2026-05-14 to maximize the demo experience.
        Does NOT use macOS fullscreen (that would put Excel in a separate
        space and break the tour-panel overlay)."""
        self._run_script('''
            tell application "Microsoft Excel"
                try
                    set display full screen to true
                end try
            end tell
        ''')

    def exit_excel_fullscreen_view(self):
        """Reverse enter_excel_fullscreen_view — call before quitting Excel
        so the next launch isn't stuck in fullscreen view."""
        self._run_script('''
            tell application "Microsoft Excel"
                try
                    set display full screen to false
                end try
            end tell
        ''')

    def close_other_excel_windows(self, keep_basename):
        """Close every Excel window EXCEPT the one matching keep_basename.
        Avoids 'Recent files' / 'Excel Start screen' / leftover workbooks
        cluttering the demo experience."""
        if not keep_basename:
            return
        self._run_script(f'''
            tell application "Microsoft Excel"
                try
                    repeat with wb in workbooks
                        if (name of wb) is not "{keep_basename}" then
                            close wb saving no
                        end if
                    end repeat
                end try
            end tell
        ''')

    def _set_excel_window_geometry(self, x, y, width, height):
        """Internal helper — apply position+size to Excel's first real window."""
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

        def __init__(self, workbook_path=None, on_purchase=None, parent=None):
            super().__init__(parent)
            # v0.14.5 Path B: the demo is now a single self-contained
            # window showing pre-rendered images of each tab + the pretty
            # pocket card. NO Excel, NO browser, NO TourController, NO
            # macOS permission prompts. workbook_path is accepted for
            # call-site compatibility but unused.
            self._stops = TOUR_STOPS
            self._index = 0
            self._on_purchase = on_purchase  # callback when user clicks Purchase
            self._current_pixmap = None      # original (unscaled) stop image
            self._dwell_timer = QTimer(self)
            self._dwell_timer.setSingleShot(True)
            self._dwell_timer.timeout.connect(self._on_dwell_complete)
            self._paused = False
            self._ended = False  # True once end-of-tour shown -> Close

            self.setWindowTitle("Loadscope — Demo Tour")
            self._build_ui()
            # Don't auto-start; caller invokes start() so it can hide the
            # main window first.

        # --- UI construction ----------------------------------------------------
        def _build_ui(self):
            # v0.14.2: compact layout (Chad 2026-05-14: more workbook,
            # less narration panel). Target panel height ~120-140px so
            # the workbook gets the lion's share of vertical space.
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 8, 16, 8)
            layout.setSpacing(6)

            # Top row: title (left) + step indicator (right)
            header_row = QHBoxLayout()
            header_row.setSpacing(12)

            self.title_label = QLabel("")
            tf = QFont()
            tf.setPointSize(14)
            tf.setWeight(QFont.DemiBold)
            self.title_label.setFont(tf)
            if _theme:
                # v0.14.2: title in accent orange (Chad 2026-05-14:
                # bring the brand into the demo panel without
                # over-saturating with full orange background).
                self.title_label.setStyleSheet(f"color: {_theme.ACCENT};")
            header_row.addWidget(self.title_label, stretch=1)

            self.progress_label = QLabel("")
            pf = QFont()
            pf.setPointSize(10)
            self.progress_label.setFont(pf)
            self.progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if _theme:
                self.progress_label.setStyleSheet(f"color: {_theme.TEXT_SECONDARY};")
            header_row.addWidget(self.progress_label)

            layout.addLayout(header_row)

            # Thin progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, len(self._stops))
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(3)
            layout.addWidget(self.progress_bar)

            # Narration body — compact
            self.narration_label = QLabel("")
            nf = QFont()
            nf.setPointSize(12)
            self.narration_label.setFont(nf)
            self.narration_label.setWordWrap(True)
            self.narration_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            # v0.14.5: narration is a compact band at the top; the big
            # pre-rendered tab image gets the rest of the window.
            self.narration_label.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Minimum
            )
            if _theme:
                # v0.14.2: orange left-edge stripe + dark gray surface.
                self.narration_label.setStyleSheet(
                    f"color: {_theme.TEXT_PRIMARY}; "
                    f"background-color: {_theme.BG_ELEVATED}; "
                    f"border-left: 4px solid {_theme.ACCENT}; "
                    f"padding: 8px 12px 8px 14px; "
                    f"border-top-right-radius: 6px; "
                    f"border-bottom-right-radius: 6px;"
                )
            layout.addWidget(self.narration_label)

            # v0.14.5 Path B: the star of the demo — a pre-rendered,
            # pixel-perfect image of the actual workbook tab / pretty
            # pocket card. Scaled to fit, aspect preserved. No Excel.
            self.image_label = QLabel("")
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.image_label.setMinimumHeight(360)
            if _theme:
                self.image_label.setStyleSheet(
                    f"background-color: {_theme.BG_ELEVATED}; "
                    f"border-radius: 6px;"
                )
            layout.addWidget(self.image_label, stretch=1)

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
            """Path B: a single self-contained full-window demo. No Excel,
            no browser, no positioning, no permission prompts."""
            try:
                scr = self.screen().availableGeometry()
                self.setGeometry(scr)
            except Exception:
                self.resize(1280, 820)
            self.show()
            self.raise_()
            self.activateWindow()
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
            # The same button is "Skip tour" mid-tour and "Close" on the
            # end screen. Once ended, it must actually close the window
            # (previously it re-ran _show_end_of_tour and did nothing).
            if self._ended:
                self.close()
                return
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

            # Path B: show the pre-rendered image for this stop.
            self._load_stop_image(stop)

            # Enforce min dwell — disable Next until timer fires
            self.next_btn.setEnabled(False)
            self.next_btn.setText(f"Next → (wait {stop['min_dwell_seconds']}s)")
            self._dwell_timer.start(stop["min_dwell_seconds"] * 1000)

            # Previous always available except on first stop
            self.prev_btn.setEnabled(index > 0)

        def _load_stop_image(self, stop):
            """Load this stop's pre-rendered PNG into the image label."""
            self._current_pixmap = None
            name = stop.get("image")
            path = get_demo_screenshot(name) if name else None
            if path and QPixmap is not None:
                pm = QPixmap(path)
                if not pm.isNull():
                    self._current_pixmap = pm
            if self._current_pixmap is None:
                self.image_label.setText(
                    "(demo image unavailable — reinstall Loadscope)")
            else:
                self.image_label.setText("")
                self._apply_pixmap()

        def _apply_pixmap(self):
            """Scale the current stop image to fit the label, preserving
            aspect ratio. Re-run on every resize for crisp rendering."""
            if self._current_pixmap is None:
                return
            sz = self.image_label.size()
            if sz.width() < 10 or sz.height() < 10:
                return
            self.image_label.setPixmap(self._current_pixmap.scaled(
                sz, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._apply_pixmap()

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
            self._ended = True
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

        def closeEvent(self, event):
            """Path B: the demo never launched Excel, so there's nothing
            to tear down. The main window re-shows itself via the panel's
            destroyed signal (wired in main.py _open_demo_tour)."""
            try:
                self._dwell_timer.stop()
            except Exception:
                pass
            super().closeEvent(event)


def show_tour(workbook_path, parent=None, on_purchase=None):
    """Convenience entry point — creates and starts the panel."""
    if QWidget is None:
        raise RuntimeError("PyQt5 not available")
    panel = DemoTourPanel(workbook_path, on_purchase=on_purchase, parent=parent)
    panel.show()
    panel.start()
    return panel
