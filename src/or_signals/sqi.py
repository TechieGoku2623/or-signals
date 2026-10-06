"""Artifact / SQI. Flush and dropout are first-class; gaps are never interpolated."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from or_signals import SAFETY_DISCLAIMER
from or_signals.io import CaseRecord
from or_signals.schemas import ArtifactReason, Interval, QualityReport, SignalQuality

FLUSH_JUMP_MMHG = 80.0
FLUSH_LEVEL_MMHG = 200.0
DAMP_PULSE_MMHG = 8.0
FLAT_EPS = 0.05
FLAT_SEC = 2.0
HYPOTENSION_MAP = 65.0


def _runs(mask: NDArray[np.bool_], hz: float, reason: ArtifactReason) -> list[Interval]:
    intervals: list[Interval] = []
    n = int(mask.size)
    i = 0
    while i < n:
        if not bool(mask[i]):
            i += 1
            continue
        j = i + 1
        while j < n and bool(mask[j]):
            j += 1
        intervals.append(Interval(start_sec=i / hz, end_sec=j / hz, reason=reason))
        i = j
    return intervals


def detect_nan(signal: NDArray[np.float64], hz: float) -> list[Interval]:
    return _runs(np.isnan(signal), hz, "nan")


def detect_flatline(
    signal: NDArray[np.float64], hz: float, min_sec: float = FLAT_SEC
) -> list[Interval]:
    clean = np.asarray(signal, dtype=np.float64)
    if clean.size == 0:
        return []
    finite = np.isfinite(clean)
    delta = np.zeros(clean.size, dtype=np.float64)
    delta[1:] = np.abs(np.diff(np.where(finite, clean, 0.0)))
    flat = finite & (delta < FLAT_EPS)
    flat[0] = False
    intervals = []
    for interval in _runs(flat, hz, "flatline"):
        if interval.end_sec - interval.start_sec >= min_sec:
            intervals.append(interval)
    return intervals


def detect_dropout(signal: NDArray[np.float64], hz: float) -> list[Interval]:
    """Dropout = NaN run or a long flatline. Never filled in."""

    return detect_nan(signal, hz) + detect_flatline(signal, hz)


def detect_flush(abp: NDArray[np.float64], hz: float) -> list[Interval]:
    """Sudden square jump: large step up plus a high, low-pulsatility plateau."""

    x = np.asarray(abp, dtype=np.float64)
    finite = np.isfinite(x)
    if x.size < int(hz):
        return []
    win = max(int(hz * 0.4), 4)
    jump = np.zeros(x.size, dtype=np.bool_)
    for i in range(win, x.size):
        if not (finite[i] and finite[i - win]):
            continue
        if x[i] - x[i - win] >= FLUSH_JUMP_MMHG and x[i] >= FLUSH_LEVEL_MMHG:
            jump[i] = True
    high_flat = finite & (x >= FLUSH_LEVEL_MMHG)
    mask = jump | high_flat
    return _runs(mask, hz, "flush")


def detect_damping(abp: NDArray[np.float64], hz: float) -> list[Interval]:
    """Overdamped arterial line: pulse pressure collapses while samples exist."""

    x = np.asarray(abp, dtype=np.float64)
    win = max(int(hz * 1.0), 8)
    if x.size < win:
        return []
    mask = np.zeros(x.size, dtype=np.bool_)
    for i in range(0, x.size - win + 1, max(win // 2, 1)):
        sl = x[i : i + win]
        if not np.all(np.isfinite(sl)):
            continue
        if float(np.ptp(sl)) < DAMP_PULSE_MMHG and float(np.mean(sl)) > 30.0:
            mask[i : i + win] = True
    return _runs(mask, hz, "damping")


def usable_mask(
    signal: NDArray[np.float64], rejected: list[Interval], hz: float
) -> NDArray[np.bool_]:
    mask = np.isfinite(signal)
    for interval in rejected:
        start = max(int(interval.start_sec * hz), 0)
        end = min(int(math_ceil(interval.end_sec * hz)), mask.size)
        mask[start:end] = False
    return mask


def math_ceil(value: float) -> int:
    return int(np.ceil(value))


def merge_intervals(intervals: list[Interval]) -> list[Interval]:
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: (item.start_sec, item.end_sec))
    merged = [ordered[0]]
    for item in ordered[1:]:
        last = merged[-1]
        if item.start_sec <= last.end_sec + 1e-9 and item.reason == last.reason:
            merged[-1] = Interval(
                start_sec=last.start_sec,
                end_sec=max(last.end_sec, item.end_sec),
                reason=last.reason,
            )
        else:
            merged.append(item)
    return merged


def _quality(
    name: str, signal: NDArray[np.float64], hz: float, rejected: list[Interval]
) -> SignalQuality:
    mask = usable_mask(signal, rejected, hz)
    n = int(signal.size)
    usable = float(np.count_nonzero(mask) / n) if n else 0.0
    return SignalQuality(
        signal=name,
        n_samples=n,
        usable_fraction=usable,
        rejected=merge_intervals(rejected),
        interpolated=False,
    )


def raw_map_hypotension(abp: NDArray[np.float64], hz: float) -> bool:
    """Naive MAP-on-raw. Must not be used as the clinical hypotension call."""

    if abp.size == 0:
        return False
    win = max(int(hz), 1)
    for i in range(0, abp.size - win + 1, win):
        sl = abp[i : i + win]
        if np.all(np.isfinite(sl)) and float(np.mean(sl)) < HYPOTENSION_MAP:
            return True
    return False


def usable_map_hypotension(abp: NDArray[np.float64], mask: NDArray[np.bool_], hz: float) -> bool:
    if abp.size == 0:
        return False
    win = max(int(hz), 1)
    for i in range(0, abp.size - win + 1, win):
        sl = abp[i : i + win]
        keep = mask[i : i + win]
        if int(np.count_nonzero(keep)) < win // 2:
            continue
        if float(np.mean(sl[keep])) < HYPOTENSION_MAP:
            return True
    return False


def assess_case(record: CaseRecord) -> QualityReport:
    wave_hz = record.sidecar.waveform_hz
    num_hz = record.sidecar.numeric_hz
    abp_rej = detect_flush(record.abp, wave_hz) + detect_damping(record.abp, wave_hz)
    abp_rej += detect_dropout(record.abp, wave_hz)
    spo2_rej = detect_dropout(record.spo2, num_hz)
    bis_rej = detect_dropout(record.bis, num_hz) if record.sidecar.labels.has_bis else []
    abp_q = _quality("abp", record.abp, wave_hz, abp_rej)
    spo2_q = _quality("spo2", record.spo2, num_hz, spo2_rej)
    per = [abp_q, spo2_q]
    if record.sidecar.labels.has_bis:
        per.append(_quality("bis", record.bis, num_hz, bis_rej))
    abp_mask = usable_mask(record.abp, abp_rej, wave_hz)
    gap_reasons = {"nan", "flatline", "dropout"}
    gaps = [item for item in abp_q.rejected + spo2_q.rejected if item.reason in gap_reasons]
    usable_duration = {
        item.signal: float(item.usable_fraction * record.sidecar.duration_sec) for item in per
    }
    return QualityReport(
        disclaimer=SAFETY_DISCLAIMER,
        case_id=record.sidecar.case_id,
        per_signal=per,
        hypotension_on_raw=raw_map_hypotension(record.abp, wave_hz),
        hypotension_on_usable=usable_map_hypotension(record.abp, abp_mask, wave_hz),
        gaps_reported=gaps,
        downstream_incomplete=bool(gaps),
        usable_duration_sec=usable_duration,
    )


def never_interpolated(report: QualityReport) -> bool:
    return all(item.interpolated is False for item in report.per_signal)
