# TALAVERA v1 — Safety

> **Nothing in this repository is approved. Nothing has been built or energized.**
> This document states the safety design intent and the rules the design must satisfy.
> It is not a certification, and it does not substitute for your own review.

---

## 1. The one rule everything else follows from

**Every output's safe state is its de-energized state.**

A design where safety depends on something *working* has a failure mode where it stops working. A design
where safety is the absence of energy does not. Battery death, a cut umbilical, a dropped relay coil, a
cracked solder joint and a deliberate e-stop press must all land in the same place: safe.

This is why there is no microcontroller on the arm, fire or e-stop path. Not because microcontrollers are
unreliable, but because a microcontroller's safe state is a claim about software, and a relay coil's safe
state is a claim about physics.

---

## 2. Named safe states

| Output | Safe state name | Mechanism | Holds without firmware? |
|---|---|---|---|
| Igniter | `PYRO_SHUNTED` | Normally-closed relay contact shorts the two match conductors together. De-energized = shorted. | Yes |
| Arm path | `DISARMED` | Normally-open arm relay, key removed from station switch, arming plug withdrawn at bench | Yes |
| Fire path | `FIRE_OPEN` | Momentary normally-open button. Never latching, never software-held. | Yes |
| Bench power | `BENCH_UNPOWERED` | Master relay is normally-open and must be held in by its coil. E-stop breaks the coil circuit, so the relay drops out. | Yes |
| Load cell excitation | `EXCITATION_OFF` | Derived from the master rail | Yes |
| LED beacon | `BEACON_DARK` | Derived from the master rail. Darkness means de-energized, which is what the operator needs to know. | Yes |
| Logger | `LOGGER_IDLE` | Has no outputs at all. Cannot influence any row above. | Yes — by construction |

### Why the igniter safe state is *shorted*, not *open*

Twenty metres of exposed field cable is a loop. An open circuit at the end of a long loop will develop a
voltage across the e-match from nearby transmitters, static accumulation and weather. A short across the
match pair clamps that to zero and gives induced current a path that is not through the bridgewire.

This is standard practice for pyrotechnic firing systems and it is **absent from Wirikuta 1.1**, where the
safe state is only "MOSFET off". Adding it is one of the main safety improvements in TALAVERA.

---

## 3. The firing chain

Three independent elements in series. All three must be true to pass current.

| # | Element | Where | Defeated by |
|---|---|---|---|
| 1 | ARM key switch | Station, 20 m away | Turning a key that one named person carries |
| 2 | FIRE momentary button | Station | Holding a button. Releasing it opens the circuit. |
| 3 | ARMING PLUG | **At the bench** | A human physically walking up and inserting it |

Element 3 is the important one. It means the bench cannot fire while anyone is near it *unless someone
deliberately made it able to*, and it is visible from a distance — the same role the MG995 servo played in
Wirikuta 1.1, with no actuator and no firmware.

Plus the shunt: while `DISARMED`, the match is shorted. The shunt releases only when the arm relay pulls in.

---

## 4. The logger is a passenger

Logging stays on the bench board, on an **ESP32-DevKitC V4 (ESP32-WROOM-32D)** (D-028). That is a
deliberate decision and it only stays safe under five constraints, which are **design rules, not
suggestions**:

1. **No electrical connection to any safety net.** The logger sees the buffered output of the
   instrumentation amplifier and nothing else. No net it owns may reach the arm line, fire line, shunt
   coil, master coil or igniter pair.
2. **No outputs.** It reads, and it writes to its own SD card. It drives nothing.
3. **Its own fused, separately regulated rail**, so it cannot brown out a relay coil, and a firing
   transient cannot reach it.
4. **A layout keep-out** between the logger zone and the firing chain, enforced at Gate 4 and checked at
   Gate 5.
5. **Radios stopped.** The WROOM-32D carries Wi-Fi and Bluetooth. Both are switched off as the first
   action at boot and must never be enabled (D-029).

If these five hold, the requirement "no controller on anything safety depends on" is satisfied even though
a microcontroller is physically present on the board.

### Why the radio matters here, and why it is not a firing risk

The logger has no outputs and no connection to any safety net, so a radio on it cannot issue a command
that reaches the igniter. The safety argument is unchanged by the ESP32.

The concern is different: a 2.4 GHz transmitter at up to +20 dBm would sit centimetres from the AD620
front end and from a 20 m pyrotechnic cable — the two most EMI-sensitive things on the bench. One is the
measurement the bench exists to make, already noise-limited (manual p. 28). The other is a long
conductor pair running to a bridgewire. Neither wants a transmitter next to it.

This is a **measurement-integrity and pickup** concern, not a command-injection one. It is listed as a
safety constraint because the pyro cable is involved.

### Resolved — logger power domain

**Decided (D-047): the logger sits upstream of the master kill relay, with its own fuse and its own
switch.** The E-STOP kills the pyro circuit and the beacon; the logger keeps running until stopped
deliberately via RECORD, so the data file always closes cleanly. The E-STOP's job is to make the bench
safe, and a logger with no outputs is not a hazard.

