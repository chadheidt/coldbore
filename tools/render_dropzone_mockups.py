"""Render three drop-zone design variants as a single side-by-side PNG.

Used for design review when comparing UI directions before committing to a
refactor. Run, view the PNG, pick a variant.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QImage, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap,
)
from PyQt5.QtWidgets import QApplication

import theme

# ---- Mockup geometry ----
W, H = 520, 360
CARD_M = 28  # margin around inner card

# ============================================================================
# Hero icon painters
# ============================================================================

def draw_csv_crosshair_icon(p, cx, cy, size=72):
    """CSV file silhouette with an accent-colored crosshair badge in the
    lower-right corner — the 'Loadscope CSV import' visual."""
    accent = QColor(theme.ACCENT)
    text_color = QColor(theme.TEXT_PRIMARY)

    doc_w = size * 0.72
    doc_h = size * 0.92
    doc_x = cx - doc_w / 2
    doc_y = cy - doc_h / 2 - 4
    fold = 14

    # File body
    body = QPainterPath()
    body.moveTo(doc_x, doc_y)
    body.lineTo(doc_x + doc_w - fold, doc_y)
    body.lineTo(doc_x + doc_w, doc_y + fold)
    body.lineTo(doc_x + doc_w, doc_y + doc_h)
    body.lineTo(doc_x, doc_y + doc_h)
    body.closeSubpath()
    p.setPen(QPen(text_color, 2))
    p.setBrush(QColor(theme.BG_BASE))
    p.drawPath(body)

    # Corner fold lines
    p.drawLine(QPointF(doc_x + doc_w - fold, doc_y),
               QPointF(doc_x + doc_w - fold, doc_y + fold))
    p.drawLine(QPointF(doc_x + doc_w - fold, doc_y + fold),
               QPointF(doc_x + doc_w, doc_y + fold))

    # "CSV" label inside the file
    p.setFont(QFont("Helvetica Neue", int(size * 0.16), QFont.Bold))
    p.setPen(QColor(theme.TEXT_SECONDARY))
    p.drawText(
        QRectF(doc_x, doc_y + doc_h * 0.35, doc_w, doc_h * 0.3),
        Qt.AlignCenter, "CSV",
    )

    # Crosshair badge
    badge_r = size * 0.22
    bx, by = doc_x + doc_w - 4, doc_y + doc_h - 4
    p.setBrush(QBrush(accent))
    p.setPen(QPen(QColor(theme.BG_BASE), 3))
    p.drawEllipse(QPointF(bx, by), badge_r, badge_r)
    # White crosshair on the badge
    p.setPen(QPen(QColor("#ffffff"), 2))
    tick = badge_r * 0.7
    p.drawLine(QPointF(bx - tick, by), QPointF(bx + tick, by))
    p.drawLine(QPointF(bx, by - tick), QPointF(bx, by + tick))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(bx, by), badge_r * 0.32, badge_r * 0.32)


def draw_simple_crosshair(p, cx, cy, size=64):
    """Compact crosshair: concentric rings + cross + center dot."""
    p.setBrush(Qt.NoBrush)
    color = QColor(theme.TEXT_PRIMARY)
    p.setPen(QPen(color, 1.6))
    for r_frac in (0.20, 0.36, 0.52):
        p.drawEllipse(QPointF(cx, cy), size * r_frac, size * r_frac)
    tick = size * 0.58
    p.drawLine(QPointF(cx - tick, cy), QPointF(cx + tick, cy))
    p.drawLine(QPointF(cx, cy - tick), QPointF(cx, cy + tick))
    p.setBrush(QBrush(color))
    p.drawEllipse(QPointF(cx, cy), 2.5, 2.5)


def draw_target_with_arrow(p, cx, cy, size=88):
    """Big bullseye target with an arrow striking center — for the bold variant."""
    accent = QColor(theme.ACCENT)
    navy = QColor("#1f4e78")
    rings = [
        (0.50, navy),
        (0.40, QColor("#ffffff")),
        (0.30, accent),
        (0.20, QColor("#ffffff")),
        (0.08, navy),
    ]
    p.setPen(Qt.NoPen)
    for r_frac, color in rings:
        p.setBrush(QBrush(color))
        p.drawEllipse(QPointF(cx, cy), size * r_frac, size * r_frac)
    # Arrow shaft from upper-left to center
    p.setPen(QPen(QColor(theme.TEXT_PRIMARY), 3))
    start = QPointF(cx - size * 0.55, cy - size * 0.55)
    end = QPointF(cx + 2, cy + 2)
    p.drawLine(start, end)
    # Arrow head
    head = QPainterPath()
    head.moveTo(end)
    head.lineTo(QPointF(cx - 6, cy + 2))
    head.lineTo(QPointF(cx + 2, cy - 6))
    head.closeSubpath()
    p.setBrush(QBrush(QColor(theme.TEXT_PRIMARY)))
    p.setPen(Qt.NoPen)
    p.drawPath(head)
    # Fletching at tail
    p.setPen(QPen(accent, 2))
    p.drawLine(start, QPointF(start.x() - 8, start.y() + 4))
    p.drawLine(start, QPointF(start.x() - 4, start.y() - 8))


def draw_soft_shadow(p, rect, blur_layers=8, max_alpha=70, y_offset=6):
    """Fake a soft drop shadow by stacking offset rounded-rect alpha layers."""
    p.setPen(Qt.NoPen)
    for i in range(blur_layers, 0, -1):
        alpha = int(max_alpha * (i / blur_layers) ** 2 * 0.4)
        spread = i * 1.5
        offset = y_offset
        shadow_rect = rect.adjusted(-spread, -spread + offset, spread, spread + offset)
        p.setBrush(QBrush(QColor(0, 0, 0, alpha)))
        p.drawRoundedRect(shadow_rect, 14 + i * 0.5, 14 + i * 0.5)


# ============================================================================
# Variant A — Refined card (recommended)
# ============================================================================

def variant_a_refined_card():
    pm = QPixmap(W, H)
    pm.fill(QColor(theme.BG_BASE))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Subtle background reticle ghost (brand element, very low alpha)
    _draw_background_reticle(p, W / 2, H / 2 + 10, alpha=22)

    # Soft shadow + card surface
    card = QRectF(CARD_M, CARD_M, W - 2 * CARD_M, H - 2 * CARD_M)
    draw_soft_shadow(p, card, blur_layers=6, max_alpha=110, y_offset=8)
    p.setBrush(QBrush(QColor(theme.BG_ELEVATED)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(card, 14, 14)

    # Hero icon top-third
    icon_cx = W / 2
    icon_cy = card.top() + 70
    draw_csv_crosshair_icon(p, icon_cx, icon_cy, 80)

    # Title
    p.setFont(QFont("Helvetica Neue", 19, QFont.DemiBold))
    p.setPen(QColor(theme.TEXT_PRIMARY))
    p.drawText(
        QRectF(card.left(), card.top() + 145, card.width(), 36),
        Qt.AlignCenter, "Drop your range data",
    )

    # File-type chips
    _draw_chips(p, ["Garmin Xero", "BallisticX"],
                cx=W / 2, cy=card.top() + 200,
                bg=QColor(theme.BG_SURFACE),
                fg=QColor(theme.TEXT_SECONDARY))

    # Footer hint
    p.setFont(QFont("Helvetica Neue", 11))
    p.setPen(QColor(theme.TEXT_TERTIARY))
    p.drawText(
        QRectF(card.left(), card.bottom() - 36, card.width(), 22),
        Qt.AlignCenter, "Drop multiple at once · format auto-detected",
    )

    p.end()
    return pm


# ============================================================================
# Variant B — Modern Apple-style minimal
# ============================================================================

def variant_b_apple_minimal():
    pm = QPixmap(W, H)
    pm.fill(QColor(theme.BG_BASE))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # No card outline — just subtle inner glow ring (hover-state preview)
    glow_rect = QRectF(60, 60, W - 120, H - 120)
    pen = QPen(QColor(180, 200, 230, 22), 1.5)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(glow_rect, 18, 18)

    # Compact crosshair icon — top-third, centered
    draw_simple_crosshair(p, W / 2, H / 2 - 50, 72)

    # Title (Apple uses heavier weight at smaller sizes)
    p.setFont(QFont("Helvetica Neue", 17, QFont.DemiBold))
    p.setPen(QColor(theme.TEXT_PRIMARY))
    p.drawText(
        QRectF(0, H / 2 + 10, W, 28),
        Qt.AlignCenter, "Drop range data here",
    )

    # Subtitle — Apple-style: smaller, secondary color, dot separator
    p.setFont(QFont("Helvetica Neue", 12))
    p.setPen(QColor(theme.TEXT_SECONDARY))
    p.drawText(
        QRectF(0, H / 2 + 42, W, 22),
        Qt.AlignCenter, "Garmin Xero  ·  BallisticX",
    )

    p.end()
    return pm


# ============================================================================
# Variant C — Bold branded onboarding
# ============================================================================

def variant_c_bold_onboarding():
    pm = QPixmap(W, H)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Subtle navy → graphite vertical gradient background
    grad = QLinearGradient(0, 0, 0, H)
    grad.setColorAt(0.0, QColor("#1f3147"))
    grad.setColorAt(1.0, QColor(theme.BG_BASE))
    p.fillRect(QRectF(0, 0, W, H), QBrush(grad))

    # Hero target illustration left side
    icon_cx = 110
    icon_cy = H / 2
    draw_target_with_arrow(p, icon_cx, icon_cy, 100)

    # Right column — stacked title + steps
    text_x = 200
    text_w = W - text_x - 30

    # Title
    p.setFont(QFont("Helvetica Neue", 18, QFont.Bold))
    p.setPen(QColor(theme.TEXT_PRIMARY))
    p.drawText(QRectF(text_x, 60, text_w, 28),
               Qt.AlignLeft, "Bring your range data")

    # Underline accent
    p.setPen(QPen(QColor(theme.ACCENT), 3))
    p.drawLine(QPointF(text_x, 96), QPointF(text_x + 60, 96))

    # Numbered steps
    p.setFont(QFont("Helvetica Neue", 12))
    p.setPen(QColor(theme.TEXT_SECONDARY))
    steps = [
        "1.  Drag your CSVs in",
        "2.  Loadscope sorts them",
        "3.  Click Import to build",
    ]
    for i, step in enumerate(steps):
        p.drawText(QRectF(text_x, 130 + i * 28, text_w, 24),
                   Qt.AlignLeft, step)

    # File-type chips below steps
    _draw_chips(p, ["Garmin Xero", "BallisticX"],
                cx=text_x + 80, cy=H - 50,
                bg=QColor("#2a3a4d"), fg=QColor(theme.TEXT_PRIMARY),
                left_align=True)

    p.end()
    return pm


# ============================================================================
# Helpers
# ============================================================================

def _draw_chips(p, labels, cx, cy, bg, fg, left_align=False):
    """Draw rounded pill 'chips' centered horizontally at cx (or starting at cx)."""
    p.setFont(QFont("Helvetica Neue", 10, QFont.DemiBold))
    fm = p.fontMetrics()
    chips = []
    total_w = 0
    spacing = 12
    for label in labels:
        w = fm.width(label) + 24
        chips.append((label, w))
        total_w += w
    total_w += spacing * (len(chips) - 1)

    if left_align:
        x = cx - total_w / 2 + total_w / 2  # default behavior — left-anchored
        x = cx - total_w / 2
    else:
        x = cx - total_w / 2
    y = cy - 12
    for label, w in chips:
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(theme.BORDER_MEDIUM), 1))
        p.drawRoundedRect(QRectF(x, y, w, 24), 12, 12)
        p.setPen(fg)
        p.drawText(QRectF(x, y, w, 24), Qt.AlignCenter, label)
        x += w + spacing


def _draw_background_reticle(p, cx, cy, alpha=30):
    """Faint background reticle (brand pattern)."""
    color = QColor(theme.TEXT_PRIMARY)
    color.setAlpha(alpha)
    p.setPen(QPen(color, 1))
    p.setBrush(Qt.NoBrush)
    for r in (40, 80, 130):
        p.drawEllipse(QPointF(cx, cy), r, r)
    # Crosshair
    p.drawLine(QPointF(cx - 160, cy), QPointF(cx + 160, cy))
    p.drawLine(QPointF(cx, cy - 110), QPointF(cx, cy + 110))


# ============================================================================
# Main
# ============================================================================

def main():
    app = QApplication.instance() or QApplication(sys.argv)

    pm_a = variant_a_refined_card()
    pm_b = variant_b_apple_minimal()
    pm_c = variant_c_bold_onboarding()

    LABEL_H = 40
    SPACING = 24
    DESC_H = 50
    total_w = W * 3 + SPACING * 4
    total_h = H + LABEL_H + DESC_H + 32

    combined = QPixmap(total_w, total_h)
    combined.fill(QColor("#1a1c1f"))
    p = QPainter(combined)
    p.setRenderHint(QPainter.Antialiasing)

    p.setFont(QFont("Helvetica Neue", 14, QFont.Bold))
    p.setPen(QColor(theme.TEXT_PRIMARY))
    title_descs = [
        ("A · Refined card  (recommended)",
         "Solid surface, soft drop shadow, hero CSV+crosshair icon. Familiar app card aesthetic — Things, Bear, Dropbox."),
        ("B · Modern Apple-style minimal",
         "No border, no card outline. Pure surface + soft glow ring. Native macOS Big Sur/Ventura design language."),
        ("C · Bold branded onboarding",
         "Navy gradient + target hero + numbered steps. Most personality, most marketing-y, biggest departure from current."),
    ]
    for i, (label, desc) in enumerate(title_descs):
        x = SPACING + i * (W + SPACING)
        # Bold label
        p.setFont(QFont("Helvetica Neue", 14, QFont.Bold))
        p.setPen(QColor(theme.TEXT_PRIMARY))
        p.drawText(QRectF(x, 14, W, 24), Qt.AlignCenter, label)
        # Description
        p.setFont(QFont("Helvetica Neue", 11))
        p.setPen(QColor(theme.TEXT_SECONDARY))
        p.drawText(
            QRectF(x + 10, 38, W - 20, DESC_H - 10),
            Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, desc,
        )

    # Mockups below
    for i, pm in enumerate([pm_a, pm_b, pm_c]):
        x = SPACING + i * (W + SPACING)
        y = LABEL_H + DESC_H + 4
        p.drawPixmap(int(x), int(y), pm)

    p.end()
    out = "/Users/macbook/Desktop/Loadscope dropzone mockups.png"
    combined.save(out)
    print(f"Saved: {out}")
    return out


if __name__ == "__main__":
    main()
