# Operations Manual — TALAVERA Static Test Bench

**PRELIMINARY — REVISION A — 6 November 2026**

**Ignitia Rocket Lab** — Tecnológico de Monterrey, Campus Guadalajara

---

> # ⛔ NOT FOR USE
>
> **This manual describes hardware that does not exist yet.**
>
> No board has been fabricated. No circuit has been approved. No output has been energized.
> The procedures below are the *design intent* against which the hardware will be built and
> verified — they are written now so that the design can be checked against how the bench will
> actually be operated.
>
> This document becomes operational only when:
> 1. The named review owner has signed every row of [SAFETY.md](SAFETY.md) §8, and
> 2. The bring-up plan in [../test/BRINGUP-PLAN.md](../test/BRINGUP-PLAN.md) has been completed and recorded.
>
> **A Spanish-language field edition must be produced before any live operation.** Operators
> reading emergency procedures under time pressure must read them in their working language.
> This English edition exists for design review.

---

## Document control

| | |
|---|---|
| Document | Operations Manual — TALAVERA Static Test Bench |
| Revision | A (preliminary) |
| Date | 6 November 2026 |
| Author | Sofia Pacheco Leon — Ignitia Rocket Lab, Avionics & Electronics |
| Co-author | Claude (Anthropic) |
| Team leader | TBD |
| Division leader | TBD |
| Faculty advisor | TBD |
| Repository | **https://github.com/sofi1209/TALAVERA-v1-TestBench** |
| Supersedes | Nothing. Wirikuta 1.1 remains the operational bench until TALAVERA is accepted. |
| Predecessor document | *Manual de operaciones: WIRIKUTA 1.1 Banco de Pruebas*, August 2025 |
| Review owner | **Emilio Guadarrama** — Division Leader & Vice President |

The authoritative version of this manual is the copy in the repository. Printed copies are
uncontrolled and must carry the revision letter and date.

---

## 1. Glossary

Carried forward from the Wirikuta manual so that terminology stays consistent across benches.

| Term | Meaning |
|---|---|
| **TALAVERA** | The test bench electronics described here: a bench board on the test stand and a control station board at the operator position, joined by a wired umbilical. |
| **Users** | Any team member whose active participation is needed to run a static test: bench operators, ignition officer, telemetry monitors, safety specialists, data engineers, protocol leads. |
| **Spectators** | People present at the test site who are not part of test operations. |
| **Operators** | People who physically interact with the bench, meaning anyone approaching closer than 2 m, before or after remote ignition. |
| **NAR / Tripoli** | National Association of Rocketry and Tripoli Rocketry Association. Their safety codes set the standoff distances used here. |
| **Arming plug** | A removable connector at the bench that physically completes the firing circuit. Withdrawn, the bench cannot fire. |
| **Shunt** | A normally-closed relay contact that shorts the two e-match conductors together while the system is disarmed. |

---

## 2. System description

TALAVERA replaces the Wirikuta 1.1 electronics. The functional difference is that **no
microcontroller takes part in arming, firing or emergency stop.** Those paths are switches, relay
contacts and resistors.

### 2.1 Parts of the system

| Part | Location | Contains |
|---|---|---|
| **Bench board** | On the test stand, in a removable enclosure | Input protection, master kill relay, arm relay, fire relay, arming plug receptacle, normally-closed shunt, load cell excitation and amplifier, differential line driver, LED beacon drive, thrust logger |
| **Control station board** | At the operator position, 20 m away | Power switch, E-STOP, ARM key switch, FIRE button, continuity check, indicator lamps, differential receiver, DAQ output, battery voltmeter |
| **Umbilical, cable A** | Between them | Pyrotechnic pair only. 2 × 16 AWG, shielded. |
| **Umbilical, cable B** | Between them | Control and analog: arm, fire, e-stop, thrust pair, battery sense, return. Shielded multicore. |

