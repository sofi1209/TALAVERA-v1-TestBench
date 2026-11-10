# TALAVERA v1 — Consolidated design proposal, Rev A → Rev A.1

**Date:** 9 November 2026 · **Baseline:** commit `43e9803` · **Status: PROPOSAL — NOT APPROVED**

**Inputs:** two independent audits of the same files, Claude (`AUDIT-2026-11-09.md`) and ChatGPT
(`TALAVERA-v1-schematic-audit.md`), plus ChatGPT's review of the Claude audit. This document supersedes the
recommended fixes in `AUDIT-2026-11-09.md` where they differ (see §9, errata).

> **Safety.** Every change to the arm, fire, shunt, continuity, E-STOP, battery or high-current path below is
> a **proposal for the review owner's decision and written sign-off**. Nothing here approves a circuit.
> Verification is on an **inert fixture** (dummy load resistor plus current meter), never a live initiator,
> and only under the project's written authorization. The governing principle is unchanged: **no
> microcontroller takes part in arming, firing or emergency stop.**

Status key: **V** verified (netlist or a fetched datasheet) · **A** assumed (named evidence still needed) ·
**D** decision for the review owner.

---

## 1. Where the two audits agree (diagnosis, both verified)

| Problem | Claude ID | ChatGPT ID |
|---|---|---|
| Series Schottky `D_RP1` reversed, so nothing downstream of F1 is powered | B-3 | B01 |
| Firing output has no return: `PYRO_MATCH_N` = `K3.12, P1.2, U_CONT1.2` only | B-1 | B03 |
| Continuity circuit unexcited and wired across the load; reads the shunt when disarmed | B-2 | B04 |
| Station has no supply conductor in the umbilical; `PWR_FLAG` hides it from ERC | M-10 | B02 |
| E-STOP drops K4 only: shunt stays open with ARM on; ESTOP short to GND defeats it | M-7, M-8 | B05 |
| ARM/FIRE adjacent-conductor short bypasses FIRE | M-9 | B06 |
| Regulator capacitance missing or uncharacterised; bench LDO thermal; station has no caps | M-3/4/5 | B08 |
| DevKitC: drawn as a bare module; mutually exclusive supplies violated | M-6 | M01 |
| 6N137 RX path inverts the UART; no current margin; SP3485 RO cannot drive the LED | M-2 | M02 |
| MLT-8530 is an externally driven transducer on a 12 V DC drive | M-13 | M04 |
| AD620 path B: floating REF, no caps, unqualified headroom | M-14 | M06 |
| Path 2 (`THRUST_DIFF`) has no source | m-2 | M08 |
| `VBAT_SENSE` scaling and meter undefined; J_DAQ bridges the isolation barrier; shield at both ends | m-8, m-3, m-9 | M09, M03 |

**Added from the ChatGPT audit (each checked against the files, V):** E-STOP release while ARM and FIRE are
held re-energizes the output; firmware samples at 20 SPS (`ADS_REG1 = 0x04`) and labels raw counts
`thrust_N`; `ADC_CS` has no pull-up; the SD-detect note says pin 9 while the wiring uses pin 10; the BOM still
lists `S_CONT` and the "cable A" pyro terminal; the repo's own standoff estimate falls below its cited
minimum; NTS4001N V<sub>GS(max)</sub> = ±20 V (closes the 6 Nov C-5 datasheet check).

---

## 2. The three coupled decisions

ChatGPT's framing is right: station power, E-STOP behaviour and pre-arm continuity drive the harness and
relay design together. They must be decided in one review.

