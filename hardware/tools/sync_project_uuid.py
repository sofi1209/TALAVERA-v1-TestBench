"""Point each .kicad_pro's sheet entry at its .kicad_sch root UUID.

The generators mint a fresh root UUID on every run, so a regenerated schematic
leaves the project file referencing a sheet that no longer exists. KiCad then
loses per-sheet settings and the symbol instance paths stop matching.
docs/HANDOFF.md told the reader to "resync the project UUIDs" after
regenerating, and no tool did it - the previous session's workaround was to
revert the schematics whenever the diff turned out to be UUID-only.

    python sync_project_uuid.py            # both boards
    python sync_project_uuid.py --check    # exit 1 if out of sync, change nothing

Run it after gen_*.py, before committing a regenerated schematic.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.abspath(os.path.join(HERE, os.pardir))
BOARDS = ("talavera-bench", "talavera-station")


def root_uuid(sch_path):
    """The (uuid "...") immediately inside (kicad_sch - the sheet's own id."""
    with open(sch_path, encoding="utf-8") as fh:
        head = fh.read(4096)
    m = re.search(r'\(uuid\s+"([0-9a-fA-F-]{36})"\)', head)
    return m.group(1) if m else None


def main(argv):
    check_only = "--check" in argv
    bad = 0
    for board in BOARDS:
        d = os.path.join(HW, board)
        sch = os.path.join(d, board + ".kicad_sch")
        pro = os.path.join(d, board + ".kicad_pro")
        if not (os.path.isfile(sch) and os.path.isfile(pro)):
            print("  %-18s missing project or schematic - skipped" % board)
            continue
        want = root_uuid(sch)
        if not want:
            print("  %-18s no root uuid found in the schematic" % board)
            bad += 1
            continue
        with open(pro, encoding="utf-8") as fh:
            data = json.load(fh)
        sheets = data.get("sheets") or []
        have = sheets[0][0] if sheets and sheets[0] else None
        if have == want:
            print("  %-18s in sync   %s" % (board, want))
            continue
        if check_only:
            print("  %-18s OUT OF SYNC  project=%s  schematic=%s"
                  % (board, have, want))
            bad += 1
            continue
        name = sheets[0][1] if sheets and len(sheets[0]) > 1 else "Root"
        data["sheets"] = [[want, name]] + [s for s in sheets[1:]]
        # Keep KiCad's own formatting: 2-space indent, trailing newline.
        with open(pro, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        print("  %-18s synced    %s -> %s" % (board, have, want))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
