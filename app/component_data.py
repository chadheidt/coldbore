"""Loader + accessors for the bundled component data (Smart Setup).

component_data.json drives the cascading bullet/primer pickers, the
turret-click safeguard list, and the curated chrono/brass options. It
is ALSO the seed of the ballistic-solver BC database (the solver adds
BC fields + grows the bullet list; same file, never restructured).

Bundle-aware exactly like demo_tour.get_demo_screenshot: in the .app
modules load from Contents/Resources/lib/pythonXX.zip, so __file__ is
inside the zip — resolve the real Contents/Resources/ via
sys.executable. Never raises; returns safe empties if missing.
"""

import json
import os
import sys

_FILENAME = "component_data.json"
_cache = None


def _data_path():
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        try:
            exe = os.path.abspath(sys.executable)
            p = os.path.join(os.path.dirname(os.path.dirname(exe)),
                             "Resources", _FILENAME)
            if os.path.isfile(p):
                return p
        except (OSError, ValueError):
            pass
    for cand in (
        os.path.join(here, "resources", _FILENAME),
        os.path.normpath(os.path.join(here, "..", "Resources", _FILENAME)),
        os.path.normpath(os.path.join(here, "..", "..", "Resources",
                                      _FILENAME)),
    ):
        if os.path.isfile(cand):
            return cand
    return None


def load_component_data():
    global _cache
    if _cache is not None:
        return _cache
    p = _data_path()
    try:
        with open(p, encoding="utf-8") as f:
            _cache = json.load(f)
    except Exception:
        _cache = {}
    return _cache


def turret_clicks():
    """EXACT strings the Ballistics click-count formulas accept. A value
    outside this set silently breaks all click math — so the turret
    field is a LOCKED dropdown of exactly these."""
    return list(load_component_data().get(
        "turret_clicks", ["0.1 Mil", "0.05 Mil", "1/4 MOA", "1/8 MOA"]))


def chronographs():
    return list(load_component_data().get("chronographs", []))


def brass_options():
    return list(load_component_data().get("brass", []))


def primer_manufacturers():
    return list(load_component_data().get("primers", {}).keys())


def primers_for(manufacturer):
    return list(load_component_data().get("primers", {}).get(
        manufacturer, []))


def bullet_manufacturers():
    return list(load_component_data().get("bullets", {}).keys())


def bullets_for(manufacturer):
    """List of {name, weight, cal} dicts for a manufacturer."""
    return list(load_component_data().get("bullets", {}).get(
        manufacturer, []))


# ---- compose / parse the single workbook cell strings -----------------
# Bullet cell format matches the existing workbook ("Hornady 140gr
# ELD-M"); primer cell is "CCI BR-2".

def bullet_label(entry):
    """Display label for a bullet entry inside its manufacturer list."""
    return f"{entry['weight']}gr {entry['name']} ({entry.get('cal', '')})".strip()


def compose_bullet(manufacturer, entry):
    return f"{manufacturer} {entry['weight']}gr {entry['name']}".strip()


def compose_primer(manufacturer, model):
    return f"{manufacturer} {model}".strip()


def parse_bullet(cell_value):
    """Best-effort reverse of compose_bullet -> (manufacturer, entry) so
    an existing workbook value pre-selects the cascade. Returns
    (None, None) if it doesn't match the curated data (caller then
    treats it as a free-typed value)."""
    if not cell_value:
        return (None, None)
    s = str(cell_value).strip()
    data = load_component_data().get("bullets", {})
    for mfr, entries in data.items():
        if s.lower().startswith(mfr.lower() + " "):
            rest = s[len(mfr):].strip()
            for e in entries:
                if compose_bullet(mfr, e)[len(mfr):].strip().lower() == \
                        rest.lower():
                    return (mfr, e)
            return (mfr, None)
    return (None, None)


def parse_primer(cell_value):
    if not cell_value:
        return (None, None)
    s = str(cell_value).strip()
    data = load_component_data().get("primers", {})
    for mfr, models in data.items():
        if s.lower().startswith(mfr.lower() + " "):
            model = s[len(mfr):].strip()
            for m in models:
                if m.lower() == model.lower():
                    return (mfr, m)
            return (mfr, model or None)
    return (None, None)