| # | Decision | Recommended | Alternative | Why recommended |
|---|---|---|---|---|
| **D1** | Station power | **Fed from the bench battery** on a dedicated umbilical conductor, fused at the bench (`F3`, value TBD, ~0.5 A class), tapped from `+12V_PROT` | Separate fused station battery with its own switch | One battery to manage (consistent with D-047). A dead or disconnected bench battery leaves the station dead, which is the safe direction. Load ≈ 170 mA peak (§4.5) |
| **D2** | E-STOP | **Two diverse channels plus a latched ARM PERMIT.** Channel 1 (existing): E-STOP breaks K4's coil. Channel 2 (new, station-local): a second NC block drops a latching permit relay `K6` that feeds the ARM key. Re-enable needs **RESET** with the key OFF and FIRE released, then a fresh ARM | Single-channel E-STOP plus procedure | Meets "release never re-energizes the output", needs no new umbilical conductor, and a cable short to GND can no longer defeat the ARM-dropping channel. All relays and switches, no semiconductors except flyback diodes |
| **D3** | Continuity | **Pre-arm check via a momentary CONT TEST control**, keeping the written requirement. TEST energizes **K3 only** (shunt open, low side grounded) while K1/K2 stay de-energized. Sense current is sourced from the TEST line itself through a fault-tolerant series limit | Armed-state check (needs a requirement change) | Keeps REQUIREMENTS.md as written ("before arming") and keeps the firing path disabled during the test. No sense current flows at any other time. A sense-line short to GND becomes self-revealing (§4.3) |

---

## 3. Arm / fire / shunt chain (bench) — **D**

### 3.1 Proposed topology

```
+12V_PROT ──K4 (NO, master)──► +12V_MASTER ──K1 (NO, ARM)──► ARM_BUS ──K2 (NO, FIRE)──► PYRO_FIRE_OUT
                                                                                            │
                         CONT_TEST ─► R_CONT_A ─► R_CONT_B ─► D_BLK ─► opto LED ───────────┤   (sense injection)
                                                                                            │
                                                                                        J_ARM (plug)
                                                                                            │
                                                                                      PYRO_MATCH_P
                                                                                            │
                                                                                         [E-MATCH]
                                                                                            │
                                                                                      PYRO_MATCH_N
                                                                                            │
                                                                     K3 COM ── NC → PYRO_MATCH_P  (shunt, de-energized)
                                                                            └─ NO → GND           (low side, energized)

K3 coil: ARM_LINE ─►|─┐                       (D_A3: ARM energizes K3)
         CONT_TEST ─►|─┴─ K3.A1, K3.A2 = GND  (D_T3: TEST energizes K3 only, not K1)
```

| State | K4 | K1 | K2 | K3 | Match terminals | Current through match |
|---|---|---|---|---|---|---|
| Disarmed | any | open | open | de-energized | **shorted together, floating from GND** | none |
| CONT TEST held | any | open | open | energized | shunt open, low side to GND, **no source path** | sense current only, limited by R_CONT_A + R_CONT_B |
| Armed | closed | closed | open | energized | shunt open, low side to GND | none |
| Fire | closed | closed | closed | energized | source to GND | fire current |
| E-STOP | open | open (permit dropped) | open | de-energized | shorted, floating | none |

### 3.2 Why K3 does both jobs, and what happens when it fails

This answers ChatGPT's objection, that one relay is responsible for both functions. The two contacts of one
Form C pole are mutually exclusive by construction, so **the shunt can never be across a live source**. With
separate relays, a shunt that fails to open while the fire relay closes shorts the battery through the shunt
contact.

| K3 failure | Effect | Safe? | How it is detected |
|---|---|---|---|
| Coil open, or NC contact welded | Shunt stays closed, low side never grounds | **Yes**: cannot fire | CONT TEST never lights |
| NO contact welded | Shunt cannot close; low side permanently grounded | Degraded: K4 + K1 + K2 + plug still in series | Pre-test meter check across `P1` with plug out, disarmed, match disconnected: must read ≈ 0 Ω (shunt). Add to the checklist |
| Transfer bridging (make-before-break) | Momentary battery path through the shunt during fire | Fuse stress | Requires break-before-make. **A**: standard Form C changeover is break-before-make; confirm with Songle, or measure transfer on a bare relay with a scope |
| Contact rating | Fire current through the NO contact | — | SRD NO 10 A / NC 6 A at 28 VDC (**V**, Songle via LCSC). Fire current is unknown until O-1 |

