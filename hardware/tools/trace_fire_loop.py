"""Trace the bench firing loop as a CLOSED CIRCUIT, per relay state, under faults.

Why this exists
---------------
ERC and validate_sch.py both answer "is this pin connected to that net". Neither
answers "can current actually flow from the battery, through the initiator, and
back to the battery". The Rev A schematic passed both tools while PYRO_MATCH_N
reached only K3's NC contact and the opto LED - each of which led back to
PYRO_MATCH_P - so the firing loop had NO RETURN and the bench could not fire in
any state. Continuity is a LOOP question, never a path question.

    python trace_fire_loop.py <bench.net> [<station.net>]

Sections (Batch 2, 10 November 2026 - every case below is a failure mode found
in the Batch 2 analysis, and each one gates the exit code):

  1. state table      - fire current only with FIRE held (K3 now follows FIRE)
  2. structure        - shunt closed and isolated from the return in SAFE and
                        ARMED; released only in FIRE / TEST
  3. TEST path        - test source dead while K1 is in; test current only
                        through the match; no sneak path that reads "good"
  4. dead short       - no state shorts the battery around the initiator
  5. contact faults   - every single relay fault (NO welded, stuck released,
                        changeover bridged = make-before-break) in every state;
                        double faults that fire are listed, not gated
  6. reverse polarity - a reversed battery has a crowbar path through F1
  7. umbilical shorts - (needs the station netlist) DC solve of every pair of
                        umbilical conductors shorted, in every operating state,
                        against the relay coil limits of the SRD datasheet

Exit code is non-zero if any gated check fails, so it can gate a release the
way DRC does.

LIMITS. Sections 1-6 are connectivity with ideal contacts. Section 7 is a DC
model with ideal diodes, nominal coil resistance and no cable resistance. None
of it covers transients, induced energy, arcing, contact ratings, timing or
anything thermal, and NONE OF IT APPROVES ANYTHING.
"""
import collections
import itertools
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import umbilical  # noqa: E402

PLUG_IN = True        # J_ARM arming plug inserted by hand at the bench
MATCH_FITTED = True   # P1 carries an intact initiator


# ----------------------------------------------------------------- netlists
def _blocks(txt):
    pat = re.compile(
        r'\(net\s*\(code "\d+"\)\s*\(name "([^"]+)"\)(.*?)(?=\n\t\t\(net\s|\n\t\)\s*\Z)',
        re.S)
    return pat.finditer(txt)


def load(path):
    """ref -> {pin: net} from a kicadsexpr netlist export."""
    txt = open(path, encoding="utf-8").read()
    comp = collections.defaultdict(dict)
    node = re.compile(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)')
    for m in _blocks(txt):
        net = m.group(1)
        for ref, pin in node.findall(m.group(2)):
            comp[ref][pin] = net
    return comp


def load_parts(path):
    """ref -> {value, lib, part, dnp} from the (components ...) section."""
    txt = open(path, encoding="utf-8").read()
    parts = {}
    heads = list(re.finditer(r'\(comp\s*\(ref "([^"]+)"\)', txt))
    end = txt.find("(libparts")
    for i, m in enumerate(heads):
        ref = m.group(1)
        stop = heads[i + 1].start() if i + 1 < len(heads) else (end if end > 0 else len(txt))
        body = txt[m.end():stop]
        v = re.search(r'\(value "([^"]*)"\)', body)
        lib = re.search(r'\(lib "([^"]*)"\)', body)
        part = re.search(r'\(part "([^"]*)"\)', body)
        parts[ref] = {"value": v.group(1) if v else "",
                      "lib": lib.group(1) if lib else "",
                      "part": part.group(1) if part else "",
                      "dnp": '(name "dnp")' in body}
    return parts


