"""
Visual theme for Loadscope.

Hunter-orange-on-charcoal palette (Direction 1) with the spacing and
typography of a clean modern app (Direction 2). All colors and font sizes
are defined here so a future restyle is one file change.
"""

# ============================================================
# Color palette
# ============================================================

# Backgrounds — solid graphite palette for now (carbon-fiber pattern deferred to end)
BG_BASE = "#2d3036"        # window base — graphite
BG_SURFACE = "#373a41"     # title bars, secondary surfaces
BG_ELEVATED = "#42454c"    # raised cards, drop zone, inputs
BG_INPUT = "#1c1e22"       # log area kept darker so messages pop

# Borders — subtle, not loud
BORDER_SUBTLE = "#4a4d55"
BORDER_MEDIUM = "#5b5f68"

# Carbon fiber weave colors — heavy 3D shading for glossy clearcoat look
CARBON_BASE = BG_BASE
CARBON_FIBER_DEEP = "#0a0c11"     # deepest shadow between fibers
CARBON_FIBER_DARK = "#15181f"     # dark side of fiber bundle
CARBON_FIBER_MID = "#22262e"      # ambient cylinder color
CARBON_FIBER_HIGHLIGHT = "#454a55" # bright specular highlight (the glossy shine)
CARBON_FIBER_TIP = "#5a606b"      # peak specular — just at fiber crown


