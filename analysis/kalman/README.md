# Post-test thrust processing

Offset correction, filtering and total-impulse integration for a TALAVERA thrust log.

**Status: not yet ported.** The Wirikuta implementation exists in Annex C of the Wirikuta operations
manual and should be brought in here once the log format is fixed at Gate 4.

---

## What the pipeline does

1. Load the CSV produced by the bench logger.
2. Correct the zero offset by subtracting the mean of the pre-ignition samples.
3. Apply a Kalman filter to estimate force.
4. Smooth for presentation.
5. Integrate under the curve across the burn interval to obtain **total impulse**.

---

## Two things change versus Wirikuta

**The input file needs no hand editing.** Wirikuta wrote diagnostic results into the top of the CSV, so
cells had to be deleted manually before the script would parse it (Wirikuta manual p. 27, Imagen 17).
The TALAVERA logger has no diagnostics routine, so the file contains a comment header and thrust rows
only.

**Raw counts are preserved alongside the scaled value.** The logger writes `millis,raw_counts,thrust_N`.
If a log is taken before calibration is finalised, the raw column lets it be rescaled afterwards instead
of being discarded.

```
# TALAVERA v1 thrust log
# cal_n_per_count=1.00000000 cal_verified=false
millis,raw_counts,thrust_N
```

**Check `cal_verified` before trusting a thrust figure.** When it reads `false`, the `thrust_N` column
is raw counts with a placeholder scale factor and means nothing in newtons.

---

## Known limitation carried over

Wirikuta's experience was that when motor impulse is small relative to the load cell noise, the burn
start and end remain hard to identify even after filtering — a 1-grain motor was not characterisable
(manual p. 28).

TALAVERA attacks this at the source rather than in post-processing: differential signalling off the
bench, a dedicated shielded analog pair, and the firing current moved into a physically separate cable.
Whether that is enough to resolve a 1-grain motor is an open question, and it is worth measuring the
noise floor in Stage 4 of the bring-up plan against the Wirikuta baseline before assuming it is.
