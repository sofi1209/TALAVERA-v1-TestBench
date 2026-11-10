# Handoff — TALAVERA v1

> **Status update, Batch 2, 10 November 2026.** The schematics are at **Rev A.2**: K3's coil follows
> FIRE, FIRE is a floating two-wire loop on a new pin map, a pre-arm continuity TEST exists in topology,
> the E-STOP has two channels and a latched ARM permit, and reverse polarity is a crowbar. All of it is
> pending Emilio's sign-off (D-074 to D-080). Read `docs/BATCH2-SAFETY-TOPOLOGY-2026-11-10.md` first.
> `trace_fire_loop.py` now takes **both** netlists and runs seven sections; a release run must pass the
> station netlist too. The A.1 note below still applies to everything else.
>
> **Status update, 10 November 2026.** This handoff was written on 6 November and its status tables are
> out of date. The project is now at **Rev A.1**: two independent audits of 9 Nov found that the bench
> could not fire and that `D_RP` was reversed, and both are corrected. The current state is in
> `README.md`, `docs/REV-A1-CHANGES-2026-11-09.md`, `docs/AUDIT-RECONCILIATION-2026-11-09.md` and
> `docs/LAYOUT-PLAN-REV-A1.md`; the decision log runs to D-073. §4.3 below is withdrawn (see its own
> note). The verification steps in §5 still apply, with one change: use `kicad-cli` from the installed
> KiCad (10.0.x) and a real Python 3 install.

Written 6 November 2026, at the end of the session that took this project from nothing to two audited
schematics. Read this before touching anything.

**Repository:** https://github.com/sofi1209/TALAVERA-v1-TestBench (public)
**Author:** Sofia Pacheco Leon · **Review owner:** Emilio Guadarrama
**State:** 23 commits, 43 files, working tree clean, 63 decisions logged, 19 open items.

---

## 1. What this is

Replacement electronics for **Wirikuta 1.1**, Ignitia's solid-motor static test bench. The point of the
redesign is one sentence: **no microcontroller takes part in arming, firing or emergency stop.** Those
are relay contacts, switches and a plug you insert by hand. A logger rides along with no authority over
anything.

Two boards: `talavera-bench` (on the test stand) and `talavera-station` (operator position, 20 m away),
joined by one 12-conductor umbilical.

Start with `README.md`, then `docs/SAFETY.md`. `docs/DECISION-LOG.md` has every decision with its
reason — D-001 to D-063. Do not re-litigate a decision without reading its entry first.

---

## 2. Where it actually stands

| Gate | State |
|---|---|
| 0 Requirements | Complete |
| 1 Architecture | Complete in substance, never formally signed |
| 2 Schematic | **Both boards drawn, audited, 10 of 12 findings fixed** |
| 3 Components | Partly done — main parts chosen, pyro and analog values blocked |
| 4 Layout | Not started |
| 5–7 | Not started |

Per **D-053**, Gates 2–5 proceed without per-gate sign-off. **Gate 6 (fabrication release) and bring-up
Stage 5 (live e-match) keep mandatory written sign-off from Emilio.** That line is not negotiable and
was reasoned through, not assumed — a drawing cannot hurt anyone; a board and an initiator can.

---

## 3. The two things that block real progress

Everything else can proceed around them.

| | Needed | Blocks |
|---|---|---|
| **O-1** | E-match part, **no-fire current**, all-fire current, resistance | `R_CONT`, fuse rating, all relay contact ratings, pyro trace width |
| **O-2** | Load cell make/model, bridge resistance, mV/V, rated excitation | ADS1220 PGA gain, whether the PGA common-mode limit bites, ratiometric reference |

Both are data only Ignitia can supply. **Do not guess either.** Every pyro and analog value in the
schematic is deliberately `TBD` pending them.

## 4. The three open design decisions

These need a human, not more analysis.

