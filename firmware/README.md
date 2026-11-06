# Firmware

## This firmware has no safety authority

TALAVERA's arming, firing and emergency-stop paths are **hardware only** — switches, relay contacts and
resistors. Nothing in this folder participates in them. Nothing in this folder can participate in them,
because the logger has no outputs.

If every line of code here were deleted, or hung, or ran wrong, the bench would remain exactly as safe.
The only consequence would be a missing thrust record.

That is the entire point of the TALAVERA redesign. Read [../docs/SAFETY.md](../docs/SAFETY.md) before
changing anything here.

---

## Contents

| Folder | Purpose |
|---|---|
| `logger/` | Thrust data logger for the bench board. Reads the amplified load-cell signal, writes CSV to SD. |

---

## The four constraints

These are enforced in hardware and must not be worked around in software:

1. **No electrical connection to any safety net.** The logger sees the buffered output of the
   instrumentation amplifier and nothing else.
2. **No outputs.** It reads, and it writes to its own SD card. It drives nothing.
3. **Its own fused, separately regulated rail.** It cannot brown out a relay coil.
4. **A layout keep-out** separates it from the firing chain.

If a future change to this firmware seems to require an output pin that leaves the logger's own
subsystem, that change is wrong. Raise it as a hardware question instead.

---

## No state machine

Wirikuta 1.1 ran a nine-state machine with six remote commands, RF handling and a diagnostics routine.
All of it is gone. The logger has exactly one behaviour:

> **It records whenever it has power.**

The file opens when the logger is switched on and closes when it is switched off. There are no states,
no commands, no timeouts, no abort logic and no radio.

This deletes the entire class of defect that motivated the redesign — including the two concrete bugs
found in the Wirikuta firmware (see [../docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md) §6) — and it has a
second benefit: the CSV contains thrust data only. The manual cell deletion previously required before
the Kalman script would parse the file (Wirikuta manual p. 27) is no longer necessary.

---

## Operational consequence

Because the logger is stopped by its own switch rather than by cutting power, **stop it deliberately
before pressing E-STOP** so the file closes cleanly. This is step 4 of the post-test procedure in the
operations manual. Yanking power mid-write risks corrupting data from a test that cannot be repeated.
