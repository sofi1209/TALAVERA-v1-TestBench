# Project skills

Claude Code loads skills from this directory. Account-level skills enabled on claude.ai are **not**
automatically available here — `ListSkills` will show them, but the `Skill` tool cannot invoke them.
They have to exist on disk.

## Skills this project wants

| Skill | Why it matters here |
|---|---|
| `pcb-electronics-review` | Schematic, netlist, BOM, power-distribution and pre-fabrication review. This is the audit skill. |
| `kicad-board-design` | The gated workflow (requirements → architecture → schematic → ERC → layout → DRC → fab package) that this project already follows. |
| `embedded-firmware-validation` | ESP32 / SPI / SD / state-machine firmware review for `firmware/logger`. |
| `pcb-routing-workflow` | Placement and routing planning. Needed from Gate 4 onward, not before. |

## Installing them

Each skill is a folder containing a `SKILL.md` with YAML frontmatter:

```
.claude/skills/
  pcb-electronics-review/
    SKILL.md
  kicad-board-design/
    SKILL.md
  embedded-firmware-validation/
    SKILL.md
  pcb-routing-workflow/
    SKILL.md
```

Export each one from claude.ai (Settings → Capabilities → Skills) and drop the folder in here. Commit
them so every session and every teammate gets the same behaviour.

To confirm a new session can see them, ask it to run `ListSkills` and then invoke one by name. If
`Skill` returns *"Unknown skill"*, the folder is missing or the frontmatter is malformed.

## Why they are not already here

The session that built this project could see these skills listed but could not invoke them, and had
no way to read their contents — so it **did not fabricate them**. The audit in
`docs/AUDIT-2026-11-06.md` was produced without them, following only the scope their descriptions
state. Treat that audit as thorough but not as having applied the team's actual review checklist.
