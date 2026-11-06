# TALAVERA v1 — Decision Log

Project: replacement electronics for the Wirikuta 1.1 solid-motor static test bench
Organisation: Ignitia Rocket Lab — Tecnológico de Monterrey, Campus Guadalajara
Reference: *Manual de operaciones: WIRIKUTA 1.1 Banco de Pruebas*, August 2025

**Review owner: TBD — must be named before Gate 2.**

> No circuit in this project is approved. No output has been energized.
> Pyrotechnic, actuator, motor, high-current, battery and mains circuits require written
> sign-off from the named review owner.

---

## Decisions

| ID | Decision | Reason | Date | Approved by |
|----|----------|--------|------|-------------|
| D-001 | Source of truth is the Wirikuta operations manual, Aug 2025, extracted text layer | Only machine-readable record available | 2026-11-06 | pending |
| D-002 | Annex A and B treated as unavailable; KiCad sources requested | Raster images, no text layer | 2026-11-06 | pending |
| D-003 | Nothing energized; no circuit approved at any gate by the design assistant | Project safety rule | 2026-11-06 | standing |
| D-004 | Two Annex C firmware defects logged as rationale for hardware-defined logic | Verified in the source listings | 2026-11-06 | pending |
| D-005 | Environment figures recorded as **assumed** pending confirmation | No environmental spec in the manual | 2026-11-06 | pending |
| D-006 | Arm/fire path is a **wired umbilical**. No MCU on the safety path. | User decision at Gate 0 | 2026-11-06 | Cristian |
| D-007 | 20 m standoff is **below** the NAR/TRA reduced minimum of 22.5 m for H class | Manual pp. 7–8 | 2026-11-06 | noted deviation |
| D-008 | Igniter safe state is **SHORTED**, via a normally-closed contact | 20 m pickup loop; falls safe on power loss | 2026-11-06 | pending |
| D-009 | Firing pair is 16 AWG. Cable R and C confirmed non-binding at 20 m and 40 m. | Computed from standard AWG table | 2026-11-06 | pending |
| D-010 | Thrust signal leaves the bench **differential**, not single-ended | Long run beside a firing line; addresses p. 28 noise floor | 2026-11-06 | pending |
| D-011 | Design for a **20 m** umbilical, extensible to 40 m+ | User decision; deviation D-007 accepted | 2026-11-06 | Cristian |
| D-012 | Data logging stays on the **bench board**, as an isolated no-authority passenger | User decision | 2026-11-06 | Cristian |
| D-013 | Arming is a **bench arming plug** plus a **station key switch** — three series elements | User decision | 2026-11-06 | Cristian |
| D-014 | **Two boards**: one bench, one station. Drops the bench-to-bench JST-XH interconnect. | User decision | 2026-11-06 | Cristian |
| D-015 | **One** igniter channel | User decision | 2026-11-06 | Cristian |
| D-016 | **Two** umbilical cables: pyro pair isolated from the control/analog multicore | A firing transient at *t=0* beside a strain gauge corrupts the data | 2026-11-06 | pending |
| D-017 | LED beacon driven from the **real** ARM/FIRE signals, never a software report | The beacon must not be able to misreport state | 2026-11-06 | pending |
| D-018 | Logger has **no state machine and no command set**; it records whenever powered | Removes all firmware complexity; also yields a clean CSV with nothing to hand-strip (p. 27) | 2026-11-06 | pending |
| D-019 | Retain a differential thrust pair to the station for live readout and redundancy | A static fire is non-repeatable; a single SD write is a single point of failure | 2026-11-06 | pending |
| D-020 | Project preliminary name: **TALAVERA** | User decision | 2026-11-06 | Cristian |
| D-021 | Repository layout uses `docs/ hardware/ firmware/ fabrication/ analysis/ test/` | Follows the IGNIS-v5 README *style* but with a deeper folder tree, since this project has two boards plus manual, safety and bring-up documents | 2026-11-06 | pending |
| D-022 | Target **KiCad 10.0**. Format versions read from the installed demo projects rather than assumed. | KiCad 10.0 found at `C:\Program Files\KiCad\10.0` | 2026-11-06 | — |
| D-023 | Board outlines are **placeholders**: 100 × 80 mm bench, 80 × 60 mm station | Size target is an open item; noted in each PCB title block | 2026-11-06 | pending |
| D-024 | Net classes `PYRO`, `SAFETY`, `POWER`, `ANALOG` pre-defined with pattern assignment | Makes DRC itself enforce pyro clearance and trace width, instead of relying on reviewer attention | 2026-11-06 | pending |
| D-025 | Schematics committed **intentionally empty**, carrying only the safety ground rules as a text block | Gate 2 is not approved; the project skeleton must not imply a design exists | 2026-11-06 | — |
| D-026 | MIT licence plus an explicit safety notice disclaiming fitness | Hardware that fires pyrotechnics should not ship an unqualified permission grant | 2026-11-06 | pending |
| D-027 | **No GitHub remote created and nothing pushed.** Local repository only. | Publishing is the user's call, not the assistant's | 2026-11-06 | — |

---

## Pending decisions

| Question | Options | Blocks |
|---|---|---|
| Logger power domain | Upstream of master relay (recommended) / downstream shared rail / own battery | Gate 1 completion |
| Review owner | — | Gate 2 |
| Largest motor class | — | Standoff and connector sizing |
| Fabrication house, layers, size | — | Gates 4 and 6 |

---

## Revision history

| Rev | Date | Change |
|---|---|---|
| A | 2026-11-06 | Gate 0 complete. Repository and KiCad project skeletons created. |
