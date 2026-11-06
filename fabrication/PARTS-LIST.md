# TALAVERA v1 — Preliminary parts list

> ### PRELIMINARY — not a BOM
>
> **No schematic exists.** Gate 2 has not started, so there is no netlist to reconcile against.
> Designators are placeholders, quantities are estimates, and rows marked `[CANDIDATE]` carry
> **unverified** part numbers. The IGNIS v5 and MAGNIS v1 lists state that their designators and
> quantities match a netlist; **this list cannot make that claim yet.**
>
> Do not order from this document. It exists so lab stock can be checked early.

> ### Assembly constraint (D-049)
>
> The board goes to **JLCPCB assembled**, so every *populated* part must be **LCSC-stocked**.
> This is what ruled out a populated AD620: the SOIC `AD620ARZ` is listed under LCSC
> “Pre-ordered Products”, which JLCPCB very likely cannot place. Panel controls, the DevKitC
> and the AD620 bypass option are hand-fitted and exempt.

Formatted to match `IGNIS_V5_Parts_List_rev3.xlsx` and `MAGNIS_v1_Parts_List.xlsx`.
LCSC codes are reused from those lists where the part is the same.

Spreadsheet versions: [`TALAVERA_v1_Parts_List_bench.csv`](TALAVERA_v1_Parts_List_bench.csv) · [`TALAVERA_v1_Parts_List_station.csv`](TALAVERA_v1_Parts_List_station.csv) — open directly in Excel.

**Status values:** `In lab` = confirmed present in the IGNIS v5 / MAGNIS v1 lists · `Pending decision` = awaiting a gate decision · `TBD` = not yet specified · `Candidate` = proposed, unverified

| | Lines |
|---|---|
| Confirmed in lab | **35** |
| Still TBD or pending | **18** |

---

## Bench board

### LOGGER

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Dev board ESP32-DevKitC V4 (WROOM-32D, PCB antenna) | ESP32-DevKitC-32D | MCU1 | 1 | -- | UNIT | Mouser | DigiKey | Socketed, as on MAGNIS v1. Radios stopped in firmware (D-029). Choose the 32D option at UNIT. |
| In lab | Female header 1x19, 2.54 mm | PPTC191LFBN-RC | - (MCU1) | 2 | -- | UNIT | Mouser | DigiKey | Sockets for the DevKit. Cut from a 1x40 strip. Same approach as MAGNIS v1. |

### STORAGE

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | MicroSD socket push-push | THD2528-11SD-GF | CARD1 | 1 | C283232 | UNIT | Mouser | DigiKey | Pin 9 CD -> SD_DETECT with a 10 k pull-UP (as IGNIS v5 R28). Locating pegs drilled 1.3 mm (MAGNIS v1). Shell pads MP1-4 to GND. |

### ANALOG FRONT END  (D-046)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| New (approved) | 24-bit ADC, SPI, 2 kSPS, integrated PGA x1-128, TSSOP-16 | ADS1220IPWR | U_ADC | 1 | C48263 | UNIT | Mouser | DigiKey | SELECTED. Replaces the ADS1115 and its I2C bus. Stocked at BOTH UNIT and LCSC (C48263, ~15.9k, ~$1.71 @100) - stock checked 6 Nov 2026, re-verify before ordering. Internal PGA is the PRIMARY front end. Verify input common-mode range with PGA enabled at 3.3 V against the load cell (open item 4). |
| Optional / bypassable | Instrumentation amplifier (hand-populated) | AD620ARZ (SOIC) or AD620AN (DIP, UNIT) | U_AMP | 0 | C578332 | UNIT | Mouser | DigiKey | Footprint laid out with 0 ohm BYPASS LINKS, NOT populated at assembly. AD620ARZ is listed under LCSC 'Pre-ordered Products' so JLCPCB very likely cannot place it. Hand-populate to A/B the two front ends in bring-up Stage 4. |
| New (approved) | Resistor 0 ohm 0805 - AD620 bypass links | Generic 0 R jumper | R_BYP1, R_BYP2 | 2 | -- | UNIT | Mouser | DigiKey | Fitted = PGA-only chain. Removed + AD620 populated = two-stage chain. Lets both be measured on identical hardware. |
| TBD | Load cell excitation reference | TBD | U_REF | 1 | -- | -- | -- | -- | Cannot be specified until the load cell datasheet is available (open item 4). Check whether the excitation can serve as the ADS1220 external reference for a ratiometric measurement, which would cancel excitation drift. |

