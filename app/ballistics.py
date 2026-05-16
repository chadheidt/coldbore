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
# Published G7 standard-projectile drag coefficients. Source: the
# standard G7 drag function (Ballistic Resource Library / Litz tables) —
# a fixed published standard, not estimated. Linear-interpolated.
_G7_MACH = [
    0.00, 0.50, 0.70, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20,
    1.30, 1.40, 1.50, 1.75, 2.00, 2.25, 2.50, 3.00, 3.50, 4.00,
]
_G7_CD = [
    0.1198, 0.1197, 0.1196, 0.1393, 0.1722, 0.2999, 0.3884, 0.4055,
    0.4084, 0.3923, 0.3678, 0.3454, 0.3260, 0.2887, 0.2604, 0.2380,
    0.2200, 0.1925, 0.1714, 0.1551,
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


def _g7_cd(mach):
    if mach <= _G7_MACH[0]:
        return _G7_CD[0]
    if mach >= _G7_MACH[-1]:
        return _G7_CD[-1]
    for i in range(1, len(_G7_MACH)):
        if mach <= _G7_MACH[i]:
            m0, m1 = _G7_MACH[i - 1], _G7_MACH[i]
            c0, c1 = _G7_CD[i - 1], _G7_CD[i]
            return c0 + (c1 - c0) * (mach - m0) / (m1 - m0)
    return _G7_CD[-1]


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
# The solver is G7-only (it carries the standard G7 drag curve). Per the
# project rule we NEVER convert a G1 BC to G7 (force-conversion injects
# error and burns the customer). The resolver therefore REFUSES loudly
# rather than guessing — the caller/UI decides what to do.

class BcUnavailable(Exception):
    """No usable BC: none supplied and none curated for this bullet.
    The UI should prompt the shooter to enter a measured/published BC."""


class BcModelUnsupported(Exception):
    """A G1-native BC was the only thing available. The G7 solver will
    NOT force-convert it. Resolved at ship-gate (2) (G1 drag-curve
    support / authoritative G7 values), not by silent conversion."""


def resolve_g7_bc(manual_bc=None, manual_model="G7",
                   db_g7=None, db_g1=None):
    """Decide which G7 BC feeds solve_trajectory.

    Precedence: an explicit user override wins over the curated DB.
      * manual_bc + manual_model "G7"  -> use it
      * manual_bc + manual_model "G1"  -> BcModelUnsupported (no convert)
      * else curated db_g7             -> use it
      * else only db_g1 curated        -> BcModelUnsupported
      * else                           -> BcUnavailable

    Returns a float G7 BC. Never fabricates or converts.
    """
    if manual_bc is not None:
        model = (manual_model or "G7").strip().upper()
        if model == "G7":
            return float(manual_bc)
        raise BcModelUnsupported(
            f"Manual BC given as {model}; the solver is G7-only and will "
            f"not convert. Enter a G7 BC or wait for {model} support.")
    if db_g7 is not None:
        return float(db_g7)
    if db_g1 is not None:
        raise BcModelUnsupported(
            "Only a G1 BC is curated for this bullet; the G7 solver will "
            "not convert it. Enter a G7 BC manually for now.")
    raise BcUnavailable(
        "No ballistic coefficient available for this bullet. Enter the "
        "manufacturer's published or your measured G7 BC.")


def solve_trajectory(muzzle_velocity_fps, g7_bc, zero_yd=100.0,
                     sight_height_in=1.75, ranges_yd=None,
                     temp_f=59.0, pressure_inhg=29.92, altitude_ft=0.0,
                     humidity_pct=50.0, wind_mph=10.0,
                     wind_angle_clock=3.0, dt=0.0005):
    """Return {range_yd: {'drop_in','elev_moa','elev_mil','wind_in',
    'wind_moa','wind_mil','tof_s'}}. Point-mass RK-free Euler at small
    dt; G7 drag scaled by BC; gravity; constant crosswind.

    DRAFT — see module docstring ship-gate before any reliance/ship.
    """
    if ranges_yd is None:
        ranges_yd = list(range(100, 1100, 100))
    sigma = air_density_ratio(temp_f, pressure_inhg, altitude_ft,
                              humidity_pct)
    speed_sound = _SPEED_SOUND_STD * math.sqrt(
        (temp_f + 459.67) / 518.67)
    # Standard G7-BC point-mass retardation (see _RETARD_K derivation):
    #   a_drag = _RETARD_K * sigma * Cd_std(M) * V^2 / BC
    # The integrator below works with E = a_drag / V (a per-second rate),
    # so that ax = -E*vx, ay = -E*vy reproduces the vector drag
    # deceleration opposite the velocity vector. Hence E carries ONE
    # power of v here and the second comes from the *vx / *vy below.

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
        targets = [r * 3.0 for r in ranges_yd]   # yd -> ft
        ti = 0
        # previous-step state, for interpolating exactly to each target
        # range (muzzle = origin at rest-time 0)
        x0 = y0 = z0 = t0 = 0.0
        while ti < len(targets) and t < 12.0:
            v = math.sqrt(vx * vx + vy * vy)
            mach = v / speed_sound
            cd = _g7_cd(mach)
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
                out[ranges_yd[ti]] = (y0 + f * (y - y0),
                                      z0 + f * (z - z0),
                                      t0 + f * (t - t0))
                ti += 1
            x0, y0, z0, t0 = x, y, z, t
        return out

    # Solve launch angle so the path crosses line-of-sight at zero_yd.
    # Line of sight starts sight_height below bore and is ~flat; find
    # angle by secant iteration on drop@zero.
    sh_ft = sight_height_in / 12.0
    lo, hi = -0.02, 0.06
    for _ in range(60):
        mid = (lo + hi) / 2.0
        res = _fly(mid)
        yz = res.get(int(zero_yd))
        if yz is None:
            # zero not in range list — fly explicitly to zero
            r2 = _fly(mid, False)
            yz = r2.get(int(zero_yd), (None, None, None))
        y_at_zero = yz[0]
        # want bullet path = line of sight height (-sh_ft) at zero
        if y_at_zero is None:
            break
        if y_at_zero + sh_ft > 0:
            hi = mid
        else:
            lo = mid
    launch = (lo + hi) / 2.0

    flight = _fly(launch, want_wind=True)
    result = {}
    for r in ranges_yd:
        if r not in flight:
            continue
        y, z, t = flight[r]
        # bullet position relative to line of sight (which sits sh_ft
        # below bore). Drop below LoS (inches), positive = come up.
        path_in = (y + sh_ft) * 12.0
        rng_in = r * 36.0
        drop_below_los_in = -path_in
        # angular come-up: inches at range -> MOA / Mil
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
