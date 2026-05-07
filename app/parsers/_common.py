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
