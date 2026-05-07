# Rifle Load Development — Project Context (read me first)

A handoff note so any future Claude session can pick up where we left off without re-deriving everything.

**Also read `Build progress.md`** — it tracks the in-progress GUI app build (phases 1–6).

---

## What this project is

Chad is a precision rifle shooter doing systematic load development. He uses:
- **Garmin Xero** chronograph (ShotView app) → exports per-shot velocity CSVs
- **BallisticX** target-analysis app → exports group-statistics CSVs
- **Excel for Mac 2016** (version 16.16.27) — important constraint, see below

The workbook in this folder is his bench tool. After every range trip, his Garmin and BallisticX CSVs auto-import into the workbook so he doesn't have to type velocities, group sizes, mean radius, etc. by hand.

Two main test types per load development cycle:
1. **Powder ladder** — vary charge weight (P1–P10), find the velocity flat-spot / SD low
2. **Seating depth** — vary jump (S1–S10), find the smallest groups
3. **Confirmation** — build at the winner and verify (CONFIRM-1, CONFIRM-2…)

---

## Files in this folder (don't move or rename without updating the script)

| File | Purpose |
|---|---|
| `Rifle Loads Template (do not edit).xltx` | Master template. New cycles `File → Save As` from this. |
| `My Load Dev Data.xlsx`, `7 Saum hunter load dev.xlsx`, etc. | Chad's working file(s). |
| `import_data.py` | CLI Python script that reads CSVs and writes to the workbook. Used by Desktop `.command`. |
| `Import Rifle Data.command` | Lives on Chad's **Desktop**. Bash wrapper that runs `import_data.py`. Auto-installs `openpyxl` on first run. |
| `Test Cold Bore.command` | Dev launcher for the GUI app — runs `app/main.py`. |
| `app/` | The new GUI app code (PyQt5). See "GUI app architecture" below. |
| `Build progress.md` | Tracks the GUI app build (phase status). |
| `Setup Instructions.docx` / `.md` | Full one-time setup walkthrough for the CLI flow. |
| `Garmin Imports/` | Drop Garmin CSVs here. |
| `BallisticX Imports/` | Drop BallisticX CSVs here. |

`import_data.py`'s `PROJECT = ...` constant near the top points at this folder for the CLI flow. The GUI app uses a config file at `~/Library/Application Support/Cold Bore/config.json` instead, with auto-detection of legacy folder locations on first run.

## GUI app architecture (`app/` folder)

| File | Purpose |
|---|---|
| `csv_router.py` | Thin wrapper around `parsers.detect_parser()` that returns the legacy KEY string |
| `main.py` | The PyQt5 window: drop zone, workbook picker, status counter, Run Import button, log area, update banner, Tools menu. Drops auto-route via the parser registry. Crash reporter wired in. |
| `config.py` | Load/save JSON config; `get_project_folder()` checks config + auto-detects legacy folder locations; legacy migration from "Rifle Load Importer" to "Cold Bore" |
| `setup_wizard.py` | `SetupWizard` QDialog for first-run; creates project folder, subfolders, copies bundled .xltx template |
| `updater.py` | `UpdateChecker(QThread)` — fetches JSON manifest, compares versions, emits result signal (non-blocking). `DEFAULT_MANIFEST_URL` baked in. |
| `version.py` | `APP_NAME`, `APP_VERSION`, `TEMPLATE_VERSION`, `DISCLAIMER_VERSION`, `DISCLAIMER_TEXT` |
| `theme.py` | Color palette, QSS, drop-zone & banner stylesheets, carbon-fiber tile generator |
| `disclaimer.py` | First-launch modal disclaimer dialog + acceptance tracking |
| `settings_dialog.py` | Tools → Settings… UI (auto-update toggle, manifest URL override, backup retention) |
| `load_card.py` | Tools → Generate Load Card… — reads workbook, writes printable HTML to `Load Cards/` |
| `load_sharing.py` | Tools → Export/Import Shared Load — `.coldbore` JSON file format for sharing loads with friends |
| `crash_reporter.py` | Opt-in crash dialog with copy-to-clipboard / email-to-support actions |
| `parsers/` | **Pluggable parser registry.** Drop a new module here to add a chronograph or target app. Currently `garmin_xero.py` + `ballisticx.py`. See Phase 6.5 in Build progress.md for the contract. |
| `resources/` | App icon generator (`generate_icon.py`) and the generated `AppIcon.icns` |

## Project root `.command` launchers

