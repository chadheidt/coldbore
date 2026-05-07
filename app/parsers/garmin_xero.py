"""
Garmin Xero ShotView CSV parser.

Format characteristics:
    Line 1: free-text session title (used as the load label)
    Line 2: header row "#,SPEED (FPS),Δ AVG (FPS),KE (FT-LB),POWER FACTOR..."
    Then alternating per-shot rows ("1,3013.6,...") and stat rows
    ("AVERAGE SPEED,3014.2", "STD DEV,4.2", "SPREAD,12.1", ...).
"""

from ._common import parse_label


KIND = "chronograph"
NAME = "Garmin Xero"
KEY = "garmin"
IMPORT_FOLDER = "Garmin Imports"

# Header keywords that uniquely identify Garmin's CSV format
_HEADER_MARKERS = ("SPEED (FPS)", "POWER FACTOR", "KE (FT-LB)")


def detect(path):
    """Return True if this file looks like a Garmin Xero CSV."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            f.readline()                  # title line
            line2 = f.readline().strip()  # header line
        return any(m in line2 for m in _HEADER_MARKERS)
    except (OSError, UnicodeDecodeError):
        return False


def parse(path):
    """Read a Garmin Xero CSV. Returns a single chronograph record dict, or None."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  WARNING: couldn't read {path}: {e}")
        return None
    if not lines:
        return None

    title = lines[0].strip().strip('"').strip()
    tag, charge, powder = parse_label(title)

    shots = []
    avg_vel = sd = es = bullet_wt = avg_ke = None
    date_text = note = ""

    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if not parts:
            continue
        col1 = parts[0]
        col2 = parts[1] if len(parts) > 1 else ""

        # Per-shot row: column 1 is an integer shot number
        try:
            int(col1)
            try:
                shots.append(float(col2))
            except ValueError:
                pass
            continue
        except ValueError:
            pass

        # Stat row
        up = col1.upper()
        if up == "AVERAGE SPEED":
            try: avg_vel = float(col2)
            except ValueError: pass
        elif up == "STD DEV":
            try: sd = float(col2)
            except ValueError: pass
        elif up == "SPREAD":
            try: es = float(col2)
            except ValueError: pass
        elif up == "PROJECTILE WEIGHT(GRAINS)":
            try: bullet_wt = float(col2)
            except ValueError: pass
        elif up == "AVG KINETIC ENERGY":
            try: avg_ke = float(col2)
            except ValueError: pass
        elif up == "DATE":
            date_text = col2.strip().strip('"').strip()
        elif up == "SESSION NOTE":
            note = col2.strip().strip('"').strip()

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
        "AvgKE": avg_ke,
        "SessionTitle": title,
        "SessionNote": note,
    }
