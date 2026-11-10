"""Minimal KiCad 10 schematic generator: s-expression parser + symbol extractor + builder."""
import re, uuid, os, glob


class SymbolLibError(RuntimeError):
    """Raised when a symbol library cannot be found or does not hold the symbol.

    This used to be swallowed. validate_sch.py wrapped every call to get_symbol()
    in `except Exception: continue`, so a SYMDIR pointing anywhere else made the
    pin-coincidence, power-pin and floating-pin checks vanish while the validator
    still reported a byte-identical "0 errors". Those three checks are the guards
    added after the GND_RTN split, the AMS1117 pin-1 error and the SP3485 left
    with no ground. Never make this failure quiet again.
    """


_SYMDIR_PATTERNS = (
    "C:/Program Files/KiCad/*/share/kicad/symbols",
    "C:/Program Files (x86)/KiCad/*/share/kicad/symbols",
    "/usr/share/kicad/symbols",
    "/usr/local/share/kicad/symbols",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
)

SYMDIR_TRIED = []


def find_symdir():
    """Locate KiCad's stock symbol directory without hardcoding one machine.

    Order: explicit override, then the usual install locations, highest version
    first. Returns None if nothing is found - callers must treat that as an
    error, not as "no symbols to check".
    """
    # An override that is set but wrong is a configuration mistake, so it is
    # fatal rather than quietly falling back to whatever else is installed -
    # silently using a different library set is how a "clean" run stops meaning
    # anything.
    for var in ("TALAVERA_SYMDIR", "KICAD_SYMBOL_DIR"):
        p = os.environ.get(var)
        if p:
            SYMDIR_TRIED.append("$%s=%s" % (var, p))
            if os.path.isdir(p):
                return p
            raise SymbolLibError(
                "$%s is set to '%s', which is not a directory. Unset it or point it "
                "at the directory holding Device.kicad_sym." % (var, p))
    found = []
    for pat in _SYMDIR_PATTERNS:
        SYMDIR_TRIED.append(pat)
        found += [p for p in glob.glob(pat) if os.path.isdir(p)]
    if found:
        # "10.0" sorts above "9.0" as a string, which is the wrong way round for
        # single-digit majors, so compare on parsed version tuples.
        def ver(p):
            m = re.search(r"KiCad[\\/]([0-9]+)\.([0-9]+)", p)
            return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        found.sort(key=ver, reverse=True)
        return found[0]
    return None


SYMDIR = find_symdir()

# ---------------------------------------------------------------- sexp parser
TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')

_ESCMAP = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}

def unesc(s):
    """Decode a KiCad quoted-string body into its real characters."""
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(_ESCMAP.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)

def esc(s):
    """Encode a real string for a KiCad quoted string. Raw newlines are illegal."""
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r"))

def parse(text):
    pos, stack, cur = 0, [], []
    n = len(text)
    while pos < n:
        m = TOK.match(text, pos)
        if not m:
            break
        pos = m.end()
        op, cp, s, at = m.groups()
        if op:
            new = []
            cur.append(new)
            stack.append(cur)
            cur = new
        elif cp:
            if not stack:
                break
            cur = stack.pop()
        elif s is not None:
            cur.append(('str', unesc(s)))
        else:
            cur.append(('sym', at))
    return cur

def ser(node, indent=0):
    pad = "\t" * indent
    if isinstance(node, tuple):
        kind, v = node
        return '"%s"' % esc(v) if kind == 'str' else v
    if not node:
        return "()"
    head = node[0]
    # inline if short and contains no sublists
    simple = all(isinstance(c, tuple) for c in node)
    if simple:
        return "(" + " ".join(ser(c) for c in node) + ")"
    # canonical KiCad style: head plus any leading atoms stay on one line,
    # e.g.  (symbol "Device:R"  /  (property "Reference" "R1"
    out = ["(" + ser(head)]
    i = 1
    while i < len(node) and isinstance(node[i], tuple):
        out.append(" " + ser(node[i]))
        i += 1
    for c in node[i:]:
        out.append("\n" + pad + "\t" + ser(c, indent + 1))
    out.append("\n" + pad + ")")
    return "".join(out)

def head(node):
    return node[0][1] if node and isinstance(node[0], tuple) else None

