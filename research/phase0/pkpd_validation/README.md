# pkpd_validation

## What is measured

On the synthetic bolus case, correlation of effect-site concentration (Ce)
with a recorded depth-index proxy, versus correlation of raw infusion rate
with the same proxy.

## Why it decides something

The product uses effect-site concentration, not raw infusion rate. If Ce
does not track the depth proxy better than rate after a bolus, the PK/PD
layer is not doing useful work.

## How to run

```bash
uv run python research/phase0/pkpd_validation/run.py
```

Model: 2-compartment + effect-site with published Schnider constants
(Schnider 1998/1999; V3/CL3 omitted). The depth index is a Hill function of
Ce plus noise — a proxy, not an awareness label.
