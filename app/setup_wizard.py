"""
First-run setup wizard.

Shows a small dialog when the app launches and finds no valid project folder.
Walks the user through:
    1. Picking a location for their True Zero project folder.
    2. Creating the folder + subfolders (Garmin Imports/, BallisticX Imports/, Completed Loads/).
    3. Copying the bundled .xltx template into the project folder.

Returns the chosen project folder path on success, or None if cancelled.
"""

import os
import shutil
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


# Subfolders we always create inside the project folder
SUBFOLDERS = ("Garmin Imports", "BallisticX Imports", "Completed Loads")


def find_bundled_template():
    """Locate the .xltx template that should be copied into a fresh project folder.

    Search order:
      1. py2app .app bundle: <App.app>/Contents/Resources/  (next to MacOS/)
      2. Repo root (dev mode — running from the source tree)
      3. resources/templates/ subfolder next to this script

    Returns Path or None.
    """
    here = Path(__file__).resolve().parent

    # 1. py2app bundle. When bundled, sys.executable lives at
    # <App.app>/Contents/MacOS/<AppName>, and DATA_FILES land in
    # <App.app>/Contents/Resources/.
    if getattr(sys, "frozen", False):
        try:
            resources_dir = Path(sys.executable).resolve().parent.parent / "Resources"
            if resources_dir.is_dir():
                for cand in resources_dir.glob("*.xltx"):
                    return cand
        except (OSError, ValueError):
            pass

    # PyInstaller fallback (we're not using it, but harmless to try)
    if hasattr(sys, "_MEIPASS"):
        bundle = Path(sys._MEIPASS)
        for cand in bundle.glob("*.xltx"):
            return cand

    # 2. Repo root (one level up from app/)
    repo_root = here.parent
    candidates = [c for c in repo_root.glob("*.xltx") if "template" in c.name.lower()]
    if candidates:
        for c in candidates:
            if c.name == "Rifle Loads Template (do not edit).xltx":
                return c
        return candidates[0]

    # 3. resources/templates/ subfolder
    resources = here / "resources" / "templates"
    if resources.is_dir():
        for cand in resources.glob("*.xltx"):
            return cand

    return None


def setup_project_folder(project_folder, template_path):
    """Create the project folder structure and copy the template in.

    Raises an exception on failure. Returns nothing on success.
    """
    project_folder = Path(project_folder)
    project_folder.mkdir(parents=True, exist_ok=True)

    for sub in SUBFOLDERS:
        (project_folder / sub).mkdir(exist_ok=True)

    # Copy the template if not already present
    dest_template = project_folder / "Rifle Loads Template (do not edit).xltx"
    if not dest_template.exists() and template_path and template_path.exists():
        shutil.copy2(template_path, dest_template)


class SetupWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chosen_folder = None
        self.setWindowTitle("True Zero — First-Time Setup")
        self.setMinimumWidth(540)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        # Try to import theme; degrade gracefully if not present
        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        # Title
        title = QLabel("Welcome — let's set up your True Zero folder")
        f = QFont()
        f.setPointSize(17)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        if self._t:
            title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Description
        body = QLabel(
            "This is a one-time setup. We'll create a 'True Zero Loads' folder for "
            "your workbooks and CSV imports. By default it goes in your Documents "
            "folder, but you can pick anywhere."
        )
        body.setWordWrap(True)
        if self._t:
            body.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        else:
            body.setStyleSheet("color: #444;")
        layout.addWidget(body)

        # Path picker row
        path_row = QHBoxLayout()
        self.path_field = QLineEdit()
        default_path = str(Path.home() / "Documents" / "True Zero Loads")
        self.path_field.setText(default_path)
        path_row.addWidget(self.path_field, stretch=1)

        browse = QPushButton("Choose…")
        browse.clicked.connect(self._browse)
        path_row.addWidget(browse)

        layout.addLayout(path_row)

        # What we'll create
        info = QLabel(
            "We'll create the folder and these subfolders inside it:\n"
            "    • Garmin Imports\n"
            "    • BallisticX Imports\n"
            "    • Completed Loads\n\n"
            "We'll also copy the workbook template in. Any existing files in "
            "this location will be left alone."
        )
        if self._t:
            info.setStyleSheet(f"color: {self._t.TEXT_SECONDARY}; padding: 8px 0;")
        else:
            info.setStyleSheet("color: #555; padding: 8px 0;")
        layout.addWidget(info)

        # Action buttons
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        button_row.addWidget(cancel)

        create = QPushButton("Create")
        create.setDefault(True)
        create.setObjectName("primary")  # picks up the orange accent style
        create.clicked.connect(self._create)
        button_row.addWidget(create)

        layout.addLayout(button_row)

    def _browse(self):
        start = self.path_field.text() or str(Path.home() / "Documents")
        # Use the parent of the proposed folder as the start dir
        start_parent = str(Path(start).parent) if start else str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self, "Pick a parent folder", start_parent
        )
        if folder:
            # Append "True Zero Loads" to whatever the user picked, so they don't have
            # to manually create-then-pick. They can edit if they want a different name.
            picked = Path(folder) / "True Zero Loads"
            self.path_field.setText(str(picked))

    def _create(self):
        proposed = self.path_field.text().strip()
        if not proposed:
            QMessageBox.warning(self, "Pick a folder", "Please pick a folder location.")
            return

        target = Path(proposed).expanduser()
        template = find_bundled_template()

        try:
            setup_project_folder(target, template)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Setup failed",
                f"Couldn't set up the folder at:\n\n{target}\n\nError:\n{e}",
            )
            return

        if not template:
            QMessageBox.warning(
                self,
                "Template missing",
                f"The folder was created at {target}, but I couldn't find the workbook "
                "template to copy in. You'll need to put your .xltx template into this "
                "folder manually before importing.",
            )

        self.chosen_folder = target
        self.accept()


def run_wizard(parent=None):
    """Show the wizard. Returns the chosen Path or None if cancelled."""
    dlg = SetupWizard(parent)
    if dlg.exec_() == QDialog.Accepted:
        return dlg.chosen_folder
    return None
