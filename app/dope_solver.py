"""Predicted-DOPE overlay for the Range & DOPE panel — pure, no Qt.

Gate-4 integration of the ship-gated solver (see app/ballistics.py).
Computes PREDICTED DOPE *live* from the workbook's rifle/load inputs +
the bundled authoritative BC database (or a user-supplied manual BC).

Design rule (deliberate): the workbook only ever stores CONFIRMED
(user-entered) DOPE. Predictions are NEVER written to the workbook —
they are a live overlay the panel renders in gray/italic and the Pocket
Card uses to fill empty rows (watermarked). This keeps every existing
formula/test intact, makes "predicted vs confirmed" unambiguous, and
means a wrong/ში changed BC can never silently corrupt saved DOPE.

Inputs are read defensively (formula cells may have no cached value in a
fresh workbook). This module NEVER raises for expected conditions — it
returns a status so the UI can show the right message.
"""

from openpyxl import load_workbook

import ballistics
import component_data as _cd

# Workbook cells (Ballistics sheet derives these from Load Log).
_BAL = "Ballistics"
_MV_CELL = "K5"          # muzzle velocity (fps)
_ZERO_CELL = "E6"        # zero range (yd)
_SIGHT_CELL = "H6"       # sight height (in)
_BULLET_CELL = ("Load Log", "B9")
_CLICK_CELL = ("Load Log", "G7")     # "0.1 Mil" / "0.25 MOA" -> unit
_TEMP_CELL = ("Load Log", "G13")     # temperature (deg F), optional
_DOPE_ROWS = range(9, 19)            # Ballistics rows 9..18
_RANGE_COL = "A"

# status codes
OK = "ok"
NO_INPUTS = "no_inputs"        # MV/zero/sight not available yet
NO_BC = "no_bc"                # no curated BC and no manual override
MODEL_UNSUPPORTED = "model_unsupported"
ERROR = "error"


def _num(v):
    try:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def read_solver_inputs(workbook_path):
    """Pure read of everything the solver needs. Tolerant of missing /
    uncalculated formula cells. Returns a dict (values may be None)."""
    wb = load_workbook(workbook_path, data_only=True, keep_vba=False)
    bal = wb[_BAL]
    rows = []
    for r in _DOPE_ROWS:
        rng = _num(bal[f"{_RANGE_COL}{r}"].value)
        if rng and rng > 0:
            rows.append((r, int(round(rng))))
    click = str(wb[_CLICK_CELL[0]][_CLICK_CELL[1]].value or "").lower()
    return {
        "mv": _num(bal[_MV_CELL].value),
        "zero": _num(bal[_ZERO_CELL].value),
        "sight_h": _num(bal[_SIGHT_CELL].value),
        "temp_f": _num(wb[_TEMP_CELL[0]][_TEMP_CELL[1]].value),
        "bullet": str(wb[_BULLET_CELL[0]][_BULLET_CELL[1]].value or "").strip(),
        "unit": "moa" if "moa" in click else "mil",
        "row_ranges": rows,           # [(workbook_row, range_yd), ...]
    }


def resolve_bullet_bc(bullet_str, manual_bc=None, manual_model="G7"):
    """(bc, model, source) using the manual override else the curated
    DB keyed off the Load Log bullet string. Raises ballistics.
    BcUnavailable / BcModelUnsupported exactly like ballistics.resolve_bc
    (never fabricates, never converts models)."""
    if manual_bc is not None:
        bc, model = ballistics.resolve_bc(manual_bc=manual_bc,
                                          manual_model=manual_model)
        return bc, model, "manual"
    mfr, entry = _cd.parse_bullet(bullet_str)
    db = _cd.bullet_bc(entry) if entry else {"g7": None, "g1": None}
    bc, model = ballistics.resolve_bc(db_g7=db.get("g7"),
                                      db_g1=db.get("g1"))
    src = "database (%s %s)" % (mfr or "?", model)
    return bc, model, src


def _fmt(val, unit):
    """Predicted DOPE display string. Mil to 0.1, MOA to 0.1 — a
    starting point the shooter confirms/refines at the range."""
    return ("%.1f" % val) if unit == "mil" else ("%.1f" % val)


def predicted_dope(workbook_path, manual_bc=None, manual_model="G7",
                   temp_f=None, pressure_inhg=29.92, altitude_ft=0.0,
                   humidity_pct=50.0, wind_mph=10.0, wind_clock=3.0):
    """Live predicted DOPE for the workbook's rifle/load.

    Returns {status, message, unit, bc, bc_model, bc_source,
    atmosphere:{...}, rows:{workbook_row:{'elev','wind'}}}. rows is
    empty unless status == OK. Never raises for expected conditions.
    """
    out = {"status": ERROR, "message": "", "unit": "mil",
           "bc": None, "bc_model": None, "bc_source": None,
           "atmosphere": {}, "rows": {}}
    try:
        inp = read_solver_inputs(workbook_path)
    except Exception as e:                       # unreadable workbook
        out["message"] = str(e)
        return out
    out["unit"] = inp["unit"]

    if not inp["mv"] or inp["mv"] <= 0 or not inp["row_ranges"]:
        out["status"] = NO_INPUTS
        out["message"] = ("Set your bullet and muzzle velocity in "
                          "Rifle & Setup to see predicted DOPE.")
        return out
    zero = inp["zero"] if (inp["zero"] and inp["zero"] > 0) else 100.0
    sight_h = inp["sight_h"] if (inp["sight_h"] and inp["sight_h"] > 0) \
        else 1.75
    tf = temp_f if temp_f is not None else (
        inp["temp_f"] if inp["temp_f"] is not None else 59.0)

    try:
        bc, model, src = resolve_bullet_bc(
            inp["bullet"], manual_bc=manual_bc, manual_model=manual_model)
    except ballistics.BcModelUnsupported as e:
        out["status"] = MODEL_UNSUPPORTED
        out["message"] = str(e)
        return out
    except ballistics.BcUnavailable:
        out["status"] = NO_BC
        out["message"] = (
            "No ballistic coefficient for this bullet yet — enter the "
            "manufacturer's G7 (or G1) BC to see predicted DOPE.")
        return out

    ranges = [rng for _, rng in inp["row_ranges"]]
    try:
        sol = ballistics.solve_trajectory(
            muzzle_velocity_fps=inp["mv"], g7_bc=bc, zero_yd=zero,
            sight_height_in=sight_h, ranges_yd=ranges, temp_f=tf,
            pressure_inhg=pressure_inhg, altitude_ft=altitude_ft,
            humidity_pct=humidity_pct, wind_mph=wind_mph,
            wind_angle_clock=wind_clock, drag_model=model)
    except Exception as e:
        out["message"] = "solver error: %s" % e
        return out

    unit = inp["unit"]
    ekey = "elev_moa" if unit == "moa" else "elev_mil"
    wkey = "wind_moa" if unit == "moa" else "wind_mil"
    rows = {}
    for wb_row, rng in inp["row_ranges"]:
        s = sol.get(rng)
        if not s:
            continue
        rows[wb_row] = {"elev": _fmt(s[ekey], unit),
                        "wind": _fmt(s[wkey], unit)}
    out.update({
        "status": OK, "message": "", "unit": unit,
        "bc": bc, "bc_model": model, "bc_source": src,
        "atmosphere": {"temp_f": tf, "pressure_inhg": pressure_inhg,
                       "altitude_ft": altitude_ft,
                       "humidity_pct": humidity_pct,
                       "wind_mph": wind_mph, "wind_clock": wind_clock},
        "rows": rows,
    })
    return out