**Alternative (D):** a dedicated low-side relay `K5` (NO to GND), with K3 kept as a pure NC shunt. One more
SRD (~$0.23) separates the functions but reintroduces the shunted-battery failure. The review owner chooses.

### 3.3 Continuity sense chain rules

- **Two series resistors** `R_CONT_A`, `R_CONT_B`, each alone sufficient to hold sense current below the
  agreed fraction of no-fire current. A single shorted resistor must not raise current above the limit. Values
  are blocked on O-1.
- `D_BLK` (series blocking diode) protects the opto LED from reverse voltage while firing (`PYRO_FIRE_OUT` at
  ~12 V while `CONT_TEST` is at 0 V).
- **Move `D_FIRE` off `PYRO_FIRE_OUT`** to `FIRE_LINE` at the bench (K2 coil command, still hardware). In its
  current position it is a ground path that would light the opto with the match **disconnected**.
- Single opto part, **CTR-binned**. Resolve PC817 vs TLP521GB-S vs "6N137" to one MPN.
- Station load: delete `R_CONT_PU1`; high-efficiency `D_CONT` at ~2 mA (`R_D_CONT` ≈ 4.7–5.1 k at 12 V). Then
  the required opto LED current, which equals the sense current through the match, is ~2 mA ÷ CTR<sub>min</sub>. Final
  number set by the review owner against O-1.

### 3.4 Reverse polarity, without a series element in the fire path

- Delete `D_RP1`. Add a **crowbar diode** after F1 (A → GND, K → `+12V_FUSED`). A reversed battery forward-biases
  it and clears F1. Diode surge rating must coordinate with F1's I²t: **A**, part and fuse TBD (O-17).
- **Keyed, polarized battery connector** (e.g. XT60-class), so reversal is mechanically hard.
- `F1` in a **blade-fuse holder** (field-replaceable). This also answers ChatGPT's point that a surge rating
  cannot qualify a series diode: no series diode remains.
- **Unidirectional TVS** on `+12V_PROT` (≥ 15 V standoff, for SLA charge at 14.4–14.7 V) plus a bulk
  electrolytic for hot-plug damping. The clamp voltage (~24–26 V class) is acceptable once the AMS1117 front
  end (15 V abs max, **V**) is gone (§5).

---

## 4. Station and umbilical — **D**

### 4.1 E-STOP / ARM PERMIT latch (station, new)

```
+12V_STN ─ E-STOP NC block 2 ─► P ─┬─ ARM key NC aux ─ FIRE NC aux ─ RESET (NO) ─┐
                                   │                                             ├─► L ── K6 coil ── GND
                                   └──────────── K6 COM→NO (self-hold) ──────────┘
L ─► ARM key (NO) ─► ARM_LINE ─► FIRE button (NO) ─► FIRE_LINE
L ─► CONT TEST (momentary NO) ─► CONT_TEST
```

- E-STOP pressed: K6 drops, so ARM, FIRE and CONT TEST are dead, K1/K2/K3 drop and the **shunt recloses**.
  Channel 1 drops K4 independently.
- E-STOP released: nothing re-energizes. RESET only latches K6 with the **key OFF and FIRE released**.
- Station power loss or brownout: K6 drops and a manual reset is required. No automatic restart.
- E-STOP mushroom needs two NC blocks; the ARM key and FIRE button each need an NC auxiliary block. Panel parts
  TBD with the contact-block configuration.
- K6 = same `SRD-12VDC-SL-C` with flyback (one part type across both boards).

### 4.2 Umbilical pinout (12 conductors, path 2 deferred)

