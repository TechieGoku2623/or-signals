from __future__ import annotations

from pathlib import Path

import numpy as np

from or_signals.io import list_case_ids, read_case
from or_signals.sqi import (
    assess_case,
    detect_dropout,
    detect_flatline,
    detect_flush,
    never_interpolated,
    raw_map_hypotension,
    usable_map_hypotension,
    usable_mask,
)

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample"


def test_five_cases_present() -> None:
    assert list_case_ids(SAMPLE) == ["artifact", "bolus", "clean", "dropout", "no-label"]


def test_clean_mostly_usable() -> None:
    report = assess_case(read_case(SAMPLE, "clean"))
    abp = next(item for item in report.per_signal if item.signal == "abp")
    assert abp.usable_fraction > 0.9
    assert report.hypotension_on_usable is False
    assert never_interpolated(report)
    assert "not a clinical monitor" in report.disclaimer.lower()


def test_flush_rejected_not_hypotension() -> None:
    record = read_case(SAMPLE, "artifact")
    report = assess_case(record)
    abp = next(item for item in report.per_signal if item.signal == "abp")
    assert abp.usable_fraction < 0.8
    assert any(item.reason in {"flush", "damping", "flatline"} for item in abp.rejected)
    assert report.hypotension_on_raw is True
    assert report.hypotension_on_usable is False
    assert abp.interpolated is False


def test_dropout_gaps_not_interpolated() -> None:
    record = read_case(SAMPLE, "dropout")
    report = assess_case(record)
    assert report.gaps_reported
    assert all(item.interpolated is False for item in report.per_signal)
    assert np.isnan(record.abp).any()
    filled = record.abp.copy()
    # The library must not do this; the test only documents the invariant.
    assert not np.isfinite(filled).all()


def test_no_label_excluded() -> None:
    record = read_case(SAMPLE, "no-label")
    assert record.sidecar.labels.has_usable_sedation_depth is False
    assert record.sidecar.labels.has_bis is False
    assert np.isnan(record.bis).all()
    report = assess_case(record)
    assert all(item.signal != "bis" for item in report.per_signal)


def test_detect_helpers_on_tiny_arrays() -> None:
    short = np.array([80.0, 85.0], dtype=np.float64)
    assert detect_flush(short, 100.0) == []
    assert detect_flatline(np.array([], dtype=np.float64), 100.0) == []
    assert detect_dropout(np.array([np.nan, np.nan, np.nan], dtype=np.float64), 1.0)
    assert raw_map_hypotension(np.array([], dtype=np.float64), 1.0) is False
    mask = usable_mask(np.array([80.0, 85.0], dtype=np.float64), [], 1.0)
    assert usable_map_hypotension(np.array([80.0, 85.0], dtype=np.float64), mask, 1.0) is False
