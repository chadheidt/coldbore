"""Guards for the signed disclaimer (app/version.py).

Gate 3 of the ballistic solver: predicted DOPE is a new liability
surface. The disclaimer must carry the predicted-estimate language and
DISCLAIMER_VERSION must have bumped so every user re-accepts on the next
shipped release. Also enforces the project's hard ASCII rule for the
disclaimer text (non-ASCII has crashed Python 3.9 builds before).
"""

import version


def test_disclaimer_version_bumped_for_predicted_dope():
    # Was 1; the predicted-DOPE clause is substantive -> must be >= 2 so
    # existing users are re-prompted on the next shipped release.
    assert isinstance(version.DISCLAIMER_VERSION, int)
    assert version.DISCLAIMER_VERSION >= 2


def test_disclaimer_has_predicted_estimate_clause():
    t = version.DISCLAIMER_TEXT
    # key, Chad-approved phrases (Option A, game/hunting line cut)
    assert "Predicted ballistic data is an ESTIMATE" in t
    assert "MUST be confirmed by live fire at known distances" in t
    assert "shot that matters" in t
    # the game/hunting callout was deliberately CUT
    assert "game" not in t.lower()
    # liability clause extended to cover reliance on predictions
    assert ("reliance on \\\n" not in t)  # no stray escape artifacts
    assert "reliance on predicted ballistic values that were not " \
           "verified at the range" in t


def test_disclaimer_clauses_renumbered_through_six():
    t = version.DISCLAIMER_TEXT
    for n in range(1, 7):
        assert f"\n{n}. " in t, f"missing clause {n}"
    assert "\n7. " not in t
    # predicted clause is #4; assume-all-risk moved to #6
    assert t.index("4. Predicted ballistic data") < \
        t.index("6. You assume all risk")


def test_disclaimer_text_is_pure_ascii():
    # Project hard rule: no em-dashes/curly quotes/non-ASCII in text
    # that gets written by the Py3.9 ASCII-default build path.
    version.DISCLAIMER_TEXT.encode("ascii")
