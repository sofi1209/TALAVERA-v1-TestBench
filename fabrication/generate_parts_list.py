import csv, os
ROOT = r"C:/Users/sofip/Documents/Ignitia/TALAVERA-v1-TestBench"
COLS = ["Status","Component name","ID # (part number)","Designator","Amount",
        "LCSC","UNIT Electronics","Mouser MX","DigiKey MX","Notes"]
U="UNIT"; M="Mouser"; D="DigiKey"; X="--"

def R(st,name,pn,des,amt,lcsc,unit,mou,dig,notes):
    return [st,name,pn,des,amt,lcsc,unit,mou,dig,notes]

BENCH = [
 ("LOGGER",[
  R("In lab","Dev board ESP32-DevKitC V4 (WROOM-32D, PCB antenna)","ESP32-DevKitC-32D","MCU1","1",X,U,M,D,
    "Socketed, as on MAGNIS v1. Radios stopped in firmware (D-029). Choose the 32D option at UNIT."),
  R("In lab","Female header 1x19, 2.54 mm","PPTC191LFBN-RC","- (MCU1)","2",X,U,M,D,
    "Sockets for the DevKit. Cut from a 1x40 strip. Same approach as MAGNIS v1."),
 ]),
 ("STORAGE",[
  R("In lab","MicroSD socket push-push","THD2528-11SD-GF","CARD1","1","C283232",U,M,D,
    "Pin 9 CD -> SD_DETECT with a 10 k pull-UP (as IGNIS v5 R28). Locating pegs drilled 1.3 mm (MAGNIS v1). Shell pads MP1-4 to GND."),
 ]),
 ("ANALOG FRONT END  (D-046)",[
  R("New (approved)","24-bit ADC, SPI, 2 kSPS, integrated PGA x1-128, TSSOP-16","ADS1220IPWR","U_ADC","1","C48263",U,M,D,
    "SELECTED. Replaces the ADS1115 and its I2C bus. Stocked at BOTH UNIT and LCSC (C48263, ~15.9k, ~$1.71 @100) - stock checked 6 Nov 2026, re-verify before ordering. Internal PGA is the PRIMARY front end. Verify input common-mode range with PGA enabled at 3.3 V against the load cell (open item 4)."),
  R("Optional / socketed","Instrumentation amplifier, DIP-8 (optional)","AD620AN","U_AMP","0 (socket fitted)",X,U,M,D,
    "DIP-8 in a SOCKET, not populated by default (D-054). UNIT stocks the through-hole part at ~111 MXN. A socket makes the A/B comparison a chip pull, not a rework. Left out by default: at ~$6-8 it is the most expensive part on the board and the ADS1220 PGA makes it redundant."),
  R("New (approved)","IC socket DIP-8","Generic DIP-8 socket","XU_AMP","1",X,U,M,D,
    "Always fitted, so the AD620 can be added or removed without soldering."),
  R("New (approved)","Resistor 0 ohm 0805 - AD620 bypass links","Generic 0 R jumper","R_BYP1, R_BYP2","2",X,U,M,D,
    "Fitted = PGA-only chain (default). Removed + AD620 in its socket = two-stage chain. Lets both be measured on identical hardware in bring-up Stage 4."),
  R("TBD","Load cell excitation reference","TBD","U_REF","1",X,X,X,X,
    "Cannot be specified until the load cell datasheet is available (open item 4). Check whether the excitation can serve as the ADS1220 external reference for a ratiometric measurement, which would cancel excitation drift."),
 ]),
 ("SAFETY CHAIN  (hardware only - no MCU)",[
  R("New (approved)","Relay SPDT, 12 V coil, 10 A contacts, through-hole","SRD-12VDC-SL-C","K1, K2, K3, K4","4","C30431",X,M,D,
    "ONE part for all four positions (D-055). SPDT gives both NO and NC: K1/K2/K4 wired NO, K3 wired NC for the shunt. ~$0.23, ~131,800 in LCSC stock, also at Mexican retailers. Coil ~30 mA / 400 ohm. CONTACT RATING still to confirm against e-match current (O-1, O-3)."),
  R("TBD","Arming plug / removable shorting link","TBD","J_ARM","1",X,X,X,X,
    "Withdrawn by hand at the bench, inserted last. Must be keyed and obviously absent at a glance."),
  R("In lab","Switching diode - relay coil flyback","1N4148W","D_K1..D_K4","4","C81598",U,M,D,
    "One per relay coil."),
 ]),
 ("PYRO INTERFACE  (one channel - D-015)",[
  R("In lab","Optocoupler SMD-4, CTR 100-600 %","TLP521GB-S (UMW)","U_CONT","1","C364143",U,M,D,
    "Continuity sense isolation. Topology reused from IGNIS v4/2v2 Pyros.SchDoc (PYRO_CHx_CONT). Sense only - see notes."),
  R("In lab","Screw terminal 6-pin 5.08 mm","1729160","P1","1","C457192",X,M,D,
    "E-match pair plus umbilical pyro pair. Not at UNIT (KF301 is 5.0 mm pitch)."),
  R("Candidate","N-MOSFET 60 V / 5 A (SOT-223)","NCE6005AR","Q_FIRE","1","C189606",U,M,D,
    "ONLY if a solid-state firing element is chosen downstream of the relays. Relays remain the primary interrupt."),
  R("TBD","Continuity sense series resistor","TBD","R_CONT","1",X,X,M,D,
    "Value MUST hold sense current below the e-match no-fire rating. Cannot be computed - open item 3."),
 ]),
 ("INDICATORS",[
  R("In lab","Red LED 0805","NCD0805R1","D_IND1..6","6","C84256",U,M,D,
    "Hardware-driven status LEDs."),
  R("TBD","High-brightness beacon LEDs, long-range","TBD","D_BEACON","TBD",X,X,M,D,
    "Must be visible at 20-40 m (manual p. 24). DRIVEN FROM THE REAL ARM/FIRE LINES (D-017), not from the MCU."),
  R("Logger status only","Addressable RGB LED 5050","WS2812B-B/T","LED1","1","C2761795",U,M,D,
    "CAUTION: addressable LEDs need an MCU data signal, so they CANNOT serve the safety beacon (D-017). Logger-local status only."),
 ]),
 ("TELEMETRY  (secondary path - BUILT IN REV A, D-048)",[
  R("New (approved)","RS-485 transceiver, 3.3 V, half-duplex","SP3485EN-L/TR","U_485","1","C8963",X,M,D,
    "Native to the ESP32 3.3 V domain. ~$0.14-0.27, ~190,700 in LCSC stock. Replaces the ~$10 ADM2582E (D-056): isolation moves to the STATION board where USB powers the isolated side, so no isolated DC-DC is needed anywhere."),
 ]),
 ("POWER & PROTECTION",[
  R("In lab","Schottky 40 V / 2 A SMA - reverse polarity","SS24","D_RP","1","C50645",U,M,D,
    "SMA footprint. Series or blocking configuration per Gate 2."),
  R("In lab","LDO 3.3 V","AMS1117-3.3","U_3V3","1","C6186",U,M,D,
    "Logger domain. Own fused rail, separate from relay coils (SAFETY.md section 4, constraint 3)."),
  R("In lab","LDO 5 V","AMS1117-5.0","U_5V","1","C6187",U,M,D,
    "Only if a 5 V rail proves necessary. Confirm at Gate 2."),
  R("TBD","Fuse and holder, 12 V input","TBD","F1","1",X,X,M,D,
    "Rating pending the current budget. Separate fuse for the logger rail."),
  R("TBD","TVS / ESD array - one per umbilical conductor","TBD","D_TVS","10-12",X,X,M,D,
    "ESD protection on all external connectors is a Gate 2 requirement."),
 ]),
 ("CONNECTORS & TEST",[
  R("In lab","JST-SH 4-pin right-angle (debug UART)","SM04B-SRSS-TB(LF)(SN)","J_DBG","1","C160404",U,M,D,
    "Logger debug only. Not a safety interface."),
  R("TBD","Umbilical connector, keyed + strain relief","TBD","J_UMB","1",X,X,M,D,
    "Cable B, 8-10 conductors. Keyed, strain-relieved, pin 1 marked (Gate 1 requirement)."),
  R("New (approved)","Test point - bare pad / via","Bare pad (no part)","TP1..TP14","~14",X,X,X,X,
    "Test points on EVERY rail and EVERY safety signal (Gate 2 requirement). Bare pads replace Keystone 5015 (D-057): free, and they work with probe hooks."),
 ]),
 ("PASSIVES  (existing IGNIS library - 0603 R, 0805 C, D-058)",[
  R("In lab","Resistor 10 kOhm 0603 1 %","0603WAF1002T5E","R*","~12","C25804",U,M,D,"Pull-ups, dividers, SD_DETECT. 0603 retained (D-058): reels already owned, and hand-solderable."),
  R("In lab","Resistor 4.7 kOhm 0603 1 %","0603WAF4701T5E","R*","~4","C23162",U,M,D,""),
  R("In lab","Resistor 1 kOhm 0603 1 %","0603WAF1001T5E","R*","~8","C21190",U,M,D,"LED series, opto drive"),
  R("In lab","Resistor 100 Ohm 0603 1 %","0603WAF1000T5E","R*","~4","C22775",U,M,D,""),
  R("In lab","Capacitor 100 nF 50 V X7R 0805","CC0805KRX7R9BB104","C*","~15","C49678",U,M,D,"Decoupling"),
  R("In lab","Capacitor 10 uF 25 V X5R 0805","CL21A106KAYNNNE","C*","~6","C15850",U,M,D,""),
  R("In lab","Capacitor 22 uF 25 V X5R 0805","CL21A226MAQNNNE","C*","~3","C45783",U,M,D,"Bulk on the logger rail"),
 ]),
]

