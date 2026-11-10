# TALAVERA v1 — Independent schematic audit, 9 November 2026

**Revision audited:** Rev A schematics, commit `43e9803` (`sofi1209/TALAVERA-v1-TestBench`), KiCad 10.0.5
netlist exports dated 2026-11-09T16:11, ERC reports dated 2026-11-09T16:12.
**Method:** both `.net` exports parsed by an independent script (not the repo's `netlist.py`), every net read
by pin function, plus a DC-path trace of the pyro loop. The repo's own Python tools were **not executed**.
Datasheet values were fetched where possible; anything not fetched is marked **assumed**.

**Verdict: NOT FIT FOR LAYOUT.** Three blockers. Two of them are in the pyro circuit and were missed by both
automated checkers, the 6 Nov audit, *and* the cross-model handoff — which described the pyro circuit
incorrectly (see §4).

> **Safety status.** Nothing here approves any pyro, battery or high-current circuit. Proposed fixes for the
> arm/fire/shunt/continuity path are topology suggestions for the review owner's decision and sign-off.
> Bring-up of anything in the fire path uses an inert load only.

Status key — **V** verified (netlist, or datasheet fetched this session) · **A** assumed (needs the named
datasheet) · **J** judgement call, not ranked on facts alone.

---

## 1. Findings

| ID | Sev | Location | Evidence | Why it is wrong | Recommended fix | Status |
|---|---|---|---|---|---|---|
| **B-1** | **Blocker** | `PYRO_MATCH_N` (bench) | Net members: `K3.12, P1.2, U_CONT1.2` — nothing else. DC trace from `PYRO_MATCH_N` that does not re-enter `PYRO_MATCH_P` reaches only `CONT_LED_A` and `K3.14(NC flag)`. | **The firing loop has no return.** Current from K4→K1→K2→J_ARM→match has nowhere to go: `MATCH_N` touches only the shunt contact and the opto LED, both of which lead back to `MATCH_P`. The bench **cannot fire**. Root cause: D-045 dropped the IGNIS gate-drive half, and the low-side MOSFET *was* the return. README still says "1 channel, low-side". | Use K3's unused NO contact as the low-side switch: **K3 COM = `PYRO_MATCH_N`, NC = `PYRO_MATCH_P`, NO = `GND`**. Zero added parts. Disarmed: match shorted **and** disconnected from ground. Armed: shunt open, low side grounded. The shunt then never carries battery current (form C is break-before-make), and fire current passes through K3's NO contact (10 A rated) instead of its NC (6 A). **Review owner decision.** | V |
| **B-2** | **Blocker** | `R_CONT1`, `U_CONT1` (bench); `D_CONT1`, `R_CONT_PU1` (station) | `R_CONT1.1 = PYRO_MATCH_P`, `U_CONT1.2 = PYRO_MATCH_N`: R + LED sit **in parallel** with the match. No net supplies current into this island. | **Continuity sensing has no excitation source and the wrong topology.** (a) Nothing drives it, so the lamp can never light. (b) A detector in parallel with a 1–2 Ω match measures voltage *across* it, not continuity. (c) While disarmed, K3 shorts both terminals, so any disarmed-state check reads the **shunt**, not the match — always "good" (OPERATIONS-MANUAL §2.3 already concedes this). The README diagram shows the original source came from the station over cable A; D-059/O-18 deleted cable A and the source went with it. | Make continuity an **armed-state** check, sourced from `ARM_BUS`: `ARM_BUS → R_CONT → opto LED → PYRO_FIRE_OUT` (across K2's contacts), returning through plug → match → K3 NO → GND. Lamp lit = armed **and** plug in **and** match intact **and** low side closed. No sense current flows while disarmed, which settles the H-2 question by construction. Two dependencies: move `D_FIRE` off `PYRO_FIRE_OUT` (see M-12), and cut the station load (see M-11). `R_CONT` value stays blocked on O-1. **Review owner decision.** | V |
| **B-3** | **Blocker** | `D_RP1`, `gen_bench.py:34-37` | `D_RP1.1 (K_1)` on `+12V_FUSED`, `D_RP1.2 (A_2)` on `+12V_PROT`. | Series Schottky has its cathode on the battery side, so it is reverse-biased in normal polarity and **nothing downstream of F1 is powered**. Confirms the handoff. | Swap the stubs (pin 2 to `+12V_FUSED`). **Also see M-1**: swapping alone leaves a 2 A part in a 6–10 A fire path. | V |
| M-1 | Major | `D_RP1` in the fire path | Fire current flows `+12V_PROT → K4 → K1 → K2`, i.e. through `D_RP1`. SS24: I<sub>F(AV)</sub> 2 A, I<sub>FSM</sub> 50 A (distributor listing). | At 12 V into a ~1–2 Ω match plus contacts, fire current is ~6–10 A (match R unknown, O-1). A short ignition pulse is inside the surge rating, but a match that fails short, or a held FIRE button, puts 6–10 A DC through a 2 A diode. | Pick one: (a) P-MOSFET reverse-polarity stage at the input, sized for the fire current; (b) **crowbar diode after F1** (reversed battery → diode conducts → F1 blows), zero forward drop, very simple, costs a fuse after a mistake; (c) keyed, non-reversible battery connector in addition. For an easily repaired board: (b)+(c) with a blade fuse. Note: without protection, reversed polarity forward-biases `D_K4` through the E-STOP loop. | V (topology) / A (match current) |
| M-2 | Major | Station `U_ISO1`, `R_ISO1` | `RO_BENCH → R_ISO1 → U_ISO1.2(A)`, `U_ISO1.3(C) → GND`. 6N137 truth table: LED on + enable H → **output L** (Everlight 6N137 datasheet, p. 1). | **The RX isolator inverts the UART.** RS-485 idle (mark) = RO high = LED on = `UART_RX_USB` low, so the CH340C sees a continuous break. Telemetry path 3 cannot work. The DNP TX path has the same inversion. M-3 "fixed" (8.18 mA) used typical V<sub>F</sub> and ignored RO output drop; worst case is ≈5 mA = I<sub>FT</sub> max (5 mA, datasheet p. 3), zero margin. | LED anode → `R_ISO1` → `+3V3_BENCH`; cathode → `RO_BENCH`. RO low = LED on = output low: non-inverting. Drop `R_ISO1` to ~150 Ω for margin (recompute from the chosen 6N137 vendor's V<sub>F(max)</sub>). Same for `U_ISO2`. | V |
| M-3 | Major | Station rails `+12V_STN`, `+5V_BENCH`, `+3V3_BENCH` | No capacitor on any of the three; only `C_USB1`, `C_V3` exist. | AMS1117 datasheet: "22 µF solid tantalum on the output will ensure stability". Two cascaded LDOs with **no output capacitance** can oscillate, which breaks the RS-485 receiver. The SP3485 has no local decoupling. The 6N137 datasheet states a 0.1 µF bypass **must** be connected at pins 8–5; `C_USB1` is shared with the CH340C. | Per regulator: 10 µF input, 22 µF tantalum output (or the chosen vendor's documented equivalent). 100 nF at `U_485` VCC, 100 nF at each 6N137 pins 8–5. | V |
| M-4 | Major | Bench `U_3V3`, `+3V3_LOGGER` | Output capacitance is ceramic only: `C6`, `C10` 10 µF and four × 100 nF, all `Device:C`. | Datasheet stability case is 22 µF tantalum. Ceramic-only output is not covered by this datasheet, and some AMS1117 sources oscillate on low-ESR outputs. | Add a 22 µF tantalum (or electrolytic) at `U_3V3` output, or choose an LDO documented as ceramic-stable. | A — confirm against the LCSC C6186 vendor datasheet |
| M-5 | Major | Bench `U_3V3` thermal and input | AMS1117: θ<sub>JA</sub> SOT-223 "46 °C/W to >90 °C/W depending on mounting", T<sub>J</sub> 125 °C continuous, thermal shutdown 165 °C, **V<sub>IN</sub> abs max 15 V** (datasheet p. 2, 4–5). | At 12.7 V and ~150 mA (A), P ≈ 1.4 W → T<sub>J</sub> ≈ 120–182 °C at 55 °C ambient. Realistic layouts are over the limit and can reach thermal shutdown, resetting the logger during the burn. The 150 mA budget should also include the SP3485 driving two 120 Ω terminations (~30–40 mA while transmitting). An SLA on charge sits at ~14.4–14.7 V, close to 15 V abs max, and no TVS limits hot-plug ringing on `C1`. | **Cascade, and make it hand-replaceable:** a TO-220 5 V stage on a 7805 footprint (LM7805 with clip heatsink, or a pin-compatible switching drop-in such as a 7805-replacement module), then a 3.3 V LDO for the analog rail. The 5 V rail also fixes M-6. Add a unidirectional TVS (~15–18 V standoff, part TBD) plus a bulk electrolytic on `+12V_PROT`. | V (datasheet) / A (current, ambient, V<sub>batt</sub>) |
| M-6 | Major | `MCU1` (DevKitC V4) supply | `MCU1.2` fed from `+3V3_LOGGER`. Espressif DevKitC V4 guide: power "must be provided using one and only one" of USB / 5V pin / 3V3 pin, "otherwise the board and/or the power supply source can be damaged". | Plugging USB into the socketed DevKitC to flash or debug while the bench battery is connected back-feeds two 3.3 V regulators into each other. This will happen during bring-up. | Feed the DevKitC **5V pin** from the new 5 V rail through a Schottky (ORing with USB VBUS; verify against the DevKitC schematic), and power the ADC/SD/SP3485 from the board's own 3.3 V LDO. Replace the WROOM-32D symbol with a 2×19 DevKitC V4 header symbol so the netlist matches what is soldered (closes M-2 of the 6 Nov audit). | V (Espressif) |
| M-7 | Major | Station `J_ARMSW1`, `J_ESTOP1`; bench `K4` | `ARM_LINE` is sourced only from `+12V_STN` through the key switch. E-STOP only breaks `K4`'s coil. | **E-STOP does not return the bench to the de-energized state.** With the key on and E-STOP pressed, K4 removes fire power (fire is prevented), but K1 and K3 stay energized, so **the shunt stays open**. That contradicts SAFETY.md and OPERATIONS-MANUAL §2.3 ("a pressed E-STOP ... same result"), and the shunt is the H2 defence against induced energy. | Cheapest fix, station only: a second NC contact block on the E-STOP mushroom in series between `+12V_STN` and the ARM key. Then E-STOP drops K1, K2 and K3 too, and the shunt recloses. | V (topology) |
| M-8 | Major (J) | `ESTOP_LOOP`, umbilical pin 3 | K4 coil low side → 20 m conductor → NC switch → GND. | A single short of `ESTOP_LOOP` to GND or shield (cable crush, connector debris) holds K4 in and **silently defeats E-STOP**. SAFETY.md H4 covers cut cables but not shorts. | Options for the review owner: high-side E-STOP (out-and-back pair carrying `+12V_PROT`, with a PTC, so a short to ground drops K4), or keep low-side but add a pre-test E-STOP functional check to the procedure (it already exists at step 4, so this is about whether a single fault is acceptable). | J |
| M-9 | Major (J) | Umbilical pinout, both boards | `ARM_LINE` = pin 1, `FIRE_LINE` = pin 2, adjacent. | One pin-1/pin-2 short (solder bridge, bent pin, crushed cable) makes **FIRE follow ARM**: the match fires when the key turns, defeating the "button held" element. | Separate them with a ground: e.g. 1 ARM, 2 GND, 3 FIRE. Keep `ESTOP_LOOP` away from GND pins if it stays low-side. | V (pinout) / J (severity) |
| M-10 | Major | Station `+12V_STN`, `J_12V1` | Only source is the 2-pin "+12V tap", behind a PWR_FLAG. Sheet text: "The station draws its bench-referenced power FROM the umbilical". Umbilical pins 1–9 carry signals, 10–12 are GND/shield. **No supply conductor exists.** No fuse on the station side. | The energy that pulls in K1, K2 and K3 has no defined source. The PWR_FLAG hides that from ERC. An unfused station supply drives 20 m of `ARM_LINE`. The ops manual mentions a station "power switch" that is not drawn. | Decide and draw it. Option A: separate station battery, fused, with a power switch. Option B: carry fused `+12V_PROT` up a reallocated conductor (pin 11 is a duplicate GND; pins 8/9 are unused until O-19). Either way, fuse it at the source. ARM pulls ~60 mA plus lamps/buzzer, FIRE ~30 mA (SRD 400 Ω coils, V). | V |
| M-11 | Major | Station `R_CONT_PU1` 4k7 + `R_D_CONT1` 1k on `PYRO_CONT_SENSE` | Opto must sink 12 V/4.7 k + (12 − V<sub>F</sub>)/1 k ≈ 12 mA (A: V<sub>F</sub> ≈ 2 V). | With an opto CTR of 100 % (TLP521GB per parts list) or 50 % (unbinned PC817), the **bench LED, and so the e-match, must carry 12–25 mA** for the lamp to light. The station's lamp, not the no-fire current, would set the sense current. | Make the opto drive a high-impedance input: a high-efficiency LED at 1–2 mA (R_D_CONT ~4.7–10 k) and `R_CONT_PU` removed or ≥ 47 k, or a small transistor at the station. Then pick `R_CONT` for ~1–2 mA once O-1 is known. Resolve the part conflict (§3) because CTR sets this. | A (CTR, V<sub>F</sub>) |
| M-12 | Major | `R_D_FIRE1`/`D_FIRE1` on `PYRO_FIRE_OUT` | 1 k + LED from `PYRO_FIRE_OUT` to GND. | Fine today. With any continuity source that crosses K2 (B-2 fix), an **open match** leaves this LED chain as a path to ground. The opto conducts and the lamp reads "good" with no match: a sneak path. | Drive the FIRING lamp from `FIRE_LINE` on the bench (the K2 coil command, still not firmware), or recompute with `R_D_FIRE` large enough that it cannot light the opto. | V (topology) |
| M-13 | Major | Station `LS1` (MLT-8530), `Q_BUZZ1` | `LS1.1 = +12V_STN`, `LS1.2 = BUZZ_DRV` switched by a DC gate. | Vendor listings describe the MLT-8530 as an **externally driven electromagnetic transducer, ~3.6 V**. A 12 V DC drive gives a click, not a tone, and likely overcurrents both the coil and the NTS4001N. The "audible ARMED warning" would not work. | Use a **12 V self-drive (active) buzzer**, ideally panel-mount on terminals. Keep the gate divider and flyback. | A — MLT-8530 datasheet not retrieved; NTS4001N V<sub>GS(max)</sub> and I<sub>D</sub> still unverified |
| M-14 | Major (path B) | `U_AMP1`, `U_5V1`, `+5V_AMP`, `AMP_REF` | `AMP_REF` members: `R_BYP4.1, U_AMP1.5` only. `+5V_AMP` has no capacitor. | Path B as drawn is incoherent: REF floats (AD620 REF must be driven from a low-impedance source), `U_5V` has no output capacitor (M-3 applies), and a 5 V-supplied AD620 output can exceed the 3.3 V ADS1220 input range. A 3.3 V-excited bridge (CM ≈ 1.65 V) may also sit below the AD620's single-supply input range. | Add a buffered REF (divider + op-amp, or AD620 REF from a reference ~1.25 V), U_5V input/output caps, and output clamping or an attenuator into AIN0. Or drop path B and keep the DIP socket only if someone will actually populate it. | V (netlist) / A (AD620 CM and ADS1220 abs max, datasheets not fetched) |
| m-1 | Minor | Bench ERC | `power_pin_not_driven` at `U_3V3.3`. | ERC does not propagate a source through F2. A real issue only because B-3 also blocks power. | `PWR_FLAG` on `+12V_LOGGER`. | V |
| m-2 | Minor | `THRUST_DIFF_P/N` | 2 × `isolated_pin_label` warnings (bench); pass-through to `J_DAQ` (station). | Documented as O-19; the warning is justified, but path 2 does not exist. | Keep the warnings and record the justification, or remove the labels and mark J_UMB 8/9 reserved until O-19 closes. | V |
| m-3 | Minor | `J_DAQ1.3` = bench `GND` | Station comment: GND and GNDREF are "never joined". | A USB DAQ on the same laptop bridges GND to GNDREF and defeats the isolation barrier. | Isolate path 2 at the station as well, or label J_DAQ "battery-powered / isolated instruments only". | J |
| m-4 | Minor | `Q_BUZZ1` pins | Netlist pin numbers are `G`, `D`, `S`. | Standard SOT-23 footprints use pads 1/2/3, so footprint mapping will fail at Gate 3. | Use a numbered variant (e.g. `Q_NMOS_GSD`) matched to the NTS4001N pinout. | V |
| m-5 | Major at Gate 3 | K1–K4 pin mapping (O-3) | Symbol pins `A1/A2/11/12/14`. | For K3, an NO/NC swap at footprint assignment **inverts the shunt** (and with B-1, the low side). It is the single most safety-critical footprint on the board. | Map against the SRD datasheet drawing; verify on the bare board with a meter, relay de-energized, before any population of the pyro path. | A |
| m-6 | Minor | `RS485_DE` (IO14) | No pull-down; firmware has no RS-485 code at all. | DE floats or follows IO14's boot state, so the bench driver state is undefined and path 3 has no firmware. | 10 k pull-down on `RS485_DE`; add the UART2 TX to firmware. | V (netlist, firmware grep) / A (IO14 boot behaviour) |
| m-7 | Minor | RS-485, umbilical signals | No fail-safe bias; no TVS on any umbilical line. | With the bench driver off, a terminated idle bus gives an undefined RO. The 20 m cable sits next to a motor. Relay coils with flybacks are inherently robust receivers; the RS-485 pair and sense lines are not. | Bias resistors at the station; SM712-class TVS on A/B; small TVS or RC on `PYRO_CONT_SENSE` and `VBAT_SENSE`. | A |
| m-8 | Minor | `VBAT_SENSE` → `J_VM1` | 47 k/10 k gives 2.1 V at 12 V, 8.2 kΩ source. | A "voltmeter module" will display 2.1, not 12, and two-wire self-powered modules cannot run from 2.1 V. The ≥ 12 V pre-test check would be misread. | Choose the module first; scale to match (×5.7) or send the protected unscaled rail through a series resistor. | A (module unknown) |
| m-9 | Minor | `J_UMB1.12` both boards | Shield tied to GND at bench **and** station; bench comment says "single-point to bench ground". | Comment contradicts the netlist. | Decide; float the station end or tie it through an RC. | V |
| m-10 | Minor | ADC inputs, `J_LC1` | No RC/EMI filter on AIN0/AIN1, no ESD, no shield pin on a cabled bridge. | Measurement integrity next to the motor and the fire current. | Differential plus common-mode RC at AIN0/AIN1, 5th pin for the shield, star ground: the fire return (after B-1) must not share copper with AVSS. | J |
| m-11 | Minor | 1 k LED resistors, both boards | (12 − 2)²/1 k = 0.10 W; 0.15 W at 14.4 V. | At the limit of 0603. | 0805/1206, or 2.2 k. | A (footprint not assigned) |
| m-12 | Note (J) | K2 contacts | — | A K2 contact welded by a previous shorted match fires on ARM. | Procedure: ARM with the plug **out**, confirm FIRING lamp dark, disarm, then insert the plug. | J |
| m-13 | Note (J) | `D_K1/D_K3` flybacks | Plain diode across coil. | Lengthens K3 release, so the shunt recloses more slowly on disarm. Release is 8 ms max without a diode (SRD datasheet). | Acceptable for a manual system; a zener in series speeds release if wanted. | J |

## 2. Polarity sweep (acceptance criterion 2), by pin function

| Part | Pin function → net | Result |
|---|---|---|
| D_RP1 (SS24) | K → `+12V_FUSED`, A → `+12V_PROT` | **Reversed (B-3)** |
| D_K1, D_K2, D_K3 | K → coil + (`ARM_LINE`/`FIRE_LINE`), A → GND | Correct |
| D_K4 | K → `+12V_PROT` (= K4.A1), A → `ESTOP_LOOP` (= K4.A2) | Correct |
| D_BUZZ1 | K → `+12V_STN`, A → `BUZZ_DRV` | Correct |
| D_ESD1/2 | bidirectional TVS | Polarity not applicable |
| All 7 LEDs | K → GND / `PYRO_CONT_SENSE`, A → resistor | Correct |
| LS1 | + → `+12V_STN` | Correct (part is wrong, M-13) |
| U_ISO1/U_ISO2 (6N137) | A/C/VCC/VE/GND/VO consistent | Electrically legal, **logically inverted (M-2)** |
| U_CONT1 (PC817) | Symbol exports **no pin functions**, so this cannot be verified from the netlist. Assuming 1 A / 2 K / 3 E / 4 C: LED A on `CONT_LED_A`, C on `PYRO_CONT_SENSE`, E on GND. | A |
| Relays | Coils unpolarised; contact NO/NC mapping open (m-5) | A |
| C1, C2, C6, C10 (bulk) | Pin 1 on the positive rail in every case | OK if later changed to polarised parts |

## 3. Documentation conflicts found

- **U_CONT part:** PC817 in the schematic, TLP521GB-S in the parts list, 6N137 in the handoff. CTR sets M-11.
- README: regulation "LM78xx" vs AMS1117 in the schematic; architecture shows cable A carrying pyro and continuity, while the schematic sources fire current at the bench (O-18 unresolved in docs).
- OPERATIONS-MANUAL step 5 "press CONTINUITY": the button was removed (H-2). "Switch on station power": no switch is drawn.
- Title-block comment 3 names `fabrication/generate_schematics.py`; the generators are `hardware/tools/gen_*.py`. Generator `OUT` paths are absolute Windows paths, so regeneration only works on one machine.

## 4. Corrections to the cross-model handoff

| Handoff claim | Finding |
|---|---|
| "Sense current crosses the initiator permanently ... live whenever the bench is powered" (also 6 Nov audit, H-2 follow-on) | **False.** Nothing sources it (B-2). The real problem is the opposite: no continuity sensing works at all, and the firing loop is open (B-1). |
| "Continuity lamp now lit = good match" (verified) | True for the station logic only. Bench side cannot produce the "good" state. |
| Continuity opto is a 6N137 | Schematic says PC817; parts list says TLP521GB-S. |
| DevKitC header "does not expose nine of the drawn pins" | Espressif's J2/J3 pinout exposes every module signal pin, including the flash pins and IO16/17. The real mismatch is the 5 V pin, the onboard LDO/USB/EN network, and M-6. |
| M-3 fixed, 8.18 mA | Nominal only; ≈ I<sub>FT(max)</sub> worst case, and the opto is wired inverting (M-2). |
| No-connect flags: 28 bench, 15 station | Netlist has 27 and 13 no-connect pins. Minor, probably counting flags vs pins. |
| D_RP reversed, ERC error, THRUST_DIFF unsourced, missing station caps | All confirmed. |

## 5. Acceptance criteria

| # | Criterion | Status |
|---|---|---|
| 1 | ERC 0 errors, warnings justified | **Not met** (m-1; m-2 justifiable) |
| 2 | Every diode verified by pin function | **Not met** (B-3); U_CONT not verifiable from netlist |
| 3 | Every power_in rail sourced | **Not met** (`+12V_LOGGER`; `+12V_STN` source is undefined, M-10) |
| 4 | Regulator capacitance per datasheet | **Not met** (M-3, M-4, M-14) |
| 5 | No firmware semiconductor in arm/fire/E-STOP; de-energized = safe | No firmware-controlled semiconductor on the path, **verified**: no logger net touches a coil or pyro net, and coil nets contain only relays, flybacks and J_UMB. De-energized states: K1 NO, K2 NO, K3 NC, K4 NO, verified as drawn. **But** the fire loop is open (B-1), E-STOP does not restore the shunt (M-7), and single cable shorts defeat E-STOP or merge ARM/FIRE (M-8, M-9). *Assessment only, not a sign-off.* |
| 6 | Every value verified or assumed | **Not met** — pyro and analog values blocked on O-1/O-2 |

## 6. Reliability and repairability recommendations (design goal)

1. **Field-replaceable protection:** blade fuse holders for F1/F2 (automotive blades, available everywhere) plus a crowbar diode, rather than an SMD diode that fails silently.
2. **Swappable regulation:** TO-220 7805-footprint 5 V stage (linear or pin-compatible switching drop-in), then one 3.3 V LDO. No SOT-223 doing an 8.7 V drop.
3. **Pluggable terminal blocks** for battery, match, load cell, panel controls and umbilical, each **keyed or a different pitch**, so the match cannot plug into the load-cell header.
4. **Test points on every safety net:** `ARM_LINE`, `FIRE_LINE`, `ESTOP_LOOP`, `ARM_BUS`, `PYRO_FIRE_OUT`, `PYRO_MATCH_P/N`, each rail. Bring-up uses an inert dummy match (power resistor plus lamp).
5. **0805 minimum, THT for relays and connectors**, sockets for DevKitC and AD620 (already planned). Silk the relay state on the board ("K3 NC = SHUNT").
6. Fix the DevKitC symbol so the schematic is the build: what is drawn is what you probe.

## 7. Open questions for the review owner

1. Adopt the K3-as-low-side topology (B-1) and the armed-state continuity scheme (B-2)? Both are pyro decisions.
2. Station supply: separate battery, or bench power up the umbilical (M-10)? This decides the conductor allocation and the ARM/FIRE pin separation (M-9).
3. E-STOP: second contact block (M-7); high-side or low-side loop (M-8)?
4. Reverse-polarity approach for the fire path (M-1).
5. Keep path B (AD620) in Rev A, or defer?

## 8. Not checked

Layout/DRC (none exists); footprints (unassigned); ADS1220 pinout re-verified only against my reading of the TI datasheet, not fetched; AD620 input range, ADS1220 abs max, NTS4001N, PC817/TLP521 CTR, 6N137 V<sub>F(max)</sub> for the chosen vendor, MLT-8530 datasheet; firmware (not compiled); repo tools not executed; all O-1/O-2-dependent values.

### Sources
- [AMS1117 datasheet (Advanced Monolithic Systems)](https://files.waveshare.com/upload/b/b8/AMS1117-datasheet.pdf)
- [Songle SRD relay datasheet (LCSC)](https://atta.szlcsc.com/upload/public/pdf/source/231023/SRD.pdf-ba91e5635ca2ace5c4c74973894313b7.pdf)
- [Everlight 6N137 datasheet (Mouser)](https://www.mouser.com/datasheet/2/143/6N137_EL26XX%20SERIES-709083.pdf)
- [ESP32-DevKitC V4 user guide (Espressif)](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html)
- [SS24 listing (rlocman)](https://www.rlocman.es/datasheet/data.html?di=99386)
- [MLT-8530 listing (electroncomponents)](https://www.electroncomponents.com/mlt-8530-electromagnetic-passive-buzzer-3v-5v-smd), [CUI CMT-8530S equivalent (DigiKey)](https://www.digikey.in/en/products/detail/same-sky-formerly-cui-devices/CMT-8530S-SMT-TR/6012407)
- [AD620 summary (adom wiki, secondary)](https://wiki.adom.inc/ray/ad620)