| Pin | Net | Adjacent fault result |
|---|---|---|
| 1 | `ARM_LINE` | ↔ 2 GND: fuse/permit drops (safe) |
| 2 | GND | — |
| 3 | `FIRE_LINE` | ↔ 2/4 GND: K2 cannot energize (safe) |
| 4 | GND | — |
| 5 | `CONT_TEST` | ↔ 6 sense: line held high, lamp dark (false-*bad*, safe) |
| 6 | `PYRO_CONT_SENSE` | ↔ 7: VBAT through 47 k, negligible |
| 7 | `VBAT_SENSE` | ↔ 8 ESTOP: 47 k source, < 0.1 V on K4 coil, K4 releases (drop-out ≥ 0.6 V, **V**) |
| 8 | `ESTOP_LOOP` | ↔ 9 +12 V: coil sees ~0 V, K4 releases (safe) |
| 9 | `+12V_STN_FEED` (fused F3 at bench) | ↔ 10: 12 V on RS-485 A, so a TVS is required |
| 10 | `RS485_A` | — |
| 11 | `RS485_B` | — |
| 12 | Shield (bench end only, per final grounding diagram) | — |

ARM and FIRE are no longer adjacent. **Residual risk (D):** a crushed cable can still bridge any two
conductors (ChatGPT). Separation fixes connector-level faults only, and adjacency must be re-checked against
the chosen connector's real geometry (circular connectors are not linear). Mitigations remain procedural:
plug inserted last, personnel clear before ARM, and harness inspection.

### 4.3 Self-revealing continuity faults (procedure + design)

The continuity lamp is meaningful **only while CONT TEST is held**. Rule: *lamp lit with TEST released = sense
fault, stop.* This converts the `PYRO_CONT_SENSE`-to-GND false-good (ChatGPT B04) into a visible fault.

### 4.4 Station telemetry (replaces the 6N137 fix in AUDIT-2026-11-09, see errata)

- Replace `U_ISO1`/`U_ISO2` (6N137) with a **2-channel digital isolator** (non-inverting, SOIC-8, one RX
  channel used; part and stock TBD, e.g. the ADuM1201 class already named in UMBILICAL-AND-TELEMETRY.md). Side 1
  on `+3V3_BENCH`, side 2 on `+5V_USB` or `+3V3` from the CH340C supply. This removes the inversion, the LED
  drive margin (SP3485 RO is specified only at −1.5 mA / +2.5 mA, **V**) and the mandatory 6N137 bypass.
- Station receive-only: keep `RE` low and `DE` low. Add bias for a defined idle state; the SP3485 datasheet
  covers open/shorted inputs but not an idle terminated bus (**V**).
- **Bench `R_TERM` → DNP:** bench is the only driver, so terminate at the receiver only. This roughly halves
  driver current. **A**: confirm with an edge-rate check over the real 20 m cable.
- SM712-class TVS on A/B at both ends.

### 4.5 Station power

- Supply loads after the isolator change: SP3485 + isolator side 1 (a few mA). Replace the 12→5→3.3 AMS1117
  cascade with **one 3.3 V regulator rated ≥ 20 V input** (TO-92 78L33-class is hand-replaceable; part **A**),
  with datasheet-specified caps. `+5V_BENCH` is deleted.
- Station 12 V budget (**A**, SRD 30 mA per coil **V**): K1 + K3 ≈ 60 mA, K2 ≈ 30 mA, K6 ≈ 30 mA, lamps
  ≈ 15 mA, active buzzer ≈ 20–30 mA, regulator ≈ 5 mA, so **≈ 170 mA peak**. At an assumed 24 AWG conductor
  (~84 mΩ/m), the 20 m feed plus two parallel GND returns drop ≈ 0.4 V, well clear of the 9 V pick-up (**V**).
- Buzzer: **12 V active (self-drive) sounder**, panel-mount on terminals. Keep `Q_BUZZ` and its divider, or drive
  the sounder directly from `ARM_LINE` and delete the MOSFET (simpler, one fewer part to fail).
