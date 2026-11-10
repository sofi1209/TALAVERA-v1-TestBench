# TALAVERA v1 — Batch 2: safety topology, Rev A.2, 10 November 2026

**Baseline:** `main` at `0b3d582` (Rev A.1) · **Review owner:** Emilio Guadarrama
**Status: DRAWN AND CHECKED FOR CONNECTIVITY. NOTHING IS APPROVED. NOTHING IS VERIFIED SAFE.**

The six safety-topology problems from the Rev A.1 audit round were analysed, options put to the author,
and the recommended set drawn in the generators. A clean validator, a clean ERC and a passing tracer
mean **connected as intended**, not safe. Every item in §8 needs Emilio's written sign-off. Gate 6
(fabrication release) and bring-up Stage 5 (live e-match) keep mandatory written sign-off.

| Batch 2 ID | Repo IDs | Problem | Drawn option |
|---|---|---|---|
| P-01 | D-B, H10, H11 | No working continuity check | Station TEST energising K3 only; test current from K1's NC; two series resistors; active-high sense |
| P-02 | D-A, D-065 | K3 owns shunt and return; K2 weld fired on ARM | K3 keeps both contacts, **coil moved from ARM to the FIRE command** |
| P-03 | M-9, B06 | ARM and FIRE adjacent; an ARM/FIRE short fired on ARM | **Floating two-wire FIRE loop**, double-pole FIRE button, new pin map |
| P-04 | M-7, M-8, B05, D-073 | E-STOP dropped K4 only; shunt stayed open; single channel | **Second E-STOP channel** in the ARM feed, plus a **latched ARM permit** (K5) |
| P-05 | D-C, D-064 | Series SS24 (2 A class) in the 6–12 A fire path | **Crowbar diode after F1** plus a keyed battery connector |
| P-06 | D1, D-067 | Station power | **Keep the separate station feed**; no supply conductor in the umbilical |

---

## 1. Method

1. Read the five Rev A.1 records and the generators' fire path; exported fresh netlists from `main`.
2. Obtained the relay datasheet linked from the LCSC page for C30431 (§2).
3. Wrote a DC single-short model of the umbilical: every pair of conductors shorted, in every operating
   state, solving the coil voltage on each relay and judging it **only** against the datasheet limits.
   Run first on the Rev A.1 design, then on candidate designs.
4. Drew the chosen set, then ported the model into `trace_fire_loop.py` (section 7) so it runs from
   **both KiCad netlists** rather than from a hand-transcribed model.
5. Self-tested the tracer against two deliberately broken designs (§6.3).

## 2. Relay data in hand, and what it does not settle

The datasheet LCSC links for C30431 is **Sanyou-branded "SRD-Series version V3.2"**, while the part is
listed as **Songle** `SRD-12VDC-SL-C`, and that ordering code does not appear in the datasheet's own
nomenclature. **Provenance is open (O-24).** Values from it, treated as unverified for our exact part:

| Parameter | Datasheet | Consequence |
|---|---|---|
| Contacts, DC | 10 A NO / 6 A NC at 28 VDC (UL general use); 7 A 28 VDC (TÜV) | First real number for the contact margin. Fire current still unknown (O-1) |
| Pick-up voltage | **max** 75 % → guaranteed ON at ≥ 9.0 V | No minimum is given |
| Drop-out voltage | **min** 5 % → guaranteed OFF only at ≤ 0.6 V | A held relay may stay in at any voltage above 0.6 V |
| Operate / release | 8 ms / 5 ms max, **without** a coil diode | Ours have diodes; real release is longer, unmeasured |
| Contact form | "Form C" | **Break-before-make is not stated.** Form C conventionally means it; the maker does not say so (O-3) |

Between 0.6 V and 9 V the datasheet guarantees **neither** state. Every result below in that band is
marked **??** and closes only by measuring must-operate and must-release voltages on real units (O-22).

## 3. Rev A.1 single faults that fired without a FIRE press

