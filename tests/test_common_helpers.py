"""Tests for app/parsers/_common.py — the shared label/number parsing helpers."""

from parsers._common import parse_label, extract_inches, extract_signed


# ============================================================
# parse_label — the load label convention <tag> <number> <powder>
# ============================================================

class TestParseLabel:
    def test_powder_ladder_label(self):
        assert parse_label("P1 45.5 H4350") == ("P1", 45.5, "H4350")

    def test_seating_depth_label(self):
        # "0.070" jump should parse as 0.07 grains/inches (we don't disambiguate; numeric is numeric)
        assert parse_label("S7 0.070 H4350") == ("S7", 0.07, "H4350")

    def test_confirmation_label(self):
        assert parse_label("CONFIRM-1 41.5 RL26") == ("CONFIRM-1", 41.5, "RL26")

    def test_lowercase_tag_uppercased(self):
        assert parse_label("p1 45.5 h4350") == ("P1", 45.5, "h4350")

    def test_no_powder(self):
        assert parse_label("P1 45.5") == ("P1", 45.5, "")

    def test_no_number(self):
        assert parse_label("P1") == ("P1", None, "")

    def test_empty_string(self):
        assert parse_label("") == ("", None, "")

    def test_none_returns_empty_tuple(self):
        assert parse_label(None) == ("", None, "")

    def test_extra_whitespace(self):
        # Multiple spaces between tokens shouldn't break parsing
        assert parse_label("  P3   46.0    RL26 ") == ("P3", 46.0, "RL26")

    def test_comma_in_number(self):
        # Some users may write "1,234" — should parse as 1234
        assert parse_label("P1 1,234 H4350") == ("P1", 1234.0, "H4350")


# ============================================================
# extract_inches — pulls inches from display strings like '0.358" (0.342 MOA)'
# ============================================================

class TestExtractInches:
    def test_us_format_with_quote(self):
        assert extract_inches('0.358"') == 0.358

    def test_us_format_with_moa_suffix(self):
        assert extract_inches('0.358" (0.342 MOA)') == 0.358

    def test_european_decimal_comma(self):
        assert extract_inches('0,358"') == 0.358

    def test_us_thousands_separator(self):
        # 1,234.56 — US: comma is thousands sep, dot is decimal
        assert extract_inches('1,234.56"') == 1234.56

    def test_european_thousands_separator(self):
        # 1.234,56 — EU: dot is thousands sep, comma is decimal
        assert extract_inches('1.234,56"') == 1234.56

    def test_negative_value(self):
        assert extract_inches('-0.05"') == -0.05

    def test_none(self):
        assert extract_inches(None) is None

    def test_empty(self):
        assert extract_inches("") is None

    def test_no_number(self):
        assert extract_inches("garbage") is None


# ============================================================
# extract_signed — pulls signed numbers like "+ 0.13" or "- 0.07"
# ============================================================

class TestExtractSigned:
    def test_positive(self):
        assert extract_signed("+ 0.13") == 0.13

    def test_negative(self):
        assert extract_signed("- 0.07") == -0.07

    def test_european_decimal(self):
        assert extract_signed("+ 0,13") == 0.13

    def test_no_sign(self):
        assert extract_signed("0.5") == 0.5

    def test_none(self):
        assert extract_signed(None) is None

    def test_empty(self):
        assert extract_signed("") is None
