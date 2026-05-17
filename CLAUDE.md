# Loadscope — context for Claude

## 🔴 OBEY EVERY TURN — the rules that get "saved but not read" (do NOT skip)

1. **Box every ask.** Anything you need from Chad (decision/answer/choice/approval/action) goes in a `> ⚠️ **YOUR TO-DO**` blockquote, every line bold — it fires his phone. No box = no ask. Never a soft "let me know".
2. **Do it yourself, end-to-end.** Incl. the build (`open "Build App.command"`), R2 upload, and install self-test. Don't delegate what a tool can do; no mid-flow "go check this".
3. **Investigate → recommend → act once.** Find the existing mechanism before building a new one; audit your own output before sending; never lead Chad through a chain of pivots.
4. **No per-fix releases pre-beta.** Website work stays on a branch off `main` until Chad explicitly says "publish" (`docs/` publishes from `main`).
5. **Marketing/website copy:** precision-rifle vernacular, never corny. Banned: *node, "before you leave the truck", truer, come-ups, graded*. Lead with **best-load**. Offer options. Chad reviews in the **browser** (not the preview panel).
6. **Always recommend** when offering choices; explanations for Chad's steps at a 5th-grade level; end work with an explicit "done / ready" signal.

Full rationale: the `READ EVERY SESSION` memories in MEMORY.md + the sections below. If these conflict with old prose below, **these win**.

---

You're working on **Loadscope**, Chad Heidt's PyQt5 Mac desktop app for precision rifle load development. CSV imports from Garmin Xero (chronograph) and BallisticX (target groups) feed an Excel workbook with scoring formulas. Distributed as a single .app bundle to a small group of friends. In-app auto-updates via custom Python+bash installer.

## Read these first (every session)

1. **`Notes for next session.md`** — current state, recent decisions, lessons learned. Always read the top section first; older sections below are kept as historical context.
2. **`Build progress.md`** — phase-by-phase build history, deferred items, future-work plans (Phases 7/8/9).

These two files are the source of truth. They override anything that conflicts in this CLAUDE.md.

## Live marketing site

**https://chadheidt.github.io/coldbore/** (also `Loadscope Website.webloc` at project root for one-click open from Finder).

GitHub Pages serves from `docs/` on `main`. Hero images are rendered programmatically via `tools/render_workbook.py` and `tools/render_loadscope.py` — re-run those when the in-app drop zone or workbook layout changes so the marketing imagery stays accurate.

## How Chad and Claude work together

Chad is a precision rifle shooter, **not** a software developer. The collaboration pattern:

- **Claude does the file edits and shell commands.** Use the tools directly — don't make Chad copy-paste.
- **Claude self-drives the build AND the install** (proven 2026-05-16): build via `open "Build App.command"` (LaunchServices = the same path a Finder double-click uses; escapes the provenance EPERM), and self-test the auto-update by driving `installer._build_helper_script` against `/Applications`. **Chad's hands are genuinely needed only for**: actions requiring his Apple ID / keychain / an interactive auth dialog, credentials he must generate in a dashboard, or his product/brand judgment. The build and the install are NOT Chad's job anymore.
- Be efficient. Don't over-explain. Reserve walkthroughs for browser/Finder steps.
- For releases, always edit version strings in three files in lockstep: `app/version.py`, `setup.py`, `manifest.json`.

## Build & release procedure (the proven path)

