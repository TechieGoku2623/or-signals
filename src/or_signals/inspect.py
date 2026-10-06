"""Channel inventory and usable duration after SQI. Research, not a monitor."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from or_signals import SAFETY_DISCLAIMER
from or_signals.io import CaseRecord
from or_signals.schemas import ChannelInventory, InspectReport
from or_signals.sqi import assess_case


def _coverage(signal: NDArray[np.float64]) -> float:
    n = int(signal.size)
    if n == 0:
        return 0.0
    return float(np.count_nonzero(np.isfinite(signal)) / n)


def inspect_case(record: CaseRecord) -> InspectReport:
    quality = assess_case(record)
    usable = {item.signal: item for item in quality.per_signal}
    sidecar = record.sidecar
    specs: list[tuple[str, NDArray[np.float64], float]] = [
        ("abp", record.abp, sidecar.waveform_hz),
        ("spo2", record.spo2, sidecar.numeric_hz),
        ("bis", record.bis, sidecar.numeric_hz),
        ("infusion_mg_per_min", record.infusion_mg_per_min, sidecar.numeric_hz),
        ("ce_ug_per_ml", record.ce_ug_per_ml, sidecar.numeric_hz),
    ]
    channels: list[ChannelInventory] = []
    for name, signal, hz in specs:
        n = int(signal.size)
        duration = (n / hz) if hz else 0.0
        frac = usable[name].usable_fraction if name in usable else _coverage(signal)
        channels.append(
            ChannelInventory(
                name=name,
                sfreq=hz,
                n_samples=n,
                duration_sec=duration,
                coverage=_coverage(signal),
                usable_fraction=frac,
                usable_duration_sec=frac * duration,
            )
        )
    after = min(
        (item.usable_duration_sec for item in channels if item.name in {"abp", "spo2"}),
        default=0.0,
    )
    return InspectReport(
        disclaimer=SAFETY_DISCLAIMER,
        case_id=sidecar.case_id,
        synthetic=bool(sidecar.synthetic),
        duration_sec=sidecar.duration_sec,
        waveform_hz=sidecar.waveform_hz,
        numeric_hz=sidecar.numeric_hz,
        channels=channels,
        usable_duration_after_sqi_sec=after,
    )
