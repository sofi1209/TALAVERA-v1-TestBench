"""Extract the real netlist from a .kicad_sch: net -> [ref.pin(name)]."""
import sys, math, collections
import ksch

def netlist(path):
    root = ksch.parse(open(path, encoding="utf-8").read())[0]
    parent = {}
    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb

    for w in ksch.kids(root, "wire"):
        xy = ksch.kids(ksch.kid(w, "pts"), "xy")
        if len(xy) == 2:
            union((round(float(ksch.val(xy[0], 1)), 2), round(float(ksch.val(xy[0], 2)), 2)),
                  (round(float(ksch.val(xy[1], 1)), 2), round(float(ksch.val(xy[1], 2)), 2)))

    name_at = {}
    for lb in ksch.kids(root, "label"):
        at = ksch.kid(lb, "at")
        name_at[(round(float(ksch.val(at, 1)), 2), round(float(ksch.val(at, 2)), 2))] = ksch.val(lb)

    pins = []      # (ref, pinnum, pinname, point, is_power_sym, value)
    for sym in ksch.kids(root, "symbol"):
        lid = ksch.val(ksch.kid(sym, "lib_id"))
        at = ksch.kid(sym, "at")
        sx, sy = float(ksch.val(at, 1)), float(ksch.val(at, 2))
        ang = float(ksch.val(at, 3)) if len(at) > 3 else 0.0
        props = {ksch.val(p): ksch.val(p, 2) for p in ksch.kids(sym, "property")}
        ref, value = props.get("Reference", "?"), props.get("Value", "")
        dnp = any(ksch.head(c) == "dnp" and ksch.val(c) == "yes"
                  for c in sym if isinstance(c, list))
        try:
            libname, symname = lid.split(":")
            flat = ksch._flatten(ksch.load_lib(libname), symname)
        except Exception:
            continue
        info = {}
        def wk(nd):
            for p in ksch.kids(nd, "pin"):
                a2 = ksch.kid(p, "at"); nu = ksch.kid(p, "number"); nm = ksch.kid(p, "name")
                if a2 is None or nu is None: continue
                info[ksch.val(nu)] = (float(ksch.val(a2, 1)), float(ksch.val(a2, 2)),
                                      ksch.val(nm) or "")
            for sub in ksch.kids(nd, "symbol"): wk(sub)
        wk(flat)
        th = math.radians(ang); ct, st = math.cos(th), math.sin(th)
        for pn, (px, py, pnm) in info.items():
            rx = px * ct - py * st; ry = px * st + py * ct
            pt = (round(sx + rx, 2), round(sy - ry, 2))
            pins.append((ref, pn, pnm, pt, lid.startswith("power:"), value, dnp))

    # power symbols name their net
    for ref, pn, pnm, pt, ispwr, value, dnp in pins:
        if ispwr:
            name_at[pt] = value

    for pt, nm in list(name_at.items()):
        find(pt)

    nets = collections.defaultdict(list)
    roots_named = {}
    for pt, nm in name_at.items():
        roots_named[find(pt)] = nm
    anon = 0
    for ref, pn, pnm, pt, ispwr, value, dnp in pins:
        if ispwr: continue
        r = find(pt)
        nm = roots_named.get(r)
        if nm is None:
            nm = "UNNAMED@%.1f,%.1f" % pt
        tag = "%s.%s%s%s" % (ref, pn, ("(" + pnm + ")") if pnm else "", " [DNP]" if dnp else "")
        nets[nm].append(tag)
    return nets

for path in sys.argv[1:]:
    print("=" * 74)
    print(path.split("/")[-1])
    nets = netlist(path)
    for nm in sorted(nets):
        conns = sorted(set(nets[nm]))
        flag = "  <-- SINGLE NODE" if len(conns) == 1 else ""
        print("  %-18s %s%s" % (nm, ", ".join(conns), flag))