# ------------------------------------------------- section 1-6: contact graph
def is_power_part(ref):
    """Parts that can carry FIRE current. A 10 k pull-up is not a conductor for
    this question, and treating every resistor as one is how a tracer starts
    "finding" loops that cannot pass an amp."""
    if ref.startswith("R_STAR"):          # 0 R star bond is a real conductor
        return True
    if ref.startswith("R"):               # every other resistor limits current
        return False
    if ref.startswith("D"):
        # Diodes go in as DIRECTED anode->cathode edges: the crowbar, the
        # flybacks, the K3 OR diodes and the TEST blocking diode all lead
        # nowhere a contact can reach unless their direction allows it.
        return True
    if ref.startswith("F"):
        return True
    if ref.startswith("J_ARM") or ref == "P1":
        return True
    return ref.startswith("K") and ref[1:2].isdigit()


FAULTS = ("NO welded", "stuck released", "bridged (make-before-break)")


def contacts(ref, on, fault):
    """Closed contact pairs of one Form C pole. A pole makes exactly one contact
    unless it is faulted - modelling both as closed in normal operation is what
    let an earlier tracer walk through a relay in both directions at once."""
    if fault == "NO welded":
        return [('11', '14')]
    if fault == "stuck released":
        return [('11', '12')]
    if fault == "bridged (make-before-break)":
        return [('11', '14'), ('11', '12')]
    return [('11', '14')] if on else [('11', '12')]


def edges(comp, energised, power_only=True, faults=None, with_match=False):
    """Conducting pin pairs for this state, as (net_a, net_b, directed, ref)."""
    faults = faults or {}
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
            for a, b in contacts(ref, energised.get(ref), faults.get(ref)):
                add(ref, a, b)
    if PLUG_IN:
        add("J_ARM1", '1', '2')
    if with_match and MATCH_FITTED:
        add("P1", '1', '2')
    if not power_only:
        add("U_CONT1", '1', '2', directed=True)   # the test-current opto LED
    return out


def reaches(comp, energised, start, goal, skip=(), power_only=True, faults=None,
            with_match=False):
    """Shortest conducting path start -> goal, or None. Stops AT the goal."""
    adj = collections.defaultdict(list)
    for a, b, directed, ref in edges(comp, energised, power_only, faults, with_match):
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


def fire_loop(comp, energised, faults=None):
    """Current must ENTER one initiator terminal and LEAVE the other, asked as
    two independent reachability questions with P1 removed from the graph."""
    a, b = comp["P1"]['1'], comp["P1"]['2']
    for term_in, term_out in ((a, b), (b, a)):
        feed = reaches(comp, energised, BATT_P, term_in, skip=("P1",), faults=faults)
        ret = reaches(comp, energised, term_out, BATT_N, skip=("P1",), faults=faults)
        if feed and ret:
            return feed, ret
    return None, None


# Batch 2 relay drive (PROVISIONAL, not approved):
#   K4 master   - held by its coil through E-STOP channel 1
#   K1 arm      - ARM_LINE, from the station key via the K5 permit (channel 2)
#   K2 fire     - floating FIRE_P / FIRE_N loop, only while FIRE is held
#   K3 shunt    - FIRE_P (or TEST_LINE) through D_K3F / D_K3T, returned on FIRE_N
STATES = [
    #  name                        K4     K1     K2     K3     fire expected?
    ("SAFE",                       True,  False, False, False, False),
    ("TEST held",                  True,  False, False, True,  False),
    ("ARMED",                      True,  True,  False, False, False),
    ("FIRE held",                  True,  True,  True,  True,  True),
    ("E-STOP, both channels",      False, False, False, False, False),
    ("E-STOP, channel 2 failed",   False, True,  True,  True,  False),
    ("E-STOP, channel 1 failed",   True,  False, False, False, False),
    ("FIRE contacts, no ARM",      True,  False, True,  True,  False),
]

OPERATING = ("SAFE", "TEST held", "ARMED", "FIRE held", "E-STOP, both channels")

BATT_P = "/+12V_RAW"
BATT_N = "GND"


def en_of(k4, k1, k2, k3):
    return {"K4": k4, "K1": k1, "K2": k2, "K3": k3}


