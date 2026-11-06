# Fabrication

**Empty, and must stay empty until Gate 6 is approved.**

> Gates 0–5 must be complete, ERC and DRC must be clean with every remaining item justified, and the
> named review owner must have approved export. **Nothing is ordered or uploaded** without a separate,
> explicit instruction.

---

## What goes here, when the time comes

| Artefact | Notes |
|---|---|
| Gerbers | One set per board, per revision |
| Drill files | Plated and non-plated separated |
| BOM | Must match the placed parts exactly — checked at Gate 5 |
| Centroid / pick-and-place | Must match the placed parts exactly — checked at Gate 5 |
| Fab drawing | Stackup, finish, tolerances, board thickness |
| Assembly drawing | Only if the house is assembling |
| README per revision | Which commit, which fab house, which options |

---

## Rules

1. **Export only from a tagged commit.** A fabrication package that cannot be traced to an exact commit
   is not reviewable. Tag as `bench-revA`, `station-revA`.
2. **One folder per revision.** Never overwrite a previous package. Name folders `bench-revA/`,
   `bench-revB/`.
3. **Generated files are gitignored.** Attach the package to a GitHub Release rather than committing
   binaries, so the repository stays diffable.
4. **BOM and centroid are verified against the board, not against intent.** Gate 5 checks that every
   placed part appears in both, and that neither contains a part that is not placed.

---

## Fabrication parameters

All **TBD** — open item 8 in [../docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md).

| Parameter | Value |
|---|---|
| Fab house | TBD |
| Layer count | TBD (2 assumed) |
| Board size target | TBD (100 × 80 mm and 80 × 60 mm are placeholders) |
| Assembly | TBD |
| Copper weight | TBD — the firing trace width depends on this |
| Surface finish | ENIG assumed in the stackup |

> Copper weight matters more than usual here. The `PYRO` net class assumes a 2.00 mm track, which is
> sized for the firing current on the assumption of 1 oz copper. Confirm the weight before trusting
> that width.
