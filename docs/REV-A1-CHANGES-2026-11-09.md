# TALAVERA v1 — Rev A.1 corrective change record, 9 November 2026

**Baseline:** `43e9803` · **Author:** Sofia Pacheco Leon · **Review owner:** Emilio Guadarrama
**Status: SCHEMATIC CORRECTIONS DRAWN AND VERIFIED. NO CIRCUIT IS APPROVED.**

Applied under the authorisation to make the corrections, and under **D-053**, which lets Gates 2–5
proceed without a per-gate signature — a drawing cannot hurt anyone. **Gate 6 (fabrication release) and
bring-up Stage 5 (live e-match) still require Emilio's written sign-off.** No gerbers exported, nothing
ordered, no initiator connected.

Sources: `AUDIT-RECONCILIATION-2026-11-09.md`, and the two archived independent audits under
`docs/external-audits/`.

---

## 1. Verification, after the changes

| Check | Tool | bench | station |
|---|---|---|---|
| Structural | `validate_sch.py` | **0 errors, 0 warnings** | **0 errors, 0 warnings** |
| Symbol resolution actually ran | `validate_sch.py` stats | `structural_checks ran` | `structural_checks ran` |
| Native ERC | `kicad-cli sch erc` 10.0.5 | **0 violations** | **0 violations** |
| Firing loop closes, and only when it should | `trace_fire_loop.py` | **all states as expected** | n/a |

The bench board had never been ERC-clean under the native tool before. It now is — and that claim is no
longer the whole story, which is the point of the third row.

**The firing loop, traced from KiCad's own netlist export:**

```
feed    +12V_RAW -> +12V_FUSED -> +12V_PROT -> +12V_MASTER -> ARM_BUS -> PYRO_FIRE_OUT -> PYRO_MATCH_P
match   PYRO_MATCH_P -> PYRO_MATCH_N
return  PYRO_MATCH_N -> PYRO_RTN -> GND
```

| State | K4 | K1 | K2 | K3 | Fire current |
|---|---|---|---|---|---|
| SAFE | in | — | — | — | none |
| ARMED | in | in | — | in | none |
| **FIRE held** | in | in | in | in | **flows** |
| E-STOP pressed | — | in | in | in | none |
| FIRE without ARM | in | — | in | — | none |

Also verified: disarmed, the initiator terminals are shorted by the shunt **and** isolated from the
supply return; armed, the shunt is released and the low side is tied to the return.

---

## 2. Blockers closed

### B-3 / B01 · `D_RP` reverse-polarity diode un-reversed **V**

`gen_bench.py` — the series SS24 had its cathode toward the battery, so it was reverse-biased in
*normal* polarity and nothing downstream of F1 was powered. Anode now on `+12V_FUSED`, cathode on
`+12V_PROT`. This was the sixth reversed diode in the project; see §4 for the guard that now exists.

### B-1 / B03 · The firing loop has a return **V — topology NOT APPROVED**

`PYRO_MATCH_N` reached only K3's NC contact and the opto LED, both of which led back to
`PYRO_MATCH_P`. No path to the supply return existed, so no current could flow in any state.

K3 now does both jobs on one Form C pole, using the contact that was previously unused and
no-connect-flagged:

| | Before | After |
|---|---|---|
| COM (11) | `PYRO_MATCH_P` | `PYRO_MATCH_N` |
| NC (12) | `PYRO_MATCH_N` | `PYRO_MATCH_P` |
| NO (14) | *unused* | `PYRO_RTN` |

De-energised, the match is shorted *and* isolated from the return. Energised, the shunt opens and the
low side ties to the return. Fire current passes through the NO contact (10 A) rather than the NC (6 A).

**This is decision D-A and it is not settled.** Both audits converged on this topology, but it depends
on the Songle SRD changeover being genuinely break-before-make, which no datasheet in hand confirms
(O-3). Audit B's objection stands on the record: one contact mechanism now owns two safety functions,
which makes their failures harder to evaluate independently. **Get the Songle evidence, then decide.**

### R-1 · `PYRO_RTN` is a separate net with one star bond **V**

