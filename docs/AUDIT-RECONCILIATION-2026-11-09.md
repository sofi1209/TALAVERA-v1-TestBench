# TALAVERA v1 — Reconciliation of two independent audits

**Date:** 9 November 2026 · **Baseline:** commit `43e9803`, unchanged · **Status: ANALYSIS — NOTHING APPROVED**

**Inputs.** Two independent audits of the same revision, produced from the cross-model handoff package:

| | Document | Verdict |
|---|---|---|
| Audit A | `AUDIT-2026-11-09.md` + `PROPOSAL-REV-A1-2026-11-09.md` (Claude) | NOT FIT FOR LAYOUT, 3 blockers |
| Audit B | `TALAVERA-v1-schematic-audit.md` + `TALAVERA-v1-final-proposal.md` (ChatGPT) | Hold schematic release, 8 blockers |

**Method of this document.** Every decisive claim in both audits was re-checked against the KiCad-exported
netlists in `exports/2026-11-09/` — not against either audit's prose, and not against the repo's own
`netlist.py`. Claims I could not reproduce are marked as such. Two findings below appear in **neither**
audit.

> **Safety.** Nothing here approves any pyrotechnic, actuator, battery or high-current circuit. Every
> arm / fire / shunt / continuity / E-STOP proposal is a topology option for **Emilio Guadarrama's**
> decision and written signature. Gate 6 (fabrication release) and bring-up Stage 5 (live e-match) keep
> mandatory written sign-off. No gerbers exported, nothing ordered, no initiator connected.

Status key: **V** verified here against the exported netlist · **A** assumed, needs the named datasheet ·
**D** decision for the review owner.

---

## 1. The headline: the bench cannot fire, and my own previous finding was wrong

Both audits independently found that **the firing loop has no return**, and I have confirmed it:

```
/PYRO_MATCH_N   K3.12 (NC)   P1.2 (E-MATCH)   U_CONT1.2 (opto LED cathode)
```

Three pins, and nothing else. `K3.12` is the NC contact whose COM (`K3.11`) is `PYRO_MATCH_P`. The opto
LED's anode returns through `R_CONT` to `PYRO_MATCH_P`. **Both paths lead back to `MATCH_P`; neither
reaches GND.** `U_CONT1.3` is on GND, but that is the phototransistor emitter, across the isolation
barrier. **V**

The source chain is intact — `+12V_PROT → K4.11/14 → +12V_MASTER → K1.11/14 → ARM_BUS → K2.11/14 →
PYRO_FIRE_OUT → J_ARM (arming plug) → PYRO_MATCH_P → P1 (match)` — and then stops. No current can flow
in any state. **V**

Root cause, from Audit A and consistent with `gen_bench.py:130`: D-045 dropped the IGNIS gate-drive half,
and in IGNIS **the low-side MOSFET was the return**. D-059/O-18 then deleted cable A, which had carried the
station-sourced sense current. Both halves of the return were removed, each for a defensible reason, and
nothing replaced either.

### My finding N-3 was wrong, and so was H-2 from 6 November

`docs/AUDIT-2026-11-09-FOLLOWUP.md` N-3 states that sense current crosses the initiator permanently. The
cross-model handoff repeated it. **Both audits flag it as unsupported, and they are right.** I verified
that the branch `PYRO_MATCH_P → R_CONT → opto LED → PYRO_MATCH_N` is electrically continuous and
concluded current flows through it. I never asked what drives it. Nothing does: both ends of that branch
sit on the two match terminals, no net imposes a potential difference across them, and no path reaches
ground. The current is **zero**, not "permanent and unquantified".

That is the same class of error as the project's own meta-lesson, one level up: I confirmed a path was
*connected* and called it *energised*. A continuity check is a **loop** question, never a path question.
`docs/AUDIT-2026-11-09-FOLLOWUP.md` is superseded on N-3 by this document.

The 6 November H-2 "follow-on" carries the identical error, so the open question recorded in
`docs/HANDOFF.md` §4.3 — "sense current now flows through the e-match continuously" — describes a
condition that does not exist. The real defect is the opposite and worse: **there is no working
continuity check at all, and the bench cannot fire.**

---

## 2. Claims verified, by audit

### 2.1 Both audits right, confirmed here (V)

