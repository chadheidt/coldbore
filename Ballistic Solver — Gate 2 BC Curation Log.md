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


## POLICY UPDATE — 2026-05-16 (Chad decision: generalized cross-check)

The cross-check is no longer JBM-specific (JBM lacks Sierra single-G7,
Hammer entirely, etc.). New rule, same rigor:
- **Source of record** = the maker's own published BC, NATIVE model,
  never converted.
- **Cross-check** = ANY independent authoritative source: JBM, Applied
  Ballistics / Litz published measured data, or a second reputable
  independent publication of that maker's value.
- Populate ONLY when two independent authoritative sources agree
  (direct, or G1/G7 ratio-consistent as a sanity check WITHOUT storing
  a converted number). Blank when no independent corroboration exists.
- Chad also granted blanket "search/fetch any query/URL" authorization.
Same no-fabrication / no-single-source / no-conversion guarantees;
just not brittle to JBM's coverage gaps.

## Progress update — 2026-05-16 late

**Curated & shipped: 17 / 61** (all dual-corroborated, provenance
recorded; build guard `test_no_bc_value_without_authoritative_provenance`
enforces no value without a source).

- **Hornady — 12/15** populated (ELD-M/ELD-X 147/168/178/225/143/178/212
  + 140 ELD-M @0.326 your call + A-Tip 135/153/230 via Doppler-G7 with
  JBM-G1 ratio-1.98 cross-check + 6mm ELD-M 0.270). 3 blank: phantom
  6.5 153 ELD-M (seed bug), 2 legacy BTHP Match (no current maker
  source).
- **Berger — 5/12** populated (140 Hybrid Target 0.311, 144 LRHT 0.336,
  140 VLD Target 0.313, .308 175 VLD Target 0.255, .224 73 BT 0.176 —
  each corroborated by TWO authoritative sources: JBM Litz⇔catalog or
  JBM⇔bergerbullets.com). 7 blank: single-JBM-source only (156 EOL,
  .308 185/215 Target Hybrid, 6mm 105) or ambiguous seed identity
  (.308 168 "Elite Hunter" — not a Berger product; .30 245 "Long Range
  HT" — JBM only has EOL Elite Hunter; 156 "Hybrid Target" — seed dup
  of the EOL).

**Method note:** manufacturer sites/PDFs are NOT cleanly machine-
readable here (JS calculators, column-mangled PDFs). The reliable
rule-compliant path proved to be: JBM library exact-entry value (it
encodes manufacturer vs Litz provenance) **plus** a second independent
authoritative confirmation (JBM Litz⇔catalog pair, the G1/G7 ratio
sanity, or a clean manufacturer search snippet). **Single-source =
blank.** This keeps the "burned customer" risk at zero at the cost of
slower coverage — correct trade for a paid product.

**Remaining: 44 across Sierra/Lapua/Nosler/Barnes/Cutting Edge/Lehigh.**
Same method, same bar. This is genuine careful per-bullet work (each
maker ≈ a focused pass); coverage will keep climbing via data-only
`bc_database_version` bumps with no app rebuild, so it never blocks a
release. Sierra needs banded-G1 judgement; Lapua Scenar vs Scenar-L are
different bullets (seed mixes them); Nosler several are G1-only;
Barnes TTSX/LRX are hunting bullets (G1). Expect a meaningful number of
principled blanks — that is the rule working, not a gap to paper over.

## Sierra — 0/9 populated (principled blank under Policy 1)

Clean **Litz-measured G7** obtained from JBM for the match bullets
(6.5 142 SMK 0.301, .308 168 SMK 0.218, .308 175 SMK 0.243, .30 220
SMK 0.31, .308 175 TMK 0.267, .224 77 SMK 0.19, 6mm 107 SMK 0.26) —
but that is ONE authoritative source. Sierra's own data is
velocity-banded G1; their product pages are JS-rendered (no static
BC) and the official banded-BC PDF extracts column-scrambled (numbers
not reliably pairable to bullets — misparse risk). No *reliable*
independent second authoritative source obtainable here, so Policy 1 ⇒
**blank, not guess.** Sierra is the #1 future-fill candidate the
moment a clean second source is in hand (Sierra is the most popular
match brand) — DB is independently-versioned so this is a data-only
top-up later, never a release blocker. Litz G7 values are recorded
here so the fill is fast once corroborated. GameKing (hunting, banded
G1) and the ambiguous 6.5 150 / .224 77 "Tipped MatchKing" seed
identities: blank regardless.

**Realistic expectation going forward:** makers that publish only
banded-G1 or aren't in JBM (Sierra, likely Cutting Edge, Lehigh, and
the new Hammer add) will be largely principled-blank under Policy 1
until clean second sources are sourced. Makers with JBM Litz+catalog
pairs (Lapua, Nosler, Barnes — like Berger) should dual-source more
cleanly. Coverage climbs post-launch via data-only `bc_database_version`
bumps; it never blocks a ship.

## 61-SEED FIRST PASS COMPLETE — 24/61 dual-corroborated (2026-05-16)

| Maker | Curated | Notes |
|---|---|---|
| Hornady | 12/15 | ELD-M/ELD-X + A-Tip (Doppler G7, JBM-G1 ratio xchk). Blank: phantom 153 ELD-M, 2 legacy BTHP Match |
| Berger | 5/12 | Litz⇔catalog / bergerbullets.com. Blank: single-source or ambiguous seed identity |
| Lapua | 3/7 | Scenar-L G7/G1 + Scenar cat/Litz. Blank: Scenar≠Scenar-L, Naturalis, 167 Δ0.007 |
| Nosler | 3/7 | ABLR G7/G1 pair + RDF (Nosler guide=JBM). Blank: single-source RDF, identity |
| Barnes | 1/5 | .308 168 TTSX (Litz+catalog ratio). Blank: single-G1 LRX/MatchBurner, TSX≠TTSX |
| Sierra | 0/9 | Litz G7 known but no reliable independent 2nd source here (banded-G1). #1 fill target |
| Cutting Edge | 0/4 | single-G1 MTH / Lazer mismatch — no independent 2nd |
| Lehigh | 0/2 | not in JBM |
| **Total** | **24/61** | **37 principled blanks** |

**This is the no-fabrication policy working, not a failure.** Every
populated BC has two independent authoritative sources + provenance;
the solver safely prompts the user for any blank; the DB is
independently versioned so all 37 blanks are fillable post-launch via
data-only `bc_database_version` bumps with NO app rebuild and NO
release block. Highest-value future fills (clean sources known/likely):
Sierra match line (Litz G7 already recorded above), Berger single-
source Hybrids, Barnes LRX/Match Burner, Nosler RDF, Hornady A-Tip
re-confirm. Seed-list bugs (phantom 153 ELD-M, 6mm wt, Berger/Lapua/
Sierra/Nosler name drift, Scenar vs Scenar-L) to fix in the pre-beta
seed-list cleanup pass — along with ADDING Hammer Bullets (Chad
approved). 191 tests green; no-fabrication build guard enforced.

*Updated 2026-05-16. Solver still NOT wired / NOT shipped (gate 3 DONE;
gate 4 approved + queued incl. demo; wiring after).*