My own finding, in neither audit, and it changes the B-1 fix. Routing the match return to `GND` would
have put the full fire current — roughly 6–12 A pending O-1 — through the single net that also carries
`R_EXC_N` (load-cell excitation return), `U_ADC.5 (AVSS)` and the ESP32 grounds, during the burn.

`PYRO_RTN` now contains exactly `K3.14` and `R_STAR1.1`, bonded to `GND` only at `R_STAR` beside
`J_PWR`. Verified from the netlist.

> **Layout requirement, not a suggestion.** `PYRO_RTN` is a dedicated copper path from K3 to `R_STAR`.
> It may not be poured into the analog or digital ground, and `R_STAR` is the single bond. The 0805
> placeholder is not a 10 A part — size the link and its copper once O-1 lands, and consider a wire
> link or a bolted star post instead.

### M-10 / B02 · The station supply is drawn honestly, and fused **V**

The sheet claimed the station drew bench-referenced power *from the umbilical*, and a `PWR_FLAG` on
`+12V_STN` hid from ERC that no supply conductor exists — pins 1–9 are signals, 10–12 returns. The
sheet now states that the supply arrives on its own feed at `J_12V`, and `F_STN` fuses it: it was
previously unfused while driving 20 m of `ARM_LINE` and three relay coils.

**Whether to keep a separate feed or reallocate an umbilical conductor is decision D1, unmade.** I drew
the honest version of what exists rather than inventing a conductor allocation, because that choice is
coupled to the ARM/FIRE pin separation (M-9) and the E-STOP architecture.

---

## 3. Mechanical corrections, single right answer

| Item | Change |
|---|---|
| ERC error `power_pin_not_driven` | `PWR_FLAG` on `+12V_LOGGER`; ERC does not propagate a source through fuse F2 |
| `D_FIRE` sneak path (M-12) | FIRING lamp moved from `PYRO_FIRE_OUT` to `FIRE_LINE`. On the output it was a 1 k path to ground that any continuity source crossing K2 would light with **no match fitted** |
| `ADC_CS` floating (M07) | `R_ADCCS` 10 k pull-up added; `SD_CS` already had one |
| `RS485_DE` unbiased (m-6) | `R_DE` 10 k pull-**down** at the bench, so reset and unpowered states leave the driver **off** |
| Station had no rail decoupling (N-2 / M-3 / B08) | `C_STN1` 10 µF on `+12V_STN`, `C_STN2`/`C_STN3` 22 µF on `+5V_BENCH`/`+3V3_BENCH`, `C_485` 100 nF at the SP3485 VCC pin, `C_ISO1`/`C_ISO2` 100 nF at each 6N137 pins 8–5 as its datasheet requires. **22 µF values are ASSUMED** from the AMS1117 stability note — confirm against the exact part, O-20 |
| Shield grounded at both ends (m-9 / M03) | Station end now floats; pin 12 bonds at the bench only, matching the bench sheet's own note |
| `THRUST_DIFF` phantom path (N-1 / m-2 / M08) | Deferred for Rev A. Bench pins 8/9 and the station's `J_DAQ` carry no-connect flags; `J_DAQ` is marked not fitted. It was a pair present at both connectors with no source — and its pin 3 exported bench ground to the laptop bench, bridging the isolation barrier |
| SD-detect note wrong | Note corrected: `CARD1.10 (DET_A)` to `SD_DETECT`, `.9 (DET_B)` to GND. The **wiring was already right**; only the note was wrong |
| Stale BOM (M10) | `S_CONT` removed — the continuity button was deleted by H-2 on 6 November and the parts list kept listing it. `R_STAR`, `F_STN`, `C_STN2/3` added |
| Machine-locked tooling (M10 / §3) | `OUT` paths in both generators and `ROOT` in the parts list are now relative to the file |

---

## 4. R-2 · The validator can no longer pass vacuously

