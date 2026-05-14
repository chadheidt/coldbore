"""Pop the FAQ dialog standalone so it can be visually reviewed without
launching the full Loadscope app (which would trigger license/wizard flows)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from PyQt5.QtWidgets import QApplication

from faq_dialog import FaqDialog


def main():
    app = QApplication(sys.argv)
    dlg = FaqDialog()
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
