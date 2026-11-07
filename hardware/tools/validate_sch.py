import sys, collections, math
import ksch

PAPER = {"A2": (594.0, 420.0), "A3": (420.0, 297.0), "A4": (297.0, 210.0)}

def check(path):
    txt = open(path, encoding="utf-8").read()
    errs, warns = [], []

    # 1. paren balance, and RAW NEWLINES INSIDE STRINGS.
    #    KiCad rejects a literal line break inside a quoted string with
    #    "Unterminated delimited string" - it requires a \n escape. An earlier
    #    version of this checker silently accepted them, so the schematic
    #    validated clean here and still failed to load. Treat it as an error.
    d = 0; instr = False; i = 0; line = 1; rawnl = []
    while i < len(txt):
        c = txt[i]
        if c == "\n": line += 1
        if instr:
            if c == chr(92): i += 2; continue
            if c == '"': instr = False
            elif c == "\n": rawnl.append(line - 1)
        else:
            if c == '"': instr = True
            elif c == '(': d += 1
            elif c == ')':
                d -= 1
                if d < 0: errs.append("unbalanced ) at %d" % i); break
        i += 1
    if d != 0: errs.append("paren depth ends at %d" % d)
    if rawnl:
        errs.append("RAW NEWLINE inside a quoted string at line(s) %s - KiCad will refuse to load "
                    "the file ('Unterminated delimited string'). Escape as \\\\n."
                    % ", ".join(str(n) for n in rawnl[:10]))

    tree = ksch.parse(txt)
    if not tree or ksch.head(tree[0]) != "kicad_sch":
        errs.append("root is not kicad_sch"); return errs, warns, {}
    root = tree[0]

    paper = ksch.val(ksch.kid(root, "paper"))
    W, H = PAPER.get(paper, (594.0, 420.0))

    # 2. lib_symbols index: name -> set of pin numbers
    libdefs = {}
    ls = ksch.kid(root, "lib_symbols")
    for sym in ksch.kids(ls, "symbol"):
        name = ksch.val(sym)
        pins = set()
        def walk(nd):
            for p in ksch.kids(nd, "pin"):
                n = ksch.kid(p, "number")
                if n is not None: pins.add(ksch.val(n))
            for sub in ksch.kids(nd, "symbol"): walk(sub)
        walk(sym)
        libdefs[name] = pins

    # 3. instances
    refs = collections.Counter()
    placed = []
    for sym in ksch.kids(root, "symbol"):
        lid = ksch.val(ksch.kid(sym, "lib_id"))
        at = ksch.kid(sym, "at")
        x, y = float(ksch.val(at, 1)), float(ksch.val(at, 2))
        ref = None
        for p in ksch.kids(sym, "property"):
            if ksch.val(p) == "Reference": ref = ksch.val(p, 2)
        if lid not in libdefs:
            errs.append("lib_id not in lib_symbols: %s (%s)" % (lid, ref))
            continue
        used = {ksch.val(p) for p in ksch.kids(sym, "pin")}
        missing = used - libdefs[lid]
        if missing:
            errs.append("%s (%s) pins not in symbol: %s" % (ref, lid, sorted(missing)))
        if ksch.kid(sym, "instances") is None:
            errs.append("%s has no (instances) block" % ref)
        if ref and not ref.startswith("#PWR"):
            refs[ref] += 1
        if not (0 <= x <= W and 0 <= y <= H):
            errs.append("%s outside %s sheet at (%.1f, %.1f)" % (ref, paper, x, y))
        placed.append((ref, lid, x, y))

    for r, n in refs.items():
        if n > 1: errs.append("duplicate reference %s x%d" % (r, n))

    # 4. wires + labels: every label should coincide with a wire endpoint
    ends = set()
    for w in ksch.kids(root, "wire"):
        pts = ksch.kid(w, "pts")
        xy = ksch.kids(pts, "xy")
        for p in xy:
            ends.add((round(float(ksch.val(p, 1)), 2), round(float(ksch.val(p, 2)), 2)))
        if len(xy) == 2:
            a = (float(ksch.val(xy[0], 1)), float(ksch.val(xy[0], 2)))
            b = (float(ksch.val(xy[1], 1)), float(ksch.val(xy[1], 2)))
            if abs(a[0]-b[0]) < 1e-9 and abs(a[1]-b[1]) < 1e-9:
                warns.append("zero-length wire at %.2f,%.2f" % a)

    # 4b. Connectivity, mirroring what KiCad ERC calls dangling. Every wire end
    #     must land exactly on a pin, a label, or another wire end; every label
    #     must land exactly on a wire end or a pin. "Near enough" is not a
    #     connection - an earlier version allowed 1 mm of slop and passed a
    #     schematic that ERC rejected with 200 dangling errors.
    pinpts = set()
    for sym in ksch.kids(root, "symbol"):
        lid = ksch.val(ksch.kid(sym, "lib_id"))
        at = ksch.kid(sym, "at")
        sx, sy = float(ksch.val(at, 1)), float(ksch.val(at, 2))
        ang = float(ksch.val(at, 3)) if len(at) > 3 else 0.0
        try:
            _d, lpins = ksch.get_symbol(lid)
        except Exception:
            continue
        th = math.radians(ang); ct, st = math.cos(th), math.sin(th)
        for pn in {ksch.val(p) for p in ksch.kids(sym, "pin")}:
            if pn not in lpins: continue
            px, py, _pa = lpins[pn]
            rx = px * ct - py * st
            ry = px * st + py * ct
            pinpts.add((round(sx + rx, 2), round(sy - ry, 2)))

    nets = collections.Counter()
    labelpts = set()
    for lb in ksch.kids(root, "label"):
        nm = ksch.val(lb)
        at = ksch.kid(lb, "at")
        x, y = round(float(ksch.val(at, 1)), 2), round(float(ksch.val(at, 2)), 2)
        nets[nm] += 1
        labelpts.add((x, y))
        if (x, y) not in ends and (x, y) not in pinpts:
            errs.append("DANGLING LABEL '%s' at (%.2f, %.2f) - not exactly on a wire end or pin"
                        % (nm, x, y))

    endcount = collections.Counter()
    for w in ksch.kids(root, "wire"):
        for p in ksch.kids(ksch.kid(w, "pts"), "xy"):
            endcount[(round(float(ksch.val(p, 1)), 2), round(float(ksch.val(p, 2)), 2))] += 1
    for pt, n in endcount.items():
        if pt in pinpts or pt in labelpts or n > 1:
            continue
        errs.append("DANGLING WIRE END at (%.2f, %.2f) - touches no pin, label or wire" % pt)

    # 4c. KiCad treats a reference with no trailing digit as unannotated
    for r in refs:
        if not r[-1:].isdigit():
            errs.append("reference '%s' has no trailing digit - KiCad reports it as unannotated" % r)

    # 4d. Connection grid. KiCad's schematic grid is 50 mil = 1.27 mm; anything
    #     off it raises endpoint_off_grid and may silently fail to connect.
    GRID = 1.27
    def offgrid(p):
        return (abs(p[0] / GRID - round(p[0] / GRID)) > 1e-6 or
                abs(p[1] / GRID - round(p[1] / GRID)) > 1e-6)
    bad = sorted({p for p in (pinpts | ends) if offgrid(p)})
    if bad:
        errs.append("%d pin/wire endpoints OFF the 1.27 mm connection grid, e.g. %s"
                    % (len(bad), ", ".join("(%.2f,%.2f)" % p for p in bad[:4])))

    # 4e. Resolve nets, then sanity-check named power pins. This is the check
    #     that would have caught all four AMS1117 regulators being wired with
    #     GND on the input rail and the output shorted to ground.
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
    netname = {}
    for lb in ksch.kids(root, "label"):
        at = ksch.kid(lb, "at")
        netname[find((round(float(ksch.val(at, 1)), 2), round(float(ksch.val(at, 2)), 2)))] = ksch.val(lb)

    GROUNDY = ("GND", "VSS", "AGND", "DGND", "AVSS", "GNDREF")
    SUPPLY = ("VI", "VIN", "VCC", "VDD", "AVDD", "DVDD", "VBUS", "VO", "VOUT")
    for sym in ksch.kids(root, "symbol"):
        lid = ksch.val(ksch.kid(sym, "lib_id"))
        if lid.startswith("power:"): continue
        at = ksch.kid(sym, "at")
        sx, sy = float(ksch.val(at, 1)), float(ksch.val(at, 2))
        ang = float(ksch.val(at, 3)) if len(at) > 3 else 0.0
        ref = next((ksch.val(p, 2) for p in ksch.kids(sym, "property")
                    if ksch.val(p) == "Reference"), "?")
        try:
            libname, symname = lid.split(":")
            flat = ksch._flatten(ksch.load_lib(libname), symname)
        except Exception:
            continue
        pinfo = {}
        def wk(nd):
            for p in ksch.kids(nd, "pin"):
                a2 = ksch.kid(p, "at"); nu = ksch.kid(p, "number"); nm = ksch.kid(p, "name")
                if a2 is None or nu is None: continue
                pinfo[ksch.val(nu)] = (float(ksch.val(a2, 1)), float(ksch.val(a2, 2)),
                                       (ksch.val(nm) or "").upper())
            for sub in ksch.kids(nd, "symbol"): wk(sub)
        wk(flat)
        th = math.radians(ang); ct, st = math.cos(th), math.sin(th)
        for pn, (px, py, pname) in pinfo.items():
            rx = px * ct - py * st; ry = px * st + py * ct
            pt = (round(sx + rx, 2), round(sy - ry, 2))
            net = netname.get(find(pt))
            if net is None: continue
            isgnd = any(net.upper() == g or net.upper().endswith("_" + g) for g in GROUNDY)
            if pname in GROUNDY and not isgnd:
                errs.append("%s pin %s is named %s but sits on net '%s' - not a ground net"
                            % (ref, pn, pname, net))
            if pname in SUPPLY and isgnd:
                errs.append("%s pin %s is named %s but sits on ground net '%s'"
                            % (ref, pn, pname, net))

    # 5. single-use nets are suspicious (nothing to connect to)
    powernets = {ksch.val(p, 2) for sym in ksch.kids(root, "symbol")
                 if (ksch.val(ksch.kid(sym, "lib_id")) or "").startswith("power:")
                 for p in ksch.kids(sym, "property") if ksch.val(p) == "Value"}
    singles = sorted(n for n, c in nets.items() if c == 1 and n not in powernets)
    if singles:
        warns.append("nets appearing once (no second connection): %s" % ", ".join(singles))

    # 6. rough symbol overlap check on origins
    for i in range(len(placed)):
        for j in range(i+1, len(placed)):
            if placed[i][1].startswith("power:") or placed[j][1].startswith("power:"):
                continue
            dx = abs(placed[i][2]-placed[j][2]); dy = abs(placed[i][3]-placed[j][3])
            if dx < 6 and dy < 6:
                warns.append("%s and %s origins within 6mm" % (placed[i][0], placed[j][0]))

    stats = {"paper": paper, "symbols_in_lib": len(libdefs),
             "instances": len(placed), "components": len(refs),
             "wires": len(ksch.kids(root, "wire")),
             "labels": sum(nets.values()), "nets": len(nets)}
    return errs, warns, stats

for path in sys.argv[1:]:
    print("=" * 70)
    print(path.split("/")[-1])
    e, w, st = check(path)
    for k, v in st.items(): print("   %-16s %s" % (k, v))
    print("   ERRORS: %d" % len(e))
    for x in e[:25]: print("      !", x)
    print("   WARNINGS: %d" % len(w))
    for x in w[:12]: print("      ~", x)
