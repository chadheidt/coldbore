"""Render three alternative hero-icon options for the Refined Card drop zone.

Chad picked the Refined Card direction but didn't like the CSV-folder + crosshair
badge. This script renders the same card layout with three different icon ideas
side-by-side so he can pick the one that best says "drop a CSV here" without
looking like a folder/file icon.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap,
)
from PyQt5.QtWidgets import QApplication

import theme

W, H = 520, 360
CARD_M = 28


# ---------- Soft shadow helper (lifted from render_dropzone_mockups) ----------

def draw_soft_shadow(p, rect, blur_layers=6, max_alpha=110, y_offset=8):
    p.setPen(Qt.NoPen)
    for i in range(blur_layers, 0, -1):
        alpha = int(max_alpha * (i / blur_layers) ** 2 * 0.4)
        spread = i * 1.5
        offset = y_offset
        shadow_rect = rect.adjusted(-spread, -spread + offset,
                                     spread, spread + offset)
        p.setBrush(QBrush(QColor(0, 0, 0, alpha)))
        p.drawRoundedRect(shadow_rect, 14 + i * 0.5, 14 + i * 0.5)


def draw_chips(p, labels, cx, cy):
    p.setFont(QFont("Helvetica Neue", 11))
    pad_x = 14
    chip_h = 26
    gap = 10
    widths = [p.fontMetrics().horizontalAdvance(s) + 2 * pad_x for s in labels]
    total = sum(widths) + gap * (len(labels) - 1)
    x = cx - total / 2
    for label, w in zip(labels, widths):
        rect = QRectF(x, cy - chip_h / 2, w, chip_h)
        p.setBrush(QBrush(QColor(theme.BG_SURFACE)))
        p.setPen(QPen(QColor(theme.BORDER_MEDIUM), 1))
        p.drawRoundedRect(rect, 13, 13)
        p.setPen(QColor(theme.TEXT_SECONDARY))
        p.drawText(rect, Qt.AlignCenter, label)
        x += w + gap


# ---------- Three alternative hero icons ----------

def icon_big_crosshair(p, cx, cy, size=88):
    """Large precision-rifle crosshair: 3 rings + crosshair + mil-dots + center."""
    fg = QColor(theme.TEXT_PRIMARY)
    accent = QColor(theme.ACCENT)

    # Outer "rifle scope" ring (slightly heavier)
    p.setPen(QPen(fg, 2.2))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy), size * 0.50, size * 0.50)

    # Two inner rings (lighter)
    p.setPen(QPen(QColor(theme.TEXT_PRIMARY).lighter(95), 1.4))
    p.drawEllipse(QPointF(cx, cy), size * 0.35, size * 0.35)
    p.drawEllipse(QPointF(cx, cy), size * 0.20, size * 0.20)

    # Crosshair (full diameter)
    p.setPen(QPen(fg, 1.6))
    tick = size * 0.55
    p.drawLine(QPointF(cx - tick, cy), QPointF(cx + tick, cy))
    p.drawLine(QPointF(cx, cy - tick), QPointF(cx, cy + tick))

    # Mil-dots along the crosshair
    p.setBrush(QBrush(fg))
    p.setPen(Qt.NoPen)
    for d in (size * 0.20, size * 0.35):
        for dx, dy in ((-d, 0), (d, 0), (0, -d), (0, d)):
            p.drawEllipse(QPointF(cx + dx, cy + dy), 1.6, 1.6)

    # Accent center dot (the "you are here" target)
    p.setBrush(QBrush(accent))
    p.drawEllipse(QPointF(cx, cy), 3.5, 3.5)


def icon_drop_arrow_ring(p, cx, cy, size=88):
    """Circular ring with downward chevron arrow inside — universal 'drop here'."""
    fg = QColor(theme.TEXT_PRIMARY)
    accent = QColor(theme.ACCENT)
    bg = QColor(theme.BG_ELEVATED)

    # Ring (dashed for "drop zone" affordance, but heavier than the old version)
    pen = QPen(fg, 2.5)
    pen.setStyle(Qt.DashLine)
    pen.setDashPattern([3, 2.4])
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy), size * 0.46, size * 0.46)

    # Subtle inner accent ring (filled circle, very transparent)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor(accent.red(), accent.green(), accent.blue(), 30)))
    p.drawEllipse(QPointF(cx, cy), size * 0.40, size * 0.40)

    # Downward chevron arrow
    arrow_h = size * 0.42
    arrow_w = size * 0.48
    p.setPen(QPen(accent, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    # Vertical shaft
    p.drawLine(QPointF(cx, cy - arrow_h / 2),
               QPointF(cx, cy + arrow_h / 2 - 4))
    # Chevron head
    p.drawLine(QPointF(cx, cy + arrow_h / 2),
               QPointF(cx - arrow_w / 2, cy + arrow_h / 2 - arrow_w / 2))
    p.drawLine(QPointF(cx, cy + arrow_h / 2),
               QPointF(cx + arrow_w / 2, cy + arrow_h / 2 - arrow_w / 2))


def icon_data_grid(p, cx, cy, size=88):
    """Spreadsheet/data-table grid — clearly says 'tabular data' without folders."""
    fg = QColor(theme.TEXT_PRIMARY)
    accent = QColor(theme.ACCENT)

    cols, rows = 4, 5
    cell_w = size * 0.16
    cell_h = size * 0.13
    grid_w = cols * cell_w
    grid_h = rows * cell_h
    x0 = cx - grid_w / 2
    y0 = cy - grid_h / 2

    # Header row (filled accent — like a column-header band)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(accent))
    p.drawRoundedRect(QRectF(x0, y0, grid_w, cell_h), 3, 3)

    # Body rows — alternating fill for table-stripes look
    stripe = QColor(theme.BG_SURFACE).lighter(110)
    for r in range(1, rows):
        if r % 2 == 0:
            p.setBrush(QBrush(stripe))
            p.drawRect(QRectF(x0, y0 + r * cell_h, grid_w, cell_h))

    # Grid lines (thin)
    p.setPen(QPen(QColor(theme.TEXT_PRIMARY).darker(220), 1))
    for c in range(cols + 1):
        p.drawLine(QPointF(x0 + c * cell_w, y0),
                   QPointF(x0 + c * cell_w, y0 + grid_h))
    for r in range(rows + 1):
        p.drawLine(QPointF(x0, y0 + r * cell_h),
                   QPointF(x0 + grid_w, y0 + r * cell_h))

    # Outer border (heavier)
    p.setPen(QPen(fg, 1.8))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(x0, y0, grid_w, grid_h), 3, 3)


# ---------- Card renderer ----------

def render_card(icon_fn, title="Drop your CSV files here"):
    pm = QPixmap(W, H)
    pm.fill(QColor(theme.BG_BASE))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    card = QRectF(CARD_M, CARD_M, W - 2 * CARD_M, H - 2 * CARD_M)
    draw_soft_shadow(p, card)
    p.setBrush(QBrush(QColor(theme.BG_ELEVATED)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(card, 14, 14)

    # Hero icon
    icon_fn(p, W / 2, card.top() + 78, 88)

    # Title
    p.setFont(QFont("Helvetica Neue", 18, QFont.DemiBold))
    p.setPen(QColor(theme.TEXT_PRIMARY))
    p.drawText(
        QRectF(card.left(), card.top() + 162, card.width(), 32),
        Qt.AlignCenter, title,
    )

    # Chips
    draw_chips(p, ["Garmin Xero", "BallisticX"],
               cx=W / 2, cy=card.top() + 215)

    # Footer hint
    p.setFont(QFont("Helvetica Neue", 11))
    p.setPen(QColor(theme.TEXT_TERTIARY))
    p.drawText(
        QRectF(card.left(), card.bottom() - 36, card.width(), 22),
        Qt.AlignCenter, "Drop multiple at once · format auto-detected",
    )

    p.end()
    return pm


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    _ = app

    pm1 = render_card(icon_big_crosshair)
    pm2 = render_card(icon_drop_arrow_ring)
    pm3 = render_card(icon_data_grid)

    LABEL_H = 36
    SPACING = 24
    total_w = W * 3 + SPACING * 4
    total_h = H + LABEL_H + 70

    combined = QPixmap(total_w, total_h)
    combined.fill(QColor("#1a1c1f"))

    p = QPainter(combined)
    p.setRenderHint(QPainter.Antialiasing)

    # Heading
    p.setFont(QFont("Helvetica Neue", 14, QFont.Bold))
    p.setPen(QColor("#ededed"))
    p.drawText(QRectF(0, 14, total_w, 28), Qt.AlignCenter,
               "Refined Card · pick a hero icon")

    label_y = 50
    mockup_y = label_y + LABEL_H

    items = [
        (pm1, "1 · Big precision crosshair"),
        (pm2, "2 · Drop-arrow ring"),
        (pm3, "3 · Spreadsheet grid"),
    ]
    for i, (pm, label) in enumerate(items):
        x = SPACING + i * (W + SPACING)
        p.setFont(QFont("Helvetica Neue", 12, QFont.Bold))
        p.setPen(QColor("#ededed"))
        p.drawText(QRectF(x, label_y, W, LABEL_H), Qt.AlignCenter, label)
        p.drawPixmap(int(x), mockup_y, pm)

    p.end()

    out = "/Users/macbook/Desktop/Loadscope dropzone icon options.png"
    combined.save(out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    main()
