# Loadscope

**Loadscope finds your best rifle load.** It is a desktop app for precision
rifle handloaders on **macOS and Windows** — it reads your chronograph and your
target groups, scores every charge and seating depth you actually shot, and
names the winner.

Website and downloads: **https://loadscope.app**

## What it does

- **Plan a ladder.** Enter a starting charge or seating depth, a step, and the
  number of rungs; Loadscope lays out the test.
- **Import your range data.** Garmin Xero, LabRadar, MagnetoSpeed and Athlon
  Rangecraft for velocity; BallisticX, OnTarget, ShotMarker and Silver Mountain
  for targets. No renaming, no labelling — targets pair to velocity strings by
  shot order.
- **Measure groups from a photo.** Photograph the target, set the scale, mark
  the shots. Loadscope reads group size, **mean radius** and vertical
  dispersion.
- **Score every rung on four metrics** — velocity flat-spot, velocity standard
  deviation, mean radius and vertical SD — weighted for the distance you are
  shooting, out to 1500 yards. Lowest composite wins.
- **Carry it to the range.** Printed load cards and pocket cards, a ballistic
  solver with live conditions, and free iPhone companion apps
  ([Loadscope Ballistics](https://apps.apple.com/app/loadscope-ballistics/id6777277349),
  [Loadscope Measure](https://apps.apple.com/app/loadscope-measure/id6785319358)).

Everything runs on your own computer. No account, no subscription, no cloud —
your load data never leaves your machine.

**Loadscope does not generate or publish load data.** It scores the loads you
have already safely worked up and fired. Always work up loads from published
manufacturer data.

---

## About this repository

This repo is intentionally limited to:

- `docs/` — the public website served by GitHub Pages at **loadscope.app**
  (custom domain set via `docs/CNAME`).
- `manifest.json` — the auto-update manifest the Loadscope app reads from
  `https://raw.githubusercontent.com/chadheidt/coldbore/main/manifest.json`.

**The Loadscope application source is proprietary and lives in a private
repository.** Do not add application code here. Website and release-manifest
changes are published to this repo from the private repo via the documented
publish step.

(c) 2026 Loadscope LLC. All rights reserved.
