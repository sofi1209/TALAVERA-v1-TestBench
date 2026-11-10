# Changelog

## [Unreleased] — Revision A.1 — corrective, 9 November 2026

Two independent audits of commit `43e9803` found that **the bench could not fire**: `PYRO_MATCH_N`
reached only K3's NC contact and the opto LED, both of which led back to `PYRO_MATCH_P`, so no current
could flow in any state. Both also confirmed the reversed `D_RP`, which left nothing downstream of F1
powered. Reconciled in `docs/AUDIT-RECONCILIATION-2026-11-09.md`; changes recorded in
`docs/REV-A1-CHANGES-2026-11-09.md`. **No circuit is approved.**

### Fixed — blockers
- **Firing loop has a return.** K3 now carries the shunt and the low-side return on one Form C pole,
  using its previously unused NO contact. Provisional: decision **D-A**, and it assumes the Songle
  changeover is break-before-make (O-3). (D-065)
- **`D_RP` un-reversed** — anode on `+12V_FUSED`, cathode on `+12V_PROT`. (D-064)
- **`PYRO_RTN` is a separate net** with a single star bond at `R_STAR`, so the fire current does not
  return through the load-cell excitation return and the ADS1220 AVSS during the burn. (D-066)
- **Station supply drawn honestly and fused** at `F_STN`; the umbilical carries no supply conductor.
  (D-067)

### Fixed — mechanical
- `PWR_FLAG` on `+12V_LOGGER`, clearing the one real ERC error.
- FIRING lamp moved to `FIRE_LINE`, removing a sneak path that read "good" with no match fitted. (D-068)
- `R_ADCCS` pull-up on `ADC_CS`; `R_DE` pull-**down** on the bench `RS485_DE`.
- Station rail decoupling added — `C_STN1`–`C_STN3`, `C_485` at the SP3485 VCC pin, `C_ISO1`/`C_ISO2` at
  each 6N137 pins 8–5 as its datasheet requires. 22 µF values **assumed**, O-20.
- Shield bonds at the bench end only. (D-070)
- Path 2 deferred: umbilical pins 8/9 reserved, `J_DAQ` not fitted. (D-069)
- SD-detect sheet note corrected; the wiring was already right.
- `S_CONT` removed from the parts list — the button was deleted by H-2 on 6 November.
- Generator and parts-list paths are relative, so regeneration is no longer tied to one machine.

### Fixed — tooling, so a clean result means something
- `validate_sch.py` returned a **byte-identical "0 errors"** when `SYMDIR` was wrong, because symbol
  resolution sat in `except Exception: continue`. `SYMDIR` now resolves from the environment or by
  globbing, a set-but-wrong override is fatal, unresolved symbols are a hard error, the run prints
  `symdir` and `structural_checks`, and it exits non-zero. (D-071)
- **Automatic diode polarity checking**, which the handoff recorded as the one class with no guard.
  Three rules, each self-tested against a deliberately broken board. (D-072)
- **`hardware/tools/trace_fire_loop.py`** — asks whether current can complete a circuit from the
  battery through the initiator and back, per relay state. Self-tested against the original netlist,
  where it correctly reports that the board cannot fire.

### Fixed — housekeeping, 10 November 2026
- **ERC is clean on KiCad 10.0.8, not only 10.0.5.** The embedded `Relay_SPDT` copies had drifted from
  the installed library (pin numbers and geometry were identical; regenerating re-embeds the current
  symbol), and ground stubs and `PWR_FLAG`s used a local `GND`/`GNDREF` label next to a power symbol,
  which newer KiCad flags as `same_local_global_label`. `ksch.stub()` and `pwr_flag()` now draw ground as
  a power symbol. Connectivity is unchanged: every net of both boards compares identical to the previous
  netlist.
- Title block reads **Rev A.1, 2026-11-10** (`Sch(rev=, date=)`), and `generator_version` is `9.0`,
  matching the file format, instead of the non-existent `9.99`.
- `README.md` status banner and `docs/HANDOFF.md` carry the Rev A.1 state instead of the 6 Nov audit.
- Exports for this revision are in `exports/2026-11-10-revA1/`.

### Verification
`validate_sch.py` 0 errors / 0 warnings on both boards · `kicad-cli sch erc` **0 violations on both**,
the first time the bench board has been ERC-clean under the native tool · `trace_fire_loop.py` all five
states as expected, with no fire current in SAFE, ARMED, E-STOP or FIRE-without-ARM.

### Still open — decisions for the review owner
**D-A** K3 one relay or two · **D-B** pre-arm continuity TEST · **D1** station power · E-STOP second
channel and latched ARM permit · umbilical ARM/FIRE separation · **M-1** bench thermal · **M-2** DevKitC
representation · 6N137 RX inversion (O-21) · buzzer part · path B survival.
Blocked on data: **O-1** e-match, **O-2** load cell, **O-20** AMS1117 capacitors.

**Gate 6 and bring-up Stage 5 keep mandatory written sign-off from Emilio Guadarrama.**

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

- ~~Review owner must be named.~~ Resolved: **Emilio Guadarrama** (D-050).
- Logger power domain must be decided.
- E-match no-fire current and load cell datasheet required.
