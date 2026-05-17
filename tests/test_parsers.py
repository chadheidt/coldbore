"""Tests for the parser registry and the individual chronograph/group parsers."""

import os
import tempfile
import textwrap
from pathlib import Path

import pytest

from parsers import (
    ALL_PARSERS,
    detect_parser,
    parser_by_key,
    chronograph_parsers,
    group_parsers,
)


GARMIN_SAMPLE_CSV = textwrap.dedent('''\
    "P1 45.5 H4350"
    #,SPEED (FPS),Δ AVG (FPS),KE (FT-LB),POWER FACTOR (KGR⋅FT/S),TIME,CLEAN BORE,COLD BORE,SHOT NOTES
    1, 3013.6, 0.8, 2681.6, 400.8, 9:36:59 AM, , ,
    2, 3018.4, 5.5, 2690.1, 401.4, 9:38:43 AM, , ,
    3, 3012.9, 0.1, 2680.3, 400.7, 9:39:54 AM, , ,
    AVERAGE SPEED, 3014.96
    STD DEV, 2.97
    SPREAD, 5.5
    PROJECTILE WEIGHT(GRAINS), 140
    DATE, "March 1, 2026 9:36 AM"
    SESSION NOTE, "test session"
''')


BALLISTICX_SAMPLE_CSV = textwrap.dedent('''\
    Label,Distance,Caliber,CreatedAt,GroupMeasureType,GroupSizeDisplay,OverallWidthDisplay,OverallHeightDisplay,ATZDisplay,ElevationDisplay,WindageDisplay,MeanRadiusDisplay,CEPDisplay,SDRadialDisplay,SDVerticalDisplay,SDHorizontalDisplay
    ,100,.284 / 7mm,"May 6, 2026 at 12:35 PM",,"0.358"" (0.342 MOA)","0.357""","0.255""",D: 0.96 L: 0.52,0.14,0.18,"0.162"" (0.155 MOA)","0.178"" (0.170 MOA)","0.117"" (0.111 MOA)","0.094"" (0.090 MOA)","0.136"" (0.130 MOA)"
''')


# ============================================================
# Registry shape
# ============================================================

class TestRegistry:
    def test_at_least_two_parsers_registered(self):
        assert len(ALL_PARSERS) >= 2

    def test_parser_modules_export_required_attributes(self):
        for parser in ALL_PARSERS:
            assert hasattr(parser, "KIND"), f"{parser.__name__} missing KIND"
            assert parser.KIND in ("chronograph", "group"), \
                f"{parser.__name__} KIND must be 'chronograph' or 'group'"
            assert hasattr(parser, "NAME"), f"{parser.__name__} missing NAME"
            assert hasattr(parser, "KEY"), f"{parser.__name__} missing KEY"
            assert hasattr(parser, "IMPORT_FOLDER"), \
                f"{parser.__name__} missing IMPORT_FOLDER"
            assert callable(getattr(parser, "detect", None)), \
                f"{parser.__name__} missing callable detect()"
            assert callable(getattr(parser, "parse", None)), \
                f"{parser.__name__} missing callable parse()"

    def test_keys_are_unique(self):
        keys = [p.KEY for p in ALL_PARSERS]
        assert len(set(keys)) == len(keys), f"Duplicate KEY in registry: {keys}"

    def test_parser_by_key_lookup(self):
        for parser in ALL_PARSERS:
            assert parser_by_key(parser.KEY) is parser

    def test_parser_by_key_unknown_returns_none(self):
        assert parser_by_key("nonexistent_key") is None

    def test_chronograph_parsers_all_have_correct_kind(self):
        for p in chronograph_parsers():
            assert p.KIND == "chronograph"

    def test_group_parsers_all_have_correct_kind(self):
        for p in group_parsers():
            assert p.KIND == "group"


# ============================================================
# Auto-detection
# ============================================================

@pytest.fixture
def garmin_csv_file(tmp_path):
    p = tmp_path / "P1_45_5_H4350.csv"
    p.write_text(GARMIN_SAMPLE_CSV, encoding="utf-8")
    return p


