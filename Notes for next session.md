# Rifle Load Development — Project Context (read me first)

A handoff note so any future Claude session can pick up where we left off without re-deriving everything.

**Also read `Build progress.md`** — it tracks the in-progress GUI app build (phases 1–6).

---

## 🚧 v0.12.0 IN FLIGHT — May 11, 2026 (evening — request-access automation + branding)

**Branch: `v0.12-request-access`** (commit `1ece18f` and beyond). Main is still at proven v0.11.3.

The work in flight is a Cold Bore → True Zero brand rename PLUS a full request-access automation
pipeline: website form → Cloudflare Worker → Chad's gmail with Approve/Deny buttons → Resend emails
the tester their assigned beta-key. Domain `truezero.co` was bought through Cloudflare's registrar
during this session.

**STATE FILE LIVES AT `~/Documents/True Zero - v0.12 setup state.md`** (outside the project tree,
not in git, contains API tokens + IDs + step-by-step where we left off). If VS Code crashes
mid-flight, that file is the source of truth for resuming.

Quick status snapshot:
- ✅ `truezero.co` active in Cloudflare
- ✅ `BETA_REQUESTS` KV namespace created (`a0362498a5c74b1eb124decdb011f41c`)
- ✅ ADMIN_TOKEN generated
- ✅ All file changes committed to `v0.12-request-access` branch
- ⏳ Cloudflare Turnstile widget (token lacks Turnstile:Edit scope)
- ⏳ Resend domain verification (API key restricted to sending only)
- ⏳ Worker env vars (6 needed) not yet set
- ⏳ New Worker source not yet deployed
- ⏳ App version 0.12.0 committed but not yet built/signed/shipped

The `dcd344f` "v0.11.3 SHIPPED" notes below remain the authoritative breadcrumb for what's
actually in production right now.

---

## ✅ v0.11.3 SHIPPED + AUTO-UPDATE PROVEN — May 11, 2026 (afternoon — beta-ready closeout)

**True Zero is genuinely ready for beta distribution.** Every loose thread we identified is closed:

- Auto-update path verified end-to-end on Chad's machine (v0.11.2 → v0.11.3 via the yellow banner; Worker-gated download, ditto-based swap, signed/notarized relaunch, Tools → About now reports 0.11.3)
- 10 beta-key slots pre-generated and registered in BOTH `app/license.py`'s `VALID_KEYS` AND the Cloudflare Worker's `VALID_CODES`. Issuing a key to a new tester no longer requires an app rebuild — just pick the next unassigned slot from `beta-keys.txt`, record the recipient, email them
- Pyflakes smoke test added (`tests/test_main_smoke.py`) — would have caught yesterday's NameError in 0.5 seconds. `Run Tests.command` auto-installs pyflakes alongside pytest
- `True Zero — How to Issue License Keys.docx` on Chad's Desktop (`~/Desktop/True Zero app/cold bore notes/`) rewritten to reflect the simpler "pick a pre-generated key" workflow. Original backed up at `/tmp/True Zero - License Keys doc - BEFORE 2026-05-11 update.docx` (will vanish on reboot)
- Worker source in the Cloudflare dashboard has one batch of duplicate key entries from the manual-paste step (Set dedupes them at runtime so functionally fine). Backup at `worker/coldbore-download.js` is the clean version — if Chad ever wants to tidy the live source, copy that file into the dashboard editor and redeploy

### State on Chad's machine right now

- `/Applications/True Zero.app` runs **v0.11.3** (auto-updated from v0.11.2, no manual intervention needed beyond the click)
- `main` HEAD: `8d9c9c8` ("v0.11.3 - five more beta-key slots; the auto-update closeout build")
- Working tree clean except untracked `True Zero.app alias` (gitignored)
- R2 holds v0.11.3 `Cold.Bore.dmg` (55M) and `Cold.Bore.zip` (58M)
- 11 keys total in `app/license.py` + Worker `VALID_CODES`: Chad's local testing key + 10 unassigned beta slots
- `beta-keys.txt` mirrors the 11 keys; top of the file calls out the "key must live in BOTH license.py AND the Worker" rule

### Lessons that got baked in during the afternoon

- **`Build Signed App.command` had two long-standing bugs** that bit us on the FIRST build of the day, both already documented in the v0.9.0 lessons but never patched into the script. Both fixed now (commit `9e4b9fd`):
  - Build out-of-tree in `/tmp/coldbore-build/`. macOS attaches `com.apple.provenance` xattrs to files copied inside the project tree, blocking py2app from rewriting the bundled Python3 framework. Final `.dmg` + `.zip` copied back to `dist/` at the end.
  - Codesign EVERY Mach-O in the bundle, not just `.dylib`/`.so`. Old filter missed `Contents/MacOS/python` and `Contents/Frameworks/Python3.framework/Versions/3.9/Python3`. Apple's notary service rejected the whole submission citing them as adhoc-signed.
- **The auto-update path is the regression hotspot.** v0.11.0 shipped with a NameError caught only by today's controlled test bump (v0.11.1) on Chad's own machine. The pattern: anytime `app/updater.py` or `app/installer.py` changes, ship a test-bump release BEFORE assuming the change works. Cost: one ~15-min build+notarize cycle. Value: bug found on dev machine, not on five strangers'.
- **Settings change today: project-level `Bash(*)` + `Edit(*)` + `Write(*)` + `Read(*)`** in `.claude/settings.local.json` (gitignored). Chad asked mid-session because prompts were stacking up. User-level `~/.claude/settings.json` now also has a `Stop` hook playing Glass.aiff (same sound as the Notification + PermissionRequest hooks) so Chad hears a tone any time the agent finishes a turn and is waiting on him.

### What's pending after v0.11.3

- **Send the website link + a key to the first wave of pro-shooter beta testers.** This is the actual milestone. The two friends Chad already gave the public website link to may eventually ping for a key; per his earlier call, wait for the ping rather than proactively pushing.
- **Issue keys one at a time as people sign on.** Per the rewritten Desktop doc, the workflow is: pick next slot in `beta-keys.txt`, record recipient name + date, email them the key + website link. No code touched.
- **Once anyone hits v0.11.3 → vX.Y.Z auto-update on a non-Chad machine**, that's a real signal the system works in the wild. Until then, we have proof from Chad's machine but not from someone else's.
- **Phase 9 commercialization** (when ready): LLC, EULA, USPTO trademark, `coldbore.app` domain, Gumroad/Stripe, public launch.

### Next time we change `app/updater.py` or `app/installer.py`

Do the following BEFORE assuming the release is good:

1. Run `Run Tests.command` to confirm `tests/test_main_smoke.py` (the pyflakes check) passes — catches the NameError class of bug.
2. After the release ships to R2 and the manifest points at the new version, click Install Update on Chad's `/Applications/True Zero.app` and watch the full swap-and-relaunch happen. Confirm Tools → About reports the new version.
3. If anything fails at step 2, the helper script writes its error to `~/Library/Application Support/True Zero/last_install_error.log`, and the next launch of True Zero surfaces that via a popup. Paste the error here and we debug.

If you're tempted to skip this loop for "trivial" changes — don't. The v0.11.0 NameError was a two-character import bug and it still cost us four hours today.

---

## ✅ v0.11.2 SHIPPED — May 11, 2026 (morning — auto-update fix)

**v0.11.2 is on Chad's `/Applications/True Zero.app` right now.** Manually installed via the website .dmg flow (which means the same flow a real beta tester would use was just verified end-to-end). Tools → About reports 0.11.2.

### What happened (the short version)

We set out to do the one thing yesterday's breadcrumb flagged as untested: prove the in-app auto-update path on the new v0.11.0 stack. We shipped v0.11.1 as a trivial test-bump so v0.11.0 had something to update to. The test exposed a real, embarrassing bug in v0.11.0: clicking **Install Update** crashed with `NameError: name 'updater' is not defined` — `app/main.py:1167` called `updater.resolve_download_url(manifest)` but line 62's import was a `from updater import …` style that didn't bring the module name into scope. Yesterday's session never caught it because the code path was never exercised before shipping. **The test did exactly what we wanted: surfaced the regression on Chad's own machine before any beta tester saw it.**

v0.11.1 the binary is doomed — same bug as v0.11.0, just a version-string bump. We skipped past it in the manifest and shipped v0.11.2 with the actual fix. Chad's v0.11.0 in /Applications can't auto-update past the crash, so Chad did a one-time **manual install** of v0.11.2 via the website .dmg flow. Auto-updates from v0.11.2 forward should work, but **this has NOT been tested yet** — that test costs another build+notarize+upload cycle and we deferred it. First chance to verify: the next real release.

### Other lessons baked in during the morning

1. **`Build Signed App.command` had two long-standing bugs** that bit us on the first build attempt today, both already documented in the v0.9.0 lessons but never patched into the script. Both fixed now (commit `9e4b9fd`):
   - **Build out-of-tree.** py2app now writes into `/tmp/coldbore-build/` instead of the project's `dist/`. macOS attaches `com.apple.provenance` xattrs to files copied inside the project tree, blocking py2app/macholib from rewriting the bundled Python3 framework — manifests as `[Errno 1] Operation not permitted` during the changefunc phase. The .dmg + .zip get copied back to `dist/` at the end so downstream workflow steps (Finder open, R2 upload) are unchanged.
   - **Codesign every Mach-O, not just `.dylib`/`.so`.** The old find loop missed `Contents/MacOS/python` (a py2app-generated launcher) and `Contents/Frameworks/Python3.framework/Versions/3.9/Python3` (no extension to match). Both shipped adhoc-signed and Apple's notary service rejected the whole submission. New loop walks the entire bundle and asks `file -b` whether each entry is Mach-O. 249 binaries signed now.