`validate_sch.py` resolved symbols through a `SYMDIR` hardcoded to one machine, inside
`except Exception: continue`. With that path wrong it returned a **byte-identical "0 errors"** while the
pin-coincidence, floating-pin and power-pin checks silently did nothing — and those three are the guards
added after the `GND_RTN` split, the AMS1117 pin-1 error and the SP3485 left with no ground.

- `ksch.py` resolves `SYMDIR` from `$TALAVERA_SYMDIR`, `$KICAD_SYMBOL_DIR`, or by globbing the usual
  install locations, newest first. An override that is set but wrong is now **fatal**, not silently
  replaced by whatever else is installed.
- `SymbolLibError` replaces the bare raises, and carries the path it tried.
- `validate_sch.py` resolves every `lib_id` **before** any geometry check and reports an error naming
  each failure, plus `structural_checks: SKIPPED`. It prints the `symdir` it used, so a clean run is
  attributable to a known library set, and it **exits non-zero** on any error.

Verified both ways: a dead override aborts with a clear message; a valid directory holding no libraries
gives 232 errors and `structural_checks SKIPPED` instead of a clean bill of health.

### New guard: automatic diode polarity

`docs/HANDOFF.md` recorded diode polarity as the one fault class with no automated guard — *"Nothing
automatic. Check every diode by hand."* — after five reversed flybacks and a reversed buzzer diode.
There is now a guard, in three rules, each self-tested against a deliberately broken board:

1. **Relay flyback, exact.** A diode whose two nets are *exactly* a relay's two coil nets must have its
   cathode on A1. No rail inference, which is the point: `ARM_LINE` and `FIRE_LINE` carry 12 V without
   saying so in the name, so a rank-based rule would have missed four of the five original reversals.
   *Tested: reversing `D_K1` produces an error.*
2. **Known rails.** A diode between two nets of known, different rail potential must not be
   forward-biased from the higher to the lower.
3. **Rail-to-signal, warning.** Anode on a positive rail with an unranked cathode — correct for a series
   pass diode, reversed for a flyback across a low-side-driven load. *Tested: reversing `D_BUZZ`
   produces the warning.*

**What it still does not cover:** a series pass diode between two nets of the same rank — exactly where
`D_RP` sat reversed while ERC, this validator and a completed hand audit all passed it. For that there
is now `trace_fire_loop.py`.

### New tool: `hardware/tools/trace_fire_loop.py`

Asks the question none of the existing tools asked: **can current complete a circuit from the battery,
through the initiator, and back?** It models relay contacts per state, treats diodes as directed
anode-to-cathode edges, and deliberately excludes current-limiting resistors from the power path — a
10 kΩ pull-up is not a conductor for this question, and treating every resistor as one is how a tracer
starts finding loops that cannot pass an amp.

Two mistakes were made writing it and both are worth recording, because they are the same mistake as the
original fault. First it excluded diodes entirely, which cut the feed at `D_RP` and reported a dead
board. Then its path search carried a "did I pass through the initiator" flag and kept searching past
the goal, so it wandered back through the sense branch and manufactured loops that do not exist — the
same failure Audit A admitted in its own `reach2.py`. It now asks two independent reachability
questions with `P1` removed from the graph, and stops at the goal.

**Self-tested against the original netlist**, where it correctly reports `FIRE held: none — MISMATCH`
and `armed: low side tied to the supply return: NO`.

It covers connectivity only. Contact ratings, timing, break-before-make, welded contacts and anything
thermal are outside it, and it approves nothing.

---

## 5. Deliberately NOT changed

Each of these is a decision or needs data. Changing them unilaterally would be exactly the thing I
should not do.

