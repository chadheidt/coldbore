"""Zero-dependency G7 point-mass ballistic solver (DRAFT).

[[loadscope-ballistic-solver-v015]]. Predicts the Ballistics-tab DOPE
(elevation + wind per distance) from the data Loadscope already has
(muzzle velocity, zero, sight height) plus a G7 BC and atmospherics.

Path B: pure-Python, NO numpy/scipy (those aren't in the py2app bundle
and adding a sci dep is the fragility class that's bitten us). Standard
3-DOF point-mass integration against the published G7 reference drag
table scaled by the bullet's G7 BC — the same model class as Strelok /
GeoBallistics / the free Hornady & Berger web calculators.

⚠️⚠️ STATUS: BROKEN-DRAFT SCAFFOLD — DO NOT USE / DO NOT WIRE / DO NOT
SHIP. A 2026-05-15 sanity test proved the trajectory integrator's
retardation constant/formula (`K` + `decel`) is WRONG by ~7 orders of
magnitude (TOF≈0.001s @ 1000yd, absurd outputs). What IS correct and
reusable: the module shape/API, the published G7 drag table
(_G7_MACH/_G7_CD — a fixed standard, fine), and air_density_ratio()
(self-verified ≈1.000 at ICAO standard). The trajectory math needs the
CORRECT standard G7-BC point-mass retardation (per McCoy "Modern
Exterior Ballistics" / GNU Ballistics reference), implemented carefully,
then the solver-memory ship-gates: validate vs professional solvers
(Hornady 4DOF / GeoBallistics / Applied Ballistics) on the reference
loads, AND the signed-disclaimer predicted-DOPE language +
DISCLAIMER_VERSION bump. NOT autonomous-guess territory — safety
critical (wrong DOPE = blown shot / liability). Nothing imports this.

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
    # Drag constant for the G7-BC method (standard form): the bullet's
    # retardation = sigma * Cd_G7(M) * V^2 / (BC * K), K chosen so a
    # G7-BC bullet matches the reference. Standard constant:
    K = 2.08551e-04  # ft, standard G7 retardation coefficient

    def _fly(launch_angle_rad, want_wind=False):
        # state in feet; x downrange, y vertical (line of bore at 0)
        vx = muzzle_velocity_fps * math.cos(launch_angle_rad)
        vy = muzzle_velocity_fps * math.sin(launch_angle_rad)
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
        while ti < len(targets) and t < 12.0:
            v = math.sqrt(vx * vx + vy * vy)
            mach = v / speed_sound
            cd = _g7_cd(mach)
            decel = sigma * cd * v / (g7_bc * K)   # 1/s (×v below)
            ax = -decel * vx
            ay = -decel * vy - _G
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            if want_wind:
                # bullet lags the wind -> drift ≈ cross*(t - x/V0)
                z = cross * (t - x / muzzle_velocity_fps)
            t += dt
            while ti < len(targets) and x >= targets[ti]:
                out[ranges_yd[ti]] = (y, z, t)
                ti += 1
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
