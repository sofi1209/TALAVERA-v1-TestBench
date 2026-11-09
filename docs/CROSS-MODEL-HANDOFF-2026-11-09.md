# Cross-model handoff — independent audit request, TALAVERA v1

*Paste the block below into the reviewing model. It is self-contained: the reviewer has no access to
the repository, the session or the files. Attach `exports/2026-11-09/talavera-bench-schematic.pdf`,
`talavera-station-schematic.pdf`, and the two `.net` netlists if the model accepts attachments.*

*Redaction applied: no absolute paths, no credentials, no personal names. The repository URL is public
and is the only identity-revealing item — strip the "Repository" line if you would rather not share it.*

---

## 1. Goal

Independently audit the two schematics of a **solid-rocket-motor static test bench control system**
before any PCB layout begins, and say whether the design is electrically correct — not merely
connected. A prior audit plus two automated checkers already passed this revision, and a blocker was
still found afterwards; I want a fresh pair of eyes that has not seen either audit.

## 2. Context

- **What it is:** replacement electronics for a university rocketry lab's static test bench, which
  fires a solid motor on a thrust stand while logging load-cell data. Two boards joined by one
  12-conductor umbilical: `talavera-bench` at the stand, `talavera-station` at the operator position
  ~20 m away.
- **The governing safety principle, which must not change:** *no microcontroller takes part in arming,
  firing or emergency stop.* Those three functions are relay contacts, panel switches and a shorting
  plug inserted by hand. The ESP32 logger has **no authority over any output** — it reads a load cell
  and writes an SD card. Any suggestion that moves arming, firing or E-STOP under firmware control is
  out of scope and should be rejected, not evaluated.
- **Design state:** Gate 2 of 7 (schematic). No layout exists. Rev A will be a bare PCB, hand
  assembled. Fabrication release and any live-initiator testing require the review owner's written
  sign-off, which has not been given.
- **Tooling:** KiCad 10.0.5 on Windows. The `.kicad_sch` files are **generated** by Python
  (`hardware/tools/gen_bench.py`, `gen_station.py`, on a helper `ksch.py`) — they are never hand-edited,
  so every fix is a change to a generator, and the schematic files declare
  `(generator_version "9.99")`, which is not a real release.
- **Key parts:** ESP32-DevKitC V4 (socketed), ADS1220 24-bit ADC over SPI, four SRD-12VDC-SL-C SPDT
  relays, SP3485 RS-485 transceiver, 6N137 optocouplers, AMS1117 linear regulators, 12 V 2.6 Ah SLA
  battery. An AD620 instrumentation amp and a 5 V rail exist as a DNP alternative analogue path.
- **Repository:** https://github.com/sofi1209/TALAVERA-v1-TestBench (public)

## 3. Problem / what was observed

Three extractions were run on the committed revision: the project's own `validate_sch.py`, its own
`netlist.py`, and KiCad's `kicad-cli sch erc` + `sch export netlist`.

| Tool | bench | station |
|---|---|---|
| `validate_sch.py` | 0 errors, 1 warning | 0 errors, 0 warnings |
| `netlist.py` | exit 0 | exit 0 |
| `kicad-cli sch erc` | **1 error, 2 warnings** | 0 errors, 0 warnings |

The project's documentation recorded this revision as **ERC-clean with 0 errors**. That claim was not
reproducible, because KiCad's ERC had apparently never been run on the bench board — the only ERC
reports in version control are station-only, warnings-only runs. Chasing the single real ERC error led
to a blocker that a completed hand audit had missed.

**History that matters for calibration:** an audit on 6 November found **12 faults in a revision that
both automated checkers called clean**, including a 3.3 V rail split into two unconnected nets (no IC
had power), a load-cell bridge with no excitation, and **five reversed relay flyback diodes**. Ten were
fixed. The project's own handoff notes that diode polarity is the one fault class with no automated
guard. The blocker below is a **sixth reversed diode**, in a different category, which is why the sweep
that caught the five missed it.

## 4. Relevant code and netlist evidence

**The blocker — `gen_bench.py:34-37`:**

