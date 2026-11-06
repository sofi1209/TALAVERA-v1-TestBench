# TALAVERA v1 — Requirements (Gate 0 output)

Status: **Gate 0 complete.** Gate 1 awaiting approval.

Reference design: *Manual de operaciones: WIRIKUTA 1.1 Banco de Pruebas*, Ignitia Rocket Lab, August 2025.

Evidence labels used throughout: **V** = verified from the manual or a datasheet, with page.
**A** = assumed, needs confirmation. **TBD** = not yet known.

---

## 1. Goal

Replace the Wirikuta 1.1 electronics with a simpler, more robust board set. Remove the microcontroller
from every function the test's safety depends on. Keep only the functions the test needs.

---

## 2. Function list

### 2.1 Bench board

| Function | Why the test needs it |
|---|---|
| Reverse-polarity protection and fuse on the 12 V input | The battery is connected by hand in a field, often in a hurry. A reversed lead must not destroy the board or energize anything. |
| Master power cut (e-stop / dead-man) | Removes all energy from a distance. Carries over the Wirikuta concept (**V** p. 20), hardware-only. |
| Igniter shunt, normally closed | Safe state is a shorted match. Addresses the 20 m pickup loop. **New** — absent from Wirikuta. |
| Arming interrupt, physical, in series | A visible break an operator can confirm by eye before approaching. Same role the MG995 servo played (**V** p. 20), with no actuator. |
| Firing switch, in series after arming | The only element that energizes the match. |
| Load cell excitation and instrumentation amplifier | The measurement is the entire point of the test. |
| Differential line driver for the thrust signal | Single-ended analog over 20 m beside a firing line will not survive. Also the fix for the noise floor that currently defeats a 1-grain motor (**V** p. 28). |
| LED beacon drive | Long-range visual state confirmation (**V** p. 24). Must work with the station absent or dead. |
| Battery voltage sense to the station | The pre-test check requires at least 12 V (**V** p. 12), read remotely rather than by walking up. |
| ESD / surge protection on every umbilical conductor | 20–40 m of exposed field cable. |
| Test points on every rail and every safety signal | Gate 2 requirement. |
| Thrust logger | Local record of the test. **ESP32-DevKitC V4 (ESP32-WROOM-32D)**, constrained to zero authority with its radios stopped — see [SAFETY.md](SAFETY.md) §4. |
| On-board microSD socket | Primary data record. Embedded socket with card-detect, not a breakout module — one fewer set of headers to vibrate loose. Ports the IGNIS-v5 `Storage.SchDoc` topology. |
| Isolated RS-485 driver *(secondary path, built in rev A — D-048)* | Live numeric data to a laptop at the station. Galvanically isolated so a laptop is never tied to bench ground during a firing. **Outward data only, never a command path.** |

### 2.2 Control station board

| Function | Why |
|---|---|
| Power switch | — |
| E-STOP, mushroom head | Breaks bench power independently of everything else. |
| ARM key switch | Hardware arming with a removable key as positive control. |
| FIRE momentary button, in series with ARM | Two deliberate actions, both mechanical. |
| Igniter continuity check, current-limited below no-fire | Confirms the match is connected *before* arming, without firing it. **New** — absent from Wirikuta. |
| Armed / continuity / power indicator lamps | Local state, independent of the bench beacon. |
| Differential receiver and DAQ output | Hands the thrust signal to a recorder. |
| Battery voltmeter | Displays bench battery voltage. |

### 2.3 Removed, with the trade-off stated

| Removed | Trade-off accepted |
|---|---|
| Arduino, NRF24L01, nine-state machine | Eliminates the pin-5 collision and `igniteMotor()` defect class. Loses remote arming convenience — replaced by the umbilical. |
| MG995 servo as arming actuator | A servo is a motor needing PWM timing. Replaced by a hand-inserted arming plug. **Cost: an operator must walk to the bench to arm** — which is how pyrotechnics are normally handled anyway. |
| On-bench state machine, commands, RF diagnostics | Logger records whenever powered. **Cost: no automated pre-flight self-test.** Those checks move to hardware the operator can see: continuity lamp, battery voltmeter, beacon. |
| Second bench PCB and the JST-XH interconnect | One fewer connector to vibrate loose. |

---

## 3. Settled parameters

| Parameter | Value | Decision |
|---|---|---|
| Arm/fire path | Wired umbilical, no MCU | D-006 |
| Umbilical length | 20 m, extensible to 40 m+ | D-011 |
| Cables | Two: dedicated pyro pair + control/analog multicore | D-016 |
| Arming | Bench arming plug + station key switch | D-013 |
| Igniter channels | One | D-015 |
| Boards | Two: bench + station | D-014 |
| Data logging | On the bench board, isolated passenger | D-012 |
| Igniter safe state | Shorted (normally-closed contact) | D-008 |
| Thrust signal | Differential off the bench | D-010 |
| Firing pair | 16 AWG | D-009 |
| Logger processor | ESP32-DevKitC V4 (WROOM-32D), socketed, radios stopped | D-028, D-029, D-042 |
| Converter | **ADS1220IPWR** — 24-bit, SPI, 2 kSPS, integrated PGA. AD620 laid out bypassable, hand-populated. | D-046 |
| Storage | On-board microSD socket `THD2528-11SD-GF`, with `SD_DETECT` | D-037, D-041 |
| Logger power | Upstream of the master kill relay, own fuse and switch | D-047 |
| Secondary telemetry | Isolated RS-485 over cable B, USB-C on the station board, built in rev A | D-038, D-048 |
| Fabrication | JLCPCB, 2-layer, assembled. Every populated part must be LCSC-stocked. | D-049 |
| Review owner | **Emilio Guadarrama** | D-050 |