- Delete `J_12V1`'s `PWR_FLAG` fiction: the rail is sourced by J_UMB pin 9.

---

## 5. Bench logger, power and measurement

| Item | Proposal | Status |
|---|---|---|
| Logger supply | `+12V_PROT → F2 → 5 V stage on a 7805 TO-220 footprint` (LM7805 + clip heatsink, or a pin-compatible switching drop-in; either is hand-swappable) → Schottky → **DevKitC 5V pin**. Removes the 1.3–1.4 W SOT-223 drop and the 15 V abs max | D / part A |
| 3.3 V domain | Peripherals (ADS1220, SD, SP3485) on the **DevKitC 3V3 pin as an output**: one 3.3 V domain, so no back-feed between domains (ChatGPT M01) and no USB conflict. Load ≈ 215 mA peak incl. SD and RS-485. **A**: DevKitC LDO rating from the Espressif schematic | A |
| Analog rail | ADS1220 AVDD through a ferrite + 10 µF/100 nF; separate AVDD/DVDD bypass at the pins | A |
| Measurement | **Single path: bridge → ADS1220 PGA → SD.** Delete U_AMP, R_G, R_BYP1–4, U_5V (path B) and the `THRUST_DIFF` path 2 for Rev A. Record the loss of path-2 redundancy in REQUIREMENTS.md (both audits agree) | D |
| ADC inputs | Differential + common-mode RC at AIN0/AIN1, ESD at J_LC, 5th pin for the load-cell shield | A |
| SPI defaults | **10 k pull-up on `ADC_CS`** (new; SD_CS already has one); 10 k pull-down on `RS485_DE` | V (gap) |
| DevKitC symbol | Replace WROOM-32D with a 2×19 DevKitC V4 header symbol matching Espressif's J2/J3; drop R_EN/C_EN (on-module) | V |
| SD detect | Fix note (pin 10 = DET_A, pin 9 = GND) and confirm the THD2528 switch type on a real part | V (note) / A (switch) |
| Indicators | 1 k LED resistors to 0805 or 2.2 k | A |

**Firmware (logger, not safety):** set data rate against the motor rise time (≥ 1 kSPS per the trade study;
20 SPS today), log **raw counts** until calibrated (no `thrust_N` label), add a sample sequence number and
dropped-sample count, decouple SD writes from sampling (buffer), defined fault indication on SD failure, and
implement RS-485 TX with explicit DE control. None of this touches arm, fire or E-STOP.

---

## 6. Repairability

1. **Keyed, locking, pluggable terminals** for battery, match, load cell, panel controls and umbilical, each a
   different key or pitch so nothing mates with the wrong header.
2. **Blade fuses** (F1, F2, F3), with the crowbar instead of an SMD series diode.
3. **TO-220 / TO-92 regulators** on standard footprints. Sockets for the DevKitC (already planned). THT relays.
   0805 minimum passives. Avoid SOD-923 where a larger ESD part fits.
4. **Labelled test points with an adjacent ground** on: `+12V_RAW/FUSED/PROT/MASTER`, `+5V_LOGGER`, `+3V3`,
   `ARM_LINE`, `FIRE_LINE`, `CONT_TEST`, `ESTOP_LOOP`, `ARM_BUS`, `PYRO_FIRE_OUT` (recessed), `PYRO_MATCH_P/N`
   (recessed), ADC inputs and reference, the station feed. Expected voltage per state printed in the bring-up
   plan.
5. **Removable power links** (jumper or 0 Ω header) for the logger and telemetry rails, so either can be
   isolated without touching the interlocks.
6. Silkscreen relay roles ("K3: NC = SHUNT, NO = LOW SIDE"), connector pin numbers and polarity on both mating
   drawings.
7. Generators: portable output paths; fail on missing libraries; revision-locked BOM and harness drawing
   generated from the reviewed schematic.

