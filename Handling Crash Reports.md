# Handling Crash Reports

A reference for what to do when a user emails you a crash report from Loadscope.

---

## What a crash report looks like

Loadscope has an opt-in crash reporter (built into the app — `app/crash_reporter.py`). When something inside the app throws an unhandled exception, the user sees a dialog with the full traceback and a **"Send via Email"** button. If they click Send, it opens their default mail app with this pre-filled:

- **To:** `support@loadscope.app` (which forwards to your personal Gmail)
- **Subject:** `Loadscope v0.X.Y — crash report`
- **Body:** structured text starting with `Loadscope vX.Y.Z — crash report`, including app version, Python version, macOS version, and the full Python traceback

You'll get something like:

```
Loadscope v0.6.0 — crash report
Date: 2026-05-15T14:32:08
Python: 3.11.5
Platform: macOS-14.5-arm64-arm-64bit

Traceback:
Traceback (most recent call last):
  File "/Applications/Loadscope.app/Contents/Resources/main.py", line 123, in handle_drops
    parser = detect_parser(p)
  File "...", line 45, in detect_parser
    ...
KeyError: 'GroupSizeDisplay'
```

Real bug-finding gold — the exact line and reason it failed.

---

## What to do (the easy path: come back to Claude)

1. **Open Cowork** and re-engage with the project. Use the magic phrase from the top of `Notes for next session.md`.
2. **Paste the crash report** into the chat. Just the whole email body.
3. Say: *"User reported this crash. Help me fix it."*
4. Claude will:
   - Read the traceback and identify the bug
   - Edit the appropriate file(s) to fix it
   - Write a test case in `tests/` that would have caught the bug (so it doesn't come back)
   - Suggest a version bump (e.g., 0.6.0 → 0.6.1) and a release-notes line
5. **You commit + push + create the release** (Claude walks you through it). About 10-15 minutes total.
6. **Reply to the user** thanking them for the report and telling them v0.6.1 is on the way (auto-update banner will show within a few hours).

---

## Triage tips

Before you panic:

- **Check the app version in the report.** If they're on v0.5.0 and you've already shipped v0.6.0 with that bug fixed, just reply: "Hey, please update to the latest — I think this is fixed." Tools → Check for Updates… in their app should show the newer version.
- **Look for patterns.** If three users report the same traceback, it's a real bug worth fixing fast. If one user reports something weird and you can't reproduce, ask for more info before changing code.
- **The traceback location is THE clue.** The last few lines of "Traceback" tell you exactly what file and line failed and what type of error. Most fixes are within 5 lines of that.

---

## Common crash patterns and what they usually mean

| Error type | Likely cause | Where to look |
|---|---|---|
| `KeyError: 'XYZ'` in a parser | CSV format changed (Garmin firmware update, BallisticX update) — missing column | `app/parsers/<source>.py` — make the column lookup tolerant or add a fallback |
| `FileNotFoundError` | User's project folder moved or got deleted | `app/config.py` — better error handling around missing folders |
| `PermissionError` | Workbook open in Excel during write | Already handled (we show a friendly message), but if a new path triggers it, add the same handling |
| `AttributeError: 'NoneType' object has no attribute …` | A cell that we expected to have a value was empty | The line shown — add `if x is not None:` guard or use `.get(key, default)` |
| `UnicodeDecodeError` | CSV with weird encoding | We already handle UTF-8-sig; for other encodings add `errors='replace'` to the open() call |
| Anything inside `setup_wizard.py` | Probably first-run on a fresh Mac with no template | Check the bundled template path logic |

---

## What to ask the user if the report is confusing

If the traceback is empty or doesn't make sense, ask the user to reply with:

1. **Steps to reproduce.** "What did you click / drag right before the crash?"
2. **A screenshot of the activity log** (the dark log area at the bottom of the Loadscope window). They can copy/paste text from it too.
3. **A sample of the CSV that triggered it** (if it's an import problem). Make sure to ask them to anonymize anything sensitive — though for chronograph data there's not much to anonymize.

If you got a crash report email but not the user's name, you can reply to the email to ask follow-up questions. Email replies thread to the support inbox.

---

## After shipping the fix

- The user gets the fix automatically via the in-app update banner (within hours of you publishing the new release and updating manifest.json)
- **Reply to the original report** when the fix is live: *"Fixed in v0.6.1, just released. Open Loadscope → Tools → Check for Updates to grab it."*
- **Add a line to the release notes** mentioning the fix, ideally crediting the user if they're OK with it ("Thanks Bob for finding this")

---

## Important: never blindly catch exceptions to make crashes go away

If you (or a future Claude session) is tempted to wrap the failing code in `try/except: pass` to silence a crash report — DON'T. That hides the bug, lets bad data into the workbook, and makes the user think things are working when they're not. Always actually fix the bug. The test you write should reproduce the crash AND assert the fix.