@pytest.fixture
def ballisticx_csv_file(tmp_path):
    p = tmp_path / "P1 45.5 H4350.csv"
    p.write_text(BALLISTICX_SAMPLE_CSV, encoding="utf-8")
    return p


class TestDetectParser:
    def test_detects_garmin(self, garmin_csv_file):
        parser = detect_parser(str(garmin_csv_file))
        assert parser is not None
        assert parser.KEY == "garmin"

    def test_detects_ballisticx(self, ballisticx_csv_file):
        parser = detect_parser(str(ballisticx_csv_file))
        assert parser is not None
        assert parser.KEY == "ballisticx"

    def test_unknown_file_returns_none(self, tmp_path):
        p = tmp_path / "garbage.csv"
        p.write_text("hello,world\n1,2\n", encoding="utf-8")
        assert detect_parser(str(p)) is None

    def test_nonexistent_file_returns_none(self, tmp_path):
        # detect functions catch OSError internally
        assert detect_parser(str(tmp_path / "nope.csv")) is None


# ============================================================
# Garmin Xero parser
# ============================================================

class TestGarminParser:
    def test_parses_label_from_first_line(self, garmin_csv_file):
        from parsers import garmin_xero
        result = garmin_xero.parse(str(garmin_csv_file))
        assert result["Tag"] == "P1"
        assert result["ChargeOrJump"] == 45.5
        assert result["Powder"] == "H4350"

    def test_parses_shot_velocities(self, garmin_csv_file):
        from parsers import garmin_xero
        result = garmin_xero.parse(str(garmin_csv_file))
        assert result["Shots"] == [3013.6, 3018.4, 3012.9]

    def test_parses_stats(self, garmin_csv_file):
        from parsers import garmin_xero
        result = garmin_xero.parse(str(garmin_csv_file))
        assert result["AvgVel"] == 3014.96
        assert result["SD"] == 2.97
        assert result["ES"] == 5.5
        assert result["BulletWt"] == 140

    def test_record_has_kind_and_source(self, garmin_csv_file):
        from parsers import garmin_xero
        result = garmin_xero.parse(str(garmin_csv_file))
        assert result["kind"] == "chronograph"
        assert result["Source"] == "garmin"


# ============================================================
# BallisticX parser
# ============================================================

class TestBallisticXParser:
    def test_uses_filename_as_label(self, ballisticx_csv_file):
        from parsers import ballisticx
        result = ballisticx.parse(str(ballisticx_csv_file))
        assert len(result) == 1
        assert result[0]["Tag"] == "P1"
        assert result[0]["ChargeOrJump"] == 45.5
        assert result[0]["Powder"] == "H4350"

    def test_parses_group_metrics(self, ballisticx_csv_file):
        from parsers import ballisticx
        result = ballisticx.parse(str(ballisticx_csv_file))
        rec = result[0]
        assert rec["GroupIn"] == 0.358
        assert rec["MRIn"] == 0.162
        assert rec["HeightIn"] == 0.255

    def test_record_has_kind_and_source(self, ballisticx_csv_file):
        from parsers import ballisticx
        result = ballisticx.parse(str(ballisticx_csv_file))
        assert result[0]["kind"] == "group"
        assert result[0]["Source"] == "ballisticx"

    def test_falls_back_to_label_column_when_filename_unparseable(self, tmp_path):
        # Filename "history_items.csv" doesn't have a numeric charge — should
        # fall back to the in-CSV Label column
        p = tmp_path / "history_items.csv"
        body = (
            "Label,Distance,Caliber,CreatedAt,GroupSizeDisplay,MeanRadiusDisplay,"
            "OverallWidthDisplay,OverallHeightDisplay,CEPDisplay,SDRadialDisplay,"
            "SDVerticalDisplay,SDHorizontalDisplay,ElevationDisplay,WindageDisplay\n"
            "P3 46.0 RL26,100,.284 / 7mm,\"May 6 2026\","
            "\"0.5\"\",\"0.2\"\",\"0.4\"\",\"0.3\"\",\"0.25\"\",\"0.15\"\",\"0.12\"\",\"0.10\"\","
            "0,0\n"
        )
        p.write_text(body, encoding="utf-8")
        from parsers import ballisticx
        result = ballisticx.parse(str(p))
        assert len(result) == 1
        assert result[0]["Tag"] == "P3"
        assert result[0]["ChargeOrJump"] == 46.0
        assert result[0]["Powder"] == "RL26"