Cable A and cable B are **separate cables and must stay separated along the run.** Firing current
flows in cable A at the same instant the thrust measurement matters most.

### 2.2 The firing chain

```
STATION (20 m away)                    BENCH

[ARM key] ──── arm line ─────────►  [arm relay]
                                          │
[FIRE button] ── fire line ───────►  [fire relay]
                                          │
                                   [ARMING PLUG]  ◄── inserted by hand, last
                                          │
                                     ╔════╧════╗
                                     ║ E-MATCH ║
                                     ╚════╤════╝
                                          │
                              [shunt relay, normally CLOSED]
                                    shorts the match
                                    until ARM is turned
```

Three independent things must all be true for current to reach the match: the key is turned, the
button is held, and someone walked to the bench and inserted the arming plug. With any one of them
absent, the match is **shorted to itself**, not merely disconnected.

### 2.3 Safe states

Every safe state is the de-energized state. A dead battery, a cut umbilical and a pressed E-STOP all
produce the same result.

| Output | Safe state | What you observe |
|---|---|---|
| Igniter | `PYRO_SHUNTED` | ARMED lamp dark. **The continuity lamp tells you nothing** — it cannot light in any state (hazard H11). Shunt state is confirmed with a meter across the match terminals, plug withdrawn |
| Arm path | `DISARMED` | ARMED lamp dark, key removed, plug withdrawn |
| Fire path | `FIRE_OPEN` | Button released |
| Bench power | `BENCH_UNPOWERED` | Beacon dark |
| Beacon | `BEACON_DARK` | No light at the bench |
| Logger | `LOGGER_IDLE` | Logger indicator off |

---

## 3. Personal protective equipment

Unchanged from Wirikuta practice.

**All spectators and users who are not operators, minimum:**
- Safety glasses
- Safety vest

**Operators — anyone approaching within 2 m of the bench, mandatory:**
- Safety glasses
- Safety vest
- Thermal gloves
- Hard hat
- Safety boots

Compliance is mandatory during assembly, operation and teardown.

---

## 4. Standoff distance

Determine expected **total impulse** by simulation before every test, then read the distance from
this table. Total impulse sets the distance, not peak thrust.

| Motor class | Total impulse (N·s) | NAR personnel minimum | ×0.75 static-test reduction |
|---|---|---|---|
| H or smaller | 0 – 320 | 30 m | 22.5 m |
| I | 320 – 640 | 30 m | 22.5 m |
| J | 640 – 1,280 | 30 m | 22.5 m |
| K | 1,280 – 2,560 | 60 m | 45 m |
| L | 2,560 – 5,120 | 90 m | 67.5 m |
| M | 5,120 – 10,240 | 150 m | 112.5 m |

> ### ⚠️ Standoff limitation of the 20 m configuration
>
> A 20 m umbilical gives roughly **15–17 m of actual standoff** once cable routing, sag and service
> loops are accounted for. **That clears no class in the table above.**
>
> This is a recorded and accepted deviation (decision D-007 / D-011), not an oversight. Anyone
> operating the bench must know it.
>
> The boards are electrically unchanged at 40 m — verified by calculation, see the README. Closing
> the gap is a cable purchase and nothing more. **Extending the umbilical to 40 m is strongly
> recommended before testing anything above the smallest motors.**

A mandatory confinement test — motor buried with only the nozzle exposed — precedes any bench test
of a new motor, as in Wirikuta practice.

---

## 5. Pre-test procedures

### 5.1 Site and installation

1. Choose open, level ground, free of obstacles, with firm footing.
2. Confirm the standoff distance from §4 can actually be achieved at this site.
3. Minimum installation area 3 m × 3 m for the stand and its guy cables.
4. Level the frame, then anchor it to ground with the steel guy cables and stakes.
5. Confirm no play or movement in the structure.
6. Route **cable A and cable B separately** from bench to station. Keep them apart along the run.
7. Delimit the safety area with tape or cones. Assign observation points.

