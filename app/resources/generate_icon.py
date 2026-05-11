"""
Generate the Loadscope app icon.

Design: a brass rifle cartridge angled diagonally in front of a classic ring
target, contained in a dark rounded-square macOS-style backdrop.

Output: AppIcon.icns next to this script, plus an icon.iconset/ folder with
all the individual PNGs that went into it.

Run:
    /usr/bin/python3 app/resources/generate_icon.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PyQt5.QtWidgets import QApplication


# ============================================================
# Color palette for the icon
# ============================================================
BG_DARK = QColor("#22262e")              # the rounded-square backdrop
BG_DARKER = QColor("#16181d")            # subtle radial vignette

TARGET_BG = QColor("#f3eee0")            # cream paper
TARGET_RING_DARK = QColor("#1a1a1a")     # the black scoring rings
TARGET_BULLSEYE = QColor("#c8232c")      # red bullseye dot

CASE_DARK = QColor("#5a4010")            # brass shadow
CASE_MID = QColor("#a8821e")             # brass body
CASE_BRIGHT = QColor("#e8c44a")          # brass highlight
CASE_PEAK = QColor("#fae28a")            # brass specular tip

CASE_RIM = QColor("#3d2c08")             # extractor groove / rim
PRIMER_DARK = QColor("#2a1a05")
PRIMER_MID = QColor("#5a3a0a")

BULLET_DARK = QColor("#5a3010")          # copper-jacket shadow
BULLET_MID = QColor("#b87333")           # copper jacket body
BULLET_BRIGHT = QColor("#e6a060")        # copper highlight
BULLET_TIP_DARK = QColor("#2a1808")


def draw_icon(painter, size):
    """Draw the icon at the given square size (in pixels)."""
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # ---- Rounded-square dark background -------------------------------
    bg_radius = size * 0.225
    painter.setPen(Qt.NoPen)
    painter.setBrush(BG_DARK)
    painter.drawRoundedRect(0, 0, size, size, bg_radius, bg_radius)

    # Subtle radial vignette to give depth
    vignette = QRadialGradient(size / 2, size / 2, size * 0.7)
    vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
    vignette.setColorAt(1.0, QColor(0, 0, 0, 80))
    painter.setBrush(QBrush(vignette))
    painter.drawRoundedRect(0, 0, size, size, bg_radius, bg_radius)

    # ---- Target rings -------------------------------------------------
    cx = size / 2
    cy = size / 2
    target_r = size * 0.42

    # Cream paper background
    painter.setBrush(TARGET_BG)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QPointF(cx, cy), target_r, target_r)

    # Concentric scoring rings — drawn as filled circles, alternating dark/cream
    n_rings = 5
    for i in range(n_rings):
        r = target_r * (1 - i / (n_rings + 0.5))
        painter.setBrush(TARGET_RING_DARK if i % 2 == 1 else TARGET_BG)
        painter.drawEllipse(QPointF(cx, cy), r, r)

    # Red bullseye in the very center
    painter.setBrush(TARGET_BULLSEYE)
    painter.drawEllipse(QPointF(cx, cy), target_r * 0.10, target_r * 0.10)

    # ---- Brass cartridge, drawn vertically (bullet pointing up) -------
    painter.save()
    painter.translate(cx, cy)
    painter.rotate(-90)  # vertical — bullet up, case base down

    # Cartridge proportions (relative to icon size)
    case_length = size * 0.46
    case_width = size * 0.13
    bullet_length = size * 0.20
    bullet_width = size * 0.10
    total_length = case_length + bullet_length

    case_x = -total_length / 2
    case_y = -case_width / 2
    bullet_x = case_x + case_length

    # Outline pen — visible at large sizes, vanishes at small ones
    outline_w = max(0.5, size / 350)
    outline = QPen(QColor("#1a1206"), outline_w)
    outline.setJoinStyle(Qt.RoundJoin)
    outline.setCapStyle(Qt.RoundCap)

    # ---- Brass case (rectangle with cylindrical gradient) -------------
    case_grad = QLinearGradient(0, case_y, 0, case_y + case_width)
    case_grad.setColorAt(0.00, CASE_DARK)
    case_grad.setColorAt(0.18, CASE_MID)
    case_grad.setColorAt(0.42, CASE_BRIGHT)
    case_grad.setColorAt(0.55, CASE_PEAK)
    case_grad.setColorAt(0.68, CASE_BRIGHT)
    case_grad.setColorAt(0.82, CASE_MID)
    case_grad.setColorAt(1.00, CASE_DARK)
    painter.setBrush(QBrush(case_grad))
    painter.setPen(outline)
    painter.drawRect(QRectF(case_x, case_y, case_length, case_width))

    # ---- Extractor groove + rim at the base of the case ---------------
    rim_w = case_width * 0.12
    painter.setBrush(CASE_RIM)
    painter.drawRect(QRectF(case_x, case_y, rim_w, case_width))

    # ---- Primer pocket — small dark circle at base --------------------
    primer_cx = case_x + rim_w * 0.45
    primer_r = case_width * 0.18
    primer_grad = QRadialGradient(primer_cx, 0, primer_r * 1.2)
    primer_grad.setColorAt(0.0, PRIMER_MID)
    primer_grad.setColorAt(1.0, PRIMER_DARK)
    painter.setBrush(QBrush(primer_grad))
    painter.setPen(QPen(QColor("#1a0e02"), outline_w * 0.6))
    painter.drawEllipse(QPointF(primer_cx, 0), primer_r, primer_r)

    # ---- Bullet (copper jacket, ogive shape) --------------------------
    # Polygon points — base on left, tapered tip on right
    ogive_start = bullet_x + bullet_length * 0.45
    points = [
        QPointF(bullet_x, -bullet_width / 2),                         # base top
        QPointF(bullet_x, bullet_width / 2),                          # base bottom
        QPointF(ogive_start, bullet_width / 2),                       # ogive bottom
        QPointF(bullet_x + bullet_length, 0),                         # tip
        QPointF(ogive_start, -bullet_width / 2),                      # ogive top
    ]

    bullet_grad = QLinearGradient(0, -bullet_width / 2, 0, bullet_width / 2)
    bullet_grad.setColorAt(0.00, BULLET_DARK)
    bullet_grad.setColorAt(0.45, BULLET_MID)
    bullet_grad.setColorAt(0.55, BULLET_BRIGHT)
    bullet_grad.setColorAt(0.65, BULLET_MID)
    bullet_grad.setColorAt(1.00, BULLET_TIP_DARK)
    painter.setBrush(QBrush(bullet_grad))
    painter.setPen(outline)
    painter.drawPolygon(QPolygonF(points))

    # ---- Cannelure — a thin ring around the bullet shaft --------------
    cannelure_x = bullet_x + bullet_length * 0.18
    cannelure_w = bullet_length * 0.04
    painter.setBrush(BULLET_DARK)
    painter.setPen(Qt.NoPen)
    painter.drawRect(QRectF(cannelure_x, -bullet_width / 2,
                            cannelure_w, bullet_width))

    # ---- Case mouth — thin dark line where bullet meets case ---------
    painter.setBrush(CASE_RIM)
    painter.drawRect(QRectF(case_x + case_length - case_width * 0.04, case_y,
                            case_width * 0.04, case_width))

    painter.restore()


def render_size(size, output_path):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)  # transparent
    painter = QPainter(img)
    draw_icon(painter, size)
    painter.end()
    img.save(str(output_path), "PNG")


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    here = Path(__file__).resolve().parent
    iconset = here / "icon.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()

    # Required PNG sizes for an .icns bundle
    sizes = [
        (16,   "icon_16x16.png"),
        (32,   "icon_16x16@2x.png"),
        (32,   "icon_32x32.png"),
        (64,   "icon_32x32@2x.png"),
        (128,  "icon_128x128.png"),
        (256,  "icon_128x128@2x.png"),
        (256,  "icon_256x256.png"),
        (512,  "icon_256x256@2x.png"),
        (512,  "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    print(f"Generating PNGs into {iconset}...")
    for size, name in sizes:
        render_size(size, iconset / name)
        print(f"  ✓ {name}  ({size}x{size})")

    # Combine into .icns using macOS's iconutil
    icns_path = here / "AppIcon.icns"
    print(f"\nRunning iconutil to produce {icns_path}…")
    result = subprocess.run(
        ["iconutil", "-c", "icns", "-o", str(icns_path), str(iconset)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"iconutil failed:\n{result.stderr}")
        sys.exit(1)

    print(f"\nDone. Icon at: {icns_path}")
    print("Rebuild the .app to bake the new icon in:")
    print("    double-click  Build App.command")


if __name__ == "__main__":
    main()
