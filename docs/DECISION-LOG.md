# TALAVERA v1 — Decision Log

Project: replacement electronics for the Wirikuta 1.1 solid-motor static test bench
Organisation: Ignitia Rocket Lab — Tecnológico de Monterrey, Campus Guadalajara
Reference: *Manual de operaciones: WIRIKUTA 1.1 Banco de Pruebas*, August 2025

**Author:** Sofia Pacheco Leon · **Co-author:** Claude (Anthropic)
**Review owner: TBD — must be named before Gate 2.**

> No circuit in this project is approved. No output has been energized.
> Pyrotechnic, actuator, motor, high-current, battery and mains circuits require written
> sign-off from the named review owner.

---

## Decisions

| ID | Decision | Reason | Date | Approved by |
|----|----------|--------|------|-------------|
| D-001 | Source of truth is the Wirikuta operations manual, Aug 2025, extracted text layer | Only machine-readable record available | 2026-11-06 | pending |
| D-002 | Annex A and B treated as unavailable; KiCad sources requested | Raster images, no text layer | 2026-11-06 | pending |
| D-003 | Nothing energized; no circuit approved at any gate by the design assistant | Project safety rule | 2026-11-06 | standing |
| D-004 | Two Annex C firmware defects logged as rationale for hardware-defined logic | Verified in the source listings | 2026-11-06 | pending |
| D-005 | Environment figures recorded as **assumed** pending confirmation | No environmental spec in the manual | 2026-11-06 | pending |
| D-006 | Arm/fire path is a **wired umbilical**. No MCU on the safety path. | User decision at Gate 0 | 2026-11-06 | Sofia Pacheco Leon |
| D-007 | 20 m standoff is **below** the NAR/TRA reduced minimum of 22.5 m for H class | Manual pp. 7–8 | 2026-11-06 | noted deviation |
| D-008 | Igniter safe state is **SHORTED**, via a normally-closed contact | 20 m pickup loop; falls safe on power loss | 2026-11-06 | pending |
| D-009 | Firing pair is 16 AWG. Cable R and C confirmed non-binding at 20 m and 40 m. | Computed from standard AWG table | 2026-11-06 | pending |
| D-010 | Thrust signal leaves the bench **differential**, not single-ended | Long run beside a firing line; addresses p. 28 noise floor | 2026-11-06 | pending |
| D-011 | Design for a **20 m** umbilical, extensible to 40 m+ | User decision; deviation D-007 accepted | 2026-11-06 | Sofia Pacheco Leon |
| D-012 | Data logging stays on the **bench board**, as an isolated no-authority passenger | User decision | 2026-11-06 | Sofia Pacheco Leon |
| D-013 | Arming is a **bench arming plug** plus a **station key switch** — three series elements | User decision | 2026-11-06 | Sofia Pacheco Leon |
| D-014 | **Two boards**: one bench, one station. Drops the bench-to-bench JST-XH interconnect. | User decision | 2026-11-06 | Sofia Pacheco Leon |
| D-015 | **One** igniter channel | User decision | 2026-11-06 | Sofia Pacheco Leon |
| D-016 | **Two** umbilical cables: pyro pair isolated from the control/analog multicore | A firing transient at *t=0* beside a strain gauge corrupts the data | 2026-11-06 | pending |
| D-017 | LED beacon driven from the **real** ARM/FIRE signals, never a software report | The beacon must not be able to misreport state | 2026-11-06 | pending |
| D-018 | Logger has **no state machine and no command set**; it records whenever powered | Removes all firmware complexity; also yields a clean CSV with nothing to hand-strip (p. 27) | 2026-11-06 | pending |
| D-019 | Retain a differential thrust pair to the station for live readout and redundancy | A static fire is non-repeatable; a single SD write is a single point of failure | 2026-11-06 | pending |
| D-020 | Project preliminary name: **TALAVERA** | User decision | 2026-11-06 | Sofia Pacheco Leon |
| D-021 | Repository layout uses `docs/ hardware/ firmware/ fabrication/ analysis/ test/` | Follows the IGNIS-v5 README *style* but with a deeper folder tree, since this project has two boards plus manual, safety and bring-up documents | 2026-11-06 | pending |
| D-022 | Target **KiCad 10.0**. Format versions read from the installed demo projects rather than assumed. | KiCad 10.0 found at `C:\Program Files\KiCad\10.0` | 2026-11-06 | — |
| D-023 | Board outlines are **placeholders**: 100 × 80 mm bench, 80 × 60 mm station | Size target is an open item; noted in each PCB title block | 2026-11-06 | pending |
| D-024 | Net classes `PYRO`, `SAFETY`, `POWER`, `ANALOG` pre-defined with pattern assignment | Makes DRC itself enforce pyro clearance and trace width, instead of relying on reviewer attention | 2026-11-06 | pending |
| D-025 | Schematics committed **intentionally empty**, carrying only the safety ground rules as a text block | Gate 2 is not approved; the project skeleton must not imply a design exists | 2026-11-06 | — |
| D-026 | MIT licence plus an explicit safety notice disclaiming fitness | Hardware that fires pyrotechnics should not ship an unqualified permission grant | 2026-11-06 | pending |
| D-027 | **No GitHub remote created and nothing pushed.** Local repository only. | Publishing is the user's call, not the assistant's | 2026-11-06 | superseded by D-033 |
| D-028 | Logger processor is the **ESP32-DevKitC V4 (ESP32-WROOM-32D)**, replacing the Arduino UNO | User decision. 3.3 V is native for SD and I²C, so level shifting disappears. Logger remains a zero-authority passenger. | 2026-11-06 | Sofia Pacheco Leon |
| D-029 | **Wi-Fi and Bluetooth stopped as the first action at boot, never enabled** | A +20 dBm 2.4 GHz transmitter centimetres from the AD620 front end and a 20 m pyro cable is an EMI source next to the two most sensitive things on the bench. Measurement integrity and pickup, not command injection. | 2026-11-06 | pending |
| D-030 | ~~ADS1115 retained.~~ **ESP32 internal SAR ADC not used** — this half stands. | The internal ADC is nonlinear and noisy. The load-cell chain is already noise-limited to the point a 1-grain motor is uncharacterisable (manual p. 28); using a worse converter moves the design backwards on its core measurement. **ADS1115 retention reopened by D-036.** | 2026-11-06 | partly superseded |
| D-031 | Logger pin map avoids GPIO6–11 (SPI flash) and all strapping pins (0, 2, 5, 12, 15). RECORD on GPIO34. | GPIO34–39 are input-only, so RECORD is physically incapable of becoming an output through a coding mistake. A cable left connected cannot block boot. | 2026-11-06 | pending |
| D-032 | Logger gains a **RECORD input** (active low, external pull-up) rather than being started and stopped by cutting its power | Opening RECORD closes the data file cleanly before the operator presses E-STOP, which is the post-test sequence. Avoids corrupting a non-repeatable test record. | 2026-11-06 | pending |
| D-033 | GitHub repository **created and pushed** at the user's explicit instruction | User instruction, 2026-11-06. Supersedes D-027. | 2026-11-06 | Sofia Pacheco Leon |
| D-034 | Repository made **public** | User instruction. Created private first because public cannot be un-published; changed on explicit request. | 2026-11-06 | Sofia Pacheco Leon |
| D-035 | Credits: Author Sofia Pacheco Leon; Co-author Claude; Team Leader Maximiliano Funoy; Division Leader & VP Emilio Guadarrama; Faculty Advisor Dr. José Luis Henríquez Mercado | User instruction, formatted as in IGNIS-v5 | 2026-11-06 | Sofia Pacheco Leon |
| D-036 | **D-030 reopened.** ADS1115 is a candidate for replacement; selection deferred to Gate 3. Primary criterion is **moving off I²C**. | Reported field problems, corroborated by IGNIS-v5's own `DataLogger.h` comment on "documented I²C solder-joint issues" and its deliberate choice to keep the data path on SPI. A second board in the same lab reached the same conclusion. See [ADC-TRADE-STUDY.md](ADC-TRADE-STUDY.md). | 2026-11-06 | pending |
| D-037 | **Embedded microSD card slot on the bench board**, porting the IGNIS-v5 `Storage.SchDoc` topology, replacing a breakout module | Parts and a known-good reference design are already in the lab. Removes a module and its headers, which is one fewer thing to vibrate loose. Confirmed from the IGNIS-v5 schematic: microSD socket, 10 k pull-ups, 100 nF and 22 µF decoupling, plus an `SD_DETECT` card-present line worth carrying over. | 2026-11-06 | pending |
| D-038 | **Direct USB down the umbilical rejected.** Secondary telemetry path to be isolated RS-485 over cable B, with the USB-C connector on the **station** board. | USB 2.0 is specified to 5 m; the umbilical is 20 m. Active repeaters would add four powered devices and four connectors to the data path. RS-485 is rated to ~1200 m, is differential, and extends to 40 m at no cost. Isolation is required because a laptop would otherwise be tied to bench ground during a firing. See [UMBILICAL-AND-TELEMETRY.md](UMBILICAL-AND-TELEMETRY.md). | 2026-11-06 | pending |
| D-039 | Reuse IGNIS-v5 parts already stocked: `TYPE-C-31-M-12` USB-C, `ESD9B5.0ST5G`, `TLP521`/`PC817` optoisolator, `AMS1117-3.3`/`-5.0`, `SS24`, `NCE6005AR` | Known parts, known footprints, already on the shelf; shortens Gate 3 sourcing | 2026-11-06 | pending |
| D-040 | Preliminary parts list created in the IGNIS v5 / MAGNIS v1 format: `fabrication/PARTS-LIST.md` plus two CSVs. **35 lines confirmed in lab stock, 24 still TBD or pending.** Explicitly labelled *not a BOM* — no netlist exists to reconcile against. | Lets lab stock be checked before Gate 2 without implying a design exists | 2026-11-06 | pending |
| D-041 | **microSD socket resolved: `THD2528-11SD-GF` (LCSC C283232).** Closes open item 14. | Found in both the IGNIS v5 and MAGNIS v1 lists. IGNIS v5 note: pin 9 CD → SD_DETECT with a 10 k pull-up, shell pads MP1–4 to GND. MAGNIS v1 note: locating pegs drilled 1.3 mm. | 2026-11-06 | Sofia Pacheco Leon |
| D-042 | Logger mounting: **socketed DevKitC V4 on `PPTC191LFBN-RC` 1×19 sockets, plus a mechanical hold-down** | MAGNIS v1 already does exactly this, so the footprint and sockets are proven in-house. Keeps the logger field-replaceable, which matters for the part most likely to need reflashing. The hold-down is added because MAGNIS is a ground station while this board rides the test stand. | 2026-11-06 | pending |
| D-043 | **`WS2812B-B/T` excluded from the safety beacon.** Beacon must be plain LEDs wired to the real ARM/FIRE lines. | Addressable LEDs require an MCU data stream, so a WS2812B beacon can always misreport state — precisely what D-017 forbids. Retained for logger-local status only. | 2026-11-06 | pending |
| D-044 | **`SKRPABE010` excluded from the FIRE control.** FIRE requires a substantial panel-mount momentary button, ideally guarded. | A 4.6 × 3.2 mm SMD tactile can be actuated by a dropped tool, a closing lid or a slipped thumb. Retained for the continuity check. | 2026-11-06 | pending |
| D-045 | Adopt the IGNIS v4 / 2v2 **continuity-sense topology** (optocoupler across the e-match returning `PYRO_CHx_CONT`). **Do not adopt the gate-drive half.** | The sense circuit is proven in-house and is the basis for the station continuity check. The gate drive puts the MCU in the firing path, which is the arrangement TALAVERA exists to remove (D-013). Porting `Pyros.SchDoc` wholesale would silently undo the redesign. | 2026-11-06 | pending |