def section_states(comp):
    bad = 0
    print("  1. STATE TABLE")
    print("  %-26s %-5s %-5s %-5s %-5s  %-6s %s"
          % ("state", "K4", "K1", "K2", "K3", "fire", "verdict"))
    fire_path = None
    for name, k4, k1, k2, k3, expect in STATES:
        feed, ret = fire_loop(comp, en_of(k4, k1, k2, k3))
        got = feed is not None
        if got and expect:
            fire_path = (feed, ret)
        ok = got == expect
        bad += 0 if ok else 1
        print("  %-26s %-5s %-5s %-5s %-5s  %-6s %s"
              % (name, k4, k1, k2, k3, "FLOWS" if got else "none",
                 "ok" if ok else "*** MISMATCH, expected %s ***"
                 % ("FLOWS" if expect else "none")))
    if fire_path:
        print("\n  the firing loop, FIRE held:")
        print("    feed   %s" % " -> ".join(fire_path[0]))
        print("    match  %s -> %s" % (comp["P1"]['1'], comp["P1"]['2']))
        print("    return %s" % " -> ".join(fire_path[1]))
    return bad


def section_structure(comp):
    """The shunt must short the initiator, isolated from the return, whenever
    FIRE and TEST are not held - which now includes the whole ARMED wait."""
    bad = 0
    a, b = comp["P1"]['1'], comp["P1"]['2']
    print("\n  2. SHUNT AND RETURN")

    def line(text, good, msg_bad):
        nonlocal bad
        print("  %-58s: %s" % (text, "yes" if good else msg_bad))
        bad += 0 if good else 1

    for name, en in (("SAFE", en_of(True, False, False, False)),
                     ("ARMED", en_of(True, True, False, False))):
        line("%s: initiator shorted by the shunt" % name,
             reaches(comp, en, a, b, skip=("P1",)), "NO - SHUNT MISSING")
        line("%s: shunted pair isolated from the return" % name,
             not reaches(comp, en, a, BATT_N, skip=("P1",)), "NO - tied to return")
    for name, en in (("FIRE held", en_of(True, True, True, True)),
                     ("TEST held", en_of(True, False, False, True))):
        line("%s: shunt released" % name,
             not reaches(comp, en, a, b, skip=("P1",)), "NO - still shorted")
        line("%s: low side tied to the supply return" % name,
             reaches(comp, en, b, BATT_N, skip=("P1",)), "NO - return open")
    return bad


def section_test(comp):
    """P-01: the continuity TEST must source no current while armed, must pass
    its current only through the initiator, and must be dark when not held."""
    bad = 0
    print("\n  3. CONTINUITY TEST PATH")
    if "U_CONT1" not in comp or "12" not in comp.get("K1", {}):
        print("  !! U_CONT1 or K1 NC not on a net - TEST path not drawn")
        return 1
    src = comp["K1"]["12"]
    tc = comp["U_CONT1"]["2"]          # opto LED cathode: downstream of the sense

    def line(text, good, msg_bad):
        nonlocal bad
        print("  %-58s: %s" % (text, "yes" if good else msg_bad))
        bad += 0 if good else 1

    for name, en in (("ARMED", en_of(True, True, False, False)),
                     ("FIRE held", en_of(True, True, True, True))):
        line("%s: test source %s dead" % (name, src),
             not reaches(comp, en, BATT_P, src), "NO - TEST SOURCE LIVE WHILE ARMED")
    test = en_of(True, False, False, True)
    line("TEST held: test source live",
         reaches(comp, test, BATT_P, src), "NO - no source")
    line("TEST held: test current returns THROUGH the initiator",
         reaches(comp, test, tc, BATT_N, power_only=False, with_match=True),
         "NO - test loop open")
    line("TEST held, match removed: no sneak path to ground",
         not reaches(comp, test, tc, BATT_N, power_only=False, with_match=False),
         "NO - SNEAK PATH, lamp would read good with no match")
    line("SAFE (TEST not held): no test current",
         not reaches(comp, en_of(True, False, False, False), tc, BATT_N,
                     power_only=False, with_match=True),
         "NO - test current flows at SAFE")
    return bad


