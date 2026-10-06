# label_availability

## What is measured

How many of the five sample cases, and of a committed 200-row synthetic
case-index stand-in, have any usable awareness label or sedation-depth
(BIS-like) label.

## Why it decides something

Intraoperative awareness is rare. If almost no rows have an awareness label,
a model of awareness is not identifiable and the project must pivot to
over-sedation / depth-index risk. This harness is that pivot gate.

## How to run

```bash
uv run python research/phase0/label_availability/run.py
```

The 200-row index is synthetic. A live VitalDB label audit is unmeasured.