1. **M-1, thermal.** The bench drops 12 V → 3.3 V in one AMS1117: ~1.3 W in a SOT-223, ~133 °C junction
   at the assumed 55 °C ambient, against a 125 °C limit. The station already cascades 12→5→3.3; the
   bench does not. Cascade it, or put a cheap buck at 12→5 and keep an LDO for the last step so the
   analog front end still sees LDO ripple rejection.
2. **M-2, representation.** The sheet draws a bare WROOM-32D but the build sockets a DevKitC that
   already has its own regulator, EN network and USB bridge — and whose header does not carry nine of
   the drawn pins. The schematic does not represent what gets built.
3. **H-2 follow-on. ~~Sense current now flows through the e-match continuously.~~ WITHDRAWN — that is
   wrong.** Nothing sources that current: the `R_CONT` + opto branch sits between the two match
   terminals, no net imposes a potential difference across them, and the current is **zero**. Two
   independent audits caught the error on 9 November. The real defect is the opposite and worse — there
   was no working continuity check at all, and the firing loop had no return, so the bench could not
   fire. See `AUDIT-RECONCILIATION-2026-11-09.md` §1 and `REV-A1-CHANGES-2026-11-09.md`.
   The firing loop is fixed; **the continuity function is still a decision for Emilio (D-B)**, and any
   test must open the shunt, so the H2 induced-energy defence is absent while it is held.

---

## 5. Hard-won lessons — read these before editing the generators

The schematics are **generated**, not hand-drawn: `hardware/tools/gen_bench.py` and `gen_station.py`
on top of `ksch.py`. Regenerating is one command. Hand edits in KiCad will be overwritten.

```bash
cd hardware/tools && python gen_bench.py && python gen_station.py
```

Then validate. **All four steps, every time** — the first two are not sufficient, and the project has
the scars to prove it:

```bash
python hardware/tools/validate_sch.py hardware/talavera-bench/talavera-bench.kicad_sch hardware/talavera-station/talavera-station.kicad_sch
```

```bash
python hardware/tools/netlist.py hardware/talavera-bench/talavera-bench.kicad_sch
```

**3. Native KiCad ERC — not optional.** It had never been run on the bench board, and when it finally
was, the one error it reported led to a blocker: `D_RP` reversed, so nothing downstream of F1 was
powered. `validate_sch.py` passing is not ERC passing.

```bash
kicad-cli sch erc --format report --severity-all -o exports/ERC-bench.rpt hardware/talavera-bench/talavera-bench.kicad_sch
```

**4. The firing loop, as a loop.** ERC and the validator both answer "is this pin on that net". Neither
answers "can current get back to the battery". The Rev A board passed both while the firing loop had no
return at all and could not fire in any state.

```bash
kicad-cli sch export netlist --format kicadsexpr -o exports/bench.net hardware/talavera-bench/talavera-bench.kicad_sch && python hardware/tools/trace_fire_loop.py exports/bench.net
```

Every one of these exits non-zero on failure, so they can gate a release.

### Bugs that cost real time. Do not reintroduce them.