| File | Purpose |
|---|---|
| `Build App.command` | Runs `setup.py py2app` — produces `dist/Cold Bore.app` |
| `Generate Icon.command` | Runs `app/resources/generate_icon.py` — produces `AppIcon.icns` |
| `Test Cold Bore.command` | Dev launcher — runs `app/main.py` directly |
| `Run Tests.command` | Auto-installs pytest, runs `tests/` suite |
| `Clean Up Old App.command` | One-time migration cleanup — removes old "Rifle Load Importer" artifacts |
| `Test Update URL.command` | Diagnostic — fetches the manifest URL and prints the response |
| `Import Rifle Data.command` | (Pre-GUI legacy) — runs `import_data.py` from Chad's Desktop |

The GUI is mid-build. See `Build progress.md` for current phase status. Currently complete: drag-and-drop with auto-routing by content, Run Import button, first-run wizard, persistent config, background update check (manifest URL configurable). Remaining: visual styling pass and py2app bundling.

---

## Workbook architecture (10 sheets)

Visible tabs:
1. **After Range Day** — single-page printable cheat sheet with two scenarios (continuing a cycle vs. starting a new one), label format, troubleshooting.
2. **Load Log** — powder ladder. Charge in column B, shots C–G, Avg/SD/ES H–J, Group K, Vertical L, Mean Radius M. Has a red SUGGESTED CHARGE bar at top driven by composite scoring.
3. **Charts** — auto-updating charts off Load Log/Seating Depth.
4. **Seating Depth** — same layout as Load Log but column B is jump (inches) instead of charge.
5. **Garmin Xero Import** — visible mirror of GarminSessions for sanity-checking what the script parsed.
6. **BallisticX Import** — visible mirror of BallisticXGroups.
7. **Load Library** — confirmed loads, manual entry.
8. **Ballistics** — DOPE tables for confirmed loads at 100/300/500/800/1000 yards.

Hidden helper sheets (the script writes here):
9. **GarminSessions** — columns A–R: Tag, ChargeOrJump, Powder, Date, Shot1–7, AvgVel, SD, ES, BulletWt, AvgKE, SessionTitle, SessionNote.
10. **BallisticXGroups** — columns A–Q: Tag, ChargeOrJump, Powder, Date, Distance, Caliber, GroupIn, WidthIn, HeightIn, MRIn, CEPIn, SDRadIn, SDVertIn, SDHorizIn, ElevOffsetIn, WindOffsetIn, Label.

Visible tabs reference the hidden sheets via cell-range refs like `GarminSessions!$A$2:$A$200` and use `LOOKUP(2, 1/(criteria), result)` patterns to route data by Tag.

---

## The label convention (critical)

Format: `<tag> <number> <powder>` — space-separated.

Examples:
- `P1 45.5 H4350` → Powder ladder Load 1, 45.5 gr, H4350
- `S7 0.070 H4350` → Seating Test 7, 0.070" jump
- `CONFIRM-1 41.5 H4350` → Confirmation group

The first space-separated word is the Tag (uppercased). First numeric token = ChargeOrJump. First non-numeric after that = Powder.

**Where the label comes from for each source:**

- **Garmin**: labeled inside the ShotView app. The CSV's first line carries the session title, and the script reads that.
- **BallisticX**: read from the **CSV filename** (without `.csv`). Chad cannot edit the in-app Label field reliably, so we route by filename instead. Logic: if the filename parses to a label with a numeric charge/jump (e.g., `P1 45.5 H4350.csv`), use the filename. Otherwise fall back to the in-CSV `Label` column.

---

## Key script behavior (`import_data.py`)

1. `find_workbook()` — picks the most-recently-edited non-template `.xlsx` in the project folder. **If 2+ workbooks exist, it prompts the user with a numbered list.** Excludes `.xltx` template, `~$` lock files, hidden files.
2. Parses every CSV in `Garmin Imports/` and `BallisticX Imports/` (recurses no — top-level only, so subfolders inside those are safe to use as archives).
3. **Safety check**: if both folders are empty, prints `SAFETY STOP — no CSVs found in either import folder`, opens the workbook, and exits without writing. This protects against accidental wipes.
4. Otherwise: clears rows 2+ in `GarminSessions` and `BallisticXGroups` and writes parsed records. Sets `wb.template = False` before saving (avoids the template content-type bug we hit earlier).
5. Opens the workbook in Excel via `subprocess.run(["open", workbook_path])`.

---

## Workflow for Chad

**Adding to current cycle (most range trips):**
1. Drop Garmin CSVs into `Garmin Imports/`.
2. Drop BallisticX CSV into `BallisticX Imports/`, **rename file to the label** (e.g. `P1 45.5 H4350.csv`).
3. Close Excel. Double-click `Import Rifle Data` on Desktop.
4. Workbook opens with all data filled in. Update the green Test Session info bar (date/temp/notes), Cmd+S.

