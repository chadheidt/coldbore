"""Pocket Range Card (DOPE card) generator.

Reads the user's Ballistics tab (rifle/cartridge/scope info + the 100-1000yd
elev/wind table they've filled in) and writes a single 4x6 landscape HTML
page sized for printing as a pocket-card range reference.

User opens the HTML in their browser and chooses File → Print → Save as PDF,
or prints directly to 4x6 index card stock if they have it. Standard
letter-paper printing also works (the card just appears centered with
whitespace around it).

Workbook → Print Pocket Range Card… in the app launches this.
"""

import base64
import os
import subprocess
from datetime import datetime

from openpyxl import load_workbook


def _logo_data_uri():
    """Read the Loadscope icon and return a base64 data URI so the
    generated HTML stays a single self-contained file (works offline,
    portable to email, doesn't break if the user moves it)."""
    # Look up the icon in the package's resources. Two location candidates
    # depending on whether we're in dev or in the .app bundle:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(here, "..", "docs", "assets", "icon.png")),
        os.path.normpath(os.path.join(here, "resources", "icon.png")),
        # py2app Resources dir
        os.path.normpath(os.path.join(here, "..", "Resources", "icon.png")),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
    # Icon missing — return empty so the card still renders, just no logo
    return ""


# Header info on the Ballistics tab. Cell coordinates are the value cells
# (not the labels). Some are merged ranges — using the top-left anchor.
HEADER_FIELDS = {
    "rifle":    ("Ballistics", "B5"),
    "bullet":   ("Ballistics", "E5"),
    "charge":   ("Ballistics", "H5"),
    "vel":      ("Ballistics", "K5"),
    "scope":    ("Ballistics", "B6"),
    "zero":     ("Ballistics", "E6"),
    "sight_ht": ("Ballistics", "H6"),
    "twist":    ("Ballistics", "K6"),
    # Scope click value lives on Load Log (single source of truth — the
    # Ballistics click-column formulas all reference it). Showing it on
    # the printed card tells the shooter which scope click value the
    # click counts assume.
    "click":    ("Load Log", "G7"),
}

# DOPE table rows on the Ballistics tab. Data lives in rows 9..18
# (100yd through 1000yd in 100yd increments). Columns:
#   A=Range, B=Mils Elev, C=Mil Clicks, D=MOA Elev, E=MOA Clicks,
#   F=Wind Mils/10mph, G=Wind Mil Clk, H=Wind MOA/10mph, I=Wind MOA Clk,
#   J=TOF (sec)
DOPE_ROWS = range(9, 19)
DOPE_COL_KEYS = ["range", "mils_elev", "mils_clk", "moa_elev", "moa_clk",
                 "wind_mils", "wind_mils_clk", "wind_moa", "wind_moa_clk",
                 "tof"]
DOPE_COL_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


def _cell(wb, sheet, coord):
    if sheet not in wb.sheetnames:
        return None
    return wb[sheet][coord].value


def _fmt(v, blank="—"):
    """Format a cell value for display in the card. Returns blank glyph
    for None / empty / NaN."""
    if v is None:
        return blank
    if isinstance(v, str):
        return v.strip() or blank
    if isinstance(v, float):
        if v != v:  # NaN
            return blank
        if v == int(v):
            return str(int(v))
        # 2 decimal places, trimming trailing zeros
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def _gather(workbook_path):
    """Read all card data from the workbook. Uses data_only=True so the
    LOOKUP formulas on the Ballistics tab evaluate to their cached values."""
    wb = load_workbook(workbook_path, data_only=True, keep_vba=False)
    if "Ballistics" not in wb.sheetnames:
        raise ValueError("This workbook doesn't have a Ballistics tab.")

    data = {"header": {}, "dope": []}
    for key, (sheet, coord) in HEADER_FIELDS.items():
        data["header"][key] = _cell(wb, sheet, coord)

    bal = wb["Ballistics"]
    rows_filled = 0
    for r in DOPE_ROWS:
        row = {"row_num": r}
        for letter, key in zip(DOPE_COL_LETTERS, DOPE_COL_KEYS):
            row[key] = bal[f"{letter}{r}"].value
        # A row is considered "filled" if there's any elev or wind data
        if any(row.get(k) not in (None, "") for k in
               ("mils_elev", "moa_elev", "wind_mils", "wind_moa")):
            rows_filled += 1
        data["dope"].append(row)

    if rows_filled == 0:
        raise ValueError(
            "Ballistics tab has no DOPE data yet. Fill in the elevation and "
            "wind values for at least one range (rows 9–18) before generating "
            "a Pocket Range Card."
        )

    data["workbook_name"] = os.path.splitext(os.path.basename(workbook_path))[0]
    data["generated_at"] = datetime.now().strftime("%b %d, %Y")
    return data


