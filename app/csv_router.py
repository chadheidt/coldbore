"""
Detect which parser handles a dropped CSV.

Thin wrapper around the parser registry in app.parsers — exists for legacy
callers that expect the simple "garmin"/"ballisticx"/None return values.
New code should import directly from app.parsers and use detect_parser().
"""

import os
import sys

# When called as a top-level module (e.g. via Test Loadscope.command),
# make sure the parsers package is importable.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from parsers import detect_parser


def detect_csv_type(path):
    """Return the parser's stable KEY string ('garmin', 'ballisticx', etc.)
    for a given CSV path, or None if no parser claims it.
    """
    parser = detect_parser(path)
    return parser.KEY if parser else None


if __name__ == "__main__":
    # Smoke test against the sample files in the project folder.
    from pathlib import Path
    project = Path(__file__).resolve().parent.parent
    samples = [
        project / "Garmin Imports" / "P1_57_3_h1000_2026-03-01_09-33-01.csv",
        project / "BallisticX Imports" / "P1 57.3 h1000.csv",
    ]
    for s in samples:
        if s.exists():
            print(f"{s.name}  →  {detect_csv_type(s)}")
        else:
            print(f"(missing) {s}")
