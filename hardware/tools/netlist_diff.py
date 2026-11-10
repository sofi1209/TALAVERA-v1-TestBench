"""Compare two KiCad kicadsexpr netlists - the "netlist comparison against a
baseline" step of the verification chain.

    python netlist_diff.py <baseline.net> <new.net>

Reports components added, removed or changed in value; nets added or removed;
and nets whose member pins changed. Net names are compared without the leading
'/', and KiCad's per-pin "unconnected-(...)" nets are ignored. Every line it
prints should be a change the batch INTENDED - an unexplained line is the thing
to chase. Exit code is 0 when the netlists are connectivity-identical, 1 when
they differ, so it can also assert "connectivity unchanged" after a cosmetic edit.

It compares connectivity, not correctness, and approves nothing.
"""
import re
import sys


def load(path):
    t = open(path, encoding="utf-8").read()
    comps = {m.group(1): m.group(2) for m in
             re.finditer(r'\(comp\s*\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)', t)}
    nets = {}
    for m in re.finditer(r'\(net\s*\(code "\d+"\)\s*\(name "([^"]+)"\)(.*?)'
                         r'(?=\n\t\t\(net\s|\n\t\)\s*\Z)', t, re.S):
        name = m.group(1).lstrip("/")
        if name.startswith("unconnected-"):
            continue
        nets[name] = frozenset("%s.%s" % rp for rp in
                               re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', m.group(2)))
    return comps, nets


def main(base_path, new_path):
    a_c, a_n = load(base_path)
    b_c, b_n = load(new_path)
    changed = False
    print("components: %d -> %d" % (len(a_c), len(b_c)))
    for r in sorted(set(b_c) - set(a_c)):
        print("  + %-12s %s" % (r, b_c[r])); changed = True
    for r in sorted(set(a_c) - set(b_c)):
        print("  - %-12s %s" % (r, a_c[r])); changed = True
    for r in sorted(set(a_c) & set(b_c)):
        if a_c[r] != b_c[r]:
            print("  ~ %-12s %s  ->  %s" % (r, a_c[r], b_c[r])); changed = True
    print("nets: %d -> %d" % (len(a_n), len(b_n)))
    for n in sorted(set(b_n) - set(a_n)):
        print("  + %-18s %s" % (n, " ".join(sorted(b_n[n])))); changed = True
    for n in sorted(set(a_n) - set(b_n)):
        print("  - %-18s %s" % (n, " ".join(sorted(a_n[n])))); changed = True
    for n in sorted(set(a_n) & set(b_n)):
        if a_n[n] != b_n[n]:
            add, rem = sorted(b_n[n] - a_n[n]), sorted(a_n[n] - b_n[n])
            print("  ~ %-18s %s%s" % (n, ("+" + " +".join(add)) if add else "",
                                      ("  -" + " -".join(rem)) if rem else ""))
            changed = True
    print("nets unchanged: %d" % sum(1 for n in set(a_n) & set(b_n) if a_n[n] == b_n[n]))
    return 1 if changed else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
