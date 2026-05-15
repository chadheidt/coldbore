"""Hide / restore Microsoft Excel's chrome (ribbon icon strip, headings, etc.).

When Loadscope opens a workbook in Excel, we want the user to focus on their
worksheet content -- not Excel's icon strip and column/row headings. This
module ships one helper that hides as much chrome as Excel for Mac actually
allows reliably, and a second that restores it.

Achievable chrome-hide matrix on Excel for Mac (16.x), audited via screenshots
============================================================================

    Element                 Hideable?   Mechanism
    ----------------------- ----------- -------------------------------------
    Title bar               No (kept)   --
    Mac menu bar            No (kept)   File > Print stays reachable here
    Ribbon TABS row         No*         (* only via macOS native fullscreen,
                                          which moves Excel to its own Space
                                          -- bad UX with Loadscope)
    Ribbon icon strip       Yes         kOUIRibbonDefaultCollapse persistent
                                          preference (Excel reads on launch)
    Formula bar             Yes         set display formula bar to false
                                          (no-op in modern Mac Excel which
                                          integrates the formula bar into
                                          the title bar; harmless)
    Status bar              Partial     set display status bar to false
                                          (zoom + page-mode bits may persist)
    Row/column headings     Yes         set display headings of active window
    Scroll bars             No (kept)   users still need to scroll
    Sheet tabs              No (kept)   users still need to switch tabs

The big lever for the ribbon icon strip is the persistent preference
`com.microsoft.Excel kOUIRibbonDefaultCollapse = YES` -- the same setting
Excel itself writes when the user presses Cmd+Option+R. Because it is a
GLOBAL Excel preference (it affects every workbook the user ever opens, not
just Loadscope's) and it persists across launches, we must NOT leave the
customer's Excel permanently altered. So we:

  1. Capture the user's prior `kOUIRibbonDefaultCollapse` value the first
     time we touch it, persisting it in Loadscope's own config so the
     restore survives even a Loadscope crash/force-quit.
  2. Collapse the ribbon for the Loadscope session.
  3. Restore the user's original value when Loadscope quits (wired to
     QApplication.aboutToQuit in main.py) or when the demo tour closes.

This keeps the clean view while Loadscope is in use and returns the
customer's Excel to exactly how they had it afterward -- important for a
paid product where "Loadscope changed my Excel and won't change it back"
would be a legitimate support complaint.
"""

import os
import subprocess
import sys

_EXCEL_DOMAIN = "com.microsoft.Excel"
_RIBBON_PREF_KEY = "kOUIRibbonDefaultCollapse"

# Config key under which we stash the user's pre-Loadscope ribbon-pref state
# so restore_excel_chrome() can put it back. Value is the raw string the
# pref had ("0"/"1"/etc.), or the _ABSENT sentinel if the key didn't exist.
_CONFIG_PRIOR_KEY = "_excel_ribbon_pref_prior"
_ABSENT = "__absent__"


_MINIMIZE_SCRIPT = '''
tell application "Microsoft Excel"
    try
        set display formula bar to false
    end try
    try
        set display status bar to false
    end try
    try
        if (count of windows) > 0 then
            set display headings of active window to false
        end if
    end try
end tell
'''


_RESTORE_SCRIPT = '''
tell application "Microsoft Excel"
    try
        set display formula bar to true
    end try
    try
        set display status bar to true
    end try
    try
        if (count of windows) > 0 then
            set display headings of active window to true
        end if
    end try
end tell
'''


def _run_osascript(script, timeout=8):
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
        return True
    except Exception:
        return False