| Finding | A | B | Evidence I reproduced |
|---|---|---|---|
| `D_RP1` series Schottky reversed | B-3 | B01 | `K_1`→`+12V_FUSED`, `A_2`→`+12V_PROT`; = my N-5 |
| Firing loop has no return | B-1 | B03 | §1 above |
| Continuity branch unexcited, across the load, reads the shunt when disarmed | B-2 | B04 | §1; `R_CONT1.1`/`U_CONT1.2` both on the match terminals |
| Station has no supply conductor; `PWR_FLAG` hides it from ERC | M-10 | B02 | `+12V_STN` ← `J_12V1.1` only; `J_UMB` 1–9 all signals, 10–12 GND |
| E-STOP drops K4 only; shunt stays open with ARM on | M-7 | B05 | `ESTOP_LOOP` → `K4.A2` only; `ARM_LINE` → `K1.A1`,`K3.A1` |
| ARM/FIRE adjacent on umbilical pins 1/2 | M-9 | B06 | `J_UMB1.1`=`ARM_LINE`, `.2`=`FIRE_LINE`, both boards |
| 6N137 RX path inverts the UART | M-2 | M02 | `RO_BENCH`→`R_ISO1`→`U_ISO1.2(A_2)`; LED conducts on RO high |
| Station has zero decoupling on its three bench-referenced rails | M-3 | B08 | only `C_USB1`, `C_V3` exist; = my N-2 |
| `ADC_CS` has no pull-up while `SD_CS` has one | §5 | M07 | `ADC_CS` = `MCU1.28`,`U_ADC1.2`; `SD_CS` includes `R_SDCS1.2` |
| `RS485_DE` unbiased at the bench; station biases its own | m-6 | M02 | `RS485_DE` = `MCU1.13`,`U_485.2`,`U_485.3`; station has `R_DE1`,`R_RE1` |
| Shield pin 12 tied to GND at **both** ends | m-9 | M03 | `J_UMB1.12` on GND, both boards |
| `THRUST_DIFF` has no source | m-2 | M08 | = my N-1 |
| Stale BOM: deleted continuity switch still listed | — | M10 | `generate_parts_list.py:102` still lists `S_CONT` SKRPABE010; `:220` "retained for the continuity check only" |
| Generators are machine-locked | §3 | M10 | absolute `OUT` paths in both; `ksch.py:4` `SYMDIR` pinned to `C:/Program Files/KiCad/10.0/...` |

Fourteen independent agreements, all reproducible. Treat this set as settled.

### 2.2 Audit A right, Audit B silent

- **M-12, `D_FIRE` sneak path.** `R_D_FIRE1` + `D_FIRE1` run from `PYRO_FIRE_OUT` to GND. Harmless today,
  but it becomes a return path to ground the moment any continuity source crosses K2 — the opto would
  conduct and the lamp would read "good" with **no match fitted**. Audit B's §3 raises the same risk as an
  objection to A's own fix without noticing A had already resolved it. A is right, and the fix (move the
  FIRING lamp to `FIRE_LINE`) is correct. **V (topology)**
- **The K3 fix is clean and costs nothing.** `K3.14` (NO) is currently unused and carries a no-connect
  flag. `COM = PYRO_MATCH_N, NC = PYRO_MATCH_P, NO = GND` gives: disarmed → match shorted *and* isolated
  from ground; armed → shunt open, low side grounded; fire → current through the NO contact (10 A rated)
  rather than the NC (6 A). Verified as a drop-in against `gen_bench.py:107-109`. **V**

### 2.3 Audit B right, Audit A silent

- **M07, firmware.** 20 SPS placeholder against the trade study's ≥ 1 kSPS target, raw counts labelled
  `thrust_N`, no sequence counter, synchronous SD writes, SD-init failure leaves the logger dead until
  reset. None of it touches arm/fire/E-STOP, but it decides whether a burn is recorded.
- **M01, the DevKitC supply conflict.** Espressif specifies USB / 5V pin / 3V3 pin as mutually exclusive.
  Plugging USB to flash while the bench battery is connected ties two 3.3 V regulators together. This
  will happen during bring-up. Audit A reaches the same place via its own M-6, but B names the mechanism.
- **N01 / M05 numeric work** — USB-C CC pull-downs coherent; the ADS1220 PGA common-mode inequality
  written out with both bounds; 8.25 kΩ divider source impedance.

### 2.4 Where I could not reproduce a claim, or the claim is wrong

