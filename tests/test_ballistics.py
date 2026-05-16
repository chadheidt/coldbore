"""Validation harness for the zero-dependency G7 point-mass solver
(app/ballistics.py).

This is the strengthened replacement for the weak 2026-05-15 sanity test
that caught the ~7-orders-of-magnitude broken-draft bug.

TWO tiers of checks:

  1. HARD PHYSICAL INVARIANTS — must hold for ANY correct point-mass
     G7 solver regardless of atmosphere/zero conventions: finite
     outputs, ~0 come-up at the zero range, monotonically increasing
     come-up past the zero, plausible & increasing time-of-flight,
     crosswind drift that grows with range. A solver that fails these
     is broken (as the draft was).

  2. PUBLISHED-REFERENCE BALLPARK — a well-known factory load
     (Hornady 6.5 Creedmoor 140gr ELD-M) checked against widely
     published come-up figures, with INTENTIONALLY WIDE tolerance
     bands.

⚠️ The tier-2 reference numbers are from general ballistics knowledge,
NOT an authoritative live query of a professional solver. Passing tier 2
means the math is in the right regime — it is NECESSARY BUT NOT
SUFFICIENT to ship. Ship-gate #1 (validate vs a LIVE Hornady 4DOF /
GeoBallistics / Applied Ballistics run on the reference loads, with
Chad's review) is the authoritative gate and is deliberately NOT
automated here. See app/ballistics.py module docstring.
"""

import math

import ballistics


# --------------------------------------------------------------------------
# air_density_ratio
# --------------------------------------------------------------------------
def test_air_density_ratio_icao_standard_is_unity():
    # At ICAO standard (59F, 29.92 inHg, sea level, the function's own
    # default humidity) sigma should be essentially 1.0.
    sigma = ballistics.air_density_ratio(temp_f=59.0, pressure_inhg=29.92,
                                         altitude_ft=0.0, humidity_pct=0.0)
    assert abs(sigma - 1.0) < 1e-3


def test_air_density_ratio_altitude_thins_air():
    sea = ballistics.air_density_ratio(altitude_ft=0.0)
    high = ballistics.air_density_ratio(altitude_ft=6000.0)
    assert high < sea
    # ~6000 ft should be roughly 0.80-0.86 of sea-level density.
    assert 0.78 < high < 0.88


def test_air_density_ratio_heat_thins_air():
    cold = ballistics.air_density_ratio(temp_f=20.0)
    hot = ballistics.air_density_ratio(temp_f=100.0)
    assert hot < cold


# --------------------------------------------------------------------------
# G7 drag-table interpolation
# --------------------------------------------------------------------------
def test_g7_cd_clamps_and_interpolates():
    # clamps below/above the table
    assert ballistics._g7_cd(-1.0) == ballistics._G7_CD[0]
    assert ballistics._g7_cd(99.0) == ballistics._G7_CD[-1]
    # exact node returns that node
    assert abs(ballistics._g7_cd(1.00) - 0.3884) < 1e-9
    # midpoint between two nodes is between their Cds
    lo, hi = ballistics._g7_cd(2.00), ballistics._g7_cd(2.50)
    mid = ballistics._g7_cd(2.25)
    assert min(lo, hi) <= mid <= max(lo, hi)


# --------------------------------------------------------------------------
# Reference load used for both tiers
#   Hornady 6.5 Creedmoor 140gr ELD-M factory (24" bbl):
#   MV 2710 fps, G7 BC 0.315, 100yd zero, 1.75" sight height,
#   ICAO standard atmosphere.
# --------------------------------------------------------------------------
REF = dict(
    muzzle_velocity_fps=2710.0,
    g7_bc=0.315,
    zero_yd=100.0,
    sight_height_in=1.75,
    ranges_yd=[100, 200, 300, 400, 500, 600, 800, 1000],
    temp_f=59.0, pressure_inhg=29.92, altitude_ft=0.0, humidity_pct=0.0,
    wind_mph=10.0, wind_angle_clock=3.0,
)