def _read_ribbon_pref():
    """Return the current raw value of the Excel ribbon-collapse preference
    as a string (e.g. "0" or "1"), or None if the key does not exist.
    Best-effort -- returns None on any error too.
    """
    try:
        result = subprocess.run(
            ["defaults", "read", _EXCEL_DOMAIN, _RIBBON_PREF_KEY],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None  # key absent (or read failed)
        return result.stdout.strip()
    except Exception:
        return None


def _write_ribbon_pref_bool(value_bool):
    try:
        subprocess.run(
            ["defaults", "write", _EXCEL_DOMAIN, _RIBBON_PREF_KEY,
             "-bool", "YES" if value_bool else "NO"],
            capture_output=True, text=True, timeout=5,
        )
        return True
    except Exception:
        return False


def _delete_ribbon_pref():
    try:
        subprocess.run(
            ["defaults", "delete", _EXCEL_DOMAIN, _RIBBON_PREF_KEY],
            capture_output=True, text=True, timeout=5,
        )
        return True
    except Exception:
        return False


def _load_config():
    """Lazy, decoupled access to Loadscope's config. Never raises -- returns
    ({}, None) if config is unavailable so chrome handling degrades to a
    best-effort no-restore rather than crashing the app or a test.

    config.py does `from version import APP_NAME`, which only resolves with
    app/ on sys.path (the runtime layout) -- NOT via `from app import
    config`. So we replicate the app's own import environment: put this
    module's directory (app/) on sys.path, then `import config` exactly as
    main.py does.
    """
    try:
        _app_dir = os.path.dirname(os.path.abspath(__file__))
        if _app_dir not in sys.path:
            sys.path.insert(0, _app_dir)
        import config as _config
        return _config.load_config(), _config
    except Exception:
        return {}, None


def _save_prior_ribbon_state(raw_value):
    """Persist the user's pre-Loadscope ribbon state. Only saves if we have
    NOT already saved one (so a second workbook-open in the same run doesn't
    overwrite the true original with our own collapsed value)."""
    cfg, mod = _load_config()
    if mod is None:
        return
    if cfg.get(_CONFIG_PRIOR_KEY) is not None:
        return  # already captured; don't clobber the real original
    cfg[_CONFIG_PRIOR_KEY] = raw_value if raw_value is not None else _ABSENT
    try:
        mod.save_config(cfg)
    except Exception:
        pass


def _pop_prior_ribbon_state():
    """Read and clear the saved prior state. Returns the saved string,
    _ABSENT, or None if nothing was saved."""
    cfg, mod = _load_config()
    if mod is None:
        return None
    prior = cfg.get(_CONFIG_PRIOR_KEY)
    if prior is None:
        return None
    try:
        cfg.pop(_CONFIG_PRIOR_KEY, None)
        mod.save_config(cfg)
    except Exception:
        pass
    return prior


def _looks_truthy(raw):
    return str(raw).strip().lower() in ("1", "yes", "true")


def minimize_excel_chrome():
    """Hide the Excel chrome that we can reliably control on Mac:
      - Persists preference: ribbon collapses to tabs-only on next Excel
        launch (no Bold/Italic/Format/etc. icon strip). The user's prior
        value is captured first so restore_excel_chrome() can put it back.
      - Hides on the active window: formula bar, status bar, row/column
        headings.

    Best-effort and idempotent. Silently does nothing if Excel isn't
    running or `defaults`/AppleScript aren't reachable.

    NOT touched by this helper: the ribbon TABS themselves (Home/Insert/
    Page Layout/etc.). Excel for Mac doesn't expose a reliable way to
    fully hide the tabs in-window -- that requires macOS native fullscreen,
    which moves Excel to its own Space and breaks switching to Loadscope.
    """
    # Capture-then-collapse. _save_prior_ribbon_state() is a no-op if we've
    # already captured the original this run, so calling minimize twice
    # never loses the user's true pre-Loadscope value.
    _save_prior_ribbon_state(_read_ribbon_pref())
    _write_ribbon_pref_bool(True)
    return _run_osascript(_MINIMIZE_SCRIPT)


def restore_excel_chrome():
    """Reverse minimize_excel_chrome:
      - Restores the global ribbon-collapse preference to whatever value
        the user had before Loadscope touched it (or removes the key if
        it didn't exist), so the customer's Excel returns to exactly how
        they had it.
      - Restores formula bar, status bar, and row/column headings on the
        active window.

    Wired to QApplication.aboutToQuit (real-user path) and to the demo
    tour panel's closeEvent. Safe to call when nothing was minimized --
    it's a no-op if no prior state was captured.
    """
    prior = _pop_prior_ribbon_state()
    if prior is not None:
        if prior == _ABSENT:
            _delete_ribbon_pref()
        else:
            _write_ribbon_pref_bool(_looks_truthy(prior))
    return _run_osascript(_RESTORE_SCRIPT)