From `trace_fire_loop.py` section 7 run on the `main` netlists (flyback diodes included):

| Fault | When | Result |
|---|---|---|
| ARM↔FIRE short (pins 1/2, adjacent) | on ARM | **Fires** — all four coils ≥ 9 V |
| K2 contact welded | on ARM | **Fires** — ARM closed K1 and K3 together |
| FIRE button stuck | on ARM | **Fires** |
| FIRE↔CONT_SENSE, FIRE↔RS485_A/B | ARMED | **May fire (??)** |
| FIRE↔ESTOP (pins 2/3, adjacent) | E-STOP pressed while ARMED | **May fire (??)**: K4 7.0 V, K2 held in the ?? band |
| ESTOP↔GND or shield chafe; ESTOP↔RS485_B | E-STOP pressed during a burn | **Burn continues** — K4 held at 12.0 V / 10.1 V |
| K4 weld, E-STOP contact weld | any | E-STOP lost — one channel |
| Latched E-STOP released with key ON | after an E-STOP | Re-arms at once; with FIRE stuck it fires on release |

No single umbilical short fired from SAFE, because no conductor carries supply until the key is turned.
That property is kept (P-06).

## 4. Options and decisions, per problem

### P-02 — K3: coil moved to the FIRE command (option C)

| Option | For | Against |
|---|---|---|
| A. As drawn in A.1, coil on ARM | Zero parts | **K2 weld fires on ARM.** Shunt open for the whole armed wait |
| B. Two relays (Audit B) | Independent welds | NC weld + FIRE dead-shorts the battery; shunt reclosure becomes an inter-relay race |
| **C. One Form C pole, coil on FIRE** | Zero parts. K2 weld alone or K3 weld alone **cannot fire**. Shunt closed and isolated through ARMED (H2). NC only ever closes onto an isolated MATCH_N | Under make-before-break K3 bridges at **every** fire — contact stress and weld risk, not ignition |

The coil floats on `K3_COIL`/`FIRE_N`, fed from `FIRE_P` through `D_K3F` or from `TEST_LINE` through
`D_K3T`. A ground-returned K3 was drawn first and **rejected**: an ARM↔FIRE_N short (adjacent pins 2/3)
then forward-biases `D_K2` and `D_K3F` and pulls K3 in while ARMED — shunt open, one K2 weld from firing.
The tracer reproduces that as a gated failure (§6.3).

### P-01 — continuity TEST (option A)

Station key OFF feeds a momentary TEST button; `TEST_LINE` energises **K3 only**. The test current comes
from **K1's NC contact** (`CONT_SRC`), so it mechanically cannot exist while `ARM_BUS` is live:

```
CONT_SRC -> R_TEST1 -> R_TEST2 -> opto LED -> D_CBLK -> MATCH_P -> match -> MATCH_N -> K3 NO -> PYRO_RTN
```

Two series resistors so one short-failed resistor cannot exceed no-fire — **each alone must be
sufficient** (values blocked, O-1). The sense is **active-high**, sourced from `CONT_SRC`, so a
sense-line short to ground reads "no match" and the lamp cannot light while armed. The old `R_CONT`
in parallel with the match, which took the full rail after a burn-through, is deleted.
**H10 stands:** the shunt is open while TEST is held. Momentary only; personnel clear.

Rejected: B, a bench TEST button (shunt open with a person at the bench); C, an off-board handheld
tester only (no remote check after the plug goes in).

### P-03 — floating FIRE loop and pin map (option D)

K2 (and K3) coils float between `FIRE_P` and `FIRE_N`; the station FIRE button is double-pole
(`ARM_LINE→FIRE_P`, `FIRE_N→GND`). A single short of either FIRE wire to ARM or ground, or one welded
button pole, cannot energise the coil. The `D_FIRE` lamp sits across the pair, not to ground.

Pin map, single source of truth in `hardware/tools/umbilical.py`:

`1 FIRE_P · 2 FIRE_N · 3 ARM · 4 GND · 5 RS485_A · 6 RS485_B · 7 GND · 8 CONT · 9 VBAT · 10 ESTOP · 11 TEST · 12 shield`

Chosen so no adjacent pair is gated in the short matrix. **Adjacency is assumed linear with 12 next to 1;
the connector and cable lay-up are unknown (O-23).** All 12 conductors are used, so path 2 (D-069)
cannot return without a larger cable. `FIRE_P`/`FIRE_N` must be a twisted pair.

Rejected: A, re-pin with GND guards (ESTOP next to a guard defeats channel 1); B, FIRE as the coil low
side (a chafe to the shield then fires on ARM).

### P-04 — two-channel E-STOP and latched ARM permit (A + C)

- **Channel 1** (unchanged): E-STOP block 1 holds bench K4 through `ESTOP_LOOP`.
- **Channel 2** (new): E-STOP block 2 feeds `ESTOP_OK`, which feeds the permit. Removing it removes
  `ARM_LINE` and the FIRE command, so K1, K2 and K3 drop and **the shunt re-closes** (M-7 closed in
  topology).
- **K5 permit** (same SRD part) self-holds from `ESTOP_OK`. It sets only through RESET, and RESET is
  enabled only with E-STOP released, the FIRE NC auxiliary closed (actuator released) and the key OFF.
  Releasing a latched E-STOP, or restoring station power, does **not** re-arm the bench. A welded K5
  loses only this anti-restart property.

Required panel parts (not chosen, O-25): E-STOP with **two positive-opening NC blocks**, a **three-pole**
key (changeover + two closed-in-OFF), FIRE with **2 NO + 1 NC**, TEST and RESET momentaries.
D-073's external dead-man stays an independent barrier and is given no credit in any result here.

### P-05 — crowbar instead of a series diode (option A)

`D_RP` (SS24) deleted; `F1` now feeds `+12V_PROT` directly; `D_XBAR` from `GND` (anode) to `+12V_PROT`
(cathode). A reversed battery forward-biases it and F1 clears; the tracer confirms the reverse path
exists and passes through F1. `J_PWR` is to be **keyed**. Not sized: the crowbar must survive F1's
clearing I²t at the SLA's short-circuit current — both unknown (O-17). Fallback if coordination cannot
be shown: a properly sized series Schottky (option B). Side benefit: `VBAT_SENSE` now reads the true
battery after F1, with no diode drop.

Why it matters beyond protection: a degraded series diode raises the forward drop and can push the
match below all-fire — a **hang-fire**, which draws people toward a live motor.

### P-06 — station power (option A)

Keep the separate station feed (D-067). A supply conductor in the umbilical would let one short to
`ARM_LINE` arm the bench silently, and a crush across supply, ARM and FIRE fire it from SAFE. There is
also no pin left. Requirement, unverified: the bench coils must see ≥ 9 V, i.e.
`V_station − I·R_loop − V_f(D_K3F) ≥ 9 V` at ~100 mA with FIRE held. The cable gauge is not recorded,
so this cannot be computed yet (O-23).

## 5. What changed in the generators

| File | Change |
|---|---|
| `gen_bench.py` | `D_RP`/`+12V_FUSED` removed; `D_XBAR` crowbar; `J_PWR` keyed. K1 NC → `CONT_SRC`. K2 coil `FIRE_P`/`FIRE_N`; K3 coil `K3_COIL`/`FIRE_N` with `D_K3F`, `D_K3T`; `D_K2`, `D_K3` re-pointed. `R_CONT` removed; `R_TEST1`, `R_TEST2`, `D_CBLK`, `R_CS` added; `U_CONT` LED in series, emitter drives the sense high. `D_FIRE` across the FIRE pair. Umbilical from `umbilical.py`. Rev A.2 |
| `gen_station.py` | Umbilical from `umbilical.py`. `J_ARMSW` 7 terminals, `J_FIRESW` 6, `J_ESTOP` 4; `J_TESTSW`, `J_RESET`, `K5`, `D_K5` added. `D_CONT` active-high; `R_CONT_PU` removed. Rev A.2 |
| `umbilical.py` | New: the pin map and the assumed adjacency, shared by both generators and the tracer |
| `trace_fire_loop.py` | Sections 1–7, below |
| `generate_parts_list.py` | Rows for every added and removed part; Batch 2 parts marked *Pending decision* |

