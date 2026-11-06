# TALAVERA v1 — Bring-up Plan

**PRELIMINARY — Gate 7 not approved.**

> No stage below may be executed until the named review owner has signed off the board and
> authorised that specific stage in writing, with a stated safe setup.
>
> **No e-match, igniter, actuator or live load is connected at any stage before Stage 5,
> and Stage 5 requires its own separate written authorisation.**

---

## Ground rules for every stage

1. **Current-limited bench supply only.** Never the 12 V SLA battery during Stages 1–4.
   Set the limit, confirm it by shorting the leads before connecting the board.
2. **Outputs disconnected.** Igniter terminals open, beacon disconnected, load cell disconnected,
   until the stage that explicitly adds them.
3. **One change at a time.** Record the measurement before and after.
4. **Record every measured value** in the stage table, against the expected value.
   A measurement that is merely "about right" is not a pass.
5. **Stop on the first anomaly.** Do not continue to the next stage to "see if it clears".

---

## Stage 0 — Bare board inspection

No power applied.

| Check | Expected | Measured | Pass |
|---|---|---|---|
| Visual: solder bridges, tombstoned parts, polarity marks | None / correct | | |
| Continuity: 12 V input to GND | Open (no short) | | |
| Continuity: each regulated rail to GND | Open (no short) | | |
| Continuity: igniter output pair | **Shorted** — the shunt is closed at rest | | |
| Reverse-polarity device orientation | Matches schematic | | |
| Part markings match BOM | All | | |

**The igniter pair reading shorted with no power applied is the single most important check on
this board.** If it reads open, the shunt is wired wrong and the board must not be powered.

---

## Stage 1 — Input protection

Current-limited supply, limit set low. Outputs disconnected.

| Check | Expected | Measured | Pass |
|---|---|---|---|
| Apply 12 V correct polarity, measure input current | Within expected quiescent | | |
| Fuse intact | Yes | | |
| **Apply reversed polarity** at the current limit | No current flow, no heating, no damage | | |
| Igniter pair still shorted | Yes | | |

---

## Stage 2 — Rails

| Check | Expected | Measured | Pass |
|---|---|---|---|
| Each regulated rail voltage at its test point | Per schematic | | |
| Ripple on each rail | Per schematic | | |
| Regulator case temperature after 10 min | Within derated limit | | |
| Logger rail present and separately fused | Yes | | |
| Igniter pair still shorted | Yes | | |

---

## Stage 3 — Safety chain, igniter output open and monitored

Igniter terminals connected to a **high-impedance voltmeter and a current probe only.**
No load. No match. Nothing that can dissipate energy.

| Check | Expected | Measured | Pass |
|---|---|---|---|
| Power-up with station disarmed: voltage across igniter pair | 0 V, pair shorted | | |
| Power-up transient: any current pulse through igniter pair | **None, at any point** | | |
| Arming plug withdrawn, ARM key turned: igniter pair | Shunt releases, still 0 V, no current | | |
| Arming plug withdrawn, ARM + FIRE: igniter pair | Still open, no current — plug breaks the chain | | |
| Arming plug inserted, disarmed: igniter pair | Shorted by shunt, 0 V | | |
| Arming plug inserted, ARM only: igniter pair | Shunt released, fire relay open, no current | | |
| Press E-STOP in every state above | Master drops out, shunt re-closes, 0 V | | |
| Remove supply abruptly in every state above | Shunt re-closes, 0 V | | |
| **Disconnect each umbilical conductor in turn** | Falls to disarmed and shorted every time | | |

Every row in this table must pass before the board is allowed near a load of any kind.

---

## Stage 4 — Measurement and indication, inert loads only

| Check | Expected | Measured | Pass |
|---|---|---|---|
| Igniter output into an **inert resistive load** matching the e-match resistance — ARM + FIRE | Current within computed range, duration = button hold | | |
| Same, with a current probe: rise time and peak | Per design | | |
| Beacon connected: state matches the real ARM/FIRE lines in every combination | Exactly | | |
| Load cell connected, no mechanical load: amplifier output | At expected zero offset | | |
| Known calibration mass applied: amplifier output | Per computed sensitivity | | |
| Differential pair over the **full 20 m umbilical**: noise floor at the station | Better than the Wirikuta baseline | | |
| Battery sense reading at station vs a reference meter | Agree within tolerance | | |
| Logger: file created, parses cleanly, no diagnostic rows | Yes | | |
| Logger stopped by its own switch: file closes cleanly | Yes | | |
| Logger: confirm no logger net reaches any safety net | Verified by measurement and by layout review | | |
| Logger: **confirm Wi-Fi and Bluetooth are off** — scan for the module's SSID and BT address with the logger running | Not present on either band | | |
| Logger: noise floor on the thrust channel with the logger running vs. powered down | No measurable degradation attributable to the logger | | |
| Logger: RECORD opened — file closes cleanly, then E-STOP pressed | File intact and parseable after the E-STOP | | |

**The inert load must match the e-match resistance and must be rated for the energy.**
A resistor that cannot take the pulse is not an inert load, it is a fuse.

---

## Stage 5 — Live e-match — SEPARATE WRITTEN AUTHORISATION REQUIRED

> **Not authorised. Do not plan, schedule or prepare this stage until every row of Stages 0–4 has
> passed and been recorded, and the review owner has signed a separate authorisation naming the
> safe setup, the location, the personnel and the standoff distance.**

When it happens, it happens as a **standalone e-match test with no motor present**, at full standoff,
following the full ignition procedure in [../docs/OPERATIONS-MANUAL.md](../docs/OPERATIONS-MANUAL.md) §6.

A motor is only ever introduced after a successful bare e-match firing.

---

## Sign-off

| Stage | Executed by | Date | Review owner sign-off |
|---|---|---|---|
| 0 | | | |
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | **separate authorisation** |
