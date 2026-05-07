"""pytest configuration — adds the project's app/ folder to sys.path so test
modules can import csv_router, parsers, etc., without needing an installed package."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
