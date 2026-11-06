# Trade study — replacing the ADS1115

**Status: proposal. No part selected. Decision belongs to Gate 3.**

> ### Every figure in this document is UNVERIFIED
>
> The numbers below are nominal values from recollection, written to frame the comparison. **None has
> been read from a datasheet in this document's preparation.** Before any part is selected, each
> candidate's figures must be confirmed against its datasheet and recorded with the page, per the
> project evidence rule. Do not order parts from this table.

---

## 1. Why this is being reopened

The ADS1115 was carried over from Wirikuta 1.1 (manual p. 19) on the reasoning that an external 16-bit
converter beats the ESP32's internal SAR ADC. That reasoning still holds — the internal ADC is not a
candidate. But "better than the worst option" is not the same as "the right part", and the reported
field problems deserve a real answer.

### Corroborating evidence from IGNIS-v5

While reviewing the IGNIS-v5 flight computer for its storage circuit, this comment turned up in
`DataLogger.h`:

> *"...board's documented I²C solder-joint issues, and the SD bus is on the..."*

IGNIS-v5 independently documented I²C reliability problems and **deliberately kept its data path on
SPI**. That is a second, unrelated board in the same lab reaching the same conclusion.

This reframes the question. The likely problem is not the ADS1115's conversion quality — it is that
**the ADS1115 is only available with an I²C interface**, and I²C is the fragile part:

| I²C weakness | Effect on a test bench |
|---|---|
| Two open-drain lines held up by external pull-ups | A marginal solder joint or a corroded header reads as a stuck bus |
| No framing, no reset, bus-wide lockup | One stuck device hangs the whole bus until power-cycled |
| Shared addresses, no chip select | Any added sensor can conflict |
| Not designed for length or noise | A firing transient nearby can corrupt a transfer |

SPI has an explicit clock, separate data directions and a per-device chip select. It does not lock up
in the same way.

**Therefore the primary selection criterion is: get off I²C.**

---

## 2. Selection criteria

| # | Criterion | Why |
|---|---|---|
| 1 | **SPI interface, not I²C** | The corroborated failure mode, in two separate boards |
| 2 | **≥ 1 kSPS** | A solid-motor ignition rise is on the order of 10–30 ms. The ADS1115's 860 SPS ceiling gives only ~10–25 samples across the rise. More headroom is wanted. |
| 3 | **Integrated bridge PGA** | If the converter can take the load cell's millivolt-level differential output directly, **the AD620 is deleted** — one fewer part, one fewer offset and drift source |
| 4 | 3.3 V operation | Matches the ESP32 domain; removes the ADS1115's 3.3 V input-range squeeze (open item 11) |
| 5 | Availability and a named second source | Gate 3 requirement |

Criterion 3 is the interesting one. It is the difference between swapping a chip and **removing a stage
from the signal chain** — which is what "simpler" was supposed to mean in this project.

---

## 3. Candidates

| Part | Bits | Interface | Max rate | Integrated PGA | Replaces AD620? | Verdict |
|---|---|---|---|---|---|---|
| **ADS1115** (incumbent) | 16 | **I²C** | 860 SPS | ×16 max, not bridge-grade | No | **Fails criterion 1.** The interface is the problem and it cannot be changed. |
| **HX711** | 24 | SPI-like | **10 / 80 SPS** | Yes, load-cell specific | Yes | **Rejected.** 80 SPS cannot resolve an ignition transient. Common in kitchen scales for a reason. |
| **ADS1232 / ADS1234** | 24 | SPI | **80 SPS** | Yes, bridge-oriented | Yes | **Rejected.** Same speed problem. |
| **AD7190 / AD7192** | 24 | **SPI** | ~4.8 kSPS | **Yes, to ×128, bridge-oriented** | **Yes** | **Recommended.** Purpose-built for strain-gauge bridges. |
| **ADS1256** | 24 | **SPI** | ~30 kSPS | Yes, to ×64 | Yes | **Strong second source.** Widely stocked, cheap modules exist. |
| **MCP3561 / MCP3564** | 24 | **SPI** | ~150 kSPS | Yes, to ×64 | Yes | **Modern alternative.** Good availability. Faster than needed. |
| **ADS8681 / ADS8685** | 16 | **SPI** | ~1 MSPS | Yes, ±10 V inputs | No — needs the AD620 | Industrial-robust input protection, but keeps the two-stage chain. |

---

## 4. Recommendation

**Primary: AD7190.** It is a 24-bit sigma-delta converter built for bridge sensors, with an on-chip
instrumentation amplifier. It talks SPI, it is fast enough with margin, and it **replaces both the
ADS1115 and the AD620** with a single device. That removes the I²C bus, removes an amplifier stage, and
removes the 3.3 V input-range constraint in one move.

**Second source: ADS1256.** Technically more than adequate and much easier to buy, which matters for a
student team. If AD7190 lead times are bad, this is the fallback, not a compromise.

**If minimum change is preferred:** keep the AD620 and put an **MCP3561** behind it on SPI. This fixes
the interface problem alone and leaves the analog front end exactly as Wirikuta had it. Lower risk,
smaller reward.

### What this does not fix by itself

Moving to SPI will not cure a noise floor caused by layout or cabling. The noise work is separate and
already in the architecture: differential signalling off the bench, a dedicated shielded analog pair,
and the firing current moved into a physically separate cable (D-010, D-016). **Measure the noise floor
in Stage 4 of the bring-up plan against the Wirikuta baseline** rather than assuming the converter
change was responsible either way.