STATION = [
 ("CONTROLS  (hardware only - no MCU in the safety chain)",[
  R("TBD","ARM key switch, removable key, 2-position","TBD","S_ARM","1",X,X,M,D,
    "Key must be removable and carried by the ignition officer. Panel mount."),
  R("TBD","E-STOP, mushroom head, latching, NC contact","TBD","S_ESTOP","1",X,X,M,D,
    "Panel mount. Breaks the bench master relay coil. NC so a broken wire stops the bench."),
  R("TBD","FIRE pushbutton, momentary, NO, panel mount","TBD","S_FIRE","1",X,X,M,D,
    "A substantial panel button. NOT an SMD tactile - see notes."),
  R("In lab","Tactile switch (CONTINUITY test only)","SKRPABE010","S_CONT","1","C115360",U,M,D,
    "Acceptable for the continuity check. NOT acceptable for FIRE: a 4.6 mm SMD tactile is the wrong control for a pyrotechnic command."),
 ]),
 ("TELEMETRY & USB",[
  R("In lab","USB-C 16-pin (USB 2.0)","TYPE-C-31-M-12","J_USB","1","C165948",U,M,D,
    "On the STATION board, not the bench. Direct USB down a 20 m umbilical is out of spec (D-038)."),
  R("In lab","USB ESD diode, 5 V bidirectional","ESD9B5.0ST5G","D_ESD1, D_ESD2","2","C111566",U,M,D,
    "SOD-923, one per data line. Alt: USBLC6-2SC6 (C7519)."),
  R("Pending part","USB-UART bridge","CH340C / FT232RL  [CANDIDATE]","U_USB","1",X,U,M,D,
    "No MCU needed on the station for safety. A bridge is sufficient. CH340C is LCSC-stocked and cheap."),
  R("New (approved)","RS-485 transceiver, 3.3 V, half-duplex","SP3485EN-L/TR","U_485","1","C8963",X,M,D,
    "Station end, on the BENCH-REFERENCED side of the ground barrier, powered from the umbilical."),
  R("Pending part","Digital isolator / high-speed optocoupler - ground barrier","6N137 or digital isolator  [CANDIDATE]","U_ISO","2",X,X,M,D,
    "Sits between the bench-referenced side and the USB side. NOT YET VERIFIED for price or stock. The TLP521/PC817 already in stock are too slow to be relied on at 115200 baud - do not substitute them without measuring."),
 ]),
 ("MEASUREMENT OUTPUT",[
  R("TBD","Differential receiver for the thrust pair","TBD","U_RX","1",X,X,M,D,
    "Recovers the thrust signal and presents 0-5 V to a DAQ."),
  R("TBD","DAQ output connector (BNC or terminal)","TBD","J_DAQ","1",X,X,M,D,
    "Path 2 must work with no software at all."),
  R("TBD","Battery voltage display module","TBD","U_VM","1",X,U,X,X,
    "Wirikuta used a digital voltmeter module (manual p. 19). Pre-test check requires at least 12 V read remotely (manual p. 12)."),
 ]),
 ("INDICATORS & AUDIO",[
  R("In lab","Red LED 0805","NCD0805R1","D_ARMED, D_CONT, D_PWR","3+","C84256",U,M,D,
    "ARMED lamp must be driven from the real arm line."),
  R("In lab","Magnetic buzzer 2.7 kHz (passive)","MLT-8530","LS1","1","C94599",X,M,D,
    "Audible ARMED warning. Recommended addition - the manual relies on visual cues only."),
  R("In lab","N-MOSFET 30 V / 270 mA (SC-70)","NTS4001NT1G","Q_BUZZ","1","C116738",X,M,D,"Buzzer drive."),
  R("In lab","Switching diode (buzzer flyback)","1N4148W","D_BUZZ","1","C81598",U,M,D,""),
 ]),
 ("CONNECTORS & TEST",[
  R("TBD","Umbilical connector, keyed + strain relief","TBD","J_UMB","1",X,X,M,D,"Mates cable B."),
  R("In lab","Screw terminal 6-pin 5.08 mm","1729160","P1","1","C457192",X,M,D,"Pyro pair, cable A."),
  R("New (approved)","Test point - bare pad / via","Bare pad (no part)","TP1..TP8","~8",X,X,X,X,"Bare pads, per D-057."),
 ]),
 ("PASSIVES  (existing IGNIS library - 0603 R, 0805 C, D-058)",[
  R("In lab","Resistor 10 kOhm 0603 1 %","0603WAF1002T5E","R*","~8","C25804",U,M,D,""),
  R("In lab","Resistor 1 kOhm 0603 1 %","0603WAF1001T5E","R*","~6","C21190",U,M,D,"LED series"),
  R("In lab","Resistor 5.1 kOhm 0603 1 %","0603WAF5101T5E","R*","2","C23186",U,M,D,"USB-C CC pull-downs"),
  R("In lab","Resistor 22 Ohm 0603 1 %","0603WAF220JT5E","R*","2","C23345",U,M,D,"USB data series"),
  R("In lab","Capacitor 100 nF 50 V X7R 0805","CC0805KRX7R9BB104","C*","~8","C49678",U,M,D,""),
  R("In lab","Capacitor 10 uF 25 V X5R 0805","CL21A106KAYNNNE","C*","~4","C15850",U,M,D,""),
 ]),
]

