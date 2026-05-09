# Rifle Load Development — Project Context (read me first)

A handoff note so any future Claude session can pick up where we left off without re-deriving everything.

**Also read `Build progress.md`** — it tracks the in-progress GUI app build (phases 1–6).

---

## 🚧 v0.8.2 IN-FLIGHT — May 9, 2026 (universal2 build, first auto-update test)

**Updated approach over v0.8.1:** The macos-13 (Intel) runner approach in v0.8.1 hit GitHub free-tier queue saturation — 13+ minutes queued. v0.8.2 takes a different angle: build a **universal2** binary on `macos-latest` (which has fast queue availability). Universal2 binaries contain BOTH arm64 and x86_64 code in one bundle, so a single zip works natively on every Mac architecture without Rosetta 2.

**v0.8.2 changes from v0.8.1:**
- Reverted runner from `macos-13` back to `macos-latest`
- Added `"arch": "universal2"` to setup.py's py2app OPTIONS
- Workflow comment updated explaining the universal2 approach

**Why universal2 is the better long-term answer:**
- One zip, every Mac → no friend-distribution complexity
- Native performance on both architectures (no Rosetta 2 overhead on Apple Silicon)
- Future-proof: when GitHub eventually retires macos-13, this build path is unaffected
- Industry standard: universal2 is what professional Mac apps ship

**Prerequisites that must hold:**
- `actions/setup-python@v5` provides a universal2 Python on macos-latest (true as of 2026)
- PyQt5's universal2 wheels exist on PyPI (true for 5.15+ on Python 3.9+)
- openpyxl is pure Python (true — universal by definition)

**v0.8.1 status:** A v0.8.1 commit + tag + release exist locally but the CI run was stuck queued when we pivoted to v0.8.2. Either let it eventually complete (the resulting zip would be Intel-only, also functional) or just ignore it — v0.8.2 supersedes it. If anything's confused on GitHub, deleting the v0.8.1 release record is fine.

---

## 🚧 v0.8.1 (DEPRECATED) — May 9, 2026 (Intel runner fix)

**Where we left off:** Chad got v0.8.0 running locally (Build App.command on his Intel Mac) but **the v0.8.0 zip on GitHub Releases is Apple Silicon-only and crashes on Intel Macs.** This is because GitHub's `macos-latest` runner is now ARM64 by default in 2026, and produced an arm64-only py2app bundle. Chad has an Intel Mac (`uname -m` → `x86_64`) so the bundle exited immediately on launch with a swallowed PyQt5 ImportError.

v0.8.1 fixes this by switching CI from `macos-latest` to `macos-13` (Intel runner). Intel binaries run natively on Intel AND on Apple Silicon via Rosetta 2 (which ships with every Apple Silicon Mac), so a single Intel build covers both architectures. Performance impact for a small PyQt app is invisible.

**What's done in v0.8.1:**
- ✅ `.github/workflows/build-mac.yml` — both `test` and `build` jobs now `runs-on: macos-13`. Header comment explains why and points future-Claude at the universal2 alternative when macos-13 is eventually retired by GitHub.
- ✅ Version bumps to 0.8.1 in `app/version.py`, `setup.py`, `manifest.json`
- ✅ Release notes in manifest highlight the Intel fix

**What's pending — the release flow:**
1. Open GitHub Desktop. ~4 changed files (workflow, version.py, setup.py, manifest.json) plus this breadcrumb file.
2. Commit message: `v0.8.1 — CI fix: build on Intel runner so bundle works on every Mac`
3. **Commit to main → Push origin**.
4. Wait ~5 min for CI green. Note: the `test` job uses `macos-13` now too, which has slightly slower startup than `macos-latest` — first run may take longer than usual.
5. Create v0.8.1 release at https://github.com/chadheidt/coldbore/releases/new — direct publish, NOT draft.
6. Wait for `Cold.Bore.zip` to attach to the release.

**The big test: in-app auto-update.** Once the v0.8.1 release is live with its zip attached:

