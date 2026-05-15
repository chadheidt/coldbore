#!/usr/bin/env python3
"""Build-time tool — render each demo-tour stop to a high-res PNG.

Path B (pre-rendered demo): the shipped app shows these PNGs in a single
controlled window. Excel is NEVER launched on a customer's machine for
the demo — no popups, no window juggling, no macOS permission prompts.
Run by the developer on a Mac with Microsoft Excel installed; the cost
of needing Excel is paid here once, for pixel-perfect fidelity.

    python3 tools/render_demo_screenshots.py

Writes app/resources/demo_screenshots/:
    01-load-log.png 02-charts.png 03-seating-depth.png
    04-ballistics.png 05-pocket-card.png 06-load-library.png

Pipeline (all built-in macOS tooling, no shipped deps):
  * Excel "save … as PDF" emits the WHOLE workbook as one multi-page
    PDF (one page per visible sheet — verified). We export ONCE, then
    render the page for each demo sheet with Quartz (CoreGraphics).
    The page index per sheet comes from openpyxl's visible-sheet order
    (reliable — Excel's `repeat … visible of sheet` AppleScript throws
    an intermittent -50).
  * Pocket card -> pocket_card HTML -> qlmanage (built-in WebKit) PNG.
  * All outputs autocropped to content with Pillow (dev-only; the
    shipped app never imports PIL).
"""
import glob
import os
import shutil
import subprocess
import sys
import time

import Quartz
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEMO_WB = os.path.join(ROOT, "app", "resources", "Loadscope - Demo Workbook.xlsx")
OUT_DIR = os.path.join(ROOT, "app", "resources", "demo_screenshots")
TMP = "/tmp/loadscope_demo_render"

# (output filename, kind, target). Mirrors TOUR_STOPS in app/demo_tour.py.
STOPS = [
    ("01-load-log.png",      "sheet", "Load Log"),
    ("02-charts.png",        "sheet", "Charts"),
    ("03-seating-depth.png", "sheet", "Seating Depth"),
    ("04-ballistics.png",    "sheet", "Ballistics"),
    ("05-pocket-card.png",   "card",  None),
    ("06-load-library.png",  "sheet", "Load Library"),
]


def _osa(script, timeout=40):
    return subprocess.run(["osascript", "-e", script],
                          capture_output=True, text=True, timeout=timeout)


def _visible_sheet_pages():
    """{sheet_name: 1-based PDF page} from openpyxl's visible-sheet order.
    Each visible sheet is fit-to-one-page, so it's 1 page each."""
    wb = load_workbook(DEMO_WB)
    vis = [n for n in wb.sheetnames if wb[n].sheet_state == "visible"]
    return {name: i + 1 for i, name in enumerate(vis)}, len(vis)


def _prepped_workbook():
    """Copy the demo workbook and strip print headers/footers from every
    sheet. Load Log / Charts / Seating Depth carry a footer ("Rifle Load
    Development Log / Page N") that pins the rendered content's bounding
    box to the page bottom — so autocrop keeps a big white band and the
    image displays small. Ballistics / Load Library have NO footer, which
    is exactly why they already look right. Removing header+footer makes
    every demo image crop tight and display large + consistent."""
    from openpyxl import load_workbook
    wb = load_workbook(DEMO_WB)
    for name in wb.sheetnames:
        ws = wb[name]
        for hf in (ws.oddHeader, ws.oddFooter, ws.evenHeader,
                   ws.evenFooter, ws.firstHeader, ws.firstFooter):
            hf.left.text = hf.center.text = hf.right.text = None
        ws.HeaderFooter.differentFirst = False
        ws.HeaderFooter.differentOddEven = False
    out = os.path.join(TMP, "_demo_noheader.xlsx")
    wb.save(out)
    return out


def _export_workbook_pdf(pdf_path):
    src = _prepped_workbook()
    _osa('tell application "Microsoft Excel" to try\n'
         'close every workbook saving no\nend try')
    r = _osa(f'tell application "Microsoft Excel" to open POSIX file "{src}"')
    if r.returncode != 0:
        raise SystemExit(f"Could not open prepped workbook in Excel:\n{r.stderr}")
    time.sleep(2.5)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    # Excel emits the WHOLE workbook here (one page per visible sheet) —
    # verified. We rely on that and split by page below.
    r = _osa(f'tell application "Microsoft Excel" to save active sheet '
             f'in POSIX file "{pdf_path}" as PDF file format')
    _osa('tell application "Microsoft Excel" to try\n'
         'close every workbook saving no\nend try')
    if not os.path.isfile(pdf_path):
        raise RuntimeError(f"Workbook PDF export failed: {r.stderr}")