def section_dead_short(comp):
    bad = 0
    print("\n  4. BATTERY DEAD SHORT AROUND THE INITIATOR")
    for name, k4, k1, k2, k3, _e in STATES:
        p = reaches(comp, en_of(k4, k1, k2, k3), BATT_P, BATT_N, skip=("P1",))
        if p:
            bad += 1
            print("  *** %s: battery shorted: %s" % (name, " -> ".join(p)))
    print("  %s" % ("none in any state" if not bad else "%d state(s) shorted" % bad))
    return bad


def section_faults(comp):
    """Every single relay fault in every state. Gated: any fire current in a
    state that must not fire. Reported: battery shorts under a fault (fuse
    clears, not ignition) and double faults that fire."""
    bad = 0
    relays = ["K1", "K2", "K3", "K4"]
    singles = [(r, f) for r in relays for f in FAULTS]
    # Faults go on top of HEALTHY operating states only. "E-STOP, channel 2
    # failed" and "FIRE contacts, no ARM" are already failure scenarios, so a
    # relay fault on top of them is a double fault, counted below instead.
    healthy = [s for s in STATES if s[0] in OPERATING]
    print("\n  5. RELAY CONTACT FAULTS (%d single faults x %d operating states)"
          % (len(singles), len(healthy)))
    shorts = []
    for r, f in singles:
        for name, k4, k1, k2, k3, expect in healthy:
            en = en_of(k4, k1, k2, k3)
            feed, _ret = fire_loop(comp, en, {r: f})
            if feed and not expect:
                bad += 1
                print("  *** SINGLE FAULT FIRES: %s %s, in %s" % (r, f, name))
            if reaches(comp, en, BATT_P, BATT_N, skip=("P1",), faults={r: f}):
                shorts.append("%s %s, in %s" % (r, f, name))
    if not bad:
        print("  no single contact fault fires in any state that must not fire")
    for s_ in shorts:
        print("  note: battery shorted around the initiator (F1 clears, no "
              "ignition): %s" % s_)
    doubles = []
    quiet = [s for s in STATES if s[0] in ("SAFE", "TEST held", "ARMED")]
    for (r1, f1), (r2, f2) in itertools.combinations(singles, 2):
        if r1 == r2:
            continue
        for name, k4, k1, k2, k3, _e in quiet:
            if fire_loop(comp, en_of(k4, k1, k2, k3), {r1: f1, r2: f2})[0]:
                doubles.append("%s %s + %s %s, in %s" % (r1, f1, r2, f2, name))
    print("  double faults that fire in SAFE / TEST / ARMED (reported, not gated): %d"
          % len(doubles))
    for d in doubles:
        print("    %s" % d)
    return bad


def section_reverse(comp):
    """A reversed battery must find a crowbar path, and that path must pass
    through F1 so the fuse clears it."""
    print("\n  6. REVERSE POLARITY")
    safe = en_of(True, False, False, False)
    via = reaches(comp, safe, BATT_N, BATT_P)
    no_fuse = reaches(comp, safe, BATT_N, BATT_P, skip=("F1",))
    print("  %-58s: %s" % ("reversed battery: crowbar path exists",
                           " -> ".join(via) if via else "NO - NO CROWBAR"))
    print("  %-58s: %s" % ("reversed battery: that path passes through F1",
                           "yes" if (via and not no_fuse) else "NO - UNFUSED"))
    return 0 if (via and not no_fuse) else 1


# ----------------------------------------------- section 7: umbilical shorts
# Relay coil data, SRD-Series datasheet V3.2 (Sanyou-branded; the BOM part is
# Songle SRD-12VDC-SL-C - provenance OPEN). Coil 400 R +-10 % at 12 V nominal.
# Pick-up (max) 75 % -> guaranteed ON at >= 9.0 V. Drop-out (min) 5 % ->
# guaranteed OFF only at <= 0.6 V. Between the two the datasheet determines
# NOTHING: no minimum pick-up, no maximum hold. Those "??" results close only by
# measuring must-operate and must-release voltages on real units.
COIL_OHM = 400.0
V_ON, V_OFF = 9.0, 0.6
R_CLOSED = 0.05
# ASSUMED: the bench SP3485 driver is enabled and idling (A high, B low) behind
# ~50 R. A disabled driver is high impedance and makes these shorts harmless,
# so this is the worse case.
DRIVER = {"RS485_A": 3.3, "RS485_B": 0.0}
DRIVER_OHM = 50.0
CONT_LIT_V = 1.5      # sense-line voltage at which the station lamp is taken as lit

