#!/usr/bin/env python3
"""
Rifle Loads — Import Data

Walks every parser's import folder (Garmin Imports/, BallisticX Imports/, etc.),
parses each CSV with its registered parser, and writes the data into the
active working .xlsx in this project folder.

Run via: double-click "Import Rifle Data.command" on your Desktop.

CSV parsing is delegated to the parser registry in app/parsers/. Adding support
for a new chronograph or target-analysis app means dropping a new file in
app/parsers/ — see app/parsers/__init__.py for the contract.
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from openpyxl import load_workbook

PROJECT = os.path.expanduser("~/Documents/Claude/Projects/Rifle Load Data")
GARMIN_DIR = os.path.join(PROJECT, "Garmin Imports")
BX_DIR = os.path.join(PROJECT, "BallisticX Imports")

# Make the parser registry importable. import_data.py runs from the project
# root (CLI flow) and from inside the bundled .app, so add app/ to sys.path.
_HERE = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.join(_HERE, "app")
if os.path.isdir(_APP_DIR) and _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from parsers import ALL_PARSERS, chronograph_parsers, group_parsers


# Backwards-compatible re-exports for any old callers that imported these
# helpers directly from import_data (e.g., older test scripts).
from parsers._common import parse_label, extract_inches, extract_signed  # noqa: F401


# Sanity ranges for incoming data — we WARN but don't reject if values fall
# outside these. They're meant to catch obvious garbage (parsing failures,
# Garmin reading a phantom shot, BallisticX CSV from the wrong source).
# Tuned wide enough to accept anything plausible from a rifle cartridge.
SANITY_VEL_FPS = (500, 5000)         # rifle muzzle velocity in fps
SANITY_SD_FPS = (0, 60)              # standard deviation in fps
SANITY_ES_FPS = (0, 200)             # extreme spread in fps
SANITY_GROUP_IN = (0, 10)            # group size in inches at any reasonable distance
SANITY_VERTICAL_IN = (0, 10)         # vertical dispersion in inches
SANITY_MR_IN = (0, 10)               # mean radius in inches
SANITY_CHARGE_GR = (5, 200)          # powder charge weight (grains) — covers everything from .22 to magnum
SANITY_BULLET_WT_GR = (10, 800)      # bullet weight (grains)


def _validate_chronograph_record(d, source_filename, warnings):
    """Sanity-check a chronograph record. Append human-readable warnings to
    the warnings list rather than raising — the data still gets imported,
    but the user sees a flagged note in the activity log."""
    name = source_filename
    tag = d.get("Tag", "?")

    avg_vel = d.get("AvgVel")
    if avg_vel is not None and not (SANITY_VEL_FPS[0] <= avg_vel <= SANITY_VEL_FPS[1]):
        warnings.append(f"  ⚠ {name} ({tag}): AvgVel {avg_vel} fps is outside "
                        f"plausible range ({SANITY_VEL_FPS[0]}-{SANITY_VEL_FPS[1]})")

    sd = d.get("SD")
    if sd is not None and not (SANITY_SD_FPS[0] <= sd <= SANITY_SD_FPS[1]):
        warnings.append(f"  ⚠ {name} ({tag}): SD {sd} fps is outside "
                        f"plausible range ({SANITY_SD_FPS[0]}-{SANITY_SD_FPS[1]})")

    es = d.get("ES")
    if es is not None and not (SANITY_ES_FPS[0] <= es <= SANITY_ES_FPS[1]):
        warnings.append(f"  ⚠ {name} ({tag}): ES {es} fps is outside "
                        f"plausible range ({SANITY_ES_FPS[0]}-{SANITY_ES_FPS[1]})")

    bw = d.get("BulletWt")
    if bw is not None and not (SANITY_BULLET_WT_GR[0] <= bw <= SANITY_BULLET_WT_GR[1]):
        warnings.append(f"  ⚠ {name} ({tag}): BulletWt {bw} gr is outside "
                        f"plausible range ({SANITY_BULLET_WT_GR[0]}-{SANITY_BULLET_WT_GR[1]})")

    charge = d.get("ChargeOrJump")
    # ChargeOrJump can be either a powder charge (5-200 grains) or a jump
    # (typically 0-0.2 inches). Skip range check — too ambiguous to flag.

    # Per-shot velocities
    shots = d.get("Shots") or []
    for i, shot in enumerate(shots):
        if shot is None:
            continue
        if not (SANITY_VEL_FPS[0] <= shot <= SANITY_VEL_FPS[1]):
            warnings.append(f"  ⚠ {name} ({tag}): Shot {i+1} velocity {shot} fps "
                            f"is outside plausible range ({SANITY_VEL_FPS[0]}-{SANITY_VEL_FPS[1]})")


def _validate_group_record(g, source_filename, warnings):
    """Sanity-check a target-group record."""
    name = source_filename
    tag = g.get("Tag", "?")

    for field, label, rng in [
        ("GroupIn", "Group", SANITY_GROUP_IN),
        ("HeightIn", "Vertical", SANITY_VERTICAL_IN),
        ("MRIn", "Mean radius", SANITY_MR_IN),
    ]:
        v = g.get(field)
        if v is not None and not (rng[0] <= v <= rng[1]):
            warnings.append(f"  ⚠ {name} ({tag}): {label} {v}\" is outside "
                            f"plausible range ({rng[0]}-{rng[1]}\")")


def _check_duplicate_tags(records, label):
    """Return human-readable warnings for any tag that appears twice in records."""
    warnings = []
    by_tag = {}
    for r in records:
        tag = r.get("Tag", "")
        if not tag:
            continue
        by_tag.setdefault(tag, []).append(r)
    for tag, group in by_tag.items():
        if len(group) > 1:
            warnings.append(
                f"  ⚠ Duplicate tag '{tag}' in {label}: {len(group)} records share "
                f"this tag. The workbook will only show the last one for that row."
            )
    return warnings


def _read_backup_keep_setting(default=5):
    """Read the backup retention count from the GUI's config file. Falls back
    to `default` if config or app/ folder isn't available (e.g. running as the
    pure CLI flow without the GUI installed). 0 = disable backups."""
    try:
        import config as app_config  # only imports if app/ is on sys.path
        cfg = app_config.load_config()
        return int(cfg.get("backup_keep_count", default))
    except Exception:
        return default


def _rotate_workbook_backups(workbook_path, keep=5):
    """Keep a small rotating set of timestamped backups of the workbook in a
    .backups/ subfolder next to it. Called before each import so the user
    can recover from a botched run.

    Backups are named like:  <Workbook> 2026-05-07 14-32-08.xlsx
    Oldest are deleted once the count exceeds `keep`.
    """
    workbook_path = os.path.abspath(workbook_path)
    project_dir = os.path.dirname(workbook_path)
    backups_dir = os.path.join(project_dir, ".backups")
    os.makedirs(backups_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(workbook_path))[0]
    ext = os.path.splitext(workbook_path)[1]
    stamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    dest = os.path.join(backups_dir, f"{base} {stamp}{ext}")

    try:
        shutil.copy2(workbook_path, dest)
        print(f"  Backed up to: .backups/{os.path.basename(dest)}")
    except Exception as e:
        print(f"  WARNING: couldn't create backup: {e}")
        return

    # Rotate — delete oldest backups for THIS workbook beyond `keep`
    same_base_backups = sorted(
        [f for f in os.listdir(backups_dir)
         if f.startswith(base + " ") and f.endswith(ext)],
        reverse=True,  # newest first
    )
    for old in same_base_backups[keep:]:
        try:
            os.remove(os.path.join(backups_dir, old))
        except OSError:
            pass


def list_workbooks(project_dir=None):
    """Return a list of working .xlsx paths in the project folder, most-recent-first.

    Excludes .xltx template, Excel lock files (~$), and hidden files. This is the
    library function — both the CLI find_workbook() and the GUI use it.
    """
    if project_dir is None:
        project_dir = PROJECT
    candidates = []
    for f in os.listdir(project_dir):
        full = os.path.join(project_dir, f)
        if not os.path.isfile(full):
            continue
        if f.startswith("~$") or f.startswith("."):
            continue
        if f.lower().endswith(".xlsx") and "template" not in f.lower():
            candidates.append(full)
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates


def find_workbook():
    """Find the working .xlsx in the project folder (CLI flow).

    Behavior:
      - 0 working .xlsx files  →  return None (caller prints setup error)
      - 1 working .xlsx file   →  auto-pick it, no prompt
      - 2+ working .xlsx files →  print a numbered list and ask the user
                                  which one to import into
    """
    candidates = list_workbooks()
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # Multiple workbooks — prompt the user
    print("\n" + "=" * 60)
    print("Multiple working workbooks found in the project folder.")
    print("=" * 60)
    print("\nWhich workbook do you want to import into?\n")
    for i, path in enumerate(candidates, start=1):
        name = os.path.basename(path)
        mtime = os.path.getmtime(path)
        import datetime
        when = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        marker = "  (most recently edited)" if i == 1 else ""
        print(f"  {i}.  {name}    [{when}]{marker}")
    print()

    while True:
        try:
            choice = input(f"Type a number 1-{len(candidates)} (or press Enter for 1): ").strip()
        except EOFError:
            choice = ""
        if choice == "":
            return candidates[0]
        try:
            idx = int(choice)
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1]
        except ValueError:
            pass
        print(f"  Invalid choice. Type a number from 1 to {len(candidates)}.")


def write_chronograph_records(wb, records):
    """Write all chronograph session records to the GarminSessions hidden sheet.

    Sheet name is historical (kept as-is to avoid breaking existing workbooks),
    but it now holds chronograph data from any source — Garmin, LabRadar,
    MagnetoSpeed, etc. The Source field on each record indicates which parser
    produced it.
    """
    if "GarminSessions" not in wb.sheetnames:
        print("  ERROR: workbook has no GarminSessions sheet")
        return 0
    sht = wb["GarminSessions"]
    # Clear rows 2+
    for row in sht.iter_rows(min_row=2, max_row=sht.max_row):
        for cell in row:
            cell.value = None

    out_row = 2
    for d in records:
        sht.cell(row=out_row, column=1).value = d.get("Tag", "")
        sht.cell(row=out_row, column=2).value = d.get("ChargeOrJump")
        sht.cell(row=out_row, column=3).value = d.get("Powder", "")
        sht.cell(row=out_row, column=4).value = d.get("Date", "")
        for i, shot in enumerate((d.get("Shots") or [])[:7]):
            sht.cell(row=out_row, column=5 + i).value = shot
        sht.cell(row=out_row, column=12).value = d.get("AvgVel")
        sht.cell(row=out_row, column=13).value = d.get("SD")
        sht.cell(row=out_row, column=14).value = d.get("ES")
        sht.cell(row=out_row, column=15).value = d.get("BulletWt")
        sht.cell(row=out_row, column=16).value = d.get("AvgKE")
        sht.cell(row=out_row, column=17).value = d.get("SessionTitle", "")
        sht.cell(row=out_row, column=18).value = d.get("SessionNote", "")
        out_row += 1
    return out_row - 2


# Backwards-compat alias for any callers still using the old name
write_garmin = write_chronograph_records


def write_group_records(wb, bx_records):
    """Write all target-group records to the BallisticXGroups hidden sheet.

    Sheet name is historical — it now holds group analysis data from any
    target-analysis app, with Source indicating the originating parser.
    """
    if "BallisticXGroups" not in wb.sheetnames:
        print("  ERROR: workbook has no BallisticXGroups sheet")
        return 0
    sht = wb["BallisticXGroups"]
    for row in sht.iter_rows(min_row=2, max_row=sht.max_row):
        for cell in row:
            cell.value = None

    out_row = 2
    for g in bx_records:
        sht.cell(row=out_row, column=1).value = g.get("Tag", "")
        sht.cell(row=out_row, column=2).value = g.get("ChargeOrJump")
        sht.cell(row=out_row, column=3).value = g.get("Powder", "")
        sht.cell(row=out_row, column=4).value = g.get("Date", "")
        sht.cell(row=out_row, column=5).value = g.get("Distance")
        sht.cell(row=out_row, column=6).value = g.get("Caliber", "")
        sht.cell(row=out_row, column=7).value = g.get("GroupIn")
        sht.cell(row=out_row, column=8).value = g.get("WidthIn")
        sht.cell(row=out_row, column=9).value = g.get("HeightIn")
        sht.cell(row=out_row, column=10).value = g.get("MRIn")
        sht.cell(row=out_row, column=11).value = g.get("CEPIn")
        sht.cell(row=out_row, column=12).value = g.get("SDRadIn")
        sht.cell(row=out_row, column=13).value = g.get("SDVertIn")
        sht.cell(row=out_row, column=14).value = g.get("SDHorizIn")
        sht.cell(row=out_row, column=15).value = g.get("ElevOffsetIn")
        sht.cell(row=out_row, column=16).value = g.get("WindOffsetIn")
        sht.cell(row=out_row, column=17).value = g.get("Label", "")
        out_row += 1
    return out_row - 2


# Backwards-compat alias for any callers still using the old name
write_ballisticx = write_group_records


def run_import(workbook_path, project_dir=None, open_excel=True):
    """Read all CSVs in the import folders and write them into the workbook.

    Designed to be called from both the CLI (main()) and from the GUI app.
    Prints progress to stdout — capture with contextlib.redirect_stdout if you
    want to route the output somewhere other than the Terminal.

    Returns a dict:
        {
            "ok": True/False,
            "workbook": <path>,
            "garmin_rows": <int>,
            "ballisticx_rows": <int>,
            "error": <str or None>,
            "safety_stop": <bool>,   # True if no CSVs found and we did nothing
        }
    """
    if project_dir is None:
        project_dir = PROJECT

    print(f"\nWorkbook: {os.path.basename(workbook_path)}")

    # Walk every registered parser and pull records from its import folder.
    # Each file in a parser's folder is checked with that parser's detect() —
    # this means if you accidentally drop a Garmin CSV in BallisticX Imports/,
    # we won't try to parse it as a BallisticX file (it'll just be skipped
    # and you'll see a warning).
    chronograph_records = []
    group_records = []

    for parser in ALL_PARSERS:
        folder = os.path.join(project_dir, parser.IMPORT_FOLDER)
        print(f"\nReading {parser.NAME} CSVs from: {folder}")
        if not os.path.isdir(folder):
            print(f"  (folder doesn't exist — skipping)")
            continue
        for fn in sorted(os.listdir(folder)):
            if not fn.lower().endswith(".csv"):
                continue
            full = os.path.join(folder, fn)
            try:
                if not parser.detect(full):
                    print(f"  skip: {fn}  (doesn't look like a {parser.NAME} CSV)")
                    continue
                result = parser.parse(full)
            except Exception as e:
                print(f"  WARNING: {parser.NAME} parser failed on {fn}: {e}")
                continue

            if result is None:
                continue
            if isinstance(result, list):
                # Group parser — list of records
                group_records.extend(result)
                print(f"  parsed: {fn}  →  {len(result)} group(s)")
            else:
                # Chronograph parser — single record
                chronograph_records.append(result)
                shots_count = len(result.get("Shots") or [])
                print(
                    f"  parsed: {fn}  →  Tag={result.get('Tag')!r}, "
                    f"Charge={result.get('ChargeOrJump')}, "
                    f"Powder={result.get('Powder')!r}, {shots_count} shots"
                )

    print(f"\nTotals: {len(chronograph_records)} chronograph session(s), "
          f"{len(group_records)} target group(s)")

    # ---- Data validation (warnings only — non-blocking) ----
    warnings = []
    for d in chronograph_records:
        # We don't have the original filename per-record any more; use Tag/SessionTitle as identifier
        ident = d.get("SessionTitle") or d.get("Tag") or "?"
        _validate_chronograph_record(d, ident, warnings)
    for g in group_records:
        ident = g.get("Label") or g.get("Tag") or "?"
        _validate_group_record(g, ident, warnings)
    warnings += _check_duplicate_tags(chronograph_records, "Garmin/chronograph data")
    warnings += _check_duplicate_tags(group_records, "BallisticX/group data")
    if warnings:
        print(f"\nValidation warnings ({len(warnings)}):")
        for w in warnings:
            print(w)
        print("(Data was still imported — review the warnings above and your "
              "source CSVs to confirm the values are correct.)")

    # SAFETY CHECK — if no records anywhere, refuse to wipe the workbook.
    if not chronograph_records and not group_records:
        print("\n" + "=" * 60)
        print("SAFETY STOP — no CSVs found in either import folder.")
        print("=" * 60)
        print("\nNothing was written to the workbook. The existing data is untouched.")
        if open_excel:
            print("\nOpening the workbook anyway so you can review it.")
            subprocess.run(["open", workbook_path])
        return {
            "ok": True,
            "workbook": workbook_path,
            "garmin_rows": 0,
            "ballisticx_rows": 0,
            "error": None,
            "safety_stop": True,
        }

    # Backup the workbook before we modify it. If anything goes wrong (CSV
    # parse error mid-import, openpyxl bug, power outage), the user can
    # recover from the most recent backup. Retention count comes from settings.
    backup_keep = _read_backup_keep_setting(default=5)
    if backup_keep > 0:
        _rotate_workbook_backups(workbook_path, keep=backup_keep)
    else:
        print("  (Backups disabled in settings — skipping pre-import backup.)")

    # Open workbook and write data
    print(f"\nWriting to workbook…")
    try:
        wb = load_workbook(workbook_path, keep_vba=False)
    except Exception as e:
        msg = f"Couldn't open workbook: {e}. Is it open in Excel? Close it and try again."
        print(f"  ERROR: {msg}")
        return {
            "ok": False, "workbook": workbook_path,
            "garmin_rows": 0, "ballisticx_rows": 0,
            "error": msg, "safety_stop": False,
        }

    # Force save as regular workbook (not template)
    wb.template = False

    n_g = write_chronograph_records(wb, chronograph_records)
    n_b = write_group_records(wb, group_records)
    print(f"  Wrote {n_g} chronograph row(s) and {n_b} target-group row(s)")

    try:
        wb.save(workbook_path)
        print(f"  Saved.")
    except PermissionError:
        msg = "Workbook is open in Excel. Close it and try again."
        print(f"  ERROR: {msg}")
        return {
            "ok": False, "workbook": workbook_path,
            "garmin_rows": n_g, "ballisticx_rows": n_b,
            "error": msg, "safety_stop": False,
        }

    if open_excel:
        print(f"\nOpening workbook in Excel…")
        subprocess.run(["open", workbook_path])

    print("\nDONE.")
    return {
        "ok": True, "workbook": workbook_path,
        "garmin_rows": n_g, "ballisticx_rows": n_b,
        "error": None, "safety_stop": False,
    }


def main():
    """CLI entry point — used by 'Import Rifle Data.command'."""
    print("=" * 60)
    print("Rifle Loads — Import Data")
    print("=" * 60)

    workbook_path = find_workbook()
    if not workbook_path:
        print("\nERROR: No working .xlsx workbook found in:")
        print(f"  {PROJECT}")
        print("\nMake sure you have a saved working file (e.g., 'My Load 6.5CM.xlsx').")
        print("(The .xltx template is excluded — make a working copy via File > Save As first.)")
        sys.exit(1)

    result = run_import(workbook_path)
    print("=" * 60)
    if not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
