# TALAVERA v1 — Two-layer floorplan and routing plan

**Date:** 10 November 2026 · **Baseline:** `86a22f2` · **Status: PLAN ONLY — LAYOUT HAS NOT STARTED AND MUST NOT**

This is paper work done ahead of Gate 4. It commits no copper, and it approves nothing. Gate 6
(fabrication release) and bring-up Stage 5 (live e-match) keep mandatory written sign-off from
**Emilio Guadarrama**.

Run the readiness gate yourself:

```bash
python hardware/tools/check_layout_ready.py
```

---

## 1. Verdict: layout must not start

`check_layout_ready.py` reports **2 blocking, 8 topology and 9 sizing gates open** (Rev A.2, 10 Nov:
the four safety-topology gates are now *drawn* but stay open until signed; O-22, O-23, O-25 added). The schematic itself
is in good shape — validator, native ERC, layout checker and the firing-loop tracer all pass — but three
different kinds of thing are missing.

### Blocking — you cannot place or route at all

| Gate | State |
|---|---|
| Schematic verified | **ok** — validator 0/0, `kicad-cli` ERC 0 violations both boards, `trace_fire_loop.py` all seven sections on both netlists, UUIDs in sync |
| Footprints assigned | **NO — 118 of 118 components have none** (Rev A.2) |
| PCB files populated | **NO** — both `.kicad_pcb` hold an outline and nothing else |
| Net classes defined | **ok** — PYRO / SAFETY / POWER / ANALOG with 8 patterns, both boards |

The footprint gate is the simple one: a netlist cannot become a board without footprints, and O-16 says
three of them (`SRD-12VDC-SL-C`, `THD2528-11SD-GF`, `TYPE-C-31-M-12`) still have to be made or imported.

### Topology — eight open decisions change *which parts exist*

This is the real reason to wait. Placing parts you have not chosen is work you will throw away.

| | Decision | What it changes on the board |
|---|---|---|
| **D-A** | K3 both shunt and return, or two relays | **Drawn in Rev A.2 as one relay, coil on FIRE (D-074) - pending sign-off.** O-3 now sets contact life, not topology |
| **D-B** | Pre-arm continuity TEST | **Drawn in Rev A.2 (D-076) - pending sign-off.** Values blocked on O-1 |
| **D1** | Station power source | **Separate feed kept (D-080) - pending sign-off.** New pin map D-075; connector part O-23 |
| **E-STOP** | Must the shunt re-close automatically | **Two channels plus K5 permit drawn (D-077/D-078) - pending sign-off.** Adds K5 and panel contact blocks on the station (O-25) |
| **M-1** | Bench 3.3 V thermal architecture | SOT-223 vs a TO-220 cascade or a buck module — different packages, different area |
| **M-2** | DevKitC vs bare WROOM-32D | The sheet draws a 38-pin module; the build sockets a 2×19 header. **The footprint cannot be assigned until the symbol matches the part** |
| **O-21** | 6N137 RX path inverts | A part change, possibly to a digital isolator: different footprint |
| **M-13** | Buzzer | MLT-8530 is a ~3.6 V externally driven transducer on a 12 V DC drive. A 12 V active sounder is a different part |

### Sizing — copper that cannot be computed yet

**O-1** (e-match no-fire/all-fire/resistance) sets the PYRO trace width, `R_STAR` and its copper, all
three fuse ratings and every relay contact margin. The `PYRO` class currently carries **2.00 mm as a
placeholder**, and **O-9** notes that width assumes 1 oz copper, unconfirmed. Also open: **O-2** load
cell, **O-8** board size, **O-14** station enclosure, **O-17** fuse budget.

---

## 2. What the netlist already tells us

Measured from the KiCad `kicadsexpr` exports, not estimated.

| | bench | station |
|---|---|---|
| Real nets | 48 | 34 |
| Pins on nets | 196 | 136 |
| Routing demand, all nets (MST edges) | 148 | 102 |
| Ground pins | 45 (one net) | 36 (**two** nets) |
| Edges absorbed by a ground pour | 44 | 34 |
| **Signal edges left to route** | **104** | **68** |
| Two-pin nets | 19 of 48 | 18 of 34 |

Widest signal nets — bench: `+3V3_LOGGER` (20 pins), `+12V_PROT` (7), `ARM_LINE` (5), `SPI_MOSI`/
`SPI_MISO` (4 each). Station: `+5V_USB` (10), `+12V_STN` (9), `+5V_BENCH` (7), `ARM_LINE` (5).

> **Method, and its limit.** These are *routing demand* figures: the minimum number of connections that
> must be made, counting each net as a chain. They are **not** a crossing count. A true crossing count
> needs a placement, a placement needs footprints, and there are none — so any crossing number quoted
> today would be invented. Re-run the count against the first real placement before trusting a
> two-layer decision.

### Is two layers enough?

**Bench: plausible but tight, and it hinges on `+3V3_LOGGER`.** With the bottom poured as ground, 104
signal edges remain on essentially one routing layer. The 20-pin 3.3 V rail cannot also be a bottom
pour, so it needs a deliberate top-side spine with short stubs — treat it as a drawn bus, not as
something the router finds. **Estimate, to be replaced by a crossing count on the first placement.**

**Station: two layers, but the bottom cannot be one plane.** See §4 — the isolation barrier splits it.

---

## 3. Bench floorplan

Three zones that must not interleave, with the pyro zone physically separate.