# Station panel contacts per state: (ref, pin, pin) closed. Mirrors the contact
# sets drawn in gen_station.py.
KEY_ON = [("J_ARMSW1", '1', '2')]
KEY_OFF = [("J_ARMSW1", '1', '3'), ("J_ARMSW1", '4', '5'), ("J_ARMSW1", '6', '7')]
FIRE_PRESSED = [("J_FIRESW1", '1', '2'), ("J_FIRESW1", '3', '4')]
FIRE_RELEASED = [("J_FIRESW1", '5', '6')]
ESTOP_RELEASED = [("J_ESTOP1", '1', '2'), ("J_ESTOP1", '3', '4')]
TEST_PRESSED = [("J_TESTSW1", '1', '2')]

#  name           key    fire   test   estop  bench relays ON        K5 ON
DC_STATES = [
    ("SAFE",       False, False, False, False, {"K4"},                True),
    ("TEST",       False, False, True,  False, {"K4", "K3"},          True),
    ("ARMED",      True,  False, False, False, {"K4", "K1"},          True),
    ("FIRE",       True,  True,  False, False, {"K4", "K1", "K2", "K3"}, True),
    ("SAFE+ESTOP", False, False, False, True,  set(),                 False),
    ("ARMED+ESTOP", True, False, False, True,  set(),                 False),
    ("FIRE+ESTOP", True,  True,  False, True,  set(),                 False),
]
QUIET = ("SAFE", "TEST", "ARMED")


def parse_ohms(v):
    m = re.match(r'^\s*(\d+)([RrKkMm]?)(\d*)\b', v or "")
    if not m or "TBD" in v.upper():
        return None
    mult = {"": 1, "r": 1, "k": 1e3, "m": 1e6}[m.group(2).lower()]
    whole, frac = m.group(1), m.group(3)
    ohms = float(whole + ("." + frac if frac else "")) * mult
    return max(ohms, R_CLOSED)


class Merge:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def norm(net):
    return net.lstrip("/")


