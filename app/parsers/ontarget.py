"""
OnTarget PC v2.* / OnTarget TDS v3.* point-data CSV parser.

Format (documented; produced by OnTarget "Tools -> Export Point Data",
matches the well-known shotGroups `readDataOT2` reader). Header row, then
one row per shot:

    Project Title, Group, Ammunition, Distance, Aim X, Aim Y,
    Center X, Center Y, Point X, Point Y[, Velocity]

OnTarget exports raw impact coordinates, NOT pre-computed group
dimensions, so we group rows by (Project Title, Group) and compute the
group stats from the points via _common.group_stats_from_points. Point
coordinates are in inches.

VALIDATION STATUS: built from the publicly documented column layout, NOT
yet verified against a real OnTarget export. `NEEDS_REAL_SAMPLE_VALIDATION`
is True until a genuine export file is checked (header casing/whitespace,
units, decimal locale). Do not present as fully trusted until then.
"""

import csv
import os

from ._common import parse_label, group_stats_from_points


KIND = "group"
NAME = "OnTarget"
KEY = "ontarget"
IMPORT_FOLDER = "OnTarget Imports"

# True until a real OnTarget export has been parsed and confirmed.
NEEDS_REAL_SAMPLE_VALIDATION = True

# Column names that uniquely identify the OnTarget point-data export.
_REQUIRED_COLS = ("Point X", "Point Y", "Center X", "Aim X")


def _norm(name):
    return (name or "").strip().lstrip("﻿").lower()


def detect(path):
    """Return True if this looks like an OnTarget point-data CSV."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            header = f.readline()
    except (OSError, UnicodeDecodeError):
        return False
    cols = {_norm(c) for c in header.split(",")}
    return all(_norm(r) in cols for r in _REQUIRED_COLS)


def _num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def parse(path):
    """Read an OnTarget export. Returns a list of group records.

    One record per (Project Title, Group). Group dimensions are computed
    from the per-shot Point X/Y. Load label is taken from the filename
    when it parses to a load-style label (e.g. 'P1 45.5 H4350.csv'),
    otherwise from the Project Title / Group / Ammunition columns.
    """
    filename_label = os.path.splitext(os.path.basename(path))[0]
    fn_tag, fn_charge, fn_powder = parse_label(filename_label)
    use_filename = fn_charge is not None

    buckets = {}   # (project, group) -> dict(rows)
    try:
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # Normalize fieldnames so we tolerate casing/whitespace drift.
            keymap = {_norm(k): k for k in (reader.fieldnames or [])}

            def g(row, label):
                k = keymap.get(_norm(label))
                return row.get(k) if k else None

            for row in reader:
                proj = (g(row, "Project Title") or "").strip()
                grp = (g(row, "Group") or "").strip()
                ammo = (g(row, "Ammunition") or "").strip()
                key = (proj, grp)
                b = buckets.setdefault(key, {
                    "proj": proj, "grp": grp, "ammo": ammo,
                    "dist": _num(g(row, "Distance")),
                    "aimx": _num(g(row, "Aim X")), "aimy": _num(g(row, "Aim Y")),
                    "pts": [],
                })
                px, py = _num(g(row, "Point X")), _num(g(row, "Point Y"))
                if px is not None and py is not None:
                    b["pts"].append((px, py))
    except Exception as e:
        print(f"  WARNING: couldn't read {path}: {e}")
        return []

    groups = []
    for (proj, grp), b in buckets.items():
        if use_filename:
            label = filename_label
            tag, charge, powder = fn_tag, fn_charge, fn_powder
        else:
            label = " ".join(x for x in (proj, grp, b["ammo"]) if x).strip()
            tag, charge, powder = parse_label(label or grp or proj)
        aim = (b["aimx"], b["aimy"]) if b["aimx"] is not None else None
        stats = group_stats_from_points(b["pts"], aim=aim)
        groups.append({
            "kind": KIND,
            "Source": KEY,
            "Tag": tag,
            "ChargeOrJump": charge,
            "Powder": powder,
            "Date": "",
            "Distance": b["dist"],
            "Caliber": b["ammo"],
            "GroupIn": stats["GroupIn"],
            "WidthIn": stats["WidthIn"],
            "HeightIn": stats["HeightIn"],
            "MRIn": stats["MRIn"],
            "CEPIn": stats["CEPIn"],
            "SDRadIn": stats["SDRadIn"],
            "SDVertIn": stats["SDVertIn"],
            "SDHorizIn": stats["SDHorizIn"],
            "ElevOffsetIn": stats["ElevOffsetIn"],
            "WindOffsetIn": stats["WindOffsetIn"],
            "Label": label,
        })
    return groups