| Claim | Source | My result |
|---|---|---|
| Netlist has **27** bench / **13** station no-connect pins; the handoff's 28/15 is wrong | A §4 | **A is wrong.** The exported netlists contain **28** and **15** `no_connect` pins. My original count stands; A's correction does not. |
| The standoff shortfall is an audit finding | A R-SD1, B M11 | **Already documented, not a discovery.** `SAFETY.md` H9 records it as "**Not mitigated.** Accepted deviation, logged as D-007", and `SAFETY.md:169` states "The 20 m configuration clears no class in this table." The repo flagged this before either audit. It still needs the review owner for the actual site — but as a logged deviation to close, not a defect found. |
| SD-detect **wiring** disagrees with the part | B M10 | **Wiring is correct**: `CARD1.10 (DET_A)` → `SD_DETECT`, `CARD1.9 (DET_B)` → GND. The defect is in the *note*, as A states. |
| `reach2.py` shows the match return reaching GND | A evidence bundle | A's own errata §9.5 withdraws this: the shipped script loops back through `PYRO_MATCH_P` and treats mutually exclusive contacts as simultaneously closed. The **finding** is unaffected — `PYRO_MATCH_N` has exactly three pins — but that evidence file should not be cited. |
| Audit B could not re-run native KiCad 10 ERC (local KiCad 9.0.2) | B §"What was checked" | Stated honestly by B. My ERC reports in `exports/2026-11-09/` are the only native KiCad 10 runs; B's connectivity conclusions agree with them. |

---

## 3. Two findings in neither audit

### 3.1 R-1 · Fixing the firing loop injects 6–12 A into the load-cell ground **V (topology) / A (current)**

This is the one that worries me most, because it is **created by the agreed fix for B-1**.

Both audits route the match return to `GND`. The bench has exactly one ground net, and these are among
its 43 members:

```
GND   R_EXC_N1.2        <- load-cell bridge excitation return (0 R link)
      U_ADC1.5 (AVSS)   <- ADS1220 analog ground
      U_ADC1.6, .7      <- AIN3/REFN1 and AIN2, tied to GND
      K1.A2, K2.A2, K3.A2   <- relay coil returns
      MCU1.1, .15, .38, .39 <- ESP32 grounds
      CARD1.6, .9, .SH      <- microSD ground and shield
      J_PWR1.2              <- battery negative
```

With the B-1 fix as written (`K3 NO → GND`), the **entire fire current returns through the same net that
carries the load-cell excitation return and the converter's AVSS** — during the burn, which is the only
moment the instrument exists to measure. At 12 V into a 1–2 Ω match that is roughly 6–12 A (**A**,
blocked on O-1) through shared copper, alongside a 24-bit converter resolving microvolts.

Two consequences, neither addressed:

1. **Measurement.** The ratiometric reference is taken at the board (`REFP0`/`REFN0` = `LC_EXC_P`/`LC_EXC_N`),
   so any IR shift in the excitation return appears directly as apparent thrust. Audit B's M05 identifies
   the lead-drop limitation of board-side reference sensing; neither audit connects it to the fire return.
2. **The logger surviving ignition.** `+3V3_LOGGER` is referenced to this same ground. A transient ground
   shift at ignition can brown out or reset the ESP32 at exactly the wrong instant — and the logger rail
   was deliberately placed upstream of K4 (D-047) so that an E-STOP could not corrupt the data file. That
   intent is defeated by a ground-borne reset.

Audit A's `m-10` does say "star ground: the fire return must not share copper with AVSS" — ranked
**Minor**, listed under ADC filtering, and not tied to B-1. That is too quiet for a consequence this
direct.

**Recommendation (D).** Make the pyro return a **distinct net at the schematic level**, not a layout
intention: `PYRO_RTN` from `K3` NO to the battery negative terminal, joined to `GND` at a single defined
star point at `J_PWR`. Then the fire loop shares no copper with AVSS, and the star point is drawn rather
than left to the layout engineer. This belongs in the same review as B-1, because it changes the fix.

### 3.2 R-2 · `validate_sch.py` reports a byte-identical "0 errors" when it checks nothing **V (reproduced)**

Audit B notes the Windows symbol path in passing. It is worse than a portability nuisance, and this is
the mechanism that let twelve faults survive a "clean" validator.

`ksch.py:4` pins `SYMDIR = "C:/Program Files/KiCad/10.0/share/kicad/symbols"`. `validate_sch.py` resolves
symbols through it in two places, each wrapped identically:

```python
try:
    _d, lpins = ksch.get_symbol(lid)        # line 111
except Exception:
    continue
```
```python
try:
    libname, symname = lid.split(":")
    flat = ksch._flatten(ksch.load_lib(libname), symname)   # line 193
except Exception:
    continue
```

Those two blocks are the **exact pin-coincidence check, the floating-pin check and the power-pin semantic
check** — the three guards added after the `GND_RTN` split, the AMS1117 pin-1 error and the SP3485 with no
ground. Run on this machine, I get:

```
SYMDIR correcto             -> ([], ['nets appearing once: THRUST_DIFF_N, THRUST_DIFF_P'], {...})
SYMDIR roto (otra maquina)  -> ([], ['nets appearing once: THRUST_DIFF_N, THRUST_DIFF_P'], {...})
```