class TwoBoards:
    """Bench and station netlists joined through the J_UMB pins."""

    def __init__(self, bench_path, station_path):
        self.c = {"B": load(bench_path), "S": load(station_path)}
        self.parts = {"B": load_parts(bench_path), "S": load_parts(station_path)}
        self.m = Merge()
        for side in "BS":
            for ref, pins in self.c[side].items():
                for _p, net in pins.items():
                    self.m.find(self.key(side, net))
        self.m.union(self.key("B", "GND"), self.key("S", "GND"))
        for pin, _net in umbilical.PINS + [(umbilical.SHIELD_PIN, None)]:
            b = self.c["B"].get("J_UMB1", {}).get(pin)
            s = self.c["S"].get("J_UMB1", {}).get(pin)
            if b and s:
                self.m.union(self.key("B", b), self.key("S", s))
        self.skipped = []

    @staticmethod
    def key(side, net):
        n = norm(net)
        return "GND" if n == "GND" else "%s:%s" % (side, n)

    def node(self, side, ref, pin):
        net = self.c[side].get(ref, {}).get(pin)
        return self.m.find(self.key(side, net)) if net else None

    def conductor(self, net):
        return self.m.find(self.key("B", net))

    def elements(self, st):
        name, key, fire, test, estop, bench_on, k5_on = st
        el, di = [], []
        for side in "BS":
            for ref, info in self.parts[side].items():
                if info["dnp"] or ref not in self.c[side]:
                    continue
                n = lambda p: self.node(side, ref, p)   # noqa: E731
                if ref.startswith("R"):
                    ohm = parse_ohms(info["value"])
                    if ohm is None:
                        if (side, ref) not in self.skipped:
                            self.skipped.append((side, ref))
                        continue
                    if n('1') and n('2'):
                        el.append((n('1'), n('2'), ohm))
                elif ref.startswith("F"):
                    el.append((n('1'), n('2'), R_CLOSED))
                elif ref.startswith("K") and ref[1:2].isdigit():
                    el.append((n('A1'), n('A2'), COIL_OHM))
                    on = (ref in bench_on) if side == "B" else k5_on
                    for a, b in contacts(ref, on, None):
                        if n(a) and n(b):
                            el.append((n(a), n(b), R_CLOSED))
                elif ref.startswith("D") and info["part"] in ("D", "D_Schottky", "LED"):
                    if n('1') and n('2'):
                        di.append((n('2'), n('1')))          # anode -> cathode
        if PLUG_IN and self.node("B", "J_ARM1", '1'):
            el.append((self.node("B", "J_ARM1", '1'), self.node("B", "J_ARM1", '2'), R_CLOSED))
        sw = (KEY_ON if key else KEY_OFF) + (FIRE_PRESSED if fire else FIRE_RELEASED)
        sw += (TEST_PRESSED if test else []) + ([] if estop else ESTOP_RELEASED)
        for ref, a, b in sw:
            na, nb = self.node("S", ref, a), self.node("S", ref, b)
            if na and nb:
                el.append((na, nb, R_CLOSED))
        for net, v in DRIVER.items():
            el.append((self.conductor(net), "FIX:%s" % net, DRIVER_OHM))
        return el, di

    def fixed(self):
        # Every key goes through find(): the shield pin merges bench GND with the
        # station's unconnected pin-12 net, so "GND" is not necessarily the root.
        f = {self.m.find("GND"): 0.0}
        f[self.m.find(self.key("B", self.c["B"]["J_PWR1"]['1']))] = 12.0
        f[self.m.find(self.key("S", self.c["S"]["J_12V1"]['1']))] = 12.0
        for net, v in DRIVER.items():
            f["FIX:%s" % net] = v
        return f


def solve(el, fixed):
    """Nodal DC solve, pure Python. Nodes not connected to any fixed source are
    dropped - they carry no current - which keeps the systems small."""
    adj = collections.defaultdict(set)
    for a, b, _r in el:
        adj[a].add(b); adj[b].add(a)
    live, q = set(fixed), collections.deque(fixed)
    while q:
        x = q.popleft()
        for y in adj[x]:
            if y not in live:
                live.add(y); q.append(y)
    nodes = sorted(n for n in live if n not in fixed)
    idx = {n: i for i, n in enumerate(nodes)}
    N = len(nodes)
    G = [[0.0] * (N + 1) for _ in range(N)]
    for a, b, r in el:
        if a not in live:
            continue
        g = 1.0 / r
        for p, o in ((a, b), (b, a)):
            if p in idx:
                G[idx[p]][idx[p]] += g
                if o in idx:
                    G[idx[p]][idx[o]] -= g
                else:
                    G[idx[p]][N] += g * fixed[o]
    for i in range(N):
        G[i][i] += 1e-9                     # isolated islands settle at 0 V
    for c in range(N):
        p = max(range(c, N), key=lambda r: abs(G[r][c]))
        G[c], G[p] = G[p], G[c]
        piv = G[c][c]
        rowc = G[c]
        for r in range(N):
            if r != c:
                f = G[r][c] / piv
                if f:
                    rr = G[r]
                    for k in range(c, N + 1):
                        rr[k] -= f * rowc[k]
    v = dict(fixed)
    v.update({n: G[idx[n]][N] / G[idx[n]][idx[n]] for n in nodes})
    return v


def solve_with_diodes(el, di, fixed):
    on = set()
    v = solve(el, fixed)
    for _ in range(30):
        new = {i for i, (a, k) in enumerate(di)
               if (v.get(a, 0.0) - v.get(k, 0.0)) > (-1e-6 if i in on else 1e-6)}
        if new == on:
            return v
        on = new
        v = solve(el + [(di[i][0], di[i][1], R_CLOSED) for i in on], fixed)
    return v


