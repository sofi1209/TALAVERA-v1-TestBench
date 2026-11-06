# Gate 2 readiness — what is missing before drawing schematics

**Short answer: nothing blocks starting.** Two of fourteen sheets cannot be *finished*, and three
footprints need creating — but neither prevents drawing.

Checked against the installed KiCad 10.0 libraries on 6 November 2026.

---

## 1. Symbols — all present in KiCad 10 stock libraries

Verified by searching `C:\Program Files\KiCad\10.0\share\kicad\symbols`.

| Part | Symbol | Library |
|---|---|---|
| ADS1220 | ✅ | `Analog_ADC` |
| AD620 | ✅ | `Amplifier_Instrumentation` |
| SP3485 | ✅ | `Interface_UART` |
| CH340 | ✅ | `Interface_USB` |
| ESP32-WROOM-32D | ✅ | `RF_Module` |
| microSD connector | ✅ | `Connector` |
| USB-C receptacle | ✅ | `Connector` |
| SPDT relay | ✅ | `Relay` — generic, fits `SRD-12VDC-SL-C` |

**Nothing needs drawing as a symbol.** The ESP32-DevKitC has no dedicated symbol, but it is socketed, so
it is two 1×19 connector symbols — no library work required.

## 2. Footprints — three gaps, and they do not block the schematic

| Part | Footprint | Status |
|---|---|---|
| ADS1220 | `TSSOP-16_4.4x5mm_P0.65mm` | ✅ `Package_SO` |
| AD620 | `DIP-8_W7.62mm` + socket | ✅ `Package_DIP` |
| DevKitC sockets | `PinSocket_1x19_P2.54mm_Vertical` ×2 | ✅ `Connector_PinSocket_2.54mm` |
| Passives | `R_0603`, `C_0805` — **`_HandSolder` variants exist** | ✅ use the HandSolder pads (D-051) |
| AMS1117 | `SOT-223-3_TabPin2` | ✅ |
| ESD9B5.0ST5G | `D_SOD-923` | ✅ |
| **`SRD-12VDC-SL-C` relay** | — | ❌ **create.** `Relay_THT` has Schrack, Axicom, Finder, Fujitsu — no Songle SRD. Simple 5-pin through-hole outline. |
| **`THD2528-11SD-GF` microSD** | — | ❌ **create or import.** `Connector_Card` has Hirose DM3AT/DM3BT and Molex only. Ignitia already has this footprint in Altium from IGNIS v5; MAGNIS v1 notes locating pegs drilled 1.3 mm. |
| **`TYPE-C-31-M-12` USB-C** | — | ❌ **create or import.** KiCad ships Amphenol and other USB-C footprints; the HRO 16-pin part has its own layout. Also already in the Altium library. |

These are **Gate 4 work.** KiCad lets a schematic be drawn in full and footprints assigned afterwards, so
they are not a prerequisite. SnapMagic — already used for the IGNIS libraries — offers KiCad exports for
all three.

## 3. The two data items block *values*, not topology

| | Blocks | Does **not** block |
|---|---|---|
| **O-1** e-match no-fire current | `R_CONT` value, fuse rating, relay contact rating, `PYRO` trace width | The pyro sheet's topology, the shunt wiring, the continuity opto arrangement |
| **O-2** load cell datasheet | ADS1220 PGA gain, excitation value, reference choice, whether the PGA common-mode limit bites | The analog sheet's topology, the AD620 socket and bypass links |

Both change **resistor values and ratings, not the circuit**. Rework risk from drawing before they arrive
is low: a changed gain is a changed resistor, not a redrawn sheet.

---

## 4. Sheet-by-sheet readiness

### Bench board

