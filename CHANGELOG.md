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

### Logger processor change

**Changed**
- Logger processor is now the **ESP32-DevKitC V4 (ESP32-WROOM-32D)**, replacing the Arduino UNO. (D-028)
- Logger gains a **RECORD input** (GPIO34, input-only, external pull-up) so the data file closes cleanly
  before the operator presses E-STOP. Previously the logger recorded whenever powered. (D-032)
- Pin map avoids GPIO6–11 (SPI flash) and all strapping pins (0, 2, 5, 12, 15). (D-031)

**Added**
- **Wi-Fi and Bluetooth stopped as the first action at boot**, with a fifth logger constraint in
  `docs/SAFETY.md` explaining that this is an EMI concern, not a command-injection one. (D-029)
- Bring-up checks for radio silence, logger noise contribution, and clean file close across an E-STOP.
- Voltage-domain section in `hardware/README.md`: the AD620 gain must keep its output inside the
  ADS1115 input range at a 3.3 V supply.

**Kept deliberately**
- **ADS1115 retained; the ESP32 internal SAR ADC is not used.** It is nonlinear and noisy, and the
  load-cell chain is already noise-limited (manual p. 28). (D-030)

### Authorship

- Author: Sofia Pacheco Leon. Co-author: Claude (Anthropic).
- Credits restructured to the IGNIS-v5 README style, with team leader, division leader and faculty
  advisor rows pending names.

### Outstanding before Gate 2

- Review owner must be named.
- Logger power domain must be decided.
- E-match no-fire current and load cell datasheet required.
