"""Smoke tests against the kind of bugs that only crash at runtime.

The motivating regression: v0.11.0 shipped with a NameError in
app/main.py's _begin_update_download -- it called
updater.resolve_download_url(manifest), but updater wasn't imported
as a module name, only specific symbols. The bug didn't surface
until a real running app clicked Install Update. The fix is small;
the embarrassment of shipping it isn't.

Pyflakes statically detects names referenced but never bound, which
is exactly the class of bug above. We run it across app/ on every
test invocation and fail on any "undefined name" warning. Stylistic
warnings (unused imports, etc.) are intentionally ignored -- the
codebase has accumulated some, and they aren't bugs.
"""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"


def test_no_undefined_names_in_app_modules():
    result = subprocess.run(
        [sys.executable, "-m", "pyflakes", str(APP_DIR)],
        capture_output=True,
        text=True,
    )
    bug_lines = [
        line for line in result.stdout.splitlines()
        if "undefined name" in line
    ]
    assert not bug_lines, (
        "pyflakes found undefined-name references in app/ -- these "
        "crash at runtime the moment the offending code path executes:\n"
        + "\n".join(bug_lines)
    )


def test_app_main_imports_cleanly():
    """As a backstop, importing app.main should not raise at module-load time.

    Catches ImportError / SyntaxError that pyflakes might miss for
    third-party-import-related issues (e.g., a `from PyQt5 import X`
    where X has been removed upstream).
    """
    import importlib

    # Reload protection -- if a previous test imported main, we want a
    # fresh evaluation so changes to app/main.py are seen.
    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
    else:
        importlib.import_module("main")
