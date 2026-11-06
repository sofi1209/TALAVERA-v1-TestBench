## What this changes

<!-- One or two sentences. Which gate does this belong to? -->

**Gate:** <!-- 0-7 -->

---

## Safety checklist

Tick every box or explain why it does not apply. A PR touching the safety chain with unticked boxes
should not be merged.

- [ ] No microcontroller has been placed on the arm, fire or e-stop path.
- [ ] Every output still has a named safe state that holds with no firmware running.
- [ ] Every safe state is still the **de-energized** state.
- [ ] The igniter safe state is still **shorted**, via a normally-closed contact.
- [ ] The logger still has no outputs and no connection to any safety net.
- [ ] Firing nets are named `PYRO_*` so they inherit the `PYRO` net class.
- [ ] Safety signals are named `ARM_*` / `FIRE_*` / `ESTOP_*`.
- [ ] No pyrotechnic, actuator, motor, high-current, battery or mains circuit is marked approved in
      this PR. Those require the review owner's written sign-off.

## Evidence

- [ ] Every new value is labelled **verified** (datasheet or manual, with page) or **assumed**.
- [ ] No rating has been invented or carried over from a different gain chain or supply.

## Documentation

- [ ] [docs/DECISION-LOG.md](../docs/DECISION-LOG.md) updated: decision, reason, date, approver.
- [ ] [docs/SAFETY.md](../docs/SAFETY.md) updated if any safe state, hazard or mitigation changed.
- [ ] [docs/OPERATIONS-MANUAL.md](../docs/OPERATIONS-MANUAL.md) updated if any procedure changed.

## Checks (Gates 5 and 6 only)

- [ ] ERC clean, report attached, each remaining item listed and justified.
- [ ] DRC clean, report attached, each remaining item listed and justified.
- [ ] BOM matches the placed parts exactly.
- [ ] Centroid matches the placed parts exactly.

---

## Review owner sign-off

Required for anything touching the firing chain, the power input, or the fabrication package.

**Reviewer:**
**Date:**