| Item | Why not | Needs |
|---|---|---|
| **Continuity function** (B-2 / B04) | `R_CONT` + opto still sit in parallel with the match with no pre-arm source, so the lamp can never light. It **fails to the "no match" reading**, which is the safe direction. A correct pre-arm TEST needs a sense-current limit, and that needs the no-fire current | **O-1**, and decision **D-B** |
| **E-STOP architecture** (M-7/M-8 / B05) | **Narrowed by D-073.** An external off-PCB dead-man or RBF interrupt in the firing line carries the operator abort, independent of every board net, so no abort system is designed onto the board. What remains is **automatic** behaviour: E-STOP still drops K4 only, so the shunt stays open while ARM is on, and the external interrupt does not re-close it. The shunt is the H2 defence against induced energy on a 20 m loop | Review-owner decision, now a smaller one |
| **Umbilical pinout** (M-9 / B06) | ARM and FIRE are still adjacent on pins 1/2. Separating them is coupled to the station-power conductor allocation and to whether the E-STOP loop stays low-side | Decisions **D1** + E-STOP, together |
| **6N137 inversion** (M-2 / M02) | The RX path inverts, so telemetry cannot work: the LED conducts on `RO` high and an enabled 6N137 pulls its output low, giving the CH340C a continuous break. Swapping the LED round makes `RO` *sink* the current, and the SP3485 drive limits are not in hand. Noted on the sheet as **O-21** | SP3485 datasheet, or a digital isolator |
| **AMS1117 bench thermal** (M-1 / M-5 / B08) | ~1.3 W in SOT-223, ~133 °C junction against a ~125 °C limit at an assumed 55 °C ambient. The fix is a different power architecture | Decision **M-1** |
| **DevKitC representation** (M-2 / M01 / M06) | The sheet still draws a bare WROOM-32D. Replacing it with a 2×19 header symbol changes the footprint, the BOM and the supply pin | Decision **M-2** |
| **Buzzer part** (M-13 / M04) | `LS1` polarity is correct but the MLT-8530 is an externally driven ~3.6 V transducer on a 12 V DC drive. Needs a 12 V active sounder | Part selection |
| **AD620 path B** (M-14 / M06) | `AMP_REF` still floats and `+5V_AMP` has no cap. Both audits recommend dropping path B from Rev A | Decision |
| **Firmware** (M07) | 20 SPS placeholder against a ≥ 1 kSPS target, raw counts labelled `thrust_N`, no sequence counter. Touches no safety circuit | **O-2**, then calibration |

---

## 6. What Emilio is being asked to decide

1. **D-A** — K3 doing both shunt and return, or two relays? *Blocked on the Songle break-before-make
   evidence. The drawn topology assumes break-before-make.*
2. **D-B** — the pre-arm continuity TEST function. *Note the hazard neither audit stated: any continuity
   test must open the shunt, so the H2 induced-energy defence on a 20 m loop is absent for the duration.
   TEST must be momentary only, never latching.*
3. **D1** — station power: separate feed, or a reallocated umbilical conductor?
4. **Does the shunt have to re-close automatically?** D-073 puts the operator abort on an external dead-man
   or RBF interrupt, which does not re-close the shunt. So the only question left here is whether an
   E-STOP must restore the H2 induced-energy defence by itself, or whether a procedural step is enough.
5. **M-1** thermal, **M-2** DevKitC representation, and whether path B survives Rev A.

Items 1, 3 and 4 are coupled through the harness and the relay count, so they want one review, not four.

**Gate 4 must not start until D-A is closed**, because the relay topology decides the pyro copper, and
R-1 decides where the fire current is allowed to flow.

---

## 7. Schematic legibility

Both sheets had text sitting on text, net labels landing on reference and value text, and notes running
outside their section boxes — including two collisions I introduced myself by dropping `R_STAR` on top of
the D-047 note. `hardware/tools/check_layout.py` is new and measures it: text/text, text/symbol,
symbol/symbol, label and property collisions, and anything that escapes the dashed box it belongs to.

Bench went from 17 reported collisions to **zero**; station from 12 to **zero**.

One correction is worth recording, because the "fix" was worse than the problem. A USB-C receptacle has
four VBUS pins carrying one net, and their labels coincide exactly. That draws as a single label and is
correct. Staggering the stub lengths to separate them put a longer wire through a shorter one's label
anchor, and **KiCad ERC caught it as `label_multiple_wires` — two violations the project validator
passed.** The stagger is reverted and the checker now ignores coincident same-net labels. The lesson is
the project's own, again: a clean validator is not a clean ERC, and a cosmetic change can break
connectivity.