def band(volts):
    volts = abs(volts)
    return "ON" if volts >= V_ON else ("off" if volts <= V_OFF else "??")


def run_matrix(tb, short=None):
    rows = {}
    fixed = tb.fixed()
    relays = {r: (tb.node("B", r, 'A1'), tb.node("B", r, 'A2'))
              for r in ("K1", "K2", "K3", "K4")}
    cont = tb.conductor("PYRO_CONT_SENSE")
    for st in DC_STATES:
        el, di = tb.elements(st)
        if short:
            el.append((short[0], short[1], R_CLOSED))
        v = solve_with_diodes(el, di, fixed)
        cv = {r: v.get(a, 0.0) - v.get(b, 0.0) for r, (a, b) in relays.items()}
        rows[st[0]] = (cv, {r: band(x) for r, x in cv.items()}, v.get(cont, 0.0))
    return rows


def section_umbilical(bench_path, station_path):
    print("\n  7. UMBILICAL SINGLE-SHORT MATRIX (DC, both boards)")
    tb = TwoBoards(bench_path, station_path)
    base = run_matrix(tb)
    bad = 0
    # Sections 1-6 ASSUME which relays each operating state energises. This DC
    # baseline DERIVES it from the drawn coil wiring of both boards, so the
    # assumption is checked here, not trusted: the two tables must agree.
    st_map = {"SAFE": "SAFE", "TEST": "TEST held", "ARMED": "ARMED",
              "FIRE": "FIRE held", "SAFE+ESTOP": "E-STOP, both channels",
              "ARMED+ESTOP": "E-STOP, both channels", "FIRE+ESTOP": "E-STOP, both channels"}
    graph = {s[0]: {r for r, on in zip(("K4", "K1", "K2", "K3"), s[1:5]) if on} for s in STATES}
    for st in DC_STATES:
        if graph[st_map[st[0]]] != st[5]:
            bad += 1
            print("  *** state tables disagree for %s: %s vs %s"
                  % (st[0], sorted(graph[st_map[st[0]]]), sorted(st[5])))
    print("  baseline, no fault (coil volts):")
    for st in DC_STATES:
        cv, b, cont = base[st[0]]
        want = st[5]
        ok = all((b[r] == "ON") == (r in want) and b[r] != "??" for r in b)
        bad += 0 if ok else 1
        print("    %-12s %s  sense=%.1fV %s"
              % (st[0], " ".join("%s=%5.2f" % (r, cv[r]) for r in ("K4", "K1", "K2", "K3")),
                 cont, "ok" if ok else "*** MODEL DISAGREES WITH STATE TABLE ***"))
    if tb.skipped:
        print("  resistors with no value, left OPEN in the model: %s"
              % ", ".join("%s:%s" % s for s in tb.skipped))

    nets = []
    for _p, net in umbilical.PINS:
        if net not in nets:
            nets.append(net)
    pin_of = collections.defaultdict(set)
    for p, net in umbilical.PINS:
        pin_of[net].add(p)
    pin_of["GND"].add(umbilical.SHIELD_PIN)
    adj = set()
    for p, q in umbilical.adjacent_pairs():
        for a in nets:
            for b in nets:
                if a != b and p in pin_of[a] and q in pin_of[b]:
                    adj.add(frozenset((a, b)))

    errors, residual = [], []
    print("  %-34s %s" % ("pair (A = adjacent pins)", "result"))
    for a, b in itertools.combinations(nets, 2):
        rows = run_matrix(tb, (tb.conductor(a), tb.conductor(b)))
        is_adj = frozenset((a, b)) in adj
        tags = []
        for st in DC_STATES:
            name = st[0]
            cv, bd, cont = rows[name]
            all4 = [bd[r] for r in ("K4", "K1", "K2", "K3")]
            can = all(x != "off" for x in all4)
            sure = all(x == "ON" for x in all4)
            if name in QUIET:
                if sure or can:
                    tags.append(("E", "%s: %s" % (name, "FIRES" if sure else "MAY FIRE (??)")))
                # K1 pulled in outside ARMED cannot fire on its own (K2 and K3
                # still need the FIRE loop), but it puts the bench one weld from
                # firing. Gated when the pins are adjacent; reported otherwise.
                if name != "ARMED" and bd["K1"] != "off":
                    tags.append(("E" if (bd["K1"] == "ON" and is_adj) else "W",
                                 "%s: K1 %s (%.1f V)" % (name, "ARMS" if bd["K1"] == "ON"
                                                          else "may arm", cv["K1"])))
                # K3 pulled in outside FIRE/TEST opens the shunt (H2 lost) and
                # ties the low side: the bench is then one K2 weld from firing.
                if name in ("SAFE", "ARMED") and bd["K3"] != "off":
                    tags.append(("E" if (bd["K3"] == "ON" and is_adj) else "W",
                                 "%s: SHUNT %s (K3 %.1f V)" % (name, "OPENS" if bd["K3"] == "ON"
                                                               else "may open", cv["K3"])))
                if name in ("SAFE", "TEST") and cont >= CONT_LIT_V and base[name][2] < CONT_LIT_V:
                    tags.append(("E" if is_adj else "W",
                                 "%s: continuity lamp FALSE GOOD" % name))
            elif "ESTOP" in name:
                if can:
                    tags.append(("E" if is_adj else "W",
                                 "%s: burn %s" % (name, "CONTINUES" if sure else "may continue (??)")))
                elif bd["K4"] != "off":
                    tags.append(("i", "%s: channel 1 held (K4 %.1f V), channel 2 stops it"
                                 % (name, cv["K4"])))
            elif name == "FIRE" and not can:
                tags.append(("i", "FIRE: cannot fire (nuisance, safe)"))
        sev = "E" if any(t[0] == "E" for t in tags) else ("W" if any(t[0] == "W" for t in tags) else "")
        label = "%s%s <-> %s" % ("A " if is_adj else "  ", a, b)
        if not tags:
            print("  %-34s no hazard" % label)
        else:
            print("  %-34s %s%s" % (label, {"E": "*** ", "W": "residual: ", "": ""}[sev],
                                    "; ".join(t[1] for t in tags)))
        if sev == "E":
            errors.append(label)
        elif sev == "W":
            residual.append(label)
    print("  gated failures: %d   residual (non-adjacent or datasheet-undetermined): %d"
          % (len(errors), len(residual)))
    print("  '??' = between 0.6 V and 9 V, where the SRD datasheet guarantees neither")
    print("  state. Closes only by measuring must-operate / must-release on real units.")
    return bad + len(errors)


