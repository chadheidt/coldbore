"""Render the Gate-4 PREDICTED Pocket Range Card to a demo screenshot.

The bundled demo workbook ships with confirmed DOPE, so the old
05-pocket-card.png showed a plain card with no PREDICTED banner — it
never demonstrated the gate-4 watermark (`pocket_card.py` only draws the
"PREDICTED DOPE (italic rows) - verify at the range" banner when there
are unconfirmed/predicted rows).

This tool copies the demo workbook, CLEARS the DOPE table (same pre-
range state render_dope_preview.py uses), so the solver predicts every
row → the Pocket Card renders WITH the PREDICTED banner + italic rows.
That is exactly the "your card before you leave the truck" pitch the
demo's Pocket Card stop now narrates.

Dev/dev-Mac only (needs qlmanage WebKit + openpyxl + Pillow); not
bundled, not run in the app. Output overwrites
app/resources/demo_screenshots/05-pocket-card.png so the existing demo
tour stop picks it up with no TOUR_STOPS change.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "app")
sys.path.insert(0, APP)

from openpyxl import load_workbook  # noqa: E402

import pocket_card  # noqa: E402

DEMO = os.path.join(APP, "resources", "Loadscope - Demo Workbook.xlsx")
OUT = os.path.join(APP, "resources", "demo_screenshots", "05-pocket-card.png")


def _pre_range_workbook(dst):
    """Demo copy with the DOPE table cleared = every row predicted."""
    shutil.copy(DEMO, dst)
    wb = load_workbook(dst)
    bal = wb["Ballistics"]
    for r in range(9, 19):
        for col in ("B", "D", "F", "H"):
            bal[f"{col}{r}"] = None
    wb.save(dst)
    return dst


def _autocrop(png_path):
    from PIL import Image, ImageChops
    im = Image.open(png_path).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg)
    box = diff.getbbox()
    if box:
        pad = 12
        l, t, r, b = box
        im = im.crop((max(0, l - pad), max(0, t - pad),
                      min(im.size[0], r + pad), min(im.size[1], b + pad)))
        im.save(png_path)


def main():
    tmpdir = tempfile.mkdtemp(prefix="ls_predcard_")
    try:
        wb = _pre_range_workbook(os.path.join(tmpdir, "demo.xlsx"))
        html = pocket_card.generate_pocket_card(wb, open_after=False)
        cardout = os.path.join(tmpdir, "card")
        os.makedirs(cardout)
        subprocess.run(["qlmanage", "-t", "-s", "2000", html, "-o", cardout],
                       check=True, capture_output=True, text=True)
        produced = glob.glob(os.path.join(cardout, "*.png"))
        if not produced:
            raise RuntimeError("qlmanage produced no PNG for the pocket card")
        shutil.move(produced[0], OUT)
        _autocrop(OUT)
        print("wrote", OUT, "(%d bytes)" % os.path.getsize(OUT))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