1. Edit `app/version.py`, `setup.py`, `manifest.json` to the new version (ASCII only).
2. Commit + push to `main`.
3. **Claude builds it (do NOT delegate to Chad):** `open "/Users/macbook/Projects/Loadscope/Build App.command"`. `open` launches it via LaunchServices — the *same* path a Finder double-click uses — so it escapes the `com.apple.provenance` EPERM that kills `bash "Build App.command"` / a direct `python3 setup.py py2app`. Poll for `dist/Loadscope.app`, wait for the `setup.py py2app` process to exit and the bundle size to stabilize, then bundle-verify (Info.plist `CFBundleShortVersionString`, the bundled `version.pyc`, key `Contents/Resources` assets).
4. Zip: `cd dist && ditto -c -k --keepParent "Loadscope.app" "Loadscope.zip"`, then `zip -j "Loadscope.zip" "../Loadscope — Quick Start.docx"`.
5. **MANDATORY — upload to R2 (the actual auto-update delivery; older CLAUDE.md omitted this and a ship nearly went out broken):** `cd /Users/macbook/Projects/Loadscope && npx --yes wrangler r2 object put "coldbore-releases/Loadscope.zip" --file=dist/Loadscope.zip --remote` (wrangler OAuth already set up). Also rebuild + `wrangler r2 object put` `Loadscope.dmg` for the website fresh-install path. The in-app updater downloads from this R2 bucket via the Cloudflare Worker — NOT from the GitHub release.
6. `gh release create vX.Y.Z --repo chadheidt/coldbore --title "Loadscope X.Y.Z" --notes-file <notes> --draft "dist/Loadscope.zip"` then `gh release edit vX.Y.Z --repo chadheidt/coldbore --draft=false --latest`. (`published` doesn't fire CI's `release: created` listener — no race.)
7. **Verify the whole chain before saying "shipped":** curl raw `manifest.json` (app_version correct) → POST Worker `/authorize` with Chad's test key `CBORE-DDCX-AEGK-J2FR-2SIB` body `{"code","file"}` → GET the returned signed URL = HTTP 200 + a valid ~70MB zip. Use **curl + a browser User-Agent** (the sandbox default UA gets Cloudflare-1010-blocked on `*.workers.dev`/`api.resend.com`). Brief R2→Worker propagation lag — a first GET can 404; re-test ~1 min before concluding it's broken.
8. Optional install self-test (no Chad needed): download via the real Worker path, then `installer._build_helper_script(zip, "/Applications/Loadscope.app", errlog)` → run it → confirm `/Applications` flips version and the error log is empty. Chad's only optional glance: open it from `/Applications` and eyeball.

## Things that have bitten us before (read once)

- **Don't put non-ASCII (em-dashes, curly quotes, etc.) in commit messages, the helper bash script in `installer._build_helper_script`, or asset filenames.** Python 3.9 default ASCII encoding on file writes has crashed builds.
- **GitHub renames release-asset filenames** — `Loadscope.zip` → `Loadscope.zip` (spaces → periods). Manifest URLs must use the period form.
- **Stick with `macos-13` Intel CI runner** (or local Build App.command). `arch = 'universal2'` produces broken bundles because PyQt5 wheels go arm64-only.
- `can_self_install()` returns False for the **dev process only** — the real `/Applications/Loadscope.app` IS self-testable by driving `installer._build_helper_script` against it (proven 2026-05-16). Still can't be tested from `dist/`.
- **The release MUST include the R2 upload (step 5).** The auto-updater serves the zip from the `coldbore-releases` R2 bucket via the Worker, not the GitHub release. Skip it and the manifest says "update available" while R2 serves the old build = broken update. Caught 2026-05-16 only by end-to-end verification — always do step 7.

## Common requests Chad makes

- "Ship Loadscope vX.Y.Z with [list of changes]" → run the procedure above.
- "I got a bug report from a friend" / "here's a crash log" → read traceback, fix in the right module, write or update a test in `tests/`, bump patch version, ship. Reference: `Handling Bug Reports.md`, `Handling Crash Reports.md`.
- "Let's start the iOS port / Windows port" → Build progress.md has full plans for Phase 8 (iOS) and Phase 7 (Windows).
- "Where's the link for friends?" → `Send Loadscope to friends.md` at project root.

## What NOT to do without asking

- **Don't push to `main` without confirmation** when the change is non-trivial. (Version bumps and breadcrumb updates as part of an explicit release flow are pre-authorized.)
- **No per-fix releases pre-beta.** Zero users/testers yet → batch all release ceremony into the beta-launch release; routine fixes just commit/push `main` + keep tests green. Website/workbook changes get a Chad **review checkpoint** (open a rendered preview / the file for him), not a release. Revisit cadence when real users exist. (See memory `project_release_review_cadence`.)
- **GitHub Pages publishes `docs/` from `main`.** In-progress website work must stay off `main` (park on a branch) until Chad explicitly says "publish" — committing/pushing `docs/` to `main` = it goes live.
- **Don't delete or rename project files / folders** without asking. Especially `Rifle Loads Template (do not edit).xltx` and the import folders.
- **Don't move the project folder out of `~/Projects/Loadscope`.** Config and `.command` launchers have the path baked in.
- **Don't put the project folder back into iCloud.** It used to be there; we moved it out specifically because iCloud was breaking the .git/ directory.