| D-046 | **ADC: `ADS1220IPWR`** (24-bit, SPI, 2 kSPS, integrated PGA ×1–128, TSSOP-16). Populated, with its internal PGA as the primary front end. **The AD620 footprint is laid out with 0 Ω bypass links** for optional hand population. Supersedes the ADS1115 half of D-030. | Sofia chose the minimum-change logic but required availability at UNIT **or** LCSC, preferably both. ADS1220 is stocked at **both** (UNIT ADS1220IPWR; LCSC C48263, ~15.9 k, ~$1.71 @100) and is TI's own bridge-sensor part. Decisive factor: the **SOIC AD620ARZ is on pre-order at LCSC**, so JLCPCB almost certainly cannot place it — keeping the AD620 populated would have been a schedule risk under D-049. Laying it out bypassable keeps the proven topology available and lets both front ends be A/B tested on one board, which matters because the noise floor is the known unsolved problem (manual p. 28). | 2026-11-06 | Sofia Pacheco Leon |
| D-047 | **Logger power sits UPSTREAM of the master kill relay**, with its own fuse and its own switch | User decision. E-STOP kills pyro and beacon while the logger keeps running until stopped deliberately via RECORD, so the data file always closes cleanly. The E-STOP's job is to make the bench safe, and a logger is not a hazard. One battery to manage in the field. Closes the Gate 0 question. | 2026-11-06 | Sofia Pacheco Leon |
| D-048 | **RS-485 / USB secondary telemetry path built into revision A**, not left as footprints | User decision. Live numeric data from the first test, and the IGNIS-v5 ground-station app likely covers most of the software. Isolation remains mandatory. | 2026-11-06 | Sofia Pacheco Leon |
| D-049 | **Fabrication: JLCPCB, 2 layers, JLCPCB assembly** | User decision, matching the IGNIS v5 route (its BOM notes "JLCPCB places it" and "JLCPCB supplies from LCSC"). Two layers suffice: this is relays, switches and one analog chain, not a dense digital design. **Consequence: every populated part must be LCSC-stocked, which is what ruled out the AD620ARZ in D-046.** | 2026-11-06 | Sofia Pacheco Leon |