### SAFETY CHAIN  (hardware only - no MCU)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| TBD | Relay, 12 V coil, contact NORMALLY OPEN - ARM | TBD | K1 | 1 | -- | -- | Mouser | DigiKey | Energised by the station ARM key. Must be NO so DISARMED is the de-energised state. |
| TBD | Relay, 12 V coil, contact NORMALLY OPEN - FIRE | TBD | K2 | 1 | -- | -- | Mouser | DigiKey | Energised only while the station FIRE button is held. |
| TBD | Relay, 12 V coil, contact NORMALLY CLOSED - SHUNT | TBD | K3 | 1 | -- | -- | Mouser | DigiKey | MANDATORY NC. Shorts the e-match pair whenever disarmed (D-008). Releases only when K1 pulls in. |
| TBD | Relay, 12 V coil, NO - MASTER / E-STOP | TBD | K4 | 1 | -- | -- | Mouser | DigiKey | Held in by its coil. E-STOP breaks the coil circuit so it drops out. |
| TBD | Arming plug / removable shorting link | TBD | J_ARM | 1 | -- | -- | -- | -- | Withdrawn by hand at the bench, inserted last. Must be keyed and obviously absent at a glance. |
| In lab | Switching diode - relay coil flyback | 1N4148W | D_K1..D_K4 | 4 | C81598 | UNIT | Mouser | DigiKey | One per relay coil. |

### PYRO INTERFACE  (one channel - D-015)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Optocoupler SMD-4, CTR 100-600 % | TLP521GB-S (UMW) | U_CONT | 1 | C364143 | UNIT | Mouser | DigiKey | Continuity sense isolation. Topology reused from IGNIS v4/2v2 Pyros.SchDoc (PYRO_CHx_CONT). Sense only - see notes. |
| In lab | Screw terminal 6-pin 5.08 mm | 1729160 | P1 | 1 | C457192 | -- | Mouser | DigiKey | E-match pair plus umbilical pyro pair. Not at UNIT (KF301 is 5.0 mm pitch). |
| Candidate | N-MOSFET 60 V / 5 A (SOT-223) | NCE6005AR | Q_FIRE | 1 | C189606 | UNIT | Mouser | DigiKey | ONLY if a solid-state firing element is chosen downstream of the relays. Relays remain the primary interrupt. |
| TBD | Continuity sense series resistor | TBD | R_CONT | 1 | -- | -- | Mouser | DigiKey | Value MUST hold sense current below the e-match no-fire rating. Cannot be computed - open item 3. |

### INDICATORS

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Red LED 0805 | NCD0805R1 | D_IND1..6 | 6 | C84256 | UNIT | Mouser | DigiKey | Hardware-driven status LEDs. |
| TBD | High-brightness beacon LEDs, long-range | TBD | D_BEACON | TBD | -- | -- | Mouser | DigiKey | Must be visible at 20-40 m (manual p. 24). DRIVEN FROM THE REAL ARM/FIRE LINES (D-017), not from the MCU. |
| Logger status only | Addressable RGB LED 5050 | WS2812B-B/T | LED1 | 1 | C2761795 | UNIT | Mouser | DigiKey | CAUTION: addressable LEDs need an MCU data signal, so they CANNOT serve the safety beacon (D-017). Logger-local status only. |

### TELEMETRY  (secondary path - BUILT IN REV A, D-048)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Pending part | Isolated RS-485 transceiver | ADM2582E / ADM2587E  [CANDIDATE] | U_485 | 1 | -- | -- | Mouser | DigiKey | Path confirmed for rev A (D-048); exact part still to choose. Integrated isolation plus isolated supply. Must be LCSC-stocked for JLCPCB assembly (D-049). Alternative: MAX13487 + ADuM1201 + isolated DC-DC. |
| In lab | Optocoupler SMD-4 (discrete isolation alternative) | TLP521GB-S (UMW) | U_ISO | 2 | C364143 | UNIT | Mouser | DigiKey | Cheaper discrete isolation if a bidirectional link is not needed. |

### POWER & PROTECTION

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Schottky 40 V / 2 A SMA - reverse polarity | SS24 | D_RP | 1 | C50645 | UNIT | Mouser | DigiKey | SMA footprint. Series or blocking configuration per Gate 2. |
| In lab | LDO 3.3 V | AMS1117-3.3 | U_3V3 | 1 | C6186 | UNIT | Mouser | DigiKey | Logger domain. Own fused rail, separate from relay coils (SAFETY.md section 4, constraint 3). |
| In lab | LDO 5 V | AMS1117-5.0 | U_5V | 1 | C6187 | UNIT | Mouser | DigiKey | Only if a 5 V rail proves necessary. Confirm at Gate 2. |
| TBD | Fuse and holder, 12 V input | TBD | F1 | 1 | -- | -- | Mouser | DigiKey | Rating pending the current budget. Separate fuse for the logger rail. |
| TBD | TVS / ESD array - one per umbilical conductor | TBD | D_TVS | 10-12 | -- | -- | Mouser | DigiKey | ESD protection on all external connectors is a Gate 2 requirement. |

