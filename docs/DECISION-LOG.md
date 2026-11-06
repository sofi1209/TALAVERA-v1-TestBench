# TALAVERA v1 — Decision Log

Project: replacement electronics for the Wirikuta 1.1 solid-motor static test bench
Organisation: Ignitia Rocket Lab — Tecnológico de Monterrey, Campus Guadalajara
Reference: *Manual de operaciones: WIRIKUTA 1.1 Banco de Pruebas*, August 2025

**Author:** Sofia Pacheco Leon · **Co-author:** Claude (Anthropic)
**Review owner: Emilio Guadarrama** — Division Leader & Vice President, Ignitia Rocket Lab.
Signs off pyrotechnic, actuator, motor, high-current, battery and mains circuits.

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
| D-050 | **Review owner: Emilio Guadarrama** — Division Leader & Vice President. Signs off pyrotechnic, actuator, motor, high-current, battery and mains circuits, and the separate Stage 5 authorisation. | User decision. Well placed for it: he co-drew `Pyros.SchDoc` in IGNIS v4/2v2, so he is the right person to review the pyro section — including whether declining its MCU gate-drive half (D-045) is correct. Closes open item 1. | 2026-11-06 | Sofia Pacheco Leon |
| D-051 | **D-049 revised: rev A is a bare PCB, hand-assembled.** JLCPCB (or any house) fabricates the board only. Later revisions may use assembly; a single awkward part can always be hand-added. | User decision. **Consequence: the "every populated part must be LCSC-stocked" constraint is relaxed** to "must be buyable from LCSC or UNIT". This is what un-blocked the AD620 (see D-054). Second consequence: package choice now favours hand-solderability. | 2026-11-06 | Sofia Pacheco Leon |
| D-052 | **Component selection policy: cheap, with reliable sourcing, in hand-solderable packages.** Applied to every remaining choice. | User decision, stated as "the only very essential thing". Ranks above elegance and above marginal performance. Formalised in [REQUIREMENTS.md](REQUIREMENTS.md) §9. | 2026-11-06 | Sofia Pacheco Leon |
| D-053 | **Design-gate policy relaxed for Gates 2–5 only.** Schematic, component selection, layout and checks proceed continuously without per-gate sign-off. **Gate 6 (fabrication release) and Stage 5 of bring-up (live e-match) keep mandatory written sign-off from the review owner.** | User asked whether the gate rule can be ignored "as long as it is not prejudicial". Assessed: not prejudicial for Gates 2–5, because no hardware exists and a drawing cannot injure anyone — an error there costs time, not safety. **Prejudicial for Gate 6 and Stage 5**, which are the points where a drawing becomes a physical thing and where a live initiator is connected. Gate outputs are still produced as documentation; they simply stop being approval barriers. | 2026-11-06 | Sofia Pacheco Leon |
| D-054 | **AD620 footprint changed from SOIC-8 to DIP-8, in a socket.** Still not populated by default. | D-051 removed the assembly obstacle: UNIT stocks the through-hole `AD620AN` (~111 MXN), which is both easier to hand-solder than SOIC and *socketable*. A socket makes the A/B comparison a chip pull rather than a rework. It stays depopulated by default because under D-052 it is the most expensive part on the board (~$6–8 against the ADS1220's ~$2) and the ADS1220's PGA makes it redundant. | 2026-11-06 | pending |
| D-055 | **One relay part for all four positions: `SRD-12VDC-SL-C`** (SPDT, 12 V coil, 10 A contacts, through-hole). LCSC C30431. | SPDT gives both a NO and an NC contact per relay, so the same part serves K1/K2/K4 wired NO and **K3 wired NC** for the shunt. One BOM line, interchangeable spares, through-hole for hand assembly. ~$0.23 with ~131,800 in LCSC stock, and also carried by Mexican retailers. Contact rating must still be confirmed against the e-match current (O-1). | 2026-11-06 | pending |
| D-056 | **RS-485: `SP3485EN-L/TR`** (LCSC C8963) instead of ADM2582E. **Isolation moves to the station board, powered from USB.** | SP3485EN is a 3.3 V half-duplex transceiver — native to the ESP32 domain — at ~$0.14–0.27 with ~190,700 in LCSC stock, against roughly $10 for an integrated-isolation ADM2582E. The isolation requirement is met architecturally instead: the station board carries two ground domains, a bench-referenced side powered from the umbilical and a laptop side powered from USB 5 V, with the barrier between them. **The laptop's own USB supply powers the isolated side, so no isolated DC-DC is needed** — which is what made the expensive part unnecessary. | 2026-11-06 | pending |
| D-057 | `Keystone 5015` test points replaced by **bare pads / vias**. | Free, and they work with probe hooks. D-052. | 2026-11-06 | pending |
| D-058 | **Resistors stay 0603**, reusing the existing IGNIS library part numbers. 0805 is a fallback only if hand assembly proves painful. | Corrects an over-application of D-051 in the first draft of D-057, which had moved resistors to 0805 for hand-solderability. Ignitia already owns 0603 reels from the IGNIS builds, and anyone who has assembled an IGNIS board can hand-solder 0603. Buying new 0805 reels would have added cost and a BOM line for marginal benefit — which contradicts D-052. Capacitors were already 0805 and stay there. | 2026-11-06 | pending |

| D-059 | **Firing current is sourced at the BENCH, so the pyro pair never enters the umbilical.** The e-match run is a short local ~1–2 m cable. **Revises D-016 and D-009.** | Found while drawing the schematic. K1/K2 and the arming plug all sit at the bench and switch the bench battery, which is forced by D-013 (arming plug at the bench). So the "cable A, 20 m of 16 AWG pyro pair" in D-016 does not exist: there is **one umbilical, not two**, and the 40 m-loop resistance calculation in D-009 was for a topology this design does not use. 16 AWG remains specified for the short local run, where it is trivially satisfied. | 2026-11-06 | pending |
| D-060 | **Umbilical is 12 conductors**, not 8–10: ARM, FIRE, ESTOP, CONT_SENSE, RS485_A, RS485_B, VBAT_SENSE, THRUST_P, THRUST_N, 2× GND, SHIELD | Found while drawing: the 10-pin allocation had no room for the differential thrust pair that D-010 and D-019 require, so path 2 would have been silently dropped. | 2026-11-06 | pending |
| D-061 | **AD620 path B requires the +5V_AMP rail** (AMS1117-5.0, depopulated by default). Path A runs on 3.3 V alone. | Found while drawing: the AD620's minimum **total** supply is 4.6 V, so it cannot run on 3.3 V at all. Single-supply use also needs AMP_REF biased above ground, and its output must stay inside the ADS1220 input range (O-7). | 2026-11-06 | pending |
| D-062 | Station RS-485 is **receive-only by default**: RE and DE both pulled low, TX opto and its resistors depopulated. | Nothing at the station needs to talk to the bench. Leaving the TX path unpopulated removes a route that would otherwise invite a software "fire" command later, and it costs nothing to fit if genuine two-way telemetry is wanted. | 2026-11-06 | pending |
| D-063 | Schematics are **generated from scripts** in `hardware/tools/`, not hand-drawn. | Reproducible, reviewable in diffs, and the net-class naming rules can be enforced mechanically. Regenerating is one command; the `.kicad_sch` files remain ordinary KiCad files that open and edit normally. | 2026-11-06 | pending |

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
