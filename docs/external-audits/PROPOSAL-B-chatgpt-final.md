# TALAVERA v1 · Final Rev A design proposal

9 November 2026 · Baseline reviewed at GitHub commit `43e980364137857c72099dcaf6f4be3cf3cbf186`

**Decision requested** — Adopt the architecture below for the next schematic revision. The current sheets remain on hold. This is a design proposal for the project review owner, with separate gates for schematic approval, fabrication and live testing.

## 1. Recommended Rev A architecture

| Area | Decision | Reason and constraint |
|---|---|---|
| Hardware safety | Keep ARM, FIRE, E-STOP, reset and continuity interlocks entirely in hardware. Preserve the removable bench plug and normally closed shunt. Keep the shunt and output-return functions independently reviewable. | The MCU, SD card and USB interface have no direct command path. Their power and wiring faults still belong in the installed-system fault review. |
| Station supply | Use one bench battery with a dedicated, source-protected station feed and explicit return through a keyed harness. Keep firing energy local to the bench. Keep a separate station supply as a fallback decision if the approved harness fails the voltage-drop or fault tests. | One battery simplifies field setup and charging. A documented branch and return let a technician distinguish a dead station from a dead bench. Final conductor count follows the required safety functions, cable construction and site separation. |
| E-STOP and restart | A stop or qualifying loss of safety-loop power removes firing authority and restores the shunt. Releasing the E-STOP actuator leaves the system inhibited. Require a deliberate hardware reset with ARM and FIRE released, then a fresh arm action. | A second contact block can help drop ARM, but it alone leaves restart behavior unresolved. Review independence, detection of cable faults and behavior with a welded contact. |
| Pre-arm continuity | Preserve the repository's pre-arm requirement. Use a distinct hardware TEST state that positively inhibits firing power throughout testing, including entry and exit. A successful check returns the system to SAFE. A new operator action is required to arm. | A shunt across the terminals prevents a measurement from distinguishing the match from the shunt. If TEST temporarily releases the shunt, it may do so only after the firing path is inhibited. Define the limits and review this transition with the actual initiator specification. |
| Logger power and service | Use a replaceable bench buck stage for digital power. Keep the logger on its own protected branch upstream of the safety cutoff. Use the actual DevKitC header symbol, a removable service link, and a mutually exclusive USB programming power mode. Provide a defined clean ADC rail with local bypassing. | A failed regulator or DevKitC should be replaceable without disturbing the safety harness. The logger is intended to keep recording through E-STOP while its branch supply remains healthy. Verify supply independence and backfeed behavior. |
| Measurement | Fit one production analog path, load cell → ADS1220 → SD. Remove the DNP AD620 option from the standard build. Use ratiometric excitation and reference only after qualifying the actual load cell. | One population removes four-link assembly ambiguity and a floating AD620 reference. The data record depends on measured capture performance and calibration. |
| Telemetry | Use a receive-only isolated RS-485 link with a logic-compatible buffer or digital isolator, defined idle/reset states and no station transmit path. Make it independently serviceable. Explicitly defer the unimplemented analog DAQ pair for Rev A and update the requirements. | Losing the live view may interrupt monitoring. It must leave the SD capture and safety state intact. Deferring the analog path removes a phantom backup and avoids an external ground path through the DAQ. |
| Indication and repair | Fit a replaceable active panel sounder rated for the approved rail. Distinguish command, actual hardware state and fault indications. Add keyed locking connectors, replaceable fuse holders, legible net and pin labels, and probe points with nearby returns. | A dark command lamp does not prove a safe output. A field technician should be able to isolate power, harness, interlock, logger and telemetry faults with a meter and an inert fixture. |

## 2. Hardware behavior to approve before drawing the interlocks

| State or event | Required result |
|---|---|
| Startup, brownout recovery or harness reconnect | Firing path inhibited. Shunt closed. Outputs do not re-arm from controls left asserted. |
| SAFE | Firing path inhibited and shunt closed. An open, disconnected or invalid diagnostic input cannot report continuity good. |
| TEST | Hardware firing inhibit remains effective. The diagnostic distinguishes a valid connected load from an open load and defined short faults. Leaving or losing TEST restores the shunt and SAFE. |
| ARMED | Requires a deliberate new arm action with FIRE released. Indication distinguishes an arm command from confirmed hardware state. |
| E-STOP from any state | Drops firing authority and returns the shunt to its safe state within the approved response time. Logger and telemetry may continue only in their separate domains. |
| E-STOP released with ARM or FIRE held | Remains inhibited. The hardware requires release of the relevant controls, deliberate reset and a fresh arm action. |
| Relay or harness fault | No unintended output from any fault claimed tolerable. Test the agreed cases, including a welded contact, cut loop, short to return, ARM/FIRE cross-short and partially connected harness. Record which faults are detected and which independent inhibit remains effective. |

**Proposal decision on the K3 option.** Keep the other audit's K3 transfer-contact return as an alternative for review. It reduces part count but makes one contact mechanism responsible for the shunt and return. The baseline keeps those functions separate so their failures can be evaluated independently. The final relay circuit still needs exact contact mapping, timing and fault evidence. An armed-only continuity check would require an explicit change to the operations requirement and is outside this baseline.

## 3. Merged findings and dispositions

