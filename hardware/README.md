# Hardware

KiCad projects for the two TALAVERA boards.

| Project | Board | Outline |
|---|---|---|
| `talavera-bench/` | Bench board — mounts on the test stand | 100 × 80 mm **placeholder** |
| `talavera-station/` | Control station board — operator position, 20 m away | 80 × 60 mm **placeholder** |
| `libraries/` | Project symbols, footprints and 3D models | — |

---

## Status: skeletons only

> **The schematics are intentionally empty.** Gate 2 has not started and no circuit has been designed.
>
> Each schematic carries a single text block listing the non-negotiable design rules, so that the rules
> are visible in the tool where the work will happen rather than only in a document.
>
> Each PCB carries a rectangular `Edge.Cuts` outline at a placeholder size, the layer stack, and the
> design rules. No footprints are placed.

Opening either project and seeing an empty sheet is the expected result.

---

## KiCad version

Targets **KiCad 10.0**. File format versions were read from the demo projects shipped with the installed
KiCad rather than assumed:

| File | Format version | Generator |
|---|---|---|
| `.kicad_sch` | `20250610` | `eeschema` |
| `.kicad_pcb` | `20250513` | `pcbnew` |
| `.kicad_pro` | `meta.version 3` | — |

Opening these in an older KiCad will fail or force a downgrade. If you need an older version, say so
and the projects will be regenerated.

---

## Net classes

Defined up front so that **DRC enforces pyro separation**, rather than relying on a reviewer noticing a
thin trace. Nets are assigned by name pattern, so a correctly named net inherits the right rules
automatically.

| Class | Pattern | Clearance | Track width | Why |
|---|---|---|---|---|
| `PYRO` | `PYRO_*` | 1.00 mm | 2.00 mm | Firing current, and the widest clearance on the board |
| `SAFETY` | `ARM_*`, `FIRE_*`, `ESTOP_*` | 0.50 mm | 0.50 mm | Safety signalling |
| `POWER` | `+12V*`, `+5V*` | 0.40 mm | 1.00 mm | Supply rails |
| `ANALOG` | `LC_*`, `THRUST_*` | 0.30 mm | 0.30 mm | Load cell and thrust signal |
| `Default` | everything else | 0.25 mm | 0.30 mm | — |

**Use these prefixes when naming nets at Gate 2.** A firing net not named `PYRO_*` will silently inherit
`Default` rules, which is exactly the failure this scheme exists to prevent.

---

## Design rules that layout must satisfy (Gate 4)

1. Keep-out between the logger zone and the entire firing chain.
2. Connectors on the board edge.
3. Pin 1 marked on every connector, on silkscreen, readable after assembly.
4. Keyed, strain-relieved connectors on every external interface.
5. Analog return separated from high-current return; join at a single defined point.
6. Test points on every rail and every safety signal, probe-accessible with the board mounted.
7. Pyro traces routed away from the analog front end, never parallel to it.

---

## Running checks

KiCad is not run by the design assistant. To produce the reports for Gate 5, run these and paste back
the output:

```bash
kicad-cli sch erc --output erc-bench.rpt hardware/talavera-bench/talavera-bench.kicad_sch
```

```bash
kicad-cli pcb drc --output drc-bench.rpt hardware/talavera-bench/talavera-bench.kicad_pcb
```

Both write a plain-text report to the named file. The same two commands apply to `talavera-station`.
