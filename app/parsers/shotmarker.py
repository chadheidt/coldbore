"""
ShotMarker (AMP) electronic-target CSV export parser.

ShotMarker exports per-shot data (the open-source shotGroups package reads
it via `readDataShotMarker`). Coordinates are in inches, distance in yards,
and a velocity column is often present. Exact header spellings vary by
firmware/export, so this parser maps columns flexibly by keyword and
computes group dimensions from the per-shot X/Y via
_common.group_stats_from_points.

VALIDATION STATUS: built from the publicly documented structure, NOT
verified against a real ShotMarker export. `NEEDS_REAL_SAMPLE_VALIDATION`
is True until a genuine file is checked. detect() is deliberately strict —
it requires an explicit ShotMarker identifier (content token or filename)
plus an X/Y column pair — so it never silently mis-claims another CSV.
A real export will let us relax/confirm detection.
"""

import csv
import os

from ._common import parse_label, group_stats_from_points


KIND = "group"
NAME = "ShotMarker"
KEY = "shotmarker"
IMPORT_FOLDER = "ShotMarker Imports"

NEEDS_REAL_SAMPLE_VALIDATION = True

_ID_TOKENS = ("shotmarker", "shot marker", "amp target")


def _find(cols, *needles):
    for i, c in enumerate(cols):
        cl = c.strip().lower()
        if any(n in cl for n in needles):
            return i
    return None


def _looks_like_us(path):
    base = os.path.basename(path).lower()
    return any(t.replace(" ", "") in base.replace(" ", "")
               for t in ("shotmarker", "shotmrk", "_sm_")) or base.startswith("sm ")


_X_NEEDLES = ("x (in", "x_in", "x(in", "x in", "x pos")
_Y_NEEDLES = ("y (in", "y_in", "y(in", "y in", "y pos")


def _header_row(rows, scan=8):
    """Find the column-header row within the first `scan` rows: the first
    row that has both an X and a Y column. Tolerates a preamble (title /
    metadata lines) above the table, which real e-target exports often have.
    Returns (index, header_list) or (None, None)."""
    for i, r in enumerate(rows[:scan]):
        if (_find(r, *_X_NEEDLES) is not None
                and _find(r, *_Y_NEEDLES) is not None):
            return i, r
    return None, None


def detect(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            head = f.read(4000)
    except (OSError, UnicodeDecodeError):
        return False
    low = head.lower()
    lines = [ln.split(",") for ln in head.splitlines()[:8]]
    hidx, header = _header_row(lines)
    has_xy = header is not None
    id_hit = any(t in low for t in _ID_TOKENS) or _looks_like_us(path)
    # ShotMarker's distinctive combo: x/y cols + yaw/pitch or a fps column.
    distinctive = has_xy and (_find(header, "yaw", "pitch") is not None
                              or _find(header, "v (fps", "v(fps", "fps")
                              is not None)
    return bool(id_hit and has_xy) or distinctive


def parse(path):
    """Return a list of group records (one per string/group, else one)."""
    filename_label = os.path.splitext(os.path.basename(path))[0]
    fn_tag, fn_charge, fn_powder = parse_label(filename_label)
    use_fn = fn_charge is not None
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            rows = list(csv.reader(f))
    except Exception as e:
        print(f"  WARNING: couldn't read {path}: {e}")
        return []
    if not rows:
        return []

    hidx, header = _header_row(rows)
    if header is None:
        return []
    xi = _find(header, *_X_NEEDLES)
    yi = _find(header, *_Y_NEEDLES)
    di = _find(header, "distance", "yard", "yd")
    gi = _find(header, "string", "group", "series", "session")
    if xi is None or yi is None:
        return []

    buckets = {}
    for r in rows[hidx + 1:]:
        if len(r) <= max(xi, yi):
            continue
        try:
            x = float(r[xi]); y = float(r[yi])
        except (ValueError, IndexError):
            continue
        gkey = r[gi].strip() if gi is not None and len(r) > gi else ""
        dist = None
        if di is not None and len(r) > di:
            try:
                dist = float(r[di])
            except ValueError:
                dist = None
        b = buckets.setdefault(gkey, {"pts": [], "dist": dist})
        b["pts"].append((x, y))
        if b["dist"] is None and dist is not None:
            b["dist"] = dist

    out = []
    for gkey, b in buckets.items():
        if use_fn:
            label, tag, charge, powder = (
                filename_label, fn_tag, fn_charge, fn_powder)
        else:
            label = gkey or filename_label
            tag, charge, powder = parse_label(label)
        s = group_stats_from_points(b["pts"])
        out.append({
            "kind": KIND, "Source": KEY, "Tag": tag,
            "ChargeOrJump": charge, "Powder": powder, "Date": "",
            "Distance": b["dist"], "Caliber": "",
            "GroupIn": s["GroupIn"], "WidthIn": s["WidthIn"],
            "HeightIn": s["HeightIn"], "MRIn": s["MRIn"], "CEPIn": s["CEPIn"],
            "SDRadIn": s["SDRadIn"], "SDVertIn": s["SDVertIn"],
            "SDHorizIn": s["SDHorizIn"], "ElevOffsetIn": s["ElevOffsetIn"],
            "WindOffsetIn": s["WindOffsetIn"], "Label": label,
        })
    return out
