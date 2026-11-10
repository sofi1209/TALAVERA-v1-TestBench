"""Trace the bench firing loop as a CLOSED CIRCUIT, per relay state.

Why this exists
---------------
ERC and validate_sch.py both answer "is this pin connected to that net". Neither
answers "can current actually flow from the battery, through the initiator, and
back to the battery". The Rev A schematic passed both tools while PYRO_MATCH_N
reached only K3's NC contact and the opto LED - each of which led back to
PYRO_MATCH_P - so the firing loop had NO RETURN and the bench could not fire in
any state. Two independent audits found it; the project's own tooling could not,
and neither could I: I verified the sense branch was continuous and called it
energised without asking what drove it.

Continuity is a LOOP question, never a path question. This script asks the loop
question, from KiCad's own netlist export, and prints the state table.

    python trace_fire_loop.py ../../exports/<dir>/talavera-bench.net

Exit code is non-zero if any state disagrees with the expected safety table, so
it can gate a release the way DRC does.

It models ideal contacts and says nothing about contact ratings, timing,
break-before-make, welded contacts or anything thermal. It is a connectivity
proof only, and it approves nothing.
"""
import re
import sys
import collections

PLUG_IN = True        # J_ARM arming plug inserted by hand at the bench
MATCH_FITTED = True   # P1 carries an intact initiator


def load(path):
    """ref -> {pin: net} from a kicadsexpr netlist export."""
    txt = open(path, encoding="utf-8").read()
    comp = collections.defaultdict(dict)
    pat = re.compile(
        r'\(net\s*\(code "\d+"\)\s*\(name "([^"]+)"\)(.*?)(?=\n\t\t\(net\s|\n\t\)\s*\Z)',
        re.S)
    node = re.compile(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)')
    for m in pat.finditer(txt):
        net = m.group(1)
        for ref, pin in node.findall(m.group(2)):
            comp[ref][pin] = net
    return comp


# Only these carry FIRE current. A 10 k pull-up is not a conductor for this
# question, and treating every resistor and diode as one is how a tracer starts
# "finding" loops that cannot pass an amp - the failure mode that made the
# previous session's reach2.py print a ground path that was not there.
# Current-limiting parts and indicator branches are examined separately, as
# sneak paths, which is a different question with a different answer.
POWER_PARTS = ("F", "K", "J_ARM", "P1", "R_STAR")


def is_power_part(ref):
    if ref.startswith("R_STAR"):          # 0 R star bond is a real conductor
        return True
    if ref.startswith("R"):               # every other resistor limits current
        return False
    if ref.startswith("D"):
        # Diodes go in as DIRECTED anode->cathode edges. D_RP is a series
        # element in the supply path and must conduct forward or the feed side
        # is cut; the flybacks and indicator LEDs are directed into coil nets
        # and indicator branches that carry no contact, so they lead nowhere.
        # Direction is what makes this safe - and is what caught D_RP reversed.
        return True
    if ref.startswith("F"):
        return True
    if ref.startswith("J_ARM") or ref == "P1":
        return True
    return ref.startswith("K") and ref[1:2].isdigit()


def edges(comp, energised, power_only=True):
    """Conducting pin pairs for this state, as (net_a, net_b, directed, ref)."""
    out = []

    def add(ref, a, b, directed=False):
        pins = comp.get(ref, {})
        if a in pins and b in pins:
            out.append((pins[a], pins[b], directed, ref))

    for ref in comp:
        if power_only and not is_power_part(ref):
            continue
        if ref.startswith("F") or ref.startswith("R"):
            add(ref, '1', '2')
        elif ref.startswith("D"):          # pin 2 = A, pin 1 = K: anode -> cathode
            add(ref, '2', '1', directed=True)
        elif ref.startswith("K") and ref[1:2].isdigit():
            # A Form C pole makes exactly one contact. Modelling both as closed
            # is what let an earlier tracer walk through a relay in both
            # directions at once.
            if energised.get(ref):
                add(ref, '11', '14')       # COM - NO
            else:
                add(ref, '11', '12')       # COM - NC
    if PLUG_IN:
        add("J_ARM1", '1', '2')
    if MATCH_FITTED and not power_only:
        pass                               # P1 handled by the caller when split
    if not power_only:
        add("U_CONT1", '1', '2', directed=True)
    return out


def reaches(comp, energised, start, goal, skip=(), power_only=True):
    """Shortest conducting path start -> goal, or None. Stops AT the goal."""
    adj = collections.defaultdict(list)
    for a, b, directed, ref in edges(comp, energised, power_only):
        if ref in skip:
            continue
        adj[a].append((b, ref))
        if not directed:
            adj[b].append((a, ref))
    q = collections.deque([(start, [start])])
    seen = {start}
    while q:
        net, path = q.popleft()
        if net == goal:
            return path                    # terminate here, never wander past it
        for nxt, _ref in adj[net]:
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [nxt]))
    return None


