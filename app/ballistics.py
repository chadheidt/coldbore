"""Zero-dependency G7 point-mass ballistic solver (DRAFT).

[[loadscope-ballistic-solver-v015]]. Predicts the Ballistics-tab DOPE
(elevation + wind per distance) from the data Loadscope already has
(muzzle velocity, zero, sight height) plus a G7 BC and atmospherics.

Path B: pure-Python, NO numpy/scipy (those aren't in the py2app bundle
and adding a sci dep is the fragility class that's bitten us). Standard
3-DOF point-mass integration against the published G7 reference drag
table scaled by the bullet's G7 BC — the same model class as Strelok /
GeoBallistics / the free Hornady & Berger web calculators.

STATUS (2026-05-16): RETARDATION MATH FIXED + SELF-VALIDATED, STILL
SHIP-GATED. DO NOT WIRE / DO NOT SHIP until the gates below clear.

What was wrong (2026-05-15 broken-draft): the integrator divided by the
retardation coefficient instead of multiplying by it
(`decel = sigma*cd*v / (g7_bc*K)`), a ~1/K^2 ≈ 2.3e7 error — the
"~7 orders of magnitude" the sanity test caught (TOF≈0.001s @ 1000yd).

What is fixed (2026-05-16): the standard McCoy / GNU-Ballistics G7-BC
point-mass retardation is now derived from first principles inline and
applied correctly (see `_RETARD_K` derivation + `_fly`). The drag
table, air_density_ratio(), and module API were already correct.

Self-validation (tests/test_ballistics.py): physically-sane checks
(monotonic come-up, plausible TOF, sane drift) PLUS a ballpark match to
published reference DOPE for a known 6.5 Creedmoor 140 ELD-M load. A
self-check confirms the math is no longer broken and is in the right
regime — it is NECESSARY BUT NOT SUFFICIENT.

REMAINING SHIP-GATES (require Chad — do NOT bypass):
  (1) Validate vs a LIVE professional solver (Hornady 4DOF /
      GeoBallistics / Applied Ballistics) on the reference loads.
      Self-validation here is from training-knowledge reference
      numbers, not an authoritative live query.
  (2) BC database = authoritative manufacturer-sourced G7 values.
      Do NOT fabricate. No BC values are bundled yet.
  (3) Signed-disclaimer predicted-DOPE language + DISCLAIMER_VERSION
      bump (re-prompt all users).
  (4) Predicted-vs-confirmed DOPE UX in the Range&DOPE panel +
      Chad review.
Nothing imports this module; it remains a safe no-op until gates clear.

Units: yards / feet / inches / fps / grains, US convention.
"""

import math

# --- Standard G7 reference drag table (Cd vs Mach) ---------------------
# THE authoritative standard G7 (McCoy) drag function, verbatim from
# JBM Ballistics' published table (jbmballistics.com/.../text/mcg7.txt),
# the exact 84-point Mach->Cd standard JBM's own solver integrates. This
# is a FIXED published reference, not estimated.
#
# History: a prior hand-truncated 20-point version had supersonic Cd
# values 5-15% LOW (e.g. M2.0 was 0.2604 vs the standard 0.2980), which
# made the solver retain ~8% too much velocity at 1000 yd and under-
# predict come-up/wind. Gate-1 validation vs JBM caught it; replaced
# with the full authoritative table. Linear-interpolated.
_G7_MACH = [
    0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
    0.5, 0.55, 0.6, 0.65, 0.7, 0.725, 0.75, 0.775, 0.8, 0.825,
    0.85, 0.875, 0.9, 0.925, 0.95, 0.975, 1, 1.025, 1.05, 1.075,
    1.1, 1.125, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.5, 1.55,
    1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2, 2.05,
    2.1, 2.15, 2.2, 2.25, 2.3, 2.35, 2.4, 2.45, 2.5, 2.55,
    2.6, 2.65, 2.7, 2.75, 2.8, 2.85, 2.9, 2.95, 3, 3.1,
    3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.2,
    4.4, 4.6, 4.8, 5,
]
_G7_CD = [
    0.1198, 0.1197, 0.1196, 0.1194, 0.1193, 0.1194, 0.1194, 0.1194, 0.1193, 0.1193,
    0.1194, 0.1193, 0.1194, 0.1197, 0.1202, 0.1207, 0.1215, 0.1226, 0.1242, 0.1266,
    0.1306, 0.1368, 0.1464, 0.1660, 0.2054, 0.2993, 0.3803, 0.4015, 0.4043, 0.4034,
    0.4014, 0.3987, 0.3955, 0.3884, 0.3810, 0.3732, 0.3657, 0.3580, 0.3440, 0.3376,
    0.3315, 0.3260, 0.3209, 0.3160, 0.3117, 0.3078, 0.3042, 0.3010, 0.2980, 0.2951,
    0.2922, 0.2892, 0.2864, 0.2835, 0.2807, 0.2779, 0.2752, 0.2725, 0.2697, 0.2670,
    0.2643, 0.2615, 0.2588, 0.2561, 0.2533, 0.2506, 0.2479, 0.2451, 0.2424, 0.2368,
    0.2313, 0.2258, 0.2205, 0.2154, 0.2106, 0.2060, 0.2017, 0.1975, 0.1935, 0.1861,
    0.1793, 0.1730, 0.1672, 0.1618,
]

