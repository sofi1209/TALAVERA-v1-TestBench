"""Report overlapping items and items outside their section box.

validate_sch.py answers "is it connected". ERC answers "is it legal". Neither
answers "can a human read this sheet" - and a schematic that cannot be read is
a schematic that gets reviewed badly. This finds text sitting on top of text,
text sitting on top of symbols, symbols on top of each other, and anything that
has escaped the dashed section rectangle it belongs to.

    python check_layout.py ../talavera-bench/talavera-bench.kicad_sch

Exit code is non-zero if anything collides or escapes, so it can gate a commit.

Boxes are approximations: KiCad's stroke font is not metric-exact and property
text is placed by its own rules. Treat the output as a list of places to look,
not as proof. A small overlap between a label and the wire it annotates is
normal and is filtered out.
"""
import collections
import math
import sys

import ksch

# Stroke-font metrics, measured off a rendered sheet rather than guessed:
# KiCad's default stroke font advances about 0.9 x the text size per character,
# with roughly 1.45 em line pitch. The first version of this file used 0.6,
# which under-measured every text box by a third and quietly missed collisions.
CHAR_W = 0.90
LINE_H = 1.45
PAD = 0.3            # ignore grazes smaller than this
MIN_AREA = 1.0       # ignore slivers


def rects_overlap(a, b, pad=0.0):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix = min(ax2, bx2) - max(ax1, bx1) - pad
    iy = min(ay2, by2) - max(ay1, by1) - pad
    if ix <= 0 or iy <= 0:
        return 0.0
    return ix * iy


def text_box(node):
    """Bounding box of a (text ...) item, justified left top."""
    s = ksch.val(node)
    at = ksch.kid(node, "at")
    x, y = float(ksch.val(at, 1)), float(ksch.val(at, 2))
    eff = ksch.kid(node, "effects")
    size = 1.27
    if eff is not None:
        fnt = ksch.kid(eff, "font")
        if fnt is not None:
            sz = ksch.kid(fnt, "size")
            if sz is not None:
                size = float(ksch.val(sz, 1))
    lines = (s or "").split("\n")
    w = max((len(ln) for ln in lines), default=1) * size * CHAR_W
    h = len(lines) * size * LINE_H
    # justify left top: the anchor is the top-left corner
    return (x, y, x + w, y + h), (s or "").split("\n")[0][:46]


def symbol_box(sym, libcache):
    """Bounding box of a placed symbol, from its library graphics and pins."""
    lid = ksch.val(ksch.kid(sym, "lib_id")) or ""
    at = ksch.kid(sym, "at")
    sx, sy = float(ksch.val(at, 1)), float(ksch.val(at, 2))
    ang = float(ksch.val(at, 3)) if len(at) > 3 else 0.0
    ref = next((ksch.val(p, 2) for p in ksch.kids(sym, "property")
                if ksch.val(p) == "Reference"), "?")
    if lid not in libcache:
        try:
            libname, symname = lid.split(":")
            libcache[lid] = ksch._flatten(ksch.load_lib(libname), symname)
        except Exception:
            libcache[lid] = None
    flat = libcache[lid]
    if flat is None:
        return None, ref
    pts = []

    def walk(nd):
        for kind in ("rectangle", "polyline", "circle", "arc"):
            for g in ksch.kids(nd, kind):
                for tag in ("start", "end", "mid", "center", "xy"):
                    for e in ksch.kids(g, tag):
                        pts.append((float(ksch.val(e, 1)), float(ksch.val(e, 2))))
                for p in ksch.kids(g, "pts"):
                    for e in ksch.kids(p, "xy"):
                        pts.append((float(ksch.val(e, 1)), float(ksch.val(e, 2))))
        for p in ksch.kids(nd, "pin"):
            a2 = ksch.kid(p, "at")
            if a2 is None:
                continue
            pts.append((float(ksch.val(a2, 1)), float(ksch.val(a2, 2))))
        for sub in ksch.kids(nd, "symbol"):
            walk(sub)
    walk(flat)
    if not pts:
        return None, ref
    th = math.radians(ang); ct, st = math.cos(th), math.sin(th)
    gx, gy = [], []
    for px, py in pts:
        rx = px * ct - py * st
        ry = px * st + py * ct
        gx.append(sx + rx); gy.append(sy - ry)
    return (min(gx), min(gy), max(gx), max(gy)), ref


