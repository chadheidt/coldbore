# Cold Bore — context for Claude

You're working on **Cold Bore**, Chad Heidt's PyQt5 Mac desktop app for precision rifle load development. CSV imports from Garmin Xero (chronograph) and BallisticX (target groups) feed an Excel workbook with scoring formulas. Distributed as a single .app bundle to a small group of friends. In-app auto-updates via custom Python+bash installer.

## Read these first (every session)

1. **`Notes for next session.md`** — current state, recent decisions, lessons learned. Always read the top section first; older sections below are kept as historical context.
2. **`Build progress.md`** — phase-by-phase build history, deferred items, future-work plans (Phases 7/8/9).

These two files are the source of truth. They override anything that conflicts in this CLAUDE.md.

## How Chad and Claude work together

Chad is a precision rifle shooter, **not** a software developer. The collaboration pattern:

- **Claude does the file edits and shell commands.** Use the tools directly — don't make Chad copy-paste.
- **Chad does the things that genuinely require his hands**: double-clicking `Build App.command` from Finder, clicking through GitHub release pages (rare now that we use `gh`), installing the .app to `/Applications`, testing the auto-update from `/Applications`.
- Be efficient. Don't over-explain. Reserve walkthroughs for browser/Finder steps.
- For releases, always edit version strings in three files in lockstep: `app/version.py`, `setup.py`, `manifest.json`.

## Build & release procedure (the proven path)

1. Edit `app/version.py`, `setup.py`, `manifest.json` to the new version.
2. Commit + push to `main`.
3. Have Chad **double-click `Build App.command` from Finder** (NOT `python3 setup.py py2app` from a Bash tool — that path fails with EPERM on the bundled Python framework due to a `com.apple.provenance` xattr; only Build App.command from Finder works).
4. Once `dist/Cold Bore.app` exists, zip via `ditto -c -k --keepParent "Cold Bore.app" "Cold.Bore.zip"`, then add the Quick Start docx via `zip -j "Cold.Bore.zip" "../Cold Bore — Quick Start.docx"`.
5. `gh release create vX.Y.Z --repo chadheidt/coldbore --title "Cold Bore X.Y.Z" --notes-file <notes> --draft "dist/Cold.Bore.zip"`.
6. `gh release edit vX.Y.Z --repo chadheidt/coldbore --draft=false --latest` to publish. The `published` event doesn't fire CI's `release: created` listener, so there's no race against manual asset attach.
7. Chad opens Cold Bore from `/Applications` → yellow banner → Install Update → Quit and Install → app reopens at new version. Tools → About reports new version.

## Things that have bitten us before (read once)

- **Don't put non-ASCII (em-dashes, curly quotes, etc.) in commit messages, the helper bash script in `installer._build_helper_script`, or asset filenames.** Python 3.9 default ASCII encoding on file writes has crashed builds.
- **GitHub renames release-asset filenames** — `Cold Bore.zip` → `Cold.Bore.zip` (spaces → periods). Manifest URLs must use the period form.
- **Stick with `macos-13` Intel CI runner** (or local Build App.command). `arch = 'universal2'` produces broken bundles because PyQt5 wheels go arm64-only.
- **Auto-update test must run from `/Applications`**, not `dist/`. `can_self_install()` returns False in dev mode.

## Common requests Chad makes

- "Ship Cold Bore vX.Y.Z with [list of changes]" → run the procedure above.
- "I got a bug report from a friend" / "here's a crash log" → read traceback, fix in the right module, write or update a test in `tests/`, bump patch version, ship. Reference: `Handling Bug Reports.md`, `Handling Crash Reports.md`.
- "Let's start the iOS port / Windows port" → Build progress.md has full plans for Phase 8 (iOS) and Phase 7 (Windows).
- "Where's the link for friends?" → `Send Cold Bore to friends.md` at project root.

## What NOT to do without asking

- **Don't push to `main` without confirmation** when the change is non-trivial. (Version bumps and breadcrumb updates as part of an explicit release flow are pre-authorized.)
- **Don't delete or rename project files / folders** without asking. Especially `Rifle Loads Template (do not edit).xltx` and the import folders.
- **Don't move the project folder out of `~/Projects/Rifle Load Data`.** Config and `.command` launchers have the path baked in.
- **Don't put the project folder back into iCloud.** It used to be there; we moved it out specifically because iCloud was breaking the .git/ directory.
