import sys, collections, math
import ksch

PAPER = {"A2": (594.0, 420.0), "A3": (420.0, 297.0), "A4": (297.0, 210.0)}

def check(path):
    txt = open(path, encoding="utf-8").read()
    errs, warns = [], []

    # 1. paren balance outside strings
    d = 0; instr = False; i = 0
    while i < len(txt):
        c = txt[i]
        if instr:
            if c == chr(92): i += 2; continue
            if c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == '(': d += 1
            elif c == ')':
                d -= 1
                if d < 0: errs.append("unbalanced ) at %d" % i); break
        i += 1
    if d != 0: errs.append("paren depth ends at %d" % d)

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

    nets = collections.Counter()
    orphan = 0
    for lb in ksch.kids(root, "label"):
        nm = ksch.val(lb)
        at = ksch.kid(lb, "at")
        x, y = round(float(ksch.val(at, 1)), 2), round(float(ksch.val(at, 2)), 2)
        nets[nm] += 1
        # label is offset 0.5mm from the wire end; look for an end within 1mm
        if not any(abs(x-ex) <= 1.01 and abs(y-ey) <= 1.01 for ex, ey in ends):
            orphan += 1
    if orphan:
        warns.append("%d labels not within 1mm of a wire endpoint" % orphan)

    # 5. single-use nets are suspicious (nothing to connect to)
    singles = sorted(n for n, c in nets.items() if c == 1)
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