# --- Standard G1 reference drag table (Cd vs Mach) --------------------
# THE authoritative standard G1 (Ingalls/McCoy) drag function, verbatim
# from JBM Ballistics' published table (.../downloads/text/mcg1.txt),
# the same authoritative source as the G7 table above. Needed because
# many makers (Sierra, Nosler, Barnes, older Lapua) publish G1 BCs;
# we store the maker's NATIVE model and never force-convert G1<->G7.
_G1_MACH = [
    0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45,
    0.5, 0.55, 0.6, 0.7, 0.725, 0.75, 0.775, 0.8, 0.825, 0.85,
    0.875, 0.9, 0.925, 0.95, 0.975, 1, 1.025, 1.05, 1.075, 1.1,
    1.125, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5, 1.55,
    1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2, 2.05,
    2.1, 2.15, 2.2, 2.25, 2.3, 2.35, 2.4, 2.45, 2.5, 2.6,
    2.7, 2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6,
    3.7, 3.8, 3.9, 4, 4.2, 4.4, 4.6, 4.8, 5,
]
_G1_CD = [
    0.2629, 0.2558, 0.2487, 0.2413, 0.2344, 0.2278, 0.2214, 0.2155, 0.2104, 0.2061,
    0.2032, 0.2020, 0.2034, 0.2165, 0.2230, 0.2313, 0.2417, 0.2546, 0.2706, 0.2901,
    0.3136, 0.3415, 0.3734, 0.4084, 0.4448, 0.4805, 0.5136, 0.5427, 0.5677, 0.5883,
    0.6053, 0.6191, 0.6393, 0.6518, 0.6589, 0.6621, 0.6625, 0.6607, 0.6573, 0.6528,
    0.6474, 0.6413, 0.6347, 0.6280, 0.6210, 0.6141, 0.6072, 0.6003, 0.5934, 0.5867,
    0.5804, 0.5743, 0.5685, 0.5630, 0.5577, 0.5527, 0.5481, 0.5438, 0.5397, 0.5325,
    0.5264, 0.5211, 0.5168, 0.5133, 0.5105, 0.5084, 0.5067, 0.5054, 0.5040, 0.5030,
    0.5022, 0.5016, 0.5010, 0.5006, 0.4998, 0.4995, 0.4992, 0.4990, 0.4988,
]

_RHO0 = 0.0764742          # ICAO sea-level standard air density, lb/ft^3
_SPEED_SOUND_STD = 1116.45  # fps at ICAO 59F sea level
_G = 32.174                # ft/s^2

