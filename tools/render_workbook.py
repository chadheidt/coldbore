"""
Render the Load Log section of the demo workbook as a clean PNG image,
without going through Excel's screen-capture pipeline. Uses Pillow.

Output: /Users/macbook/Desktop/workbook.png
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/Users/macbook/Desktop/workbook.png")

W = 1080
H = 720
PAD = 24

# Colors
BG = (255, 255, 255)
TEXT = (24, 27, 32)
TEXT_DIM = (110, 116, 124)
BORDER = (220, 224, 230)
BORDER_DARK = (180, 188, 196)
SECTION_BAR = (52, 62, 76)
SUGGESTED_BAR = (197, 32, 30)
SUGGESTED_BAR_TEXT = (255, 255, 255)
WINNER_ROW_BG = (244, 252, 246)
ACCENT = (217, 119, 6)  # hunter orange

# Fonts — macOS Helvetica
def load_font(size, bold=False):
    fname = "/System/Library/Fonts/Helvetica.ttc"
    return ImageFont.truetype(fname, size, index=1 if bold else 0)


F_TITLE = load_font(20, bold=True)
F_SUGG = load_font(16, bold=True)
F_SECT = load_font(11, bold=True)
F_LABEL = load_font(11, bold=True)
F_VAL = load_font(11)
F_HEAD = load_font(11, bold=True)
F_DATA = load_font(11)
F_TAG = load_font(11, bold=True)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    y = PAD

    # ---------- 1. TITLE BAR ----------
    d.text((PAD, y), "Rifle Load Development Log", font=F_TITLE, fill=TEXT)
    # subtle horizontal rule
    y += 32
    d.line([(PAD, y), (W - PAD, y)], fill=BORDER_DARK, width=1)
    y += 12

    # ---------- 2. SUGGESTED CHARGE BAR (red) ----------
    bar_h = 42
    d.rectangle([(PAD, y), (W - PAD, y + bar_h)], fill=SUGGESTED_BAR)
    bar_text_y = y + bar_h // 2 - 8
    d.text((PAD + 14, bar_text_y),
           "SUGGESTED CHARGE:  56.3 gr H1000",
           font=F_SUGG, fill=SUGGESTED_BAR_TEXT)
    metrics = "Avg Vel: 2869 fps     SD: 2.9     MR: 0.153 MOA     Best in: SD, MR, Vert"
    # right-align the metrics
    bbox = d.textbbox((0, 0), metrics, font=F_SUGG)
    metrics_w = bbox[2] - bbox[0]
    d.text((W - PAD - 14 - metrics_w, bar_text_y), metrics,
           font=F_SUGG, fill=SUGGESTED_BAR_TEXT)
    y += bar_h + 14

    # ---------- 3. RIFLE & SHOOTER ----------
    y = draw_section_header(d, y, "RIFLE & SHOOTER")
    y = draw_kv_row(d, y, [
        ("Rifle:",    "7 SAUM"),
        ("Shooter:",  "Chad"),
        ("Cartridge:", "7mm SAUM"),
    ])
    y = draw_kv_row(d, y, [
        ("Barrel:",   'Proof Sendero, 26"'),
        ("Optic:",    "Nightforce ATACR 7-35"),
        ("Chrono:",   "Garmin Xero C1"),
    ])
    y += 8

    # ---------- 4. LOAD COMPONENTS ----------
    y = draw_section_header(d, y, "LOAD COMPONENTS  (constants for this powder ladder)")
    y = draw_kv_row(d, y, [
        ("Bullet:",   "195 gr Berger Hybrid"),
        ("Powder:",   "H1000"),
        ("Primer:",   "CCI 200"),
        ("Brass:",    "Peterson"),
    ], cols=4)
    y = draw_kv_row(d, y, [
        ("CBTO:",     "2.870\""),
        ("Off Lands:", "0.020\""),
        ("Dist (yd):", "100"),
    ])
    y += 8

    # ---------- 5. TEST SESSION ----------
    y = draw_section_header(d, y, "TEST SESSION  (date / conditions)")
    y = draw_kv_row(d, y, [
        ("Date:",     "5/8/2026"),
        ("Temp (°F):", "65"),
        ("Notes:",    "Calm, light overcast"),
    ])
    y += 16

    # ---------- 6. DATA TABLE ----------
    cols = [
        ("Load",      55),
        ("Charge",    65),
        ("Shot 1",    62),
        ("Shot 2",    62),
        ("Shot 3",    62),
        ("Shot 4",    62),
        ("Shot 5",    62),
        ("Avg",       65),
        ("SD",        46),
        ("ES",        46),
        ("Group",     62),
        ("Vert",      55),
        ("MR",        55),
        ("Composite", 80),
    ]
    table_w = sum(w for _, w in cols)
    table_x = PAD + (W - 2 * PAD - table_w) // 2  # center the table

    # header row
    head_h = 26
    d.rectangle([(table_x, y), (table_x + table_w, y + head_h)],
                fill=(248, 250, 252), outline=BORDER_DARK)
    cx = table_x
    for label, w in cols:
        text_y = y + head_h // 2 - 7
        bbox = d.textbbox((0, 0), label, font=F_HEAD)
        tw = bbox[2] - bbox[0]
        d.text((cx + (w - tw) // 2, text_y), label, font=F_HEAD, fill=TEXT)
        cx += w
    y += head_h

    # 6 data rows: P1-P6
    rows = [
        # Tag, Charge, Shot 1-5, Avg, SD, ES, Group, Vert, MR, Composite
        ("P1", "55.0", "2798", "2812", "2806", "2785", "2820", "2804.2", "13.4", "35", "0.62\"", "0.41\"", "0.31\"", "—"),
        ("P2", "55.7", "2832", "2841", "2828", "2845", "2836", "2836.4", "6.8",  "17", "0.48\"", "0.32\"", "0.24\"", "0.581"),
        ("P3", "56.3", "2867", "2871", "2865", "2872", "2870", "2869.0", "2.9",  "7",  "0.31\"", "0.18\"", "0.16\"", "0.283"),  # WINNER
        ("P4", "57.0", "2895", "2899", "2890", "2906", "2898", "2897.6", "5.9",  "16", "0.41\"", "0.25\"", "0.20\"", "0.442"),
        ("P5", "57.7", "2923", "2935", "2918", "2940", "2926", "2928.4", "9.0",  "22", "0.55\"", "0.38\"", "0.27\"", "0.694"),
        ("P6", "58.3", "2952", "2967", "2945", "2972", "2958", "2958.8", "10.9", "27", "0.78\"", "0.55\"", "0.39\"", "—"),
    ]
    row_h = 30
    for i, row in enumerate(rows):
        is_winner = row[0] == "P3"
        bg = WINNER_ROW_BG if is_winner else BG
        d.rectangle([(table_x, y), (table_x + table_w, y + row_h)],
                    fill=bg, outline=BORDER)
        cx = table_x
        for j, val in enumerate(row):
            label, w = cols[j]
            font = F_TAG if j == 0 else F_DATA
            color = TEXT
            text_y = y + row_h // 2 - 7
            bbox = d.textbbox((0, 0), val, font=font)
            tw = bbox[2] - bbox[0]
            d.text((cx + (w - tw) // 2, text_y), val, font=font, fill=color)
            cx += w
        # winner indicator
        if is_winner:
            d.text((table_x + table_w + 8, y + row_h // 2 - 8),
                   "WINNER", font=F_HEAD, fill=ACCENT)
        y += row_h

    # subtle outer border around the data table
    d.rectangle([(table_x, y - row_h * len(rows) - head_h),
                 (table_x + table_w, y)],
                outline=BORDER_DARK, width=1)

    img.save(OUT, "PNG", optimize=True)
    print(f"Saved: {OUT}  size={img.size}")


def draw_section_header(d, y, label):
    bar_h = 22
    # green-ish bar at left, blending into faint background
    d.rectangle([(PAD, y), (PAD + 6, y + bar_h)], fill=ACCENT)
    d.rectangle([(PAD + 6, y), (W - PAD, y + bar_h)], fill=(248, 246, 240))
    d.text((PAD + 14, y + 5), label, font=F_SECT, fill=SECTION_BAR)
    return y + bar_h + 6


def draw_kv_row(d, y, items, cols=3):
    row_h = 22
    inner_w = W - 2 * PAD
    col_w = inner_w // cols
    for i, (label, value) in enumerate(items):
        cx = PAD + (i % cols) * col_w
        # Label in bold
        d.text((cx + 8, y + 4), label, font=F_LABEL, fill=TEXT_DIM)
        # Compute label width to position the value next to it
        bbox = d.textbbox((0, 0), label, font=F_LABEL)
        lw = bbox[2] - bbox[0]
        d.text((cx + 8 + lw + 6, y + 4), value, font=F_VAL, fill=TEXT)
    return y + row_h


if __name__ == "__main__":
    main()
