"""Plain-text reports for inspect / quality / pkpd."""

from __future__ import annotations

import numpy as np

from or_signals import SAFETY_DISCLAIMER
from or_signals.io import CaseRecord
from or_signals.pkpd import diverge_after_bolus, series_from_infusion
from or_signals.plot import artifact_measurements, ascii_dual, ascii_trace
from or_signals.schemas import InspectReport, QualityReport
from or_signals.sqi import FLUSH_JUMP_MMHG, FLUSH_LEVEL_MMHG, assess_case


def render_inspect(report: InspectReport) -> str:
    lines = [
        SAFETY_DISCLAIMER,
        "",
        f"case: {report.case_id}  synthetic={report.synthetic}",
        f"duration_sec={report.duration_sec:.1f}  waveform_hz={report.waveform_hz}  "
        f"numeric_hz={report.numeric_hz}",
        "",
        f"{'channel':<22}{'sfreq':>8}{'n':>8}{'cover':>8}{'usable_s':>10}{'usable%':>8}",
    ]
    for ch in report.channels:
        lines.append(
            f"{ch.name:<22}{ch.sfreq:8.1f}{ch.n_samples:8d}{ch.coverage:8.3f}"
            f"{ch.usable_duration_sec:10.2f}{ch.usable_fraction:8.3f}"
        )
    lines.append("")
    lines.append(
        f"usable duration after SQI (min of ABP/SpO2): {report.usable_duration_after_sqi_sec:.2f}s"
    )
    lines.append("Waveforms are synthetic. Depth-index proxies are not awareness labels.")
    return "\n".join(lines)


def render_quality(record: CaseRecord, report: QualityReport, *, plot: bool) -> str:
    lines = [
        SAFETY_DISCLAIMER,
        "",
        f"case: {report.case_id}",
        f"hypotension_on_raw={report.hypotension_on_raw}  "
        f"hypotension_on_usable={report.hypotension_on_usable}",
        f"any_interpolated={any(item.interpolated for item in report.per_signal)}",
        f"downstream_window_incomplete={report.downstream_incomplete}",
        "",
        "per-signal SQI",
    ]
    for item in report.per_signal:
        rejected = (
            ", ".join(f"{iv.reason} {iv.start_sec:.1f}-{iv.end_sec:.1f}s" for iv in item.rejected)
            or "none"
        )
        lines.append(
            f"  {item.signal:<6} usable={item.usable_fraction:.3f}  "
            f"n={item.n_samples}  interpolated={item.interpolated}  rejected=[{rejected}]"
        )
    if report.gaps_reported:
        lines.append("")
        lines.append("gaps (never interpolated):")
        for gap in report.gaps_reported:
            dur = gap.end_sec - gap.start_sec
            lines.append(
                f"  {gap.reason}  {gap.start_sec:.1f}-{gap.end_sec:.1f}s  duration={dur:.1f}s"
            )
        lines.append("downstream window incomplete: true (gap removes samples from later joins)")
    else:
        lines.append("")
        lines.append("gaps: none")
    abp_q = next((item for item in report.per_signal if item.signal == "abp"), None)
    if abp_q is not None:
        meas = artifact_measurements(record, abp_q.rejected)
        lines.append("")
        lines.append("artifact rules + measured values")
        lines.append(
            f"  rule: flush if jump>={FLUSH_JUMP_MMHG:.0f} mmHg "
            f"and level>={FLUSH_LEVEL_MMHG:.0f} mmHg"
        )
        lines.append("  rule: damping if pulse pressure < 8 mmHg on a 1 s window")
        lines.append(
            f"  measured max ABP={meas['measured_max_mmhg']:.1f} mmHg  "
            f"min={meas['measured_min_mmhg']:.1f} mmHg  "
            f"max step={meas['measured_max_step_mmhg']:.1f} mmHg"
        )
        lines.append(f"  rejected reasons: {meas['rejected_reasons']}")
        if plot:
            lines.append("")
            lines.append(
                ascii_trace(
                    record.abp,
                    width=72,
                    height=8,
                    rejected=abp_q.rejected,
                    hz=record.sidecar.waveform_hz,
                    ylabel="ABP mmHg",
                )
            )
    return "\n".join(lines)


def render_pkpd(record: CaseRecord, *, plot: bool) -> str:
    series = series_from_infusion(record.infusion_mg_per_min, 1.0)
    rate = np.asarray(record.infusion_mg_per_min, dtype=np.float64)
    stored = np.asarray(record.ce_ug_per_ml, dtype=np.float64)
    recomputed = np.asarray(series.effect_site_ug_per_ml, dtype=np.float64)
    diverged = diverge_after_bolus(rate, stored, 20)
    rate_peak = int(np.argmax(rate))
    ce_peak = int(np.argmax(stored))
    lines = [
        SAFETY_DISCLAIMER,
        "",
        f"case: {record.sidecar.case_id}",
        f"model: {series.model}",
        f"citation: {series.citation[:72]}",
        f"raw infusion peak at t={rate_peak:.0f}s  value={float(rate[rate_peak]):.1f} mg/min",
        f"effect-site Ce peak at t={ce_peak:.0f}s  value={float(stored[ce_peak]):.3f} µg/ml",
        f"diverged_after_bolus: {diverged}",
        f"recomputed Ce matches stored: {bool(np.allclose(stored, recomputed, atol=1e-6))}",
        "Depth-index proxies are not awareness labels. Waveforms are synthetic.",
    ]
    if plot:
        lines.append("")
        lines.append(
            ascii_dual(
                rate,
                stored,
                width=72,
                label_left="infusion mg/min",
                label_right="Ce µg/ml",
            )
        )
    return "\n".join(lines)


def assess_and_render_quality(record: CaseRecord, *, plot: bool) -> str:
    return render_quality(record, assess_case(record), plot=plot)