def generate_carbon_tile(tile_size=64, fiber_width=8):
    """Build a tileable QPixmap of a 2x2 carbon-fiber twill weave with
    heavy 3D fiber shading — meant to evoke a glossy clearcoat over real
    woven fiber bundles (like a Proof Research barrel).

    Each fiber is rendered as a cylindrical bundle with a 5-stop gradient
    (deep shadow, dark, mid, highlight, mid) so light reads as bouncing off
    the rounded crown. Cell boundaries are hidden by alternating which
    direction's fibers sit "on top" so the eye reads it as overlapping weave
    instead of separate squares.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import (
        QBrush,
        QColor,
        QLinearGradient,
        QPainter,
        QPixmap,
    )

    pixmap = QPixmap(tile_size, tile_size)
    pixmap.fill(QColor(CARBON_FIBER_DEEP))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)

    half = tile_size // 2
    deep = QColor(CARBON_FIBER_DEEP)
    dark = QColor(CARBON_FIBER_DARK)
    mid = QColor(CARBON_FIBER_MID)
    highlight = QColor(CARBON_FIBER_HIGHLIGHT)
    tip = QColor(CARBON_FIBER_TIP)

    def fiber_gradient(x0, y0, x1, y1):
        """Cylindrical fiber gradient — deep edge, mid, highlight, mid, deep edge.
        The asymmetric peak (slightly off-center) gives the rounded glossy feel."""
        g = QLinearGradient(x0, y0, x1, y1)
        g.setColorAt(0.00, deep)
        g.setColorAt(0.18, dark)
        g.setColorAt(0.40, mid)
        g.setColorAt(0.55, highlight)
        g.setColorAt(0.62, tip)
        g.setColorAt(0.72, highlight)
        g.setColorAt(0.86, dark)
        g.setColorAt(1.00, deep)
        return g

    def draw_vertical_fibers(x, y, w, h):
        """Draw vertical fibers in the rect (x,y,w,h)."""
        fx = x
        while fx < x + w:
            fw = min(fiber_width, x + w - fx)
            grad = fiber_gradient(fx, 0, fx + fw, 0)
            painter.setBrush(QBrush(grad))
            painter.drawRect(fx, y, fw, h)
            fx += fiber_width

    def draw_horizontal_fibers(x, y, w, h):
        fy = y
        while fy < y + h:
            fh = min(fiber_width, y + h - fy)
            grad = fiber_gradient(0, fy, 0, fy + fh)
            painter.setBrush(QBrush(grad))
            painter.drawRect(x, fy, w, fh)
            fy += fiber_width

    # 2x2 twill: TL & BR have vertical fibers; TR & BL have horizontal fibers.
    # We draw with slight overshoot at each cell boundary so adjacent cells
    # overlap by a fiber width — softening the seams visually.
    overshoot = fiber_width // 2

    # Lay down horizontal fibers first across TR + BL bands (full width strips
    # of the tile), then layer vertical fibers from TL + BR on top. The top
    # layer's strong highlights will visually "weave over" the bottom layer
    # right at the cell boundaries — that's what eliminates the checkerboard.

    # Horizontal fibers: top-right cell (full strip from x=half-overshoot to right)
    draw_horizontal_fibers(half - overshoot, 0, tile_size - half + overshoot, half)
    # Horizontal fibers: bottom-left cell
    draw_horizontal_fibers(0, half, half + overshoot, tile_size - half)

    # Vertical fibers: top-left cell
    draw_vertical_fibers(0, 0, half + overshoot, half + overshoot)
    # Vertical fibers: bottom-right cell
    draw_vertical_fibers(half - overshoot, half - overshoot,
                         tile_size - half + overshoot,
                         tile_size - half + overshoot)

    painter.end()
    return pixmap

# Text — three tiers
TEXT_PRIMARY = "#ededed"
TEXT_SECONDARY = "#b8bec9"
TEXT_TERTIARY = "#6f7682"

# Accent — hunter orange
ACCENT = "#d97706"
ACCENT_HOVER = "#e8870a"
ACCENT_PRESSED = "#b8650a"
ACCENT_DIMMED = "#8a4d05"   # for disabled buttons

# Semantic colors used in the activity log
LOG_GARMIN = "#5fbcd6"      # cool blue
LOG_BALLISTICX = "#d97706"  # accent orange
LOG_SUCCESS = "#7dc97d"     # soft green
LOG_WARNING = "#dcdcaa"     # soft yellow
LOG_ERROR = "#f48771"       # soft red
LOG_DIM = "#6f7682"
LOG_INFO = "#9cdcfe"        # light cyan
LOG_DEFAULT = TEXT_SECONDARY

# Update banner colors
BANNER_BG = "#2a2410"
BANNER_BORDER = "#5a4810"
BANNER_TEXT = "#f4e4b0"
BANNER_LINK = ACCENT


# ============================================================
# Typography
# ============================================================

FONT_SIZE_TINY = 11
FONT_SIZE_SMALL = 12
FONT_SIZE_BODY = 14
FONT_SIZE_DROPZONE = 17
FONT_SIZE_HEADING = 16

# Mono font for the activity log
FONT_MONO_FAMILY = "SF Mono, Menlo, Consolas, monospace"


# ============================================================
# Spacing
# ============================================================

PAD_WINDOW = 24
PAD_DROPZONE = 44
GAP_LARGE = 22
GAP_MEDIUM = 14
RADIUS = 10


# ============================================================
# Stylesheet — applied to the whole QApplication
# ============================================================

def application_stylesheet():
    """Return a QSS string covering all the standard widgets."""
    return f"""
    /* Base — applied to all widgets, but no background here so the
       carbon-fiber central widget (which paints its own background) can
       show through. Top-level windows and dialogs get an explicit fill below. */
    QWidget {{
        color: {TEXT_PRIMARY};
        font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
        font-size: {FONT_SIZE_BODY}px;
    }}

    /* Top-level windows fill themselves with the base color so the title bar
       and any letterbox area around the central widget look right. */
    QMainWindow {{
        background-color: {BG_BASE};
    }}

    /* Buttons — default subtle outlined style */
    QPushButton {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER_MEDIUM};
        padding: 8px 16px;
        border-radius: 6px;
        font-size: {FONT_SIZE_SMALL}px;
    }}
    QPushButton:hover {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border-color: {BORDER_MEDIUM};
    }}
    QPushButton:pressed {{
        background-color: {BG_ELEVATED};
    }}
    QPushButton:disabled {{
        color: {TEXT_TERTIARY};
        border-color: {BORDER_SUBTLE};
        background-color: transparent;
    }}

    /* Primary call-to-action button — hunter orange */
    QPushButton#primary {{
        background-color: {ACCENT};
        color: #1a1208;
        border: none;
        font-weight: 600;
        letter-spacing: 0.4px;
        padding: 9px 22px;
    }}
    QPushButton#primary:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton#primary:pressed {{
        background-color: {ACCENT_PRESSED};
    }}
    QPushButton#primary:disabled {{
        background-color: {ACCENT_DIMMED};
        color: {TEXT_TERTIARY};
    }}

    /* Read-only log area */
    QTextEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER_SUBTLE};
        border-radius: {RADIUS - 2}px;
        padding: 10px 12px;
    }}

    /* Line edits in the wizard */
    QLineEdit {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_MEDIUM};
        padding: 8px 10px;
        border-radius: 6px;
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}

    /* Tooltips and dialogs match the theme */
    QDialog {{
        background-color: {BG_BASE};
    }}

    /* Labels — transparent so carbon shows through. Specific labels
       (drop zone, update banner) override this in their own stylesheets. */
    QLabel {{
        background-color: transparent;
        color: {TEXT_PRIMARY};
    }}

    /* Menu bar (whether system bar or in-window) */
    QMenuBar {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border-bottom: 1px solid {BORDER_SUBTLE};
    }}
    QMenuBar::item {{
        background: transparent;
        padding: 6px 12px;
    }}
    QMenuBar::item:selected {{
        background-color: {BG_ELEVATED};
    }}
    QMenu {{
        background-color: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_SUBTLE};
    }}
    QMenu::item:selected {{
        background-color: {ACCENT};
        color: #1a1208;
    }}

    /* Scrollbar — subtle, dark */
    QScrollBar:vertical {{
        background: {BG_BASE};
        width: 10px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER_MEDIUM};
        min-height: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_TERTIARY};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """


def dropzone_idle_stylesheet():
    """v0.14 refined card: solid surface, no dashed border, hero crosshair
    + chip badges. Targets QFrame#DropZone + child labels by objectName."""
    return f"""
        QFrame#DropZone {{
            background-color: {BG_ELEVATED};
            border: 1px solid {BG_ELEVATED};
            border-radius: 14px;
        }}
        QLabel#DropZoneTitle {{
            font-size: 18pt;
            font-weight: 600;
            color: {TEXT_PRIMARY};
            background: transparent;
            border: none;
            padding: 0;
        }}
        QLabel#DropZoneChip {{
            background-color: {BG_SURFACE};
            border: 1px solid {BORDER_MEDIUM};
            border-radius: 13px;
            padding: 5px 14px;
            font-size: 11px;
            color: {TEXT_SECONDARY};
        }}
        QLabel#DropZoneFooter {{
            color: {TEXT_TERTIARY};
            font-size: 11px;
            background: transparent;
            border: none;
            padding: 0;
        }}
        QPushButton#DropZoneCTA {{
            background-color: {ACCENT};
            color: #1a1208;
            border: none;
            border-radius: 8px;
            font-size: 13pt;
            font-weight: 600;
            letter-spacing: 0.4px;
            padding: 10px 28px;
        }}
        QPushButton#DropZoneCTA:hover {{
            background-color: {ACCENT_HOVER};
        }}
        QPushButton#DropZoneCTA:pressed {{
            background-color: {ACCENT_PRESSED};
        }}
    """