**Starting a new cycle (different cartridge/bullet/powder):**
1. Move the finished workbook into a `Completed Loads/` subfolder (script ignores subfolders).
2. Move old CSVs into archive subfolders inside `Garmin Imports/` and `BallisticX Imports/`.
3. Double-click the `.xltx` template → File → Save As → name for new cycle.
4. Drop new CSVs and run import as normal.

---

## Constraints / decisions worth remembering

- **Excel for Mac 2016** does not support Power Query. Power Query was the original plan; we abandoned it and switched to a Python script + Desktop `.command` to stay compatible with Chad's version.
- **Cell-range refs** (e.g., `$A$2:$A$200`) are used instead of structured table refs because Excel 2016 + openpyxl-written tables had issues.
- **`wb.template = False` is required** before saving — without it, .xlsx files written by openpyxl had template content-type and Excel refused to open them.
- **Comments/VML caused "unreadable content" warnings** earlier. Solved by removing duplicate hover comments on the Ballistics tab and a LibreOffice round-trip cleanup.
- **Don't auto-fill via formulas where the script writes.** The hidden sheets are pure data, formulas live on the visible tabs.

---

## What's complete

**Workbook + CLI flow:**
- Full template architecture, info bars, charts, scoring formulas, DOPE tables.
- Auto-import pipeline from both apps working end-to-end via Desktop `.command`.
- Filename-based routing for BallisticX (since in-app labels don't work).
- Safety stop for empty import folders.
- Multi-workbook chooser when 2+ working files exist (CLI-only — GUI uses most-recent).
- One-page printable After Range Day cheat sheet with both scenarios.
- Setup Instructions.docx with troubleshooting.

**GUI app build (in progress, see `Build progress.md`):**
- Phase 1 ✅ — PyQt5 drop-target window with CSV auto-detection
- Phase 2 ✅ — Drops copy into the right folder; Run Import button triggers import; Excel opens
- Phase 3 ✅ — First-run wizard + persistent config; auto-detects existing project folders
- Phase 4 ✅ — Background update check + manual "Check for Updates" menu + yellow banner notification
- Phase 5 ⏳ — Visual styling pass (deferred, Chad explicitly wants this last)
- Phase 6 ⏳ — py2app bundling into a real `.app` for sharing with friends

## Likely future requests / open ideas

- **iOS port (Phase 8)** — Chad wants to build this with Claude eventually. Full collaboration plan is in `Build progress.md` under "Future: iOS app (Phase 8)". Has timeline, division of labor, architectural decisions, and recommended first move (4-6 hour prototype). When Chad says "let's start the iOS app", read that section.
- **Sales / commercialization (Phase 9)** — Chad is interested in eventually selling Cold Bore. Full commercialization plan in `Build progress.md` under "Future: Sales readiness (Phase 9)" — Path A (low-effort tip jar / wait for signal) and Path B (full commercialization with LLC, trademark, lawyer, App Store, etc.). Year-1 revenue range: $0–60k depending on path and luck. When Chad says "let's commercialize" or "let's start selling", read that section.
- If Chad ever upgrades Excel to 365, we could rebuild on Power Query for a cleaner one-click-from-Excel UX.
- Charts on the Charts tab could be expanded once Chad has run more cycles.
- The Ballistics tab DOPE entry is still manual — could potentially auto-fill from confirmed loads if he wants.
- Composite scoring weights (SD vs group vs vertical) are tunable in the formulas if he wants to bias differently.

---

## Quick "where do I look" map for future Claude

- **Label parsing** → `parse_label()` in `import_data.py` (~line 22).
- **Garmin CSV format** → `parse_garmin_csv()` (~line 70). Title on line 1, per-shot rows have integer in col 1 + velocity in col 2, stat rows have keyword in col 1 + value in col 2.
- **BallisticX CSV format** → `parse_ballisticx_csv()` (~line 138). Standard `csv.DictReader`, one row per group. Filename routing logic at the top of the function.
- **Workbook discovery** → `find_workbook()` (~line 173). Multi-file prompt is here.
- **Safety stop** → `main()` (~line 290).
- **Hidden sheet writers** → `write_garmin()` (~line 196) and `write_ballisticx()` (~line 226).

If you (future Claude) need to change CSV parsing, openpyxl's read/write API works fine here — just remember `wb.template = False` before save and use cell-range refs not structured refs.