---

## 4. Environment

**All rows assumed.** Confirm or override before Gate 3 component selection.

| Parameter | Assumed value | Note |
|---|---|---|
| Operating temperature | 0 to +55 °C ambient | Specify −40…+85 °C parts wherever free |
| Radiant heat at the board | Unknown | Needs enclosure-to-nozzle distance |
| Vibration | 10 g RMS random, 20–2000 Hz, short duration | Real driver is a few seconds of burn |
| Shock | 50 g, 11 ms half-sine | Transport and handling are the likely killer |
| Humidity | 0–95 % non-condensing; outdoor dew and dust | — |
| EMI | E-match firing transient, nearby RF | — |
| Enclosure | 3D-printed, removable | **V** manual p. 18 |

---

## 5. Verified reference facts

Page numbers are the Wirikuta manual's own footers.

| Fact | Page |
|---|---|
| Load cell rated 5,000 N; 40×40 Bosch extrusion; 30 × 40 × 98 cm | 4 |
| 12 V 2.6 Ah battery; Arduino logic; NRF24L01; SD module; LED array | 5 |
| Load cell → AD620 → ADS1115 → Arduino | 19 |
| IRLZ44N ×2 for LEDs, IRF540 for igniter | 19 |
| LM7809 + LM7805 linear regulators from 12 V | 19 |
| Two bench PCBs joined by JST-XH | 19 |
| MG995 servo physically actuates a toggle in the igniter line | 20 |
| Dead-man button + 12 V relay, independent of RF, 5–10 m rope | 15, 20 |
| Nine-state machine; IgnitionWait 30 s timeout; ArmedWait 10 s countdown | 21–22 |
| Six control-station commands; pull-up buttons with debounce caps; LCD | 25–26 |
| Noise floor defeats a 1-grain motor even after Kalman filtering | 28 |
| NAR/TRA standoff by total impulse; 25 % reduction permitted for static tests | 7–8 |
| Diagnostics rows must be hand-deleted from the CSV before the Kalman script parses it | 27 |

---

## 6. Defects found in the existing firmware (manual Annex C)

1. **Pin 5 double-allocated.** `ServoSwitch.h` defines `SERVO_PIN 5`; `SDLogger.h` defines
   `BUTTON_PIN 5`, and `SDLogger.cpp` calls `pinMode(BUTTON_PIN, INPUT)`. The servo that gates the
   igniter line shares a pin with an unrelated input. Whichever `pinMode` runs last wins.
2. **`igniteMotor()` never records firing.** The line reads `currentIgniterState == true;` — a
   comparison, not an assignment — so `getMosfetState()` returns `false` while the igniter is energized.

Both are cited as rationale for hardware-defined logic, not as criticism of the Wirikuta team. They are
the ordinary cost of putting safety logic in software.

---

## 7. Open items

Ordered by what they block.

Renumbered 6 November 2026. Closed items are listed separately below rather than struck through in place.

### Blocking Gate 2 — the schematic cannot be drawn without these

| # | Item | Why it blocks |
|---|---|---|
| **O-1** | **E-match make and part, no-fire current, all-fire current, resistance** | Sets `R_CONT`, the fuse rating, all four relay contact ratings and the `PYRO` trace width. The entire pyro section stays `TBD` without it, and no safety margin can be claimed. |
| **O-2** | **Load cell make and model, bridge resistance, mV/V, rated excitation** | Sets the ADS1220 PGA gain, decides whether the PGA common-mode restriction bites, and decides whether a ratiometric reference is possible. The whole analog chain depends on it. |

Both are data only Ignitia can supply. Neither will be guessed.

### Needed during Gate 2 and 3, derivable or minor