2. **The auto-update path is the thing that always breaks silently.** Code is written, code compiles, tests pass, build succeeds, binary ships — and the failure only surfaces when a real running app actually tries to download a real update. The breadcrumb yesterday DID say "this is unproven" but the wording was buried. For future releases, anytime the updater or installer code changes, suggest a test-bump release (like v0.11.1 today) BEFORE assuming the change works. The cost is one extra 15-min build+notarize cycle; the value is finding the bug on Chad's machine instead of on five strangers' machines.

3. **Settings change today: project-level `Bash(*)` + `Edit(*)` + `Write(*)` + `Read(*)`** are now in `.claude/settings.local.json` (gitignored). Chad explicitly asked for "all bash commands" and "all write access" mid-session because the prompts were piling up. Future sessions in this project won't prompt for these.

### State on Chad's machine right now

- `/Applications/True Zero.app` runs **v0.11.2** (manually installed via .dmg from website, license key `CBORE-DDCX-AEGK-J2FR-2SIB` re-validated silently on launch)
- `main` HEAD: `4afd571` ("v0.11.2 - fix NameError in v0.11.0 auto-updater")
- Working tree clean except the untracked `True Zero.app alias` (already gitignored — see `ee1cc0a`)
- Cloudflare R2 holds `Cold.Bore.dmg` and `Cold.Bore.zip` for v0.11.2 (both replaced today; the broken v0.11.1 binaries that briefly existed there have been overwritten)
- Manifest on `main` says v0.11.2 with the fix release notes

### What's pending after v0.11.2

- **Verify auto-update v0.11.2 → vX.Y.Z works.** First chance is the next real release. Build it, ship it, watch Chad's v0.11.2 banner show up, click Install Update, confirm clean swap. If it fails, we'll have a real crash log this time (not a NameError) and we'll know what next layer of the stack is broken.
- **Add a smoke test for `app.main`'s import surface.** A test that does nothing but `import app.main` and walks the module's globals would have caught today's NameError in 0.5 seconds. Cost: ~20 lines in `tests/`. Worth doing in a quiet moment.
- **Issue keys + send the website link to beta testers.** v0.11.2 is the version that goes out. Use `~/Desktop/True Zero — How to Issue License Keys.docx`. **Remember the doc still needs updating** to mention that new keys go in TWO places: `app/license.py` AND the Cloudflare Worker's `VALID_CODES` set in the dashboard. Without the Worker update, a new tester would have a key that unlocks the app but can't download from the website.
- **Phase 9 commercialization** (when ready): LLC, EULA, USPTO trademark, `coldbore.app` domain, Gumroad/Stripe, public launch.

---

## ✅ v0.11.0 SHIPPED — May 10, 2026 (evening — private downloads via Cloudflare Worker)

**Beginning with v0.11.0, True Zero binaries are not available on GitHub.** Both the marketing `.dmg` and the auto-update `.zip` are served by a Cloudflare Worker (`coldbore-download.cheidt182.workers.dev`) that validates an access code server-side and returns a 5-minute signed URL pointing at Cloudflare R2 storage. Without a valid code there is no path to the binary, period.

### What was built tonight (after v0.10.1)

1. **Cloudflare R2 bucket `coldbore-releases`** holds the .dmg and .zip. R2 free tier: 10 GB storage + free egress. Current cost: $0/mo.