One operational consequence to carry into the manual: **a dark beacon no longer means the whole board is
dead.** The logger may still be powered. That does not affect safety — the logger cannot energise
anything — but operators must be told that beacon-dark confirms the *pyro circuit* is de-energised, not
that every component is unpowered.

The reasoning behind the choice:

The Wirikuta protocol presses the e-stop to cut power after the burn, then retrieves the SD card
(manual p. 13, step 4b). **If the logger shares the killed rail, the e-stop yanks power mid-write and can
corrupt the file** — losing data from a test that cannot be repeated.

| Option | Consequence |
|---|---|
| **Upstream of the master relay**, own fuse and switch | E-stop kills pyro and beacon; logger keeps running until stopped deliberately, so the file closes cleanly. One battery to manage. *Recommended.* |
| **Downstream**, shared rail | "E-stop cuts everything" stays literally true. Costs the clean file close. |
| **Own battery** | Maximum isolation. A second battery to charge, check and forget. |

---

## 5. Hazard table

| # | Hazard | Cause | Mitigation | Residual |
|---|---|---|---|---|
| H1 | Unintended ignition with personnel near the bench | Any energization of the match | Arming plug must be inserted by hand; shunt shorts the match while disarmed | Operator inserts plug then lingers — procedural |
| H2 | Unintended ignition from induced energy on the umbilical | 20 m loop, RF or static | NC shunt across match pair; shielded dedicated pyro cable | Not eliminated, strongly reduced |
| H3 | Ignition on power-up or brown-out | Relay chatter, inrush | All safety relays normally-open; match shorted until arm relay pulls in | Needs Gate 2 verification |
| H4 | Loss of ability to stop | Umbilical damage | E-stop drops the master relay. A cut cable de-energizes the coil, which is the safe direction. | Cut cable also ends telemetry — expected |
| H5 | Reversed battery | Hand-wired field hookup | Fuse plus reverse-polarity protection on input | — |
| H6 | Operator approaches an armed bench | Misread state | Beacon driven from real ARM/FIRE signals, not a software report | Procedural |
| H7 | Data loss on an unrepeatable test | SD corruption, single record | Logger power domain (section 4); redundant live analog feed to station | Open until domain decided |
| H8 | Motor fragments / case failure | Motor construction | Out of scope for this board. Governed by the confinement test and standoff distance. | Manual pp. 7–9 |
| H9 | Standoff below code | 20 m umbilical yields 15–17 m real standoff vs 22.5 m NAR/TRA reduced minimum | **Not mitigated.** Accepted deviation, logged as D-007. | Extend umbilical to close it |

---

## 6. Prohibited during design and bring-up

Until the named review owner signs off in writing, with a stated safe setup:

- No output may be energized.
- No actuator, e-match, igniter or live load may be connected.
- No pyrotechnic, actuator, motor, high-current, battery or mains circuit is approved.
- Bring-up runs on a current-limited bench supply, with outputs disconnected, then with inert loads only.
  See [../test/BRINGUP-PLAN.md](../test/BRINGUP-PLAN.md).

**An e-match is connected last, after everything else is verified, with the system disarmed and the
arming plug withdrawn.**

---

## 7. Standoff distance

From the Wirikuta manual (pp. 7–8), NAR/TRA minimum personnel distance by total impulse, with the 25 %
static-test reduction the manual permits:

| Motor class | Total impulse (N·s) | NAR personnel min | ×0.75 static | Cleared by 20 m umbilical? |
|---|---|---|---|---|
| H or smaller | 0 – 320 | 30 m | 22.5 m | **No** |
| I | 320 – 640 | 30 m | 22.5 m | **No** |
| J | 640 – 1,280 | 30 m | 22.5 m | **No** |
| K | 1,280 – 2,560 | 60 m | 45 m | No |
| L | 2,560 – 5,120 | 90 m | 67.5 m | No |
| M | 5,120 – 10,240 | 150 m | 112.5 m | No |

A 20 m cable yields roughly 15–17 m of standoff once routing, sag and service loops are accounted for.
**The 20 m configuration clears no class in this table.** It is an accepted deviation (D-007/D-011), not a
design limit: the boards are unchanged at 40 m, so extending the umbilical is a cable purchase.

For reference, Wirikuta's existing dead-man rope is specified at 5–10 m (manual pp. 15, 20).

---

## 8. Review sign-off

| Item | Reviewer | Date | Signature |
|---|---|---|---|
| Architecture (Gate 1) | Emilio Guadarrama | | |
| Schematic (Gate 2) | Emilio Guadarrama | | |
| Pyrotechnic firing circuit | Emilio Guadarrama | | |
| Battery and power input | Emilio Guadarrama | | |
| Layout (Gate 4) | Emilio Guadarrama | | |
| Fabrication package (Gate 6) | Emilio Guadarrama | | |
| Authorisation to connect a live e-match | Emilio Guadarrama | | |

**Review owner: Emilio Guadarrama** — Division Leader & Vice President, Ignitia Rocket Lab.

No row above may be signed by anyone else. Stage 5 of the bring-up plan requires a separate written
authorisation from him naming the safe setup, location, personnel and standoff distance.
