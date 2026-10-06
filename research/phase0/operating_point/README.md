# operating_point

## What is measured

Over-sedation operating points on quality-gated effect-site concentration.
Designed gold: bolus case samples with t ≥ 25 s are positive; clean-case
samples are negative. Score = Ce (µg/ml). Awareness is not the target.

## Why it decides something

Phase 0 already pivoted to over-sedation because awareness labels are
essentially absent. This table is the Phase 3 scorecard against that pivot:
does a Ce threshold separate the designed post-bolus window from a clean
infusion without treating BIS as an awareness label?

## How to run

```bash
uv run python research/phase0/operating_point/run.py
```

Seed: 0. Cases are the committed synthetic excerpts.