def main(path):
    txt = open(path, encoding="utf-8").read()
    root = ksch.parse(txt)[0]
    libcache = {}

    texts = []
    for t in ksch.kids(root, "text"):
        box, label = text_box(t)
        texts.append((box, label))

    # Net labels and the Reference/Value text on each symbol are the dominant
    # source of visual mess on these sheets, so they are measured too. A label
    # is anchored at the wire end and reads away from it; property text is
    # placed by place() relative to the symbol origin.
    labels = []
    for lb in ksch.kids(root, "label"):
        nm = ksch.val(lb) or ""
        at = ksch.kid(lb, "at")
        x, y = float(ksch.val(at, 1)), float(ksch.val(at, 2))
        rot = float(ksch.val(at, 3)) if len(at) > 3 else 0.0
        w = len(nm) * 1.27 * CHAR_W
        h = 1.27 * LINE_H
        # Reading direction, justify left, in KiCad's Y-down sheet space:
        #   0 deg -> +x     90 deg -> -y     180 deg -> -x     270 deg -> +y
        # Treating 90 and 270 the same made every downward stub's label appear
        # to run back up through its own component, which reported collisions
        # that are not on the sheet.
        if rot == 90.0:
            box = (x - h / 2, y - w, x + h / 2, y)
        elif rot == 270.0:
            box = (x - h / 2, y, x + h / 2, y + w)
        elif rot == 180.0:
            box = (x - w, y - h / 2, x, y + h / 2)
        else:
            box = (x, y - h / 2, x + w, y + h / 2)
        labels.append((box, nm))

    props = []
    for sym in ksch.kids(root, "symbol"):
        for p in ksch.kids(sym, "property"):
            key = ksch.val(p)
            if key not in ("Reference", "Value"):
                continue
            eff = ksch.kid(p, "effects")
            if eff is not None and ksch.kid(eff, "hide") is not None:
                continue
            txt = ksch.val(p, 2) or ""
            if not txt:
                continue
            at = ksch.kid(p, "at")
            x, y = float(ksch.val(at, 1)), float(ksch.val(at, 2))
            w = len(txt) * 1.27 * CHAR_W
            h = 1.27 * LINE_H
            # placed centred horizontally on the symbol origin
            props.append(((x - w / 2, y - h / 2, x + w / 2, y + h / 2), txt))

    symbols = []
    for sym in ksch.kids(root, "symbol"):
        lid = ksch.val(ksch.kid(sym, "lib_id")) or ""
        if lid.startswith("power:"):
            continue          # power symbols are small and sit on wires
        box, ref = symbol_box(sym, libcache)
        if box:
            symbols.append((box, ref))

    boxes = []
    for r in ksch.kids(root, "rectangle"):
        a = ksch.kid(r, "start"); b = ksch.kid(r, "end")
        if a is None or b is None:
            continue
        x1, y1 = float(ksch.val(a, 1)), float(ksch.val(a, 2))
        x2, y2 = float(ksch.val(b, 1)), float(ksch.val(b, 2))
        boxes.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    problems = []

    # text on text
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            a = rects_overlap(texts[i][0], texts[j][0], PAD)
            if a > MIN_AREA:
                problems.append(("TEXT/TEXT", a, texts[i][0],
                                 "'%s' x '%s'" % (texts[i][1], texts[j][1])))

    # text on symbol
    for tb, lab in texts:
        for sb, ref in symbols:
            a = rects_overlap(tb, sb, PAD)
            if a > MIN_AREA:
                problems.append(("TEXT/SYM", a, tb, "'%s' x %s" % (lab, ref)))

    # symbol on symbol
    for i in range(len(symbols)):
        for j in range(i + 1, len(symbols)):
            a = rects_overlap(symbols[i][0], symbols[j][0], PAD)
            if a > MIN_AREA:
                problems.append(("SYM/SYM", a, symbols[i][0],
                                 "%s x %s" % (symbols[i][1], symbols[j][1])))

    # annotation collisions: label/label, label/property, property/property,
    # and either of those landing on a free-text block
    ann = [(b, "label '%s'" % n, n) for b, n in labels] + \
          [(b, "text '%s'" % n, None) for b, n in props]
    for i in range(len(ann)):
        for j in range(i + 1, len(ann)):
            # Several pins of one connector carrying the SAME net put identical
            # labels at the same point - four VBUS pins on a USB-C receptacle,
            # for instance. They draw as a single label and are correct.
            # Staggering them to "fix" the report makes a longer wire run
            # through a shorter one's label anchor, which KiCad ERC reports as
            # label_multiple_wires. Learned by doing exactly that.
            if (ann[i][2] is not None and ann[i][2] == ann[j][2]
                    and abs(ann[i][0][0] - ann[j][0][0]) < 0.6
                    and abs(ann[i][0][1] - ann[j][0][1]) < 0.6):
                continue
            a = rects_overlap(ann[i][0], ann[j][0], PAD)
            if a > MIN_AREA:
                problems.append(("ANNOTATION", a, ann[i][0],
                                 "%s x %s" % (ann[i][1], ann[j][1])))
    for ab, an, _net in ann:
        for tb, lab in texts:
            a = rects_overlap(ab, tb, PAD)
            if a > MIN_AREA:
                problems.append(("ANN/TEXT", a, ab, "%s x '%s'" % (an, lab)))

    # escaped its section box: an item that overlaps a box but is not inside
    # it. A section header legitimately sits just above its box and grazes the
    # top edge, so only report when a real part of the item is outside.
    def area(r):
        return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1])

    def inside(inner, outer):
        return (inner[0] >= outer[0] - 0.5 and inner[1] >= outer[1] - 0.5 and
                inner[2] <= outer[2] + 0.5 and inner[3] <= outer[3] + 0.5)

    for tb, lab in texts + [(b, r) for b, r in symbols]:
        touching = [bx for bx in boxes if rects_overlap(tb, bx) > MIN_AREA]
        if not touching or any(inside(tb, bx) for bx in touching):
            continue
        best = max(rects_overlap(tb, bx) for bx in touching)
        own = area(tb)
        if own > 0 and best / own < 0.40:
            continue      # only grazing an edge, e.g. a section header
        problems.append(("ESCAPES BOX", best, tb, "'%s'" % lab))

    # Diagonal wires. A schematic is read by following lines, and a sloped line
    # reads as "these two things are roughly connected" rather than as a signal
    # path. Every segment must be horizontal or vertical; use an L of two
    # segments where the endpoints do not line up.
    for w in ksch.kids(root, "wire"):
        xy = ksch.kids(ksch.kid(w, "pts"), "xy")
        if len(xy) != 2:
            continue
        x1, y1 = float(ksch.val(xy[0], 1)), float(ksch.val(xy[0], 2))
        x2, y2 = float(ksch.val(xy[1], 1)), float(ksch.val(xy[1], 2))
        if abs(x1 - x2) > 0.01 and abs(y1 - y2) > 0.01:
            problems.append(("DIAGONAL", math.hypot(x2 - x1, y2 - y1),
                             (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)),
                             "wire (%.1f,%.1f)-(%.1f,%.1f)" % (x1, y1, x2, y2)))

    # Outside every section box. The boxes are the sheet's visual structure; a
    # part or a note floating outside all of them has no home and reads as
    # unrelated to anything.
    def is_header_of_a_box(tb):
        """A section title sitting just above its box, horizontally over it.

        Titles above boxes are ordinary schematic convention, so this is a real
        exemption rather than a way to silence the check: the title must sit
        within 12 mm above a box top and overlap it horizontally.
        """
        for bx in boxes:
            gap = bx[1] - tb[3]
            if -1.0 <= gap <= 12.0 and tb[0] < bx[2] and tb[2] > bx[0]:
                return True
        return False

    for tb, lab in [(b, l) for b, l in texts] + [(b, r) for b, r in symbols]:
        if not boxes:
            break
        if any(rects_overlap(tb, bx) > MIN_AREA for bx in boxes):
            continue
        if is_header_of_a_box(tb):
            continue
        problems.append(("OUTSIDE ALL", area(tb), tb, "'%s'" % lab))

    problems.sort(key=lambda p: -p[1])
    name = path.replace("\\", "/").split("/")[-1]
    print("=" * 72)
    print("%s - %d text, %d symbols, %d section boxes"
          % (name, len(texts), len(symbols), len(boxes)))
    if not problems:
        print("   no overlaps, nothing outside its box")
        return 0
    counts = collections.Counter(p[0] for p in problems)
    print("   %s" % ", ".join("%s: %d" % (k, v) for k, v in sorted(counts.items())))
    for kind, area, box, what in problems[:60]:
        print("   %-12s %6.1f mm2  at (%.0f, %.0f)  %s"
              % (kind, area, box[0], box[1], what))
    if len(problems) > 60:
        print("   ... and %d more" % (len(problems) - 60))
    return 1


if __name__ == "__main__":
    rc = 0
    for p in sys.argv[1:]:
        rc |= main(p)
    sys.exit(rc)