def main(bench_path, station_path=None):
    comp = load(bench_path)
    for req in ("P1", "J_ARM1", "K1", "K2", "K3", "K4"):
        if req not in comp:
            print("  !! %s not in the netlist - cannot trace" % req)
            return 2
    print("Firing loop trace:  %s" % os.path.basename(bench_path))
    print("  plug inserted = %s, match fitted = %s" % (PLUG_IN, MATCH_FITTED))
    print("  looking for a closed path %s -> P1 -> %s\n" % (BATT_P, BATT_N))
    bad = section_states(comp)
    bad += section_structure(comp)
    bad += section_test(comp)
    bad += section_dead_short(comp)
    bad += section_faults(comp)
    bad += section_reverse(comp)
    if station_path:
        bad += section_umbilical(bench_path, station_path)
    else:
        print("\n  7. UMBILICAL SHORTS: SKIPPED - pass the station netlist as the second"
              "\n     argument. A release run must include it.")
        bad += 1
    print("\n  %s" % ("ALL CHECKS AS EXPECTED" if not bad else "%d FAILURE(S)" % bad))
    print("  Connectivity and DC only. Contact ratings, timing, arcing, transients,")
    print("  induced energy and anything thermal are NOT covered. Approves nothing.")
    return 1 if bad else 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, os.pardir, os.pardir, "exports", "2026-11-10-revA2")
    args = sys.argv[1:] or [os.path.join(d, "talavera-bench.net"),
                            os.path.join(d, "talavera-station.net")]
    sys.exit(main(*args[:2]))