# ============================================================
# New parsers (2026-05-17): LabRadar, OnTarget, ShotMarker, SMT.
# Fixtures below are SYNTHETIC, hand-built from the publicly documented
# formats — NOT captured from real devices. Each parser carries
# NEEDS_REAL_SAMPLE_VALIDATION = True until checked vs a genuine export.
# ============================================================

ONTARGET_SAMPLE_CSV = textwrap.dedent('''\
    Project Title,Group,Ammunition,Distance,Aim X,Aim Y,Center X,Center Y,Point X,Point Y,Velocity
    Test,G1,6.5 Creedmoor,100,0.5,0.5,0.5,0.5,0,0,2805
    Test,G1,6.5 Creedmoor,100,0.5,0.5,0.5,0.5,1,0,2810
    Test,G1,6.5 Creedmoor,100,0.5,0.5,0.5,0.5,0,1,2798
    Test,G1,6.5 Creedmoor,100,0.5,0.5,0.5,0.5,1,1,2803
''')

LABRADAR_SAMPLE_CSV = textwrap.dedent('''\
    LabRadar
    Series No;SR0001
    Average;2805
    Std Dev;7.2
    Spread;19
    Shot ID;Velocity
    1;2805
    2;2812
    3;2798
''')

SHOTMARKER_SAMPLE_CSV = textwrap.dedent('''\
    x (in),y (in),v (fps),yaw,pitch,distance,string
    0,0,2805,0.1,0.2,100,S1
    1,0,2810,0.1,0.2,100,S1
    0,1,2798,0.1,0.2,100,S1
    1,1,2803,0.1,0.2,100,S1
''')

SMT_SAMPLE_CSV = textwrap.dedent('''\
    Silver Mountain Targets export
    shot,x,y,v,distance,string
    1,0,0,2805,100,A
    2,1,0,2810,100,A
    3,0,1,2798,100,A
    4,1,1,2803,100,A
''')

_ROOT2 = 2 ** 0.5
_HALF_ROOT = 0.5 ** 0.5


class TestGroupGeometry:
    def test_unit_square_known_values(self):
        from parsers._common import group_stats_from_points
        s = group_stats_from_points(
            [(0, 0), (2, 0), (0, 2), (2, 2)], aim=(1, 1))
        assert abs(s["GroupIn"] - (8 ** 0.5)) < 1e-9   # diagonal
        assert s["WidthIn"] == 2 and s["HeightIn"] == 2
        assert abs(s["MRIn"] - _ROOT2) < 1e-9          # each pt sqrt(2) from center
        assert abs(s["ElevOffsetIn"]) < 1e-9           # centroid == aim
        assert abs(s["WindOffsetIn"]) < 1e-9

    def test_single_point_is_zero_spreads_not_error(self):
        from parsers._common import group_stats_from_points
        s = group_stats_from_points([(3.0, 4.0)])
        assert s["GroupIn"] == 0.0 and s["WidthIn"] == 0.0
        assert s["MRIn"] == 0.0

    def test_empty_returns_none(self):
        from parsers._common import group_stats_from_points
        s = group_stats_from_points([])
        assert s["GroupIn"] is None


@pytest.fixture
def ontarget_csv_file(tmp_path):
    p = tmp_path / "S2 0.040 H4350.csv"
    p.write_text(ONTARGET_SAMPLE_CSV, encoding="utf-8")
    return p


@pytest.fixture
def labradar_csv_file(tmp_path):
    p = tmp_path / "P4 41.5 H4350.csv"
    p.write_text(LABRADAR_SAMPLE_CSV, encoding="utf-8")
    return p


@pytest.fixture
def shotmarker_csv_file(tmp_path):
    p = tmp_path / "shotmarker_S1.csv"
    p.write_text(SHOTMARKER_SAMPLE_CSV, encoding="utf-8")
    return p