def kids(node, name):
    return [c for c in node if isinstance(c, list) and head(c) == name]

def kid(node, name):
    k = kids(node, name)
    return k[0] if k else None

def val(node, i=1):
    return node[i][1] if len(node) > i and isinstance(node[i], tuple) else None

# ------------------------------------------------------------ symbol library
_libcache = {}

def load_lib(libname):
    if libname in _libcache:
        return _libcache[libname]
    if not SYMDIR:
        raise SymbolLibError(
            "KiCad symbol directory not found, so no symbol can be resolved. Set "
            "TALAVERA_SYMDIR to the directory holding Device.kicad_sym. Tried: %s"
            % "; ".join(SYMDIR_TRIED))
    path = os.path.join(SYMDIR, libname + ".kicad_sym")
    if not os.path.isfile(path):
        raise SymbolLibError("symbol library '%s' not found at %s (SYMDIR=%s)"
                             % (libname, path, SYMDIR))
    tree = parse(open(path, encoding="utf-8").read())[0]
    syms = {}
    for s in kids(tree, "symbol"):
        syms[val(s)] = s
    _libcache[libname] = syms
    return syms

def _flatten(syms, symname):
    """Resolve (extends "Base") by merging the base symbol's body into the derived one."""
    sym = syms[symname]
    ext = kid(sym, "extends")
    if ext is None:
        return sym
    base_name = val(ext)
    base = _flatten(syms, base_name)
    # keep the derived symbol's own properties; take everything else from the base
    out = [sym[0], sym[1]]
    out += [c for c in sym if isinstance(c, list) and head(c) == "property"]
    for c in base:
        if isinstance(c, tuple):
            continue
        h = head(c)
        if h in ("property", "extends"):
            continue
        if h == "symbol":
            # unit sub-symbols are named "<Base>_<unit>_<style>" - rename to the derived symbol
            c = [x for x in c]
            old = val(c)
            if old and old.startswith(base_name):
                c[1] = ('str', symname + old[len(base_name):])
        out.append(c)
    return out


def body_extent(libid):
    """(half_width, half_height) of a symbol's drawn body, in symbol space.

    place() uses this to put the Reference above the body and the Value below
    it. Both used to be pinned at +/-1.27 mm from the origin, which for almost
    every part in this design sits ON the body, so the designator printed
    through the symbol and collided with any net label nearby.
    """
    try:
        _d, _p = get_symbol(libid)
        syms = load_lib(libid.split(":")[0])
        flat = _flatten(syms, libid.split(":")[1])
    except Exception:
        return 1.27, 1.27
    xs, ys = [], []

    def walk(nd):
        for kind in ("rectangle", "polyline", "circle", "arc"):
            for g in kids(nd, kind):
                for tag in ("start", "end", "mid", "center"):
                    for e in kids(g, tag):
                        xs.append(float(val(e, 1))); ys.append(float(val(e, 2)))
                for p in kids(g, "pts"):
                    for e in kids(p, "xy"):
                        xs.append(float(val(e, 1))); ys.append(float(val(e, 2)))
        for p in kids(nd, "pin"):
            a = kid(p, "at")
            if a is not None:
                xs.append(float(val(a, 1))); ys.append(float(val(a, 2)))
        for sub in kids(nd, "symbol"):
            walk(sub)
    walk(flat)
    if not xs:
        return 1.27, 1.27
    return max(abs(min(xs)), abs(max(xs))), max(abs(min(ys)), abs(max(ys)))


def get_symbol(libid):
    """Return (defn_for_lib_symbols, pins) where pins maps number -> (x, y, angle)."""
    libname, symname = libid.split(":")
    syms = load_lib(libname)
    if symname not in syms:
        raise SymbolLibError("symbol '%s' not found in library '%s' (SYMDIR=%s)"
                             % (symname, libname, SYMDIR))
    flat = _flatten(syms, symname)
    syms = dict(syms); syms[symname] = flat   # so the pin walk below sees the flattened body
    defn = [x for x in flat]
    defn[1] = ('str', libid)  # rename to Lib:Name for embedding
    # collect pins from this symbol and its child units
    pins = {}

    def walk(sym):
        for p in kids(sym, "pin"):
            at = kid(p, "at")
            num = kid(p, "number")
            if at is None or num is None:
                continue
            x = float(val(at, 1)); y = float(val(at, 2))
            a = float(val(at, 3)) if len(at) > 3 else 0.0
            pins[val(num)] = (x, y, a)
        for sub in kids(sym, "symbol"):
            walk(sub)
    walk(syms[symname])
    return defn, pins

