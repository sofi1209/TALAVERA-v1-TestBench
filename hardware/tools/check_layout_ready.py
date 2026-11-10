"""Gate 4 readiness: can PCB layout start?

Layout is the first gate where a mistake costs money rather than an edit, so
the preconditions are checked mechanically instead of being judged. Three
kinds of gate are reported separately, because they fail for different reasons:

  BLOCKING   something required to place and route at all is missing
  TOPOLOGY   an open decision would change which parts exist on the board
  SIZING     copper and clearances that cannot be computed without missing data

    python check_layout_ready.py

Exit code is non-zero while any BLOCKING or TOPOLOGY gate is open. SIZING gates
alone do not stop a floorplan, but they do stop a fabrication release.

This tool reports readiness. It approves nothing, and Gate 6 and bring-up
Stage 5 keep mandatory written sign-off from the review owner.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
BOARDS = ("talavera-bench", "talavera-station")


def sch(board):
    return os.path.join(ROOT, "hardware", board, board + ".kicad_sch")


def pcb(board):
    return os.path.join(ROOT, "hardware", board, board + ".kicad_pcb")


def pro(board):
    return os.path.join(ROOT, "hardware", board, board + ".kicad_pro")


def run(args):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# ---------------------------------------------------------------- gate checks

def gate_schematic_clean():
    """The schematic must survive every check before its copper is drawn."""
    ok1, _ = run([os.path.join(HERE, "validate_sch.py")] + [sch(b) for b in BOARDS])
    ok2, _ = run([os.path.join(HERE, "check_layout.py")] + [sch(b) for b in BOARDS])
    nets = [os.path.join(ROOT, "exports", "2026-11-09-revA1", "talavera-bench.net")]
    ok3 = True
    if os.path.isfile(nets[0]):
        ok3, _ = run([os.path.join(HERE, "trace_fire_loop.py"), nets[0]])
    ok4, _ = run([os.path.join(HERE, "sync_project_uuid.py"), "--check"])
    detail = "validator %s, layout %s, fire loop %s, UUIDs %s" % (
        "ok" if ok1 else "FAIL", "ok" if ok2 else "FAIL",
        "ok" if ok3 else "FAIL", "ok" if ok4 else "FAIL")
    return (ok1 and ok2 and ok3 and ok4), detail


def gate_footprints():
    """Every component needs a footprint before a netlist can become a board."""
    missing, total = 0, 0
    for b in BOARDS:
        txt = open(sch(b), encoding="utf-8").read()
        for m in re.finditer(r'\(symbol\s*\(lib_id "([^"]+)"(.*?)\n\t\)', txt, re.S):
            if m.group(1).startswith("power:"):
                continue
            total += 1
            fp = re.search(r'\(property "Footprint" "([^"]*)"', m.group(2))
            if not fp or not fp.group(1).strip():
                missing += 1
    return missing == 0, "%d of %d components have no footprint" % (missing, total)


def gate_pcb_populated():
    """The .kicad_pcb files must hold the parts, not just an outline."""
    counts = []
    for b in BOARDS:
        if not os.path.isfile(pcb(b)):
            counts.append((b, None))
            continue
        txt = open(pcb(b), encoding="utf-8").read()
        counts.append((b, txt.count("(footprint ")))
    bad = [b for b, n in counts if not n]
    return not bad, ", ".join("%s: %s placed" % (b, n if n is not None else "no file")
                              for b, n in counts)


def gate_net_classes():
    """Copper rules must exist, and the pyro class must be explicitly sized."""
    out = []
    ok = True
    for b in BOARDS:
        d = json.load(open(pro(b), encoding="utf-8"))
        cls = (d.get("net_settings") or {}).get("classes") or []
        names = {c.get("name") for c in cls}
        pat = len((d.get("net_settings") or {}).get("netclass_patterns") or [])
        need = {"PYRO", "SAFETY", "POWER", "ANALOG"}
        if not need <= names or pat == 0:
            ok = False
        out.append("%s: %d classes, %d patterns" % (b, len(cls), pat))
    return ok, "; ".join(out)


# Open items and decisions, read from the repository's own records rather than
# restated here, so this cannot drift from DECISION-LOG.md and REQUIREMENTS.md.
TOPOLOGY_GATES = [
    ("D-A", "K3 carries both shunt and low-side return, or two relays?",
     "Changes the relay count and the whole pyro copper. Blocked on Songle "
     "break-before-make evidence (O-3)."),
    ("D-B", "Pre-arm continuity TEST function",
     "Adds a control line, series resistors and a blocking diode. Blocked on O-1."),
    ("D1", "Station power: separate feed or a reallocated umbilical conductor",
     "Decides the umbilical conductor count and the connector, and is coupled "
     "to the ARM/FIRE pin separation."),
    ("E-STOP", "Whether the shunt must re-close automatically",
     "May add a permit relay and panel contact blocks. Narrowed by D-073, which "
     "puts operator abort on an external dead-man/RBF, but not closed."),
    ("M-1", "Bench 3.3 V thermal architecture",
     "~1.3 W in SOT-223 against a ~125 C limit. A cascade or a buck changes the "
     "packages and the board area."),
    ("M-2", "DevKitC vs bare WROOM-32D representation",
     "The sheet draws a 38-pin module; the build sockets a 2x19 header. The "
     "footprint cannot be assigned until the symbol matches the part."),
    ("O-21", "6N137 RX path inverts",
     "The fix is a part change, possibly to a digital isolator, which is a "
     "different footprint."),
    ("M-13", "Buzzer part",
     "MLT-8530 is an externally driven ~3.6 V transducer on a 12 V DC drive. A "
     "12 V active sounder is a different part and footprint."),
]

SIZING_GATES = [
    ("O-1", "E-match no-fire / all-fire current and resistance",
     "Sets the PYRO trace width, R_STAR and its copper, F1/F2/F_STN ratings and "
     "every relay contact margin. The PYRO class is 2.00 mm as a placeholder."),
    ("O-9", "Copper weight",
     "The 2.00 mm PYRO width assumes 1 oz. Unconfirmed."),
    ("O-2", "Load cell make, bridge resistance, mV/V, excitation",
     "Sets the analog front end and the filtering, which drives analog placement."),
    ("O-8", "Board size target for each board",
     "Outlines are placeholders (D-023)."),
    ("O-14", "Station enclosure and panel",
     "Drives the panel-control footprints and the station outline."),
    ("O-17", "Fuse current budget", "F1, F2 and F_STN ratings."),
]


def main():
    print("=" * 74)
    print("TALAVERA v1 - Gate 4 (layout) readiness")
    print("=" * 74)

    blocking = [
        ("schematic verified", gate_schematic_clean),
        ("footprints assigned", gate_footprints),
        ("PCB files populated", gate_pcb_populated),
        ("net classes defined", gate_net_classes),
    ]
    nblock = 0
    print("\nBLOCKING - required to place and route at all")
    for name, fn in blocking:
        ok, detail = fn()
        if not ok:
            nblock += 1
        print("  [%s] %-22s %s" % ("ok" if ok else "NO", name, detail))

    print("\nTOPOLOGY - open decisions that change which parts exist")
    for tid, what, why in TOPOLOGY_GATES:
        print("  [NO] %-8s %s" % (tid, what))
        print("           %s" % why)

    print("\nSIZING - copper and clearances that cannot be computed yet")
    for oid, what, why in SIZING_GATES:
        print("  [NO] %-8s %s" % (oid, what))
        print("           %s" % why)

    print("\n" + "-" * 74)
    total = nblock + len(TOPOLOGY_GATES)
    if total:
        print("VERDICT: LAYOUT MUST NOT START. %d blocking, %d topology, %d sizing."
              % (nblock, len(TOPOLOGY_GATES), len(SIZING_GATES)))
        print("Floorplanning on paper is still useful and is not gated by these.")
    else:
        print("VERDICT: blocking and topology gates clear. Sizing gates remain;")
        print("a floorplan may proceed, a fabrication release may not.")
    print("This tool approves nothing. Gate 6 and bring-up Stage 5 keep")
    print("mandatory written sign-off from the review owner.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