| Confirmed finding or open item | Disposition |
|---|---|
| Reversed `D_RP1` | Correct polarity in the generator. Select and qualify exact input protection against the supply and fault envelope. A Schottky's single-pulse surge rating alone does not cover the real event. |
| Station feed absent despite the `PWR_FLAG` | Draw and validate a continuous supply and return from source to station. Add the flag only where it represents a real source. |
| `PYRO_MATCH_N` has no independent DC return | Resolve the return as part of the interlock review. The current revision cannot deliver the intended firing current. A cable or contact fault can still assert an output command, so the open return is a defect and provides no safety credit. |
| Present continuity circuit is an unpowered parallel branch | Replace it with the reviewed TEST function. Require explicit behavior for a sense-wire short, open cable, open match and shorted load. The proposal to test across K2 creates a potential return through `D_FIRE1`, so retain an open-load test with all indicators fitted. |
| Continuity station load and optocoupler mismatch | At nominal 12 V and an assumed 2 V lamp drop, the current lamp and pull-up ask for about 12.6 mA of collector sink current. Decouple the indicator load from the diagnostic interface. Reconcile PC817 in the sheet, TLP521GB-S in the BOM and 6N137 in the handoff. A specific match sensing current is still unknown. |
| E-STOP can be bypassed or re-enable the output on release | Close stop, reset, re-arm and cable-fault behavior as one hardware design. Preserve the guarded FIRE action and physical plug. Demonstrate that one adjacent conductor fault cannot substitute for the operator's independent action. |
| Regulator stability and thermal margin are unresolved | Replace the bench high-drop linear stage. Specify the station regulators' exact input and output capacitors, ESR and effective capacitance. Verify under the real supply envelope, including cold start, SD writes, voltage sag and independent power sequencing. The previous temperature figures are estimates. |
| Station 6N137 inverts UART and direct receiver drive is unqualified | Use a compatible interface and test normal idle, boot, an absent cable and either power domain switched off. The suggested direct-drive resistor change does not establish current margin. |
| ADC CS floats at boot, ADC runs at placeholder 20 SPS, firmware labels uncalibrated data as thrust | Add hardware deselect for ADC and SD where needed. Log raw counts and configuration until calibration. Measure the sustained project target of at least 1 kSPS with sequence numbers and observable drops. Qualify card detection, mount failure, a stalled write, restart and interrupted power. |
| Stale parts list, harness and instructions | Update together with the next sheets. Resolve microSD detect pad numbering against the actual part, remove the deleted controls and obsolete cable-A entries, and draw the actual connector, device and relay pin maps. |
| Missing exact initiator, load-cell, supply, relay and harness data | Treat these as release inputs. They are separate from confirmed wiring faults. Avoid copying example currents, fuse values or contact ratings into the final design. |
| Site separation and deployed cable length | Resolve with the project safety owner for the intended site, configuration and motor class. The repository's 15–17 m installed estimate is already below the minimum cited in its own documents. Qualify voltage drop and signal integrity at the final installed length. |

## 4. Implementation order and required evidence

| Order | Work | Pass evidence |
|---|---|---|
| 1 · Freeze interfaces | Obtain the exact initiator and load-cell data, real battery and charging envelope, longest installed harness, connector choice and intended site constraints. Approve the state table and update the requirements. | Approved interface sheet, exact part identifiers for safety-critical items and a fault matrix with expected outcomes. |
| 2 · Revise schematic generators | Make output and symbol resolution portable. Implement the reviewed hardware interlocks, supply boundaries, and measurement and telemetry circuits. Generate both sheets, harness drawing, BOM and pin maps from the reviewed revision. | Matching schematic and exports. Native KiCad ERC shows zero errors and each warning has a disposition. Review source-to-load and return paths with actual relay states, documented supply conditions and exact footprints. |
| 3 · Qualify service and bring-up | Under project authorization, use current-limited supply and inert fixtures. Check rail load steps and power permutations, fuse/branch isolation, E-STOP response and reset, harness faults, shunt feedback, open-load false indications, USB isolation and logger capture. | Recorded expected versus measured behavior. SD file remains readable in the approved fault scenarios. A technician can isolate the bad branch and replace a fuse, regulator module, harness or DevKitC without rewiring the safety circuit. |
| 4 · Release gates | Review the board layout and actual footprint samples. Freeze fabrication files only after the agreed design checks pass. Handle any live-test stage through its own project authorization. | Reviewed layout/DRC, signed fabrication package and separately authorized live-test plan where applicable. |

## 5. Evidence boundaries

The two audits used the same revision and matching netlists. The supplied native KiCad reports show one bench error and two bench warnings, and zero station errors. The earlier local recheck matched both schematic pin groups to those exports and used an ideal relay-contact model. The local KiCad version could not independently rerun native KiCad 10 ERC. The other audit's bundled reachability script prints a ground path when allowed to loop through the driven output terminal and simultaneously connect mutually exclusive relay contacts. The missing independent return is verified directly from the three pins on `PYRO_MATCH_N`. Neither audit measured relay timing, thermal performance, circuit currents or installed behavior.

## References

- [Reviewed GitHub revision](https://github.com/sofi1209/TALAVERA-v1-TestBench/tree/43e980364137857c72099dcaf6f4be3cf3cbf186) · [Requirements](https://github.com/sofi1209/TALAVERA-v1-TestBench/blob/43e980364137857c72099dcaf6f4be3cf3cbf186/docs/REQUIREMENTS.md) · [Bring-up plan](https://github.com/sofi1209/TALAVERA-v1-TestBench/blob/43e980364137857c72099dcaf6f4be3cf3cbf186/test/BRINGUP-PLAN.md)
- [TI ADS1220](https://www.ti.com/lit/ds/symlink/ads1220.pdf) · [Espressif DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html) · [MaxLinear SP3485](https://www.maxlinear.com/ds/sp3485.pdf)
- [Pilz explanation of manual E-STOP reset and prevention of restart](https://www.pilz.com/en-NZ/support/faq/standards/articles/180045), used as design guidance for reset behavior.
