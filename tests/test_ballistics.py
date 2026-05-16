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

import pytest

import ballistics
import component_data as cd


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
    # exact node returns that node — value is from the AUTHORITATIVE
    # standard G7 (McCoy) drag function (JBM mcg7.txt): Cd(M1.0)=0.3803.
    # (The prior 0.3884 was a wrong hand-truncated-table value that
    # gate-1 validation against JBM exposed.)
    assert abs(ballistics._g7_cd(1.00) - 0.3803) < 1e-9
    assert abs(ballistics._g7_cd(2.00) - 0.2980) < 1e-9
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


# --------------------------------------------------------------------------
# Tier 1b — numerical-hardening regression guards (2026-05-16 audit)
# These lock in the autonomous numerics work so a future change can't
# silently regress it. They are pure numerics (no external reference).
# --------------------------------------------------------------------------
def test_zero_comeup_is_tight_not_just_under_half_moa():
    """The bisection zeroing is actually tight (~0.0 MOA at the zero),
    far better than the loose <0.5 ballpark guard above. Lock it in."""
    sol = _solve()
    assert abs(sol[100]["elev_moa"]) < 0.05, sol[100]["elev_moa"]


def test_result_is_dt_independent_after_target_interpolation():
    """The target-range interpolation fix makes the come-up effectively
    dt-independent down to true integration error: the default dt and a
    4x-finer dt must agree well inside the gate tolerance (0.5 MOA)."""
    coarse = ballistics.solve_trajectory(dt=0.0005, **REF)
    fine = ballistics.solve_trajectory(dt=0.000125, **REF)
    for r in (300, 500, 1000):
        d_moa = abs(coarse[r]["elev_moa"] - fine[r]["elev_moa"])
        assert d_moa < 0.05, f"{r}yd come-up dt-sensitive: {d_moa} MOA"
        d_mil = abs(coarse[r]["elev_mil"] - fine[r]["elev_mil"])
        assert d_mil < 0.02, f"{r}yd come-up dt-sensitive: {d_mil} mil"


def test_integrated_crosswind_matches_textbook_lag_rule():
    """The full point-mass crosswind integration must reduce to the
    closed-form lag rule  drift = Wcross*(TOF - range/MV)  to within a
    few percent through 1000 yd (it captures higher-order curvature the
    lag rule misses, but must not diverge from it in this regime)."""
    sol = _solve()
    cross_fps = REF["wind_mph"] * 1.46667  # 3-o'clock = full value
    for r in (300, 500, 1000):
        tof = sol[r]["tof_s"]
        lag_in = cross_fps * (tof - (r * 3.0) / REF["muzzle_velocity_fps"]) \
            * 12.0
        got_in = sol[r]["wind_in"]
        assert abs(got_in - lag_in) < max(0.5, 0.03 * abs(lag_in)), \
            f"{r}yd wind {got_in}\" vs lag-rule {lag_in:.2f}\""


# --------------------------------------------------------------------------
# BC-database infrastructure (ship-gate (2) plumbing; NO real BC values)
# --------------------------------------------------------------------------
def test_bc_database_version_is_zero_no_authoritative_data_yet():
    """0 means no authoritative manufacturer BCs are bundled. If real
    curated data is ever added it MUST bump this AND update this test —
    a deliberate tripwire against fabricated BCs slipping in silently."""
    v = cd.bc_database_version()
    assert isinstance(v, int) and v == 0, v


def test_shipped_bullet_seed_carries_no_fabricated_bc():
    """Every bundled seed bullet must currently expose g7=None,g1=None.
    Guards the ship-gate-(2) rule: do NOT fabricate BC values."""
    for mfr in cd.bullet_manufacturers():
        for e in cd.bullets_for(mfr):
            bc = cd.bullet_bc(e)
            assert bc == {"g7": None, "g1": None}, (mfr, e, bc)


