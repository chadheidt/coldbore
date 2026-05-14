"""Render the actual DropZone widget (from app/main.py) to a PNG.

Used to verify the refined-card refactor looks like the mockup before
shipping. Renders in idle state and hover state side-by-side.
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame

import theme
from main import DropZone

WIDTH = 560
HEIGHT = 320


def _render_dropzone(state="idle"):
    # Wrap in a parent QFrame with the app's bg color so the drop shadow
    # has something to fall onto (otherwise it composites onto transparent
    # background and disappears).
    container = QFrame()
    container.setFixedSize(WIDTH, HEIGHT)
    container.setStyleSheet(f"background-color: {theme.BG_BASE}; border: none;")
    from PyQt5.QtWidgets import QVBoxLayout
    container_layout = QVBoxLayout(container)
    container_layout.setContentsMargins(20, 20, 20, 20)
    dz = DropZone(on_drop=lambda paths: None)
    container_layout.addWidget(dz)
    if state == "hover":
        dz._set_hover_style()
    else:
        dz._set_idle_style()
    container.show()
    QApplication.processEvents()
    QApplication.processEvents()  # second tick for layout settle
    pm = container.grab()
    container.hide()
    container.deleteLater()
    return pm


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    idle = _render_dropzone("idle")
    hover = _render_dropzone("hover")

    LABEL_H = 36
    PAD = 24
    total_w = WIDTH * 2 + PAD * 3
    total_h = HEIGHT + LABEL_H + PAD * 2

    canvas = QPixmap(total_w, total_h)
    canvas.fill(QColor("#1a1c1f"))
    p = QPainter(canvas)
    p.setRenderHint(QPainter.Antialiasing)
    p.setFont(QFont("Helvetica Neue", 13, QFont.Bold))
    p.setPen(QColor(theme.TEXT_PRIMARY))
    for i, label in enumerate(["Idle state", "Hover state (drag-over)"]):
        x = PAD + i * (WIDTH + PAD)
        p.drawText(QRectF(x, 14, WIDTH, LABEL_H), Qt.AlignCenter, label)
    for i, pm in enumerate([idle, hover]):
        x = PAD + i * (WIDTH + PAD)
        p.drawPixmap(int(x), LABEL_H + 10, pm)
    p.end()

    out = "/Users/macbook/Desktop/Loadscope dropzone refined.png"
    canvas.save(out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    main()
