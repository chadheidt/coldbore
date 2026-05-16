# Ballistic Solver — Gates 3 & 4 Review Draft (NOT shipped)

These are **drafts staged for your review**, not changes that have been
applied. Nothing here is wired or shipped. Gate 1 (live pro-solver
validation) and gate 2 (authoritative BC values) come first; gates 3 & 4
land with the solver wiring. I'm putting both in one doc so you review
the solver's user-facing pieces **once, together**, not piecemeal.

---

## Gate 3 — Disclaimer update (draft)

The signed disclaimer must add predicted-DOPE liability language, and
because it's a substantive change `DISCLAIMER_VERSION` bumps `1 -> 2`
so **every existing user is re-prompted to accept on next launch**.
That re-prompt is why this is a hold-gate decision, not an autonomous
edit.

**Proposed change to `app/version.py` (exact, ASCII-only, ready to apply
verbatim on your OK):**

- `DISCLAIMER_VERSION = 1`  ->  `DISCLAIMER_VERSION = 2`
- Insert a new numbered clause as **#4** (renumbering the current
  liability/risk clauses to #5, #6, #7):

> 4. Predicted ballistic data is an ESTIMATE. When Loadscope shows a
> predicted DOPE / come-up / wind table, those numbers are computed from
> a G7 ballistic-coefficient point-mass model using the bullet, muzzle
> velocity, and atmospheric values you supply. They are a starting
> point ONLY. Their accuracy depends entirely on the accuracy of those
> inputs (an estimated or wrong ballistic coefficient, muzzle velocity,
> or atmosphere produces a wrong prediction). Predicted values MUST be
> confirmed by live fire at known distances before you rely on them.
> Do not use predicted values for a shot that matters until you have
> verified them at the range.

- Add to the existing "not liable" clause (now #6) a trailing sentence:

> This expressly includes any damage, injury, or loss resulting from
> reliance on predicted ballistic values that were not verified at the
> range.

**Why this wording:** plain-language, mirrors the existing clause voice,
no curly quotes / em-dashes (Python 3.9 ASCII-write safety per the build
rules), and it ties to the on-screen "verify at the range" treatment in
gate 4 so the legal text and the UX say the same thing.

---

## Gate 4 — Predicted-vs-confirmed DOPE UX (design for review)

Goal: the shooter always knows, at a glance, which numbers Loadscope
predicted vs. which they confirmed at the range, and the printed card
warns when it still contains predictions. This lives in the Range&DOPE
panel of the unified shell (v0.14.9).

### Visual model

- **Predicted cells:** gray + italic. Shown the moment a load has
  enough inputs to solve (bullet w/ BC, muzzle velocity; atmosphere
  defaults to ICAO standard so a prediction appears with zero extra
  input).
- **Confirmed cells:** the shooter types their actual dialed value over
  the prediction; the cell turns solid black + upright. Predicted ->
  confirmed is per-cell (you can confirm 500 and 800 and leave the rest
  predicted).
- **A small per-row marker** (e.g. a faint "pred" tag) on any row still
  using a prediction, so a half-confirmed card is unambiguous.

### Inputs added to the panel

1. **G7 BC field** next to the bullet — auto-fills from the BC database
   when the bullet is known (gate 2), always hand-editable for
   exotic/measured bullets. Empty + no DB hit => the panel asks for a
   BC before it predicts (it never guesses; see the resolver's
   `BcUnavailable` / `BcModelUnsupported` behavior already built).
2. **Atmosphere (optional):** temp + pressure-or-altitude + humidity.
   Defaults to ICAO standard so the no-input case still works; a one-
   line "Standard atmosphere assumed — set today's conditions for long
   range" nudge.
3. **Wind:** speed + clock direction, default 10 mph / 3 o'clock
   (matches the validation packet conventions).

### "How Loadscope predicts" transparency note

A short, confidence-building (not disclaimer-dump) note near the BC
field, e.g.:

> Loadscope predicts your DOPE with a G7 ballistic-coefficient solver -
> the same model class as Strelok, GeoBallistics, and the free Hornady
> and Berger web calculators. With good inputs it's accurate to about
> 1000 yards; measured-drag solvers (Applied Ballistics, Hornady 4DOF)
> pull ahead deep in the transonic range. Always confirm at the range.

(Same idea, shorter, also goes on the marketing site per the solver
memory.)

### Pocket / Range Card watermark

If **any** printed DOPE row is still predicted (not confirmed), the
card prints a footer/watermark:

> PREDICTED DOPE - verify at the range before relying on these values.

Once every row on the card is confirmed, the watermark disappears
automatically. (Reuses the existing unit-aware Pocket Card path.)

### Demo-tour narration rewrite

The solver memory flags `TOUR_STOPS[3]` in `app/demo_tour.py` with a
`PLACEHOLDER` comment — it currently assumes manual DOPE entry. Draft
replacement, same plain voice as the rest of the tour:

> "Loadscope already filled in a predicted DOPE table from your bullet,
> velocity, and atmosphere. The grey values are predictions; confirm
> them at the range and they turn black. Your printable card warns you
> any time it still has predictions on it. Click Next to see the card."

(Only relevant for the website slideshow / demo refresh, which is the
post-solver website pass — not now.)

---

## What I need from you (not now — when the solver moves forward)

> ⚠️ **YOUR TO-DO — at the gates 3 & 4 review (AFTER gate 1 passes):**
> **1. Read the Gate 3 disclaimer wording above — approve it as written, or tell me what to change. On your OK I apply it verbatim and bump DISCLAIMER_VERSION 1 -> 2.**
> **2. Read the Gate 4 UX design — approve the gray-predicted / black-confirmed model + the BC/atmosphere fields + the card watermark, or redirect. I'll build it into the Range&DOPE panel and show you a rendered preview before anything ships.**
> **Neither is urgent — gate 1 (the validation packet) and gate 2 (authoritative BC values) come first.**

*Drafted 2026-05-16. Staged for review only — disclaimer not edited,
DISCLAIMER_VERSION still 1, no UX code written, solver still unwired.*
