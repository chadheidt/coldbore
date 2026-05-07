"""Tests for the validation logic in import_data.py — sanity ranges and
duplicate-tag detection."""

import import_data


def _make_chrono(tag="P1", avg_vel=3000.0, sd=8.0, es=15.0, bullet_wt=140, shots=None):
    if shots is None:
        shots = [3000.0, 3005.0, 2995.0]
    return {
        "kind": "chronograph", "Source": "garmin",
        "Tag": tag, "ChargeOrJump": 45.5, "Powder": "H4350",
        "Date": "", "Shots": shots,
        "AvgVel": avg_vel, "SD": sd, "ES": es,
        "BulletWt": bullet_wt, "AvgKE": None,
        "SessionTitle": f"{tag} 45.5 H4350", "SessionNote": "",
    }


def _make_group(tag="P1", group_in=0.5, height_in=0.3, mr_in=0.15):
    return {
        "kind": "group", "Source": "ballisticx",
        "Tag": tag, "ChargeOrJump": 45.5, "Powder": "H4350",
        "Date": "", "Distance": 100, "Caliber": "",
        "GroupIn": group_in, "WidthIn": 0.4, "HeightIn": height_in,
        "MRIn": mr_in, "CEPIn": 0.2, "SDRadIn": None,
        "SDVertIn": None, "SDHorizIn": None, "ElevOffsetIn": None,
        "WindOffsetIn": None, "Label": f"{tag} 45.5 H4350",
    }


# ============================================================
# Chronograph validation
# ============================================================

class TestChronographValidation:
    def test_normal_record_no_warnings(self):
        warnings = []
        import_data._validate_chronograph_record(_make_chrono(), "test", warnings)
        assert warnings == []

    def test_velocity_too_low_flagged(self):
        warnings = []
        import_data._validate_chronograph_record(
            _make_chrono(avg_vel=100.0), "test", warnings,
        )
        assert any("AvgVel" in w for w in warnings)

    def test_velocity_too_high_flagged(self):
        warnings = []
        import_data._validate_chronograph_record(
            _make_chrono(avg_vel=10000.0), "test", warnings,
        )
        assert any("AvgVel" in w for w in warnings)

    def test_sd_too_high_flagged(self):
        warnings = []
        import_data._validate_chronograph_record(
            _make_chrono(sd=200.0), "test", warnings,
        )
        assert any("SD" in w for w in warnings)

    def test_negative_sd_flagged(self):
        warnings = []
        import_data._validate_chronograph_record(
            _make_chrono(sd=-5.0), "test", warnings,
        )
        assert any("SD" in w for w in warnings)

    def test_bullet_weight_outlier_flagged(self):
        warnings = []
        import_data._validate_chronograph_record(
            _make_chrono(bullet_wt=2000), "test", warnings,
        )
        assert any("BulletWt" in w for w in warnings)

    def test_bogus_shot_velocity_flagged(self):
        warnings = []
        import_data._validate_chronograph_record(
            _make_chrono(shots=[3000.0, 50.0, 3010.0]), "test", warnings,
        )
        assert any("Shot 2" in w for w in warnings)

    def test_none_values_not_flagged(self):
        # Missing values should be tolerated (None means not parsed, not zero)
        warnings = []
        rec = _make_chrono()
        rec["AvgVel"] = None
        rec["SD"] = None
        import_data._validate_chronograph_record(rec, "test", warnings)
        assert warnings == []


# ============================================================
# Group validation
# ============================================================

class TestGroupValidation:
    def test_normal_record_no_warnings(self):
        warnings = []
        import_data._validate_group_record(_make_group(), "test", warnings)
        assert warnings == []

    def test_giant_group_flagged(self):
        warnings = []
        import_data._validate_group_record(
            _make_group(group_in=25.0), "test", warnings,
        )
        assert any("Group" in w for w in warnings)

    def test_giant_vertical_flagged(self):
        warnings = []
        import_data._validate_group_record(
            _make_group(height_in=12.0), "test", warnings,
        )
        assert any("Vertical" in w for w in warnings)


# ============================================================
# Duplicate tag detection
# ============================================================

class TestDuplicateTags:
    def test_unique_tags_no_warnings(self):
        records = [_make_chrono(tag="P1"), _make_chrono(tag="P2"), _make_chrono(tag="P3")]
        assert import_data._check_duplicate_tags(records, "test") == []

    def test_two_with_same_tag(self):
        records = [_make_chrono(tag="P1"), _make_chrono(tag="P1")]
        warnings = import_data._check_duplicate_tags(records, "garmin")
        assert len(warnings) == 1
        assert "P1" in warnings[0]
        assert "garmin" in warnings[0]

    def test_three_with_same_tag(self):
        records = [_make_chrono(tag="P1") for _ in range(3)]
        warnings = import_data._check_duplicate_tags(records, "garmin")
        assert len(warnings) == 1
        assert "3 records" in warnings[0]

    def test_empty_tag_ignored(self):
        records = [_make_chrono(tag=""), _make_chrono(tag="")]
        # Empty tags shouldn't be flagged as duplicates of each other
        # (empty just means parsing didn't find a tag)
        assert import_data._check_duplicate_tags(records, "test") == []

    def test_empty_record_list(self):
        assert import_data._check_duplicate_tags([], "test") == []
