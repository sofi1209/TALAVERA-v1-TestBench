# TALAVERA v1 — Follow-up audit, 9 November 2026

**Scope:** the committed revision of both schematics (commit `43e9803`, unchanged by this session).
**Method:** generators re-run to prove they reproduce the committed files, then the design examined from
**three independent extractions** — the project's own `hardware/tools/netlist.py`, KiCad's own
`kicad-cli sch export netlist`, and `kicad-cli sch erc`.

**Why this pass exists.** `docs/AUDIT-2026-11-06.md` and `docs/HANDOFF.md` both record the audited
revision as passing ERC with **0 errors**. That is **not reproducible**. KiCad 10.0.5 reports
**1 error and 2 warnings** on `talavera-bench`. Running the tool that had never actually been run on
this board surfaced one blocker.

Findings are labelled **V** (verified in the supplied files, with the extraction named) or
**A** (assumption that still needs a datasheet).

---

## Reproduction

```bash
cd hardware/tools && python gen_bench.py && python gen_station.py
```

The regenerated files differ from the committed ones by **sheet UUIDs only** — 2,934 diff lines, of
which zero carry electrical content. Verified by filtering the diff for any line that is not a `uuid`
or `(path "/…")` field: the result is empty. **The generators are faithful to the committed
schematics**, so every finding below applies to what is in version control. The regenerated files were
then reverted, because keeping them desynchronises the `sheets` UUID in each `.kicad_pro` and gains
nothing.

| Tool | talavera-bench | talavera-station |
|---|---|---|
| `validate_sch.py` | 0 errors, 1 warning | 0 errors, 0 warnings |
| `netlist.py` | exit 0 | exit 0 |
| `kicad-cli sch erc` (10.0.5) | **1 error, 2 warnings** | 0 errors, 0 warnings |

Artefacts for this revision are in `exports/2026-11-09/`: schematic PDFs and ERC reports are committed;
the `.net` and `.xml` netlists are generated on demand and gitignored by project policy.

**Tooling note (V).** The schematic files declare `(generator_version "9.99")`, written by `ksch.py`.
The installed toolchain is **10.0.5**. The files load and export correctly, but the declared version is
not a release that exists.

---

## Blocker

### N-5 · The reverse-polarity diode is reversed — the bench board receives no power **V**

`hardware/tools/gen_bench.py:34-37`

```python
d1 = s.place(SCH, "D_RP", "SS24", 95, 35, angle=90)
s.stub(d1['1'], "+12V_FUSED", 3)
s.stub(d1['2'], "+12V_PROT", 3)
s.text("reverse-polarity block", 88, 42, 1.3, False)
```

`D_RP` is a `Device:D_Schottky` (SS24) in **series** in the supply path — the generator's own annotation
says `reverse-polarity block`. Pin 1 is the cathode, pin 2 the anode. From KiCad's own netlist export,
which is authoritative on pin function:

```
(net (code "3") (name "/+12V_FUSED")
  (node (ref "D_RP1") (pin "1") (pinfunction "K_1") (pintype "passive"))
  (node (ref "F1")    (pin "2")                     (pintype "passive")))

(net (code "4") (name "/+12V_PROT")
  (node (ref "D_RP1") (pin "2") (pinfunction "A_2") (pintype "passive"))
  (node (ref "F2")    (pin "1")                     (pintype "passive")) …)
```

The supply chain is `J_PWR.1 → +12V_RAW → F1 → +12V_FUSED → D_RP → +12V_PROT → F2 → +12V_LOGGER`. The
**cathode faces the battery and the anode faces the load**, so in normal polarity the diode is
reverse-biased and conducts nothing. Nothing downstream of `+12V_FUSED` is powered: not the logger
rail, not the master relay K4, not the safety chain, not the 3.3 V regulator.

Correct for a series blocking diode is anode on the input, cathode on the output — swap the two stubs:

```python
s.stub(d1['2'], "+12V_FUSED", 3)   # A to the incoming supply
s.stub(d1['1'], "+12V_PROT", 3)    # K to the protected rail
```

**This is the sixth reversed diode in this project** — five flyback diodes were caught on 6 November,
and `docs/HANDOFF.md` records diode polarity as the one class of fault with *no* automated guard:
*"Nothing automatic. Check every diode by hand."* `D_RP` is not a flyback, so it fell outside the sweep
that caught the other five. The polarity check must cover **every** diode in the design, by pin
function from the exported netlist, not by category.

Not a safety circuit — it fails safe, by denying power to everything. But the board is dead on first
power-up, and the symptom (nothing works at all) invites the operator to suspect the battery, the fuse
or the connector first.

---

## Major

### N-1 · `THRUST_DIFF_P/N` has no source on the bench **V**

Reported independently by all three tools — `validate_sch.py` ("nets appearing once"), `netlist.py`
("SINGLE NODE"), and KiCad ERC (`isolated_pin_label`, 2 warnings).

```
bench     THRUST_DIFF_P   J_UMB1.8(Pin_8)     <- nothing else
          THRUST_DIFF_N   J_UMB1.9(Pin_9)     <- nothing else
station   THRUST_DIFF_P   J_DAQ1.1, J_UMB1.8
          THRUST_DIFF_N   J_DAQ1.2, J_UMB1.9
```

