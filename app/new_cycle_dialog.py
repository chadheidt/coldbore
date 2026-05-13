"""
Tools → Start New Cycle

Wizard that ends a load development cycle cleanly:
  1. Asks for a name for the new cycle
  2. Moves the current workbook to Completed Loads/
  3. Moves all CSVs in Garmin Imports/ and BallisticX Imports/ to dated archive
     subfolders so they don't pollute the next cycle
  4. Copies the .xltx template to a new working .xlsx with the chosen name
  5. Tells main.py to refresh the workbook picker so the new file is selected

This automates what was previously a manual workflow described only in
documentation.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from version import APP_NAME


class NewCycleDialog(QDialog):
    def __init__(self, project_folder, current_workbook, parent=None):
        super().__init__(parent)
        self.project = str(project_folder)
        self.current_workbook = current_workbook
        self.created_workbook_path = None

        self.setWindowTitle(f"{APP_NAME} — Start New Cycle")
        self.setModal(True)
        self.setMinimumWidth(540)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Done with this load? Start a new one")
        f = QFont()
        f.setPointSize(17)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        if self._t:
            title.setStyleSheet(f"color: {self._t.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Description
        intro = QLabel(
            "Finished testing this load and want to start a new one "
            "(different bullet, powder, or cartridge)? Loadscope cleans "
            "everything up for you. Your old files aren't deleted — they're "
            "just moved out of the way so the new cycle stays organized."
        )
        intro.setWordWrap(True)
        if self._t:
            intro.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        layout.addWidget(intro)

        # New cycle name
        form = QFormLayout()
        form.setSpacing(10)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(
            "e.g. 6.5 Creedmoor 140 ELD-M H4350"
        )
        form.addRow("Name your new load:", self.name_edit)
        layout.addLayout(form)

        # Checkboxes for what gets archived
        what_label = QLabel("When you click Start, Loadscope will:")
        if self._t:
            what_label.setStyleSheet(
                f"color: {self._t.TEXT_TERTIARY}; "
                f"font-size: {self._t.FONT_SIZE_TINY}px; "
                f"text-transform: uppercase; letter-spacing: 1px; "
                f"font-weight: bold; padding-top: 6px;"
            )
        layout.addWidget(what_label)

        self.archive_workbook_cb = QCheckBox(
            f"Save the current workbook to the Completed Loads folder  "
            f"({os.path.basename(current_workbook) if current_workbook else 'none'})"
        )
        self.archive_workbook_cb.setChecked(bool(current_workbook))
        self.archive_workbook_cb.setEnabled(bool(current_workbook))
        layout.addWidget(self.archive_workbook_cb)

        self.archive_garmin_cb = QCheckBox(
            "Move your old Garmin CSV files into a dated folder (kept safe, just out of the way)"
        )
        self.archive_garmin_cb.setChecked(True)
        layout.addWidget(self.archive_garmin_cb)

        self.archive_bx_cb = QCheckBox(
            "Move your old BallisticX CSV files into a dated folder (kept safe, just out of the way)"
        )
        self.archive_bx_cb.setChecked(True)
        layout.addWidget(self.archive_bx_cb)

        self.create_new_cb = QCheckBox(
            "Create a brand new empty workbook for your new load"
        )
        self.create_new_cb.setChecked(True)
        layout.addWidget(self.create_new_cb)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = btns.button(QDialogButtonBox.Ok)
        if ok_btn is not None:
            ok_btn.setObjectName("primary")
            ok_btn.setText("Start")
        btns.accepted.connect(self._do_it)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _do_it(self):
        name = self.name_edit.text().strip()
        if self.create_new_cb.isChecked() and not name:
            QMessageBox.warning(
                self, "Name required",
                "Please type a name for the new load. "
                "Or, if you don't want a new workbook, uncheck the bottom box."
            )
            return

        # Sanitize the name for use in a filename (avoid path separators)
        safe_name = name.replace("/", "-").replace(":", "-")

        actions_done = []
        try:
            stamp = datetime.now().strftime("%Y-%m-%d")

            # 1. Move current workbook to Completed Loads/
            if self.archive_workbook_cb.isChecked() and self.current_workbook:
                completed_dir = os.path.join(self.project, "Completed Loads")
                os.makedirs(completed_dir, exist_ok=True)
                dest = os.path.join(completed_dir, os.path.basename(self.current_workbook))
                # If a workbook with the same name is already in Completed Loads,
                # add a date suffix to disambiguate
                if os.path.exists(dest):
                    base, ext = os.path.splitext(os.path.basename(self.current_workbook))
                    dest = os.path.join(completed_dir, f"{base} {stamp}{ext}")
                shutil.move(self.current_workbook, dest)
                actions_done.append(f"Moved workbook → Completed Loads/{os.path.basename(dest)}")

            # 2. Archive Garmin CSVs
            if self.archive_garmin_cb.isChecked():
                self._archive_csvs(
                    os.path.join(self.project, "Garmin Imports"),
                    f"Archive {stamp}",
                )
                actions_done.append("Archived Garmin Imports/ CSVs")

            # 3. Archive BallisticX CSVs
            if self.archive_bx_cb.isChecked():
                self._archive_csvs(
                    os.path.join(self.project, "BallisticX Imports"),
                    f"Archive {stamp}",
                )
                actions_done.append("Archived BallisticX Imports/ CSVs")

            # 4. Create new workbook from template
            if self.create_new_cb.isChecked():
                template_path = self._find_template()
                if not template_path:
                    raise RuntimeError(
                        "Couldn't find the .xltx template in the project folder. "
                        "Aborting before creating a new workbook."
                    )
                new_path = os.path.join(self.project, f"{safe_name}.xlsx")
                # Avoid overwriting an existing file
                if os.path.exists(new_path):
                    QMessageBox.warning(
                        self, "Name already used",
                        f"A workbook called '{safe_name}.xlsx' already exists in your folder. "
                        "Please pick a different name."
                    )
                    return
                # Open the template and re-save as .xlsx so it's a proper workbook.
                # Also stamp the load name onto each user-facing sheet so the
                # user always knows which load they're viewing.
                from openpyxl import load_workbook
                try:
                    import import_data
                except ImportError:
                    import_data = None
                wb = load_workbook(template_path, keep_vba=False)
                wb.template = False  # critical — same fix as setup_wizard
                inherited_labels = []
                if import_data is not None:
                    import_data.stamp_load_name(wb, name)
                    inherited_labels = import_data.inherit_rifle_setup(
                        wb, self.project, exclude_path=new_path,
                    )
                wb.save(new_path)
                self.created_workbook_path = new_path
                actions_done.append(f"Created workbook: {safe_name}.xlsx")
                if inherited_labels:
                    actions_done.append(
                        f"Pre-filled rifle setup from previous workbook: {', '.join(inherited_labels)}"
                    )

        except Exception as e:
            done_list = "\n  ".join(actions_done) if actions_done else "(none yet)"
            QMessageBox.critical(
                self, "Something went wrong",
                f"Loadscope couldn't finish setting up the new cycle:\n\n{e}\n\n"
                f"Steps that did finish:\n  {done_list}",
            )
            return

        QMessageBox.information(
            self, "All set!",
            "Loadscope finished setting up your new cycle:\n\n"
            + "\n".join(f"• {a}" for a in actions_done) +
            ("\n\nYour new workbook is ready. Drop CSVs into Loadscope "
             "whenever you're ready to import range data."
             if self.created_workbook_path else "")
        )
        self.accept()

    def _archive_csvs(self, folder, archive_subfolder_name):
        """Move all .csv files in `folder` into a subfolder named
        `archive_subfolder_name`. Skips if folder doesn't exist or is empty."""
        if not os.path.isdir(folder):
            return
        csvs = [f for f in os.listdir(folder)
                if f.lower().endswith(".csv") and not f.startswith(".")]
        if not csvs:
            return
        archive_dir = os.path.join(folder, archive_subfolder_name)
        os.makedirs(archive_dir, exist_ok=True)
        for csv_name in csvs:
            src = os.path.join(folder, csv_name)
            dst = os.path.join(archive_dir, csv_name)
            shutil.move(src, dst)

    def _find_template(self):
        """Find the .xltx template in the project folder."""
        for f in os.listdir(self.project):
            if f.lower().endswith(".xltx") and "template" in f.lower():
                return os.path.join(self.project, f)
        return None


def show_new_cycle(project_folder, current_workbook, parent=None):
    """Show the New Cycle dialog. Returns the path of the newly-created
    workbook if one was created, else None."""
    dlg = NewCycleDialog(project_folder, current_workbook, parent)
    if dlg.exec_() == QDialog.Accepted:
        return dlg.created_workbook_path
    return None