1. Chad opens his locally-built v0.8.0 Cold Bore (currently in /Applications)
2. Manifest reports v0.8.1 available → yellow banner appears with **Install Update** button
3. Chad clicks **Install Update** → banner shows download progress
4. When download done → banner shows **Quit and Install** button
5. Chad clicks → Cold Bore quits, helper script swaps in v0.8.1, Cold Bore reopens on v0.8.1
6. Tools → About reports v0.8.1, banner is gone

**Why this is the moment of truth:** v0.8.0 had the new in-app updater code but Chad was still running v0.7.0 when we tried to test it, so we got the OLD banner ("Download new version" → browser). Now Chad's running v0.8.0 locally, and v0.8.1 will be the first time his own machine sees the new "Install Update" button on a real update event.

**If the swap fails for some reason:** ~/Library/Application Support/Cold Bore/last_install_error.log will have the helper script's exit message. Next launch, Cold Bore reads that log and surfaces it via QMessageBox. Have Chad paste whatever it says.

**Friend distribution status:** Chad has NOT sent any zips to friends yet. So the broken v0.7.0/v0.7.1/v0.8.0 GitHub zips never reached anyone. Once v0.8.1 is live and verified, the zip on `releases/latest` will be Intel-binary (works on every Mac) and friend distribution can begin in earnest.

---

## ✅ v0.8.0 SHIPPED (locally) — May 9, 2026 (auto-update feature)

**Where we left off:** Chad and Claude built **Phase 12: in-app self-installer** in this session. Code is complete locally but **not yet committed/pushed/released**. v0.8.0 will be Cold Bore's first version with one-click in-app updates (Level 2 — see Build progress.md Phase 12 for full design and Phase 9 for the Sparkle/Level 3 plan when commercializing).

