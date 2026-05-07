# Cold Bore

A Mac app for precision rifle handloaders. Drag your Garmin Xero (chronograph) and BallisticX (target group) CSVs into the window, and Cold Bore organizes the data into a structured Excel workbook that scores each load and points to the best one.

## What it does

- **Auto-imports** velocity data from Garmin Xero and group analysis from BallisticX
- **Scores** every load on velocity consistency, SD, group size, and vertical dispersion
- **Recommends** the suggested winning powder charge and seating depth
- **Pluggable parser registry** so support for new chronographs and analysis apps is one new file
- **First-launch wizard**, in-app update check, printable load cards, load sharing between users, opt-in crash reporting

## Install

1. Download the latest `Cold Bore.zip` from the [Releases](../../releases) page
2. Unzip → drag `Cold Bore.app` to your Applications folder
3. Right-click → **Open** the first time (one-time Gatekeeper bypass)
4. Follow the first-launch wizard to set up your Cold Bore folder

## Develop

Source code is laid out as:

| Folder | What's inside |
|---|---|
| `app/` | PyQt5 GUI code, parsers, theme, settings, load card, load sharing |
| `app/parsers/` | Pluggable parser registry — drop a new module to add a chronograph |
| `tests/` | Pytest suite covering parsers, validation, helpers |
| `setup.py` | py2app build config |
| `.github/workflows/` | CI/CD — runs tests on push, builds .app on release |

To build locally on macOS:

```sh
./Build\ App.command
```

To run tests:

```sh
./Run\ Tests.command
```

## Disclaimer

Cold Bore is a data-analysis tool. It is **not** a source of load data and does not recommend specific charge weights for use in any firearm. Reloading is inherently dangerous; always cross-reference loads against published reloading manuals from powder, bullet, and cartridge manufacturers, watch for pressure signs, and start below maximum loads. The developer is not liable for any damage, injury, or loss resulting from use of this app.
