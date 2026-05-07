"""
Settings dialog (Tools → Settings…).

Lets the user toggle / edit common config options without hand-editing the
JSON config file. Currently exposes:

- Auto-update check on/off
- Custom update manifest URL (override of the baked-in default)
- Project folder (read-only display + "Show in Finder" button)
- Backups retention count

Persists changes through app.config (load_config / save_config).
"""

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
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

import config as app_config
from version import APP_NAME


class SettingsDialog(QDialog):
    def __init__(self, project_folder, parent=None):
        super().__init__(parent)
        self.project_folder = project_folder
        self.setWindowTitle(f"{APP_NAME} — Settings")
        self.setModal(True)
        self.setMinimumWidth(500)

        try:
            import theme
            self._t = theme
        except ImportError:
            self._t = None

        cfg = app_config.load_config()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)

        # Title
        title = QLabel("Settings")
        f = QFont()
        f.setPointSize(17)
        f.setWeight(QFont.DemiBold)
        title.setFont(f)
        layout.addWidget(title)

        sub = QLabel("Changes save automatically when you click OK.")
        if self._t:
            sub.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        layout.addWidget(sub)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        # Auto-update toggle
        self.update_check_toggle = QCheckBox("Check for app updates on launch")
        self.update_check_toggle.setChecked(
            bool(cfg.get("update_check_enabled", True))
        )
        form.addRow(self.update_check_toggle)

        # Custom manifest URL (override of the baked-in default)
        self.manifest_url_edit = QLineEdit()
        self.manifest_url_edit.setText(cfg.get("update_manifest_url", "") or "")
        self.manifest_url_edit.setPlaceholderText(
            "(blank = use built-in default)"
        )
        form.addRow("Update manifest URL:", self.manifest_url_edit)

        # Backup retention count
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setMinimum(0)
        self.backup_count_spin.setMaximum(50)
        self.backup_count_spin.setValue(int(cfg.get("backup_keep_count", 5)))
        self.backup_count_spin.setSuffix(" backups")
        form.addRow("Workbook backups to keep:", self.backup_count_spin)

        layout.addLayout(form)

        # Project folder display
        proj_label = QLabel(f"<b>Project folder:</b><br>{self.project_folder}")
        proj_label.setWordWrap(True)
        if self._t:
            proj_label.setStyleSheet(f"color: {self._t.TEXT_SECONDARY};")
        layout.addWidget(proj_label)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        # Style the OK button with the orange primary look
        ok_btn = btns.button(QDialogButtonBox.Ok)
        if ok_btn is not None:
            ok_btn.setObjectName("primary")
        layout.addWidget(btns)

    def _save(self):
        cfg = app_config.load_config()
        cfg["update_check_enabled"] = self.update_check_toggle.isChecked()
        url_value = self.manifest_url_edit.text().strip()
        if url_value:
            cfg["update_manifest_url"] = url_value
        else:
            # Empty = clear the override so the baked-in default is used
            cfg.pop("update_manifest_url", None)
        cfg["backup_keep_count"] = int(self.backup_count_spin.value())
        app_config.save_config(cfg)
        self.accept()


def show_settings(project_folder, parent=None):
    """Show the settings dialog. Returns True if the user clicked OK."""
    dlg = SettingsDialog(project_folder, parent)
    return dlg.exec_() == QDialog.Accepted
