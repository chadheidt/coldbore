# Send Cold Bore to friends

Bookmark this file. Everything you need to share Cold Bore is here.

---

## The link

This URL ALWAYS points to the newest release. Never changes, even when you ship updates.

```
https://github.com/chadheidt/coldbore/releases/latest
```

When a friend clicks it:
1. They land on the release page.
2. They click **Cold Bore.zip** under "Assets" to download.
3. The zip contains both the app AND the Quick Start guide — they open the .docx, follow the instructions, and they're running.

---

## Copy-paste message to send

Pick whichever one fits the friend.

### Short version (text message):

> Sending you Cold Bore — Mac app I built for tracking rifle load development. Download the zip, drag the app to Applications, then **right-click → Open** the very first time (Mac will warn — it's normal). Quick Start docx is in the zip and explains everything else. https://github.com/chadheidt/coldbore/releases/latest

### Longer version (email):

> Hey,
>
> Want to send you something I've been working on. Cold Bore is a Mac app I built that takes Garmin Xero and BallisticX CSV files and auto-fills my load development workbook — so I don't have to type velocity / SD / group size / etc. by hand after every range trip.
>
> Download here:
> https://github.com/chadheidt/coldbore/releases/latest
>
> Click **Cold Bore.zip** under "Assets". The zip contains both the app and a one-page Quick Start guide.
>
> Important first-time-only step: when you double-click the .app, macOS will throw a scary warning that "Apple cannot check it for malicious software." That's just because I'm not a paid Apple developer ($99/yr — overkill for sharing with friends). To get past it: **right-click the app → Open**. You'll get an "Open anyway" button. After that first launch, double-click works normally.
>
> Holler if anything's weird. Built for me but I think it'll be useful for you.
>
> — Chad

---

## Common questions friends will ask

**"Where do I drop my CSVs?"**
Just drag them onto the Cold Bore window (or onto the Cold Bore icon in the Dock). The app figures out whether each one is Garmin or BallisticX and routes it correctly.

**"What format do my BallisticX filenames need?"**
Rename each BallisticX CSV to match the load label, e.g. `P1 45.5 H4350.csv`. The first part (`P1`, `S3`, `CONFIRM-1`) is the test tag. The number is the charge weight or seating jump. The last word is the powder name. The Quick Start docx covers this in detail.

**"Why isn't anything updating?"**
Make sure Excel is closed before running the import — Cold Bore can't write to a workbook that's already open. Also make sure they're using their working .xlsx file (not the .xltx template).

**"How do I get a new version when you ship one?"**
The app checks automatically on launch. When a new version is out, a yellow banner appears at the top of the window with a download link. They click it, get the new zip, replace the .app in Applications. Done.

---

## Versions you've shipped (running list)

| Version | Date | What was new |
|---|---|---|
| v0.6.0 | May 7, 2026 | First public release. Drop zone, auto-import, first-run wizard, update check, py2app bundle, custom theme. |
| v0.7.0 | May 8, 2026 | UX polish round. Bigger window with saved geometry, Tools menu (Run Import / Restore From Backup / Start New Cycle), macOS notifications, CSV preflight, confirm-on-quit, first-launch tutorial. Plus a 14-issue audit pass. |
| v0.7.1 | May 8, 2026 | Quick Start guide bundled into the release zip — friends now get app + install instructions in a single download. No app changes since 0.7.0. |

When you ship a new version, ask Claude to add a row here.