---

## 5. Open question for Sofia

The recommendation above assumes the ADS1115 problems were **interface and reliability** problems. If
the actual symptom was different, the answer changes:

| Reported symptom | What it points at | Likely fix |
|---|---|---|
| Readings freeze, bus hangs, needs a power cycle | I²C lockup / solder joints | **Any SPI part above** |
| Readings noisy or jumpy but never stop | Layout, grounding, cabling, excitation | Fix the layout; the converter may be innocent |
| Readings drift with temperature | AD620 offset drift, or excitation instability | Integrated-PGA part with ratiometric reference |
| Saturates or clips | Gain chain mis-set for the 3.3 V range | Recompute the gain — open item 11 |
| Too slow / burn transient looks blocky | 860 SPS ceiling | Any ≥1 kSPS part above |

**Which of these matches what you saw?** More than one may apply.

---

## 6. Decision — ADS1220, chosen on sourcing

Sofia chose the logic of the minimum-change option — fix the interface, keep the known-good front end —
but required a part buyable at **UNIT Electronics or LCSC, preferably both**. That constraint selects a
different part from the one originally proposed.

### The part: ADS1220IPWR

| | |
|---|---|
| Resolution / interface | 24-bit delta-sigma, **SPI** |
| Max rate | **2 kSPS** — against the ADS1115's 860 SPS |
| Integrated PGA | ×1 to ×128 |
| Reference | Internal 2.048 V, external reference supported (needed for ratiometric bridge measurement) |
| Supply | 2.3 – 5.5 V, so it runs natively at 3.3 V |
| Package | TSSOP-16 |
| Temperature | −40 to +125 °C |
| Positioning | TI markets it explicitly for **bridge sensors** |

**Sourcing — checked 6 November 2026. Re-verify before ordering.**

| Vendor | Listing | Price |
|---|---|---|
| **UNIT Electronics** | [ADS1220IPWR IC SMD ADC](https://uelectronics.com/producto/ads1220ipwr-ic-smd-adc/) | MXN, confirm on site |
| **LCSC** | [C48263](https://www.lcsc.com/product-detail/Analog-To-Digital-Converters-ADCs_TI_ADS1220IPWR_ADS1220IPWR_C48263.html) — ~15,900 in stock | ~$2.48 @1, ~$1.71 @100 |

Available at both, which was the requirement. It also happens to be roughly a third the price of the
AD620 it sits behind.

Note the specifications above are **still from vendor summaries, not read from the datasheet.** Confirm
each against [TI's ADS1220 datasheet](https://www.ti.com/lit/ds/symlink/ads1220.pdf) and record the page
before Gate 3 closes.

### A sourcing problem with the AD620 that changes the plan

| Part | Vendor | Note |
|---|---|---|
| AD620AN (DIP-8) | [UNIT Electronics](https://uelectronics.com/producto/ad620an-amplificador-de-instrumentacion/) | ~111 MXN. **Through-hole** — fine for hand assembly, wrong for a JLCPCB-assembled board |
| AD620ANZ (DIP) | [LCSC C9680](https://www.lcsc.com/product-detail/C9680.html) | ~$7.00 |
| AD620ARZ (SOIC-8) | [LCSC C578332](https://www.lcsc.com/product-detail/Pre-ordered-Products_Analog-Devices_AD620ARZ_Analog-Devices-ADI-LINEAR-AD620ARZ_C578332.html) | ~$7.98, listed under **"Pre-ordered Products"** |

The surface-mount AD620 — the only version suitable for an assembled board — is on **pre-order at LCSC,
which means JLCPCB very likely cannot place it.** Since the board is going to JLCPCB assembled (D-049),
keeping the AD620 as a populated part is a schedule risk, not just a cost.

### Resolution: populate the ADS1220's PGA, lay out the AD620 as bypassable

1. **ADS1220 is populated and its internal PGA is the primary front end.** This is the configuration TI
   designed for a bridge sensor, and it is fully machine-placeable.
2. **The AD620 footprint is laid out with 0 Ω bypass links** so it can be hand-populated later from the
   UNIT DIP part or a hand-soldered SOIC.

This keeps the spirit of the minimum-change choice — nothing about the proven analog topology is thrown
away — while removing a part that would block automated assembly. It also buys something genuinely
useful: **both front ends can be A/B tested on the same board.** Given that the noise floor is the known
unsolved problem (manual p. 28), being able to measure one chain against the other on identical hardware
is worth the two link pads.

**Cost of this choice:** two 0 Ω links and a little board area, plus the discipline to actually run the
comparison in bring-up Stage 4 rather than leaving the AD620 unpopulated forever.

### Still to verify at Gate 2

- **ADS1220 input common-mode range with the PGA enabled is restricted** at a 3.3 V supply. The PGA can
  be bypassed for rail-to-rail input, at the cost of gain. This must be checked against the load cell's
  actual output and common-mode level once its datasheet is available (open item 4).
- Whether the excitation can be used as the external reference for a ratiometric measurement, which
  would cancel excitation drift.

---

## 7. Decision record

Recorded as **D-046** in [DECISION-LOG.md](DECISION-LOG.md), superseding the ADS1115 half of D-030.
Datasheet pages for every quoted figure must be added before Gate 3 closes.