# --- Standard G7-BC point-mass retardation coefficient ----------------
# Derivation (McCoy "Modern Exterior Ballistics" Ch.5 / the same model
# JBM & GNU Ballistics use):
#
#   Drag deceleration of the actual bullet:
#       a_drag = F_d / m = (rho * V^2 * Cd * A) / (2 * m)
#   BC method: actual Cd = i * Cd_std(M); G7 BC = m / (d^2 * i)
#   [BC in lb/in^2, m bullet weight in lb, d in inches]. Substitute
#   i = m / (d^2 * BC) and A = pi*d^2/4 — the d^2 cancels:
#       a_drag = (pi/8) * rho * Cd_std(M) * V^2 / BC          (1)
#
#   US-unit reconciliation: rho here is WEIGHT density (lb/ft^3) and BC
#   uses bullet WEIGHT, so a 1/g appears in mass-density and a g in the
#   weight-based sectional density — they cancel. The in^2 -> ft^2 area
#   conversion contributes a factor 144. Folding constants:
#       a_drag = (pi / (8*144)) * rho0 * sigma * Cd_std(M) * V^2 / BC
#              =  _RETARD_K       * sigma * Cd_std(M) * V^2 / BC
#   where sigma = rho/rho0 (air-density ratio) and
#       _RETARD_K = pi * rho0 / 1152
#
# Sanity: pi*0.0764742/1152 = 2.0856e-4 — matches the value the original
# scaffold *intended* (it had 2.08551e-4 but then DIVIDED by it; the bug
# was the operator/structure, not the magnitude). Computed exactly here
# so it is self-documenting and not a magic literal.
_RETARD_K = math.pi * _RHO0 / 1152.0   # ~= 2.0856e-04


def _interp_cd(mach, mach_tbl, cd_tbl):
    if mach <= mach_tbl[0]:
        return cd_tbl[0]
    if mach >= mach_tbl[-1]:
        return cd_tbl[-1]
    for i in range(1, len(mach_tbl)):
        if mach <= mach_tbl[i]:
            m0, m1 = mach_tbl[i - 1], mach_tbl[i]
            c0, c1 = cd_tbl[i - 1], cd_tbl[i]
            return c0 + (c1 - c0) * (mach - m0) / (m1 - m0)
    return cd_tbl[-1]


def _g7_cd(mach):
    return _interp_cd(mach, _G7_MACH, _G7_CD)


def _g1_cd(mach):
    return _interp_cd(mach, _G1_MACH, _G1_CD)


# Drag-curve dispatch by the BC's native model. Same retardation
# formula and _RETARD_K for both (the BC is defined the same way
# relative to each model's standard projectile); only the Cd(M) curve
# differs. We NEVER convert between models.
_DRAG_TABLES = {"G7": (_G7_MACH, _G7_CD), "G1": (_G1_MACH, _G1_CD)}


def _drag_cd(mach, model):
    tbl = _DRAG_TABLES.get((model or "G7").strip().upper())
    if tbl is None:
        raise BcModelUnsupported(
            "Unknown drag model %r; supported: G7, G1." % (model,))
    return _interp_cd(mach, tbl[0], tbl[1])


def air_density_ratio(temp_f=59.0, pressure_inhg=29.92, altitude_ft=0.0,
                      humidity_pct=50.0):
    """Air-density / ICAO-standard ratio (sigma). If altitude is given
    and pressure left at standard, derive pressure from the standard
    atmosphere; an explicitly supplied station pressure wins. Standard,
    verifiable against ICAO values (NOT estimated)."""
    if altitude_ft and abs(pressure_inhg - 29.92) < 1e-6:
        # ICAO barometric formula (troposphere)
        pressure_inhg = 29.92 * (1 - 6.8753e-6 * altitude_ft) ** 5.2559
    temp_r = temp_f + 459.67                       # Rankine
    # density ∝ P / T ; humidity slightly lowers density (water vapor
    # lighter than dry air) — small ICAO-style correction.
    dry_ratio = (pressure_inhg / 29.92) * (518.67 / temp_r)
    humidity_corr = 1.0 - 0.0010 * (humidity_pct / 100.0)
    return dry_ratio * humidity_corr


# --- BC resolution (manual override vs curated DB) --------------------
# The solver carries BOTH the standard G7 and G1 drag curves and solves
# in whichever model the BC is published. Per the project rule we NEVER
# convert a BC between models (force-conversion injects error and burns
# the customer) — the BC's native model selects its matching curve.

class BcUnavailable(Exception):
    """No usable BC: none supplied and none curated for this bullet.
    The UI should prompt the shooter to enter a measured/published BC."""


class BcModelUnsupported(Exception):
    """A BC was tagged with a drag model the solver doesn't carry
    (only G7 and G1 are supported). Never silently converted."""