2. **Cloudflare Worker `coldbore-download`** at `https://coldbore-download.cheidt182.workers.dev`:
   - `POST /authorize { code, file }` — validates code, returns 5-min HMAC-signed URL
   - `GET /get/<file>?exp=&sig=` — verifies signature, streams file from R2 binding
   - VALID_CODES list lives in the Worker source (same key set as `app/license.py`'s `VALID_KEYS`)
   - HMAC_SECRET environment variable (encrypted) signs the URLs
   - R2 binding name: `BUCKET` → `coldbore-releases`
   - Source code: in Cloudflare dashboard's web editor (not in git — it lives in Cloudflare). If we ever want it in version control, copy/paste into a `worker/` folder and use `wrangler` to deploy.

3. **Website Download button (`docs/index.html`)** now opens a modal asking for the access code. Modal POSTs to the Worker; on success it redirects to the signed URL (browser downloads from R2). Old direct GitHub-release links are gone from the website.

4. **In-app updater (`app/updater.py` + `app/main.py`)** now uses `resolve_download_url(manifest)`:
   - For gated manifests (with `app_download_endpoint` + `app_download_file`): POSTs the user's saved `license_key` to the Worker, gets back a signed URL, downloads from there.
   - For legacy manifests (with `app_download_url`): falls through to the direct URL — kept for backward compatibility but no v0.11.0+ manifest uses it.

5. **Manifest schema v0.11.0+:**
   ```json
   {
     "app_version": "0.11.0",
     "app_download_endpoint": "https://coldbore-download.cheidt182.workers.dev/authorize",
     "app_download_file": "Cold.Bore.zip",
     "app_website_url": "https://chadheidt.github.io/coldbore/",
     "app_release_notes": "...",
     "template_version": "1.0",
     "template_download_url": "",
     "template_release_notes": ""
   }
   ```
   The `app_website_url` is the "Or download manually" fallback link shown in the update banner — it points users at the website (so they hit the same gated flow), not at any direct download URL.

6. **Cleaned up GitHub release artifacts.** Deleted all `.dmg` and `.zip` attachments from v0.6.0 through v0.10.1 — the release records remain (for version-history continuity) but the binaries are gone. v0.11.0 release record exists with no binaries (just notes pointing at the website).

### Final state on Chad's machine

- `/Applications/True Zero.app` runs **v0.11.0** (Tools → About confirms)
- License key `CBORE-DDCX-AEGK-J2FR-2SIB` saved in config (Chad's local-testing key)
- `main` HEAD: `a261316` ("v0.11.0 - private downloads via Cloudflare Worker")
- v0.11.0 GitHub release record exists with **no binaries attached** — just version history + notes
- R2 bucket `coldbore-releases` holds the current `Cold.Bore.dmg` (55 MB) and `Cold.Bore.zip` (58 MB)
- Worker is live and verified end-to-end (valid code returns signed URL → file downloads correctly)
- Old downloads (v0.10.x copies) deleted from Chad's `~/Downloads` folder

### How to issue keys to a new beta tester (the steady-state workflow)

Chad's Desktop has `True Zero — How to Issue License Keys.docx` with click-by-click instructions, but the high-level shape is:

1. `python3 tools/generate_license_key.py` to generate a fresh CBORE-XXXX-XXXX-XXXX-XXXX
2. Add the key to TWO places: `app/license.py`'s `VALID_KEYS` AND the **Worker's `VALID_CODES`** set in the Cloudflare dashboard. **The Worker copy was the one we forgot to mention in the Desktop doc — needs updating.** TODO: update the doc to call this out.
3. Record the recipient in `beta-keys.txt` at the project root (gitignored)
4. Ship a new app release (so the app accepts the new key on first launch)
5. Email the tester the key + the website link

The same key unlocks the website Download button AND the app's license dialog.

### Two things to verify in a future session

1. **End-to-end auto-update.** v0.11.0 → vX.Y.Z transitions are now the first real test of the in-app installer's `ditto`-based flow PLUS the new Worker-gated URL fetching. We haven't shipped a vX.Y.Z higher than v0.11.0 yet, so this hasn't been proven. Next time we bump version, watch the auto-update succeed (or diagnose if it fails).

2. **Update the License Keys Word doc on Desktop** to call out that NEW keys need to be added in TWO places: `app/license.py` AND the Worker's `VALID_CODES` set in the Cloudflare dashboard. Without the Worker update, a new tester would have a key that unlocks the app (after rebuild) but can't download it from the website.

### What's pending after v0.11.0 (the actual "send to friends" milestone)

- **Email beta keys to the first round of testers.** Generate keys, add to license.py AND Worker, ship a small bump release (or just edit Worker for download-only; new app release only needed if you want them to be able to actually USE the app).
- **Phase 9 commercialization** (when ready): LLC, EULA, USPTO trademark for "True Zero", `coldbore.app` domain, Gumroad/Stripe checkout integration, public launch via YouTube demo + forum outreach.

### Notes for future-us — infrastructure reality

**Worker source code lives in Cloudflare's web editor, NOT in this git repo.** If we ever want it version-controlled, run `wrangler init` in a `worker/` subfolder, paste the current Worker source from the dashboard, and use `wrangler deploy` going forward. Today the source-of-truth is the live deployed version at https://dash.cloudflare.com → Workers & Pages → coldbore-download → Edit code.

**Where every secret/binding lives:**
- `HMAC_SECRET` — encrypted env var in the Worker (dashboard → coldbore-download → Settings → Variables and secrets). Used to sign download URLs. If you rotate it, all currently-active signed URLs immediately break (max impact = 5 minutes of disruption since URLs are 5-min lifetime).
- `BUCKET` binding → R2 bucket `coldbore-releases`. Configured under Worker → Bindings tab.
- License keys — in TWO places: `app/license.py`'s `VALID_KEYS` AND the Worker's `VALID_CODES` set. Adding/revoking requires updating both.

**Cloudflare free-tier thresholds (when this starts costing money):**
- R2 storage: 10 GB free, $0.015/GB after
- R2 Class A operations (uploads): 1M/month free
- R2 Class B operations (reads): 10M/month free
- **R2 egress: free, always** (this is the killer feature — AWS S3 charges $0.09/GB egress)
- Workers: 100k requests/day free, $0.30/M after
- Realistic True Zero beta scale: ~$0/mo. Even at 1000 downloads/day we'd stay free.

**Commerce transition (later) is small.** The website button changes from "Download True Zero" to "Buy True Zero — $XX" + small "Sign in to download" secondary. Buy button opens Stripe Checkout or Gumroad. Payment-success webhook hits the Worker, which generates a fresh CBORE-XXXX code, adds it to VALID_CODES (or KV store), emails it to the customer. Customer comes back to the website and uses the secondary link with their code. The R2 + Worker + in-app license flow built tonight stays exactly the same. Estimated 1-2 sessions to wire up Stripe webhook + migrate VALID_CODES from hardcoded set to Cloudflare KV.

**Edge case (no current impact but worth knowing):** v0.10.1's auto-updater reads `app_download_url` from the manifest. The v0.11.0 manifest doesn't have that field (intentionally — we removed the public URL). So a hypothetical v0.10.1 user would see "v0.11.0 available" but couldn't auto-update. **No real users besides Chad were on v0.10.1, and Chad installed v0.11.0 fresh.** If we ever change manifest schema again in a way that breaks old clients, include BOTH old + new fields for the transition release.

**To redeploy the Worker:** dashboard → Workers & Pages → coldbore-download → Edit code → make change → Deploy. Changes are live within seconds.

**To check usage / costs:** dashboard → Analytics or Workers → coldbore-download → Metrics.

### Backups — what's covered and where

Time Machine was set up on 2026-05-10 onto an external 1 TB USB drive named **True Zero Backup** (encrypted, hourly automatic). Combined with git and the Cloudflare-hosted infrastructure, here's where each piece of the project lives:

| What | Where | How |
|---|---|---|
| Project source code, docs, breadcrumbs | git (origin: chadheidt/coldbore) + Time Machine | automatic on every commit + hourly Time Machine |
| `beta-keys.txt` (key → tester map) | **Time Machine only** | gitignored; lives at project root |
| Workbook templates + .xltx | git + Time Machine | committed |
| User's range data (`Documents/True Zero Loads/`) | Time Machine only | data folders are gitignored |
| True Zero app config (`~/Library/Application Support/True Zero/`) | Time Machine only | local app state |
| Apple Developer cert + private key | Time Machine only (Keychain backed up as part of `~/Library/Keychains/`) | imported into Keychain on 2026-05-10 |
| `coldbore-notary` keychain profile (notarytool credentials) | Time Machine only (Keychain) | created via `xcrun notarytool store-credentials` |
| Cloudflare Worker source | git (`worker/coldbore-download.js`) + Time Machine + Cloudflare dashboard | live source-of-truth is dashboard; backup copy in repo as of commit 4177931 |
| Cloudflare R2 binary contents (.dmg, .zip) | Cloudflare R2 + Time Machine (project's `dist/`) | rebuilt from source any time |
| `HMAC_SECRET` env var (Worker) | **NOT backed up** (intentional) | rotatable in 30 sec if lost — generate new secret with `python3 -c "import secrets; print(secrets.token_hex(32))"`, paste into Worker → Settings |
| Desktop reference docs (How to Issue License Keys, etc.) | Time Machine only | local .docx files |

**Backup gotchas to watch for:**
- The external drive must stay plugged in for Time Machine to actually run backups. Hourly = "every hour the drive is plugged in." When unplugged, backups pause.
- If the encryption password is lost, the backups can't be restored. Keep that password somewhere outside the backup itself.
- The Cloudflare Worker source is the one thing where the live version is NOT in git — the dashboard is. When changes are made there (e.g., adding a new key to VALID_CODES), remember to also paste the updated source into `worker/coldbore-download.js` and commit, so the backup copy stays current.

---

## ✅ v0.10.1 SHIPPED — May 10, 2026 (late afternoon, same day)

**License dialog polished + auto-updater fixed.** The two follow-ups flagged after v0.10.0 are both done. Chad ran the new dialog locally and confirmed it looks right.

### What's new in v0.10.1

1. **License dialog UI redesign.** The locked-out screen now shows:
   - True Zero icon at the top (from `docs/assets/icon.png`, bundled by setup.py)
   - Wordmark + version line
   - Screenshot of the main window (`docs/assets/screenshot.png`)
   - One-paragraph description of what True Zero does
   - License key entry field at the bottom
   - Quit / Unlock buttons

   Implementation: `app/license_dialog.py` rewritten. `_resource_path()` helper finds bundled images in both dev mode (`docs/assets/`) and the .app bundle (`Contents/Resources/`). `setup.py` now adds `icon.png` and `screenshot.png` to `data_files` so they're available at runtime.

2. **Auto-updater fix: `unzip` → `ditto`.** `app/installer.py`'s helper script now uses `ditto -x -k` to extract the downloaded zip instead of `unzip`. BSD `unzip` drops macOS metadata that codesign relies on; `ditto` is macOS-native and preserves the bundle exactly. Should make v0.10.1 → v0.10.2+ swaps clean.

   **Caveat:** the fix is in v0.10.1's installer code. Existing v0.10.0 installs still have the broken `unzip` installer, so v0.10.0 → v0.10.1 still required Chad to do a manual fresh-install from the .dmg (not auto-update). Future v0.10.1 → vX.Y.Z transitions should work via the in-app banner. **THIS HAS NOT YET BEEN END-TO-END TESTED.** First chance is whenever the next release ships.

### Other improvements made this same evening

- **Permission-prompt sound** — `~/.claude/settings.json` now has hooks for both `Notification` and `PermissionRequest` events, both running `afplay /System/Library/Sounds/Glass.aiff`. Chad confirms permission-prompt sound works. The Notification event also fires on idle waits but is harder to trigger on demand.
- **Project-level True Zero allowlist** — `.claude/settings.json` (gitignored, local only) auto-allows the project's signing/notarization tools: `xcrun *`, `codesign *`, `security find-identity *`, `security import *`, `spctl *`, `create-dmg *`. These came up repeatedly during today's release work.
- **Cleaned up project folder** (~120 MB → 4.9 MB) by deleting the local `dist/`, `/tmp/coldbore-build/`, the Desktop signing folder, and accumulated old True Zero copies in Downloads.
- **`True Zero — How to Issue License Keys.docx`** lives on Chad's Desktop — click-by-click guide for issuing keys, recording recipients, shipping releases with new keys, and revoking.

### Final state on Chad's machine

- `/Applications/True Zero.app` runs **v0.10.1** (Tools → About confirms)
- License key: `CBORE-DDCX-AEGK-J2FR-2SIB` saved in config (Chad's local-testing key)
- `main` HEAD: `74df94e` ("v0.10.1 - dialog UI polish + installer ditto fix")
- v0.10.0 + v0.10.1 GitHub releases both published with .dmg + .zip
- Beta-tester key slots 1-5 still unassigned in `app/license.py` and `beta-keys.txt`

### What's pending — TODO when ready

- **Issue keys to specific testers.** The two friends Chad already gave the website link to will eventually ping him asking for a key (per his decision today: option 2, wait for the ping). Refer to `~/Desktop/True Zero — How to Issue License Keys.docx`.
- **Send the v0.10.1 link to the wider pro-shooter beta cohort.** Each tester gets a unique key + the website link. True Zero is now ready for real beta distribution.
- **First v0.10.1 → vX.Y.Z auto-update.** Whenever Chad ships the next minor bump, this will be the first proof that the `ditto` fix actually works. If it doesn't, the next investigation is whether the helper script needs additional xattr hygiene (e.g., re-strip `com.apple.quarantine` AFTER the swap, not just before).
- **Phase 9 commercialization** (when ready): LLC, EULA, USPTO trademark, `coldbore.app` domain, Gumroad/Stripe, public launch.

---

## ✅ v0.10.0 SHIPPED — May 10, 2026 (afternoon, same day as v0.9.0)

**Beta lockdown is live.** True Zero now refuses to open past a license-key dialog on first launch (and re-validates the stored key on every launch). v0.10.0 is signed + notarized and on Chad's `/Applications`; his test key `CBORE-DDCX-AEGK-J2FR-2SIB` unlocks it.

### What's in the lockdown

- `app/license.py` — VALID_KEYS frozenset, `normalize_key`, `is_valid_key`, `license_state` (returns `valid` / `invalid` / `missing`), `save_license`. Re-validates the stored key on every launch so revocations propagate via auto-update.
- `app/license_dialog.py` — Qt modal with key entry, Quit/Unlock buttons, REVOKED vs first-time prompt copy.
- `app/main.py` hooks the license check **before** the disclaimer.
- `tools/generate_license_key.py` — random base32 key generator. `python3 tools/generate_license_key.py [count]` prints CBORE-XXXX-XXXX-XXXX-XXXX keys.
- `beta-keys.txt` (gitignored) — Chad's private log mapping each key to its recipient.
- `tests/test_license.py` — 15 tests covering normalize, well-formed, validity, and the missing/valid/invalid state transitions. All passing.

### Operating manual

`~/Desktop/True Zero — How to Issue License Keys.docx` is the click-by-click guide for issuing a new key, recording the recipient, shipping a release, and revoking. Chad uses this when onboarding each beta tester.

### Two known follow-ups (TOMORROW'S WORK)

#### 1. CRITICAL — In-app auto-updater is broken on current macOS

When Chad triggered the v0.9.0 → v0.10.0 update via the yellow banner, the installer swap completed and the app reopened, but macOS immediately showed *"True Zero.app is damaged and can't be opened. You should move it to the Trash."* — same as the v0.8.6 → v0.9.0 attempt earlier in the day.

Hypothesis: `installer.py`'s helper script uses `unzip` to extract the new zip and `mv` to swap. Recent macOS versions are pickier — they treat the resulting bundle as having a tampered signature (the bundle hashes no longer match the original notarization metadata, OR the extraction strips a critical xattr like `com.apple.cs.codeRequirement`). 

**Likely fix**: change the helper script to use `ditto -x -k <zip> <dest>` instead of `unzip` for extraction. `ditto` is macOS-native and preserves the bundle structure faithfully (it's what we use to BUILD the zip on the dev side). `unzip` is BSD-style and doesn't know about HFS+/APFS resource forks or signature-relevant xattrs.

Until this is fixed, **every release will require beta testers to do the manual "fresh download from website + drag to Applications" dance**. That's a regression from the v0.8.5 → v0.8.6 success earlier today, and it defeats one of True Zero's core UX features.

Investigation notes for next session:
- Read `installer.py`'s `_build_helper_script()` — that's the bash that runs after the app quits to swap the new bundle in.
- Test with `ditto -x -k` swap on a local zip → install → confirm macOS doesn't flag damaged.
- May also need to re-strip quarantine via `xattr -dr com.apple.quarantine` after the swap.
- If `ditto` alone doesn't work, the alternative is to make the in-app banner just `open` the downloaded .dmg in Finder and let macOS handle the install dance natively (user drags new app to Applications). That loses one-click convenience but is bulletproof.

#### 2. POLISH — v0.10.1: show UI preview behind the license dialog

Chad's explicit request: testers should see what True Zero looks like (icon, screenshot, description) while locked out, not just a bare dialog. Plan:

- Replace `LicenseDialog`'s blank background with: app icon on top, a screenshot of the main window (the existing `docs/assets/screenshot.png` from the marketing site is perfect), a one-paragraph description of what True Zero does, then the existing key field + Quit/Unlock buttons.
- Re-render `docs/assets/screenshot.png` via `tools/render_coldbore.py` first if the marketing render is stale — but the May-10 evening version should be current.
- Keep the dialog modal — input is still blocked behind it, just visual presentation is richer.

### Files committed today (since the start of session)

- `7c3d383` — v0.10.0 license gate (added today afternoon)
- `c68fd64` — Phase 9.0 lockdown plan in Build progress.md
- `4307144` — v0.9.0 lessons-learned breadcrumb
- `a4c09f9` — landing page updates for .dmg / drop right-click step
- `0b2c5a1` — v0.9.0 version bump
- `728b37a` — Phase 8 iOS Share-Sheet integration must-have note

### What's pending after the auto-update fix

- Issue keys to the two friends Chad already gave the website link to (he chose option 2 — wait until they ping rather than push proactively)
- Send the v0.10.0 link to the wider pro-shooter beta cohort once auto-update is fixed
- Phase 9 commercialization (LLC, EULA, USPTO trademark, domain, Gumroad, public launch)

---

## ✅ v0.9.0 SHIPPED — May 10, 2026 (evening — first signed + notarized release)

**True Zero is now signed by Apple's Developer ID and notarized.** macOS opens it without any "unidentified developer" / "damaged" / right-click-Open warnings. This is the threshold for real distribution.

### Final state on Chad's machine

- `/Applications/True Zero.app` runs **v0.9.0** (Tools → About confirms). Installed fresh from the v0.9.0 .dmg, opens silently, no Gatekeeper friction.
- `main` HEAD: `a4c09f9` ("Landing page: point download at .dmg; drop right-click step")
- v0.9.0 GitHub release published: https://github.com/chadheidt/coldbore/releases/tag/v0.9.0 — both `Cold.Bore.dmg` (55 MB, signed + notarized + stapled) and `Cold.Bore.zip` (58 MB, signed, for the auto-update path) attached
- Landing page (https://chadheidt.github.io/coldbore/) updated: download button points at the .dmg directly, install steps walk through .dmg flow, Gatekeeper-warning copy removed

### How v0.9.0 was built

1. Apple Dev cert generated via openssl CSR → uploaded to developer.apple.com → downloaded `developerID_application.cer` → imported as a .p12 (with `-legacy` flag, otherwise `security import` rejects with MAC verification failed).
2. App-specific password from appleid.apple.com → stored in keychain via `xcrun notarytool store-credentials "coldbore-notary"`.
3. `create-dmg` installed via `brew install create-dmg`.
4. **Build sequence** (the working path — see lessons below):
   - py2app to `/tmp/coldbore-build/dist/` (NOT the project's `dist/` — see lesson 1)
   - `codesign --force --options runtime --timestamp --sign "Developer ID Application: Chad Heidt (NY3D844C6W)"` on every Mach-O inside the bundle individually (`--deep` is NOT enough — see lesson 2). Then sign the outer bundle with `--entitlements`.
   - `create-dmg` from a stage dir containing the signed .app + Quick Start docx
   - `codesign --timestamp` the .dmg
   - `xcrun notarytool submit ... --keychain-profile coldbore-notary --wait` (took ~25 min that evening; queue was busy)
   - `xcrun stapler staple` the .dmg
   - `ditto -c -k --keepParent` to also build Cold.Bore.zip from the same signed .app, plus add Quick Start docx
   - Copy both artifacts from `/tmp/coldbore-build/dist/` back into the project's `dist/`

### Lessons learned today (READ BEFORE NEXT SIGNED BUILD)

1. **Build outside the project directory.** macOS attaches `com.apple.provenance` (and `com.apple.macl`) xattrs to files copied within the project tree. Those xattrs then block py2app/macholib from modifying its own copies of `Python3.framework/Versions/3.9/Python3` and other Mach-O files — the build dies with `[Errno 1] Operation not permitted` during the changefunc/load-command rewrite. **Workaround: `python3 setup.py py2app --dist-dir /tmp/coldbore-build/dist --bdist-base /tmp/coldbore-build/build`.** Then continue codesign + DMG + notarization in `/tmp/`, copy final `.dmg` and `.zip` back into `dist/` only at the very end. This bug was NEW today (worked this morning, broke this evening — likely a silent macOS security policy update). Even Finder double-click on Build Signed App.command hits it. The setup.py monkey-patch attempting to strip `com.apple.provenance` after each shutil.copy didn't help (macOS silently re-applies the xattr).

2. **`codesign --deep` is NOT enough for notarization.** Apple's notary service rejected the first submission with "binary is not signed with a valid Developer ID certificate" + "signature does not include a secure timestamp" errors on every `.so` and `.dylib` inside the bundle. The `--deep` flag re-uses pre-existing signatures from those binaries (which are Apple's adhoc ones), it doesn't re-sign them with our identity. **Fix: explicitly sign every Mach-O inside `True Zero.app` with `--options runtime --timestamp --sign "Developer ID Application: ..."`.** Use a `find` loop over `Frameworks/` and `Resources/` for files where `file <path>` matches `Mach-O`. 248 files in our case. After that, sign the outer bundle with the same flags plus `--entitlements`. Then submit. Notarization passed on the second try.

3. **Pillow has to be excluded in setup.py.** `tools/render_*.py` use Pillow for the marketing-site hero images, but the runtime app doesn't need it. `openpyxl` has an optional `from PIL import Image` that pulls Pillow in by default during py2app's static analysis. Pillow's bundled `libtiff.6.dylib` then trips the same provenance-EPERM during the build. `setup.py` now lists `"PIL"` under `excludes`. Keep it there.

4. **`security import` of a .p12 needs `-legacy` openssl flag.** Without it, `openssl pkcs12 -export` writes a modern PKCS12 format that macOS's Keychain rejects with `MAC verification failed during PKCS12 import (wrong password?)` — misleading error, the password was correct. With `openssl pkcs12 -export -legacy ...`, import works.

5. **Right after Apple approves the Developer Program**, the cert is NOT auto-installed. Chad has to generate a CSR (Certificate Signing Request) — programmatically via `openssl req -new -newkey rsa:2048 -nodes -keyout coldbore.key -out CertificateSigningRequest.certSigningRequest -subj "/emailAddress=.../CN=..."` is fine — upload it to developer.apple.com, download the .cer, then bundle .cer + .key into a .p12 and `security import` with `-T /usr/bin/codesign -T /usr/bin/productsign` flags so codesign can use it without prompts.

6. **Sensitive artifacts left at `~/Desktop/cold-bore-signing/`:** `coldbore.key` (unencrypted private key), `coldbore.p12` (encrypted with password "coldbore"), `developerID_application.cer` (public cert), `CertificateSigningRequest.certSigningRequest` (CSR). Cert + key are now safely in Keychain. Chad can delete the whole folder anytime.

### What's pending (commerce phase, later)

- Send the live website link to pro-shooter beta candidates. The .dmg is signed/notarized; first-launch is silent; install instructions on the page are accurate.
- Auto-update test from v0.9.0 → v0.9.1 will be the next chance to verify the in-app updater still works — Chad's existing v0.8.6 went "damaged" before we could test the v0.8.6 → v0.9.0 path (macOS got stricter on adhoc signatures during this session). v0.9.0 → next is the path forward.
- LLC formation, USPTO trademark for "True Zero", lawyer for EULA + privacy + refund policy
- Domain `coldbore.app` (~$15/yr)
- Gumroad or Stripe Checkout embed on the landing page
- Public launch via YouTube demo + forum outreach

See `Build progress.md` Phase 9 for the full commercialization plan.

### Stale GitHub release records that could be cleaned up later (not blocking)

v0.8.1, v0.8.2, v0.8.3, v0.8.4 (broken Apple-Silicon-only or em-dash-crash builds) and possibly v0.7.x records may still exist on GitHub. None point at working binaries that anyone has. Could be deleted with `gh release delete vX.Y.Z --repo chadheidt/coldbore --cleanup-tag` if the releases page should be tidy.

---

## 🚧 BETA PREP IN FLIGHT — May 10, 2026 (afternoon session — pivoting to pro-shooter beta + commercialization)

**Big picture shift today:** Chad is moving True Zero from "friends-and-family" to "pro-shooter beta with commercialization in sight." He's signed up for the **Apple Developer Program ($99/yr)** and is waiting on Apple's 24-48 hour approval. Once approved, we ship v0.9.0 as the first signed + notarized + DMG-packaged release. After beta validation, we layer in commerce (Gumroad/Stripe, LLC, EULA).

### Live marketing site

**The landing page is live at: https://chadheidt.github.io/coldbore/**

A `.webloc` shortcut at the project root (`True Zero Website.webloc`) opens it in Chad's default browser on double-click. GitHub Pages serves from `docs/` on `main` — every push to that path redeploys within ~30 sec.

The site has:
1. Hero image — Load Log render with red SUGGESTED CHARGE bar, rifle/components/test session info, and the 6-load 7 SAUM ladder showing P3 winning at composite 0.283
2. "Drag. Click. Done." section — True Zero window mockup with the polished drop zone (reticle + MOA grid + spotlight + subtitle), workbook picker, Run Import button, and activity log
3. Features grid, 3-step install, FAQ, reloading-safety disclaimer

Both hero images are **rendered programmatically via Pillow** (see `tools/render_workbook.py` and `tools/render_coldbore.py`) — not screen-captured. Reasoning: the screen-capture path hit a 90-min wall of macOS hurdles (cross-Space windows, Screen Recording permission for the calling process, focus bouncing back). The PIL renderers produce deterministic, version-controlled, regenerable images. Re-run them whenever the in-app drop zone or workbook layout changes.

### What's done today (afternoon)

- ✅ **Drop zone polish (`app/main.py`, `app/theme.py`)** — precision-rifle reticle (mil-dot subtensions on crosshair arms, hash marks at major mil intervals), MOA-style grid background (24px pitch, anchored to crosshair), center spotlight (subtle radial highlight), subtitle ("Auto-detects format · drop multiple at once") via QLabel rich-text. Hover state intensifies all of it.
- ✅ **Template scoring fix (`Rifle Loads Template (do not edit).xltx`)** — `Charts!L18:L25` composite-score formulas now wrap in `IF(A##="","" , ...)`. Previously, partial powder ladders (fewer than 8 loads) scored empty rows as composite=0 = "best", so MIN() always picked an empty row and the SUGGESTED CHARGE bar showed blank. Patch makes empty rows return blank, MIN correctly picks the populated winner.
- ✅ **Beta-prep scaffolding committed:**
  - `entitlements.plist` — hardened-runtime entitlements for notarization (allow-unsigned-executable-memory + allow-dyld-environment-variables + disable-library-validation, the minimum for a py2app + bundled-PyQt5 setup)
  - `Build Signed App.command` — full pipeline scaffold (clean → py2app → codesign per-binary → DMG via create-dmg → notarytool submit + wait → stapler staple → spctl verify). Errors with a helpful message until Chad fills in `SIGNING_IDENTITY` and `APPLE_TEAM_ID` after his Dev ID is issued.
- ✅ **Marketing site (`docs/`)** — see above.
- ✅ **Render scripts (`tools/`)** — committed for reproducibility.
- ✅ **Word reference docs on Chad's Desktop** (NOT committed — they live on his Desktop as quick-reference printouts):
  - `True Zero - Starting a session in VS Code.docx`
  - `True Zero - GitHub access for friends.docx`
  - `True Zero - Sending to friends.docx`
- ✅ **macOS housekeeping**: Re-enabled disabled screenshot keyboard shortcuts (28-31 in `defaults read com.apple.symbolichotkeys` were `enabled = 0`); upgraded pip 21.2.4 → 26.0.1; added `~/Library/Python/3.9/bin` to PATH in `~/.bash_profile` so user-installed CLI tools (pip/pytest/etc.) are typeable directly.

### What's done today (evening — landing-page polish)

- ✅ **Website logo treatment (`docs/index.html`)** — commit `282d158`. Added a 96px True Zero icon centered above the hero headline (72px on mobile via media query). Bumped the nav-corner icon from 32px → 44px so it reads better. Live at https://chadheidt.github.io/coldbore/.
- ✅ **Cache-Control meta tag (`docs/index.html`)** — commit `4df9c74`. Added `<meta http-equiv="Cache-Control" content="no-cache, must-revalidate">` so returning visitors always see fresh content. Previously GitHub Pages' default `max-age=600` could serve a stale copy for up to 10 min after a push — now resolved. Useful as we keep iterating on marketing copy / imagery.

### What's pending (the actual blocker: Apple's email)

When Chad's Dev ID is approved (24-48 hr from his enrollment, signaled by an email from `developer@apple.com` titled something like "Welcome to the Apple Developer Program"):

1. **In Keychain Access on Chad's Mac**: Apple should auto-install the certificate when he visits developer.apple.com/account and accepts. If not: Certificates, Identifiers & Profiles → Certificates → Add → "Developer ID Application" → walk through the CSR.
2. **Verify the cert**: `security find-identity -v -p codesigning` should show `"Developer ID Application: Chad Heidt (XXXXXXXXXX)"`.
3. **Edit `Build Signed App.command`** to fill in `SIGNING_IDENTITY` (the full quoted string from step 2) and `APPLE_TEAM_ID` (the 10-char code in parentheses).
4. **Install create-dmg**: `brew install create-dmg`.
5. **Set up notarytool credentials**: Have Chad generate an app-specific password at appleid.apple.com, then `xcrun notarytool store-credentials "coldbore-notary" --apple-id <his email> --team-id XXXXXXXXXX --password <app-specific>`.
6. **Bump versions to v0.9.0** (`app/version.py`, `setup.py`, `manifest.json`).
7. **Run `Build Signed App.command` from Finder**. It produces `dist/Cold.Bore.dmg` — signed + notarized + ready to ship.
8. **Create v0.9.0 release on GitHub** (gh release create + edit to publish, same as v0.8.6). Attach the .dmg.
9. **Update the landing page download button** to point at the .dmg (not the .zip).
10. **Test the auto-update from v0.8.6 → v0.9.0** on Chad's `/Applications/True Zero.app`. Should be smoother than v0.8.6 (no Gatekeeper warning post-swap because of code signing).

### What's pending after v0.9.0 ships (commerce phase, later)

- LLC formation in Chad's state (~$50-500 depending on state)
- Trademark "True Zero" with USPTO ($250-350)
- Lawyer consultation (~$300-600) for EULA + privacy + refund policy
- Domain `coldbore.app` (~$15/yr)
- Gumroad or Stripe Checkout embed on the landing page
- Public launch via YouTube demo + forum outreach

See `Build progress.md` Phase 9 for the full commercialization plan.

### Lessons learned today (read before next release)

1. **Don't try to screen-capture another Mac app from a Bash subprocess.** TCC permission gates, Spaces visibility, and focus-bouncing all conspire. Render programmatically with PIL or have Chad use Cmd+Shift+5 himself. We burned ~90 min learning this.
2. **Helvetica.ttc on macOS lacks unicode arrows and check marks.** Stick to ASCII-safe glyphs in PIL renders or boxes appear in place of `→` `✓` etc.
3. **Excel for Mac 2016 AppleScript is fragile.** `close w saving no` errors with -50; simpler `quit saving no` and re-open works. Don't try to do too much in one AppleScript call.
4. **The composite scoring bug in the template** would silently break the SUGGESTED CHARGE bar for any ladder with fewer than 8 loads. Now patched. If you ever see SUGGESTED CHARGE blank with populated data, the L18:L25 formulas are the first thing to check.

---

## ✅ v0.8.5 + v0.8.6 SHIPPED — May 10, 2026 (auto-update PROVEN END-TO-END)

**The big news: Phase 12 / in-app self-installer works.** v0.8.5 (Chad's running app) successfully detected v0.8.6 on the manifest, downloaded the zip via the yellow banner, swapped itself, relaunched at v0.8.6, and Tools → About now reports 0.8.6. No manual steps. The custom Python+bash installer is proven for friends-and-family distribution.

**State on Chad's machine right now:**
- `/Applications/True Zero.app` runs v0.8.6 (auto-updated from v0.8.5 in the test).
- `main` branch HEAD: `bcca535` ("v0.8.6 - bump for auto-update test ...").
- `manifest.json` on main says v0.8.6, and the v0.8.6 release zip exists on GitHub.
- Both the v0.8.5 and v0.8.6 GitHub releases have `Cold.Bore.zip` attached.

**What we did today (May 10):**
1. v0.8.5 had been pushed yesterday but CI was queue-stuck. Chad manually built locally and published the v0.8.5 release this morning (before this session).
2. This Claude Code session: bumped to v0.8.6, committed + pushed, CI queued again, gave it ~9 min, went plan B.
3. Built v0.8.6 locally via `Build App.command` (see lesson 7 below), zipped via `ditto` + added Quick Start docx.
4. Used `gh release create v0.8.6 --draft` to upload, then `gh release edit --draft=false --latest` to promote. Avoids firing CI's `release: created` trigger (it only fires on initial create-as-published, not on draft→published edit).
5. Chad ran the auto-update test, all six steps passed cleanly.

### Lessons learned from today (read before next release)

7. **Run `Build App.command` from Finder, NOT `python3 setup.py py2app` from a Terminal command.** The latter fails on Chad's Intel Mac with `[Errno 1] Operation not permitted` on the bundled `Python3.framework/Versions/3.9/Python3` binary — macOS adds a `com.apple.provenance` xattr to the copy that blocks `os.chmod` (and in turn, `flipwritable` in macholib). Same script, same Python — the only thing that worked was double-clicking `Build App.command` from Finder. Three monkey-patch attempts to py2app/macholib all failed. **Save yourself the time and just have Chad double-click Build App.command.** Likely a CommandLineTools / macOS hardening update from late 2025/early 2026 introduced this. Not yet investigated whether `Build App.command`'s shell environment (no bash 5.x, no inherited xattrs from cwd?) is what makes it work — but empirically it does.

8. **Use `gh release create --draft` + `gh release edit --draft=false --latest` for manual uploads.** Direct `gh release create --latest` would fire the `release: created` event which triggers CI, and you'd race CI's asset attach against your manual asset (filename collision → upload error). Draft → publish path: `created` event fires only on the initial creation (which is the draft, attaches nothing to nothing); the publish step fires `published` which our workflow doesn't listen to. Clean.

9. **Run True Zero from `/Applications/` to test the auto-update flow, not `dist/`.** The yellow banner WILL appear in dev-mode `dist/` runs but `can_self_install()` returns False (since the .app isn't where the helper script can swap it), and the banner falls back to "download manually." For end-to-end test, must be installed in `/Applications/`.

### What to work on next (Chad's call when he resumes)

- **Send True Zero to friends.** v0.8.6 is the first reliably-Intel build with proven auto-updates. Reference: `Send True Zero to friends.md` at the project root.
- **Optional release-page cleanup**: stale v0.8.1–v0.8.4 release records still exist on GitHub. None of them point at working binaries. Could delete via `gh release delete vX.Y.Z --repo chadheidt/coldbore --cleanup-tag` if Chad wants the releases page tidy. Not blocking.
- **Phase 7 (Windows port)** — see Build progress.md. High-leverage if commercializing.
- **Phase 8 (iOS port)** — see Build progress.md. Long-tail.

### Permission allowlist (for Claude Code, set up at end of session)

User-level `~/.claude/settings.json` now has an allow list for the commonly-used Bash patterns: `gh`, `git`, `python3`, `ditto`, `zip`, `unzip`, etc. So future True Zero work in Claude Code shouldn't prompt for every command. Path: `~/.claude/settings.json` — open it directly if you need to tighten or broaden.

---

## ✅ Historical: SWITCHING TO CLAUDE CODE / PLAN B — May 9, 2026 (v0.8.5)

(Kept for context — this section's plan was executed and v0.8.5 + v0.8.6 are now both shipped.)

**Chad's frustration is real after a long release-engineering day.** Be efficient. Don't over-explain steps Claude Code can just execute. Reserve the talking for the things Chad needs to do himself (browser-based tasks like clicking Publish on GitHub).

### What Claude Code should do (action-oriented checklist)

1. **Cancel the stuck CI run.** Use `gh` if Chad has it installed (`gh run cancel 25608316391 --repo chadheidt/coldbore`); if `gh` not installed, just have Chad click Cancel workflow on https://github.com/chadheidt/coldbore/actions/runs/25608316391. Skip if the run already ended.

2. **Build the v0.8.5 zip locally.** Run from the project folder:
   ```
   cd "/Users/macbook/Projects/Rifle Load Data"
   rm -rf dist build
   python3 setup.py py2app
   cd dist
   ditto -c -k --keepParent "True Zero.app" "Cold.Bore.zip"
   cp "../True Zero — Quick Start.docx" .
   zip "Cold.Bore.zip" "True Zero — Quick Start.docx"
   ```
   Watch for build errors. py2app on Chad's Intel Mac uses his system Python 3.9 — should produce a working Intel bundle. Verify with `file dist/Cold.Bore.zip` and `unzip -l dist/Cold.Bore.zip` afterward to confirm both `True Zero.app` and `True Zero — Quick Start.docx` are inside.

3. **Hand the zip off to Chad for the GitHub release.** Tell him:
   - Open https://github.com/chadheidt/coldbore/releases/new
   - Tag: `v0.8.5`, Title: `True Zero 0.8.5`
   - Description: "Build fixed for Intel Macs. Uses macos-13 CI runner so PyQt5 ships as Intel binary - works natively on Intel and via Rosetta 2 on Apple Silicon."
   - ☑ Set as the latest release
   - Drag `dist/Cold.Bore.zip` into the "Attach binaries" area at the bottom
   - Wait for upload (~30-60 sec)
   - Click green Publish release
   - Paste the resulting URL back so you can verify

4. **After v0.8.5 is shipped, prep v0.8.6** for the auto-update test:
   - Edit `app/version.py`, `setup.py`, `manifest.json` to v0.8.6
   - Manifest release notes: "First successful in-app auto-update test. Trivial bump from v0.8.5 to give Chad's running app something to update to."
   - Also commit the pending Build progress.md SaaS-analysis section that's been sitting in his working tree (uncommitted). And the `Rifle Load Data.code-workspace` file — that should be added to `.gitignore` (it's a VS Code-specific workspace file, no value in committing).
   - Commit message: `v0.8.6 - bump for auto-update test (and SaaS architecture decision in Build progress.md)`
   - Push to main.
   - Try CI first; if it queues again, repeat plan B for v0.8.6 too.

5. **The actual auto-update test.** Once v0.8.6 release is published with `Cold.Bore.zip` attached:
   - Have Chad open True Zero on his Mac
   - Yellow banner should appear: "App update: v0.8.6 is available."
   - Click **Install Update** → progress bar → click **Quit and Install** → app quits → ~3 sec → app reopens at v0.8.6
   - Verify Tools → About reports 0.8.6
   - If anything fails, check `~/Library/Application Support/True Zero/last_install_error.log` for the helper script's error.

### State on Chad's machine right now

- v0.8.5 is committed and pushed to main (commit `0d66b5c`)
- `/Applications/True Zero.app` runs v0.8.5 (Chad locally rebuilt earlier)
- Manifest on `main` says v0.8.5; download URL points at v0.8.5 release zip that doesn't exist yet
- Working tree has uncommitted: `Build progress.md` (SaaS analysis), `Notes for next session.md` (this breadcrumb), and `Rifle Load Data.code-workspace` (untracked, ignore-worthy)
- Chad is on Intel Mac (macos 14 Sonoma, x86_64). Python 3.9 system Python, with PyQt5 Intel installed.
- `gh` CLI may or may not be installed — Chad started exploring it earlier today but never finished. Check with `which gh` before assuming.

### Current state (the snapshot)

- **v0.8.5 is committed and pushed to `main`** — commit `0d66b5c` ("v0.8.5 - back to macos-13 (Intel) for CI; universal2 was producing arm64-only PyQt5"). Visible at https://github.com/chadheidt/coldbore/commits/main.
- **CI run #20 has been queued for 1+ hour on the macos-13 free-tier runner.** No movement. URL: https://github.com/chadheidt/coldbore/actions/runs/25608316391. May or may not eventually go green depending on GitHub's queue.
- **No v0.8.5 release exists on GitHub yet.** Won't until either CI completes or we go to plan B (manual upload).
- **GitHub releases that exist:** Chad cleaned up the stale v0.8.0–v0.8.4 release records earlier. So the visible releases on GitHub are now **v0.6.0, v0.7.0, v0.7.1** — and v0.7.1 is currently flagged as Latest (since v0.8.x are all gone). NOTE: those are all GitHub-CI-built and were Apple Silicon-only, so they're broken on Intel Macs. Chad has NOT sent any zip to friends yet, so this hasn't reached anyone.
- **Manifest on GitHub `main` (raw URL):** says v0.8.5 is available with download URL pointing at v0.8.5 release zip. Friend's app would 404 if it tried to update right now (release doesn't exist). Chad's own app is on v0.8.5 too so no update banner appears for him locally.
- **Chad's `/Applications/True Zero.app`:** **WORKING.** Currently runs v0.8.5 — he locally rebuilt via Build App.command earlier, replaced /Applications/, and stripped quarantine. Tools → About reports 0.8.5.
- **Local working tree:** ONE uncommitted change — `Build progress.md` has a new section "Architecture decision: desktop app vs SaaS (web app)" added during the wait. Chad asked to capture his developer friend's SaaS suggestion and the analysis. Push this whenever he commits next; it doesn't gate anything.
- **Project folder cleanup happened:** Chad deleted `build/`, `__pycache__/`, `dist/`, `test.xlsx`, all `.DS_Store` files. Project size went from ~12 MB to ~3.8 MB.

### New tooling installed in this session (matters for next session)

Chad set up **VS Code + Claude Code (CLI + extension)** during the CI wait. From now on he can work in VS Code instead of (or in addition to) Cowork. The breadcrumbs are tool-agnostic — Claude Code reads them the same way Cowork does.

How he'd resume in VS Code:
1. Open VS Code (it should auto-reopen with the `~/Projects/Rifle Load Data` folder)
2. Click the Claude icon in the left sidebar (or run `claude` in VS Code's integrated Terminal panel — Ctrl+\` to open it)
3. Tell Claude: *"Continue True Zero. Read Notes for next session.md to catch up — we're paused waiting on CI for v0.8.5."*

How he'd resume in Cowork:
- Same as before: open Cowork, point at `~/Projects/Rifle Load Data`, type the same resume prompt.

Either works. Chad indicated VS Code will be his primary going forward but is comfortable using either.

### Resume checklist when Chad returns

1. **Check CI status** at https://github.com/chadheidt/coldbore/actions — if the v0.8.5 run finally went green, jump to step 3. If still queued or red, see step 2.

2. **Decide: keep waiting or go plan B?**
   - **Keep waiting**: do nothing. The queue may eventually clear. Risk: could be more hours.
   - **Plan B — manual upload**: build the zip locally and upload it to a fresh v0.8.5 release on GitHub manually. Bypasses CI. Steps:
     a. Cancel the stuck CI run via "Cancel workflow" button on the actions/runs/25608316391 page.
     b. Run in Terminal (or VS Code's integrated terminal):
        ```
        cd "/Users/macbook/Projects/Rifle Load Data"
        rm -rf dist build
        python3 setup.py py2app
        cd dist
        ditto -c -k --keepParent "True Zero.app" "Cold.Bore.zip"
        cp "../True Zero — Quick Start.docx" .
        zip "Cold.Bore.zip" "True Zero — Quick Start.docx"
        ```
     c. Open https://github.com/chadheidt/coldbore/releases/new
     d. Tag: `v0.8.5`, Title: `True Zero 0.8.5`, Description: "Build fixed for Intel Macs. Uses macos-13 CI runner so PyQt5 ships as Intel binary - works natively on Intel and via Rosetta 2 on Apple Silicon."
     e. ☑ Set as latest. Drag `dist/Cold.Bore.zip` into the "Attach binaries" area at the bottom. Wait for upload (~30-60 sec).
     f. Click green Publish release.

3. **If CI was green or after manual upload succeeds**, verify the v0.8.5 release page shows `Cold.Bore.zip` in Assets. Quickly fetch via web_fetch to confirm.

4. **Now ship v0.8.6 to test the auto-update banner.** Chad's running v0.8.5; the manifest currently also says v0.8.5; no banner will fire. Bump to v0.8.6 to give v0.8.5 something to update to. Steps:
   - Edit `app/version.py`, `setup.py`, `manifest.json` to v0.8.6 with new release notes (something like "First successful in-app auto-update test from v0.8.5").
   - Commit + push (along with the SaaS analysis in Build progress.md that's still pending).
   - Wait for CI on v0.8.6 (or if queue is still bad, repeat plan B).
   - Create v0.8.6 release.

5. **Then test the auto-update for real.** Open True Zero on Chad's Mac. Yellow banner should appear: "App update: v0.8.6 is available." Click **Install Update** → progress bar → click **Quit and Install** → app quits → ~3 seconds → app reopens at v0.8.6. Tools → About reports 0.8.6.

6. **If that all works**: True Zero is shipped with working in-app auto-updates. Chad can send the link to friends. The link is in `Send True Zero to friends.md` at the project root.

### Why we're at v0.8.5

Long version-bump saga today, summarized:
- v0.8.0 — Phase 12 in-app self-installer code complete. Tested in v0.7.0 (running locally), banner showed old "Download new version" link because the running v0.7.0 didn't have the new code.
- v0.8.1 — switched CI to `macos-13` (Intel) to fix arch issues; got stuck in 13+ min queue.
- v0.8.2 — switched CI to `macos-latest` with `arch = 'universal2'` for fast queue; the build's launcher was universal2 but PyQt5 came in arm64-only on Apple Silicon runner.
- v0.8.3 — fixed an em-dash crash in the helper script (Python 3.9 ASCII encoding issue when writing the bash script). Chad locally rebuilt + installed.
- v0.8.4 — trivial bump to test auto-update from v0.8.3. Auto-update flow worked (download + swap) but the new bundle crashed on launch due to arm64-only PyQt5 (universal2 didn't carry to Python C extensions).
- v0.8.5 — back to `macos-13` (Intel-only build, runs everywhere via Rosetta 2 on Apple Silicon). Trade slow CI queue for a build that actually works. Code complete locally, NOT pushed.

### Resume checklist (do in order)

When Chad comes back, walk him through these steps:

1. **First: get True Zero working again on Chad's Mac.** Open Finder → `~/Projects/Rifle Load Data` → double-click `Build App.command`. This locally rebuilds True Zero at v0.8.5 using Chad's Intel Mac's Python and Intel PyQt5 (so the resulting bundle is Intel-only and works fine on his Intel Mac).
2. After ~3 minutes, the Finder should auto-open dist/. Drag `dist/True Zero.app` → `/Applications`. Click **Replace** when prompted.
3. In Terminal: `xattr -dr com.apple.quarantine "/Applications/True Zero.app"`
4. In Terminal: `open "/Applications/True Zero.app"` — should open. Verify Tools → About says **0.8.5**.
5. **Now push v0.8.5.** GitHub Desktop should still show the 4 changed files. Commit message:
   > `v0.8.5 - back to macos-13 (Intel) for CI; universal2 was producing arm64-only PyQt5`
   Commit to main → Push origin.
6. **Wait for CI.** macos-13 queue can take 10-20 min. Watch https://github.com/chadheidt/coldbore/actions. The "v0.8.5..." run goes orange (queued) → yellow (running) → green (done).
7. **Create the v0.8.5 release directly (NOT draft):**
   https://github.com/chadheidt/coldbore/releases/new
   - Tag: `v0.8.5`
   - Title: `True Zero 0.8.5`
   - Description: "Build fixed for Intel Macs. Uses macos-13 CI runner so PyQt5 ships as Intel binary - works natively on Intel and via Rosetta 2 on Apple Silicon."
   - ☑ Set as latest → green Publish release
8. **Wait ~5 min for `Cold.Bore.zip` to attach** to the v0.8.5 release. Verify via the page or with web_fetch.
9. **(Optional cleanup)** Delete the stale v0.8.1 / v0.8.2 / v0.8.3 / v0.8.4 release records on GitHub if they exist (don't delete the tags — only the release record). Keeps the releases page tidy. v0.7.1 is the lowest-version release worth keeping for friends who might still want to grab it.
10. **Now the moment of truth — but we still need a v0.8.6 to test the auto-update against.** v0.8.5 in /Applications == v0.8.5 in manifest == no banner. To test the auto-update flow, Chad needs to push a trivial v0.8.6 (Claude prepares the version bumps; Chad pushes; CI builds; Chad creates v0.8.6 release). Then his v0.8.5 sees v0.8.6 available, clicks **Install Update**, and the swap completes successfully (since v0.8.5's installer has the em-dash fix AND the new build is Intel which works on his Mac).

### Lessons learned from today's saga (read before doing future releases)

These are critical and have saved repeat sessions before; don't drop them.

1. **Never use `arch = 'universal2'` in setup.py without also forcing universal2 wheels for binary deps.** Tried in v0.8.4. The launcher is universal but PyQt5's C extensions only get whatever pip downloaded, which on an Apple Silicon CI runner is arm64-only. The bundle then crashes on Intel.
2. **`macos-13` Intel CI runner is the simplest path.** Slow queue (10-20 min during peak) but produces an Intel binary that works natively on Intel and via Rosetta 2 on Apple Silicon. One zip, every Mac. When `macos-13` is retired by GitHub (not soon), revisit by forcing universal2 wheels via `pip download --platform macosx_11_0_universal2 --only-binary=:all:` or build matrix.
3. **The .app bundle's Python is older (3.9 system Python on macOS).** Don't use any Python 3.10+ features in `installer.py`, `updater.py`, or anywhere else that runs in the bundle. Specifically: no `Path | None` syntax (use plain returns), no `match` statements, no `:=` walrus inside expressions where 3.9 doesn't allow it. Stick to 3.8-compatible syntax.
4. **The .app's bundled Python may have ASCII as default file-write encoding.** Always pass `encoding="utf-8"` explicitly when opening files for write (`open(path, "w", encoding="utf-8")`). The em-dash crash in v0.8.0→v0.8.4 came from this. Code now does this in installer.py but watch for it elsewhere.
5. **Keep the bash helper script in `installer._build_helper_script` ASCII-only.** Don't put em dashes or curly quotes in comments — they propagate into the script body and can blow up if the file write encoding regresses. Use plain `-` instead of `—`.
6. **Never put non-ASCII in commit messages either.** The Cold.Bore.zip filename + GitHub's space-rename + the release notes all need to be ASCII-only to avoid surprises across editors and CI tools.

### gh CLI (still deferred)

Chad started exploring `brew install gh` + `gh auth login` for one-line releases (`gh release create ...`). Never finished. Not blocking; today's saga still uses the GitHub web UI flow. If we keep doing releases this often, the gh CLI would be worth setting up at the start of the next session — it'd save Chad ~5 minutes per release of clicking through the web form.

---

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

1. Chad opens his locally-built v0.8.0 True Zero (currently in /Applications)
2. Manifest reports v0.8.1 available → yellow banner appears with **Install Update** button
3. Chad clicks **Install Update** → banner shows download progress
4. When download done → banner shows **Quit and Install** button
5. Chad clicks → True Zero quits, helper script swaps in v0.8.1, True Zero reopens on v0.8.1
6. Tools → About reports v0.8.1, banner is gone

**Why this is the moment of truth:** v0.8.0 had the new in-app updater code but Chad was still running v0.7.0 when we tried to test it, so we got the OLD banner ("Download new version" → browser). Now Chad's running v0.8.0 locally, and v0.8.1 will be the first time his own machine sees the new "Install Update" button on a real update event.

**If the swap fails for some reason:** ~/Library/Application Support/True Zero/last_install_error.log will have the helper script's exit message. Next launch, True Zero reads that log and surfaces it via QMessageBox. Have Chad paste whatever it says.

**Friend distribution status:** Chad has NOT sent any zips to friends yet. So the broken v0.7.0/v0.7.1/v0.8.0 GitHub zips never reached anyone. Once v0.8.1 is live and verified, the zip on `releases/latest` will be Intel-binary (works on every Mac) and friend distribution can begin in earnest.

---

## ✅ v0.8.0 SHIPPED (locally) — May 9, 2026 (auto-update feature)

**Where we left off:** Chad and Claude built **Phase 12: in-app self-installer** in this session. Code is complete locally but **not yet committed/pushed/released**. v0.8.0 will be True Zero's first version with one-click in-app updates (Level 2 — see Build progress.md Phase 12 for full design and Phase 9 for the Sparkle/Level 3 plan when commercializing).

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
7. **Test the auto-update flow on Chad's Mac.** He's still running v0.7.0, so opening True Zero will show the new banner. Click **Install Update**, watch the download progress, click **Quit and Install** when ready. True Zero should close, the helper script should swap in v0.8.0, and True Zero should reopen on v0.8.0. The Tools → About dialog should now report v0.8.0.
8. **Acceptance criteria for v0.8.0**: a clean install-update-relaunch cycle with no Gatekeeper warnings on the relaunch (because the helper strips the quarantine xattr).

**Edge cases to watch for during the v0.8.0 test:**
- Helper script's `sleep 3` should be enough for parent quit. If the swap fails because True Zero is still alive, we'd see a "Couldn't move old app aside" error — bump the sleep.
- If Chad's True Zero is in `/Applications/` and that's not writable for some reason (rare), `can_self_install()` returns False and the banner falls back to "Or download manually" — still works, just no one-click.
- The helper script writes errors to `~/Library/Application Support/True Zero/last_install_error.log`. Next launch surfaces them via QMessageBox. If anything goes wrong, that's the place to look.
- If something REALLY goes wrong and True Zero can't relaunch after the swap, Chad can manually re-install: download `Cold.Bore.zip` from https://github.com/chadheidt/coldbore/releases/latest, drag into Applications.

---

## ✅ v0.7.1 SHIPPED — May 9, 2026

**Status: pre-beta complete. Chad is cleared to share True Zero with friends.**

**What's live:**
- v0.7.0 and v0.7.1 both published at https://github.com/chadheidt/coldbore/releases
- v0.7.1 is set as **Latest**, has the workflow change that bundles `True Zero — Quick Start.docx` into `True Zero.zip` alongside the .app
- Verified by Chad: downloading the zip from the release page yields both the .app AND the Quick Start docx
- The shareable link friends should use: **https://github.com/chadheidt/coldbore/releases/latest** (always points at newest release)

**The friend-sharing reference doc** lives at the project root: `Send True Zero to friends.md`. It has the link, copy-paste-ready text/email messages, common questions, and a running version history. **When Chad asks "where's the link to send to friends," point him there.**

### gh CLI (still deferred)

Chad started exploring `brew install gh` + `gh auth login` so future releases can be one-liners (`gh release create v0.X.Y --title "..." --notes "..." --latest`) instead of clicking through the website. Never finished the install. Not blocking — next time he does a release, ask if he wants to set this up first or just push through with the manual flow again.

### Lessons learned from v0.7.1's release flow (read before next release)

The v0.7.1 release got messy because Chad and the previous Claude weren't on the same page about what was already done. Specifically:

1. **The breadcrumb said "NOT pushed" but the commits were already on GitHub.** Always verify actual state with `git log origin/main..HEAD --oneline` and a fetch from the public release page before trusting a breadcrumb.
2. **A v0.7.1 release was created as a Draft early in the session (before the breadcrumb was written), and a v0.7.1 git tag had been pushed.** The next session's "create release" form rejected v0.7.1 as a duplicate tag, then offered to "edit existing notes" — which led Chad to a pre-existing release record. Confusing.
3. **GitHub's `/releases` page is cached for ~1-2 minutes** after a release is published. The direct tag URL (`/releases/tag/v0.7.1`) refreshes immediately. When verifying a fresh publish, prefer the tag URL.
4. **Chad got confused about CI vs releases.** He saw a green check on the Actions page after pushing and assumed that meant the release was published. It wasn't — CI runs on every push, not just releases. Be explicit about this distinction in walkthroughs.
5. **GitHub renames release assets with spaces.** True Zero's CI uploads `True Zero.zip`, but GitHub stores it as `Cold.Bore.zip` (spaces → periods). The first manifest had `Cold%20Bore.zip` (URL-encoded space) and 404'd in the in-app banner. Fix was changing manifest URL to `Cold.Bore.zip`. **Going forward, either the workflow's zip step should produce a no-spaces name (`ColdBore.zip` or `Cold.Bore.zip`) directly so the rename never happens, OR future manifest URLs should always use the period form. Pick one and document it.** The breadcrumb actually mentioned this gotcha from v0.6.0 days but it didn't get applied to the manifest. Next time we ship a new release: either fix the workflow filename, or bake "use periods, not spaces, in the manifest URL" into the release procedure.

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

If it's been weeks or months since you worked on True Zero and you're not sure how to pick up — read this section first. It's written for you, not for Claude.

### How to resume

1. Open **Cowork** (the Claude desktop app).
2. Make sure it's pointed at your project folder: `~/Projects/Rifle Load Data`.
3. Type or paste this exact phrase to start:

> **"Continue building True Zero. Read Notes for next session.md and Build progress.md to catch up."**

Claude will read both files (about 30 seconds) and have full context of where the project stands. From there, ask whatever you need — "I want to add a LabRadar parser," "let's fix this bug," "let's start the iOS app," whatever.

### Quick sanity check before you start work

Run through these to make sure nothing rotted while you were away:

1. **True Zero.app still launches** — open from Applications → does the window appear?
2. **Update check works** — Tools → Check for Updates… → should say "you're up to date" (or show an available update if you've shipped a newer version since)
3. **Build still works** — double-click `Build App.command` → should succeed and produce a fresh `dist/True Zero.app`
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
- **Your config**: `~/Library/Application Support/True Zero/config.json` — auto-update preferences, project folder pointer
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

- **Don't delete the project folder** even if you stop using True Zero. Coming back from "I have the .app and GitHub but not the source" is much harder than starting cold.
- **Don't move the project folder** without telling Claude. The config has the path baked in. (If you do move it, just tell Claude — easy to update.)
- **Don't lose the GitHub login** — if you forget your GitHub password, recovery is annoying. Save it in your password manager now if you haven't.

### Once a year ritual (recommended)

Even if you have no changes to ship, run `Build App.command` once a year. If it fails, fix it then — when there's no pressure. The fix is usually one line. Letting failures pile up makes resuming much harder.

### Tool choice: Cowork vs Claude Code

True Zero was built using **Claude Cowork** (the desktop app) and that's what you should keep using. The other option — **Claude Code** (terminal-based CLI) — would be faster for pure coding work but loses Cowork's friendly UX, drag-and-drop file picker, plugin system, and the ability to mix code work with productivity tasks (Word docs, Excel, etc.).

You're not a developer. You value friendly explanations and clear next steps. Cowork fits that perfectly. The pace we've been working at — shipping releases monthly or so — doesn't need Claude Code's speed.

**Stick with Cowork unless one of these happens:**
- You're doing long debugging sessions where the sandbox round-trip starts to feel slow
- You want to run dev servers locally and watch them in real time
- Cowork stops working on a platform you need (e.g., if Cowork-for-Windows ever has issues during the Phase 7 port)

If any of those happens, Claude Code is the upgrade path — same Anthropic backend, just a more developer-focused interface. The project's breadcrumbs and conventions are tool-agnostic; both would understand True Zero the same way.

### To ship a new version

**Easiest path: come back here and ask Claude to walk you through it.** The release procedure has a few finicky steps (version bumps in two files, manifest URL update, GitHub release creation) and Claude can do most of the file editing for you. Sequence:

1. Tell Claude: "I want to ship True Zero v0.X.0 with [list of changes]"
2. Claude bumps version in `app/version.py` and `setup.py`, asks you to commit + push
3. Claude walks you through creating the GitHub release in the browser
4. CI auto-builds and attaches the zip (~3-5 min)
5. Claude updates `manifest.json` with the new version + URL, asks you to commit + push that
6. Done — friends' apps see the update on next launch

Each step where Claude does file editing replaces a manual step you'd otherwise have to do. Total time: 10-15 minutes including chat back-and-forth. Roughly half what it'd take solo, with no risk of forgetting to bump one of the two version files.

**Backup path if Claude isn't available**: see **`True Zero — How to Send Out Updates.docx`** in the project folder. Step-by-step in 5th-grade English.

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
| `Test True Zero.command` | Dev launcher for the GUI app — runs `app/main.py`. |
| `app/` | The new GUI app code (PyQt5). See "GUI app architecture" below. |
| `Build progress.md` | Tracks the GUI app build (phase status). |
| `Setup Instructions.docx` / `.md` | Full one-time setup walkthrough for the CLI flow. |
| `Garmin Imports/` | Drop Garmin CSVs here. |
| `BallisticX Imports/` | Drop BallisticX CSVs here. |

`import_data.py`'s `PROJECT = ...` constant near the top points at this folder for the CLI flow. The GUI app uses a config file at `~/Library/Application Support/True Zero/config.json` instead, with auto-detection of legacy folder locations on first run.

## GUI app architecture (`app/` folder)

| File | Purpose |
|---|---|
| `csv_router.py` | Thin wrapper around `parsers.detect_parser()` that returns the legacy KEY string |
| `main.py` | The PyQt5 window: drop zone, workbook picker, status counter, Run Import button, log area, update banner, Tools menu. Drops auto-route via the parser registry. Crash reporter wired in. |
| `config.py` | Load/save JSON config; `get_project_folder()` checks config + auto-detects legacy folder locations; legacy migration from "Rifle Load Importer" to "True Zero" |
| `setup_wizard.py` | `SetupWizard` QDialog for first-run; creates project folder, subfolders, copies bundled .xltx template |
| `updater.py` | `UpdateChecker(QThread)` — fetches JSON manifest, compares versions, emits result signal (non-blocking). `DEFAULT_MANIFEST_URL` baked in. |
| `version.py` | `APP_NAME`, `APP_VERSION`, `TEMPLATE_VERSION`, `DISCLAIMER_VERSION`, `DISCLAIMER_TEXT` |
| `theme.py` | Color palette, QSS, drop-zone & banner stylesheets, carbon-fiber tile generator |
| `disclaimer.py` | First-launch modal disclaimer dialog + acceptance tracking |
| `settings_dialog.py` | Tools → Settings… UI (auto-update toggle, manifest URL override, backup retention) |
| `help_dialog.py` | Tools → How to Use True Zero… UI (label format, workflow, workbook-tab guide, 3-load minimum, safety reminder). Non-modal so users can keep it open while they work. First menu item in Tools for discoverability. |
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
| `Build App.command` | Runs `setup.py py2app` — produces `dist/True Zero.app` |
| `Generate Icon.command` | Runs `app/resources/generate_icon.py` — produces `AppIcon.icns` |
| `Test True Zero.command` | Dev launcher — runs `app/main.py` directly |
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
- Phase 6 ✅ — py2app bundle shipping (True Zero.app at v0.6.0)
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
- **Sales / commercialization (Phase 9)** — Chad is interested in eventually selling True Zero. Full commercialization plan in `Build progress.md` under "Future: Sales readiness (Phase 9)" — Path A (low-effort tip jar / wait for signal) and Path B (full commercialization with LLC, trademark, lawyer, App Store, etc.). Year-1 revenue range: $0–60k depending on path and luck. When Chad says "let's commercialize" or "let's start selling", read that section.
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
