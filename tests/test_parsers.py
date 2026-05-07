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