---

## Pending decisions

| Question | Options | Blocks |
|---|---|---|
| ~~Logger power domain~~ | **Resolved: upstream of the master relay** (D-047) | closed |
| ~~ADC selection~~ | **Resolved: ADS1220IPWR** (D-046) | closed |
| ~~Secondary telemetry in rev A~~ | **Resolved: build it** (D-048) | closed |
| ~~Fabrication~~ | **Resolved: JLCPCB, 2-layer, assembled** (D-049) | closed |
| Logger mounting | Socketed DevKitC V4 (field-replaceable, header vibration risk) / soldered WROOM-32D module (robust, adds USB-UART and regulator to our board) | Gate 2 and Gate 4 |
| **ADC selection** | AD7190 (recommended, replaces AD620 too) / ADS1256 (second source) / MCP3561 behind the existing AD620 (minimum change) | Gate 2 analog chain, Gate 3 sourcing |
| **What actually failed on the ADS1115** | Bus lockup / noise / drift / clipping / too slow — see [ADC-TRADE-STUDY.md](ADC-TRADE-STUDY.md) §5 | Confirms or redirects the ADC choice |
| Secondary telemetry in rev A | Build RS-485 + USB now / leave depopulated footprints | Gate 2 scope |
| microSD socket part number | Needed from IGNIS-v5 `Storage.SchDoc` — not recoverable from the Altium binary | Gate 2 schematic |
| Review owner | — | Gate 2 |
| Largest motor class | — | Standoff and connector sizing |
| Fabrication house, layers, size | — | Gates 4 and 6 |

---

## Revision history

| Rev | Date | Change |
|---|---|---|
| A | 2026-11-06 | Gate 0 complete. Repository and KiCad project skeletons created. |
