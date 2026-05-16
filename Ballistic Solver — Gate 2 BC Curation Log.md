# Ballistic Solver — Gate 2: BC Database Curation Log

**Your decisions (locked):** manufacturer's own published BC = source of
record; JBM library = independent cross-check; curate the 61 seed
bullets now; **anything not corroborated is left blank** (the app then
asks the shooter to type the BC — already handled safely by the
solver's `resolve_bc`).

## Method (per bullet)

1. Pull the manufacturer's own published BC + native model (G1/G7).
2. Independently pull JBM's library value for the **exact** same bullet.
3. Populate `component_data.json` only if they agree within 0.006 G7.
   Store the manufacturer value as the number, with a `bc_src`
   provenance string recording the source AND the JBM delta.
4. Disagreement, ambiguous bullet identity, or banded-only data →
   **leave blank** (never guess).

A build test (`test_no_bc_value_without_authoritative_provenance`)
now FAILS if any BC is ever present without a `bc_src` — a structural
no-fabrication guard. `bc_database_version` is 1 and must stay in lock-
step with "any curated value present."

## Why this is careful, not bulk-automated

A fuzzy auto-match of the 61 seed names to JBM's 3521-entry library
produced **many wrong-but-plausible matches** (Hornady 153 ELD-M → an
A-Tip; Berger 156 Hybrid Target → an Elite Hunter hunting bullet; Lapua
155 Naturalis → a Scenar; Sierra 150 TMK → a plain MatchKing; 5 with no
match). Auto-trusting those would have shipped wrong BCs into a paid
liability product. Each value is therefore pinned to the *exact* bullet
by hand-checked identity.

## Corroborated & populated this pass — Hornady (7)

| Bullet | G7 (Hornady) | JBM x-check | Δ |
|---|---|---|---|
| 6.5mm 147gr ELD-M | 0.351 | 0.351 | 0.000 |
| .308 168gr ELD-M | 0.263 | 0.263 | 0.000 |
| .308 178gr ELD-M | 0.275 | 0.275 | 0.000 |
| .30 225gr ELD-M | 0.391 | 0.391 | 0.000 |
| 6.5mm 143gr ELD-X | 0.314 | 0.315 | 0.001 |
| .308 178gr ELD-X | 0.278 | 0.278 | 0.000 |
| .30 212gr ELD-X | 0.334 | 0.336 | 0.002 |

Source of record: hornady.com/bc (Doppler-measured G7). All within
0.002 of JBM.

## Deliberately left BLANK (the cross-check working as designed)

- **Hornady 6.5mm 140gr ELD-M** — Hornady's site now publishes G7
  **0.326**; JBM has **0.305** (Hornady re-measured/revised this BC over
  the years). They disagree → blank until we pick the authoritative one
  with you. (Note: the gate-1 solver validation used 0.315 only as a
  *shared test input*, which is fine — that test compared solver-vs-
  solver, not the BC itself.)
- **Hornady A-Tip 135 / 153 / 230** — JBM A-Tip entries didn't return a
  clean matching G7; ambiguous → blank.

## Seed-data errors found (separate from BC; flag for later)

- **Hornady "6.5mm 153gr ELD-M" does not exist** — Hornady's 153gr is
  the *A-Tip*, not ELD-M. The seed list has a wrong entry.
- **Hornady "6mm 109gr ELD-M"** — the real product is **108gr**.

These are Smart-Setup seed list bugs (out of scope for BC; logged so
the bullet list itself gets corrected before beta).

## Remaining worklist (the other ~54 — methodical, in progress)

Per-maker, same method. Manufacturer source-of-record pages:
- **Berger** (12) — bergerbullets.com BC table (the static PDF path
  404'd; use their live BC page). Note seed name drift: "Hybrid Target"
  vs Berger's "Target Hybrid"; "Long Range HT 245" = EOL Elite Hunter.
- **Sierra** (9) — sierrabullets.com. Publishes **velocity-banded G1**
  for many SMK; the solver takes one BC, so use Sierra's single G7
  where published, else the high-velocity-band G1 flagged, cross-check
  vs JBM's Sierra/(Litz) entries.
- **Lapua** (7) — lapua.com per-bullet (G1+G7). Note Scenar vs
  Scenar-L are different bullets; the seed mixes them.
- **Nosler** (7) — nosler.com (RDF has G7; Custom Competition,
  Ballistic Tip, ABLR differ — verify identity, several are G1-only).
- **Barnes** (5) — barnesbullets.com (LRX/Match Burner G7; TTSX is a
  hunting bullet, G1).
- **Cutting Edge** (4), **Lehigh Defense** (2) — smaller; BCs on
  product pages; expect several blanks.

Everything not corroborated stays blank; the DB is independently
versioned and grows via data-only updates with no app rebuild — so
coverage can keep climbing toward the 500+ goal post-launch without
ever blocking a release.

*Updated 2026-05-16. Solver still NOT wired / NOT shipped (gates 3 & 4
drafts pending your review; wiring after).*