### 5.2 Motor mounting

Unchanged from Wirikuta practice. In summary: confirm the motor passed its confinement test, inspect
the case, nozzle and mounting points, clean and align the guide rails, clamp the motor so the nozzle
is perpendicular to the ground, confirm no lateral play, confirm the motor is centred on the load
cell, and confirm nothing obstructs the nozzle exhaust. Photograph the final mounting. Obtain the
responsible operator's approval before proceeding.

### 5.3 Remote systems check

Run this **after installation and before loading the motor with propellant.** No e-match is connected
at this stage.

1. Confirm the arming plug is **withdrawn** and in the possession of the ignition officer.
2. Confirm battery voltage is at least 12 V, read on the station voltmeter.
3. Switch on station power. Confirm the bench beacon lights.
4. Press **E-STOP**. Confirm the beacon goes dark. Release and confirm it returns.
5. Turn the **ARM** key with the plug still withdrawn. Confirm the ARMED lamp lights and the beacon
   changes state. Return the key to disarmed.
6. Confirm the ARMED lamp goes dark.

Any failure here is corrected before final assembly. This check is performed from the station, not at
the bench.

---

## 6. Ignition procedure

> Steps 1–4 are performed **at the bench** by the ignition officer, with the system **disarmed**, the
> key **removed from the station**, and the arming plug **in the officer's pocket**.

1. Confirm at the station that the ARM key is removed and in the ignition officer's possession.
2. Approach the bench in full operator PPE.
3. Connect the e-match to the bench board. The shunt holds it shorted; this is the condition in which
   it is safe to handle.
4. Insert the **arming plug**. Withdraw to the station. This is the last action taken at the bench.
5. **SUSPENDED — DO NOT PERFORM, AND DO NOT RELY ON THE CONTINUITY LAMP.**

   > This step told you to press **CONTINUITY** and confirm the lamp indicated a connected match.
   > **There is no such button and there is no working check.** The button was removed on 6 November
   > because it shorted the sense line to ground and reported a good match whether or not one was
   > connected — a test that could not fail. The audits of 9 November then found that the sense circuit
   > has no source at all: `R_CONT` and the optocoupler sit in *parallel* with the match, nothing drives
   > them before arming, and the lamp can never light.
   >
   > The lamp therefore reads **"no match" permanently**. That is the safe direction, but it is not a
   > check, and this procedure must not pretend otherwise.
   >
   > **Until the reviewed pre-arm TEST function exists (decision D-B, blocked on open item O-1),
   > continuity is confirmed with a meter at the bench, with the arming plug WITHDRAWN**, by a method
   > the review owner specifies. Note that any continuity test must open the shunt, so the induced-energy
   > defence (hazard H2) is absent while the test is held: see hazard H10 in
   > [SAFETY.md](SAFETY.md).

   Proceed to step 6 only after confirming the arming plug is inserted and the key is removed.
6. Confirm the area is clear and that everyone is at or beyond the standoff distance from §4.
7. Confirm the logger is running.
8. Verbal countdown. Announce ignition.
9. Turn the **ARM** key. The ARMED lamp lights, the shunt releases and the beacon changes state.
10. Press and hold **FIRE**.
11. Observe the thrust trace on the DAQ. Release FIRE after the burn ends.
12. Return the ARM key to disarmed. Confirm the ARMED lamp goes dark and the shunt re-closes.

**Nobody approaches the bench during steps 5 through 12.**

---

## 7. Abort and emergency procedures

### 7.1 Abort before firing

Return the ARM key to disarmed. The shunt re-closes immediately and the match is shorted. There is no
countdown to interrupt and no software to abort — the abort *is* the key turning back.

### 7.2 Emergency stop

Press **E-STOP**. The master relay coil loses its circuit and drops out, removing power from the
bench. Confirm visually that the beacon is dark.