## 6. Verification — connectivity only

### 6.1 The chain, in order, from a clean regeneration

| Step | bench | station |
|---|---|---|
| `gen_bench.py`, `gen_station.py` | written | written |
| `sync_project_uuid.py`, then `--check` | synced, in sync | synced, in sync |
| `validate_sch.py` (symdir resolved, structural checks ran) | **0 errors, 0 warnings** | **0 errors, 0 warnings** |
| `kicad-cli sch erc` **10.0.8** | **0 errors, 0 warnings** | **0 errors, 0 warnings** |
| Netlist vs `main` (`exports/2026-11-10-revA2/netlist-diff-vs-main-*.txt`) | +7 / −2 parts, +9 / −3 nets, 37 nets unchanged | +4 / −1 parts, +8 / −1 nets, 27 nets unchanged |
| `trace_fire_loop.py` (both netlists) | **all gated checks pass**, 11 residuals reported | — |
| `check_layout.py` | no overlaps, nothing outside its box | same |

Every netlist change is one this batch intended; none is incidental.

### 6.2 `trace_fire_loop.py` — what each section asserts (gated unless stated)

1. **State table.** Fire current only with FIRE held, across eight states including *E-STOP with
   channel 2 failed*, *channel 1 failed* and *FIRE contacts without ARM*.
2. **Shunt and return.** Shunt closed and isolated from the return in SAFE **and ARMED**; released, with
   the low side tied, only in FIRE and TEST.
3. **TEST path.** Test source dead in ARMED and FIRE; live in TEST; test current returns through the
   initiator; **no sneak path** to ground with the match removed; no test current at SAFE.
4. **Dead short.** No state shorts the battery around the initiator.
5. **Contact faults.** Every single fault — NO welded, stuck released, changeover bridged — on K1–K4, in
   every healthy operating state: **none fires.** Reported, not gated: K3 bridged in FIRE shorts the
   battery around the match (F1 clears, no ignition — the O-3 consequence), and **8 double faults** that
   fire, all of the form *K1 + K2 welded, then TEST* or *K2 + K3 welded, then ARM*.
6. **Reverse polarity.** Crowbar path exists and passes through F1.
7. **Umbilical shorts.** DC solve from both netlists. The baseline is checked against the state table
   used by sections 1–6, so the relay drive assumed there is **derived from the drawn coil wiring**, not
   trusted. Gated: any short that fires, may fire, or opens the shunt in SAFE/TEST/ARMED, and any
   adjacent short that keeps a burn going through an E-STOP, arms K1 outside ARMED, or fakes continuity.

Model limits, stated in the tool: ideal diodes, nominal 400 Ω coils, no cable resistance, bench SP3485
assumed enabled and idling (the worse case), TBD resistors left open, opto and ICs open.

### 6.3 Self-tests — the tracer must be able to fail

| Deliberately broken design | Expected | Got |
|---|---|---|
| K3 coil returned to GND instead of `FIRE_N` (scratch copy of `gen_bench.py`) | gated failure | **1 failure**: `FIRE_N <-> ARM_LINE: ARMED: SHUNT OPENS (K3 12.0 V)` |
| ARM made adjacent to ESTOP (pins 3 and 10) | gated failure | **1 failure**: `FIRE+ESTOP: burn may continue (??)`, exit code 1 |
| Rev A.1 `main` netlists through section 7 | the §3 findings | ARM↔FIRE *FIRES*; FIRE↔ESTOP *may fire*; ESTOP↔GND, ESTOP↔RS485_B *burn continues* |

