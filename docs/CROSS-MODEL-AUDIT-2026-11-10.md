# Cross-model audit brief — TALAVERA v1 Rev A.1, pre-layout

*Paste the block below into each reviewing model, **separately and without showing either one the
other's reply**. Attach `exports/2026-11-09-revA1/talavera-bench-schematic.pdf`,
`talavera-station-schematic.pdf`, and both `.net` netlists if the model accepts attachments.*

*Redaction applied: no absolute paths, no credentials, no personal names. The repository URL is public
and is the only identity-revealing item — strip the "Repository" line if you would rather not share it.*

*Why two models independently: the last round found that the bench could not fire, and both reviewers
found it separately. Agreement between two cold readers is the only evidence this project has that a
finding is real. Do not paste one model's output into the other.*

---

## 1. Goal

Audit the two schematics of a **solid-rocket-motor static test bench** one last time before PCB layout
begins. The previous revision could not fire and could not power up; both faults are fixed and
verified. I want to know what is still wrong **before** copper is committed, and specifically whether
the fix for the firing loop introduced anything new.

## 2. Context

- **What it is:** replacement electronics for a university rocketry lab's static test bench. Two boards
  joined by one 12-conductor umbilical: `talavera-bench` at the stand, `talavera-station` at the
  operator position ~20 m away. A load cell is logged while a motor burns.
- **The governing principle, which must not change:** *no microcontroller takes part in arming, firing
  or emergency stop.* Those are relay contacts, panel switches and a shorting plug inserted by hand.
  The ESP32 logger has **no authority over any output**. Reject, do not evaluate, any suggestion that
  moves arming, firing or E-STOP under firmware control.
- **An external interrupt exists off-board:** a dead-man switch or RBF-style removable link in the
  firing line, independent of every board net. It carries the operator abort. It does **not** re-close
  the igniter shunt.
- **Tooling:** KiCad 10.0.5. The `.kicad_sch` files are **generated** by Python and never hand-edited.
- **State:** Gate 2–3. No layout exists and none may start — 110 of 110 components still have no
  footprint, and eight topology decisions are open. Fabrication release and live-initiator testing
  require the review owner's written sign-off, not given.
- **Repository:** https://github.com/sofi1209/TALAVERA-v1-TestBench (public)

## 3. What changed since the last audit

The previous revision had two blockers, both found independently by two reviewers:

- **The firing loop had no return.** `PYRO_MATCH_N` reached only K3's NC contact and the optocoupler
  LED, both of which led back to `PYRO_MATCH_P`. No current could flow in any state.
- **`D_RP`, the series reverse-polarity Schottky, was reversed**, so nothing downstream of fuse F1 was
  powered.

Both are fixed. K3 now carries the shunt **and** the low-side return on one Form C pole, using a
contact that was previously unused. A third finding, mine, changed that fix: routing the match return
to `GND` would have put the fire current through the same net as the load-cell excitation return and
the converter's analog ground, so the return is now its own net with a single star bond.

## 4. Relevant netlist evidence

**The firing path now, from KiCad's own export:**

```
feed    +12V_RAW -> +12V_FUSED -> +12V_PROT -> +12V_MASTER -> ARM_BUS -> PYRO_FIRE_OUT -> PYRO_MATCH_P
match   PYRO_MATCH_P -> PYRO_MATCH_N          (P1, the e-match)
return  PYRO_MATCH_N -> PYRO_RTN -> GND       (K3 NO, then R_STAR)
```

**K3, the part I most want checked:**

```
K3  COM(11) = PYRO_MATCH_N    NC(12) = PYRO_MATCH_P    NO(14) = PYRO_RTN
    coil: ARM_LINE / GND
```

De-energised the match is shorted and isolated from the return; energised the shunt opens and the low
side ties to the return. Fire current passes through the NO contact (10 A rated) rather than the NC
(6 A rated).

**The star bond, so fire current stays out of the analog ground:**

```
/PYRO_RTN       K3.14, R_STAR1.1        <- exactly two pins
GND             R_STAR1.2, R_EXC_N1.2 (bridge excitation return),
                U_ADC1.5 (AVSS), K1.A2, K2.A2, K3.A2, MCU1 grounds,
                J_PWR1.2 (battery negative), ... 45 pins total
```

**Continuity sense, unchanged and known non-functional:**

```
PYRO_MATCH_P    J_ARM1.2, K3.12, P1.1, R_CONT1.1
CONT_LED_A      R_CONT1.2, U_CONT1.1        (PC817 LED anode)
PYRO_MATCH_N    K3.11, P1.2, U_CONT1.2
```