@pytest.fixture
def smt_csv_file(tmp_path):
    p = tmp_path / "smt_A.csv"
    p.write_text(SMT_SAMPLE_CSV, encoding="utf-8")
    return p


class TestOnTargetParser:
    def test_detects(self, ontarget_csv_file):
        assert detect_parser(str(ontarget_csv_file)).KEY == "ontarget"

    def test_parses_and_computes_group(self, ontarget_csv_file):
        from parsers import ontarget
        recs = ontarget.parse(str(ontarget_csv_file))
        assert len(recs) == 1
        r = recs[0]
        assert r["kind"] == "group" and r["Source"] == "ontarget"
        assert r["Tag"] == "S2" and r["ChargeOrJump"] == 0.04
        assert r["Powder"] == "H4350"
        assert r["Distance"] == 100
        assert abs(r["GroupIn"] - _ROOT2) < 1e-9
        assert r["WidthIn"] == 1 and r["HeightIn"] == 1
        assert abs(r["MRIn"] - _HALF_ROOT) < 1e-9
        assert abs(r["ElevOffsetIn"]) < 1e-9


class TestLabRadarParser:
    def test_detects(self, labradar_csv_file):
        assert detect_parser(str(labradar_csv_file)).KEY == "labradar"

    def test_parses_velocities_and_stats(self, labradar_csv_file):
        from parsers import labradar
        r = labradar.parse(str(labradar_csv_file))
        assert r["kind"] == "chronograph" and r["Source"] == "labradar"
        assert r["Shots"] == [2805.0, 2812.0, 2798.0]
        assert r["AvgVel"] == 2805 and r["SD"] == 7.2 and r["ES"] == 19


class TestShotMarkerParser:
    def test_detects(self, shotmarker_csv_file):
        assert detect_parser(str(shotmarker_csv_file)).KEY == "shotmarker"

    def test_parses_and_computes_group(self, shotmarker_csv_file):
        from parsers import shotmarker
        recs = shotmarker.parse(str(shotmarker_csv_file))
        assert len(recs) == 1
        r = recs[0]
        assert r["kind"] == "group" and r["Source"] == "shotmarker"
        assert r["Distance"] == 100
        assert abs(r["GroupIn"] - _ROOT2) < 1e-9


class TestSMTParser:
    def test_detects(self, smt_csv_file):
        assert detect_parser(str(smt_csv_file)).KEY == "smt"

    def test_parses_and_computes_group(self, smt_csv_file):
        from parsers import smt
        recs = smt.parse(str(smt_csv_file))
        assert len(recs) == 1
        r = recs[0]
        assert r["kind"] == "group" and r["Source"] == "smt"
        assert abs(r["GroupIn"] - _ROOT2) < 1e-9


class TestNoCrossClaim:
    """A parser must never claim another device's file (silent misroute is
    worse than no parser — the build guardrail)."""

    def test_garmin_still_wins_its_file(self, garmin_csv_file):
        assert detect_parser(str(garmin_csv_file)).KEY == "garmin"

    def test_ballisticx_still_wins_its_file(self, ballisticx_csv_file):
        assert detect_parser(str(ballisticx_csv_file)).KEY == "ballisticx"

    def test_new_parsers_dont_claim_garmin(self, garmin_csv_file):
        from parsers import labradar, ontarget, shotmarker, smt
        for p in (labradar, ontarget, shotmarker, smt):
            assert p.detect(str(garmin_csv_file)) is False

    def test_new_parsers_dont_claim_ballisticx(self, ballisticx_csv_file):
        from parsers import labradar, ontarget, shotmarker, smt
        for p in (labradar, ontarget, shotmarker, smt):
            assert p.detect(str(ballisticx_csv_file)) is False

    def test_smt_does_not_claim_shotmarker(self, shotmarker_csv_file):
        from parsers import smt
        assert smt.detect(str(shotmarker_csv_file)) is False


class TestValidationFlag:
    def test_unverified_parsers_flagged(self):
        flagged = {
            p.KEY for p in ALL_PARSERS
            if getattr(p, "NEEDS_REAL_SAMPLE_VALIDATION", False)
        }
        assert {"labradar", "ontarget", "shotmarker", "smt"} <= flagged