### 6.4 A correction to my own analysis

In the chat analysis that preceded this batch I said that the ground-returned K3 variant fails because
"an ARM↔FIRE_N short puts K2 and K3 in series at ~6 V each". **That was wrong.** My scratch model left out
the relay flyback diodes; with them, `D_K2` clamps K2 and K3 sees the full 12 V instead. The variant is
still rejected, for the reason in §4 (K3 pulls in while armed), and the tracer — which includes every
diode in the netlists — now reports that correctly. The Rev A.1 findings in §3 were re-run through the
same engine and hold; the only number that moved is K4 in the FIRE↔ESTOP case, 6.9 V → 7.0 V.

## 7. Residuals — reported, not gated, and not safe by assertion

| Pair (not adjacent unless stated) | Result | Closes by |
|---|---|---|
| FIRE_P↔ESTOP, ARM↔ESTOP | E-STOP pressed during a burn: K4 held, K1/K2/K3 left in the ?? band — **burn may continue (??)** | Keeping them apart (pin map does); measured must-release (O-22); real adjacency (O-23) |
| ARM↔TEST | During TEST, K1 pulls in (12 V): bench armed with shunt open, one K2 weld from firing. Test reads "no match"; station ARMED lamp and buzzer reveal it | Pin map keeps them apart (3 vs 11); O-23 |
| ARM↔RS485_A/B, FIRE_P↔RS485_A/B, TEST↔RS485_A/B | K1 or K3 at 0.9–2.1 V in SAFE — **datasheet cannot exclude pick-up** | O-22 |
| CONT↔RS485_A, CONT↔TEST | Continuity lamp false-good in SAFE/TEST | Pin map keeps them apart; O-23 |
| ESTOP↔GND/shield, ESTOP↔RS485, ESTOP↔FIRE_N, ESTOP↔CONT, ESTOP↔TEST | Channel 1 held; **channel 2 stops the burn** | Accepted as single-channel degradation — review owner |

## 8. Needs Emilio Guadarrama's written sign-off — none of it given

1. K3 coil on the FIRE command, one Form C pole for shunt and return (P-02 / D-A).
2. The continuity TEST function, its test-current margin below no-fire, and acceptance of H10 (P-01 / D-B).
3. The floating FIRE loop, the pin map, and the loss of path 2 from this cable (P-03).
4. The two-channel E-STOP, the K5 permit latch and its RESET conditions (P-04).
5. Station power stays a separate feed (P-06 / D1).
6. Crowbar plus keyed connector instead of a series diode, and the fuse/crowbar coordination (P-05).
7. Every relay contact margin against the e-match current.
8. The battery.
9. Acceptance of the relay measurements (O-3 transfer, O-22 coil thresholds) and of the residuals in §7.
10. **Gate 6** fabrication release.
11. **Bring-up Stage 5**, live e-match.

## 9. Blocked on data — nothing invented

| ID | Needed | Blocks |
|---|---|---|
| O-1 | E-match part, no-fire / all-fire current, resistance | `R_TEST1/2`, `R_CS`, test margin, all fuse and contact ratings, `PYRO` width |
| O-3 | Break-before-make on real units, scope on COM, many cycles, coil diode fitted | K3 contact life under option C |
| O-17 | Fuse budget and the SLA's short-circuit current | `F1`, `F_STN`, `D_XBAR` |
| O-22 | Must-operate / must-release voltage across real relay units | Every ?? residual |
| O-23 | Umbilical connector part, pin rows, cable lay-up and gauge | True adjacency; the ≥ 9 V coil budget |
| O-24 | Relay maker and its own datasheet (Songle vs Sanyou) | Every relay figure above |
| O-25 | Panel parts: two-block positive-opening E-STOP, three-pole key, 2NO+1NC FIRE, TEST, RESET | Station panel and harness |
| — | 1N4148W, PC817 (CTR at low current), crowbar diode datasheets | Diode ratings; the TEST detector |
