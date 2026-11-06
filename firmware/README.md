# Firmware

## This firmware has no safety authority

TALAVERA's arming, firing and emergency-stop paths are **hardware only** — switches, relay contacts and
resistors. Nothing in this folder participates in them. Nothing in this folder can participate in them,
because the logger has no outputs.

If every line of code here were deleted, or hung, or ran wrong, the bench would remain exactly as safe.
The only consequence would be a missing thrust record.

That is the entire point of the TALAVERA redesign. Read [../docs/SAFETY.md](../docs/SAFETY.md) before
changing anything here.

---

## Target

**ESP32-DevKitC V4**, carrying an **ESP32-WROOM-32D** module. Decision D-028.

| | |
|---|---|
| Logic level | 3.3 V |
| ADC | **Selection reopened.** ADS1115 under review; the ESP32 internal SAR ADC remains excluded. See [../docs/ADC-TRADE-STUDY.md](../docs/ADC-TRADE-STUDY.md). |
| Storage | **On-board microSD socket** over VSPI, with a card-detect line. 3.3 V native, so no level shifter. |
| Radios | **Stopped in firmware and not to be enabled.** See below. |
| Mounting | **TBD** — socketed DevKitC vs. soldered WROOM-32D. Open item. |

### Why not the ESP32's internal ADC

The ESP32's SAR ADCs are nonlinear and noisy. The Wirikuta load-cell chain is *already* noise-limited to
the point that a 1-grain motor cannot be characterised (manual p. 28), and replacing a 16-bit external
converter with a worse internal one would move the design backwards on the single measurement the bench
exists to make. The **ADS1115 is retained** (D-030).

The ADS1115 also caps the sample rate at 860 SPS. That ceiling, not the ESP32, is what sets the
acquisition interval — running the processor faster than the converter buys duplicated samples.

### Why the radios are stopped

The ESP32-WROOM-32D carries Wi-Fi and Bluetooth. TALAVERA exists partly to remove RF from the safety
path, and a 2.4 GHz transmitter at up to +20 dBm would sit centimetres from the AD620 front end and from
a 20 m pyrotechnic cable — the two most EMI-sensitive things on the bench.

The logger still cannot fire anything: it has no outputs and no connection to any safety net, so the
safety argument is unchanged. The concern is **measurement integrity and pyro-line pickup**, not direct
command injection.

`killRadios()` is the first call in `setup()` and must stay there. Enabling Wi-Fi or Bluetooth is a
hardware and safety question, not a firmware convenience (D-029).

---

## Contents

| Folder | Purpose |
|---|---|
| `logger/` | Thrust data logger for the bench board. Reads the amplified load-cell signal, writes CSV to SD. |

---

## The five constraints

Enforced in hardware. Do not work around them in software.

1. **No electrical connection to any safety net.** The logger sees the buffered output of the
   instrumentation amplifier and nothing else.
2. **No outputs.** It reads, and it writes to its own SD card. It drives nothing.
3. **Its own fused, separately regulated rail.** It cannot brown out a relay coil.
4. **A layout keep-out** separates it from the firing chain.
5. **Radios stopped.** Wi-Fi and Bluetooth off at boot, never enabled.

If a future change seems to require an output pin that leaves the logger's own subsystem, that change is
wrong. Raise it as a hardware question instead.

---

## Pin map

Chosen to avoid the ESP32's traps rather than for convenience.

| Signal | GPIO | Note |
|---|---|---|
| SD CS | 4 | — |
| SD SCK / MISO / MOSI | 18 / 19 / 23 | VSPI defaults |
| I²C SDA / SCL | 21 / 22 | ADS1115 |
| Logger LED | 13 | Logger-local only. **Not** the bench beacon. |
| RECORD input | 34 | **Input-only pin**, external pull-up required |

Three rules behind that table:

- **GPIO6–11 are wired to the SPI flash** and are never usable.
- **GPIO0, 2, 5, 12 and 15 are strapping pins** and are avoided entirely, so a cable left connected
  cannot prevent the module from booting.
- **RECORD sits on GPIO34 because 34–39 are input-only.** That pin is physically incapable of becoming
  an output through a coding mistake. GPIO34 also has no internal pull-up, so the pull-up is external;
  a broken RECORD line reads as "not recording", which loses data and changes nothing about safety.

Wirikuta's firmware defined `SERVO_PIN 5` and `BUTTON_PIN 5` on the same microcontroller, so the servo
gating the igniter line shared a pin with an unrelated input. A short, single-purpose, commented pin map
is how that class of mistake is avoided — not by being more careful.

---

## No state machine

Wirikuta 1.1 ran a nine-state machine with six remote commands, RF handling and a diagnostics routine.
All of it is gone. The logger has exactly one behaviour:

> **It records while RECORD is closed.**

The file opens when RECORD closes and is closed cleanly when RECORD opens. No states, no commands, no
timeouts, no abort logic, no radio.

This deletes the entire class of defect that motivated the redesign — including the two concrete bugs
found in the Wirikuta firmware (see [../docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md) §6) — and it has a
second benefit: the CSV contains thrust data only. The manual cell deletion previously required before
the Kalman script would parse the file (Wirikuta manual p. 27) is no longer necessary.

---

## Operational consequence

**Open RECORD before pressing E-STOP.** That closes the file cleanly, which is step 4 of the post-test
procedure in the operations manual. Yanking power mid-write risks corrupting data from a test that cannot
be repeated.

This is why RECORD exists as a separate input rather than simply switching the logger's power.

---

## Dependencies

| Library | Purpose |
|---|---|
| `Adafruit_ADS1X15` | ADS1115 driver |
| `SD`, `SPI`, `Wire` | ESP32 Arduino core |
| `WiFi`, `esp_bt` | Only to switch the radios **off** |

Build with the ESP32 Arduino core, board target **ESP32 Dev Module**. Not verified against hardware —
no board exists yet.