def resolve_bc(manual_bc=None, manual_model="G7", db_g7=None, db_g1=None):
    """Decide which (BC, model) pair feeds solve_trajectory.

    Precedence: an explicit user override wins over the curated DB; a
    curated native-G7 wins over native-G1 when a bullet has both
    published (G7 is less velocity-band sensitive for modern match
    bullets). Returns ``(bc_value: float, model: 'G7'|'G1')``.

      * manual_bc + manual_model G7/G1 -> use it in that model
      * manual_bc + other model        -> BcModelUnsupported
      * else curated db_g7             -> (db_g7, 'G7')
      * else curated db_g1             -> (db_g1, 'G1')
      * else                           -> BcUnavailable

    Never fabricates and never converts between models.
    """
    if manual_bc is not None:
        model = (manual_model or "G7").strip().upper()
        if model in _DRAG_TABLES:
            return (float(manual_bc), model)
        raise BcModelUnsupported(
            "Manual BC given as %r; supported drag models are G7 and "
            "G1 (no conversion)." % (manual_model,))
    if db_g7 is not None:
        return (float(db_g7), "G7")
    if db_g1 is not None:
        return (float(db_g1), "G1")
    raise BcUnavailable(
        "No ballistic coefficient available for this bullet. Enter the "
        "manufacturer's published or your measured BC.")


