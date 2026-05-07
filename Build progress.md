# Cold Bore App — Build Progress

Tracking the build of a self-contained .app bundle that Chad can ship to 3-4 friends.

Read this file alongside `Notes for next session.md` to understand the project as a whole.

## Vision

A single `.app` file Chad can AirDrop or email to friends. Friend opens the app, sees a window with a drop zone, drags Garmin and BallisticX CSVs in, the workbook opens in Excel filled out. First launch silently sets up the project folder structure. Built-in update check pulls new versions from a GitHub Releases or shared Dropbox URL.

## Architecture

```
Rifle Load Data/
├── app/                          (NEW — all Python code for the GUI app)
│   ├── csv_router.py             # auto-detect Garmin vs BallisticX
│   └── main.py                   # PyQt window with drop zone
├── import_data.py                # existing CLI script (Chad's personal flow, untouched)
├── Import Rifle Data.command     # existing Chad-only desktop launcher (untouched)
├── Test Cold Bore.command     # NEW — temporary test launcher for the GUI
└── (template, workbook, import folders, etc.)
```

The GUI app eventually replaces both of Chad's `.command` files for friend distribution. Chad himself can keep using whichever flow he prefers.

## Phases

### Phase 1 — Auto-route CSV detection + drop-target window  ✅ COMPLETE

- [x] `app/csv_router.py` — `detect_csv_type(path)` returns 'garmin' / 'ballisticx' / None.
      Tested on the real CSVs in `Garmin Imports/` and `BallisticX Imports/` — both detect correctly.
      Garmin marker: line 2 contains "SPEED (FPS)" or "POWER FACTOR" or "KE (FT-LB)".
      BallisticX marker: line 1 contains "GroupSizeDisplay" or other display field names.
- [x] `app/main.py` — PyQt5 window, big drop zone with hover effect, terminal-style log area.
- [x] `Test Cold Bore.command` — double-clickable launcher that installs PyQt5 if needed, then runs the GUI.

**End-of-phase test:** Chad runs `Test Cold Bore.command`, sees the window, drops mixed CSVs, watches the log correctly classify each as Garmin / BallisticX / unknown.

### Phase 2 — Wire up the actual import  ✅ COMPLETE & TESTED

- [x] After detection, GUI copies each dropped CSV into the correct folder via `shutil.copy2`.
- [x] Refactored `import_data.py`: extracted `run_import(workbook_path, project_dir, open_excel)` and `list_workbooks(project_dir)` from the old monolithic `main()`. CLI flow (`main()`) still works the same.
- [x] After successful import, `run_import` calls `subprocess.run(["open", workbook_path])` (controlled by `open_excel` arg).
- [x] GUI captures stdout from `run_import` via `contextlib.redirect_stdout` and renders it in the log area.
- [x] Errors handled: workbook open in Excel, no workbook found, unknown CSV format, copy failures, exceptions during import.
- [x] Bug fix: `shutil.SameFileError` when files dragged from inside the import folders themselves — `_stage_file` helper checks `os.path.samefile()` first.

### Phase 2.5 — Go button (added on user request)  ✅ COMPLETE & TESTED

- [x] Added a status label + Clear button + green Run Import button below the drop zone.
- [x] Drops now stage files (copy + counter) but don't trigger the import. Status updates per drop.
- [x] Run Import button enabled only when ≥1 file is staged. Disabled during import to prevent double-clicks.
- [x] Clear button resets the staged counter (without removing files from folders).
- [x] After import, staged counter resets to 0.

### Phase 3 — First-run wizard  ✅ CODE COMPLETE (needs end-user test)

- [x] `app/config.py` — load/save config at `~/Library/Application Support/Cold Bore/config.json`.
      `get_project_folder()` returns saved path, OR auto-detects an existing valid folder at known legacy locations
      (`~/Documents/Claude/Projects/Rifle Load Data`, `~/Documents/Rifle Loads`, `~/Documents/Rifle Load Data`).
      `is_setup_valid(path)` checks for the import subfolders + at least one workbook/template.
- [x] `app/setup_wizard.py` — `SetupWizard` QDialog with title, description, default path field
      (`~/Documents/Rifle Loads`), folder picker, Create button. Creates `Garmin Imports/`,
      `BallisticX Imports/`, `Completed Loads/` subfolders. Copies the bundled .xltx template in.
      `find_bundled_template()` looks in (1) py2app `_MEIPASS`, (2) macOS `.app/Contents/Resources/`,
      (3) repo root .xltx (dev mode), (4) `app/resources/templates/`.
- [x] `app/main.py` refactor: dropped the global `PROJECT` variable; `MainWindow` now accepts a
      `project_folder` arg. `main()` resolves the folder via config (or wizard) before opening the window.

**End-of-phase test:** Chad runs `Test Cold Bore.command`. Because his existing folder at
`~/Documents/Claude/Projects/Rifle Load Data` is a valid project folder, the auto-detect catches it,
saves it to config, and skips the wizard. The app opens normally with his existing data.

To force-test the wizard itself: temporarily delete or rename
`~/Library/Application Support/Cold Bore/config.json` AND move/rename the auto-detected
project folder; relaunch and the wizard should appear.

### Phase 4 — Update check  ✅ COMPLETE & TESTED END-TO-END