`R_CONT` + the opto LED sit in **parallel with the match** with no pre-arm source, so the lamp can
never light. It fails to the "no match" reading. `R_CONT` is still TBD.

## 5. Acceptance criteria

1. `kicad-cli sch erc` 0 errors, each remaining warning justified in writing.
2. Every diode verified by **pin function from the exported netlist**, not by symbol appearance.
3. Every rail that feeds a `power_in` pin has a source or `PWR_FLAG`.
4. Arming, firing and E-STOP contain no semiconductor under firmware control, and every relay's
   de-energised state is the safe state.
5. The fire current cannot return through the analog ground except at the single star bond.
6. Every value labelled **verified** (with datasheet or manual page) or **assumed**.

## 6. Evidence

**Verified** this session, reproducible from the repository:

- `validate_sch.py` 0 errors / 0 warnings on both boards, with symbol resolution confirmed to have run.
- `kicad-cli sch erc` **0 violations on both boards**.
- `trace_fire_loop.py` — current flows **only** with FIRE held; none in SAFE, ARMED, E-STOP or
  FIRE-without-ARM. Disarmed, the initiator is shorted by the shunt and isolated from the return.
- `PYRO_RTN` contains exactly `K3.14` and `R_STAR1.1`.
- Station isolation: only `U_ISO1` and `U_ISO2` touch both ground domains, and **no signal net spans
  them**.
- Routing demand after a ground pour: 104 signal edges (bench), 68 (station).

**Assumed** — do not treat as fact:

- Fire current ~6–12 A, from 12 V into a 1–2 Ω match. **The e-match is unknown.**
- Songle SRD changeover is break-before-make. **No datasheet in hand.** The K3 topology depends on it.
- AMS1117 output capacitance 22 µF, from the datasheet's stability note; the exact part is unconfirmed.
- 55 °C ambient; logger ~150 mA.

**Not checked:** layout and DRC (none exists); firmware (never compiled, ADS1220 registers are
placeholders); all pyro and analog values, blocked on the two missing data items.

## 7. Unresolved problems

- **Two missing data items block every pyrotechnic and analogue value.** The e-match part and its
  no-fire / all-fire current and resistance; and the load cell's make, bridge resistance, mV/V and
  rated excitation. **Do not invent either.**
- **No working continuity check.** Fails safe, but a pre-arm test function is undesigned and the
  operations manual step that relied on it is suspended.
- **E-STOP drops the master relay only**, so the shunt stays open while ARM is on. The external
  dead-man covers operator abort but does not re-close the shunt.
- **ARM and FIRE are adjacent** on umbilical pins 1 and 2.
- **The 6N137 receive path inverts**, so telemetry cannot work as drawn.
- **Bench 3.3 V thermal:** ~1.3 W in SOT-223, ~133 °C junction computed against a ~125 °C limit.
- **The sheet draws a bare WROOM-32D; the build sockets a DevKitC.**

## 8. Review request

Please check, in this order, and assume the previous reviewers missed things:

1. **The K3 change, hardest.** One Form C pole now owns both the shunt and the low-side return. What
   fails if the changeover is make-before-break? What fails if the NO contact welds, or the NC welds,
   or the coil opens? Is there a state in which the shunt sits across a live source? Does the
   de-energised state remain safe under every single fault you can name?
2. **Did the fix introduce anything new?** Trace the whole loop again from the netlist above. I am
   specifically worried about the post-fire case: once the match opens while FIRE is held, the full
   rail sits across `R_CONT` + the opto LED to `PYRO_RTN`.
3. **The star bond.** Is one 0 Ω link at the battery negative the right way to keep 6–12 A out of the
   analog ground on a two-layer board, or does this need a different scheme?
4. **Every diode and polarised part, by pin function.** One series diode was found reversed after five
   flybacks had already been found reversed. Redo the sweep; assume it is incomplete.
5. **The safety chain as drawn** — confirm no semiconductor under firmware control, every relay's
   de-energised state safe, no single logger fault able to energise the pyro channel. **Report your
   assessment; do not sign it off.**
6. **Anything the tools cannot see** — a connected, legal, wrong circuit. That is the failure mode this
   design keeps producing.

**Format:** one table, most severe first. Columns: ID, severity (blocker / major / minor / note),
location (reference designator, net, or file and line), evidence, why it is wrong, recommended fix, and
**verified or assumed**. Flag anything needing a datasheet I have not supplied rather than filling in a
plausible number. If a finding is a judgement call, say so instead of ranking it.