def solve_trajectory(muzzle_velocity_fps, g7_bc, zero_yd=100.0,
                     sight_height_in=1.75, ranges_yd=None,
                     temp_f=59.0, pressure_inhg=29.92, altitude_ft=0.0,
                     humidity_pct=50.0, wind_mph=10.0,
                     wind_angle_clock=3.0, dt=0.0005, drag_model="G7"):
    """Return {range_yd: {'drop_in','elev_moa','elev_mil','wind_in',
    'wind_moa','wind_mil','tof_s'}}. Point-mass RK-free Euler at small
    dt; standard drag curve scaled by BC; gravity; constant crosswind.

    ``g7_bc`` is the ballistic coefficient in ``drag_model``'s reference
    ('G7' default, or 'G1'); the matching standard curve is used. The
    name is kept for backward compatibility. Never converts models.

    DRAFT — see module docstring ship-gate before any reliance/ship.
    """
    if ranges_yd is None:
        ranges_yd = list(range(100, 1100, 100))
    sigma = air_density_ratio(temp_f, pressure_inhg, altitude_ft,
                              humidity_pct)
    speed_sound = _SPEED_SOUND_STD * math.sqrt(
        (temp_f + 459.67) / 518.67)
    # Resolve the BC's native standard drag curve ONCE (validate the
    # model up front; no per-step dict/normalise cost). Never converted.
    _dm = _DRAG_TABLES.get((drag_model or "G7").strip().upper())
    if _dm is None:
        raise BcModelUnsupported(
            "Unknown drag model %r; supported: G7, G1." % (drag_model,))
    _dm_mach, _dm_cd = _dm
    # Standard G7-BC point-mass retardation (see _RETARD_K derivation):
    #   a_drag = _RETARD_K * sigma * Cd_std(M) * V^2 / BC
    # The integrator below works with E = a_drag / V (a per-second rate),
    # so that ax = -E*vx, ay = -E*vy reproduces the vector drag
    # deceleration opposite the velocity vector. Hence E carries ONE
    # power of v here and the second comes from the *vx / *vy below.

    # Integrate to every requested range AND the zero range (the zero
    # range is needed to re-zero the sight line analytically below).
    zint = int(round(zero_yd))
    fly_ranges = sorted(set(int(r) for r in ranges_yd) | {zint})

    def _fly(launch_angle_rad, want_wind=False):
        # state in feet; x downrange, y vertical (line of bore at 0)
        vx = muzzle_velocity_fps * math.cos(launch_angle_rad)
        vy = muzzle_velocity_fps * math.sin(launch_angle_rad)
        vz = 0.0         # horizontal (cross-range) velocity, ft/s
        x = 0.0
        y = 0.0
        z = 0.0          # horizontal wind drift (ft)
        t = 0.0
        wind_fps = wind_mph * 1.46667
        # crosswind component from clock angle (3 o'clock = full value)
        cross = wind_fps * math.sin(wind_angle_clock / 12.0 * 2 * math.pi)
        out = {}
        targets = [r * 3.0 for r in fly_ranges]   # yd -> ft
        ti = 0
        # previous-step state, for interpolating exactly to each target
        # range (muzzle = origin at rest-time 0)
        x0 = y0 = z0 = t0 = 0.0
        while ti < len(targets) and t < 12.0:
            v = math.sqrt(vx * vx + vy * vy)
            mach = v / speed_sound
            cd = _interp_cd(mach, _dm_mach, _dm_cd)
            # E = a_drag / V = _RETARD_K * sigma * Cd(M) * V / BC  (1/s)
            decel = _RETARD_K * sigma * cd * v / g7_bc
            ax = -decel * vx
            ay = -decel * vy - _G
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt
            if want_wind:
                # Full point-mass crosswind: drag acts on the air-
                # relative cross velocity (vz - cross). The bullet starts
                # at vz=0 and is dragged toward wind speed; the integral
                # of the lag IS the drift. Same scalar decel as the in-
                # plane axes (the ~15 fps cross component is negligible
                # to Mach/drag). Reduces to the textbook lag rule
                # cross*(t - x/V0) at first order but captures the
                # long-range curvature that the lag rule under-predicts.
                az = -decel * (vz - cross)
                vz += az * dt
                z += vz * dt
            # Record each crossed target by LINEAR-INTERPOLATING the
            # just-stepped segment to the exact target range, rather than
            # snapping to the first step past it. The snap added a
            # sub-yard, dt-dependent overshoot bias (~0.04 MOA at
            # dt=2e-3); interpolation makes the result effectively
            # dt-independent down to true integration error.
            while ti < len(targets) and x >= targets[ti]:
                tx = targets[ti]
                f = (tx - x0) / (x - x0) if x != x0 else 0.0
                out[fly_ranges[ti]] = (y0 + f * (y - y0),
                                       z0 + f * (z - z0),
                                       t0 + f * (t - t0))
                ti += 1
            x0, y0, z0, t0 = x, y, z, t
        return out

    # Fire ALONG THE BORE (launch angle 0) and re-zero the sight line
    # analytically. This is the standard exterior-ballistics method (and
    # exactly how a professional solver's level-scope output is zeroed):
    #
    #   * The scope sits sight_height ABOVE the bore. With the scope
    #     level, the line of sight is the horizontal line at +sh_ft;
    #     the bullet's drop below that level LoS is  dLOS(x) = y(x) - sh.
    #   * Zeroing at range Z dials the scope so the (straight) sight
    #     line passes through the bullet at Z. Because the sight line is
    #     straight, the come-up to dial at range R is simply the level-
    #     scope drop with the linear sight-line rotation removed:
    #         comeup_in(R) = -[ dLOS(R) - dLOS(Z) * (R / Z) ] * 12
    #     which is identically 0 at R=Z.
    #
    # The previous code instead bisected a launch angle to put the
    # bullet sight_height BELOW the bore at the zero and measured drop
    # from a flat line at -sh_ft. That mis-modelled the sight geometry
    # and inflated come-up by ~0.5-0.9 mil (load-independent); gate-1
    # validation vs JBM caught it. The come-up is differential, so the
    # actual bore launch angle cancels and firing flat is exact.
    sh_ft = sight_height_in / 12.0
    flight = _fly(0.0, want_wind=True)
    y_zero, _, _ = flight[zint]
    dlos_zero_ft = y_zero - sh_ft               # level-scope drop at zero
    result = {}
    for r in ranges_yd:
        r = int(r)
        if r not in flight:
            continue
        y, z, t = flight[r]
        rng_in = r * 36.0
        dlos_r_ft = y - sh_ft                   # level-scope drop at R
        # remove the straight sight-line rotation that zeroes at zero_yd
        corr_ft = dlos_r_ft - dlos_zero_ft * (r / float(zint))
        come_up_in = -corr_ft * 12.0            # +ve = dial UP
        drop_below_los_in = come_up_in
        elev_moa = (drop_below_los_in / rng_in) * (180.0 / math.pi) * 60.0
        elev_mil = (drop_below_los_in / rng_in) * 1000.0
        wind_in = z * 12.0
        wind_moa = (wind_in / rng_in) * (180.0 / math.pi) * 60.0
        wind_mil = (wind_in / rng_in) * 1000.0
        result[r] = {
            "drop_in": round(drop_below_los_in, 2),
            "elev_moa": round(elev_moa, 2),
            "elev_mil": round(elev_mil, 2),
            "wind_in": round(wind_in, 2),
            "wind_moa": round(wind_moa, 2),
            "wind_mil": round(wind_mil, 2),
            "tof_s": round(t, 3),
        }
    return result