```python
d1 = s.place(SCH, "D_RP", "SS24", 95, 35, angle=90)   # SCH = "Device:D_Schottky"
s.stub(d1['1'], "+12V_FUSED", 3)
s.stub(d1['2'], "+12V_PROT", 3)
s.text("reverse-polarity block", 88, 42, 1.3, False)
```

KiCad's own netlist export, authoritative on pin function (`pin "1"` = cathode, `pin "2"` = anode):

```
(net (code "3") (name "/+12V_FUSED")
  (node (ref "D_RP1") (pin "1") (pinfunction "K_1") (pintype "passive"))
  (node (ref "F1")    (pin "2")                     (pintype "passive")))

(net (code "4") (name "/+12V_PROT")
  (node (ref "D_RP1") (pin "2") (pinfunction "A_2") (pintype "passive"))
  (node (ref "F2")    (pin "1")                     (pintype "passive"))
  (node (ref "K4")    (pin "11") …) …)
```

Supply chain: `J_PWR.1 → +12V_RAW → F1 → +12V_FUSED → D_RP → +12V_PROT → F2 → +12V_LOGGER → AMS1117`.
A series Schottky with its **cathode toward the battery** is reverse-biased in normal polarity, so
nothing downstream of `+12V_FUSED` is powered — logger rail, master relay, safety chain, regulators.

**The ERC error:**

```
[power_pin_not_driven]: Input Power pin not driven by any Output Power pins ; error
    @(100.33 mm, 80.01 mm): Symbol U_3V3 Pin 3 [VI, Power input, Line]
```

`gen_bench.py:39-40` flags only `+12V_RAW` and `GND`; ERC does not propagate a source through passives,
and `+12V_LOGGER` sits behind fuse `F2`.

**Unsourced differential pair** (all three tools flag it):

```
bench     THRUST_DIFF_P  J_UMB1.8   <- nothing else      THRUST_DIFF_N  J_UMB1.9   <- nothing else
station   THRUST_DIFF_P  J_DAQ1.1, J_UMB1.8              THRUST_DIFF_N  J_DAQ1.2, J_UMB1.9
```

**Station board capacitance, complete list** (bench has `C1`–`C10`; station has these two):

```
+5V_USB    C_USB1.1          USB_V3   C_V3.1
+12V_STN   (no capacitor)    +5V_BENCH  (no capacitor)    +3V3_BENCH  (no capacitor)
```

`+3V3_BENCH` is an AMS1117 output feeding `U_485.8(VCC)`; `+5V_BENCH` is an AMS1117 output feeding the
next regulator's input.

**Continuity sense path, bench** (`R_CONT` value is still unknown — see §7):

```
PYRO_MATCH_P  J_ARM1.2, K3.11, P1.1, R_CONT1.1
CONT_LED_A    R_CONT1.2, U_CONT1.1        (6N137 LED anode)
PYRO_MATCH_N  K3.12, P1.2, U_CONT1.2
```

K3 is a relay wired **normally-closed** so that de-energised = igniter shorted. `P1` is the hand-inserted
shorting plug.

## 5. Acceptance criteria

1. `kicad-cli sch erc` returns 0 errors on both boards, with every remaining warning individually
   justified in writing.
2. Every diode in both designs is verified by **pin function from the exported netlist**, not by
   category or by symbol appearance: series blocking diodes anode-to-source, flybacks cathode-to-coil-positive.
3. Every rail that feeds a `power_in` pin has a power source or `PWR_FLAG`.
4. Each regulator meets its datasheet stability requirement for input and output capacitance.
5. The arming / firing / E-STOP path contains no semiconductor under firmware control, and every
   relay's de-energised state is the safe state.
6. Every component value is labelled **verified** (with datasheet or manual page) or **assumed**.

## 6. Evidence

**Verified** (reproduced this session):
- Generators reproduce the committed schematics exactly — the regeneration diff is 2,934 lines of which
  **zero** carry electrical content; the remainder are sheet UUIDs. So all findings apply to what is in
  version control.