### 7.3 Loss of the umbilical

A cut or damaged umbilical de-energizes the arm and fire lines, which is the safe direction. The match
reverts to shorted.

1. Do not approach the bench.
2. Press **E-STOP** regardless.
3. Confirm the beacon is dark. If the beacon is **not** dark, treat the bench as live and continue to
   stay clear.
4. Wait at least 5 minutes.
5. Observe from a distance for smoke, heat or unusual sound.
6. Approach only with the safety officer's approval, in full PPE.
7. **Withdraw the arming plug before any other work.**
8. Record the event: time, symptoms, actions taken, diagnosis.

### 7.4 Failure to ignite

1. **Wait at least 5 minutes.** A hangfire is the most dangerous condition in this procedure.
2. Return the ARM key to disarmed and remove it. Press E-STOP.
3. Confirm the beacon is dark.
4. Approach in full PPE. **Withdraw the arming plug first.**
5. Then, and only then, inspect the match.

---

## 8. Post-test procedures

1. Wait at least 5 minutes after burn for cooling. Confirm no incandescent residue or smoke.
2. Return the ARM key to disarmed, remove it, press E-STOP, confirm the beacon is dark.
3. Approach in full PPE. **Withdraw the arming plug first.**
4. Stop the logger **deliberately with its own switch** so the data file closes cleanly. Do not rely
   on cutting power to end the recording.
5. Remove the motor with thermal gloves. Place it in a safe ventilated area.
6. Inspect the load cell, its wiring and connectors for damage. Record any anomaly.
7. Disconnect the battery. Remove the SD card.
8. Remove ground anchors and disassemble the structure.
9. Clear all residue from the site.
10. Complete the test report: date, time, ambient conditions, observations, preliminary results.

---

## 9. Data recovery

1. Remove the SD card from the bench board.
2. Copy the log file to a backup device **before opening or editing it**.
3. Verify the file is complete and uncorrupted.
4. Apply the post-test processing in [../analysis/kalman/](../analysis/kalman/) for offset correction,
   filtering and total-impulse integration.

> **Improvement over Wirikuta:** because the logger has no diagnostic routine and no state machine,
> the CSV contains thrust data only. The manual cell deletion previously required before the Kalman
> script would parse the file (Wirikuta manual p. 27) is no longer necessary.

---

## 10. Known limitations

| # | Limitation | Status |
|---|---|---|
| 1 | Hardware does not exist. Nothing is approved or built. | Gates 1–7 outstanding |
| 2 | 20 m umbilical gives 15–17 m standoff, clearing no NAR/TRA class | Accepted deviation D-007. Extend to 40 m to close. |
| 3 | No automated pre-flight self-test | Deliberate. Replaced by the §5.3 manual remote check. |
| 4 | Arming requires an operator to walk to the bench | Deliberate. This is normal pyrotechnic practice. |
| 5 | No Spanish field edition yet | **Required before live operation.** |
| ~~6~~ | ~~Review owner not named~~ — resolved: **Emilio Guadarrama** | closed |
| 7 | E-match no-fire current unknown, so the continuity check current is unspecified | Open item 3 in [REQUIREMENTS.md](REQUIREMENTS.md) |
| 8 | Logger power domain undecided, affecting clean file close in §8 step 4 | Open item 2 |

---

## 11. References

- *Manual de operaciones: WIRIKUTA 1.1 Banco de Pruebas*, Ignitia Rocket Lab, August 2025
- Tripoli Rocketry Association — High Power Rocketry Safety Code
- National Association of Rocketry — Safety Codes
- Richard Nakka's Experimental Rocketry Site — https://www.nakka-rocketry.net/

---

## 12. Revision history

| Rev | Date | Author | Change |
|---|---|---|---|
| A | 2026-11-06 | Sofia Pacheco Leon | Preliminary issue. Written from the Gate 0 requirements, before any hardware exists. |
