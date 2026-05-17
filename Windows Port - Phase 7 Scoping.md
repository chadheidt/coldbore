# Windows Port — Phase 7 Scoping (2026-05-17)

Desk-research scoping pass (no Windows laptop required for this document).
Source of truth for the Phase 7 plan going forward.

## Executive summary

Windows is a **port, not a rewrite.** The hard, valuable core of Loadscope
is already platform-independent Python. The work is platform *plumbing* —
packaging, a thin OS-abstraction layer, a Windows updater/installer — plus
one real-world long-lead item: a Windows code-signing certificate.

**Honest effort:** ~1–3 focused weeks of engineering + a Windows test
cycle, gated by (a) code-signing cert procurement lead time and (b) needing
Chad's Windows laptop for build/test/sign. Lower *risk* than it sounds
(core is proven); the cert is the critical path.

## Portability assessment (measured from the codebase 2026-05-17)

**Fully portable as-is (the bulk + all the hard IP):**
- CSV parsers (`app/parsers/`) — pure Python.
- **Workbook write path: `import_data.py` uses `openpyxl` (pure Python, cross-platform).** The .xlsx — including the scoring formulas — is written directly by openpyxl. Excel is NOT the engine; Excel only *recalculates/displays* when the user opens the file.
- Ballistic solver (`dope_solver.py`, `ballistics.py`), scoring, BC database (`component_data.py`).
- **PyQt5 UI — runs natively on Windows.** The entire UI ports with minimal change (Qt is cross-platform). This is *the* reason Windows ≠ iOS (iOS would be a SwiftUI rewrite; Windows is not).

**Mac-only — needs a Windows path (only 4 files use AppleScript/osascript):**
1. `app/main.py` (~5 sites) — "open/print your workbook in Excel". Windows: `os.startfile(path)` to open in the default app; print via the shell `print` verb or Excel COM (`pywin32`) if needed. **Low–medium.**
2. `app/excel_chrome.py` (~6) + `app/demo_tour.py` (~13) — demo-tour Excel-chrome cosmetics. The demo is now **pre-rendered images (Path B)**; this AppleScript path is largely legacy/dead. Windows: no-op/exclude. **Low.**
3. `app/installer.py` (~2) — the Mac auto-updater (bash + `.app` swap). Windows needs its own updater (download zip → replace install dir → relaunch), or adopt a framework (e.g., WinSparkle, the Windows analogue of Sparkle). **Medium — real work.**
4. Filesystem paths — Mac `~/Library` / `~/Documents` conventions throughout. Needs a platform-aware paths module (`%USERPROFILE%\Documents`, `%APPDATA%`). Also partially benefits a future iOS sandbox. **Medium.**

No existing `sys.platform`/`os.name` branching exists — so part of the work is introducing a clean **platform-abstraction layer** so Mac behavior is unchanged and Windows gets equivalents (don't litter `if win` everywhere).

## Work breakdown

| Component | Approach | Size |
|---|---|---|
| Packaging | `py2app` → **PyInstaller** (bundle PyQt5 + openpyxl) | M |
| OS-abstraction layer | paths + "open/print workbook" + no-op dead demo AppleScript | M |
| Auto-updater (Windows) | custom (zip → replace → relaunch) or **WinSparkle** | M |
| Installer | **Inno Setup** (recommended) or NSIS / MSI | M |
| **Code signing** | **OV/EV cert from a CA (Sectigo/DigiCert), likely hardware token** | **procurement-heavy, code-light — CRITICAL PATH** |
| File associations | `.xlsx`/import-folder behavior parity (registry ProgID) | S |
| Test cycle | on Chad's Windows laptop (build/run/sign/install) | M |

## Critical path & long-lead item

**Windows code signing is the gate.** Unlike Apple's tidy $99 Developer ID +
notarization, current Windows signing effectively requires an **OV or EV
code-signing certificate from a CA**, with business-identity vetting and
(for EV / post-2023 norms) a **hardware token / HSM**. More money, more
paperwork, real lead time (days–weeks). Without it, Windows SmartScreen
warns users harshly (worse than macOS Gatekeeper). **This should be started
early, in parallel with the build** — it does not block writing code but it
blocks shipping a non-scary installer.

Chad-action items (cannot be Claude-driven): purchase + identity-verify the
code-signing cert; provide the Windows laptop for build/test/sign.

## Risks

- Cert procurement timeline/cost (mitigate: start early, parallel to build).
- PyInstaller + PyQt5 packaging quirks on Windows (well-trodden; budget iteration).
- The Mac updater design doesn't port; the Windows updater is genuinely new code (mitigate: WinSparkle is mature).
- openpyxl writes formulas but does NOT calculate them — same as today on Mac; Windows users still need Excel (or a compatible spreadsheet) installed to *see* recalculated results. Document this; it's unchanged behavior, not a regression. (Longer-term de-risk: a headless calc path, but out of scope for the port.)

## Recommended approach & sequencing

- **Stack:** PyInstaller + Inno Setup + WinSparkle + a `app/platform/` abstraction layer; keep one shared codebase, Mac behavior untouched.
- **Sequencing (per roadmap + pre-beta plan):** the immediate path is pre-beta Step 4 (descriptions/social) → beta. Windows is Phase 7, high-leverage, *after* beta/with commercial traction. **BUT** start the **code-signing cert procurement now/early** regardless — it's the long pole and is pure Chad-action lead time.
- **First build steps when Phase 7 starts:** (1) PyInstaller spec that runs the app on Windows from source; (2) platform-abstraction layer (paths + open/print); (3) Windows updater; (4) Inno Setup installer; (5) sign with the procured cert; (6) full test cycle on Chad's laptop.

## Bottom line

Feasible, lower-risk than it feels (the core is done and portable), a
multi-week phase whose real constraint is the code-signing cert, not the
code. ~5x addressable-market upside (most reloaders are on Windows) — the
single highest-leverage growth move once beta validates the product.