```
   +--------------------------------------------------------------+
   |  A. POWER ENTRY          |  B. PYRO / SAFETY  (keep-out ring) |
   |  J_PWR  F1  D_XBAR C1    |  K4  K1  K2  K3                    |
   |  F2  U_3V3  C2 C3        |  J_ARM   P1                        |
   |  R_STAR  <-- star point  |  fire current 6-12 A (O-1)         |
   |--------------------------+------------------------------------|
   |  C. LOGGER + ANALOG                 |  D. EDGE CONNECTORS      |
   |  MCU1  U_ADC  CARD1  U_485          |  J_UMB  J_LC  J_REC      |
   |  J_LC bridge, C5 C6 C9 C10          |                          |
   +--------------------------------------------------------------+
```

**Rules that come out of the audits, not from taste:**

1. **`PYRO_RTN` is dedicated copper, and the bottom pour must be cut away from it.** This is finding
   R-1. The fire return runs from K3's NO contact to `R_STAR` beside `J_PWR` and bonds to `GND` **only
   there**. On a two-layer board with a bottom ground pour, that means a routed return plus a pour
   keep-out along its whole length — not a pour connection, which is what a router will do by default
   if `PYRO_RTN` is left in the default class.
2. **The analog return must not share copper with the fire return.** `R_EXC_N` (bridge excitation
   return) and `U_ADC.5 (AVSS)` meet the fire current only at `R_STAR`. Keep the ADC and the bridge
   connector on the opposite side of the board from the pyro zone.
3. **Pyro zone keep-out.** The `PYRO` class already carries 1.00 mm clearance. Add a physical keep-out
   ring around K2, K3, `J_ARM` and `P1` so no logger or analog net is routed through it, and so a probe
   slip cannot bridge a signal into the firing path.
4. **`J_ARM` and `P1` on the board edge, and obviously apart.** The arming plug is withdrawn by hand
   (D-013) and the match connector is a short local run (~1–2 m). They must not be confusable, so
   different pitch or different keying, per the repairability notes in the audits.
5. **Logger rail is upstream of K4 (D-047)** — keep `F2` and `U_3V3` in zone A, not downstream of the
   master relay, and keep that distinction visible in the copper.
6. **`+3V3_LOGGER` as a drawn top-side spine** past MCU1 → U_ADC → CARD1 → U_485, with 100 nF at each
   device pin. Twenty pins on one rail is the board's main routing load.

## 4. Station floorplan — the bottom layer cannot be one plane

**Verified from the netlist:** only `U_ISO1` and `U_ISO2` touch both ground domains, and **no signal net
spans them**. The isolation is clean as drawn, and the barrier line is defined by those two parts.

| Domain | Parts |
|---|---|
| `GND`, bench-referenced | `J_UMB1 J_12V1 J_ESTOP1 J_VM1 U_5VB1 U_3V3B1 U_485 C_485 C_STN1-3 C_ISO2 D_ARMED1 D_PWR1 Q_BUZZ1 R_BG2 R_DE1 R_RE1` |
| `GNDREF`, laptop/USB | `J_USB1 U_USB1 C_USB1 C_V3 C_ISO1 D_ESD1 D_ESD2 R_CC1 R_CC2` |
| **Straddling** | `U_ISO1`, `U_ISO2` — and nothing else |

```
   +-----------------------------+==========+----------------------+
   |  GND  (bench-referenced)    | BARRIER  |  GNDREF (laptop/USB) |
   |  J_UMB  J_12V  F_STN        | U_ISO1   |  J_USB  U_USB        |
   |  U_5VB  U_3V3B  U_485       | U_ISO2   |  D_ESD1/2  R_CC1/2   |
   |  panel: ARM  FIRE  E-STOP   |          |  C_USB  C_V3         |
   +-----------------------------+==========+----------------------+
      bottom pour: GND only        no copper    bottom pour: GNDREF only
                                   no vias
                                   no traces
```

- **Two separate bottom pours**, each tied to its own ground, with a clear gap. Nothing crosses: no
  trace, no via, no pour, no silkscreen that invites a probe across.
- **Barrier width is a review-owner decision.** This is a USB-to-bench-reference barrier, not a mains
  barrier, so it is not a creepage-table question — but the number should be chosen deliberately and
  written down, not left to whatever the pour spacing happens to be.
- `J_DAQ` is **not fitted** in Rev A (D-069). Its pin 3 used to export bench ground to the laptop bench,
  which would bridge the barrier externally whenever a mains-powered DAQ shared it. Leave the pads if
  you like, but do not populate, and keep the silkscreen saying so.
- Panel controls (ARM key, FIRE, E-STOP) are wired to terminals, not PCB parts — put those terminals on
  one edge in the operator's reading order.

## 5. Order of work, once the gates clear

1. **Close D-A** — it decides the relay count and the pyro copper, so everything in zone B waits on it.
2. **Get O-1** — then the `PYRO` width, `R_STAR` copper and the fuse ratings stop being placeholders.
3. **Fix the symbol for M-2** before assigning any footprint to MCU1.
4. Make the three footprints from O-16 and assign all 110.
5. **Then** import the netlist, place to this floorplan, and count crossings for real.
6. Route ground and power first, then the SPI group, then the rest. `kicad-cli pcb drc` is the source of
   truth; run it per batch, not per move.

## 6. Intake still needed before this plan is firm

The repository answers most of it — 2 layers (D-023), KiCad 10.0.5, net classes set, exports available,
pyro and isolation constraints as above. These are genuinely open and I have **assumed nothing**:

1. **Board size target for each board** (O-8). Outlines are placeholders. A 100 × 100 mm cap changes
   whether the zoning above fits.
2. **Fabrication house and its limits**, and whether 1 oz or 2 oz copper (O-9). The `PYRO` width depends
   on it.
3. **Mounting holes and fixed edge positions**, and the station enclosure (O-14).
4. **Barrier gap** for the station isolation split (§4).
5. **How many jumper links are acceptable** on the bench if two layers turn out to be tight.