| What went wrong | Now guarded by |
|---|---|
| Raw newlines inside quoted strings — KiCad refused to load the file entirely | `esc()` / `unesc()` in `ksch.py`; validator errors on raw newlines |
| `place()` ignored the rotation angle when computing pin coordinates, so 35 rotated symbols had every wire drawn to the wrong place — **200 ERC errors** | Rotation transform in `place()`; validator computes pins the same way |
| Labels offset 0.5 mm from the wire end — "near enough" is not a connection | Validator requires exact coincidence |
| `GND_RTN` label used alongside `power:GND` symbols — two separate nets, relay coils never reached ground | Validator resolves nets and checks named power pins semantically |
| `+3V3` vs `+3V3_LOGGER` — **the same mistake again**, on the supply rail. No IC had power. | Same check; and `netlist.py` makes rail splits obvious |
| All four AMS1117 wired as if pin 1 were VI. It is **GND**. (1=GND, 2=VO, 3=VI) | Validator's power-pin semantic check |
| Five flyback diodes reversed — each a short across its coil | **Now automatic**: `validate_sch.py` rule 4g matches each diode against the relay coil nets and requires the cathode on A1. A sixth reversed diode, the series `D_RP`, was found on 9 November and is *not* covered — a series pass diode between two same-rank nets still needs `trace_fire_loop.py` or a human |
| `validate_sch.py` reporting a byte-identical "0 errors" while checking nothing, because `SYMDIR` was hardcoded to one machine inside `except Exception: continue` | `SYMDIR` is now resolved from the environment or by globbing; unresolved symbols are a hard error and print `structural_checks: SKIPPED` |
| The firing loop having no return, so the bench could not fire — passed by ERC, by this validator, and by a completed hand audit | `trace_fire_loop.py`, which asks the loop question per relay state and self-tests against the broken netlist |
| A patch comment swallowed the rest of a line holding two statements, leaving the SP3485 with no ground | Validator reports floating pins |
| Symbols placed off the 1.27 mm grid — 204 ERC warnings | `place()` and `stub()` snap automatically |

**The meta-lesson:** ERC passing and `validate_sch.py` passing means *connected*, not *correct*. The
audit found twelve faults in a revision both tools called clean. Read the netlist.

### Shell gotcha

Heredocs in this environment mangle backslashes. Writing Python with `\n` inside strings via a bash
heredoc produces real newlines and a syntax error. Use the Write/Edit tools for anything containing
escapes.

---

## 6. Component decisions already settled

| Item | Part | Why |
|---|---|---|
| Converter | **ADS1220IPWR** (LCSC C48263) | 24-bit, **SPI** not I²C, integrated PGA, stocked at UNIT *and* LCSC |
| Relays ×4 | **SRD-12VDC-SL-C** (C30431) | One SPDT part for all four; K3 wired **NC** for the shunt |
| RS-485 | **SP3485EN-L/TR** (C8963) | ~$0.20; isolation moved to the station, powered by the laptop's USB, so no isolated DC-DC |
| microSD | **THD2528-11SD-GF** (C283232) | From the IGNIS v5 / MAGNIS v1 lists, with `SD_DETECT` |
| Logger | ESP32-DevKitC V4, socketed | Radios stopped at boot — EMI, not command risk |
| AD620 | **Not populated.** DIP-8 socket + 0 Ω link network | Both front ends A/B testable on one board |

Selection policy (**D-052**): cheap, reliably sourced from LCSC or UNIT, hand-solderable. **Safety
ratings are exempt from the price rule.**

Rev A is a **bare PCB, hand-assembled** (D-051), not JLCPCB-assembled.

---

## 7. Known-good reference material

- `IGNIS-v5-FlightComputer` on GitHub — its `Storage.SchDoc` gave the microSD topology, and its
  `DataLogger.h` documents the same I²C trouble that drove the move to SPI.
- IGNIS v4 / 2v2 `Pyros.SchDoc` — the opto-isolated **continuity sense** was adopted. Its **gate drive
  was deliberately not adopted**: in IGNIS the MCU gates the pyro channel, which is exactly what this
  redesign removes (D-045).
- The Wirikuta operations manual — page references throughout the docs are to its own footer numbers.

---

## 8. What to do first in the new session

1. Install the skills — see `.claude/skills/README.md`. They could not be loaded in the previous
   session and were **not** fabricated.
2. Re-run the validator and `netlist.py` on both boards. Confirm 0 errors before trusting anything.
3. Ask Sofia for O-1 and O-2 if they have arrived.
4. Put M-1, M-2 and the H-2 follow-on to Emilio.
5. Only then consider Gate 4.

Do **not** export a fabrication package, order anything, or connect an initiator. Gate 6 and bring-up
Stage 5 need Emilio's written sign-off.