### CONNECTORS & TEST

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | JST-SH 4-pin right-angle (debug UART) | SM04B-SRSS-TB(LF)(SN) | J_DBG | 1 | C160404 | UNIT | Mouser | DigiKey | Logger debug only. Not a safety interface. |
| TBD | Umbilical connector, keyed + strain relief | TBD | J_UMB | 1 | -- | -- | Mouser | DigiKey | Cable B, 8-10 conductors. Keyed, strain-relieved, pin 1 marked (Gate 1 requirement). |
| In lab | SMT test point, miniature | Keystone 5015 | TP1..TP14 | ~14 | -- | -- | Mouser | DigiKey | Test points on EVERY rail and EVERY safety signal (Gate 2 requirement). Bare pads also acceptable. |

### PASSIVES  (existing 0603 / 0805 library)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Resistor 10 kOhm 0603 1 % | 0603WAF1002T5E | R* | ~12 | C25804 | UNIT | Mouser | DigiKey | Pull-ups, dividers, SD_DETECT |
| In lab | Resistor 4.7 kOhm 0603 1 % | 0603WAF4701T5E | R* | ~4 | C23162 | UNIT | Mouser | DigiKey |  |
| In lab | Resistor 1 kOhm 0603 1 % | 0603WAF1001T5E | R* | ~8 | C21190 | UNIT | Mouser | DigiKey | LED series, opto drive |
| In lab | Resistor 100 Ohm 0603 1 % | 0603WAF1000T5E | R* | ~4 | C22775 | UNIT | Mouser | DigiKey |  |
| In lab | Capacitor 100 nF 50 V X7R 0805 | CC0805KRX7R9BB104 | C* | ~15 | C49678 | UNIT | Mouser | DigiKey | Decoupling |
| In lab | Capacitor 10 uF 25 V X5R 0805 | CL21A106KAYNNNE | C* | ~6 | C15850 | UNIT | Mouser | DigiKey |  |
| In lab | Capacitor 22 uF 25 V X5R 0805 | CL21A226MAQNNNE | C* | ~3 | C45783 | UNIT | Mouser | DigiKey | Bulk on the logger rail |

---

## Control station board

### CONTROLS  (hardware only - no MCU in the safety chain)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| TBD | ARM key switch, removable key, 2-position | TBD | S_ARM | 1 | -- | -- | Mouser | DigiKey | Key must be removable and carried by the ignition officer. Panel mount. |
| TBD | E-STOP, mushroom head, latching, NC contact | TBD | S_ESTOP | 1 | -- | -- | Mouser | DigiKey | Panel mount. Breaks the bench master relay coil. NC so a broken wire stops the bench. |
| TBD | FIRE pushbutton, momentary, NO, panel mount | TBD | S_FIRE | 1 | -- | -- | Mouser | DigiKey | A substantial panel button. NOT an SMD tactile - see notes. |
| In lab | Tactile switch (CONTINUITY test only) | SKRPABE010 | S_CONT | 1 | C115360 | UNIT | Mouser | DigiKey | Acceptable for the continuity check. NOT acceptable for FIRE: a 4.6 mm SMD tactile is the wrong control for a pyrotechnic command. |

### TELEMETRY & USB

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | USB-C 16-pin (USB 2.0) | TYPE-C-31-M-12 | J_USB | 1 | C165948 | UNIT | Mouser | DigiKey | On the STATION board, not the bench. Direct USB down a 20 m umbilical is out of spec (D-038). |
| In lab | USB ESD diode, 5 V bidirectional | ESD9B5.0ST5G | D_ESD1, D_ESD2 | 2 | C111566 | UNIT | Mouser | DigiKey | SOD-923, one per data line. Alt: USBLC6-2SC6 (C7519). |
| Pending part | USB-UART bridge | CH340C / FT232RL  [CANDIDATE] | U_USB | 1 | -- | UNIT | Mouser | DigiKey | No MCU needed on the station for safety. A bridge is sufficient. CH340C is LCSC-stocked and cheap. |
| Pending part | Isolated RS-485 transceiver | ADM2582E  [CANDIDATE] | U_485 | 1 | -- | -- | Mouser | DigiKey | Station end of the isolated link. Isolation is MANDATORY so the laptop is never tied to bench ground during a firing. Must be LCSC-stocked for JLCPCB assembly. |

### MEASUREMENT OUTPUT

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| TBD | Differential receiver for the thrust pair | TBD | U_RX | 1 | -- | -- | Mouser | DigiKey | Recovers the thrust signal and presents 0-5 V to a DAQ. |
| TBD | DAQ output connector (BNC or terminal) | TBD | J_DAQ | 1 | -- | -- | Mouser | DigiKey | Path 2 must work with no software at all. |
| TBD | Battery voltage display module | TBD | U_VM | 1 | -- | UNIT | -- | -- | Wirikuta used a digital voltmeter module (manual p. 19). Pre-test check requires at least 12 V read remotely (manual p. 12). |