---

## 7. Requirement changes to write down (before redrawing)

| ID | Requirement |
|---|---|
| R-ES1 | E-STOP de-energizes K4 **and** the ARM permit; the shunt recloses. Releasing E-STOP never re-energizes any output. Re-enable needs RESET with the key OFF and FIRE released, then a fresh ARM. |
| R-ES2 | No single umbilical conductor short may defeat both E-STOP channels. |
| R-CT1 | Continuity is checked **before arming**, by a momentary CONT TEST, with K1 and K2 de-energized throughout. |
| R-CT2 | Sense current stays below *[review owner: fraction]* of the initiator's no-fire current with any single resistor shorted. |
| R-CT3 | Lamp lit only while TEST is held; lit at any other time = fault. Match disconnected → lamp stays dark. |
| R-PW1 | Station powered from the bench battery via a fused dedicated conductor (if D1 accepted). |
| R-MS1 | Rev A measurement = ADS1220 → SD only. Path 2 and path B deferred; loss of analog redundancy accepted in writing. |
| R-SD1 | Site standoff resolved against motor class, barrier and governing code before the harness length is frozen (repo's 15–17 m estimate is below its own cited minimum). |

---

## 8. Inert-fixture verification matrix (after redraw, under written authorization)

Fixture: dummy load (resistor sized to the e-match, with a series current meter) in place of `P1`; current-
limited bench supply for the battery; live initiator **never** fitted.

| # | Setup | Action / fault | Expected |
|---|---|---|---|
| 1 | Disarmed, plug in | — | Load current 0; P1 terminals shorted; lamps dark |
| 2 | Disarmed, plug in | CONT TEST held | Lamp lit; load current = sense value; K1/K2 open; ARM_BUS = 0 V |
| 3 | Disarmed, **load disconnected** | CONT TEST held | **Lamp dark** |
| 4 | Disarmed | CONT TEST released | Lamp dark within relay release time |
| 5 | Armed, plug in | — | Load current 0; ARMED lamps lit; shunt open |
| 6 | Armed, plug **out** | FIRE held | FIRING indication; load current 0 (K2 weld screen) |
| 7 | Armed, plug in | FIRE held | Fire current through load; measure value and contact drop |
| 8 | Armed + FIRE held | E-STOP pressed | Load current 0; K1/K2/K3/K4 drop; shunt recloses; measure stop latency |
| 9 | After 8, ARM + FIRE still held | E-STOP released | **Load stays de-energized** |
| 10 | After 9 | RESET with key ON | K6 does not latch |
| 11 | Key OFF, FIRE released | RESET, then ARM | Returns to state 5 only |
| 12 | Armed | Short pin 8 (ESTOP) to GND, then E-STOP | Channel 2 still drops ARM; load 0 |
| 13 | Disarmed | Short `PYRO_CONT_SENSE` to GND | Lamp lit **without** TEST → flagged fault |
| 14 | Disarmed | Short `CONT_TEST` to `ARM_LINE` | TEST also arms K1 → ARMED lamp lights during TEST → visible fault, still no fire without FIRE |
| 15 | Any | One `R_CONT` shorted | Sense current still ≤ limit (R-CT2) |
| 16 | Battery reversed (current-limited) | Connect | Crowbar conducts, F1 clears, nothing else damaged |
| 17 | K3 relay on the bench | Scope COM during transfer | Break-before-make confirmed |
| 18 | Logger | Short `+3V3`, unplug SD, USB plugged while battery on | Interlocks unaffected; no back-feed; logger fault indicated |
| 19 | Telemetry | Known pattern over 20 m, bench off/on, USB off/on | Correct bytes; defined idle; no false data |
| 20 | Native ERC (KiCad 10) | Re-export | 0 errors; each warning justified; source vs export diff = 0 |

---

## 9. Errata to `AUDIT-2026-11-09.md` (Claude)

1. **M-2 fix withdrawn.** Sinking the 6N137 LED from SP3485 RO exceeds RO's specified +2.5 mA (MaxLinear
   SP3485). Replaced by the digital isolator in §4.4. The polarity diagnosis stands.
