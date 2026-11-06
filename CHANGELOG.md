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

### Storage, telemetry, and ADC review

**Added**
- `docs/ADC-TRADE-STUDY.md` — seven candidates assessed against the ADS1115. Recommendation: **AD7190**
  (SPI, integrated bridge PGA, replaces the AD620 as well), with **ADS1256** as second source. Every
  figure is flagged unverified pending datasheet confirmation.
- `docs/UMBILICAL-AND-TELEMETRY.md` — the three data paths, and why a direct USB umbilical fails.

**Changed**
- **D-030 reopened as D-036.** The ADS1115 is no longer assumed. Primary criterion is moving off I²C,
  corroborated by IGNIS-v5's own `DataLogger.h` comment on "documented I²C solder-joint issues" and its
  deliberate choice to keep its data path on SPI. The exclusion of the ESP32 internal SAR ADC stands.
- **Storage is now an on-board microSD socket** with an `SD_DETECT` card-present line, porting the
  IGNIS-v5 `Storage.SchDoc` topology instead of using a breakout module. (D-037)
- Repository made **public**. (D-034)
- Credits completed: Team Leader Maximiliano Funoy, Division Leader & VP
  [Emilio Guadarrama](https://github.com/Emilio-Guadarrama), Faculty Advisor Dr. José Luis Henríquez
  Mercado. (D-035)

**Rejected**
- **Direct USB down the umbilical.** USB 2.0 is specified to 5 m; the run is 20 m. Active repeaters
  would add four powered devices and four connectors to the data path. Replaced by isolated **RS-485**
  over cable B with the **USB-C connector on the station board**, which is rated far beyond 20 m and
  extends to 40 m at no cost. Isolation is mandatory so a laptop is never tied to bench ground during a
  firing. (D-038)

**Noted**
- Parts already stocked from the IGNIS-v5 BOM are reusable: `TYPE-C-31-M-12` USB-C,
  `ESD9B5.0ST5G` ESD diode, `TLP521`/`PC817` optoisolator, `AMS1117-3.3`/`-5.0`, `SS24`, `NCE6005AR`.
  (D-039)
- The IGNIS-v5 Python ground-station app may cover most of the live-readout work for the secondary path.

### Parts list, and four decisions closed

**Added**
- `fabrication/PARTS-LIST.md` plus two CSVs, in the IGNIS v5 / MAGNIS v1 column format.
  **35 lines confirmed against existing lab stock, 18 still open.** Explicitly not a BOM — no netlist
  exists to reconcile designators against.
- `fabrication/generate_parts_list.py` — regenerates all three files from one source.

**Decided**
- **ADC: `ADS1220IPWR`** (D-046). 24-bit, SPI, 2 kSPS, integrated PGA ×1–128, stocked at **both** UNIT
  and LCSC (C48263). The AD620 footprint is laid out with 0 Ω bypass links and hand-populated, because
  the SOIC `AD620ARZ` is on pre-order at LCSC and JLCPCB very likely cannot place it. Both front ends
  can now be A/B tested on one board.
- **Logger power sits upstream of the master kill relay** (D-047), own fuse and switch, so an E-STOP
  cannot corrupt a data file. Closes the Gate 0 question.
- **RS-485 / USB secondary path built into rev A** (D-048).
- **Fabrication: JLCPCB, 2-layer, assembled** (D-049). Consequence: every populated part must be
  LCSC-stocked.

**Resolved from the supplied BOMs**
- microSD socket is `THD2528-11SD-GF` (C283232) — open item 14 closed (D-041).
- Logger mounting is a socketed DevKitC on `PPTC191LFBN-RC`, per MAGNIS v1 — open item 10 closed (D-042).

**Changed**
- `WS2812B` excluded from the safety beacon; plain LEDs wired to the real ARM/FIRE lines (D-043).
- `SKRPABE010` excluded from the FIRE control; a guarded panel button is required (D-044).
- IGNIS v4/2v2 continuity-sense topology adopted, **gate-drive half explicitly rejected** (D-045).

### Outstanding before Gate 2

- Review owner must be named.
- Logger power domain must be decided.
- E-match no-fire current and load cell datasheet required.