def test_bullet_bc_reads_native_model_fields_when_present():
    assert cd.bullet_bc({"name": "X", "g7": "0.310"}) == \
        {"g7": 0.310, "g1": None}
    assert cd.bullet_bc({"name": "X", "g1": 0.62}) == \
        {"g7": None, "g1": 0.62}
    assert cd.bullet_bc({"name": "X"}) == {"g7": None, "g1": None}
    assert cd.bullet_bc("not a dict") == {"g7": None, "g1": None}


def test_resolve_g7_bc_manual_override_wins_over_db():
    assert ballistics.resolve_g7_bc(manual_bc=0.290, db_g7=0.315) == 0.290


def test_resolve_g7_bc_uses_db_g7_when_no_override():
    assert ballistics.resolve_g7_bc(db_g7=0.315) == 0.315


def test_resolve_g7_bc_refuses_to_convert_g1():
    # manual G1 -> refuse (no silent conversion)
    with pytest.raises(ballistics.BcModelUnsupported):
        ballistics.resolve_g7_bc(manual_bc=0.62, manual_model="G1")
    # only G1 curated -> refuse
    with pytest.raises(ballistics.BcModelUnsupported):
        ballistics.resolve_g7_bc(db_g1=0.62)


def test_resolve_g7_bc_raises_when_nothing_available():
    with pytest.raises(ballistics.BcUnavailable):
        ballistics.resolve_g7_bc()


# --------------------------------------------------------------------------
# Tier 3 — AUTHORITATIVE regression vs JBM Ballistics
#
# tests/jbm_reference.json was captured 2026-05-16 by driving JBM's
# jbmtraj-5.1 (THE standard free G7 point-mass solver) for 4 reference
# loads. JBM outputs a level-scope trajectory (Elevation 0.00 MOA); a
# 100 yd zero is applied analytically by removing the straight sight-
# line rotation (corr = drop - drop[100]*R/100), then converting to
# mil. Loadscope must match JBM within the project's stated gate-1
# tolerance (0.1 mil at 1000 yd) for elevation AND wind, across every
# load and range. This caught two real bugs (a hand-truncated G7 table
# 5-15% low in the supersonic regime, and a mis-modelled sight
# geometry); it is the strong replacement for the old training-
# knowledge ballpark band.
# --------------------------------------------------------------------------
import json as _json   # noqa: E402
import os as _os       # noqa: E402

_JBM = _os.path.join(_os.path.dirname(__file__), "jbm_reference.json")


def test_matches_jbm_reference_within_gate1_tolerance():
    ref = _json.load(open(_JBM))
    worst = 0.0
    worst_where = None
    for name, load in ref.items():
        if name.startswith("_"):
            continue
        rows = load["rows"]
        d100 = rows["100"]["drop_in"]
        sol = ballistics.solve_trajectory(
            muzzle_velocity_fps=float(load["mv"]), g7_bc=load["g7_bc"],
            zero_yd=100.0, sight_height_in=1.75,
            ranges_yd=list(range(100, 1100, 100)),
            temp_f=59.0, pressure_inhg=29.92, altitude_ft=0.0,
            humidity_pct=0.0, wind_mph=10.0, wind_angle_clock=3.0)
        for R in (200, 300, 400, 500, 600, 700, 800, 900, 1000):
            jr = rows[str(R)]
            rin = R * 36.0
            jbm_elev = -(jr["drop_in"] - d100 * (R / 100.0)) / rin * 1000.0
            jbm_wind = jr["wind_in"] / rin * 1000.0
            de = abs(sol[R]["elev_mil"] - jbm_elev)
            dw = abs(sol[R]["wind_mil"] - jbm_wind)
            if max(de, dw) > worst:
                worst = max(de, dw)
                worst_where = (name, R, round(de, 3), round(dw, 3))
            assert de < 0.10, f"{name} {R}yd elev off {de:.3f} mil vs JBM"
            assert dw < 0.10, f"{name} {R}yd wind off {dw:.3f} mil vs JBM"
    # tightest single point is the .308 going transonic at 1000 yd;
    # everything supersonic is ~0.00-0.03 mil. Guard the headroom.
    assert worst < 0.08, f"worst delta {worst:.3f} mil at {worst_where}"
