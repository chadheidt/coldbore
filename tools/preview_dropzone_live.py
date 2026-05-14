"""Pop a small Qt window showing ONLY the new DropZone widget.

Used to preview the refined-card visual without launching the full Loadscope
app (which would trigger license/wizard flows). Idle state on the left half
of the window, hover state on the right half so Chad can compare.

Quit by closing the window.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget,
)

import theme
from main import DropZone


class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loadscope Drop Zone — refined card preview")
        self.setStyleSheet(f"background-color: {theme.BG_BASE};")
        self.resize(1480, 520)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(28, 28, 28, 28)
        outer.setSpacing(20)

        # Heading
        heading = QLabel("Refined-card drop zone — three states")
        heading.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: 18px; font-weight: 600;"
        )
        outer.addWidget(heading)

        # Three side-by-side states
        row = QHBoxLayout()
        row.setSpacing(28)

        def chip_click_demo(name):
            QLabel(f"Chip clicked: {name}").show()
            print(f"[preview] chip click: {name}")

        def make_state(label_text, configure):
            box = QVBoxLayout()
            tag = QLabel(label_text)
            tag.setAlignment(Qt.AlignCenter)
            tag.setStyleSheet(
                f"color: {theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;"
            )
            box.addWidget(tag)
            dz = DropZone(on_drop=lambda paths: None,
                          on_chip_click=chip_click_demo)
            configure(dz)
            box.addWidget(dz)
            return box, dz

        # 1. Idle state — neutral
        idle_box, self.idle_dz = make_state(
            "Idle (no files dropped yet)",
            lambda dz: dz._set_idle_style(),
        )
        row.addLayout(idle_box)

        # 2. Hover state — drag-over preview
        hover_box, self.hover_dz = make_state(
            "Hover (drag-over)",
            lambda dz: dz._set_hover_style(),
        )
        row.addLayout(hover_box)

        # 3. Staged state — files dropped, CTA visible
        def make_staged(dz):
            dz._set_idle_style()
            dz.set_staged_state(3, "3 Garmin · 1 BallisticX staged")
        staged_box, self.staged_dz = make_state(
            "After drop (staged — Run Import CTA)",
            make_staged,
        )
        row.addLayout(staged_box)

        outer.addLayout(row)


def main():
    app = QApplication(sys.argv)
    win = PreviewWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