Two conductors of the 12-way umbilical carry a differential thrust pair to the operator's DAQ connector,
and on the bench side they terminate on the umbilical connector and nothing else. Either an analogue
path independent of the ESP32 was intended — in which case the bench end belongs on `LC_SIG_P/N`, and
loading the bridge with the DAQ input needs thinking about — or the pair is vestigial and two umbilical
conductors are free. **Design intent required; not resolvable from the files.**

### N-2 · The station board has no decoupling on any of its own rails **V**

From `netlist.py` and confirmed in the KiCad export. The station's three supplies carry no input or
output capacitance whatsoever:

```
+12V_STN     J_12V1.1, J_ARMSW1.1, LS1.1(+), R_CONT_PU1.1, R_D_CONT1.1,
             R_D_PWR1.1, D_BUZZ1.1(K), U_5VB1.3(VI)        <- no C
+5V_BENCH    U_5VB1.2(VO), U_3V3B1.3(VI), …                <- no C
+3V3_BENCH   U_3V3B1.2(VO), U_485.8(VCC)                   <- no C
```

The only capacitors on the board are `C_USB` on `+5V_USB` and `C_V3` on the CH340's internal regulator
output. By contrast the bench carries `C1`–`C10`.

Consequences: the AMS1117 is **not unconditionally stable without an output capacitor** (**A** — value
and ESR requirement need the datasheet; the part's typical application calls for ~22 µF on the output),
`U_485` has no supply decoupling at all while switching an RS-485 line, and the buzzer's inductive
switching shares an undecoupled `+12V_STN` with the continuity pull-up `R_CONT_PU` — the node the
operator's continuity lamp reads.

### N-4 · `+12V_LOGGER` has no power source flag — the one real ERC error **V**

```
[power_pin_not_driven]: Input Power pin not driven by any Output Power pins
    ; error
    @(100.33 mm, 80.01 mm): Symbol U_3V3 Pin 3 [VI, Power input, Line]
```

`gen_bench.py:39-40` places `PWR_FLAG` on `+12V_RAW` and `GND` only. ERC does not propagate a power
source through passives, so each rail that feeds a `power_in` pin needs its own driver. `+12V_LOGGER`
feeds `U_3V3.3(VI)` and `U_5V.3(VI)` through fuse `F2` and has neither a flag nor a power-output pin.

One line fixes it: `s.pwr_flag("+12V_LOGGER", x, y)`.

This finding matters less for what it is than for what it means: **nobody had run `kicad-cli sch erc`
on the bench board.** The only committed ERC reports are `hardware/talavera-station/ERC.rpt` and
`ERC-run2.rpt` — station only, and warnings-only runs. The "ERC clean" claim in the 6 November audit
rested on `validate_sch.py`, which is a different and narrower check.

---

## Note

### N-3 · H-2 confirmed electrically: sense current through the e-match is permanent **V**

```
PYRO_MATCH_P   J_ARM1.2, K3.11, P1.1, R_CONT1.1
CONT_LED_A     R_CONT1.2, U_CONT1.1          <- opto LED anode
PYRO_MATCH_N   K3.12, P1.2, U_CONT1.2
```

`R_CONT` is still `TBD O-1`. The path `PYRO_MATCH_P → R_CONT → opto LED → PYRO_MATCH_N` is unbroken and
ungated, so sense current crosses the initiator whenever the bench is powered, including with K3's
shunt closed. The margin against the e-match no-fire current **cannot be assessed until O-1 arrives.**
This is the open pyrotechnic question behind H-2 and it is **for the review owner, not for this
document.** No pyrotechnic circuit is marked reviewed or approved here.

---

## Status of the 6 November findings

All ten claimed fixes were re-verified against the netlist rather than against the audit text, and all
ten hold: C-1 (single `+3V3_LOGGER` carrying all five IC supply pins), C-2 (`R_EXC_P/N` links to rail
and ground), C-3 (all four relay flybacks cathode-to-positive), C-4 (buzzer flyback), C-5 (10 k/6 k8
divider present — V<sub>GS(max)</sub> still **A**), H-1 (lamp lit = good match), H-2 (button gone),
H-3 (`D_TVS`), M-3 (`R_ISO1` = 220 R — minimum I<sub>F</sub> still **A**), M-4 (28 no-connect flags on
the bench, 15 on the station).

Still open and unchanged: **M-1** (AMS1117 thermal), **M-2** (DevKitC vs bare module), and the **H-2**
design question. **O-1** and **O-2** are still outstanding and still block every pyrotechnic and
analogue value.

---

## Recommendation

**Still do not progress to layout, and the reason is now stronger.** N-5 alone makes the board
non-functional, and it was missed by a completed audit, by the project's own validator and by two
reviewers' reading of the netlist — because nobody ran KiCad's ERC on the bench board.

Order of work: N-5 and N-4 are mechanical corrections with a single right answer. N-2 needs the AMS1117
datasheet. N-1 needs a design decision. Then `kicad-cli sch erc` belongs in the regeneration routine
in `docs/HANDOFF.md`, alongside `validate_sch.py`, as a required step rather than an optional one.

## What this follow-up did not cover

- **Layout and DRC** — no layout exists (Gate 4).
- **Pyro and analogue values** — blocked on O-1 and O-2.
- **Firmware** — not compiled; ADS1220 register values are still placeholders.
- **Datasheet confirmation** for the AMS1117 output capacitor, the NTS4001NT1G V<sub>GS(max)</sub>, and
  the 6N137 minimum I<sub>F</sub>. All three remain **A**.