def _build_html(d):
    """Render the pocket card as a single-page HTML document, sized for
    4x6 landscape print (6 inches wide × 4 inches tall)."""
    h = d["header"]
    title_line = f"{_fmt(h.get('rifle'))} • {_fmt(h.get('bullet'))} • {_fmt(h.get('charge'), '—')}gr • {_fmt(h.get('vel'), '—')} fps"
    logo_uri = _logo_data_uri()
    logo_img = (
        f'<img src="{logo_uri}" alt="Loadscope" class="logo"/>'
        if logo_uri else ''
    )

    # DOPE table rows
    dope_rows_html = []
    for row in d["dope"]:
        # Skip rows where range is empty (shouldn't happen — A9..A18 are 100..1000)
        if row.get("range") in (None, ""):
            continue
        dope_rows_html.append(
            "<tr>"
            f"<td class='r'>{_fmt(row.get('range'))}</td>"
            f"<td>{_fmt(row.get('mils_elev'))}</td>"
            f"<td class='clk'>{_fmt(row.get('mils_clk'))}</td>"
            f"<td>{_fmt(row.get('moa_elev'))}</td>"
            f"<td class='clk'>{_fmt(row.get('moa_clk'))}</td>"
            f"<td>{_fmt(row.get('wind_mils'))}</td>"
            f"<td class='clk'>{_fmt(row.get('wind_mils_clk'))}</td>"
            f"<td>{_fmt(row.get('wind_moa'))}</td>"
            f"<td class='clk'>{_fmt(row.get('wind_moa_clk'))}</td>"
            f"<td class='tof'>{_fmt(row.get('tof'))}</td>"
            "</tr>"
        )
    dope_rows_str = "\n".join(dope_rows_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pocket Range Card — {_fmt(h.get('rifle'))}</title>
<style>
  @page {{
    size: 6in 4in;
    margin: 0.15in;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
    color: #000;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .card {{
    width: 5.7in;
    height: 3.7in;
    padding: 0.1in;
    border: 1.5pt solid #000;
  }}
  .title-bar {{
    background: #d97706;
    color: #fff;
    padding: 7pt 10pt;
    margin: -0.1in -0.1in 0.07in -0.1in;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1pt solid #b45309;
  }}
  .title-bar .brand {{
    display: flex;
    align-items: center;
    gap: 6pt;
    font-weight: 700;
    font-size: 12pt;
    letter-spacing: 0.3pt;
  }}
  .title-bar .brand .logo {{
    width: 22pt;
    height: 22pt;
    display: block;
  }}
  .title-bar .brand .tm {{
    font-size: 7pt;
    font-weight: 600;
    vertical-align: super;
    margin-left: 1pt;
  }}
  .title-bar .subtitle {{
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.5pt;
    text-transform: uppercase;
  }}
  .title-line {{
    font-size: 9pt;
    font-weight: 600;
    margin: 3pt 0 2pt;
    text-align: center;
  }}
  .setup {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 2pt 8pt;
    font-size: 7pt;
    margin-bottom: 4pt;
    padding-bottom: 3pt;
    border-bottom: 0.5pt solid #aaa;
  }}
  .setup .field {{ display: flex; gap: 3pt; }}
  .setup .label {{ color: #555; font-weight: 600; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 7.5pt;
    font-variant-numeric: tabular-nums;
  }}
  th {{
    background: #f0eee9;
    font-weight: 700;
    font-size: 6.5pt;
    padding: 2pt 1pt;
    text-align: center;
    border-bottom: 0.8pt solid #555;
    line-height: 1.05;
  }}
  th.spanner {{
    background: #1f2229;
    color: #fff;
    border-bottom: 0;
    border-right: 0.5pt solid #555;
    padding: 1pt;
  }}
  th.spanner:last-child {{ border-right: 0; }}
  td {{
    padding: 1.4pt 1pt;
    text-align: center;
    border-bottom: 0.3pt solid #ddd;
  }}
  td.r {{
    font-weight: 700;
    background: #faf8f4;
  }}
  td.clk {{
    color: #777;
    font-size: 6.5pt;
    font-style: italic;
  }}
  td.tof {{
    color: #555;
    font-size: 6.5pt;
  }}
  .footer {{
    margin-top: 3pt;
    font-size: 6pt;
    color: #888;
    text-align: center;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="title-bar">
    <div class="brand">
      {logo_img}
      <span>Loadscope<span class="tm">™</span></span>
    </div>
    <div class="subtitle">Pocket Range Card</div>
  </div>
  <div class="title-line">{title_line}</div>
  <div class="setup">
    <div class="field"><span class="label">Scope:</span><span>{_fmt(h.get('scope'))}</span></div>
    <div class="field"><span class="label">Click:</span><span>{_fmt(h.get('click'))}</span></div>
    <div class="field"><span class="label">Zero:</span><span>{_fmt(h.get('zero'))} yd</span></div>
    <div class="field"><span class="label">Sight Ht:</span><span>{_fmt(h.get('sight_ht'))} in</span></div>
    <div class="field"><span class="label">Twist:</span><span>{_fmt(h.get('twist'))}</span></div>
  </div>
  <table>
    <thead>
      <tr>
        <th rowspan="2">Range<br>(yd)</th>
        <th class="spanner" colspan="2">Elev — Mils</th>
        <th class="spanner" colspan="2">Elev — MOA</th>
        <th class="spanner" colspan="2">Wind 10 mph (Mils)</th>
        <th class="spanner" colspan="2">Wind 10 mph (MOA)</th>
        <th rowspan="2">TOF<br>(s)</th>
      </tr>
      <tr>
        <th>Mils</th><th>clk</th>
        <th>MOA</th><th>clk</th>
        <th>Mils</th><th>clk</th>
        <th>MOA</th><th>clk</th>
      </tr>
    </thead>
    <tbody>
      {dope_rows_str}
    </tbody>
  </table>
  <div class="footer">Generated {d['generated_at']}</div>
</div>
</body>
</html>"""


def generate_pocket_card(workbook_path, open_after=True):
    """Generate a Pocket Range Card HTML from the workbook's Ballistics tab.
    Returns the path to the generated file. If `open_after`, opens it in
    the user's default browser so they can print it (Cmd+P → 4x6 paper
    or letter, save as PDF, etc.)."""
    data = _gather(workbook_path)
    html = _build_html(data)

    project_dir = os.path.dirname(os.path.abspath(workbook_path))
    out_dir = os.path.join(project_dir, "Range Cards")
    os.makedirs(out_dir, exist_ok=True)

    workbook_base = os.path.splitext(os.path.basename(workbook_path))[0]
    stamp = datetime.now().strftime("%Y-%m-%d %H-%M")
    out_path = os.path.join(out_dir, f"{workbook_base} — Pocket Card {stamp}.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    if open_after:
        subprocess.run(["open", out_path])

    return out_path
