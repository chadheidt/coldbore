"""Frequently Asked Questions dialog for Loadscope.

Categorized FAQs with a search bar. Two-column layout: left is the
categorized question list (filtered by the search box), right is the
answer for the selected question.

v0.14: launched from the Support menu (Chad 2026-05-14).
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    import theme as _theme
except ImportError:
    _theme = None


# ---- FAQ content ----
# Each entry: (category, question, answer_html)
FAQ_DATA = [
    # ---- Getting Started ----
    ("Getting Started", "What is Loadscope?",
     "<p>Loadscope is a load-development app for precision rifle shooters. "
     "Drop your Garmin Xero chronograph and BallisticX target CSVs onto the "
     "app — it builds an Excel workbook with velocity, group, and SD "
     "analysis, then ranks every powder and seating-depth candidate to "
     "suggest your best load.</p>"),

    ("Getting Started", "How do I get started?",
     "<p>First time opening Loadscope? You'll see a welcome screen with "
     "three choices:</p>"
     "<ul>"
     "<li><b>Try the Free Demo</b> — opens a pre-loaded sample workbook "
     "and walks you through every tab with a guided tour. No license needed.</li>"
     "<li><b>Enter License Key</b> — if you've already purchased.</li>"
     "<li><b>Purchase a License</b> — opens the checkout page.</li>"
     "</ul>"),

    ("Getting Started", "What CSVs does Loadscope read today?",
     "<p>Two formats:</p>"
     "<ul>"
     "<li><b>Garmin Xero</b> — exported from the ShotView iOS app (tap "
     "Share → CSV on a session).</li>"
     "<li><b>BallisticX</b> — exported from the BallisticX iOS app (tap "
     "Share on a group → CSV).</li>"
     "</ul>"
     "<p>Loadscope auto-detects the format from the file contents — you "
     "don't have to organize them manually. Drop them on together; "
     "Loadscope sorts them into the right import folders.</p>"),

    # ---- Importing Range Data ----
    ("Importing Range Data", "How do I label my Garmin and BallisticX exports?",
     "<p>Each session or group needs a label with 3 parts separated by "
     "spaces: <b>[test tag] [grains or jump] [powder]</b>.</p>"
     "<p>Examples:</p>"
     "<ul>"
     "<li><tt>P1 45.5 H4350</tt> &nbsp;—&nbsp; Powder Ladder, Load 1, "
     "45.5 grains of H4350</li>"
     "<li><tt>S7 0.070 H4350</tt> &nbsp;—&nbsp; Seating Depth, Test 7, "
     "0.070-inch jump, H4350</li>"
     "</ul>"
     "<p>Type the label in your Garmin ShotView session name, your "
     "BallisticX group name, or by renaming the CSV file. Loadscope reads "
     "from any of those.</p>"),

    ("Importing Range Data", "What if Loadscope doesn't see my files after I drop them?",
     "<p>Two common causes:</p>"
     "<ul>"
     "<li><b>Excel is open with the workbook</b> — close it (Cmd+Q) and "
     "click Run Import again.</li>"
     "<li><b>The file label doesn't start with a recognized tag</b> "
     "(P1–P10 or S1–S10). Open the Garmin Xero Import or BallisticX "
     "Import tab in your workbook to see what made it in.</li>"
     "</ul>"),

    ("Importing Range Data", "Will Loadscope work with my LabRadar / MagnetoSpeed / Two Box Chrono?",
     "<p>Not yet — today only Garmin Xero and BallisticX are supported. "
     "Loadscope's parser plugin architecture makes adding new chronographs "
     "straightforward, though.</p>"
     "<p>Email <a href='mailto:support@loadscope.app'>support@loadscope.app</a> "
     "a sample CSV from your device and we'll add it in the next update.</p>"),

    # ---- The Workbook ----
    ("The Workbook", "How does Loadscope decide which load / seating depth is best?",
     "<p>Loadscope normalizes each candidate's <b>velocity SD</b>, <b>group "
     "size</b>, <b>mean radius</b>, and <b>vertical dispersion</b> to a "
     "0-to-1 scale (lower is better) and combines them into a single "
     "<b>composite score</b> using adjustable weights. The candidate with "
     "the lowest composite score wins.</p>"
     "<p>The default weights are equal across all four metrics. You can "
     "tune them on the Charts tab (cells C11, E11, G11, I11) — for "
     "example, prioritize SD over group size if you're shooting long range.</p>"
     "<p>Each candidate also gets a 'Best in:' tag for any individual "
     "metric where it scored best — even if it didn't win the composite.</p>"),

    ("The Workbook", "What does the 'Suggested Winner' mean?",
     "<p>The Suggested Winner is the candidate load (or seating depth) "
     "with the best composite score across all four metrics — velocity SD, "
     "group size, mean radius, and vertical dispersion. Loadscope marks "
     "it with a 🥇 medal in the P column on Load Log and Seating Depth, "
     "and writes the winning charge / jump value to the top of each tab.</p>"),

    ("The Workbook", "Can I change the scoring weights?",
     "<p>Yes — open the Charts tab and edit the four weights cells "
     "(C11, E11, G11, I11). The default is equal weight (0.25 each) for "
     "velocity SD, group size, mean radius, and vertical dispersion.</p>"
     "<p>If you change the weights, the composite scores and Suggested "
     "Winner update automatically. To return to defaults, click the "
     "orange <b>Reset Composite Weights</b> button on the Charts tab.</p>"),

    ("The Workbook", "How do I print a Pocket Range Card?",
     "<p>Open the Ballistics tab and click the orange "
     "<b>→ Print Pocket Range Card ←</b> button at the top. Loadscope "
     "generates a printable 4×6 HTML card from your DOPE data and opens "
     "it in your browser. Print on cardstock or save as PDF — it folds "
     "into your shirt pocket for the firing line.</p>"
     "<p>You'll need to fill in your dialed elevation and wind values "
     "first (Mils Dialed and Wind Hold Mils columns) — Loadscope can't "
     "predict those today (coming in v0.15).</p>"),

    ("The Workbook", "Why is my MOA column hidden? (Or vice versa.)",
     "<p>Loadscope auto-hides the click columns that don't match your "
     "scope's turret. The Click: dropdown on the Load Log tab tells "
     "Loadscope your scope's click value:</p>"
     "<ul>"
     "<li><b>0.1 Mil / 0.05 Mil scope</b> → MOA columns hide on Ballistics</li>"
     "<li><b>1/4 MOA / 1/8 MOA scope</b> → Mil columns hide on Ballistics</li>"
     "</ul>"
     "<p>If you change the dropdown, re-run import to refresh the visibility.</p>"),

    # ---- Privacy & Your Data ----
    ("Privacy & Your Data", "Where is my data stored? Does Loadscope send anything to a server?",
     "<p>Everything stays local. Your CSVs sit in your project folder "
     "(default <tt>~/Documents/Loadscope Loads</tt>), your workbooks live "
     "there too. <b>Loadscope never uploads your range data to any "
     "server</b> — no analytics, no telemetry, no cloud sync, no "
     "background phone-home.</p>"
     "<p>The only network traffic Loadscope makes: (1) checking for app "
     "updates against a manifest URL, and (2) verifying your license key "
     "with our license server when you enter it. Both are clearly "
     "indicated when they happen.</p>"),

    ("Privacy & Your Data", "How do I back up my workbooks?",
     "<p>Just copy the project folder. The .xlsx workbook is self-"
     "contained — every formula, chart, and value lives inside the file. "
     "iCloud Drive, Time Machine, Dropbox, or a manual copy all work.</p>"
     "<p>Loadscope also keeps a small backup history of your workbook "
     "automatically — every time you run an import, the previous "
     "workbook is rotated into a <tt>backups/</tt> folder inside your "
     "project folder.</p>"),

    ("Privacy & Your Data", "What happens if I uninstall Loadscope?",
     "<p>Your workbooks and CSVs stay where they are (in your project "
     "folder). Loadscope never modifies your data outside that folder. "
     "Uninstall just removes the app from <tt>/Applications</tt> — no "
     "leftover files to worry about.</p>"
     "<p>If you reinstall later, point Loadscope at your existing project "
     "folder during setup and everything resumes.</p>"),

    # ---- Updates & Licensing ----
    ("Updates & Licensing", "How does Loadscope auto-update?",
     "<p>When a new version ships, you'll see a yellow banner across the "
     "top of the Loadscope window within ~10 seconds of opening the app. "
     "Click <b>Install Update</b> → <b>Quit and Install</b> and Loadscope "
     "downloads + installs the update + reopens itself. About 30 seconds "
     "from start to finish.</p>"
     "<p>Updates check happens once per launch. There's no background "
     "polling.</p>"),

    ("Updates & Licensing", "Is Loadscope free? What does the paid version add?",
     "<p>Loadscope is currently in beta. The <b>Try the Demo</b> mode "
     "lets you walk through a pre-loaded sample workbook end-to-end at "
     "no cost — every feature is visible, just with demo data instead of "
     "yours.</p>"
     "<p>The <b>licensed version</b> unlocks importing your own CSVs and "
     "saving real workbooks. Pricing is currently $79 one-time, with "
     "lifetime updates included.</p>"),

    ("Updates & Licensing", "What's coming next?",
     "<p>Near-term roadmap:</p>"
     "<ul>"
     "<li><b>v0.15: Built-in ballistic solver</b> — predicted DOPE values "
     "in the Ballistics tab so your Pocket Range Card has data the day "
     "you build a load, before you've shot it at distance.</li>"
     "<li><b>Windows version</b> — Phase 7 of the build plan.</li>"
     "<li><b>More chronograph parsers</b> — LabRadar, MagnetoSpeed, "
     "Two Box Chrono, ProChrono.</li>"
     "<li><b>iOS companion app</b> — Phase 8.</li>"
     "</ul>"
     "<p>Roadmap status lives at <a href='https://loadscope.app'>"
     "https://loadscope.app</a>.</p>"),

    # ---- Help & Support ----
    ("Help & Support", "How do I contact support?",
     "<p>Email <a href='mailto:support@loadscope.app'>"
     "support@loadscope.app</a>. Reply within 24-48 hours, usually faster. "
     "Include your Loadscope version (Tools → About) and a screenshot if "
     "it's a visual issue.</p>"),

    ("Help & Support", "Where do I find the Quick Start guide?",
     "<p>Loadscope copies <b>Loadscope — Quick Start.docx</b> into your "
     "project folder during first-time setup. Open it from there.</p>"
     "<p>The <b>Start Here</b> tab inside every workbook also has the "
     "basics: how to label your CSVs, how to import, what's on each tab, "
     "and troubleshooting.</p>"),

    ("Help & Support", "I found a bug — what's the fastest way to report it?",
     "<p>Email <a href='mailto:support@loadscope.app'>"
     "support@loadscope.app</a> with:</p>"
     "<ol>"
     "<li>What you were trying to do</li>"
     "<li>What you expected to happen</li>"
     "<li>What actually happened</li>"
     "<li>A screenshot if it helps</li>"
     "</ol>"
     "<p>If Loadscope crashed, please include the crash report dialog "
     "text — it has a stack trace that helps pinpoint the issue.</p>"),
]


class FaqDialog(QDialog):
    """Two-column FAQ dialog: categorized question list on left, answer on
    right, search bar on top."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loadscope — Frequently Asked Questions")
        self.setMinimumSize(900, 600)
        if _theme:
            self.setStyleSheet(
                f"QDialog {{ background-color: {_theme.BG_BASE}; }}"
            )
        self._build_ui()
        # Default selection — first question
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)

        # Title
        title = QLabel("Frequently Asked Questions")
        tf = QFont()
        tf.setPointSize(20)
        tf.setWeight(QFont.DemiBold)
        title.setFont(tf)
        if _theme:
            title.setStyleSheet(f"color: {_theme.TEXT_PRIMARY};")
        outer.addWidget(title)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type to filter questions…")
        self.search.setClearButtonEnabled(True)
        if _theme:
            self.search.setStyleSheet(
                f"QLineEdit {{ background-color: {_theme.BG_SURFACE}; "
                f"color: {_theme.TEXT_PRIMARY}; border: 1px solid "
                f"{_theme.BORDER_MEDIUM}; border-radius: 6px; "
                f"padding: 8px 12px; font-size: 13px; }}"
            )
        self.search.textChanged.connect(self._filter_list)
        outer.addWidget(self.search)

        # Two-column splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left — categorized question list
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(280)
        if _theme:
            self.list_widget.setStyleSheet(
                f"QListWidget {{ background-color: {_theme.BG_SURFACE}; "
                f"color: {_theme.TEXT_PRIMARY}; border: 1px solid "
                f"{_theme.BORDER_MEDIUM}; border-radius: 6px; "
                f"padding: 4px; font-size: 12px; outline: 0; }} "
                f"QListWidget::item {{ padding: 6px 8px; }} "
                f"QListWidget::item:selected {{ "
                f"background-color: {_theme.ACCENT}; "
                f"color: white; border-radius: 4px; }} "
                f"QListWidget::item:hover {{ "
                f"background-color: {_theme.BG_ELEVATED}; "
                f"border-radius: 4px; }}"
            )
        # Populate with category headers + questions
        self._populate_list()
        self.list_widget.currentItemChanged.connect(self._show_answer)
        splitter.addWidget(self.list_widget)

        # Right — answer pane
        self.answer = QTextBrowser()
        self.answer.setOpenExternalLinks(True)
        if _theme:
            self.answer.setStyleSheet(
                f"QTextBrowser {{ background-color: {_theme.BG_SURFACE}; "
                f"color: {_theme.TEXT_PRIMARY}; border: 1px solid "
                f"{_theme.BORDER_MEDIUM}; border-radius: 6px; "
                f"padding: 16px; font-size: 13px; }}"
            )
        splitter.addWidget(self.answer)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 580])
        outer.addWidget(splitter, stretch=1)

        # Footer — close button
        footer_row = QHBoxLayout()
        footer_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        footer_row.addWidget(close_btn)
        outer.addLayout(footer_row)

    def _populate_list(self):
        """Populate list with category headers (non-selectable, bold)
        followed by their questions (selectable)."""
        self.list_widget.clear()
        last_cat = None
        for category, question, answer in FAQ_DATA:
            if category != last_cat:
                # Category header — non-selectable, styled
                hdr = QListWidgetItem(category.upper())
                hdr.setFlags(Qt.NoItemFlags)  # non-selectable, non-clickable
                f = QFont()
                f.setBold(True)
                f.setPointSize(10)
                hdr.setFont(f)
                if _theme:
                    from PyQt5.QtGui import QColor
                    hdr.setForeground(QColor(_theme.TEXT_TERTIARY))
                self.list_widget.addItem(hdr)
                last_cat = category
            # Question row
            item = QListWidgetItem("  " + question)
            item.setData(Qt.UserRole, answer)
            self.list_widget.addItem(item)

    def _filter_list(self, query):
        """Hide list rows whose question text doesn't match the query.
        Category headers stay visible if any of their children match."""
        q = query.strip().lower()
        # First pass: figure out which category-header items to hide.
        # Group questions by their preceding category header index.
        category_visible = {}  # header row idx → True if any child matches
        current_cat_idx = None
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() == Qt.NoItemFlags:
                # Category header
                current_cat_idx = i
                category_visible[current_cat_idx] = False
            else:
                # Question item
                text = item.text().strip().lower()
                answer = (item.data(Qt.UserRole) or "").lower()
                matches = (not q) or (q in text) or (q in answer)
                item.setHidden(not matches)
                if matches and current_cat_idx is not None:
                    category_visible[current_cat_idx] = True
        # Hide category headers with no visible children
        for hdr_idx, visible in category_visible.items():
            self.list_widget.item(hdr_idx).setHidden(not visible)

    def _show_answer(self, current, _previous):
        if current is None or current.flags() == Qt.NoItemFlags:
            return
        answer_html = current.data(Qt.UserRole) or ""
        question = current.text().strip()
        # Wrap with question header + base styling
        if _theme:
            text_color = _theme.TEXT_PRIMARY
            accent = _theme.ACCENT
        else:
            text_color = "#222"
            accent = "#d97706"
        full = (
            f"<style>body {{ color: {text_color}; "
            f"font-family: 'Helvetica Neue', sans-serif; line-height: 1.5; }} "
            f"h2 {{ color: {accent}; font-size: 16pt; margin-bottom: 14px; }} "
            f"a {{ color: {accent}; }} "
            f"tt {{ background-color: rgba(255,255,255,0.07); "
            f"padding: 1px 5px; border-radius: 3px; font-family: 'SF Mono', monospace; }} "
            f"ul, ol {{ margin-left: 18px; }}</style>"
            f"<h2>{question}</h2>{answer_html}"
        )
        self.answer.setHtml(full)


def show_faq_dialog(parent=None):
    """Convenience launcher — opens the FAQ dialog modally."""
    dlg = FaqDialog(parent)
    dlg.exec_()