def dropzone_hover_stylesheet():
    """Hover: accent border + accent title color + chip glow."""
    return f"""
        QFrame#DropZone {{
            background-color: {BG_ELEVATED};
            border: 1.5px solid {ACCENT};
            border-radius: 14px;
        }}
        QLabel#DropZoneTitle {{
            font-size: 18pt;
            font-weight: 600;
            color: {ACCENT};
            background: transparent;
            border: none;
            padding: 0;
        }}
        QLabel#DropZoneChip {{
            background-color: rgba(217, 119, 6, 30);
            border: 1px solid {ACCENT};
            border-radius: 13px;
            padding: 5px 14px;
            font-size: 11px;
            color: #f5b56b;
        }}
        QLabel#DropZoneFooter {{
            color: {TEXT_SECONDARY};
            font-size: 11px;
            background: transparent;
            border: none;
            padding: 0;
        }}
    """


def update_banner_stylesheet():
    return f"""
        QLabel {{
            background-color: {BANNER_BG};
            border: 1px solid {BANNER_BORDER};
            border-radius: 6px;
            padding: 12px 16px;
            color: {BANNER_TEXT};
            font-size: {FONT_SIZE_SMALL}px;
        }}
    """


def project_label_stylesheet():
    return f"color: {TEXT_TERTIARY}; font-size: {FONT_SIZE_TINY}px; letter-spacing: 0.6px;"


def status_label_stylesheet():
    return f"color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_BODY}px;"


def section_label_stylesheet():
    return f"color: {TEXT_TERTIARY}; font-size: {FONT_SIZE_TINY}px; font-weight: 600; letter-spacing: 1.4px;"
