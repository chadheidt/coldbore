"""
Opt-in crash reporter.

When the app hits an unhandled exception, this module shows the user a dialog
with the traceback and offers to email it to the support address. The user
sees exactly what would be sent (no hidden telemetry) and chooses whether
to send.

Privacy notes:
- Only sends what the user can see in the dialog.
- No automatic submission — every send requires the user to click and the
  email goes through their default mail client (so they can review/edit
  before sending).
- No system info beyond app version and Python version.

Plug it in by calling `install(parent_window=None)` once on app startup.
"""

import datetime
import platform
import sys
import traceback
import urllib.parse

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from version import APP_NAME, APP_VERSION


SUPPORT_EMAIL = "coldboreapp@gmail.com"

# Sentinel to avoid showing multiple stacked crash dialogs if exceptions
# cascade — we report the first one and quietly log the rest to stderr.
_already_reporting = False


def _format_report(exc_type, exc_value, exc_tb):
    """Build the human-readable crash report text."""
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    return (
        f"{APP_NAME} v{APP_VERSION} — crash report\n"
        f"Date: {datetime.datetime.now().isoformat(timespec='seconds')}\n"
        f"Python: {sys.version.split()[0]}\n"
        f"Platform: {platform.platform()}\n"
        f"\n"
        f"Traceback:\n"
        f"{''.join(tb_lines)}"
    )


def _show_crash_dialog(report_text, parent=None):
    """Show the crash dialog with full report visible. Lets user click Send,
    Copy, or Close. Returns nothing — the user's choice triggers the action."""
    dlg = QDialog(parent)
    dlg.setWindowTitle(f"{APP_NAME} — Unexpected Error")
    dlg.setMinimumSize(640, 480)
    dlg.setModal(True)

    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(20, 18, 20, 14)
    layout.setSpacing(12)

    header = QLabel(
        f"<b>{APP_NAME} hit an unexpected error.</b><br><br>"
        f"You can review what would be sent below, then choose to email it "
        f"to the developer (helps fix the bug) or just close the dialog. "
        f"Nothing is sent automatically."
    )
    header.setWordWrap(True)
    layout.addWidget(header)

    box = QPlainTextEdit()
    box.setPlainText(report_text)
    box.setReadOnly(True)
    layout.addWidget(box, stretch=1)

    btns = QDialogButtonBox()
    copy_btn = QPushButton("Copy to Clipboard")
    send_btn = QPushButton(f"Send via Email")
    send_btn.setObjectName("primary")
    close_btn = QPushButton("Close")
    btns.addButton(copy_btn, QDialogButtonBox.ActionRole)
    btns.addButton(send_btn, QDialogButtonBox.AcceptRole)
    btns.addButton(close_btn, QDialogButtonBox.RejectRole)
    layout.addWidget(btns)

    def on_copy():
        QApplication.clipboard().setText(report_text)
        QMessageBox.information(dlg, "Copied", "Report copied to clipboard.")

    def on_send():
        subject = f"{APP_NAME} v{APP_VERSION} — crash report"
        body = "Hi,%0A%0AHere's a crash report from Cold Bore.%0A%0A"
        body += urllib.parse.quote(report_text)
        mailto = f"mailto:{SUPPORT_EMAIL}?subject={urllib.parse.quote(subject)}&body={body}"
        QDesktopServices.openUrl(QUrl(mailto))
        dlg.accept()

    copy_btn.clicked.connect(on_copy)
    send_btn.clicked.connect(on_send)
    close_btn.clicked.connect(dlg.reject)

    dlg.exec_()


def _excepthook(exc_type, exc_value, exc_tb):
    """Custom sys.excepthook — replaces the default Python "print to stderr
    and exit" behavior with a user-friendly dialog."""
    global _already_reporting

    # KeyboardInterrupt should still kill the app cleanly
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    # Cascading exception protection — only show one dialog at a time
    if _already_reporting:
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    _already_reporting = True

    report = _format_report(exc_type, exc_value, exc_tb)
    # Print to stderr too so anyone running from Terminal still sees it
    sys.stderr.write(report)
    sys.stderr.write("\n")

    # Show the dialog if a QApplication is running
    if QApplication.instance() is not None:
        try:
            _show_crash_dialog(report)
        except Exception:
            # If even the crash dialog itself crashes, give up gracefully
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    _already_reporting = False


def install():
    """Install the crash handler. Call once at app startup, after QApplication exists."""
    sys.excepthook = _excepthook
