"""
LabRadar Doppler chronograph per-series report CSV parser.

LabRadar writes one report file per shot series to its SD card (commonly
"SRxxxx Report.csv"). The well-known community layout (also handled by
open-source tools such as github.com/Jeremy-L411/Lab_radar_csv_combine_report)
is a metadata header block followed by a per-shot table. Real files vary by
firmware and locale: delimiter is ',' OR ';', velocity may be in fps or m/s,
and metadata key spellings differ. This parser sniffs the delimiter, finds
the velocity column, collects per-shot velocities, and uses the file's own
Average/Std-Dev/Spread metadata when present (else computes them).

VALIDATION STATUS: built from the publicly documented/community structure,
NOT verified against a real LabRadar export. `NEEDS_REAL_SAMPLE_VALIDATION`
is True until a genuine file is checked. detect() is intentionally strict
so it never claims a Garmin/other CSV by accident.
"""

import csv
import io
import os

from ._common import parse_label


KIND = "chronograph"
NAME = "LabRadar"
KEY = "labradar"
IMPORT_FOLDER = "LabRadar Imports"

NEEDS_REAL_SAMPLE_VALIDATION = True

_MS_TO_FPS = 3.280839895
# Strong LabRadar identifiers — require one of these to claim the file.
_ID_MARKERS = ("labradar", "series no", "device id", "total numbers")
_VEL_COL_HINTS = ("velocity", "v0", "speed", "muzzle")


def _read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def detect(path):
    try:
        head = _read(path)[:4000].lower()
    except (OSError, UnicodeDecodeError):
        return False
    if not any(m in head for m in _ID_MARKERS):
        return False
    # Must also look velocity-oriented, and must NOT be a Garmin Xero file
    # (those carry "POWER FACTOR"/"KE (FT-LB)" and no LabRadar markers).
    if "power factor" in head and "labradar" not in head:
        return False
    return any(h in head for h in _VEL_COL_HINTS)


def _sniff_delim(sample):
    counts = {d: sample.count(d) for d in (";", ",", "\t")}
    return max(counts, key=counts.get) or ","


def parse(path):
    """Return a single chronograph record dict, or None."""
    try:
        text = _read(path)
    except Exception as e:
        print(f"  WARNING: couldn't read {path}: {e}")
        return None
    if not text.strip():
        return None

    delim = _sniff_delim(text[:4000])
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))

    title = ""
    date_text = note = ""
    avg_vel = sd = es = bullet_wt = None
    units_ms = "m/s" in text.lower() and "f" + "ps" not in text.lower()

    # Locate a header row whose cells include a velocity-ish column.
    hdr_idx = vel_col = None
    for i, r in enumerate(rows):
        low = [c.strip().lower() for c in r]
        for j, c in enumerate(low):
            if any(h in c for h in _VEL_COL_HINTS) and "avg" not in c \
                    and "average" not in c and "std" not in c:
                hdr_idx, vel_col = i, j
                break
        if hdr_idx is not None:
            break

    shots = []
    # Metadata lines are "key, value" pairs above/around the table.
    for r in rows:
        if len(r) < 2:
            if r and not title:
                title = r[0].strip().strip('"')
            continue
        key = r[0].strip().lower()
        val = r[1].strip().strip('"')
        if key in ("average", "avg", "average velocity", "mean"):
            avg_vel = _f(val)
        elif key in ("std dev", "std-dev", "standard deviation", "sd"):
            sd = _f(val)
        elif key in ("spread", "extreme spread", "es"):
            es = _f(val)
        elif key in ("bullet weight", "projectile weight", "weight"):
            bullet_wt = _f(val)
        elif key in ("date", "series date"):
            date_text = val
        elif key in ("notes", "note", "session note"):
            note = val
        elif key in ("series", "series no", "name") and not title:
            title = val

    if hdr_idx is not None:
        for r in rows[hdr_idx + 1:]:
            if len(r) <= vel_col:
                continue
            v = _f(r[vel_col])
            if v is not None and v > 0:
                shots.append(v * _MS_TO_FPS if units_ms else v)

    if units_ms:
        if avg_vel is not None:
            avg_vel *= _MS_TO_FPS
        if sd is not None:
            sd *= _MS_TO_FPS
        if es is not None:
            es *= _MS_TO_FPS

    if shots:
        if avg_vel is None:
            avg_vel = sum(shots) / len(shots)
        if es is None:
            es = max(shots) - min(shots)
        if sd is None and len(shots) > 1:
            m = sum(shots) / len(shots)
            sd = (sum((s - m) ** 2 for s in shots) / (len(shots) - 1)) ** 0.5

    tag, charge, powder = parse_label(
        title or os.path.splitext(os.path.basename(path))[0])
    if not shots and avg_vel is None:
        return None
    return {
        "kind": KIND,
        "Source": KEY,
        "Tag": tag,
        "ChargeOrJump": charge,
        "Powder": powder,
        "Date": date_text,
        "Shots": shots,
        "AvgVel": avg_vel,
        "SD": sd,
        "ES": es,
        "BulletWt": bullet_wt,
        "AvgKE": None,
        "SessionTitle": title,
        "SessionNote": note,
    }


def _f(s):
    try:
        return float(str(s).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
