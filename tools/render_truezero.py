"""
Render a True Zero window mockup as a clean PNG, matching the style of the
workbook hero image. Shows the new drop zone (reticle + MOA grid + center
spotlight + title + subtitle), workbook picker row, Run Import button, and
activity log with realistic import messages.

Output: /Users/macbook/Desktop/screenshot.png

Drawn at 2x then downsampled with LANCZOS for crisp anti-aliased lines.
"""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path("/Users/macbook/Desktop/screenshot.png")

# Final output dimensions (matches workbook.png hero size)
W = 1080
H = 720

# Render at 2x for anti-aliasing, then downsample
SCALE = 2
RW = W * SCALE
RH = H * SCALE

# True Zero palette (mirrors app/theme.py)
BG_BASE = (14, 15, 18)            # window background
BG_SURFACE = (26, 28, 32)         # drop zone surface
BG_ELEVATED = (36, 39, 44)        # log area / picker bg
BG_TITLEBAR = (22, 24, 28)        # window chrome
BORDER = (50, 54, 60)
BORDER_DARK = (70, 74, 80)
TEXT_PRIMARY = (237, 237, 237)
TEXT_SECONDARY = (184, 190, 201)
TEXT_MUTED = (130, 136, 145)
ACCENT = (217, 119, 6)
ACCENT_DIM = (160, 90, 6)
LOG_GARMIN = (160, 200, 255)
LOG_BX = (235, 195, 130)
LOG_SUCCESS = (140, 220, 160)
LOG_DEFAULT = TEXT_SECONDARY

TRAFFIC_RED = (236, 95, 89)
TRAFFIC_YELLOW = (244, 190, 76)
TRAFFIC_GREEN = (84, 191, 80)


def load_font(size, bold=False):
    return ImageFont.truetype(
        "/System/Library/Fonts/Helvetica.ttc", size * SCALE, index=1 if bold else 0
    )


F_TITLE = load_font(13, bold=False)        # window title (chrome)
F_DROP_TITLE = load_font(18, bold=True)
F_DROP_SUB = load_font(12)
F_BTN = load_font(13, bold=True)
F_LABEL = load_font(11)
F_LOG = load_font(11)
F_LOG_BOLD = load_font(11, bold=True)


