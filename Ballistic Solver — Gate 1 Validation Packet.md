# Ballistic Solver — Gate 1 Validation Packet

**Purpose:** Ship-gate (1) for the ballistic solver says the solver's
predicted DOPE must be validated against a **live professional
ballistic solver** before it can be wired into Loadscope or shipped.
That live query can't be automated from here (the good free solvers are
interactive web apps), so this is the one solver task that needs Chad's
hands. This packet makes it a ~10-minute copy-and-read job instead of
you figuring out what to test.

**What this proves / doesn't prove:** this checks Loadscope's solver
*math* against an independent G7-BC solver given **identical inputs**.
It does NOT check whether a bullet's BC is correct — that's ship-gate
(2), separate. So enter the EXACT BC shown below into the other solver
too; any BC difference would just cancel out and tell us nothing.

---

## What you do (one solver, ~10 min)

> ⚠️ **YOUR TO-DO — gate 1, when you're ready to move the solver forward:**
> **1. Open the free GeoBallistics web calculator: https://geoballistics.app (no signup needed). It's a G7-BC point-mass solver — the same model class as Loadscope's, so it's an apples-to-apples check.**
> **2. For EACH of the 4 loads below, enter the inputs EXACTLY as written (muzzle velocity, the G7 BC shown, 100-yard zero, 1.75" sight height, standard atmosphere / ICAO 59°F / 29.92 inHg / sea level, 10 mph wind from 3 o'clock / full value).**
> **3. Read GeoBallistics' come-up (elevation) in MILS at 500 and 1000 yards, and its wind in MILS at 1000 yards. Write those three numbers into the "Pro solver" row for each load (the table has blanks ready).**
> **4. Send the filled-in tables back. I'll diff every number, flag anything outside the tolerance below, and we iterate the solver until it passes — THEN you review and we move to gates 2–4.**
> **Optional second opinion:** Hornady's free 4DOF web calc (https://www.hornady.com/4dof) will be close but is *expected to differ a little by design* — it uses Doppler-measured drag, not G7 BC. A small difference there is normal and is itself useful data, not a solver bug.

**Pass tolerance (from the solver plan):** Loadscope should land within
**0.1 mil / 0.5 MOA of the pro solver at 1000 yards**. Bigger gaps =
solver bug or an input mismatch — we fix before the solver ships.

---

## The 4 reference loads — Loadscope's predictions

All: 100-yard zero, 1.75" sight height, ICAO standard atmosphere
(59°F, 29.92 inHg, sea level, 0% RH), 10 mph wind from 3 o'clock
(full-value crosswind). "Elev" = come-up you'd dial.

> The G7 BC printed with each load is a widely published manufacturer
> figure used here only as a **shared test input** — enter the same
> number in GeoBallistics. It is NOT yet part of Loadscope's BC
> database (that's gate 2; the database currently ships with zero BC
> values on purpose).

### 1. 6.5 Creedmoor — 140 gr Hornady ELD-M — MV 2710 fps — **G7 BC 0.315**

| Range (yd) | Elev mil | Elev MOA | Drop (in) | Wind mil | Wind MOA | TOF (s) |
|---|---|---|---|---|---|---|
| 100 | 0.00 | 0.00 | 0.0 | 0.12 | 0.43 | 0.113 |
| 300 | 1.81 | 6.23 | 19.6 | 0.39 | 1.36 | 0.356 |
| 500 | 3.58 | 12.30 | 64.4 | 0.70 | 2.40 | 0.625 |
| 700 | 5.57 | 19.14 | 140.3 | 1.04 | 3.58 | 0.924 |
| 1000 | 9.18 | 31.56 | 330.5 | 1.66 | 5.70 | 1.446 |
| **Pro solver →** | _500: ___ mil_ | | | _1000 wind: ___ mil_ | | |
| | _1000: ___ mil_ | | | | | |

### 2. .308 Win — 175 gr Sierra MatchKing — MV 2650 fps — **G7 BC 0.243**

| Range (yd) | Elev mil | Elev MOA | Drop (in) | Wind mil | Wind MOA | TOF (s) |
|---|---|---|---|---|---|---|
| 100 | 0.00 | 0.00 | 0.0 | 0.17 | 0.58 | 0.117 |
| 300 | 1.95 | 6.70 | 21.0 | 0.55 | 1.88 | 0.373 |
| 500 | 3.96 | 13.61 | 71.3 | 0.99 | 3.41 | 0.667 |
| 700 | 6.37 | 21.90 | 160.6 | 1.52 | 5.23 | 1.010 |
| 1000 | 11.21 | 38.52 | 403.4 | 2.56 | 8.78 | 1.655 |
| **Pro solver →** | _500: ___ mil_ | | | _1000 wind: ___ mil_ | | |
| | _1000: ___ mil_ | | | | | |

### 3. .300 PRC — 225 gr Hornady ELD-M — MV 2810 fps — **G7 BC 0.391**

| Range (yd) | Elev mil | Elev MOA | Drop (in) | Wind mil | Wind MOA | TOF (s) |
|---|---|---|---|---|---|---|
| 100 | 0.00 | 0.00 | 0.0 | 0.09 | 0.32 | 0.109 |
| 300 | 1.67 | 5.74 | 18.0 | 0.29 | 1.01 | 0.338 |
| 500 | 3.23 | 11.09 | 58.1 | 0.51 | 1.76 | 0.586 |
| 700 | 4.91 | 16.89 | 123.8 | 0.75 | 2.58 | 0.855 |
| 1000 | 7.81 | 26.86 | 281.3 | 1.16 | 3.98 | 1.304 |
| **Pro solver →** | _500: ___ mil_ | | | _1000 wind: ___ mil_ | | |
| | _1000: ___ mil_ | | | | | |

### 4. 6mm ARC — 108 gr Hornady ELD-M — MV 2700 fps — **G7 BC 0.347**

| Range (yd) | Elev mil | Elev MOA | Drop (in) | Wind mil | Wind MOA | TOF (s) |
|---|---|---|---|---|---|---|
| 100 | 0.00 | 0.00 | 0.0 | 0.11 | 0.39 | 0.113 |
| 300 | 1.81 | 6.21 | 19.5 | 0.36 | 1.23 | 0.355 |
| 500 | 3.54 | 12.18 | 63.8 | 0.63 | 2.16 | 0.620 |
| 700 | 5.47 | 18.80 | 137.8 | 0.93 | 3.21 | 0.911 |
| 1000 | 8.89 | 30.55 | 319.9 | 1.46 | 5.03 | 1.411 |
| **Pro solver →** | _500: ___ mil_ | | | _1000 wind: ___ mil_ | | |
| | _1000: ___ mil_ | | | | | |

---

## Self-check status (necessary, NOT sufficient)

Loadscope's solver already passes an automated self-validation harness
(`tests/test_ballistics.py`, 20 tests): hard physics invariants
(~0 come-up at the zero, monotonic come-up, plausible & rising TOF,
growing crosswind drift, dt-independent results, integrated crosswind
matching the textbook lag rule) plus a wide published-ballpark band for
load #1. That confirms the math is "in the right regime and not
broken" — it is **necessary but not sufficient**. This live cross-check
is the authoritative gate, on purpose.

*Generated 2026-05-16 from `app/ballistics.py` after the numerical-
hardening pass (target-range interpolation + full point-mass
crosswind). Solver remains unwired and unshipped until gates 1–4 clear.*