| # | Item | Note |
|---|---|---|
| O-3 | Relay **contact rating** confirmation for `SRD-12VDC-SL-C` | Part chosen (D-055); only the rating against the e-match current is open. Depends on O-1. |
| O-4 | ARM key switch, E-STOP mushroom, FIRE panel button | All three panel-mount, not PCB parts, so exempt from the LCSC constraint. |
| O-5 | Arming plug / removable shorting link part | Must be keyed and obviously absent at a glance. |
| O-6 | **Isolator part** for the station ground barrier, plus the USB-UART bridge | RS-485 transceiver chosen (`SP3485EN`, D-056). Candidates for the barrier: 6N137 high-speed optocoupler, or a digital isolator. **Not yet verified for price or stock** — the slow TLP521/PC817 already in stock may not carry 115200 baud reliably. |
| O-7 | **ADS1220 input common-mode range with PGA enabled at 3.3 V**, checked against the real load cell | Narrowed from the old gain-range item. The PGA can be bypassed for rail-to-rail input at the cost of gain. Depends on O-2. |
| O-8 | Board size target for each board | Outlines are placeholders (D-023). Layer count settled at 2; rev A is a bare board, hand-assembled (D-051). |
| O-9 | Copper weight | The `PYRO` 2.00 mm track width assumes 1 oz. Confirm before trusting it. |
| O-16 | **Three footprints to create or import**: `SRD-12VDC-SL-C` relay, `THD2528-11SD-GF` microSD, `TYPE-C-31-M-12` USB-C | Gate 4, not Gate 2 — KiCad assigns footprints after the schematic. All three already exist in the Altium IGNIS library; SnapMagic also exports KiCad. All symbols are already in KiCad 10 stock libraries. See [SCHEMATIC-PLAN.md](SCHEMATIC-PLAN.md). |
| O-17 | Current budget for the 12 V input fuse | Four relay coils at ~30 mA each plus the logger are known; the **beacon LED current is not**, and it dominates. Design choice, not missing data. |
| O-15 | **ADS1220 TSSOP-16 is the hardest part to hand-solder** on the board (0.65 mm pitch) | Manageable with flux and a fine tip, but it is the one part where a breakout module is a fallback if hand assembly proves painful. Decide at Gate 4. |
| O-10 | Which ADS1115 symptom was actually seen — lockup, noise, drift, clipping or speed | Informational now that D-046 is decided, but it would confirm the diagnosis or point at a layout problem the new part will not fix. |
| O-11 | Largest motor class intended (total impulse) | Standoff planning and connector sizing. |
| O-12 | Environment figures confirmed or overridden | §4 is still entirely assumed. Gate 3 part selection. |
| O-13 | KiCad sources for the two Wirikuta reference boards | Comparison only. Not blocking. |
| O-14 | Enclosure and panel for the station board | Gate 4. Drives the panel-control footprints. |

### Closed

| Item | Resolution | Decision |
|---|---|---|
| Review owner | **Emilio Guadarrama** | D-050 |
| Logger power domain | Upstream of the master kill relay, own fuse and switch | D-047 |
| ADC selection | **ADS1220IPWR**, SPI, integrated PGA; AD620 laid out bypassable | D-046 |
| Secondary telemetry scope | Built into rev A | D-048 |
| Fab house, layers, assembly | JLCPCB, 2-layer, assembled | D-049 |
| Logger mounting | Socketed DevKitC on `PPTC191LFBN-RC` plus a hold-down, per MAGNIS v1 | D-042 |
| microSD socket | **THD2528-11SD-GF** (LCSC C283232) | D-041 |
| GitHub organisation | `sofi1209` | D-033 |

---

## 9. Component selection policy (D-052)

> **Cheap, with reliable sourcing, in hand-solderable packages.**
>
> This ranks **above** elegance and above marginal performance gains. A part that is 10 % better and
> three times the price, or that has 40 units in stock at one distributor, loses.

Applied in order:

1. **Buyable from LCSC or UNIT Electronics**, preferably both. Deep stock, not a handful of units, and
   not a "pre-order" listing.
2. **Cheap.** Where two parts both do the job, the cheaper one wins unless the difference is a safety
   margin.
3. **Hand-solderable.** Rev A is a bare board, hand-assembled (D-051). Through-hole is welcome;
   0805 beats 0603; fine-pitch QFN is avoided.
4. **One part number serving several positions** beats several similar parts — fewer BOM lines, and
   spares are interchangeable.

### What the policy has already changed

| Was | Now | Saving |
|---|---|---|
| ADM2582E isolated RS-485, ~$10 | `SP3485EN-L/TR`, ~$0.14–0.27, isolation moved to the station and powered from USB | ~$10 and an isolated DC-DC |
| Four separately specified relays | One `SRD-12VDC-SL-C` SPDT part ×4, ~$0.23 each | Three BOM lines |
| AD620 populated, ~$6–8 | Depopulated by default in a DIP-8 socket; ADS1220's PGA does the job | ~$7 per board |
| Keystone 5015 test points | Bare pads | Small, but free |

**Resistors stay 0603** (D-058). An earlier draft moved them to 0805 for hand-solderability, which was
wrong: Ignitia already owns 0603 reels from the IGNIS builds, and buying new 0805 reels would have added
cost for marginal benefit — the opposite of what this policy says. Capacitors were already 0805.

### Where the policy does *not* apply

Safety-critical ratings are not negotiable on price. Specifically: the relay contact rating, the fuse
rating, the shunt relay being genuinely normally-closed, and the continuity-sense resistor holding
current below the e-match no-fire figure. If the cheap part cannot meet the rating, it loses.

---

## 8. Definition of done

- ERC and DRC clean, with every remaining item listed and justified.
- Gerbers, drill files, BOM and centroid ready for review.
- Each value in the design labelled verified or assumed. No invented ratings.
- Review owner **Emilio Guadarrama** has signed off every row in [SAFETY.md](SAFETY.md) §8.