def main():
    img = Image.new("RGB", (RW, RH), BG_BASE)
    d = ImageDraw.Draw(img, "RGBA")
    s = SCALE

    # ===== 1. Window chrome (title bar) =====
    chrome_h = 32 * s
    d.rectangle([(0, 0), (RW, chrome_h)], fill=BG_TITLEBAR)
    # Subtle line under chrome
    d.line([(0, chrome_h), (RW, chrome_h)], fill=(0, 0, 0), width=1 * s)

    # Traffic lights (top-left)
    light_r = 6 * s
    light_y = chrome_h // 2
    light_x = 18 * s
    spacing = 20 * s
    for color, x_off in [(TRAFFIC_RED, 0), (TRAFFIC_YELLOW, spacing), (TRAFFIC_GREEN, spacing * 2)]:
        cx = light_x + x_off
        d.ellipse(
            [(cx - light_r, light_y - light_r), (cx + light_r, light_y + light_r)],
            fill=color,
        )

    # Window title (centered)
    title = "True Zero"
    bbox = d.textbbox((0, 0), title, font=F_TITLE)
    tw = bbox[2] - bbox[0]
    d.text(((RW - tw) // 2, light_y - (bbox[3] - bbox[1]) // 2 - 2 * s),
           title, font=F_TITLE, fill=TEXT_SECONDARY)

    # ===== 2. Workbook picker row =====
    pad = 24 * s
    row_y = chrome_h + 18 * s
    row_h = 36 * s

    # "Workbook:" label
    d.text((pad, row_y + 10 * s), "Workbook:", font=F_LABEL, fill=TEXT_SECONDARY)
    label_bbox = d.textbbox((0, 0), "Workbook:", font=F_LABEL)
    label_w = label_bbox[2] - label_bbox[0]

    # Picker (combobox-style)
    picker_x = pad + label_w + 12 * s
    picker_w = 360 * s
    picker_y = row_y
    rounded_rect(d, (picker_x, picker_y), (picker_x + picker_w, picker_y + row_h),
                 radius=6 * s, fill=BG_ELEVATED, outline=BORDER, width=1 * s)
    d.text((picker_x + 12 * s, picker_y + 10 * s),
           "7 SAUM hunter load dev.xlsx", font=F_LABEL, fill=TEXT_PRIMARY)
    # dropdown arrow
    arr_x = picker_x + picker_w - 18 * s
    arr_y = picker_y + row_h // 2
    d.polygon(
        [(arr_x - 5 * s, arr_y - 3 * s),
         (arr_x + 5 * s, arr_y - 3 * s),
         (arr_x, arr_y + 4 * s)],
        fill=TEXT_SECONDARY,
    )

    # Refresh button
    btn_w = 90 * s
    btn_x = picker_x + picker_w + 8 * s
    rounded_rect(d, (btn_x, picker_y), (btn_x + btn_w, picker_y + row_h),
                 radius=6 * s, fill=BG_ELEVATED, outline=BORDER, width=1 * s)
    refresh_label = "Refresh"
    bbox = d.textbbox((0, 0), refresh_label, font=F_LABEL)
    refresh_w = bbox[2] - bbox[0]
    d.text((btn_x + (btn_w - refresh_w) // 2, picker_y + 10 * s),
           refresh_label, font=F_LABEL, fill=TEXT_PRIMARY)

    # ===== 3. Drop zone =====
    dz_x = pad
    dz_y = row_y + row_h + 22 * s
    dz_w = RW - 2 * pad
    dz_h = 360 * s

    draw_drop_zone(img, d, dz_x, dz_y, dz_w, dz_h)

    # ===== 4. Status row + Run Import button =====
    status_y = dz_y + dz_h + 18 * s
    status_h = 40 * s
    status_text = "3 files staged: 2 Garmin Xero, 1 BallisticX  -  click Run Import"
    d.text((pad, status_y + 12 * s), status_text, font=F_LABEL, fill=TEXT_SECONDARY)

    # Run Import button (orange) - right-aligned
    run_w = 160 * s
    run_h = status_h
    run_x = RW - pad - run_w
    rounded_rect(d, (run_x, status_y), (run_x + run_w, status_y + run_h),
                 radius=8 * s, fill=ACCENT)
    run_label = "Run Import"
    bbox = d.textbbox((0, 0), run_label, font=F_BTN)
    rl_w = bbox[2] - bbox[0]
    rl_h = bbox[3] - bbox[1]
    d.text((run_x + (run_w - rl_w) // 2, status_y + (run_h - rl_h) // 2 - 2 * s),
           run_label, font=F_BTN, fill=(255, 255, 255))

    # Clear button (right of label, left of Run Import)
    clr_w = 90 * s
    clr_x = run_x - clr_w - 8 * s
    rounded_rect(d, (clr_x, status_y), (clr_x + clr_w, status_y + run_h),
                 radius=8 * s, fill=BG_ELEVATED, outline=BORDER, width=1 * s)
    clr_label = "Clear"
    bbox = d.textbbox((0, 0), clr_label, font=F_BTN)
    cw = bbox[2] - bbox[0]
    ch = bbox[3] - bbox[1]
    d.text((clr_x + (clr_w - cw) // 2, status_y + (run_h - ch) // 2 - 2 * s),
           clr_label, font=F_BTN, fill=TEXT_PRIMARY)

    # ===== 5. Activity log =====
    log_y = status_y + status_h + 14 * s
    log_x = pad
    log_w = RW - 2 * pad
    log_h = RH - log_y - pad
    rounded_rect(d, (log_x, log_y), (log_x + log_w, log_y + log_h),
                 radius=8 * s, fill=BG_ELEVATED, outline=BORDER, width=1 * s)

    # Log lines — paint colored prefix + neutral message text
    log_lines = [
        ("[Garmin]",     LOG_GARMIN,   "P3 56.3 H1000 - 5 shots, avg 2869 fps, SD 2.9, ES 7"),
        ("[Garmin]",     LOG_GARMIN,   "P4 57.0 H1000 - 5 shots, avg 2898 fps, SD 5.9, ES 16"),
        ("[BallisticX]", LOG_BX,       "P3 56.3 H1000 - 100 yd, group 0.31\", MR 0.16\", vert 0.18\""),
        ("[BallisticX]", LOG_BX,       "P4 57.0 H1000 - 100 yd, group 0.41\", MR 0.20\", vert 0.25\""),
        ("[Import]",     LOG_SUCCESS,  "Wrote 6 chronograph rows, 6 group rows. Suggested winner: P3 (56.3 gr)."),
        ("[Import]",     LOG_SUCCESS,  "Workbook backed up to .backups/  -  opening in Excel."),
    ]

    line_y = log_y + 14 * s
    line_height = 20 * s
    for prefix, prefix_color, msg in log_lines:
        # Prefix in colored bold
        d.text((log_x + 16 * s, line_y), prefix, font=F_LOG_BOLD, fill=prefix_color)
        bbox = d.textbbox((0, 0), prefix, font=F_LOG_BOLD)
        prefix_w = bbox[2] - bbox[0]
        # Message in muted
        d.text((log_x + 16 * s + prefix_w + 8 * s, line_y), msg, font=F_LOG, fill=TEXT_SECONDARY)
        line_y += line_height

    # Downsample to final size with smooth resampling
    out = img.resize((W, H), Image.LANCZOS)
    out.save(OUT, "PNG", optimize=True)
    print(f"Saved: {OUT}  size={out.size}")


# ============================================================================
# Drop zone painter — reticle + grid + spotlight + title + subtitle
# ============================================================================
def draw_drop_zone(img, d, x, y, w, h):
    s = SCALE

    # 1. Drop zone background — surface color, dashed border, rounded corners
    rounded_rect(d, (x, y), (x + w, y + h), radius=12 * s, fill=BG_SURFACE)
    # Dashed border (simulated by drawing many short segments)
    draw_dashed_rect(d, (x, y), (x + w, y + h), radius=12 * s,
                     dash_len=8 * s, gap_len=6 * s,
                     fill=BORDER_DARK, width=2 * s)

    cx = x + w / 2
    cy = y + h / 2

    # 2. MOA grid (faint vertical + horizontal lines, anchored to center)
    grid_step = 24 * s
    margin = 6 * s
    grid_alpha = 28
    # vertical
    gx = cx
    while gx < x + w - margin:
        d.line([(int(gx), int(y + margin)), (int(gx), int(y + h - margin))],
               fill=(*ACCENT, grid_alpha), width=1 * s)
        gx += grid_step
    gx = cx - grid_step
    while gx > x + margin:
        d.line([(int(gx), int(y + margin)), (int(gx), int(y + h - margin))],
               fill=(*ACCENT, grid_alpha), width=1 * s)
        gx -= grid_step
    # horizontal
    gy = cy
    while gy < y + h - margin:
        d.line([(int(x + margin), int(gy)), (int(x + w - margin), int(gy))],
               fill=(*ACCENT, grid_alpha), width=1 * s)
        gy += grid_step
    gy = cy - grid_step
    while gy > y + margin:
        d.line([(int(x + margin), int(gy)), (int(x + w - margin), int(gy))],
               fill=(*ACCENT, grid_alpha), width=1 * s)
        gy -= grid_step

    # 3. Center spotlight (subtle radial highlight)
    spotlight_radius = max(w, h) * 0.45
    # Build a separate alpha layer for the gradient
    sp = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    sp_d = ImageDraw.Draw(sp)
    # Approximate radial gradient with concentric circles of decreasing alpha
    for i in range(20):
        t = i / 19
        a = int(20 * (1 - t))  # peak alpha 20, fades to 0
        r = int(spotlight_radius * t)
        sp_d.ellipse(
            [(int(w / 2 - r), int(h / 2 - r)),
             (int(w / 2 + r), int(h / 2 + r))],
            fill=(255, 255, 255, a),
        )
    img.paste(sp, (int(x), int(y)), sp)
    # Refresh draw object since paste invalidates
    d = ImageDraw.Draw(img, "RGBA")

    # 4. Reticle — concentric rings (soft) + crosshair (firmer) + mil-dots + hash marks
    rings = [28 * s, 56 * s, 88 * s]
    crosshair_h_half = 110 * s
    crosshair_v_half = 70 * s
    mil_dot_r = 1.6 * s
    mil_dot_dists = [16 * s, 32 * s, 48 * s, 64 * s, 80 * s]
    hash_dists = [48 * s, 80 * s]
    hash_len = 6 * s
    gap = 8 * s
    alpha_idle = 50
    ring_alpha = int(alpha_idle * 0.45)

    # Rings
    for r in rings:
        d.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
                  outline=(*ACCENT, ring_alpha), width=1 * s)

    # Crosshair (4 segments, with center gap)
    line_color = (*ACCENT, alpha_idle)
    d.line([(int(cx - crosshair_h_half), int(cy)), (int(cx - gap), int(cy))],
           fill=line_color, width=1 * s)
    d.line([(int(cx + gap), int(cy)), (int(cx + crosshair_h_half), int(cy))],
           fill=line_color, width=1 * s)
    d.line([(int(cx), int(cy - crosshair_v_half)), (int(cx), int(cy - gap))],
           fill=line_color, width=1 * s)
    d.line([(int(cx), int(cy + gap)), (int(cx), int(cy + crosshair_v_half))],
           fill=line_color, width=1 * s)

    # Mil-dots
    for dist in mil_dot_dists:
        if dist <= crosshair_h_half - 2 * s:
            d.ellipse([(cx - dist - mil_dot_r, cy - mil_dot_r),
                       (cx - dist + mil_dot_r, cy + mil_dot_r)],
                      fill=(*ACCENT, alpha_idle))
            d.ellipse([(cx + dist - mil_dot_r, cy - mil_dot_r),
                       (cx + dist + mil_dot_r, cy + mil_dot_r)],
                      fill=(*ACCENT, alpha_idle))
        if dist <= crosshair_v_half - 2 * s:
            d.ellipse([(cx - mil_dot_r, cy - dist - mil_dot_r),
                       (cx + mil_dot_r, cy - dist + mil_dot_r)],
                      fill=(*ACCENT, alpha_idle))
            d.ellipse([(cx - mil_dot_r, cy + dist - mil_dot_r),
                       (cx + mil_dot_r, cy + dist + mil_dot_r)],
                      fill=(*ACCENT, alpha_idle))

    # Hash marks
    for dist in hash_dists:
        if dist <= crosshair_h_half - 2 * s:
            d.line([(int(cx - dist), int(cy - hash_len)),
                    (int(cx - dist), int(cy + hash_len))], fill=line_color, width=1 * s)
            d.line([(int(cx + dist), int(cy - hash_len)),
                    (int(cx + dist), int(cy + hash_len))], fill=line_color, width=1 * s)
        if dist <= crosshair_v_half - 2 * s:
            d.line([(int(cx - hash_len), int(cy - dist)),
                    (int(cx + hash_len), int(cy - dist))], fill=line_color, width=1 * s)
            d.line([(int(cx - hash_len), int(cy + dist)),
                    (int(cx + hash_len), int(cy + dist))], fill=line_color, width=1 * s)

    # Center dot (full accent)
    cdot_r = 2.5 * s
    d.ellipse([(cx - cdot_r, cy - cdot_r), (cx + cdot_r, cy + cdot_r)],
              fill=(*ACCENT, 255))

    # 5. Title + subtitle — centered, on top of everything
    title = "Drop your Garmin & BallisticX CSVs here"
    subtitle = "Auto-detects format  -  drop multiple at once"
    bbox = d.textbbox((0, 0), title, font=F_DROP_TITLE)
    title_w = bbox[2] - bbox[0]
    title_h = bbox[3] - bbox[1]
    bbox = d.textbbox((0, 0), subtitle, font=F_DROP_SUB)
    sub_w = bbox[2] - bbox[0]
    sub_h = bbox[3] - bbox[1]

    text_block_h = title_h + 8 * s + sub_h
    text_top = cy - text_block_h // 2

    d.text((cx - title_w // 2, text_top), title, font=F_DROP_TITLE, fill=TEXT_PRIMARY)
    d.text((cx - sub_w // 2, text_top + title_h + 8 * s),
           subtitle, font=F_DROP_SUB, fill=TEXT_SECONDARY)


# ============================================================================
# Helpers
# ============================================================================
def rounded_rect(d, top_left, bottom_right, radius=8, fill=None, outline=None, width=1):
    d.rounded_rectangle([top_left, bottom_right],
                        radius=radius, fill=fill, outline=outline, width=width)


def draw_dashed_rect(d, top_left, bottom_right, radius, dash_len, gap_len, fill, width):
    """Approximate a dashed rounded border by drawing short segments around the perimeter."""
    x1, y1 = top_left
    x2, y2 = bottom_right
    # For simplicity, draw dashes on the four straight edges (skip corners — radius handles those visually)
    def dashed_h(y, x_start, x_end):
        x = x_start
        while x < x_end:
            seg_end = min(x + dash_len, x_end)
            d.line([(int(x), int(y)), (int(seg_end), int(y))], fill=fill, width=width)
            x = seg_end + gap_len

    def dashed_v(x, y_start, y_end):
        y = y_start
        while y < y_end:
            seg_end = min(y + dash_len, y_end)
            d.line([(int(x), int(y)), (int(x), int(seg_end))], fill=fill, width=width)
            y = seg_end + gap_len

    inset = radius
    dashed_h(y1, x1 + inset, x2 - inset)
    dashed_h(y2, x1 + inset, x2 - inset)
    dashed_v(x1, y1 + inset, y2 - inset)
    dashed_v(x2, y1 + inset, y2 - inset)
    # Corner arcs (just outline, doesn't need to be dashed)
    d.arc([(x1, y1), (x1 + 2 * radius, y1 + 2 * radius)], 180, 270, fill=fill, width=width)
    d.arc([(x2 - 2 * radius, y1), (x2, y1 + 2 * radius)], 270, 360, fill=fill, width=width)
    d.arc([(x1, y2 - 2 * radius), (x1 + 2 * radius, y2)], 90, 180, fill=fill, width=width)
    d.arc([(x2 - 2 * radius, y2 - 2 * radius), (x2, y2)], 0, 90, fill=fill, width=width)


if __name__ == "__main__":
    main()