def emit_csv(path, title, sub, groups):
    with open(path,"w",newline="",encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([title]); w.writerow([sub]); w.writerow([])
        w.writerow(COLS)
        for sec, rows in groups:
            w.writerow([sec])
            for r in rows: w.writerow(r)
        w.writerow([])
        inlab = sum(1 for _,rs in groups for r in rs if r[0]=="In lab")
        tbd   = sum(1 for _,rs in groups for r in rs if r[0] in ("TBD","Pending decision"))
        w.writerow(["", "Lines confirmed in lab (IGNIS v5 / MAGNIS v1 lists)", "", "", inlab])
        w.writerow(["", "Lines still TBD or pending a decision", "", "", tbd])

os.makedirs(ROOT+"/fabrication", exist_ok=True)
emit_csv(ROOT+"/fabrication/TALAVERA_v1_Parts_List_bench.csv",
  "TALAVERA v1 - BENCH BOARD preliminary parts list",
  "PRELIMINARY. No schematic exists; Gate 2 has not started. Designators are placeholders and quantities are estimates. Part numbers marked [CANDIDATE] are UNVERIFIED - confirm against datasheets before ordering. LCSC codes reused from IGNIS_V5_Parts_List_rev3 and MAGNIS_v1_Parts_List.",
  BENCH)
emit_csv(ROOT+"/fabrication/TALAVERA_v1_Parts_List_station.csv",
  "TALAVERA v1 - CONTROL STATION BOARD preliminary parts list",
  "PRELIMINARY. No schematic exists; Gate 2 has not started. Designators are placeholders and quantities are estimates.",
  STATION)

def md(groups):
    out=[]
    for sec,rows in groups:
        out.append("\n### "+sec+"\n")
        out.append("| "+" | ".join(COLS)+" |")
        out.append("|"+"---|"*len(COLS))
        for r in rows:
            out.append("| "+" | ".join(str(c).replace("|","\\|") for c in r)+" |")
    return "\n".join(out)

tot_lab = sum(1 for _,rs in BENCH+STATION for r in rs if r[0]=="In lab")
tot_tbd = sum(1 for _,rs in BENCH+STATION for r in rs if r[0] in ("TBD","Pending decision"))
print("in-lab lines:", tot_lab, "| TBD/pending lines:", tot_tbd)

body = (
"# TALAVERA v1 \u2014 Preliminary parts list\n\n"
"> ### PRELIMINARY \u2014 not a BOM\n>\n"
"> **No schematic exists.** Gate 2 has not started, so there is no netlist to reconcile against.\n"
"> Designators are placeholders, quantities are estimates, and rows marked `[CANDIDATE]` carry\n"
"> **unverified** part numbers. The IGNIS v5 and MAGNIS v1 lists state that their designators and\n"
"> quantities match a netlist; **this list cannot make that claim yet.**\n>\n"
"> Do not order from this document. It exists so lab stock can be checked early.\n\n"
"> ### Assembly constraint (D-049)\n>\n"
"> The board goes to **JLCPCB assembled**, so every *populated* part must be **LCSC-stocked**.\n"
"> This is what ruled out a populated AD620: the SOIC `AD620ARZ` is listed under LCSC\n"
"> “Pre-ordered Products”, which JLCPCB very likely cannot place. Panel controls, the DevKitC\n"
"> and the AD620 bypass option are hand-fitted and exempt.\n\n"
"Formatted to match `IGNIS_V5_Parts_List_rev3.xlsx` and `MAGNIS_v1_Parts_List.xlsx`.\n"
"LCSC codes are reused from those lists where the part is the same.\n\n"
"Spreadsheet versions: [`TALAVERA_v1_Parts_List_bench.csv`](TALAVERA_v1_Parts_List_bench.csv) \u00b7 "
"[`TALAVERA_v1_Parts_List_station.csv`](TALAVERA_v1_Parts_List_station.csv) \u2014 open directly in Excel.\n\n"
"**Status values:** `In lab` = confirmed present in the IGNIS v5 / MAGNIS v1 lists \u00b7 "
"`Pending decision` = awaiting a gate decision \u00b7 `TBD` = not yet specified \u00b7 "
"`Candidate` = proposed, unverified\n\n"
"| | Lines |\n|---|---|\n| Confirmed in lab | **"+str(tot_lab)+"** |\n| Still TBD or pending | **"+str(tot_tbd)+"** |\n\n"
"---\n\n## Bench board\n"+md(BENCH)+
"\n\n---\n\n## Control station board\n"+md(STATION)+
"\n\n---\n\n## Two findings from your existing BOMs that change the design\n\n"
"### 1. WS2812B cannot drive the safety beacon\n\n"
"IGNIS v5 and MAGNIS v1 both use `WS2812B-B/T` addressable RGB LEDs for status. **Addressable LEDs need\n"
"a data stream from a microcontroller.** Decision D-017 requires the TALAVERA beacon to be driven from\n"
"the real ARM and FIRE lines so that it cannot misreport state \u2014 which a WS2812B, by construction,\n"
"always can. The safety beacon must therefore be **plain LEDs wired to the actual signals**. WS2812B is\n"
"kept only for logger-local status, where a wrong colour costs nothing.\n\n"
"### 2. SKRPABE010 is the wrong control for FIRE\n\n"
"The 4.6 x 3.2 mm SMD tactile switch used across both boards is fine for a continuity test. It is not an\n"
"appropriate control for commanding a pyrotechnic event: it can be actuated by a dropped tool, a closing\n"
"lid, or a thumb that slipped. **FIRE needs a substantial panel-mount momentary button**, ideally\n"
"guarded. The tactile switch is retained for the continuity check only.\n\n"
"---\n\n## Reused from IGNIS v4 / 2v2 \u2014 with one important exception\n\n"
"`Pyros.SchDoc` in IGNIS v4 and 2v2 implements a two-channel pyro stage: `PYRO_CHx_GATE` through an\n"
"optocoupler to an S8050 NPN driving an NCE6005AR low-side MOSFET, with a second optocoupler across the\n"
"e-match returning `PYRO_CHx_CONT` for continuity. That continuity topology is **directly reusable** and\n"
"is the basis for the station's continuity check.\n\n"
"**The gate-drive half is not reusable.** In IGNIS the microcontroller gates the pyro channel. In\n"
"TALAVERA it must not \u2014 arming and firing are relay contacts and a hand-inserted plug (D-013). Porting\n"
"`Pyros.SchDoc` wholesale would reintroduce exactly the MCU-in-the-firing-path arrangement this redesign\n"
"exists to remove. Take the sense circuit; leave the gate drive.\n\n"
"One constraint carries over regardless: the continuity sense current flows **through the e-match**, so\n"
"`R_CONT` must hold it below the no-fire rating. That value cannot be computed until the e-match part is\n"
"known (open item 3).\n")
open(ROOT+"/fabrication/PARTS-LIST.md","w",encoding="utf-8").write(body)
print("written")