# ----------------------------------------------------------------- schematic
GRID = 1.27   # KiCad schematic connection grid (50 mil)

def snap(v):
    """Round to the connection grid. Anything off it triggers endpoint_off_grid."""
    return round(round(v / GRID) * GRID, 4)

def U():
    return str(uuid.uuid4())

class Sch:
    def __init__(self, project, title, rev="A", company="Ignitia Rocket Lab",
                 paper="A2", comments=(), scale=1.0, date="2026-11-06"):
        # `scale` multiplies AUTHORED placement coordinates only - place(),
        # text() and box(). Symbol bodies and text heights are fixed by KiCad,
        # so scaling the layout onto a larger sheet buys spacing without
        # shrinking anything. Pin-derived coordinates (wire, label, stub,
        # power) are already absolute and must NOT be scaled again.
        self.scale = scale
        self.date = date
        self.project = project
        self.uuid = U()
        self.title = title
        self.rev = rev
        self.company = company
        self.paper = paper
        self.comments = comments
        self.libs = {}      # libid -> defn
        self.items = []     # serialized chunks
        self.refs = {}      # prefix -> counter

    # ---- helpers
    def _lib(self, libid):
        if libid not in self.libs:
            defn, pins = get_symbol(libid)
            self.libs[libid] = defn
            self._pins = getattr(self, "_pins", {})
            self._pins[libid] = pins
        return self._pins[libid]

    def place(self, libid, ref, value, x, y, footprint="", dnp=False,
              hide_value=False, mirror=None, angle=0, hide_ref=False, raw=False):
        """Place a symbol. Returns dict pin-number -> (gx, gy, outward_angle).

        `raw` skips the layout scale, for callers that already hold an absolute
        pin-derived coordinate - power() does. Scaling one of those a second
        time drops the symbol somewhere else entirely and leaves the wire it
        was meant to terminate dangling.
        """
        if not raw:
            x, y = x * self.scale, y * self.scale
        x, y = snap(x), snap(y)
        pins = self._lib(libid)
        # KiCad treats a reference with no trailing digit as unannotated, which
        # ERC reports as an error and which breaks BOM and centroid matching.
        if not hide_ref and not ref[-1:].isdigit():
            self._refn = getattr(self, "_refn", {})
            self._refn[ref] = self._refn.get(ref, 0) + 1
            ref = "%s%d" % (ref, self._refn[ref])
        # Clear the body with the designator and the value.
        #
        # Rotating a symbol by 90 deg maps its local Y extent onto the sheet's X
        # axis, and KiCad renders the property text rotated with the symbol. So
        # a vertical part needs its text offset SIDEWAYS, not up and down -
        # offsetting in Y regardless is what printed "TBD  O-17" straight
        # through the net label next to every rotated fuse and diode.
        # Where the text goes is decided by where the PINS point, not by the
        # body's aspect: a part with horizontal pins already has net labels off
        # its left and right, so its designator belongs above and its value
        # below. Only a part whose pins all run vertically has free sides.
        #
        # Pin angles are local, so add the symbol rotation to get the direction
        # on the sheet.
        bw, bh = body_extent(libid)
        gangles = {int(round(pa + angle)) % 360 for (_px, _py, pa) in pins.values()}
        horiz_pins = bool(gangles & {0, 180})
        gx = bw if angle in (0, 180) else bh      # half-extent along sheet X
        gy = bh if angle in (0, 180) else bw      # half-extent along sheet Y
        # KiCad's stroke font advances about 0.9 x the text size per character.
        CW = 1.27 * 0.95
        if horiz_pins:                             # text above and below
            off = snap(max(gy, 1.27) + 2.6)
            dref, dval = (0, -off), (0, off)
        else:                                      # text to the sides
            dref = (-snap(max(gx, 1.27) + 1.6 + len(ref or "") * CW / 2.0), 0)
            dval = (snap(max(gx, 1.27) + 1.6 + len(value or "") * CW / 2.0), 0)
        props = [
            ("Reference", ref, dref[0], dref[1], hide_ref),
            ("Value", value, dval[0], dval[1], hide_value),
            ("Footprint", footprint, 0, 0, True),
            ("Datasheet", "~", 0, 0, True),
            ("Description", "", 0, 0, True),
        ]
        pstr = []
        # KiCad treats a property's angle as RELATIVE to its symbol, so a
        # literal 0 on a part placed at 90 deg prints the text sideways - which
        # is how "TBD  O-17" ended up running vertically across the horizontal
        # net labels on every rotated fuse, diode and resistor. Counter-rotate
        # so designators and values always read level.
        pang = (-angle) % 360
        for name, v, dx, dy, hide in props:
            h = "\n\t\t\t\t(hide yes)" if hide else ""
            pstr.append(
                '\t\t(property "%s" "%s"\n\t\t\t(at %.4f %.4f %d)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)%s\n\t\t\t)\n\t\t)'
                % (name, esc(v), x + dx, y + dy, pang, h))
        pinstr = "".join('\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)\n' % (esc(pn), U()) for pn in pins)
        mir = '\n\t\t(mirror %s)' % mirror if mirror else ""
        self.items.append(
            '\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %.4f %.4f %d)%s\n\t\t(unit 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp %s)\n'
            '\t\t(uuid "%s")\n%s\n%s'
            '\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)'
            % (esc(libid), x, y, angle, mir, "yes" if dnp else "no", U(),
               "\n".join(pstr), pinstr, esc(self.project), self.uuid, esc(ref)))
        # Rotate in symbol space (Y-up, counter-clockwise), then flip Y for the
        # schematic frame. Forgetting this step silently drew every wire on a
        # rotated symbol to the wrong coordinate.
        import math
        th = math.radians(angle)
        ct, st = math.cos(th), math.sin(th)
        out = {}
        for pn, (px, py, pa) in pins.items():
            rx = px * ct - py * st
            ry = px * st + py * ct
            gx, gy = x + rx, y - ry
            out[pn] = (round(gx, 4), round(gy, 4), (pa + 180 + angle) % 360)
        return out

    def wire(self, p1, p2):
        self.items.append(
            '\t(wire\n\t\t(pts\n\t\t\t(xy %.4f %.4f) (xy %.4f %.4f)\n\t\t)\n'
            '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (p1[0], p1[1], p2[0], p2[1], U()))

    def lwire(self, p1, p2, first="v"):
        """Route p1 to p2 with horizontal and vertical segments only.

        A sloped line reads as "these are roughly connected" rather than as a
        signal path, and KiCad will happily draw one. Every LED chain on these
        sheets was a single diagonal because the resistor and the LED did not
        line up. `first` picks which leg leaves p1.
        """
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]
        if abs(x1 - x2) < 0.01 or abs(y1 - y2) < 0.01:
            self.wire((x1, y1), (x2, y2))
            return
        corner = (x1, y2) if first == "v" else (x2, y1)
        self.wire((x1, y1), corner)
        self.wire(corner, (x2, y2))

    def label(self, name, x, y, angle=0, justify="left"):
        self.items.append(
            '\t(label "%s"\n\t\t(at %.4f %.4f %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            '\t\t\t(justify %s bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)' % (esc(name), x, y, angle, justify, U()))

    def stub(self, pin, name, length=5.08):
        """Draw a wire outward from a pin and attach a net label."""
        if name in ("GND", "GNDREF"):
            # Ground is drawn as a power symbol everywhere. A local label named
            # GND beside a power:GND symbol raises same_local_global_label and,
            # worse, is the pattern that once split GND_RTN into two nets.
            return self.power(name, pin, length)
        x, y, a = pin
        import math
        length = max(GRID, snap(length))   # off-grid stub lengths move the end off grid
        rad = math.radians(a)
        dx, dy = math.cos(rad) * length, -math.sin(rad) * length
        ex, ey = round(x + dx, 4), round(y + dy, 4)
        self.wire((x, y), (ex, ey))
        # The label anchor must sit EXACTLY on the wire end. Offsetting it even
        # 0.5 mm leaves the label dangling and the net unconnected.
        # KiCad never draws text upside down: it renders a 180 deg label as 0 deg
        # and a 270 deg label as 90 deg, swapping the justification to match.
        # Keeping "left" for those two therefore ran the label BACK INTO the
        # symbol it belongs to - that is why +12V_LOGGER printed across the
        # AMS1117 body. Justify away from the pin instead.
        if a == 0:
            self.label(name, ex, ey, 0, "left")
        elif a == 180:
            self.label(name, ex, ey, 180, "right")
        elif a == 90:
            self.label(name, ex, ey, 90, "left")
        else:
            self.label(name, ex, ey, 270, "right")
        return (ex, ey)

    def nc(self, *pins):
        """Mark pins as deliberately unconnected, so ERC stops re-raising them."""
        for p in pins:
            self.items.append(
                '\t(no_connect\n\t\t(at %.4f %.4f)\n\t\t(uuid "%s")\n\t)' % (p[0], p[1], U()))

    def pwr_flag(self, net, x, y):
        """Declare a net as driven. Needed where power enters via a connector,
        and on ground, since power-input pins alone do not count as a source."""
        self._flgn = getattr(self, "_flgn", 0) + 1
        p = self.place("power:PWR_FLAG", "#FLG%02d" % self._flgn, net, x, y,
                       hide_value=True, hide_ref=True)
        if net in ("GND", "GNDREF"):
            # A local label next to a power symbol of the same name is ambiguous
            # (KiCad: same_local_global_label), so ground flags use the power
            # symbol itself. The net is unchanged.
            self.power(net, p['1'], 2.54)
        else:
            self.stub(p['1'], net, 2.54)
        return p

    def power(self, kind, pin, length=5.08):
        """Attach a power symbol (power:GND / power:+12V ...) to a pin."""
        libid = "power:" + kind
        x, y, a = pin
        import math
        length = max(GRID, snap(length))
        rad = math.radians(a)
        dx, dy = math.cos(rad) * length, -math.sin(rad) * length
        ex, ey = round(x + dx, 4), round(y + dy, 4)
        self.wire((x, y), (ex, ey))
        # GND draws downward, rails draw upward; rotate so the symbol points away from the pin
        ang = 0
        if kind == "GND":
            ang = 0 if a == 270 else (180 if a == 90 else (90 if a == 180 else 270))
        else:
            ang = 0 if a == 90 else (180 if a == 270 else (270 if a == 180 else 90))
        self._pwrn = getattr(self, "_pwrn", 0) + 1
        self.place(libid, "#PWR%02d" % self._pwrn, kind, ex, ey,
                   hide_value=True, hide_ref=True, angle=ang, raw=True)
        return (ex, ey)

    def text(self, s, x, y, size=2.0, bold=True):
        x, y = x * self.scale, y * self.scale
        self.items.append(
            '\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %.4f %.4f 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %.2f %.2f)\n\t\t\t\t(thickness %.2f)\n\t\t\t\t(bold %s)\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (esc(s), x, y, size, size, size * 0.15, "yes" if bold else "no", U()))

    def box(self, x, y, w, h):
        x, y, w, h = x * self.scale, y * self.scale, w * self.scale, h * self.scale
        self.items.append(
            '\t(rectangle\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n'
            '\t\t(stroke\n\t\t\t(width 0.2)\n\t\t\t(type dash)\n\t\t)\n'
            '\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "%s")\n\t)' % (x, y, x + w, y + h, U()))

    def render(self):
        libs = "\n".join(ser(d, 2) for d in self.libs.values())
        com = "".join('\n\t\t(comment %d "%s")' % (i + 1, esc(c)) for i, c in enumerate(self.comments))
        return (
            '(kicad_sch\n\t(version 20250610)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n'
            '\t(uuid "%s")\n\t(paper "%s")\n'
            '\t(title_block\n\t\t(title "%s")\n\t\t(date "%s")\n\t\t(rev "%s")\n\t\t(company "%s")%s\n\t)\n'
            '\t(lib_symbols\n%s\n\t)\n%s\n'
            '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
            '\t(embedded_fonts no)\n)\n'
            % (self.uuid, self.paper, esc(self.title), esc(self.date), esc(self.rev), esc(self.company), com,
               libs, "\n".join(self.items)))

    def write(self, path):
        open(path, "w", encoding="utf-8", newline="\n").write(self.render())