**Identical output.** Net resolution from labels and wires still runs, so the tool looks alive and still
finds `THRUST_DIFF` — while every symbol-dependent structural check has silently vanished. There is no
warning, no changed exit code, no dropped count. A KiCad point upgrade from `10.0` to `10.1` is enough to
disable it, permanently and invisibly, on the machine that produced every "0 errors" in this project's
history.

**Recommendation.** Fail loudly instead of continuing: count resolution failures, and make any non-zero
count an **error** that names the unresolved `lib_id`s and the `SYMDIR` tried. Resolve `SYMDIR` from the
`KICAD*_SYMBOL_DIR` environment variable or by globbing `*/share/kicad/symbols`, with the hardcoded path
as a last resort. Make the `OUT` paths in both generators relative. One afternoon's work, and it is a
precondition for trusting any future "clean" result — including the result that will be used to close the
Rev A.1 redraw.

---

## 4. Where the two proposals genuinely disagree — for Emilio

Everything else converges. Three items are real decisions, and both audits say so.

| # | Question | Audit A | Audit B | My reading |
|---|---|---|---|---|
| **D-A** | Shunt and low-side return: one relay or two? | **K3 does both** on one Form C pole. Break-before-make makes the shunt-across-a-live-source failure impossible by construction; two relays reintroduce it. Zero added parts. | **Keep them separate** so the two failures can be evaluated independently; one mechanism owning two safety functions resists analysis. | Both arguments are sound and they trade different failure modes. A's is the stronger *electrical* argument; B's is the stronger *review* argument. A's depends on one unverified fact — that the Songle SRD changeover is genuinely break-before-make (**A**, neither audit obtained it). **Get that evidence first; it decides the question.** |
| **D-B** | Continuity: pre-arm TEST, or armed-state? | **Pre-arm momentary TEST** energising K3 only, keeping `REQUIREMENTS.md` as written. | Same conclusion: preserve the pre-arm requirement, with firing positively inhibited through entry and exit. | Agreed between them. One hazard neither states: **any** continuity test must open the shunt, so for the duration of the test the H2 induced-energy defence on a 20 m loop is absent. TEST must therefore be **momentary only, never latching**, with personnel already clear — an accepted hazard to write down, not a defect. |
| **D-C** | Reverse polarity | Delete `D_RP`; **crowbar diode** after F1 plus a keyed battery connector, so no series element sits in the fire path. | Correct the polarity, then qualify the input protection properly; a Schottky surge rating does not cover the real fault. | A's crowbar is the better answer and B's caution is the right constraint. Note a side benefit neither mentions: with `D_RP` gone, `VBAT_SENSE` reads the true battery rail instead of a post-diode one, which closes B's M09 objection about transferring a battery-terminal threshold to a post-diode measurement. Crowbar/fuse I²t coordination stays open (O-17). |

---

## 5. Consolidated state

| | Count | Notes |
|---|---|---|
| Blockers, agreed and verified | **4** | reversed `D_RP`; open firing loop; dead continuity circuit; station supply undefined |
| Major safety findings, agreed and verified | **3** | E-STOP leaves the shunt open; single-conductor E-STOP defeat; ARM/FIRE adjacency |
| New here | **2** | R-1 fire current in the analog ground; R-2 validator passes vacuously |
| Superseded of mine | **1** | N-3 / H-2 "permanent sense current" — withdrawn, §1 |
| Still blocked on data | **2** | O-1 e-match, O-2 load cell |
| Decisions for Emilio | **3** | D-A, D-B, D-C above, plus the station-power and E-STOP architecture |

**Gate 2 is not met and Gate 4 must not start.** Four blockers, three of them in the arm/fire/continuity
path, and the measurement return question (R-1) changes the agreed fix for one of them.

### Order I would work in

1. **R-2 first** — one afternoon, and nothing downstream is trustworthy without it. Fixing the validator
   before redrawing means the redraw can actually be checked.
2. **Ask Ignitia for O-1 and O-2.** O-1 gates every pyro value and the D-A contact-rating margin.
3. **Get the Songle break-before-make evidence.** It decides D-A, which decides the K3 topology, which
   decides the generator rewrite.
4. **Put D-A, D-B, D-C, station power and E-STOP architecture to Emilio in one review** — they are coupled
   through the harness and the relay count, exactly as Audit B argues.
5. **Then redraw**, with R-1 settled as a drawn `PYRO_RTN` net rather than a layout note.
6. Mechanical corrections any time: `PWR_FLAG` on `+12V_LOGGER`, `ADC_CS` pull-up, `RS485_DE` pull-down,
   `D_FIRE` to `FIRE_LINE`, SD-detect note, stale `S_CONT` BOM entry, relative generator paths.

Nothing in this document approves a circuit. Items 2–6 all terminate in a decision that is Emilio's.
