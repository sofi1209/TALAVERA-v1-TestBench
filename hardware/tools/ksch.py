"""Minimal KiCad 10 schematic generator: s-expression parser + symbol extractor + builder."""
import re, uuid, os

SYMDIR = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"

# ---------------------------------------------------------------- sexp parser
TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')

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
            cur.append(('str', s))
        else:
            cur.append(('sym', at))
    return cur

def ser(node, indent=0):
    pad = "\t" * indent
    if isinstance(node, tuple):
        kind, v = node
        return '"%s"' % v if kind == 'str' else v
    if not node:
        return "()"
    head = node[0]
    # inline if short and contains no sublists
    simple = all(isinstance(c, tuple) for c in node)
    if simple:
        return "(" + " ".join(ser(c) for c in node) + ")"
    out = ["(" + (ser(head) if isinstance(head, tuple) else ser(head, indent + 1))]
    for c in node[1:]:
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
    path = os.path.join(SYMDIR, libname + ".kicad_sym")
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


def get_symbol(libid):
    """Return (defn_for_lib_symbols, pins) where pins maps number -> (x, y, angle)."""
    libname, symname = libid.split(":")
    syms = load_lib(libname)
    if symname not in syms:
        raise KeyError("symbol not found: " + libid)
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
def U():
    return str(uuid.uuid4())

class Sch:
    def __init__(self, project, title, rev="A", company="Ignitia Rocket Lab",
                 paper="A2", comments=()):
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
              hide_value=False, mirror=None, angle=0, hide_ref=False):
        """Place a symbol. Returns dict pin-number -> (gx, gy, outward_angle)."""
        pins = self._lib(libid)
        props = [
            ("Reference", ref, 0, -1.27, hide_ref),
            ("Value", value, 0, 1.27, hide_value),
            ("Footprint", footprint, 0, 0, True),
            ("Datasheet", "~", 0, 0, True),
            ("Description", "", 0, 0, True),
        ]
        pstr = []
        for name, v, dx, dy, hide in props:
            h = "\n\t\t\t\t(hide yes)" if hide else ""
            pstr.append(
                '\t\t(property "%s" "%s"\n\t\t\t(at %.4f %.4f 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)%s\n\t\t\t)\n\t\t)'
                % (name, v, x + dx, y + dy, h))
        pinstr = "".join('\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)\n' % (pn, U()) for pn in pins)
        mir = '\n\t\t(mirror %s)' % mirror if mirror else ""
        self.items.append(
            '\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %.4f %.4f %d)%s\n\t\t(unit 1)\n'
            '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp %s)\n'
            '\t\t(uuid "%s")\n%s\n%s'
            '\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)'
            % (libid, x, y, angle, mir, "yes" if dnp else "no", U(),
               "\n".join(pstr), pinstr, self.project, self.uuid, ref))
        out = {}
        for pn, (px, py, pa) in pins.items():
            gx, gy = x + px, y - py           # library is Y-up, schematic Y-down
            out[pn] = (round(gx, 4), round(gy, 4), (pa + 180) % 360)
        return out

    def wire(self, p1, p2):
        self.items.append(
            '\t(wire\n\t\t(pts\n\t\t\t(xy %.4f %.4f) (xy %.4f %.4f)\n\t\t)\n'
            '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (p1[0], p1[1], p2[0], p2[1], U()))

    def label(self, name, x, y, angle=0, justify="left"):
        self.items.append(
            '\t(label "%s"\n\t\t(at %.4f %.4f %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            '\t\t\t(justify %s bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)' % (name, x, y, angle, justify, U()))

    def stub(self, pin, name, length=5.08):
        """Draw a wire outward from a pin and attach a net label."""
        x, y, a = pin
        import math
        rad = math.radians(a)
        dx, dy = math.cos(rad) * length, -math.sin(rad) * length
        ex, ey = round(x + dx, 4), round(y + dy, 4)
        self.wire((x, y), (ex, ey))
        if a == 0:        # pointing right
            self.label(name, ex + 0.5, ey, 0, "left")
        elif a == 180:    # left
            self.label(name, ex - 0.5, ey, 0, "right")
        elif a == 90:     # up on screen
            self.label(name, ex, ey - 0.5, 90, "left")
        else:             # down
            self.label(name, ex, ey + 0.5, 90, "right")
        return (ex, ey)

    def power(self, kind, pin, length=5.08):
        """Attach a power symbol (power:GND / power:+12V ...) to a pin."""
        libid = "power:" + kind
        x, y, a = pin
        import math
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
                   hide_value=True, hide_ref=True, angle=ang)
        return (ex, ey)

    def text(self, s, x, y, size=2.0, bold=True):
        self.items.append(
            '\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %.4f %.4f 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %.2f %.2f)\n\t\t\t\t(thickness %.2f)\n\t\t\t\t(bold %s)\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (s, x, y, size, size, size * 0.15, "yes" if bold else "no", U()))

    def box(self, x, y, w, h):
        self.items.append(
            '\t(rectangle\n\t\t(start %.4f %.4f)\n\t\t(end %.4f %.4f)\n'
            '\t\t(stroke\n\t\t\t(width 0.2)\n\t\t\t(type dash)\n\t\t)\n'
            '\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "%s")\n\t)' % (x, y, x + w, y + h, U()))

    def render(self):
        libs = "\n".join(ser(d, 2) for d in self.libs.values())
        com = "".join('\n\t\t(comment %d "%s")' % (i + 1, c) for i, c in enumerate(self.comments))
        return (
            '(kicad_sch\n\t(version 20250610)\n\t(generator "eeschema")\n\t(generator_version "9.99")\n'
            '\t(uuid "%s")\n\t(paper "%s")\n'
            '\t(title_block\n\t\t(title "%s")\n\t\t(date "2026-11-06")\n\t\t(rev "%s")\n\t\t(company "%s")%s\n\t)\n'
            '\t(lib_symbols\n%s\n\t)\n%s\n'
            '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
            '\t(embedded_fonts no)\n)\n'
            % (self.uuid, self.paper, self.title, self.rev, self.company, com,
               libs, "\n".join(self.items)))

    def write(self, path):
        open(path, "w", encoding="utf-8", newline="\n").write(self.render())