**What's done:**
- ✅ `app/updater.py` — added `UpdateDownloader(QThread)` (streams the .zip with progress signals, 500MB cap, 256KB-throttled progress emits)
- ✅ `app/installer.py` (NEW) — pure-Python module that builds and spawns the bash helper script that does the .app swap. Includes `can_self_install()`, `launch_install_swap()`, `consume_last_install_error()`. PyQt-free so it can be unit-tested without a display server.
- ✅ `app/main.py` — banner state machine (ready/downloading/installing/error), Install Update button, Quit and Install button, cancel handling, fallback to manual download link, surfacing of previous install errors at startup
- ✅ `setup.py` — added `installer` to py2app's `includes`, version bumped to 0.8.0
- ✅ `app/version.py` — `APP_VERSION = "0.8.0"`
- ✅ `manifest.json` — bumped to 0.8.0 with the v0.8.0 download URL (uses `Cold.Bore.zip` to match GitHub's space-rename behavior)
- ✅ `tests/test_installer.py` (NEW) — 7 tests covering script generation, dev-mode safety, consume-error log lifecycle
- ✅ Build progress.md — added Phase 12 section with design rationale, helper-script step list, banner state machine, known limitations
- ✅ Build progress.md — added Sparkle migration plan to Phase 9 (Path B / commercialization checklist)

**What's pending — the release flow:**
1. Open GitHub Desktop. You should see ~9 changed files (4 .py edits, 1 new installer.py, 1 new test_installer.py, manifest.json, setup.py, Build progress.md, Notes for next session.md).
2. Commit message: `v0.8.0 — in-app self-installer (Phase 12)`
3. Click **Commit to main** → **Push origin**.
4. Wait ~5 min for CI green at https://github.com/chadheidt/coldbore/actions
5. Create the v0.8.0 release at https://github.com/chadheidt/coldbore/releases/new — **DO NOT save as draft**, use the green Publish release button directly so the `release: created` event fires for CI's asset-attach step. (See lessons-learned in this file.)
6. After ~5 min, verify `Cold.Bore.zip` is attached to the v0.8.0 release.
7. **Test the auto-update flow on Chad's Mac.** He's still running v0.7.0, so opening Cold Bore will show the new banner. Click **Install Update**, watch the download progress, click **Quit and Install** when ready. Cold Bore should close, the helper script should swap in v0.8.0, and Cold Bore should reopen on v0.8.0. The Tools → About dialog should now report v0.8.0.
8. **Acceptance criteria for v0.8.0**: a clean install-update-relaunch cycle with no Gatekeeper warnings on the relaunch (because the helper strips the quarantine xattr).

**Edge cases to watch for during the v0.8.0 test:**
- Helper script's `sleep 3` should be enough for parent quit. If the swap fails because Cold Bore is still alive, we'd see a "Couldn't move old app aside" error — bump the sleep.
- If Chad's Cold Bore is in `/Applications/` and that's not writable for some reason (rare), `can_self_install()` returns False and the banner falls back to "Or download manually" — still works, just no one-click.
- The helper script writes errors to `~/Library/Application Support/Cold Bore/last_install_error.log`. Next launch surfaces them via QMessageBox. If anything goes wrong, that's the place to look.
- If something REALLY goes wrong and Cold Bore can't relaunch after the swap, Chad can manually re-install: download `Cold.Bore.zip` from https://github.com/chadheidt/coldbore/releases/latest, drag into Applications.

---

## ✅ v0.7.1 SHIPPED — May 9, 2026

**Status: pre-beta complete. Chad is cleared to share Cold Bore with friends.**

**What's live:**
- v0.7.0 and v0.7.1 both published at https://github.com/chadheidt/coldbore/releases
- v0.7.1 is set as **Latest**, has the workflow change that bundles `Cold Bore — Quick Start.docx` into `Cold Bore.zip` alongside the .app
- Verified by Chad: downloading the zip from the release page yields both the .app AND the Quick Start docx
- The shareable link friends should use: **https://github.com/chadheidt/coldbore/releases/latest** (always points at newest release)

**The friend-sharing reference doc** lives at the project root: `Send Cold Bore to friends.md`. It has the link, copy-paste-ready text/email messages, common questions, and a running version history. **When Chad asks "where's the link to send to friends," point him there.**

### gh CLI (still deferred)

Chad started exploring `brew install gh` + `gh auth login` so future releases can be one-liners (`gh release create v0.X.Y --title "..." --notes "..." --latest`) instead of clicking through the website. Never finished the install. Not blocking — next time he does a release, ask if he wants to set this up first or just push through with the manual flow again.

### Lessons learned from v0.7.1's release flow (read before next release)

The v0.7.1 release got messy because Chad and the previous Claude weren't on the same page about what was already done. Specifically:

1. **The breadcrumb said "NOT pushed" but the commits were already on GitHub.** Always verify actual state with `git log origin/main..HEAD --oneline` and a fetch from the public release page before trusting a breadcrumb.
2. **A v0.7.1 release was created as a Draft early in the session (before the breadcrumb was written), and a v0.7.1 git tag had been pushed.** The next session's "create release" form rejected v0.7.1 as a duplicate tag, then offered to "edit existing notes" — which led Chad to a pre-existing release record. Confusing.
3. **GitHub's `/releases` page is cached for ~1-2 minutes** after a release is published. The direct tag URL (`/releases/tag/v0.7.1`) refreshes immediately. When verifying a fresh publish, prefer the tag URL.
4. **Chad got confused about CI vs releases.** He saw a green check on the Actions page after pushing and assumed that meant the release was published. It wasn't — CI runs on every push, not just releases. Be explicit about this distinction in walkthroughs.
5. **GitHub renames release assets with spaces.** Cold Bore's CI uploads `Cold Bore.zip`, but GitHub stores it as `Cold.Bore.zip` (spaces → periods). The first manifest had `Cold%20Bore.zip` (URL-encoded space) and 404'd in the in-app banner. Fix was changing manifest URL to `Cold.Bore.zip`. **Going forward, either the workflow's zip step should produce a no-spaces name (`ColdBore.zip` or `Cold.Bore.zip`) directly so the rename never happens, OR future manifest URLs should always use the period form. Pick one and document it.** The breadcrumb actually mentioned this gotcha from v0.6.0 days but it didn't get applied to the manifest. Next time we ship a new release: either fix the workflow filename, or bake "use periods, not spaces, in the manifest URL" into the release procedure.

**Future-Claude checklist before walking Chad through a release:**
- [ ] Run `git log --oneline -10` and `git tag -l` locally to see what commits and tags actually exist
- [ ] Web-fetch `https://github.com/chadheidt/coldbore/releases/tag/v0.X.Y` BEFORE assuming the release doesn't exist
- [ ] Check `git log origin/main..HEAD` to see unpushed commits, and `git ls-remote --tags origin | grep v0.X.Y` to see if the tag is on GitHub (note: this needs Chad's network — sandbox can't reach GitHub directly via git)
- [ ] If a tag already exists, the "create new release" form will show it in the dropdown. SELECT it instead of trying to create a new tag of the same name
- [ ] If a release already exists as a Draft, finish publishing it via the existing record — don't try to re-create
- [ ] After CI finishes the release build, **verify the asset filename on the release page matches what's in `manifest.json`**. GitHub renames spaces to periods. Check `https://github.com/chadheidt/coldbore/releases/download/v0.X.Y/<exact-filename>` resolves before declaring victory.

---

---

## 🟧 When you come back (note to Chad, not Claude)

If it's been weeks or months since you worked on Cold Bore and you're not sure how to pick up — read this section first. It's written for you, not for Claude.

### How to resume

1. Open **Cowork** (the Claude desktop app).
2. Make sure it's pointed at your project folder: `~/Projects/Rifle Load Data`.
3. Type or paste this exact phrase to start:

> **"Continue building Cold Bore. Read Notes for next session.md and Build progress.md to catch up."**

Claude will read both files (about 30 seconds) and have full context of where the project stands. From there, ask whatever you need — "I want to add a LabRadar parser," "let's fix this bug," "let's start the iOS app," whatever.

### Quick sanity check before you start work

Run through these to make sure nothing rotted while you were away:

1. **Cold Bore.app still launches** — open from Applications → does the window appear?
2. **Update check works** — Tools → Check for Updates… → should say "you're up to date" (or show an available update if you've shipped a newer version since)
3. **Build still works** — double-click `Build App.command` → should succeed and produce a fresh `dist/Cold Bore.app`
4. **Tests still pass** — double-click `Run Tests.command` → should be all green
5. **GitHub still has your repo** — visit `https://github.com/chadheidt/coldbore` → code is there

If any of those fail, that's the first thing to fix. Tell Claude: "this step is failing, here's the error" and paste whatever you see.

### Things that could break over time

| What might go wrong | Symptom | Fix |
|---|---|---|
| macOS update broke Python paths | `.command` files do nothing or error | Re-run `Build App.command` — sometimes pip needs to reinstall packages |
| PyQt5 / openpyxl outdated | Tests fail or app crashes on launch | `pip install --upgrade --user PyQt5 openpyxl` |
| GitHub Actions deprecated | CI red X with "Node.js 20 deprecated" or similar | Tell Claude — usually a one-line fix in `.github/workflows/build-mac.yml` |
| Garmin or BallisticX changed CSV format | Imports fail with "no parser detected" or weird values | Send Claude a sample of the new CSV, we update the parser |
| Friends say their app stopped checking for updates | Manifest URL might have moved | Check that `https://raw.githubusercontent.com/chadheidt/coldbore/main/manifest.json` opens in browser |

### Where things live (refresher)

- **Your project folder**: `~/Projects/Rifle Load Data` — code, workbooks, breadcrumbs
- **Your config**: `~/Library/Application Support/Cold Bore/config.json` — auto-update preferences, project folder pointer
- **GitHub repo**: `https://github.com/chadheidt/coldbore` — public, releases, manifest
- **Support email**: `coldboreapp@gmail.com` (forwards to your personal Gmail)

### Important: project was moved out of iCloud (May 2026)

The project folder used to live at `~/Documents/Claude/Projects/Rifle Load Data`, which was synced to iCloud Drive via macOS's "Documents & Desktop" feature. That caused two real risks:

1. iCloud's "Optimize Mac Storage" feature could evict local copies of files we hadn't touched recently, which would silently break builds and tests.
2. iCloud sometimes scrambled the `.git/` directory (sync conflict files in git's internal metadata), which can corrupt the local repo.

So we moved the folder to `~/Projects/Rifle Load Data` (a non-iCloud location) and updated all the path references:

- `import_data.py` `PROJECT` constant
- `app/config.py` `CANDIDATE_LEGACY_LOCATIONS` list (new path is now first)
- All `.command` launcher files (Build / Test / Generate Icon / Run Tests / Test Update URL / Clean Up Old App)

The config auto-migrates on first launch after the move because the old path no longer exists, so `get_project_folder()` falls back to the legacy locations list and finds the folder at the new path.

**Don't put it back in iCloud.** GitHub already provides versioned backup for the code. For the workbooks/CSV data, recommend Time Machine backups to an external drive instead of iCloud.

### Things to avoid

- **Don't delete the project folder** even if you stop using Cold Bore. Coming back from "I have the .app and GitHub but not the source" is much harder than starting cold.
- **Don't move the project folder** without telling Claude. The config has the path baked in. (If you do move it, just tell Claude — easy to update.)
- **Don't lose the GitHub login** — if you forget your GitHub password, recovery is annoying. Save it in your password manager now if you haven't.

### Once a year ritual (recommended)

Even if you have no changes to ship, run `Build App.command` once a year. If it fails, fix it then — when there's no pressure. The fix is usually one line. Letting failures pile up makes resuming much harder.

### Tool choice: Cowork vs Claude Code

Cold Bore was built using **Claude Cowork** (the desktop app) and that's what you should keep using. The other option — **Claude Code** (terminal-based CLI) — would be faster for pure coding work but loses Cowork's friendly UX, drag-and-drop file picker, plugin system, and the ability to mix code work with productivity tasks (Word docs, Excel, etc.).

You're not a developer. You value friendly explanations and clear next steps. Cowork fits that perfectly. The pace we've been working at — shipping releases monthly or so — doesn't need Claude Code's speed.

**Stick with Cowork unless one of these happens:**
- You're doing long debugging sessions where the sandbox round-trip starts to feel slow
- You want to run dev servers locally and watch them in real time
- Cowork stops working on a platform you need (e.g., if Cowork-for-Windows ever has issues during the Phase 7 port)

If any of those happens, Claude Code is the upgrade path — same Anthropic backend, just a more developer-focused interface. The project's breadcrumbs and conventions are tool-agnostic; both would understand Cold Bore the same way.

### To ship a new version

**Easiest path: come back here and ask Claude to walk you through it.** The release procedure has a few finicky steps (version bumps in two files, manifest URL update, GitHub release creation) and Claude can do most of the file editing for you. Sequence:

1. Tell Claude: "I want to ship Cold Bore v0.X.0 with [list of changes]"
2. Claude bumps version in `app/version.py` and `setup.py`, asks you to commit + push
3. Claude walks you through creating the GitHub release in the browser
4. CI auto-builds and attaches the zip (~3-5 min)
5. Claude updates `manifest.json` with the new version + URL, asks you to commit + push that
6. Done — friends' apps see the update on next launch

Each step where Claude does file editing replaces a manual step you'd otherwise have to do. Total time: 10-15 minutes including chat back-and-forth. Roughly half what it'd take solo, with no risk of forgetting to bump one of the two version files.

**Backup path if Claude isn't available**: see **`Cold Bore — How to Send Out Updates.docx`** in the project folder. Step-by-step in 5th-grade English.

---

### 📌 Note for future Claude (read carefully)

Chad's preferred mode of operation: **he comes back here for help on updates and changes** rather than doing them solo from the docs. Default to "helper mode" — when he asks for an update, walk him through it interactively, do the file edits yourself via the Edit tool, and only have him click buttons in GitHub Desktop / browser that require his hands.

Don't dump the "How to Send Out Updates" doc on him as the answer. The doc is the backup for emergencies. Default workflow is collaborative.

The `app/version.py` and `setup.py` version-bump in particular is something he should never have to do manually — that's two files that have to stay in sync, easy to forget one. Always do that for him.

**Bug report and crash report workflow** — same pattern. Chad will paste:
- A user's email containing a Python traceback (from the in-app crash reporter), OR
- A user's verbal description of a bug + activity log text

Read the traceback or the log carefully. Identify the offending code path. Fix it in the appropriate file. Write or update a test in `tests/` that would have caught it. Bump the version (patch release for bug fixes — `0.6.0` → `0.6.1`). Walk Chad through commit + push + create release. Detailed playbooks for him to reference are in `Handling Crash Reports.md` and `Handling Bug Reports.md`.

---

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
| `help_dialog.py` | Tools → How to Use Cold Bore… UI (label format, workflow, workbook-tab guide, 3-load minimum, safety reminder). Non-modal so users can keep it open while they work. First menu item in Tools for discoverability. |
| `new_cycle_dialog.py` | Tools → Start New Cycle… — checkbox wizard for archiving current workbook + CSVs and starting fresh. |
| `welcome_tutorial.py` | First-launch multi-step welcome tour. 6 cards covering basics. Tracked via `tutorial_seen_version` config; bump `TUTORIAL_VERSION` to re-prompt returning users. |
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

**GUI app build (v0.7.0 IN CODE; v0.6.0 currently SHIPPED. See `Build progress.md` for phase details):**
- Phase 1 ✅ — PyQt5 drop-target window with CSV auto-detection
- Phase 2 ✅ — Drops copy into the right folder; Run Import button triggers import; Excel opens
- Phase 3 ✅ — First-run wizard + persistent config; auto-detects existing project folders
- Phase 4 ✅ — Background update check + manual "Check for Updates" menu + yellow banner notification + GitHub Actions CI/CD live
- Phase 5 ✅ — Visual styling pass (dark/orange theme; carbon-fiber background still deferred)
- Phase 6 ✅ — py2app bundle shipping (Cold Bore.app at v0.6.0)
- Phase 6.5 ✅ — Pluggable parser registry (Garmin Xero + BallisticX, more pluggable in)
- Phase 6.7 ✅ — Drag-on-Dock-icon support
- Phase 10 ✅ — Polish round (workbook lockdown, validation, backups, settings panel, load card, load sharing, crash reporter, multi-workbook switcher, tests)
- Phase 11 ✅ — UX polish round / v0.7.0 (workbook state on launch, tooltips, larger window with state-saving, Tools-menu banner, Tools→Run Import Now / Restore From Backup / Start New Cycle, macOS notifications, CSV preflight check, confirm-on-quit, first-launch tutorial)
- Open: Quick Start guide for friends (next gating item before broader sharing)
- Open: Carbon-fiber background (still disabled, needs reference image)
- Open: Ship v0.7.0 release on GitHub (build, tag, CI auto-attach, update manifest.json)
- Future: iOS port (Phase 8), Windows port (Phase 7), commercialization (Phase 9)

## Likely future requests / open ideas

- **iOS port (Phase 8)** — Chad wants to build this with Claude eventually. Full collaboration plan is in `Build progress.md` under "Future: iOS app (Phase 8)". Has timeline, division of labor, architectural decisions, and recommended first move (4-6 hour prototype). When Chad says "let's start the iOS app", read that section.
- **Sales / commercialization (Phase 9)** — Chad is interested in eventually selling Cold Bore. Full commercialization plan in `Build progress.md` under "Future: Sales readiness (Phase 9)" — Path A (low-effort tip jar / wait for signal) and Path B (full commercialization with LLC, trademark, lawyer, App Store, etc.). Year-1 revenue range: $0–60k depending on path and luck. When Chad says "let's commercialize" or "let's start selling", read that section.
- If Chad ever upgrades Excel to 365, we could rebuild on Power Query for a cleaner one-click-from-Excel UX.
- Charts on the Charts tab could be expanded once Chad has run more cycles.
- The Ballistics tab DOPE entry is still manual — could potentially auto-fill from confirmed loads if he wants.
- Composite scoring weights (SD vs group vs vertical) are tunable in the formulas if he wants to bias differently.

---

## Quick "where do I look" map for future Claude

After the parser-registry refactor (Phase 6.5) the parsing logic moved from `import_data.py` into the `app/parsers/` package. The map below reflects current locations:

- **Label parsing** → `parse_label()` in `app/parsers/_common.py`. Shared helper used by all parsers.
- **Locale-aware number parsing** → `extract_inches()` and `extract_signed()` in `app/parsers/_common.py`. Handles US (1,234.56) and European (1.234,56) decimal formats.
- **Garmin Xero parser** → `app/parsers/garmin_xero.py`. Title on line 1 of the CSV, per-shot rows have integer in col 1 + velocity in col 2, stat rows have keyword in col 1 + value in col 2.
- **BallisticX parser** → `app/parsers/ballisticx.py`. Standard `csv.DictReader`, one row per group. Filename-as-label routing logic at the top of `parse()`.
- **Parser registry / detection** → `app/parsers/__init__.py`. `ALL_PARSERS` list, `detect_parser()`, `parser_by_key()`. Adding a new parser = drop a module here + add it to `ALL_PARSERS`.
- **Workbook discovery** → `list_workbooks()` and `find_workbook()` in `import_data.py` (around line 200). Multi-file prompt is in `find_workbook()` for CLI flow; GUI uses the picker.
- **Safety stop** (no CSVs found) → `run_import()` in `import_data.py` (around line 350).
- **Validation** → `_validate_chronograph_record`, `_validate_group_record`, `_check_duplicate_tags` in `import_data.py` (around line 130).
- **Workbook backup before import** → `_rotate_workbook_backups()` in `import_data.py` (around line 200).
- **Hidden sheet writers** → `write_chronograph_records()` and `write_group_records()` in `import_data.py` (around lines 270 and 320). Sheet names are still `GarminSessions` and `BallisticXGroups` for backwards compatibility, but the writers are source-agnostic now.
- **GUI main loop** → `app/main.py`. `MainWindow` class, drop handler, Tools menu, settings + load card + load sharing + crash reporter all wired in here.
- **Update check** → `app/updater.py` (`UpdateChecker(QThread)` + `DEFAULT_MANIFEST_URL`).

If you (future Claude) need to change CSV parsing, the parser modules are independent — adding a LabRadar parser is a new file + one line in `app/parsers/__init__.py:ALL_PARSERS`. No other code changes needed; the GUI and import script auto-discover via the registry.

When working with the workbook itself, remember:
- `wb.template = False` before save (avoids the template content-type bug)
- Use cell-range refs (`$A$2:$A$200`) not structured table refs (Excel 2016 incompatible)
- Don't put formulas in the cells the import script writes to (hidden sheets); formulas live on the visible tabs.
- **Hide-zero formula pattern**: when a cell pulls from `'Garmin Xero Import'!XYZ` or `'BallisticX Import'!XYZ`, always use `=IF(OR('Sheet'!XYZ="",'Sheet'!XYZ=0),"",'Sheet'!XYZ)` — NOT just `=IF('Sheet'!XYZ="","",'Sheet'!XYZ)`. The OR-check on 0 is required because Excel's LOOKUP returns 0 when the source cell is empty (a quirk of LOOKUP), and we don't want unused shot cells / unfilled rows to display as 0. The patch script that fixed this everywhere is `outputs/patch_zero_display.py` (run once, sets all matching cells correctly). If you add a new column or row to Load Log / Seating Depth that pulls from the import sheets, follow the OR-pattern from the start.

The scoring math itself is NOT affected by the 0-display issue, because Avg/SD/ES are pulled from Garmin's pre-computed values (which Garmin computes correctly over however many shots the user actually fired). Individual shot cells (C-G on Load Log, D-H on Seating Depth) are display-only — they don't feed into any formula on the Charts sheet.
