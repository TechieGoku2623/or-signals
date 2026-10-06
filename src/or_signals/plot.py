"""ASCII (and optional PPM) traces. No interpolation. Research plots only."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from or_signals.io import CaseRecord
from or_signals.schemas import Interval


def ascii_trace(
    values: NDArray[np.float64],
    *,
    width: int = 72,
    height: int = 12,
    rejected: list[Interval] | None = None,
    hz: float = 1.0,
    ylabel: str = "",
) -> str:
    """Downsampled min-max ASCII plot. Rejected columns are marked `x`."""

    y = np.asarray(values, dtype=np.float64)
    if y.size == 0 or width < 4 or height < 3:
        return "(empty trace)"
    cols = width
    edges = np.linspace(0, y.size, cols + 1)
    col_min = np.full(cols, np.nan)
    col_max = np.full(cols, np.nan)
    rejected_col = np.zeros(cols, dtype=np.bool_)
    for i in range(cols):
        sl = y[int(edges[i]) : max(int(edges[i + 1]), int(edges[i]) + 1)]
        finite = sl[np.isfinite(sl)]
        if finite.size:
            col_min[i] = float(np.min(finite))
            col_max[i] = float(np.max(finite))
        start_sec = edges[i] / hz
        end_sec = edges[i + 1] / hz
        if rejected:
            rejected_col[i] = any(
                item.start_sec < end_sec and item.end_sec > start_sec for item in rejected
            )
    finite_min = col_min[np.isfinite(col_min)]
    finite_max = col_max[np.isfinite(col_max)]
    if finite_min.size == 0:
        return "(no finite samples — gap, not interpolated)"
    lo = float(np.min(finite_min))
    hi = float(np.max(finite_max))
    if hi <= lo:
        hi = lo + 1.0
    canvas = [[" " for _ in range(cols)] for _ in range(height)]
    for i in range(cols):
        if not np.isfinite(col_min[i]):
            for row in canvas:
                row[i] = "."
            continue
        r0 = int(round((1.0 - (col_max[i] - lo) / (hi - lo)) * (height - 1)))
        r1 = int(round((1.0 - (col_min[i] - lo) / (hi - lo)) * (height - 1)))
        r0 = min(max(r0, 0), height - 1)
        r1 = min(max(r1, 0), height - 1)
        mark = "x" if rejected_col[i] else "#"
        for r in range(min(r0, r1), max(r0, r1) + 1):
            canvas[r][i] = mark
    lines = [f"{ylabel}  lo={lo:.2f}  hi={hi:.2f}  (# usable, x rejected, . gap)"]
    for row_i, row in enumerate(canvas):
        axis = hi if row_i == 0 else (lo if row_i == height - 1 else "")
        label = f"{axis:>8}" if axis != "" else "        "
        lines.append(f"{label} |{''.join(row)}")
    lines.append(f"{'':>8} +{'-' * cols}")
    lines.append(f"{'':>8}  0s{' ' * (cols - 6)}{y.size / hz:.0f}s")
    return "\n".join(lines)


def ascii_dual(
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    *,
    width: int = 72,
    label_left: str = "rate",
    label_right: str = "Ce",
) -> str:
    """Two independently scaled traces on one time axis (`*` left, `o` right)."""

    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    n = min(int(a.size), int(b.size))
    if n == 0:
        return "(empty dual trace)"
    cols = width
    edges = np.linspace(0, n, cols + 1)

    def _col_mean(series: NDArray[np.float64]) -> NDArray[np.float64]:
        out = np.full(cols, np.nan)
        for i in range(cols):
            sl = series[int(edges[i]) : max(int(edges[i + 1]), int(edges[i]) + 1)]
            finite = sl[np.isfinite(sl)]
            if finite.size:
                out[i] = float(np.mean(finite))
        return out

    ca = _col_mean(a[:n])
    cb = _col_mean(b[:n])
    height = 12
    canvas = [[" " for _ in range(cols)] for _ in range(height)]

    def _place(col_vals: NDArray[np.float64], mark: str) -> None:
        finite = col_vals[np.isfinite(col_vals)]
        if finite.size == 0:
            return
        lo = float(np.min(finite))
        hi = float(np.max(finite))
        if hi <= lo:
            hi = lo + 1.0
        for i, value in enumerate(col_vals):
            if not np.isfinite(value):
                continue
            row = int(round((1.0 - (value - lo) / (hi - lo)) * (height - 1)))
            row = min(max(row, 0), height - 1)
            canvas[row][i] = mark if canvas[row][i] == " " else "+"

    _place(ca, "*")
    _place(cb, "o")
    lines = [
        f"{label_left} (*) vs {label_right} (o); + marks overlap. Not a clinical plot.",
    ]
    for row in canvas:
        lines.append("         |" + "".join(row))
    lines.append("         +" + ("-" * cols))
    lines.append(f"          0s{' ' * (cols - 6)}{n:.0f}s")
    return "\n".join(lines)


def write_ppm(path: Path, values: NDArray[np.float64], rejected: list[Interval], hz: float) -> None:
    """Tiny portable pixmap so `--report` can leave an image without extra deps."""

    y = np.asarray(values, dtype=np.float64)
    width = 240
    height = 80
    if y.size == 0:
        path.write_bytes(b"P6\n1 1\n255\n\x00\x00\x00")
        return
    edges = np.linspace(0, y.size, width + 1)
    finite = y[np.isfinite(y)]
    lo = float(np.min(finite)) if finite.size else 0.0
    hi = float(np.max(finite)) if finite.size else 1.0
    if hi <= lo:
        hi = lo + 1.0
    pixels = bytearray()
    for row in range(height):
        for col in range(width):
            sl = y[int(edges[col]) : max(int(edges[col + 1]), int(edges[col]) + 1)]
            ok = sl[np.isfinite(sl)]
            start_sec = edges[col] / hz
            end_sec = edges[col + 1] / hz
            is_rej = any(item.start_sec < end_sec and item.end_sec > start_sec for item in rejected)
            if ok.size == 0:
                pixels.extend(b"\x30\x30\x30")
                continue
            mid = float(np.mean(ok))
            norm = (mid - lo) / (hi - lo)
            filled = int((1.0 - norm) * (height - 1)) <= row
            if is_rej:
                pixels.extend(b"\xc0\x40\x40" if filled else b"\x40\x10\x10")
            else:
                pixels.extend(b"\x40\xb0\x80" if filled else b"\x10\x18\x20")
    header = f"P6\n{width} {height}\n255\n".encode()
    path.write_bytes(header + bytes(pixels))


def artifact_measurements(record: CaseRecord, rejected: list[Interval]) -> dict[str, float | str]:
    abp = record.abp
    finite = abp[np.isfinite(abp)]
    measured_max = float(np.max(finite)) if finite.size else float("nan")
    measured_min = float(np.min(finite)) if finite.size else float("nan")
    jump = 0.0
    if abp.size > 1:
        d = np.diff(np.where(np.isfinite(abp), abp, np.nan))
        d = d[np.isfinite(d)]
        jump = float(np.max(d)) if d.size else 0.0
    reasons = sorted({item.reason for item in rejected})
    return {
        "rule_flush_jump_mmhg": 80.0,
        "rule_flush_level_mmhg": 200.0,
        "rule_damp_pulse_mmhg": 8.0,
        "measured_max_mmhg": measured_max,
        "measured_min_mmhg": measured_min,
        "measured_max_step_mmhg": jump,
        "rejected_reasons": ",".join(reasons) if reasons else "none",
    }
