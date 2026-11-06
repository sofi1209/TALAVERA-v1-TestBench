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

| # | Item | Blocks |
|---|---|---|
| ~~1~~ | ~~Review owner's name~~ — resolved: **Emilio Guadarrama** (D-050) | closed |
| ~~2~~ | ~~Logger power domain~~ — resolved: **upstream of the master kill relay**, own fuse and switch (D-047) | closed |
| 3 | E-match make and part, **no-fire current**, all-fire current, resistance | Every safety margin claim, Gate 3 |
| 4 | Load cell make and model, bridge resistance, mV/V, rated excitation | Analog chain design, Gate 2 |
| 5 | Largest motor class intended (total impulse) | Standoff planning, connector sizing |
| 6 | KiCad sources for the two Wirikuta reference boards | Reuse and comparison |
| 7 | Environment figures confirmed or overridden | Gate 3 part selection |
| 8 | Fab house, layer count, assembly yes/no, board size target | Gate 4 and Gate 6 |
| ~~9~~ | ~~GitHub organisation / username~~ — resolved: `sofi1209` | closed |
| 10 | **Logger mounting: socketed DevKitC vs. soldered WROOM-32D module** | Gate 2 and Gate 4; vibration robustness |
| 11 | Amplifier gain must keep its output inside the chosen converter's input range at 3.3 V | Gate 2 analog chain. **Disappears if an integrated-PGA converter is chosen** — see item 12. |
| 12 | **ADC selection** — ADS1115 reopened, primary criterion is moving off I²C | Gate 2 and Gate 3. See [ADC-TRADE-STUDY.md](ADC-TRADE-STUDY.md). |
| 13 | **Which ADS1115 symptom was actually seen** — lockup, noise, drift, clipping or speed | Confirms or redirects item 12 |
| ~~14~~ | ~~microSD socket part number~~ — resolved: **THD2528-11SD-GF** (C283232) | closed |
| ~~10~~ | ~~Logger mounting~~ — resolved: socketed DevKitC on PPTC191LFBN-RC + hold-down, per MAGNIS v1 (D-042) | closed |
| 16 | **Relay selection** — 4 relays, 12 V coil; K3 must be normally-closed | Gate 2 and Gate 3. No candidate chosen; contact rating depends on the e-match current. |
| 17 | **ARM key switch, E-STOP, and FIRE panel button** part selection | Gate 2. All three are panel-mount, not PCB parts. |
| 18 | Arming plug / removable shorting link part | Gate 2. Must be keyed and obviously absent at a glance. |
| 19 | Enclosure and panel for the station board | Gate 4. Drives the panel-control footprints. |
| 15 | Whether the RS-485/USB secondary path is built in rev A or left as footprints | Gate 2 scope |

---

## 8. Definition of done

- ERC and DRC clean, with every remaining item listed and justified.
- Gerbers, drill files, BOM and centroid ready for review.
- Each value in the design labelled verified or assumed. No invented ratings.
- Review owner **Emilio Guadarrama** has signed off every row in [SAFETY.md](SAFETY.md) §8.
