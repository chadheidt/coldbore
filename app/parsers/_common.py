"""
Shared helper functions used by all parser modules.

Keep this module dependency-free (no external libraries) so any parser can
import it without dragging in extras.
"""

import re


def parse_label(s):
    """Split a load-style label into (Tag, ChargeOrJump, Powder).

    Examples:
        'P1 45.5 H4350'       -> ('P1', 45.5, 'H4350')
        'S7 0.070 H4350'      -> ('S7', 0.07, 'H4350')
        'CONFIRM-1 41.5 RL26' -> ('CONFIRM-1', 41.5, 'RL26')
        'P1 45.5'             -> ('P1', 45.5, '')
        ''                    -> ('', None, '')
    """
    if not s:
        return ("", None, "")
    tokens = [t for t in re.split(r"\s+", s.strip()) if t]
    if not tokens:
        return ("", None, "")
    tag = tokens[0].upper()
    first_num = None
    powder = ""
    for tok in tokens[1:]:
        try:
            n = float(tok.replace(",", ""))
            if first_num is None:
                first_num = n
            continue
        except ValueError:
            pass
        if not powder:
            powder = tok
    return (tag, first_num, powder)


def _to_float_locale_aware(s):
    """Parse a numeric string that might use either US (1,234.56) or European
    (1.234,56) decimal conventions. Strategy:
      - If only ',' present (no '.'), treat ',' as decimal separator
      - If both present, last one is the decimal separator
      - Otherwise treat as US format
    Returns float or None.
    """
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    has_dot = "." in s
    has_comma = "," in s
    if has_comma and not has_dot:
        # European: comma is decimal
        s = s.replace(",", ".")
    elif has_comma and has_dot:
        # Mixed — last separator is decimal, drop the other (thousands sep)
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def extract_inches(s):
    """Pull the numeric inches value from a display string like:
       '0.202" (0.056 MIL)'  -> 0.202
       '0.358"'              -> 0.358
       '0,358"' (German)     -> 0.358
       None or unparseable   -> None
    """
    if not s:
        return None
    s = str(s).strip().replace('"', "").replace("''", "")
    m = re.match(r"\s*([-+]?[\d.,]+)", s)
    if m:
        return _to_float_locale_aware(m.group(1))
    return None


def extract_signed(s):
    """Pull a signed number like '+ 0.13' or '- 0.07' as a float.
    Locale-aware (handles European decimal commas)."""
    if not s:
        return None
    cleaned = re.sub(r"\s+", "", str(s))
    return _to_float_locale_aware(cleaned)


def group_stats_from_points(points, aim=None):
    """Compute group statistics from a list of (x, y) shot coordinates.

    Used by point-data parsers (OnTarget, ShotMarker, SMT) that export raw
    impact coordinates rather than pre-computed group dimensions. Inputs and
    outputs are in whatever linear unit the points are in (inches for
    OnTarget/ShotMarker/SMT) — the caller ensures unit sanity.

    points : iterable of (x, y) numeric pairs.
    aim    : optional (x, y) point of aim. If given, ElevOffsetIn /
             WindOffsetIn = group centroid minus aim (Y = elevation,
             X = windage), matching the signed-offset convention used
             elsewhere.

    Returns a dict with the group-record numeric keys (GroupIn, WidthIn,
    HeightIn, MRIn, CEPIn, SDRadIn, SDVertIn, SDHorizIn, ElevOffsetIn,
    WindOffsetIn). Uncomputable values are None. One shot → zero spreads.
    """
    pts = []
    for p in points or []:
        try:
            x = float(p[0]); y = float(p[1])
        except (TypeError, ValueError, IndexError):
            continue
        pts.append((x, y))

    out = {k: None for k in (
        "GroupIn", "WidthIn", "HeightIn", "MRIn", "CEPIn",
        "SDRadIn", "SDVertIn", "SDHorizIn", "ElevOffsetIn", "WindOffsetIn")}
    if not pts:
        return out

    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    out["WidthIn"] = max(xs) - min(xs)
    out["HeightIn"] = max(ys) - min(ys)

    es = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            d = ((pts[i][0] - pts[j][0]) ** 2 +
                 (pts[i][1] - pts[j][1]) ** 2) ** 0.5
            if d > es:
                es = d
    out["GroupIn"] = es

    radii = [((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in pts]
    mr = sum(radii) / n
    out["MRIn"] = mr
    sr = sorted(radii)
    mid = n // 2
    out["CEPIn"] = sr[mid] if n % 2 else (sr[mid - 1] + sr[mid]) / 2.0

    def _sd(vals, mean):
        if len(vals) < 2:
            return 0.0
        return (sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5

    out["SDVertIn"] = _sd(ys, cy)
    out["SDHorizIn"] = _sd(xs, cx)
    out["SDRadIn"] = _sd(radii, mr)

    if aim is not None:
        try:
            ax = float(aim[0]); ay = float(aim[1])
            out["WindOffsetIn"] = cx - ax
            out["ElevOffsetIn"] = cy - ay
        except (TypeError, ValueError, IndexError):
            pass
    return out
