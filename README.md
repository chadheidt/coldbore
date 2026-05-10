# Cold Bore

A Mac app for precision rifle handloaders. Drag your Garmin Xero (chronograph) and BallisticX (target group) CSVs into the window, and Cold Bore organizes the data into a structured Excel workbook that scores each load and points to the best one.

## What it does

- **Auto-imports** velocity data from Garmin Xero and group analysis from BallisticX
- **Scores** every load on velocity consistency, SD, group size, and vertical dispersion
- **Recommends** the suggested winning powder charge and seating depth
- **Pluggable parser registry** so support for new chronographs and analysis apps is one new file
- **First-launch wizard**, in-app update check, printable load cards, load sharing between users, opt-in crash reporting

## Install

Cold Bore is in **private beta**. Each tester gets a unique access code that unlocks both the download and the app itself.

1. Visit [https://chadheidt.github.io/coldbore/](https://chadheidt.github.io/coldbore/)
2. Click **Download Cold Bore**, paste the access code you were emailed
3. Open the downloaded `Cold.Bore.dmg`, drag **Cold Bore** to Applications
4. Open Cold Bore from Applications, paste the same access code in the license dialog
5. Follow the first-launch wizard to set up your Cold Bore folder

Cold Bore is signed and notarized by Apple — no "unidentified developer" warning on first launch.

To request an access code, email `coldboreapp@gmail.com`.

## Develop

Source code is laid out as:

| Folder | What's inside |
|---|---|
| `app/` | PyQt5 GUI code, parsers, theme, settings, load card, load sharing, license gate |
| `app/parsers/` | Pluggable parser registry — drop a new module to add a chronograph |
| `tests/` | Pytest suite covering parsers, validation, helpers, license validator |
| `setup.py` | py2app build config |
| `tools/` | Build helpers and license-key generator |

To build locally on macOS:

```sh
./Build\ Signed\ App.command
```

To run tests:

```sh
./Run\ Tests.command
```

## Distribution architecture

For privacy and access control, Cold Bore's binaries are not hosted on GitHub. The `.dmg` and auto-update `.zip` live in **Cloudflare R2** and are served through a **Cloudflare Worker** that validates the user's access code server-side and returns a 5-minute signed URL. The website Download button and the in-app auto-updater both authenticate through the same Worker.

See `Build progress.md` and `Notes for next session.md` for the full architecture details.

## Disclaimer

Cold Bore is a data-analysis tool. It is **not** a source of load data and does not recommend specific charge weights for use in any firearm. Reloading is inherently dangerous; always cross-reference loads against published reloading manuals from powder, bullet, and cartridge manufacturers, watch for pressure signs, and start below maximum loads. The developer is not liable for any damage, injury, or loss resulting from use of this app.
