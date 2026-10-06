from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from or_signals.inspect import inspect_case
from or_signals.io import read_case, resolve_case
from or_signals.plot import ascii_dual, ascii_trace, write_ppm
from or_signals.score import labeled_windows, operating_points
from or_signals.sqi import assess_case

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample"


def test_resolve_case_id_path_and_glob() -> None:
    a = resolve_case("clean", SAMPLE)
    b = resolve_case(str(SAMPLE / "clean.npz"))
    c = resolve_case(str(SAMPLE / "clean.*"))
    assert a.sidecar.case_id == b.sidecar.case_id == c.sidecar.case_id == "clean"
    with pytest.raises(FileNotFoundError):
        resolve_case("missing-case", SAMPLE)


def test_inspect_clean_inventory() -> None:
    report = inspect_case(read_case(SAMPLE, "clean"))
    names = [item.name for item in report.channels]
    assert names[:3] == ["abp", "spo2", "bis"]
    abp = report.channels[0]
    assert abp.sfreq == 100.0
    assert abp.coverage > 0.99
    assert report.usable_duration_after_sqi_sec > 50.0
    assert "not a clinical monitor" in report.disclaimer.lower()


def test_dropout_downstream_incomplete() -> None:
    report = assess_case(read_case(SAMPLE, "dropout"))
    assert report.gaps_reported
    assert report.downstream_incomplete is True
    assert all(item.interpolated is False for item in report.per_signal)
    gap = max(item.end_sec - item.start_sec for item in report.gaps_reported)
    assert gap >= 19.0


def test_operating_points_separate_bolus() -> None:
    scores, gold = labeled_windows(read_case(SAMPLE, "clean"), read_case(SAMPLE, "bolus"))
    assert int(gold.sum()) > 0
    assert int((gold == 0).sum()) > 0
    rows = operating_points(scores, gold, [0.5, 2.0, 50.0])
    assert rows[0].tpr >= rows[-1].tpr
    high = operating_points(scores, gold, [1e9])[0]
    assert high.tp == 0


def test_ascii_and_ppm(tmp_path: Path) -> None:
    y = np.linspace(40.0, 120.0, 200)
    text = ascii_trace(y, width=40, height=8, hz=10.0, ylabel="ABP")
    assert "ABP" in text
    empty = ascii_trace(np.array([], dtype=np.float64))
    assert "empty" in empty
    gap = ascii_trace(np.array([np.nan, np.nan], dtype=np.float64))
    assert "gap" in gap
    dual = ascii_dual(np.ones(30), np.linspace(0, 3, 30), width=20)
    assert "*" in dual and "o" in dual
    dest = tmp_path / "trace.ppm"
    write_ppm(dest, y, [], 10.0)
    assert dest.read_bytes().startswith(b"P6")
    write_ppm(tmp_path / "empty.ppm", np.array([], dtype=np.float64), [], 1.0)