def fire_loop(comp, energised):
    """Current must ENTER one initiator terminal and LEAVE the other.

    Asked as two independent reachability questions with P1 removed from the
    graph, rather than as one path carrying a "did I pass through it" flag -
    that flag let the search reach the goal and keep going, which manufactures
    loops that do not exist.
    """
    a, b = comp["P1"]['1'], comp["P1"]['2']
    for term_in, term_out in ((a, b), (b, a)):
        feed = reaches(comp, energised, BATT_P, term_in, skip=("P1",))
        ret = reaches(comp, energised, term_out, BATT_N, skip=("P1",))
        if feed and ret:
            return feed, ret
    return None, None


# K4 is held in by its coil through the E-STOP loop; K1 and K3 follow the ARM
# key; K2 follows the FIRE button, which is fed from ARM_LINE.
STATES = [
    #  name                K4     K1     K2     K3     fire current expected?
    ("SAFE, estop ok",     True,  False, False, False, False),
    ("ARMED",              True,  True,  False, True,  False),
    ("FIRE held",          True,  True,  True,  True,  True),
    ("E-STOP pressed",     False, True,  True,  True,  False),
    ("FIRE without ARM",   True,  False, True,  False, False),
]

BATT_P = "/+12V_RAW"
BATT_N = "GND"


def main(path):
    comp = load(path)
    for req in ("P1", "J_ARM1", "K3"):
        if req not in comp:
            print("  !! %s not in the netlist - cannot trace" % req)
            return 2
    if "R_STAR1" not in comp:
        print("  note: no R_STAR star bond in this netlist (pre-Rev A.1)\n")

    print("Firing loop trace:  %s" % path.split("/")[-1])
    print("  plug inserted = %s, match fitted = %s" % (PLUG_IN, MATCH_FITTED))
    print("  looking for a closed path %s -> P1 -> %s\n" % (BATT_P, BATT_N))
    print("  %-20s %-5s %-5s %-5s %-5s  %-9s %s"
          % ("state", "K4", "K1", "K2", "K3", "fire", "verdict"))

    bad = 0
    fire_path = None
    for name, k4, k1, k2, k3, expect in STATES:
        en = {"K4": k4, "K1": k1, "K2": k2, "K3": k3}
        feed, ret = fire_loop(comp, en)
        got = feed is not None
        if got and expect:
            fire_path = (feed, ret)
        ok = got == expect
        bad += 0 if ok else 1
        print("  %-20s %-5s %-5s %-5s %-5s  %-9s %s"
              % (name, k4, k1, k2, k3,
                 "FLOWS" if got else "none",
                 "ok" if ok else "*** MISMATCH, expected %s ***"
                 % ("FLOWS" if expect else "none")))

    if fire_path:
        print("\n  the firing loop, FIRE held:")
        print("    feed   %s" % " -> ".join(fire_path[0]))
        print("    match  %s -> %s" % (comp["P1"]['1'], comp["P1"]['2']))
        print("    return %s" % " -> ".join(fire_path[1]))

    print()
    # The shunt must short the initiator whenever disarmed, and that short must
    # NOT also tie the initiator to the supply return.
    dis = {"K4": True, "K1": False, "K2": False, "K3": False}
    a, b = comp["P1"]['1'], comp["P1"]['2']
    shunt = reaches(comp, dis, a, b, skip=("P1",))
    print("  disarmed: initiator shorted by the shunt           : %s"
          % ("yes" if shunt else "NO - SHUNT MISSING"))
    if not shunt:
        bad += 1
    to_rtn = reaches(comp, dis, a, BATT_N, skip=("P1",))
    print("  disarmed: shunted pair isolated from the return    : %s"
          % ("NO - tied to return" if to_rtn else "yes"))
    if to_rtn:
        bad += 1
    arm = {"K4": True, "K1": True, "K2": False, "K3": True}
    still = reaches(comp, arm, a, b, skip=("P1",))
    print("  armed:    shunt released across the initiator      : %s"
          % ("NO - still shorted" if still else "yes"))
    if still:
        bad += 1
    low = reaches(comp, arm, b, BATT_N, skip=("P1",))
    print("  armed:    low side tied to the supply return       : %s"
          % ("yes" if low else "NO - return still open"))
    if not low:
        bad += 1

    print("\n  %s" % ("ALL STATES AS EXPECTED" if not bad
                      else "%d DISAGREEMENT(S)" % bad))
    print("  Connectivity only. Contact ratings, timing, break-before-make and")
    print("  welded-contact behaviour are NOT covered. Approves nothing.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "../../exports/2026-11-09-revA1/talavera-bench.net"))
