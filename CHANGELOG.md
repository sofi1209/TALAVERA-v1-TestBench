# Changelog

## [Unreleased] — Revision A

### Gate 0 — Requirements and reference (complete)

**Added**
- Repository structure, README, MIT licence with safety notice, KiCad-aware `.gitignore` and
  `.gitattributes`, PR template carrying the safety checklist.
- `docs/REQUIREMENTS.md` — function list with justification, settled parameters, open items.
- `docs/SAFETY.md` — named safe states, firing chain, hazard table, standoff analysis, sign-off sheet.
- `docs/DECISION-LOG.md` — decisions D-001 to D-027.
- `docs/OPERATIONS-MANUAL.md` — preliminary field manual, revision A.
- `test/BRINGUP-PLAN.md` — staged power-up, Stages 0 to 5.
- `hardware/talavera-bench/` and `hardware/talavera-station/` — KiCad 10 project skeletons.
  Schematics intentionally empty; PCBs carry outline, stackup and net classes only.
- `firmware/logger/` — thrust logger skeleton. No state machine, no outputs, no safety authority.
- `analysis/kalman/README.md` — post-test processing notes and log format.

**Decided**
- Wired umbilical, 20 m, extensible. No microcontroller on the safety path. (D-006, D-011)
- Igniter safe state is **shorted** via a normally-closed contact. (D-008)
- Arming is a bench arming plug plus a station key switch — three series elements. (D-013)
- Two boards, one igniter channel, logging on the bench board as an isolated passenger.
  (D-014, D-015, D-012)
- Two separate umbilical cables: pyro isolated from control and analog. (D-016)
- LED beacon driven from the real ARM/FIRE signals, never a software report. (D-017)
- Logger has no state machine; it records whenever powered. (D-018)

**Noted**
- A 20 m umbilical yields 15–17 m of real standoff, which clears no NAR/TRA motor class.
  Accepted deviation, recorded as D-007. Extending to 40 m requires no board change.

**Not done**
- No GitHub remote created. Nothing pushed or published. (D-027)
- No circuit designed. Gate 2 not started.
- No board fabricated. Nothing energized. Nothing approved.

### Outstanding before Gate 2

- Review owner must be named.
- Logger power domain must be decided.
- E-match no-fire current and load cell datasheet required.