def _solve():
    return ballistics.solve_trajectory(**REF)


# --------------------------------------------------------------------------
# Tier 1 — hard physical invariants
# --------------------------------------------------------------------------
def test_outputs_are_finite_and_complete():
    sol = _solve()
    for r in REF["ranges_yd"]:
        assert r in sol, f"no solution at {r} yd"
        for k, v in sol[r].items():
            assert math.isfinite(v), f"{k} at {r} yd is not finite: {v}"


def test_comeup_is_zero_at_zero_range():
    sol = _solve()
    # At the 100 yd zero the sight come-up should be ~0 (within a small
    # fraction of an MOA — the bisection zeroing tolerance).
    assert abs(sol[100]["elev_moa"]) < 0.5


def test_comeup_increases_monotonically_past_zero():
    sol = _solve()
    past = [r for r in REF["ranges_yd"] if r > 100]
    moa = [sol[r]["elev_moa"] for r in past]
    assert all(b > a for a, b in zip(moa, moa[1:])), f"not monotonic: {moa}"
    # come-up must be positive (you dial UP for drop past the zero)
    assert all(m > 0 for m in moa)


def test_time_of_flight_is_plausible_and_increasing():
    sol = _solve()
    tofs = [sol[r]["tof_s"] for r in REF["ranges_yd"]]
    assert all(b > a for a, b in zip(tofs, tofs[1:])), f"TOF not increasing: {tofs}"
    # A ~2710 fps 6.5 CM 140 reaches 1000 yd in roughly 1.4-1.7 s.
    # The broken draft produced ~0.001 s — this band would catch it.
    assert 1.2 < sol[1000]["tof_s"] < 2.0, sol[1000]["tof_s"]
    # 100 yd is reached in well under a quarter second.
    assert 0.05 < sol[100]["tof_s"] < 0.25, sol[100]["tof_s"]


def test_crosswind_drift_grows_with_range():
    sol = _solve()
    drift = [abs(sol[r]["wind_in"]) for r in REF["ranges_yd"]]
    assert all(b >= a for a, b in zip(drift, drift[1:])), f"drift not growing: {drift}"
    assert sol[1000]["wind_in"] != 0.0  # a 10 mph 3-o'clock wind drifts the bullet


# --------------------------------------------------------------------------
# Tier 2 — published-reference ballpark (intentionally wide bands)
# --------------------------------------------------------------------------
def test_ballpark_matches_published_640_eldm_dope():
    """Hornady 6.5 CM 140 ELD-M, 2710 fps, G7 0.315, 100yd zero.
    Widely published come-up (approx, varies by atmosphere/zero):
        300 yd  ~  4 - 6   MOA
        500 yd  ~ 11 - 15  MOA
       1000 yd  ~ 29 - 37  MOA  (~8.6 - 10.8 mil)
    Bands are deliberately loose: this tier proves 'right regime, not
    broken', NOT precision. Precision validation is ship-gate #1
    (live professional solver + Chad review), intentionally not here.
    """
    sol = _solve()
    moa_300 = sol[300]["elev_moa"]
    moa_500 = sol[500]["elev_moa"]
    moa_1000 = sol[1000]["elev_moa"]
    mil_1000 = sol[1000]["elev_mil"]

    assert 3.0 <= moa_300 <= 7.0, f"300yd come-up {moa_300} MOA out of ballpark"
    assert 9.0 <= moa_500 <= 17.0, f"500yd come-up {moa_500} MOA out of ballpark"
    assert 27.0 <= moa_1000 <= 40.0, f"1000yd come-up {moa_1000} MOA out of ballpark"
    # MOA->Mil internal consistency (1 mil = 3.438 MOA)
    assert abs(mil_1000 - moa_1000 / 3.438) < 0.2, (mil_1000, moa_1000)
