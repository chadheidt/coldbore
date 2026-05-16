# Ballistic Solver — Gate 1 Validation RESULT (executed 2026-05-16)

**You asked: "Are you able to do the gate-1 items and test them yourself?"
Yes — done.** I drove **JBM Ballistics' `jbmtraj-5.1`** directly (the
standard free G7 point-mass solver that commercial solvers are
themselves checked against), ran all 4 reference loads, and diffed it
against Loadscope. It is now an automated regression test in the suite.

## Headline

Gate-1 validation **caught two real bugs**, both now fixed, and
Loadscope now matches JBM **within 0.07 mil at every range on every one
of the 4 reference loads, for elevation AND wind** — inside the stated
0.1 mil gate-1 tolerance. Most points are 0.00–0.03 mil (effectively
identical).

This is exactly what the gate existed for: the earlier self-validation
passed with wide bands and **hid** these errors. An authoritative
external solver did not.

## The two bugs gate 1 caught (and the fixes)

**Bug 1 — wrong drag table (under-drag).** Loadscope's bundled G7 drag
table was a hand-truncated 20-point version whose supersonic drag
values were **5–15% too low** (e.g. at Mach 2.0 it had 0.2604 vs the
true standard 0.2980). Effect: the bullet kept ~8% too much velocity by
1000 yd, so time-of-flight and wind were under-predicted.
*Fix:* replaced it with **the authoritative 84-point standard G7
(McCoy) drag function published by JBM itself** — the exact table JBM's
solver integrates. Velocity now agrees with JBM to within 0.3% at all
ranges; wind to within 0.02 mil.

**Bug 2 — wrong sight geometry (come-up inflated).** The zeroing code
modelled the line of sight as a flat line *sight-height below the
bore* and bisected a launch angle to that. It should be the straight
sight line from the scope (which sits *above* the bore) re-zeroed at
the zero range. Effect: come-up was inflated ~0.5–0.9 mil, identically
across all loads (the load-independence is what proved it was geometry,
not drag).
*Fix:* fire along the bore and re-zero the straight sight line
analytically — the standard exterior-ballistics method, and exactly how
a pro solver's level-scope output is zeroed.

## The numbers (Loadscope vs JBM, 100 yd zero, ICAO std, 10 mph 3-o'clock)

Δ = Loadscope − JBM, in mils. (Tolerance: |Δ| < 0.10 mil.)

| Load | 500 yd elev Δ | 1000 yd elev Δ | 1000 yd wind Δ |
|---|---|---|---|
| 6.5 CM 140 ELD-M (2710, G7 .315) | +0.01 | +0.05 | 0.00 |
| .308 175 SMK (2650, G7 .243) | +0.01 | +0.07 | +0.02 |
| .300 PRC 225 ELD-M (2810, G7 .391) | 0.00 | +0.03 | +0.01 |
| 6 ARC 108 ELD-M (2700, G7 .347) | +0.01 | +0.03 | 0.00 |

Worst case anywhere across all loads/ranges/both axes: **0.069 mil**
(the .308 at 1000 yd, where it has gone transonic ~Mach 1.0 — the
single hardest point for any solver; everything supersonic is
0.00–0.03 mil).

The captured JBM data is saved as `tests/jbm_reference.json` and is now
a permanent automated regression guard
(`test_matches_jbm_reference_within_gate1_tolerance`), so the solver
can never silently drift from the reference again. Full suite: **185
green**.

## What this does and does NOT mean (honest status)

**Validated:** Loadscope's solver math now agrees with the authoritative
standard G7 point-mass reference to well inside the project tolerance,
on 4 diverse loads, across 100–1000 yd, elevation and wind. The math is
sound.

**Still open / unchanged:**
- This is the G7 point-mass reference (JBM). Measured-drag solvers
  (Hornady 4DOF, Applied Ballistics) use Doppler/Litz curves and will
  differ slightly **by design**, mostly deep transonic — that's
  expected and is itself part of the honest "how it works" story, not a
  bug. An optional cross-check there is a nice-to-have, not blocking.
- BC database (gate 2), disclaimer (gate 3), predicted-vs-confirmed UX
  (gate 4) are **unchanged** — still required before the solver wires
  in / ships. This used published BCs as shared test inputs only.

> ⚠️ **YOUR TO-DO — gate 1 sign-off (your call, not urgent):**
> **Gate 1's technical work is done and passing. All that's left for gate 1 is your judgement call: (a) accept the JBM validation as sufficient and let me proceed to gates 2–4, or (b) you also want an optional cross-check against a measured-drag solver (4DOF/AB) first — say which and I'll set that up. Either way, no debugging remains.**

*Generated 2026-05-16. Solver still NOT wired / NOT shipped (gates 2–4).
Supersedes the earlier "Gate 1 Validation Packet" (that was the
pre-run plan; this is the result).*