### INDICATORS & AUDIO

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Red LED 0805 | NCD0805R1 | D_ARMED, D_CONT, D_PWR | 3+ | C84256 | UNIT | Mouser | DigiKey | ARMED lamp must be driven from the real arm line. |
| In lab | Magnetic buzzer 2.7 kHz (passive) | MLT-8530 | LS1 | 1 | C94599 | -- | Mouser | DigiKey | Audible ARMED warning. Recommended addition - the manual relies on visual cues only. |
| In lab | N-MOSFET 30 V / 270 mA (SC-70) | NTS4001NT1G | Q_BUZZ | 1 | C116738 | -- | Mouser | DigiKey | Buzzer drive. |
| In lab | Switching diode (buzzer flyback) | 1N4148W | D_BUZZ | 1 | C81598 | UNIT | Mouser | DigiKey |  |

### CONNECTORS & TEST

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| TBD | Umbilical connector, keyed + strain relief | TBD | J_UMB | 1 | -- | -- | Mouser | DigiKey | Mates cable B. |
| In lab | Screw terminal 6-pin 5.08 mm | 1729160 | P1 | 1 | C457192 | -- | Mouser | DigiKey | Pyro pair, cable A. |
| In lab | SMT test point, miniature | Keystone 5015 | TP1..TP8 | ~8 | -- | -- | Mouser | DigiKey |  |

### PASSIVES  (existing library)

| Status | Component name | ID # (part number) | Designator | Amount | LCSC | UNIT Electronics | Mouser MX | DigiKey MX | Notes |
|---|---|---|---|---|---|---|---|---|---|
| In lab | Resistor 10 kOhm 0603 1 % | 0603WAF1002T5E | R* | ~8 | C25804 | UNIT | Mouser | DigiKey |  |
| In lab | Resistor 1 kOhm 0603 1 % | 0603WAF1001T5E | R* | ~6 | C21190 | UNIT | Mouser | DigiKey | LED series |
| In lab | Resistor 5.1 kOhm 0603 1 % | 0603WAF5101T5E | R* | 2 | C23186 | UNIT | Mouser | DigiKey | USB-C CC pull-downs |
| In lab | Resistor 22 Ohm 0603 1 % | 0603WAF220JT5E | R* | 2 | C23345 | UNIT | Mouser | DigiKey | USB data series |
| In lab | Capacitor 100 nF 50 V X7R 0805 | CC0805KRX7R9BB104 | C* | ~8 | C49678 | UNIT | Mouser | DigiKey |  |
| In lab | Capacitor 10 uF 25 V X5R 0805 | CL21A106KAYNNNE | C* | ~4 | C15850 | UNIT | Mouser | DigiKey |  |

---

## Two findings from your existing BOMs that change the design

### 1. WS2812B cannot drive the safety beacon

IGNIS v5 and MAGNIS v1 both use `WS2812B-B/T` addressable RGB LEDs for status. **Addressable LEDs need
a data stream from a microcontroller.** Decision D-017 requires the TALAVERA beacon to be driven from
the real ARM and FIRE lines so that it cannot misreport state — which a WS2812B, by construction,
always can. The safety beacon must therefore be **plain LEDs wired to the actual signals**. WS2812B is
kept only for logger-local status, where a wrong colour costs nothing.

### 2. SKRPABE010 is the wrong control for FIRE

The 4.6 x 3.2 mm SMD tactile switch used across both boards is fine for a continuity test. It is not an
appropriate control for commanding a pyrotechnic event: it can be actuated by a dropped tool, a closing
lid, or a thumb that slipped. **FIRE needs a substantial panel-mount momentary button**, ideally
guarded. The tactile switch is retained for the continuity check only.

---

## Reused from IGNIS v4 / 2v2 — with one important exception

`Pyros.SchDoc` in IGNIS v4 and 2v2 implements a two-channel pyro stage: `PYRO_CHx_GATE` through an
optocoupler to an S8050 NPN driving an NCE6005AR low-side MOSFET, with a second optocoupler across the
e-match returning `PYRO_CHx_CONT` for continuity. That continuity topology is **directly reusable** and
is the basis for the station's continuity check.

**The gate-drive half is not reusable.** In IGNIS the microcontroller gates the pyro channel. In
TALAVERA it must not — arming and firing are relay contacts and a hand-inserted plug (D-013). Porting
`Pyros.SchDoc` wholesale would reintroduce exactly the MCU-in-the-firing-path arrangement this redesign
exists to remove. Take the sense circuit; leave the gate drive.

One constraint carries over regardless: the continuity sense current flows **through the e-match**, so
`R_CONT` must hold it below the no-fire rating. That value cannot be computed until the e-match part is
known (open item 3).