2. **M-1 / SS24 surge argument withdrawn.** A surge rating at a specified test waveform does not qualify the part
   for an unknown pulse and fault. Replaced by the crowbar topology in §3.4.
3. **B-2 armed-state continuity withdrawn** in favour of the pre-arm CONT TEST (§2 D3), which keeps the written
   requirement.
4. **M-7 fix incomplete.** A second E-STOP contact alone allows restart on release. Replaced by the permit latch
   (§4.1).
5. **Evidence reproducibility.** `tools/reach2.py` as shipped prints `reaches GND=True` because it traverses
   back through `PYRO_MATCH_P` and treats every relay contact as closed. The `match_return_path_trace.txt`
   result came from an unshipped inline variant. The finding is unaffected (`PYRO_MATCH_N` has exactly three
   pins), but the package now ships `tools/trace_match_return.py`, which reproduces the evidence file.
6. "Logger cannot energize the output" is shown **for the schematic as drawn** only. Installed-harness, rail,
   clamp and cross-short faults are covered by matrix rows 12–18, not by netlist analysis.

## 10. Generator change list (Rev A.1)

**`hardware/tools/gen_bench.py`**
- L34–37: delete `D_RP`; add crowbar diode, TVS, bulk cap; F1 → blade holder.
- L53–62: delete `U_3V3`, `U_5V`; add the 7805-footprint 5 V stage, Schottky to DevKitC 5V.
- L107: K3 → COM `PYRO_MATCH_N`, NC `PYRO_MATCH_P`, NO `GND`; coil via `D_A3` (ARM) / `D_T3` (CONT_TEST).
- L132–139: `R_CONT_A` + `R_CONT_B` + `D_BLK` + opto from `CONT_TEST` into `PYRO_FIRE_OUT`; one opto MPN.
- L179–200: delete U_AMP, R_G, R_BYP1–4. Wire J_LC → RC filter → AIN0/AIN1.
- L211–245: DevKitC 2×19 header symbol; remove R_EN/C_EN; `ADC_CS` pull-up; `RS485_DE` pull-down.
- L267: SD-detect note pin 9 → pin 10.
- L279: `R_TERM` DNP. L289: `D_FIRE` net → `FIRE_LINE`.
- L301+: J_UMB pinout per §4.2; F3 + `+12V_STN_FEED`; delete `THRUST_DIFF`; test points; power links.
- `OUT`: relative path.

**`hardware/tools/gen_station.py`**
- L28–33: J_UMB pinout per §4.2. L39: delete `J_12V`'s PWR_FLAG source; rail from J_UMB pin 9.
- L42–44: one ≥ 20 V-input 3.3 V regulator with datasheet caps; delete `+5V_BENCH`.
- L53–61: E-STOP two NC blocks; K6 permit latch, RESET, key/FIRE NC aux contacts; CONT TEST momentary.
- L82–92: `D_CONT` ~2 mA; delete `R_CONT_PU`.
- L100: LS1 → 12 V active sounder.
- L137–157: digital isolator replaces U_ISO1/2 and R_ISO*; idle bias; TVS.
- L204: delete J_DAQ (path 2 deferred).

## 11. Open items still blocking values

O-1 e-match (no-fire / all-fire / resistance) → R_CONT_A/B, F1/F3, fire current, contact margin · O-2 load
cell → PGA gain, filter corner, data rate · O-3 relay physical pin map (K3 NO/NC swap would invert both the
shunt and the low side) · O-17 fuses and crowbar coordination · panel-part contact-block configuration ·
connector choice (re-check §4.2 adjacency) · DevKitC LDO rating · digital isolator and 3.3 V regulator MPNs
with stock · Songle break-before-make evidence.
