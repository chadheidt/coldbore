"""
BallisticX target-group analysis CSV parser.

Format characteristics:
    Line 1: header row starting with "Label,Distance,Caliber,CreatedAt,..."
    Subsequent lines: one row per analyzed target group, with all dimensions
    expressed as display strings like "0.358\" (0.342 MOA)".

Label routing quirk: BallisticX's in-CSV Label column is often unreliable
(some users can't edit it inside the app), so we prefer the CSV filename as
the load label. Drop in 'P1 45.5 H4350.csv' and the parser routes it to row P1
even if the in-CSV Label column is blank or wrong.
"""

import csv
import os

from ._common import parse_label, extract_inches, extract_signed


KIND = "group"
NAME = "BallisticX"
KEY = "ballisticx"
IMPORT_FOLDER = "BallisticX Imports"

# Header field names that uniquely identify BallisticX's CSV format
_HEADER_MARKERS = (
    "GroupSizeDisplay",
    "MeanRadiusDisplay",
    "OverallWidthDisplay",
    "CEPDisplay",
    "SDRadialDisplay",
)


def detect(path):
    """Return True if this file looks like a BallisticX CSV."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            line1 = f.readline().strip()
        if any(m in line1 for m in _HEADER_MARKERS):
            return True
        # Fallback: BallisticX header sometimes leads with "Label," and lots of commas
        if line1.startswith("Label,") and line1.count(",") >= 5:
            return True
        return False
    except (OSError, UnicodeDecodeError):
        return False


def parse(path):
    """Read a BallisticX CSV. Returns a list of group records (one per row).

    Label source priority:
      1. CSV filename (e.g., 'P1 45.5 H4350.csv') if it parses to a load-style label.
      2. The in-CSV Label column otherwise.
    """
    groups = []
    filename_label = os.path.splitext(os.path.basename(path))[0]
    fn_tag, fn_charge, fn_powder = parse_label(filename_label)
    use_filename = fn_charge is not None
    try:
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if use_filename:
                    label = filename_label
                    tag, charge, powder = fn_tag, fn_charge, fn_powder
                else:
                    label = (row.get("Label") or "").strip()
                    tag, charge, powder = parse_label(label)
                try:
                    distance = float(row.get("Distance", 0))
                except (ValueError, TypeError):
                    distance = None
                groups.append({
                    "kind": KIND,
                    "Source": KEY,
                    "Tag": tag,
                    "ChargeOrJump": charge,
                    "Powder": powder,
                    "Date": (row.get("CreatedAt") or "").strip(),
                    "Distance": distance,
                    "Caliber": (row.get("Caliber") or "").strip(),
                    "GroupIn": extract_inches(row.get("GroupSizeDisplay")),
                    "WidthIn": extract_inches(row.get("OverallWidthDisplay")),
                    "HeightIn": extract_inches(row.get("OverallHeightDisplay")),
                    "MRIn": extract_inches(row.get("MeanRadiusDisplay")),
                    "CEPIn": extract_inches(row.get("CEPDisplay")),
                    "SDRadIn": extract_inches(row.get("SDRadialDisplay")),
                    "SDVertIn": extract_inches(row.get("SDVerticalDisplay")),
                    "SDHorizIn": extract_inches(row.get("SDHorizontalDisplay")),
                    "ElevOffsetIn": extract_signed(row.get("ElevationDisplay")),
                    "WindOffsetIn": extract_signed(row.get("WindageDisplay")),
                    "Label": label,
                })
    except Exception as e:
        print(f"  WARNING: couldn't read {path}: {e}")
    return groups