- Tool results in the table in §3.
- `D_RP` pin functions, from KiCad's own export, quoted verbatim in §4.
- Ten fixes from the 6 November audit re-checked against the netlist and all holding: single 3.3 V rail
  carrying all five IC supply pins; bridge excitation links present; all four relay flybacks
  cathode-to-positive; buzzer flyback correct; gate divider present; continuity lamp now lit = good
  match; false-pass test button removed; ESD parts now `D_TVS`; `R_ISO1` = 220 R; 28 no-connect flags on
  the bench and 15 on the station.

**Assumed** (needs a datasheet — do not treat as fact):
- AMS1117 output capacitor requirement and maximum junction temperature (~125 °C).
- NTS4001NT1G V<sub>GS(max)</sub>, against a 4.86 V divider output from a 12 V rail.
- 6N137 minimum forward current for guaranteed switching (~5 mA), against 8.18 mA at 220 Ω.
- 55 °C ambient inside the enclosure.
- Logger current draw ~150 mA with radios off and the SD card writing.

**Not checked:** layout and DRC (none exists); firmware (never compiled, ADS1220 register values are
placeholders); all pyrotechnic and analogue component values (blocked, see §7).

## 7. Unresolved problems

- **Two missing data items block every pyrotechnic and analogue value.** The e-match part and its
  no-fire / all-fire current and resistance are unknown, so the continuity sense resistor, the fuse
  rating, the relay contact ratings and the pyro trace width are all `TBD`. The load cell's make,
  bridge resistance, mV/V and rated excitation are unknown, so the ADC gain and reference strategy are
  unsettled. **Do not invent either.** Flag anything that depends on them.
- **Sense current crosses the initiator permanently.** The path in §4 is ungated, so it is live whenever
  the bench is powered, including with the shunt relay closed. Whether that is acceptable depends on the
  no-fire current, which is unknown. This is a pyrotechnic question reserved for the review owner —
  **analyse it, state the risk, but do not declare it safe or approved.**
- **Thermal, undecided:** the bench drops 12 V → 3.3 V in one AMS1117 in SOT-223, roughly 1.3 W at
  150 mA, which computes to about 133 °C junction at 60 °C/W and 55 °C ambient, against a ~125 °C limit.
  The station already cascades 12 → 5 → 3.3; the bench does not. Cascade, or add a switching
  pre-regulator and keep an LDO for the final step to preserve ripple rejection for the analogue front
  end?
- **Representation mismatch:** the sheet draws a bare 38-pin ESP32-WROOM-32D, but the build sockets a
  DevKitC V4 that carries its own regulator, EN network and USB bridge, and whose header does not expose
  nine of the drawn pins. The schematic does not represent what will be built.
- **Unknown design intent** for the `THRUST_DIFF` pair in §4.

## 8. Review request

Please check, in this order:

1. **Every diode and every polarised part, by pin function.** One series diode was found reversed after
   five flybacks had already been found reversed. Assume the sweep was incomplete and redo it: diodes,
   electrolytic and tantalum capacitors, the optocouplers, the TVS parts, the relay coil connections.
2. **Power integrity:** rail-by-rail source, current budget, regulator headroom and dissipation,
   startup and sequencing, and the missing station decoupling — tell me what breaks and what merely
   violates the datasheet.
3. **The safety chain, as drawn:** confirm that arming, firing and E-STOP depend on no semiconductor
   under firmware control, that every relay's de-energised state is the safe state, and that no single
   failure of the logger can energise the pyro channel. **Report your assessment; do not sign it off.**
4. **The measurement path:** bridge excitation, the ADS1220 reference and common-mode range, and whether
   the DNP AD620 alternative path is wired coherently.
5. **Anything the three tools and two audits cannot see** — a connected, legal, wrong circuit. That is
   the failure mode this design keeps producing.

**Format for findings:** one table, most severe first. Columns: ID, severity (blocker / major / minor /
note), location (reference designator, net, or file and line), evidence, why it is wrong, recommended
fix, and **verified or assumed**. Flag anything needing a datasheet I have not supplied rather than
filling in a plausible number. If you believe a finding is a judgement call, say so instead of ranking
it.