def _pdf_page_to_png(pdf_path, page_num, png_path, scale=3.0):
    url = Quartz.CFURLCreateWithFileSystemPathRelativeToBase(
        None, pdf_path, Quartz.kCFURLPOSIXPathStyle, False, None)
    doc = Quartz.CGPDFDocumentCreateWithURL(url)
    if not doc:
        raise RuntimeError(f"Cannot open PDF {pdf_path}")
    npages = Quartz.CGPDFDocumentGetNumberOfPages(doc)
    page = Quartz.CGPDFDocumentGetPage(doc, page_num)
    if not page:
        raise RuntimeError(f"No page {page_num} (PDF has {npages})")
    rect = Quartz.CGPDFPageGetBoxRect(page, Quartz.kCGPDFCropBox)
    w = int(rect.size.width * scale)
    h = int(rect.size.height * scale)
    cs = Quartz.CGColorSpaceCreateDeviceRGB()
    ctx = Quartz.CGBitmapContextCreate(
        None, w, h, 8, 0, cs, Quartz.kCGImageAlphaPremultipliedLast)
    Quartz.CGContextSetRGBFillColor(ctx, 1, 1, 1, 1)
    Quartz.CGContextFillRect(ctx, Quartz.CGRectMake(0, 0, w, h))
    Quartz.CGContextScaleCTM(ctx, scale, scale)
    Quartz.CGContextDrawPDFPage(ctx, page)
    img = Quartz.CGBitmapContextCreateImage(ctx)
    durl = Quartz.CFURLCreateWithFileSystemPathRelativeToBase(
        None, png_path, Quartz.kCFURLPOSIXPathStyle, False, None)
    dest = Quartz.CGImageDestinationCreateWithURL(durl, "public.png", 1, None)
    Quartz.CGImageDestinationAddImage(dest, img, None)
    if not Quartz.CGImageDestinationFinalize(dest):
        raise RuntimeError(f"PNG write failed: {png_path}")


def _render_card_png(png_path):
    sys.path.insert(0, os.path.join(ROOT, "app"))
    import pocket_card
    html = pocket_card.generate_pocket_card(DEMO_WB, open_after=False)
    # Dedicated subdir — must NOT wipe TMP, which holds _workbook.pdf
    # that later sheet stops still need.
    card_tmp = os.path.join(TMP, "_card")
    if os.path.isdir(card_tmp):
        shutil.rmtree(card_tmp)
    os.makedirs(card_tmp)
    subprocess.run(["qlmanage", "-t", "-s", "2000", html, "-o", card_tmp],
                   check=True, capture_output=True, text=True)
    produced = glob.glob(os.path.join(card_tmp, "*.png"))
    if not produced:
        raise RuntimeError("qlmanage produced no PNG for the pocket card")
    shutil.move(produced[0], png_path)


def _autocrop(png_path):
    """Trim surrounding whitespace so each demo image is tight (the PDF
    page is letter-size with content at the top). Pillow is dev-only."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("  (PIL unavailable — skipping autocrop)")
        return
    im = Image.open(png_path).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        pad = 16
        l, t, r, b = bbox
        im.crop((max(0, l - pad), max(0, t - pad),
                 min(im.width, r + pad), min(im.height, b + pad))).save(png_path)


def main():
    if not os.path.isfile(DEMO_WB):
        raise SystemExit(f"Demo workbook missing: {DEMO_WB}")
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    pages, nvis = _visible_sheet_pages()
    print(f"Visible sheets ({nvis}): " +
          ", ".join(f"{n}=p{p}" for n, p in pages.items()))
    wb_pdf = os.path.join(TMP, "_workbook.pdf")
    print("Exporting whole workbook to PDF via Excel…")
    _export_workbook_pdf(wb_pdf)
    for fname, kind, target in STOPS:
        out = os.path.join(OUT_DIR, fname)
        if kind == "sheet":
            if target not in pages:
                raise SystemExit(f"Sheet {target!r} not visible in workbook")
            print(f"-> {fname}  (sheet {target}, page {pages[target]})")
            _pdf_page_to_png(wb_pdf, pages[target], out)
        else:
            print(f"-> {fname}  (pretty pocket card)")
            _render_card_png(out)
        _autocrop(out)
        print(f"   {out}  ({os.path.getsize(out)//1024} KB)")
    print(f"\nDone. {len(STOPS)} images in {OUT_DIR}")


if __name__ == "__main__":
    main()
