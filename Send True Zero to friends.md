# Send Loadscope to friends

Bookmark this file. Everything you need to share Loadscope is here.

---

## The link

This is the only URL you ever need to share. Never changes.

```
https://chadheidt.github.io/coldbore/
```

Loadscope is in private beta — the website Download button is gated behind a unique access code. Each tester needs both **the link AND their personal access code** to install.

---

## Before you send: issue the tester a key

Every new tester needs a unique CBORE-XXXX-XXXX-XXXX-XXXX code. The full click-by-click for issuing a code is in `Loadscope — How to Issue License Keys.docx` on your Desktop. Short version:

1. `python3 tools/generate_license_key.py` to get a fresh code
2. Add it to `app/license.py`'s `VALID_KEYS` set
3. Add it to the Cloudflare Worker's `VALID_CODES` set (dashboard → Workers & Pages → coldbore-download → Edit code)
4. Record the tester's name + code in `beta-keys.txt`
5. Ship a small app release so the new key is included
6. Email the tester (template below)

The same code unlocks the website download AND the app on first launch.

---

## Copy-paste message to send

Pick whichever one fits the friend. Replace `CBORE-XXXX-XXXX-XXXX-XXXX` with their actual code.

### Short version (text message):

> Sending you Loadscope — Mac app I built for tracking rifle load development. It's in private beta so you'll need this access code: `CBORE-XXXX-XXXX-XXXX-XXXX`. Click Download at https://chadheidt.github.io/coldbore/ and paste the code. After installing, open Loadscope and paste the same code in the license dialog. The Quick Start docx is on the disk image. Don't share the code please — it's tied to you so I can follow up.

### Longer version (email):

> Hey,
>
> Want to send you something I've been working on. Loadscope is a Mac app I built that takes Garmin Xero and BallisticX CSV files and auto-fills my load development workbook — so I don't have to type velocity / SD / group size / etc. by hand after every range trip.
>
> Loadscope is in private beta. To install it, you'll need your personal access code:
>
> `CBORE-XXXX-XXXX-XXXX-XXXX`
>
> Steps:
> 1. Visit https://chadheidt.github.io/coldbore/
> 2. Click **Download Loadscope** at the top of the page. A small window will pop up asking for your access code — paste the one above.
> 3. The Loadscope disk image will download. Double-click it, drag **Loadscope** to the **Applications** shortcut in the same window.
> 4. Open Loadscope from your Applications folder. A license dialog will appear — paste the same access code again to unlock the app.
> 5. The Quick Start guide is on the disk image (and a copy stays with the .dmg in your Downloads folder if you ever need it).
>
> Loadscope is signed and notarized by Apple — no "unidentified developer" warning, no right-click trick.
>
> One ask: please don't share the access code with anyone else. Each tester has a unique code so I can follow up individually on what you find. If something goes weird and you want a friend to try it, just send them my way (support@loadscope.app) and I'll set them up properly.
>
> Holler if anything's broken or confusing. Built for me but I think it'll be useful for you.
>
> — Chad

---

## Common questions friends will ask

**"Where do I drop my CSVs?"**
Just drag them onto the Loadscope window (or onto the Loadscope icon in the Dock). The app figures out whether each one is Garmin or BallisticX and routes it correctly.

**"What format do my BallisticX filenames need?"**
Rename each BallisticX CSV to match the load label, e.g. `P1 45.5 H4350.csv`. The first part (`P1`, `S3`, `CONFIRM-1`) is the test tag. The number is the charge weight or seating jump. The last word is the powder name. The Quick Start docx covers this in detail.

**"Why isn't anything updating?"**
Make sure Excel is closed before running the import — Loadscope can't write to a workbook that's already open. Also make sure they're using their working .xlsx file (not the .xltx template).

**"How do I get a new version when you ship one?"**
The app checks automatically on launch. When a new version is out, a yellow banner appears at the top of the window. They click **Install Update** (the app downloads in the background using their license key for authentication), then **Quit and Install** when ready. Loadscope quits, swaps itself, and reopens at the new version — no manual download or drag-to-Applications needed.

**"I lost my access code, can I get it back?"**
They email you. Their code is in `beta-keys.txt`.

**"Can I install Loadscope on my second Mac?"**
Currently yes — the same code works on multiple Macs (no per-machine binding yet). When sales-mode launches, that becomes 1-2 activations per code.

---

## Versions you've shipped (running list)

| Version | Date | What was new |
|---|---|---|
| v0.6.0 | May 7, 2026 | First public release. Drop zone, auto-import, first-run wizard, update check, py2app bundle, custom theme. |
| v0.7.0 | May 8, 2026 | UX polish round. Bigger window with saved geometry, Tools menu (Run Import / Restore From Backup / Start New Cycle), macOS notifications, CSV preflight, confirm-on-quit, first-launch tutorial. Plus a 14-issue audit pass. |
| v0.7.1 | May 8, 2026 | Quick Start guide bundled into the release zip. |
| v0.8.0 | May 9, 2026 | **In-app self-installer (Phase 12).** Yellow update banner now has Install Update + Quit and Install buttons. |
| v0.8.5 | May 10, 2026 | Build fixed for Intel Macs. |
| v0.8.6 | May 10, 2026 | First successful in-app auto-update test. |
| v0.9.0 | May 10, 2026 | **First Apple-signed + notarized release.** No more Gatekeeper warning on first launch. .dmg installer with drag-to-Applications layout. |
| v0.10.0 | May 10, 2026 | **License-key gate for beta lockdown.** App refuses to open without a valid CBORE code. |
| v0.10.1 | May 10, 2026 | License dialog UI polish + auto-updater `ditto` fix. |
| v0.11.0 | May 10, 2026 | **Private downloads via Cloudflare Worker + R2.** No public binary URL anywhere; both the website download AND the in-app updater authenticate via license key. This is the first release safe to send to non-tester friends, since random visitors to the website can't even download without a code. |

When you ship a new version, ask Claude to add a row here.
