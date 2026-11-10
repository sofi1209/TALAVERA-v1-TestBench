# Umbilical and telemetry options

**Status: proposal. Decision belongs to Gate 1.**

The firing chain is settled and is not affected by anything in this document. Everything here concerns
**how thrust data gets to a computer**, and none of it may acquire authority over arming or firing.

---

## 1. The request

> *"maybe add a secondary option for the umbilical where we connect it directly to a USB to a computer"*

Live data on a laptop during the burn is worth having. The bench currently gives you no live readout at
all — Wirikuta wrote to SD and you found out afterwards.

But **a direct USB cable will not work at 20 m**, and that needs saying before it gets built.

### Why direct USB fails

| Constraint | Value |
|---|---|
| USB 2.0 maximum passive cable length, per spec | **5 m** |
| Requested umbilical length | **20 m** |

USB is a short-haul bus with tight round-trip timing. A 20 m passive run is four times over spec. It
does not degrade gracefully — it enumerates intermittently or not at all, and it is exactly the kind of
fault that appears in the field and not on the bench.

Active USB extenders exist, chaining powered repeaters every 5 m. For a pyrotechnic test bench that
means **four more powered devices and four more connectors** in the one data path you care about, each
needing its own power, sitting in a field. That is the opposite of the robustness this redesign is for.

---

## 2. The fix: differential serial over the umbilical, USB at the station

Run **RS-485** (or an isolated differential UART) over the existing control cable, and put the **USB-C
connector on the station board**. The laptop plugs into the station, 20 m from the motor, not into the
bench.

```
BENCH                          UMBILICAL (cable B)              STATION            LAPTOP

[logger] --> [RS-485 driver] =====  differential pair  =====> [RS-485 rx]
                   |                                                |
             isolation                                        [USB-UART]  ---USB--> [laptop]
                                                                                    short cable
```

Why this is the right shape:

| Property | RS-485 over the umbilical | Direct USB |
|---|---|---|
| Rated distance | ~1200 m. 20 m is nothing. | 5 m, exceeded fourfold |
| Signalling | Differential — rejects common-mode noise | Single-ended pairs, timing-critical |
| Behaviour near a firing transient | Tolerant | Likely to drop the link |
| Extra hardware in the field | None | Four powered repeaters |
| Extension to 40 m later | Free | Needs four more repeaters |

The USB cable that remains is the one from the station board to the laptop sitting next to it — well
inside spec.

### Galvanic isolation is not optional here

A laptop is about to be electrically tied to the bench ground, 20 m away, at the moment several amps
flow through a firing circuit. Without isolation that is a ground loop across a potential difference,
with a pyrotechnic transient superimposed, terminating in someone's computer.

Isolate the serial link. The lab already has **optoisolators (TLP521 / PC817)** from the IGNIS-v5 BOM;
a digital isolator such as the ADuM1201 family is the cleaner modern option. Either way, isolation is a
requirement of this option, not an enhancement.

---

## 3. Parts already in the lab

From the IGNIS-v5 component library, all of which apply directly:

| Part | Role here |
|---|---|
| `TYPE-C-31-M-12` USB-C, 16-pin USB 2.0 | Station board USB connector |
| `ESD9B5.0ST5G` | USB ESD protection |
| `TLP521 / PC817` optoisolator | Serial link isolation |
| `AMS1117-3.3` / `AMS1117-5.0` LDO | 3.3 V and 5 V rails |
| ~~`SS24` Schottky~~ | ~~Reverse-polarity protection on the 12 V input~~ - removed in Rev A.2 (D-079): a crowbar after F1 replaces the series diode. Umbilical pin map now in `hardware/tools/umbilical.py` (D-075) |
| `NCE6005AR` N-MOSFET, 60 V 5 A | Candidate for the igniter drive stage |

This is a strong reuse story: known parts, known footprints, already stocked.

### And the ground station software

IGNIS-v5 ships a Python ground-station app (`GS-Telemetry-App_IGNIS-v5/`) with a serial manager, chart
rendering and a telemetry parser. If the station speaks a simple CSV or packet format over the USB
serial port, **that app is most of the live-readout work already done.** Worth evaluating before
writing anything new.

---

## 4. The three data paths, and why to keep all three

These are complementary, not alternatives. A static fire cannot be repeated, so redundancy on the
record is worth real money.

| # | Path | Role | Fails how |
|---|---|---|---|
| 1 | **Local SD on the bench board** | Primary record. Full rate, no link to lose. | Card corruption, card absent |
| 2 | **Differential analog pair to the station** | Live trace to a DAQ or scope. Works with no software at all. | Cable damage |
| 3 | **Isolated RS-485 → USB at the station** | Live numeric data and logging on the laptop. *(new, secondary)* | Cable damage, software |

Path 1 is the record. Path 2 is the one that works when everything else is broken, because it is just a
voltage on a wire. Path 3 is the convenient one.

---

## 5. Hard constraint

**Path 3 carries data outward only. It must never carry a command inward.**

A USB link to a laptop is precisely the thing that tempts someone, later, to add a "fire" button in
software. The protection is physical, not procedural: the logger has no outputs, no connection to any
safety net, and the arm and fire lines are not reachable from it (SAFETY.md §4).

If a future change seems to need the laptop to command the bench, that is a hardware and safety review
question, not a firmware feature.

---

## 6. Cost of adding this

| Item | Impact |
|---|---|
| Umbilical conductors | 2 more (one differential pair) within cable B, already specified as 8–10 conductor |
| Bench board | RS-485 driver + isolator |
| Station board | RS-485 receiver, USB-UART bridge, USB-C connector, ESD diode |
| Cable length | No change. Extends to 40 m+ free. |
| Safety argument | **Unchanged.** No new path to the igniter. |

Modest, and it uses parts already on the shelf.

---

## 7. Open question for Sofia

**Should path 3 be built into revision A, or left as footprints for later?**

Building it now costs a handful of parts and some board area, and gives live data on the first test.
Leaving pads and a depopulated footprint costs nothing now but means a rework or a revision B to
populate.

Given that paths 1 and 2 already cover the record and the live trace, this is a convenience-versus-scope
call, not a safety one.