**Update channel hosted at:** `https://github.com/chadheidt/coldbore`
**Manifest URL (baked into `app/updater.py:DEFAULT_MANIFEST_URL`):** `https://raw.githubusercontent.com/chadheidt/coldbore/main/manifest.json`
**Support email:** `coldboreapp@gmail.com` (forwards to Chad's personal Gmail; appears as "Cold Bore Support" in the recipient field via display-name in mailto)

**Shipping a new version (the procedure):**
1. Bump `APP_VERSION` in `app/version.py` AND in `setup.py`
2. `Build App.command` → produces new `dist/Cold Bore.app`
3. Right-click the .app → Compress → upload zip to a new GitHub Release with tag `v0.X.0`
4. Edit `manifest.json` in the repo: bump `app_version`, update `app_download_url` to point to the new release asset
5. Friends' apps detect the change automatically — yellow update banner appears with click-through download link

**Defensive fixes added during the end-to-end test:**
- `updater.py` now decodes responses with `utf-8-sig` (strips BOM)
- Detects HTML responses (e.g., 404 page) and gives a clearer error than json.loads' generic complaint
- Detects empty responses
- `Test Update URL.command` written for future debugging — fetches the URL with the same code the app uses and prints step-by-step diagnostics

**Original phase 4 implementation notes (kept for reference):**

- [x] `app/version.py` — `APP_VERSION = "0.4.0"`, `TEMPLATE_VERSION = "1.0"`, plus `parse_version()` and `is_newer()` helpers.
- [x] `app/updater.py` — `UpdateChecker(QThread)`. Fetches a JSON manifest via stdlib `urllib`, parses it, compares versions, emits `finished_with_result(dict)` signal. 8-second timeout. Silent on network failure unless triggered manually.
- [x] `main.py` integration: yellow update banner widget at the top of the window, hidden by default. Help menu with "Check for Updates…" and "About". Auto-check fires 1 second after window opens (non-blocking via `QTimer.singleShot`). Manual check via menu shows results either way.
- [x] Banner content: shows app and/or template version availability, release notes, and clickable links for downloads. Links open in default browser via `QDesktopServices.openUrl`.
- [x] Manifest URL is read from `config.json` field `update_manifest_url`. Not set by default — Chad will paste in once hosting decision is made.

**Manifest format expected at the URL:**
```json
{
    "app_version": "0.6.0",
    "app_download_url": "https://github.com/.../releases/download/v0.6.0/ColdBore.zip",
    "app_release_notes": "Added charge weight scaling. Fixed bug X.",
    "template_version": "1.1",
    "template_download_url": "https://...",
    "template_release_notes": "Added new column on Load Log."
}
```

**End-of-phase test:** Chad runs the app — Help menu now appears. Choosing "Check for Updates…" shows a "no update channel configured" dialog (because no URL is set). The window otherwise functions exactly like Phase 3.

To force-test the auto-check itself: temporarily put a manifest at any URL (e.g. a GitHub Gist raw URL), set `update_manifest_url` in config, relaunch, and watch for the yellow banner.

### Phase 5 — Visual styling pass  ✅ CODE COMPLETE (needs end-user test)

Chad chose a **hybrid: Direction 1's color palette + Direction 2's spacing/typography**.

Implementation:
- [x] `app/theme.py` — central palette and stylesheet module. All colors and spacing tokens live here.
      Hunter-orange (#d97706) accent on dark charcoal (#0e0f12) backgrounds, with three text tiers and three background depths for hierarchy. Apple system font, generous padding, subtle borders.
- [x] Global QSS via `app.setStyleSheet(theme.application_stylesheet())` styles every QWidget,
      QPushButton, QTextEdit, QLineEdit, QMenuBar, QMenu, QDialog, and QScrollBar.
- [x] Primary CTA buttons use `setObjectName("primary")` to pick up the orange accent style.
- [x] DropZone idle/hover stylesheets pulled out to `theme.dropzone_idle_stylesheet()` /
      `dropzone_hover_stylesheet()` — orange highlight on hover.
- [x] Setup wizard pulls in theme tokens too (with graceful fallback if theme isn't importable).
- [x] Log color tokens (`LOG_GARMIN`, `LOG_BALLISTICX`, `LOG_SUCCESS`, etc.) pulled out of inline literals.

Remaining cosmetic items (still inside Phase 5 — finish before bundling):
- [ ] **Carbon-fiber background — DEFERRED to final polish.** Chad wanted a Proof Research style carbon weave. Multiple iterations didn't quite land it without a reference image we could parse. Code is fully in place: `theme.generate_carbon_tile()` produces the tile, `CarbonBackground` class in `main.py` paints it. Currently switched off — central widget is a plain QWidget showing the graphite BG_BASE color. To re-enable: change `central = QWidget()` back to `central = CarbonBackground()` in `MainWindow.__init__`. Then iterate on `generate_carbon_tile()` parameters (or replace with an actual JPG/PNG of a Proof barrel as a tiled background image) once Chad provides a reference image we can parse.
- [ ] Custom app icon for the Dock (.icns file). Suggest a target reticle or a simple stylized "RLI" mark in hunter orange on dark bg.
- [ ] Optional: small graphic in header (e.g. a 16-20px reticle next to the project name).
- [ ] Bundle a font? Apple system fonts work fine cross-Mac, so probably skip.

**End-of-phase test:** Chad runs the launcher. Window now has dark charcoal background, hunter orange accents, clean spacing. Drop zone glows orange on drag-over. Run Import button is solid orange. Wizard (if triggered) matches.

### Phase 6.7 — Drag-on-Dock-icon support (one-action import path)  ✅ COMPLETE & TESTED

Goal: let users drag CSVs onto the .app icon directly (Dock, Applications, Desktop) and have the import run automatically — no need to open the window or click Run Import. Window-drop flow stays as-is for batched drops.

Implementation:
- `setup.py` — added `CFBundleDocumentTypes` to the plist declaring CSV handling. Sets the app as a CSV "Viewer" with `LSHandlerRank: "Alternate"` (so it shows up in "Open With…" but doesn't fight to become the default CSV opener).
- `app/main.py` — new `RifleLoadApp(QApplication)` subclass. Intercepts `QEvent.FileOpen` (macOS Apple Event "odoc"), batches files arriving in rapid succession via a 300ms debounce timer, and forwards them to the main window once it's set.
- `MainWindow.handle_external_files(paths)` — new method. Brings the window forward, runs the same staging logic as `handle_drops`, then auto-triggers `run_import_clicked` after a 200ms delay (so the user sees what's happening before Excel pops up).
- `main()` — now constructs `RifleLoadApp` instead of `QApplication`, calls `set_main_window`, and processes any CSV paths passed via `sys.argv` (covers the case where the .app launches because the user dropped files on it while it wasn't running — py2app forwards these to argv).

User experience now:
- **Drag onto window** → stage → click Run Import (controls when import runs, batches from many sources)
- **Drag onto Dock icon / app icon / Desktop alias / right-click Open With** → auto-stages + auto-imports → Excel opens

**Batch-drop guidance for users:** The icon-drop debounce is **2 seconds** (`RifleLoadApp.BATCH_DEBOUNCE_MS = 2000`). Tell friends in the Quick Start: "Grab ALL the CSVs you want from this range trip in a single Finder selection, then drag the whole batch onto the icon at once." If they drop in multiple sessions with > 2s between drops, each batch becomes a separate import (Excel will open multiple times). Considered a "show countdown banner" UX (option C) but Chad chose simplicity over more UI.

End-to-end test: needs a fresh `.app` build via `Build App.command`. The drag-on-icon path won't work in dev mode (`Test Cold Bore.command`) because there's no .app bundle for macOS to register with — only the bundled .app gets the CFBundleDocumentTypes treatment.

### Phase 6.5 — Pluggable parser registry (added day 2 — broaden iOS-future audience)  ✅ CODE COMPLETE

Refactored the two hardcoded CSV parsers into a registry so adding support for new chronographs (LabRadar, MagnetoSpeed, Athlon Rangecraft, ProChrono) or new target-analysis apps becomes a single new file in `app/parsers/`. Bumped APP_VERSION 0.4.0 → 0.5.0.

**New file layout:**
```
app/parsers/
├── __init__.py       # registry: ALL_PARSERS, detect_parser, parser_by_key, chronograph_parsers, group_parsers
├── _common.py        # parse_label, extract_inches, extract_signed (shared helpers)
├── garmin_xero.py    # Garmin Xero ShotView (chronograph)
└── ballisticx.py     # BallisticX target group analysis (group)
```

**Parser contract** — each parser module exports:
- `KIND` — `"chronograph"` or `"group"`
- `NAME` — display name shown in the UI
- `KEY` — short stable identifier (legacy "garmin", "ballisticx", etc.)
- `IMPORT_FOLDER` — folder name relative to project root
- `detect(path) -> bool` — sniff the file
- `parse(path) -> dict` (chronograph) or `list[dict]` (group)

Each record dict includes a `"Source"` field carrying the parser's KEY so we know which tool produced the data.

**Adding a new chronograph (e.g., LabRadar):**
1. Create `app/parsers/labradar.py` modeled on `garmin_xero.py`.
2. Add `from . import labradar` and append `labradar` to `ALL_PARSERS` in `app/parsers/__init__.py`.
3. Done. The drop window auto-detects it, the import script auto-walks its IMPORT_FOLDER, the workbook writer (`write_chronograph_records`) handles the record format unchanged.

**What was refactored:**
- `import_data.py` — removed inline `parse_garmin_csv` / `parse_ballisticx_csv` / helpers. `run_import` now walks `ALL_PARSERS` and pulls records from each parser's IMPORT_FOLDER. Renamed `write_garmin` → `write_chronograph_records`, `write_ballisticx` → `write_group_records` (legacy aliases kept for backwards compat).
- `app/csv_router.py` — now a thin shim that wraps `parsers.detect_parser()` and returns the legacy KEY string.
- `app/main.py` (`handle_drops`) — replaced hardcoded `if kind == "garmin" / elif "ballisticx"` branches with a generic registry lookup. New parsers' files auto-route to the right folder via parser.IMPORT_FOLDER.
- `setup.py` — added `parsers` to py2app's `packages` list so the new package is bundled into the .app.

**End-to-end smoke test passed in dev mode** (sandbox `/usr/bin/python3` against the actual workbook): correctly detects, parses, and writes both Garmin and BallisticX records through the registry. **Chad still needs to rebuild the .app** to ship this — `Build App.command` should produce a 0.5.0 bundle that behaves identically to 0.4.0 from the user's perspective.

**Future parsers to consider:**
- LabRadar (Doppler radar chrono — very popular among precision shooters)
- MagnetoSpeed (bayonet-style chrono)
- Athlon Rangecraft (newer optical chrono)
- ProChrono / Caldwell (older optical)
- Custom CSV mode (user maps their own columns to the standard fields — future feature)

### Phase 6 — py2app bundling + ship  ✅ BUILD CONFIRMED WORKING ON CHAD'S MAC

The `.app` builds, opens, and runs the import flow correctly. Chad has it installed in his Applications folder.

- [x] `app/__init__.py` — turned `app/` into a proper Python package so py2app can bundle the submodules cleanly.
- [x] `setup.py` — py2app config. App name: "Cold Bore". Bundle id: `com.chadheidt.coldbore`. Version 0.4.0. Bundles PyQt5 + openpyxl as packages. Includes csv_router/config/setup_wizard/updater/version/theme/import_data as individual modules. Adds the `.xltx` template to DATA_FILES so it lands in `<App.app>/Contents/Resources/`. NSHighResolutionCapable + LSMinimumSystemVersion 10.13.
- [x] `app/setup_wizard.py find_bundled_template()` — fixed to look at `Path(sys.executable).parent.parent / "Resources"` for the actual py2app bundle layout (the prior code used PyInstaller's `_MEIPASS` which py2app doesn't use).
- [x] `Build App.command` — one-click builder. Auto-installs PyQt5 + openpyxl + py2app + setuptools (with fallback for older pip without `--break-system-packages`). Cleans previous build/dist folders. Runs setup.py. Reports size + opens dist/ on success.
- [x] **Smoke test on Chad's Mac.** ✅ done. App installed in Applications.
- [ ] **Custom icon** — defer with carbon to final-polish round.
- [ ] **Beta to one friend** — needs Quick Start guide first; ready otherwise.
- [ ] **Quick Start.pdf** for friends — single page: unzip, drag .app to Applications, right-click → Open the first time, drop CSVs.
- [ ] Note: setup.py has `CFBundleDevelopmentRegion: "en"` and `CFBundleLocalizations: ["en"]` queued (added during the Claude-language confusion). Will take effect on next rebuild — defensive, not strictly needed.

**Friends-of-Chad install path (for reference):**
1. Friend gets a zip via email/AirDrop containing one file: `Cold Bore.app`.
2. Unzip, drag the .app to Applications.
3. Right-click → Open the first time to bypass Gatekeeper (we're not paying $99/yr to code-sign).
4. App opens. First-run wizard creates a `Rifle Loads/` folder in their Documents and copies the bundled template in. Done.
5. Drag CSVs into the window. Excel opens with data.

**Known py2app gotchas to watch for during smoke test:**
- "ModuleNotFoundError" inside the bundled .app — usually means a hidden import wasn't picked up. Add the missing module name to `includes` in setup.py and rebuild.
- "Library not loaded" Qt errors — sometimes need `qt_plugins` listed explicitly. PyQt5's main bits (QtCore/QtGui/QtWidgets) usually bundle fine via `packages: ["PyQt5"]`.
- App opens then quits silently — typical cause is a Python error during startup. Run `<App.app>/Contents/MacOS/Rifle\ Load\ Importer` from Terminal to see the error.
- The build is ~80-150 MB depending on what gets pulled in. That's normal for a bundled PyQt5 app.

## Supported platforms (devices and apps)

Pulled live in-app from the parser registry — this list updates automatically when a parser is added. Source of truth for the UI's "About" dialog and the drop-zone subtitle is `app/parsers/__init__.py:ALL_PARSERS`.

**Currently supported (v0.5.0):**

| Device / App | Type | Parser module | Notes |
|---|---|---|---|
| Garmin Xero (ShotView) | Chronograph | `app/parsers/garmin_xero.py` | First-line session title carries the load label |
| BallisticX | Target group analysis | `app/parsers/ballisticx.py` | Filename carries the load label (in-app Label field is unreliable) |

**Architecture supports adding:** any chronograph or group-analysis app that exports CSV files. Adding one is a single file in `app/parsers/` plus an entry in `ALL_PARSERS` — see Phase 6.5 for the contract.

**Likely future parsers** (deferred until real users have real samples — speculative parsers built without real CSVs tend to break in practice):
- LabRadar / LabRadar LX (Doppler radar chrono)
- MagnetoSpeed V3 / Sporter (bayonet-style)
- Athlon Rangecraft (newer optical chrono)
- Garmin Xero C1 Pro (newer model — likely shares format with Xero, untested)
- ProChrono / Caldwell (older optical)

When a friend or new user wants support for a different device:
1. Have them email/AirDrop a sample CSV from their device, ideally with the load label format used (e.g., `P1 45.5 H4350` so we can verify parsed values)
2. Add `app/parsers/<device>.py` modeled on `garmin_xero.py` (chronograph) or `ballisticx.py` (group)
3. Add to `ALL_PARSERS` in `app/parsers/__init__.py`
4. Bump APP_VERSION, rebuild, ship

The in-app About dialog and the drop-zone subtitle update automatically once the parser is registered.

## Decisions / open questions

- **PyQt5 vs PyQt6:** chose PyQt5 because py2app + PyQt6 has had compatibility headaches. Easy to swap later if needed.
- **Hosting for updates:** TBD. GitHub Releases is free, professional, and supports versioned downloads. Recommend.
- **Code signing:** skipping for now ($99/yr Apple Developer ID overkill for 3-4 friends). Friends will need to right-click → Open the very first time. Document this in Quick Start.
- **CSV auto-route after copy:** when the app copies a Garmin file into `Garmin Imports/`, what filename should it use? Probably the original name to preserve archive trail. For BallisticX, the filename IS the label, so we keep the user's name (they'll have renamed it before dropping).

## iOS portability — guideline for ALL ongoing work

Chad plans to port this to an iOS app eventually. To keep that port sane, every change from now on should respect these rules:

**Code organization:**
- **Pure-data / pure-logic code goes in `app/parsers/`** — no PyQt imports, no Mac-specific APIs. Each parser, the `_common.py` helpers, and any future schema/validation code stays portable. These translate 1:1 to Swift structs and functions.
- **PyQt UI code stays in `app/main.py`, `app/setup_wizard.py`, `app/theme.py`** — these are Mac-only. SwiftUI replaces them in the iOS port.
- **Workbook write logic in `import_data.py`** — Excel/openpyxl is Mac+Windows only. iOS may or may not use the same xlsx storage; could be a native Core Data store with an export-to-xlsx feature instead. Keep parsing and writing in separate modules so the iOS port can swap out the writer.

**Data schemas to keep stable** (these become Swift structs):
- *Chronograph record*: `kind, Source, Tag, ChargeOrJump, Powder, Date, Shots[], AvgVel, SD, ES, BulletWt, AvgKE, SessionTitle, SessionNote`
- *Group record*: `kind, Source, Tag, ChargeOrJump, Powder, Date, Distance, Caliber, GroupIn, WidthIn, HeightIn, MRIn, CEPIn, SDRadIn, SDVertIn, SDHorizIn, ElevOffsetIn, WindOffsetIn, Label`

When these need new fields, update the schema doc and bump the version. Don't change semantics of existing fields.

**File-handling patterns that DO carry to iOS:**
- Document type registration in Info.plist (CFBundleDocumentTypes, LSItemContentTypes) — same concept on iOS, just lives in the iOS target's plist
- Share-sheet integration concepts apply to iOS Share Extensions
- The label convention `<tag> <number> <powder>` is platform-agnostic
- The parser auto-detection by content sniffing is platform-agnostic

**File-handling patterns that DON'T:**
- Drag-and-drop onto Dock icons — iPhone has no Dock; iPad does but it's different
- macOS QFileOpenEvent — iOS uses `application(_:open:options:)` AppDelegate hook
- File system path conventions (~/Documents/Rifle Loads vs iOS app sandbox) — iOS apps live in their own sandbox
- The .command launcher files

When making changes, mentally ask "would this work the same way in a Swift app?" If no, it should live in a Mac-specific module (main.py, setup_wizard.py) and not pollute the parser or schema layer.

## Phase 10 — Polish, safety, and quality (added day 4)  ✅ CODE COMPLETE

A round of quality and feature improvements after Cold Bore was bundled and shipping internally.

**What was added:**

### Safety
- **Workbook backup before every import** — `import_data._rotate_workbook_backups` writes a timestamped copy to `<project>/.backups/` before modifying the workbook. Default retention 5 (configurable via Settings → "Workbook backups to keep").
- **CSV data validation** (warnings, non-blocking) — `import_data._validate_chronograph_record` and `_validate_group_record` flag implausible values (velocity outside 500-5000 fps, SD>60, group>10 inches, bullet weight outside 10-800 gr, etc.). Warnings show in the activity log. Data still imports — these are heads-up flags, not blockers.
- **Duplicate-tag detection** — `import_data._check_duplicate_tags` warns when two records share a Tag (e.g., two Garmin sessions both labeled `P1 45.5 H4350`). Prevents silent overwrites in the workbook.
- **Locale-aware number parsing** — `parsers._common.extract_inches` / `extract_signed` now handle both US (1,234.56) and European (1.234,56) decimal formats. Enables future expansion to international users.

### Workbook lockdown
- All formula cells across 8 visible sheets are protected (1,659 cells per workbook). Non-formula cells (Notes, Test Session info bar, Load Components, Rifle/Shooter, scoring weights, Load Library, DOPE entries) remain editable. Hidden helper sheets (GarminSessions, BallisticXGroups) NOT protected so import script still works.
- Implementation: `outputs/lockdown_workbook.py`. Re-runnable on any new workbook via Save-As.

### Disclaimer
- `app/disclaimer.py` — modal first-launch dialog with full disclaimer + "I understand and accept" / "Quit" buttons. Acceptance tracked via `disclaimer_accepted_version` config field; bump `DISCLAIMER_VERSION` in version.py to re-prompt.
- Tools menu has "View Disclaimer…" item to review anytime.
- About dialog includes a short disclaimer summary.

### UX
- **"Show in Finder" menu items** — Tools menu has shortcuts for Project Folder, Garmin Imports, BallisticX Imports, and Backups folder (`MainWindow._reveal_in_finder`).
- **Settings panel** (`app/settings_dialog.py`) — Tools → Settings… opens a dialog with toggles for: auto-update check on/off, custom manifest URL override, backup retention count. Avoids users having to hand-edit JSON.
- **Multi-workbook switcher** — combo box at top of the main window when project folder has 2+ working .xlsx files. User picks which one to import to / generate a load card from. Selection persists across launches via `last_selected_workbook` in config. Hidden when only one workbook exists.
- **Load card generator** (`app/load_card.py`) — Tools → Generate Load Card… reads the workbook and writes a clean printable HTML page to `<project>/Load Cards/`. Browser → Print → Save as PDF for the range bag. Bullet weight extracted heuristically from bullet description (e.g., "180 Berger Hybrid" → 180 gr).
- **Load sharing** (`app/load_sharing.py`) — Tools → Export Suggested Load… writes a `.coldbore` JSON file to `<project>/Shared Loads/`. Friends import via Tools → Import Shared Load… which shows the load contents in a read-only dialog (intentionally NOT auto-writing to the recipient's workbook — safer for safety-adjacent data).

### Software quality
- **Pytest suite** (`tests/`) — `conftest.py`, `test_common_helpers.py` (parse_label, extract_inches, extract_signed), `test_parsers.py` (registry shape, garmin/ballisticx detection and parsing, filename-fallback for BallisticX), `test_validation.py` (sanity ranges, duplicate-tag detection). 50+ test cases. Run via `Run Tests.command` which auto-installs pytest.
- **Crash reporter** (`app/crash_reporter.py`) — replaces default Python excepthook with a friendly dialog showing the full traceback, Copy-to-Clipboard button, and Send-via-Email button. Privacy-conscious: nothing sent automatically; user reviews before clicking. Wired into main() at startup.
- **GitHub Actions CI/CD** (`.github/workflows/build-mac.yml`) — runs pytest on every push, builds the .app on every release tag, auto-attaches `Cold Bore.zip` to the release. Will work once Chad pushes the repo to GitHub.

### Cell-map fix
- `LOAD_LOG_FIELDS` in `load_card.py` had three cells pointing at LABEL cells (`K10` = "Dist (yd):", `F10` = "Off Lands:") instead of value anchors. Corrected to `L10` (distance), `G10` (off lands). `bullet_wt` removed entirely — extracted heuristically from the bullet description string.

**What was deferred from this round (Chad's call):**
- Cost-per-shot tracking
- Round count / barrel life tracker
- Atmospheric corrections (DA, temperature)
- DOPE auto-fill from confirmed loads

These are good ideas for a future Phase 11 if/when they come up.

## Future: iOS app (Phase 8) — collaboration plan

Chad asked "how would it look if you and I built the iOS app together." Captured here so we can resume cold.

**Division of labor:**
- *Claude*: writes Swift/SwiftUI code, translates parser registry to Swift, designs views, reads Xcode errors Chad pastes, iterates from screenshots, maintains breadcrumb continuity across sessions.
- *Chad*: installs Xcode (free, ~50GB from Mac App Store, one-time), runs Cmd+R to build, sends screenshots when UI looks off, navigates Xcode UI basics, eventually pays $99/yr for Apple Developer Program when ready to test on real iPhone or submit to App Store.
- *Neither*: Claude can't run Xcode or the iOS Simulator from sandbox; can't click around in Xcode remotely; some real-device bugs are slower to debug remotely.

**Realistic part-time timeline (a few hours per week):**

| Phase | Goal | Approx. time |
|---|---|---|
| 1. Setup | Xcode install, create iOS project, "Hello World" runs in simulator | week 1 |
| 2. Port parsers | Swift versions of `garmin_xero.py`, `ballisticx.py`, `_common.py`, registry | week 1-2 |
| 3. Data model | Swift structs for chronograph/group records, persistence (Core Data or SQLite) | week 2-3 |
| 4. File import | iOS file picker, Share Extension hook (so CSVs from any app can be sent to Cold Bore), iPad drag-and-drop | week 3-4 |
| 5. Data presentation | Rebuild Load Log / Seating Depth / Charts / Ballistics as native SwiftUI views — biggest chunk | weeks 5-7 |
| 6. Polish | App icon at iOS sizes, dark mode, accessibility, settings | week 8 |
| 7. Test + ship | TestFlight beta, App Store submission, review process | weeks 9-12 |

**Total: ~10-12 weeks part-time.** Faster if Chad gets into it, slower if part-time is closer to "one hour a week."

**Architectural decisions to make at the start (before week 1):**

1. **Excel-or-not.** Recommendation: **drop xlsx as the storage**, present data natively in SwiftUI, add an "Export to Excel" button for users who want a workbook. Most iOS users don't have Excel. Alternative is to keep xlsx as storage and ship a viewer, but that's clunky on iPhone.

2. **iPhone vs iPad vs both.** Recommendation: build **Universal** so it runs on both, but design layouts that adapt. iPad with drag-and-drop is the natural "bench tool"; iPhone is for "look at recent loads on the way to the range."

3. **Free vs paid.** Recommendation: **free** for the foreseeable future, friends-and-family distribution. Tip jar / "Buy me a coffee" is fine to add later. Paid app would require deciding price point and value proposition.

4. **MVP scope.** Don't try to ship full feature parity in v1. Pick the most-used feature (probably just "drop a CSV, see the data, see the suggested winner") and ship that. Add the rest in later releases.

**Recommended first move when we start: build a 4-6 hour prototype** that:
- Lets Chad pick a CSV from Files
- Detects whether it's Garmin or BallisticX
- Parses it using a Swift-ported parser
- Shows the data in a basic SwiftUI list view

That answers "does the architecture translate cleanly to iOS, and does it feel right on iPhone?" before sinking weeks into a full port. Mac version stays as the reference implementation in parallel.

**Honest blockers to expect:**
- Xcode is a complex app; first-time users sometimes get stuck on project settings that are invisible in screenshots. Will need patience on both sides.
- Apple's App Store review can be opaque. Apps occasionally get rejected for non-obvious reasons; budget extra time for back-and-forth.
- Swift has stricter type rules than Python — small things take a few more lines.
- iOS lifecycle (app states, view models, dependency injection) has its own learning curve; budget extra time for the first few features as we figure out idiomatic patterns.

**What carries over from the Mac codebase (free wins):**
- Parser registry architecture and contract (already designed for portability)
- Data schemas (`Chronograph record`, `Group record` — directly become Swift structs)
- Label convention and parsing rules (`<tag> <number> <powder>`)
- Auto-detection by content sniffing
- Update-check pattern (manifest URL + version comparison) — same idea, different fetch API
- Disclaimer text (re-used verbatim, just rendered in SwiftUI alert)
- Workbook scoring formulas (translated to Swift functions)
- All the conventions and decisions in `Notes for next session.md` and `Build progress.md`

**What Chad needs to decide before we kick off:**
- Are you ready to install Xcode and learn enough of it to be the "hands" on this project?
- Are you OK with the ~10-12 week part-time commitment for v1?
- Which architectural decisions above feel right to you?

When ready: say "let's start the iOS app" and I'll write the step-by-step Xcode setup guide as the first action.

## Future: Sales readiness (Phase 9) — commercialization plan

Chad asked "how marketable is Cold Bore?" and indicated interest in selling it. Captured the realistic path here.

**Honest market assessment recap:**
- Niche audience: ~50-200k precision rifle reloaders in the US, of whom maybe 30% own Garmin Xero (today, growing). Real addressable: ~15-60k people.
- Mac-only currently — biggest constraint. ~80% of reloaders are on Windows.
- Free competitors exist (GRT, shared Excel templates, OnTarget software).
- Reloading is safety-adjacent → trust takes years for a solo developer.
- Realistic year-1 revenue: $2k–15k if commercialized well, $20-60k if a viral moment hits, $0-500 if it flops.
- Cold Bore is unlikely to be a full-time business but could be a meaningful side project that funds shooting + earns community recognition.

**Two paths to choose from:**

### Path A: Lower-effort middle path (recommended starting point)
1. Ship free to friends/3-4 testers, gather feedback, iterate
2. Build Windows version (Phase 7) when ready — it's high-leverage regardless of commercialization
3. Add a "Buy me a coffee" / Stripe tip jar — no commitment, no LLC needed
4. Watch for organic community response (forum mentions, YouTube comments, friend-of-friend installs)
5. **Only commit to full commercialization (Path B) once there's clear positive signal.** Decision should be data-driven.

### Path B: Full commercialization (~6-9 months from start to first revenue)

**Foundation (weeks 1-4, ~$500-1500):**
- [ ] Form an LLC in Chad's state (~$50-500). Critical for safety-adjacent software — limits personal liability if a user blows up a rifle and tries to blame the app.
- [ ] Trademark "Cold Bore" with USPTO (~$250-350 filing fee + maybe lawyer for ~$500). Check existing trademarks first.
- [ ] Hire a software/firearms-adjacent attorney for 2 hours of consultation (~$300-600). Reviews:
  - Disclaimer / EULA (current one is informal boilerplate; commercial needs proper EULA)
  - Privacy policy (App Store + most jurisdictions require this if you collect any data)
  - Refund policy
- [ ] Register domain (`coldbore.app` recommended, ~$15/yr) and stand up a one-page landing site with screenshot, download button, disclaimer.

**Product readiness (months 2-7):**
- [ ] **Windows version (Phase 7)** — single most leveraged move for sales. Cross-platform alone could 5x addressable market.
- [ ] **iOS app (Phase 8)** — modern shooters expect mobile; App Store gives discoverability you can't get elsewhere.
- [ ] **Quick Start guide** — single-page friend-facing doc (already on the open list).
- [ ] **In-app help / first-run polish** — error messages for the 10 ways users will break it that we haven't predicted yet.

**Distribution setup (1-2 weeks once products are ready):**
- [ ] **Mac / Windows: Gumroad or Paddle** for direct download + credit card processing + automatic sales tax handling (~5-10% cut). AVOID the Mac App Store — Apple takes 30% and the review process is annoying for utilities.
- [ ] **iOS: App Store** mandatory. $99/yr Apple Developer Program. Apple takes 30% first year, 15% after.

**Pricing recommendation:**
- One-time purchase, NOT subscription (wrong vibe for this tool)
- Mac + Windows bundle: **$19-29 one-time**
- iOS: **$4.99-$9.99 one-time** (mobile pricing is weird; expectations are lower)
- Could bundle "all platforms" as a higher-priced option ($39-49) if it ever becomes practical

**Marketing (ongoing, low cash, lots of time):**
- [ ] **YouTube demo, 5-10 minutes.** Single most cost-effective marketing for niche shooting tools. Show drag-on-icon, the auto-import, the suggested winner. Costs nothing but a weekend of editing.
- [ ] **Reviewer outreach** — send free copies to 5 influential precision-rifle YouTubers/bloggers. Most will ignore, one or two might cover it.
- [ ] **Forum presence** on Sniper's Hide, AccurateShooter, Reddit r/precisionrifle and r/handloading. DON'T spam-launch — be a useful contributor for a few weeks first, then mention the app in a relevant thread.
- [ ] **Optional: gun magazine/podcast outreach** if YouTube takes off — Recoil, Rifle Shooter, RUN-N-GUN podcast, etc.

**Timeline (Path B, full commercialization):**

| Stage | Duration |
|---|---|
| Foundation (LLC, trademark, legal, domain) | weeks 1-4 |
| Windows port | months 2-4 |
| iOS port | months 4-7 |
| Soft launch (10-20 beta users) | month 7 |
| Public launch (YouTube + forums) | month 8 |
| First $100 | ~month 9-10 |
| First $1k | ~month 12-18 |

**Critical decisions to make before committing to Path B:**
1. Is Chad ready to invest $500-1500 upfront on legal/setup before any revenue?
2. Is Chad ready for the time commitment (probably 200-400+ hours total across product + marketing)?
3. Does the community response from the free distribution (Path A) justify the investment?

**Where the breadcrumb file points us when we resume:**
- If Chad has decided on Path B: start with foundation tasks (LLC + trademark + lawyer)
- If Chad is still on Path A: keep building, ship to friends, watch for signal
- Either way: the Windows port (Phase 7) and iOS app (Phase 8) are the next high-value engineering work

## Future: Windows build (Phase 7)

Chad has a Windows PC he wants to build a Windows version on, *after* the Mac version is fully shipped to friends. Plan:

1. **Code already mostly portable** — Python + PyQt5 + openpyxl all work on Windows.
2. **Platform-specific things to wrap with `if sys.platform == "darwin"` / `elif sys.platform == "win32"`:**
   - `subprocess.run(["open", workbook_path])` in `import_data.py` (run_import) and `setup_wizard.py` — Windows uses `os.startfile(path)` or `subprocess.run(["start", "", path], shell=True)`.
   - Config path in `config.py`: `Path.home() / "Library" / "Application Support" / APP_NAME` → on Windows use `Path(os.environ["APPDATA"]) / APP_NAME`.
   - The `CANDIDATE_LEGACY_LOCATIONS` list in `config.py` — Windows folder layout differs from Mac.
   - Removing the `.command` launchers (those are bash) — replaced by `.bat` files.
3. **Build tool:** swap py2app for PyInstaller. PyInstaller is cross-platform and works fine on Windows. The `setup.py` will become a `setup_windows.py` (or we collapse them and use platform detection).
4. **Building must happen ON a Windows machine.** Mac can't cross-compile a Windows .exe. The plan: when at the Windows PC, copy the project folder over, install Python and dependencies, write `Build App.bat`, run it, get `ColdBore.exe` (or a folder structure depending on PyInstaller mode).
5. **Friends-of-Chad install path on Windows:** unzip, double-click .exe, Windows SmartScreen will warn (similar to macOS Gatekeeper) — click "More info → Run anyway" once. From then on it's just an .exe.
6. **Excel for Windows compatibility:** the workbook should work fine — openpyxl produces standard .xlsx, and Excel for Windows handles them better than Excel for Mac 2016 in some cases (Power Query is available, etc., but our Python-based architecture works everywhere).

## Where I am, in case I have to resume

Phases 1, 2, 2.5, 3, 4, and 5 are all code-complete. Phase 6 (py2app bundling) build script is ready — Chad needs to run `Build App.command` and report whether the .app builds and runs correctly. Carbon-fiber background and custom icon are deferred to a final polish pass.

Current `app/` layout:
- `csv_router.py` — auto-detect Garmin vs BallisticX from CSV content
- `main.py` — the PyQt window + main() entry point
- `config.py` — load/save config + auto-detect existing project folders
- `setup_wizard.py` — first-run dialog
- `updater.py` — background update check
- `version.py` — APP_VERSION + TEMPLATE_VERSION constants

`Test Cold Bore.command` is the dev launcher — installs PyQt5 if needed and runs `app/main.py`. Will keep working through Phase 5; gets replaced by a proper `.app` bundle in Phase 6.

`import_data.py` was refactored: `run_import(workbook_path, project_dir, open_excel)` and `list_workbooks(project_dir)` are now public, while `main()` keeps the CLI flow working unchanged for Chad's existing Desktop `.command`.
