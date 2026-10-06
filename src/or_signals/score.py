"""Over-sedation operating points on quality-gated Ce. Research, not a monitor.

Awareness labels are essentially absent (Phase 0 pivot). The designed gold
here is: bolus case, t >= 25 s (Ce elevated after the bolus). Clean case
samples are negatives. Score = effect-site concentration.
"""

from __future__ import annotations

import numpy as np

from or_signals.io import CaseRecord
from or_signals.schemas import OperatingPoint
from or_signals.sqi import assess_case


def _usable_numeric_mask(record: CaseRecord) -> np.ndarray:
    report = assess_case(record)
    n = int(record.ce_ug_per_ml.size)
    mask = np.ones(n, dtype=np.bool_)
    hz = record.sidecar.numeric_hz
    for gap in report.gaps_reported:
        start = max(int(gap.start_sec * hz), 0)
        end = min(int(np.ceil(gap.end_sec * hz)), n)
        mask[start:end] = False
    return mask


def labeled_windows(
    clean: CaseRecord,
    bolus: CaseRecord,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (scores, gold) on usable numeric samples."""

    scores: list[float] = []
    gold: list[int] = []
    for record, positive_after in ((clean, None), (bolus, 25.0)):
        mask = _usable_numeric_mask(record)
        ce = record.ce_ug_per_ml
        time = record.time_num
        for i in range(int(ce.size)):
            if not mask[i] or not np.isfinite(ce[i]):
                continue
            scores.append(float(ce[i]))
            if positive_after is None:
                gold.append(0)
            else:
                gold.append(int(float(time[i]) >= positive_after))
    return np.asarray(scores, dtype=np.float64), np.asarray(gold, dtype=np.int32)


def operating_points(
    scores: np.ndarray,
    gold: np.ndarray,
    thresholds: list[float],
) -> list[OperatingPoint]:
    rows: list[OperatingPoint] = []
    for threshold in thresholds:
        pred = scores >= threshold
        tp = int(np.count_nonzero(pred & (gold == 1)))
        fp = int(np.count_nonzero(pred & (gold == 0)))
        tn = int(np.count_nonzero(~pred & (gold == 0)))
        fn = int(np.count_nonzero(~pred & (gold == 1)))
        pos = tp + fn
        neg = tn + fp
        tpr = tp / pos if pos else 0.0
        fpr = fp / neg if neg else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        rows.append(
            OperatingPoint(
                threshold_ce=threshold,
                n_positive=pos,
                n_negative=neg,
                tp=tp,
                fp=fp,
                tn=tn,
                fn=fn,
                tpr=tpr,
                fpr=fpr,
                precision=precision,
            )
        )
    return rows