| # | Sheet | Ready? | Blocked on |
|---|---|---|---|
| 1 | Main / interconnect | ✅ | — |
| 2 | Power & protection | ⚠️ mostly | Input fuse value needs the current budget; rails are fully specified |
| 3 | Safety chain (K1–K4, arming plug) | ⚠️ mostly | Topology complete; relay **contact rating** note depends on O-1 |
| 4 | **Pyro interface** | ❌ values | **O-1** |
| 5 | **Analog front end** | ❌ values | **O-2** |
| 6 | Logger (DevKitC) | ✅ | — |
| 7 | Storage (microSD) | ✅ | Fully specified, including `SD_DETECT` and the 10 k pull-up |
| 8 | Telemetry (SP3485EN) | ✅ | — |
| 9 | Indicators | ⚠️ mostly | Beacon LED part not chosen; does not affect topology |

### Control station board

| # | Sheet | Ready? | Blocked on |
|---|---|---|---|
| 10 | Main / interconnect | ✅ | — |
| 11 | Controls (ARM key, E-STOP, FIRE, continuity) | ✅ | Panel controls are off-board, so the sheet needs only terminal symbols |
| 12 | Telemetry & USB | ⚠️ mostly | Isolator part (O-6); topology drawable |
| 13 | Measurement output | ⚠️ mostly | Output levels settle with O-2 |
| 14 | Indicators & audio | ✅ | — |

**Nine of fourteen sheets are fully ready. Two are blocked on values only.**

---

## 5. Three things to settle first — design decisions, not missing data

These are mine to propose rather than things to wait for, but they should be fixed *before* drawing
connectors, because changing them later means rewiring sheets.

### 5.1 Cable B pinout

Eight to ten conductors carrying arm, fire, e-stop, the thrust pair, the RS-485 pair, battery sense and
a common return. The allocation needs deciding once and then obeyed on both boards.

### 5.2 Net naming

The net classes already assign rules by pattern (D-024), so names are load-bearing, not cosmetic:

| Prefix | Class | Examples |
|---|---|---|
| `PYRO_*` | `PYRO` | `PYRO_MATCH_P`, `PYRO_MATCH_N`, `PYRO_SHUNT` |
| `ARM_*` | `SAFETY` | `ARM_LINE`, `ARM_RELAY_COIL` |
| `FIRE_*` | `SAFETY` | `FIRE_LINE`, `FIRE_RELAY_COIL` |
| `ESTOP_*` | `SAFETY` | `ESTOP_LOOP` |
| `LC_*`, `THRUST_*` | `ANALOG` | `LC_EXC_P`, `LC_SIG_P`, `THRUST_DIFF_P` |
| `+12V*`, `+3V3*` | `POWER` | `+12V_RAW`, `+12V_MASTER`, `+3V3_LOGGER` |

A firing net not named `PYRO_*` silently inherits `Default` rules — 0.25 mm clearance instead of 1.00 mm.
This is the one naming mistake with a safety consequence.

### 5.3 Sheet structure

Hierarchical, as the table above, following the IGNIS convention of one `.kicad_sch` per function rather
than one large flat sheet.

---

## 6. Recommendation

**Start now.** Draw the nine ready sheets and the topology of the rest, marking every O-1 and O-2
dependent value as `TBD` on the sheet itself so it cannot be forgotten. Finish the pyro and analog sheets
when the e-match part and load cell datasheet arrive.

The alternative — waiting — stalls twelve sheets' worth of work on two numbers that affect resistor
values.

## 7. What is explicitly *not* needed before schematics

| Item | Why it can wait |
|---|---|
| O-8 board size | Layout, Gate 4 |
| O-9 copper weight | Layout, Gate 4 |
| O-14 enclosure and panel | Layout, Gate 4 |
| O-11 largest motor class | Standoff and cable, not the circuit |
| O-12 environment figures | Part selection, Gate 3 |
| O-10 which ADS1115 symptom was seen | Informational; the part is already chosen |
| O-13 Wirikuta KiCad sources | Comparison only |
| O-15 TSSOP hand-soldering | Assembly, not design |
