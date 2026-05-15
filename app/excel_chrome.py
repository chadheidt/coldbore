"""Hide / restore Microsoft Excel's chrome (ribbon icon strip, headings, etc.).

When Loadscope opens a workbook in Excel, we want the user to focus on their
worksheet content — not Excel's icon strip and column/row headings. This
module ships one helper that hides as much chrome as Excel for Mac actually
allows reliably, and a second that restores it.

Achievable chrome-hide matrix on Excel for Mac (16.x), audited via screenshots
============================================================================

    Element                 Hideable?   Mechanism
    ----------------------- ----------- -------------------------------------
    Title bar               No (kept)   —
    Mac menu bar            No (kept)   File > Print stays reachable here
    Ribbon TABS row         No*         (* only via macOS native fullscreen,
                                          which moves Excel to its own Space
                                          — bad UX with Loadscope)
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

The big win: writing the persistent preference
`com.microsoft.Excel kOUIRibbonDefaultCollapse = YES` makes Excel always
launch with the ribbon collapsed to tabs-only (no icon strip). This is the
same setting Excel itself writes when the user presses Cmd+Option+R.
"""

import subprocess


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


def _set_excel_pref(key, value_bool):
    """Write a boolean Excel preference via `defaults`. Excel re-reads its
    plist on launch, so changes take effect on the next cold-launch.
    Best-effort — silent failure on unexpected errors.
    """
    try:
        subprocess.run(
            ["defaults", "write", "com.microsoft.Excel", key,
             "-bool", "YES" if value_bool else "NO"],
            capture_output=True, text=True, timeout=5,
        )
        return True
    except Exception:
        return False


def minimize_excel_chrome():
    """Hide the Excel chrome that we can reliably control on Mac:
      - Persists preference: ribbon collapses to tabs-only on next Excel
        launch (no Bold/Italic/Format/etc. icon strip).
      - Hides on the active window: formula bar, status bar, row/column
        headings.

    Best-effort and idempotent. Silently does nothing if Excel isn't
    running.

    NOT touched by this helper: the ribbon TABS themselves (Home/Insert/
    Page Layout/etc.). Excel for Mac doesn't expose a reliable way to
    fully hide the tabs in-window — that requires macOS native fullscreen,
    which moves Excel to its own Space and breaks switching to Loadscope.
    """
    _set_excel_pref("kOUIRibbonDefaultCollapse", True)
    return _run_osascript(_MINIMIZE_SCRIPT)


def restore_excel_chrome():
    """Reverse minimize_excel_chrome — restore formula bar, status bar, and
    row/column headings on the active window.

    Note: does NOT undo the persistent ribbon-collapse preference. If we
    flipped that back, the user would lose the chrome reduction on every
    subsequent Excel launch — and most users will appreciate the cleaner
    layout regardless of whether Loadscope's tour is running. Users who
    explicitly want the icon strip back can press Cmd+Option+R in Excel.
    """
    return _run_osascript(_RESTORE_SCRIPT)
