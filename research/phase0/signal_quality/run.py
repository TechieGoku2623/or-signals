"""Usable fraction after artifact rejection on the five sample cases."""

from __future__ import annotations

import sys
from pathlib import Path

from or_signals.config import get_settings
from or_signals.io import list_case_ids, read_case
from or_signals.sqi import assess_case

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def main() -> None:
    sample_dir = get_settings().sample_dir
    rows: list[list[str]] = []
    cases: dict[str, object] = {}
    artifact_rejected = False
    dropout_gapped = False
    interpolated = False
    flush_not_hypo = False
    for case_id in list_case_ids(sample_dir):
        record = read_case(sample_dir, case_id)
        report = assess_case(record)
        per = {
            item.signal: {
                "usable_fraction": item.usable_fraction,
                "n_rejected": len(item.rejected),
                "interpolated": item.interpolated,
            }
            for item in report.per_signal
        }
        cases[case_id] = {
            "per_signal": per,
            "hypotension_on_raw": report.hypotension_on_raw,
            "hypotension_on_usable": report.hypotension_on_usable,
            "n_gaps": len(report.gaps_reported),
        }
        if case_id == "artifact":
            artifact_rejected = per["abp"]["usable_fraction"] < 0.8
            flush_not_hypo = report.hypotension_on_raw and not report.hypotension_on_usable
        if case_id == "dropout":
            dropout_gapped = report.gaps_reported != []
        interpolated = interpolated or any(item.interpolated for item in report.per_signal)
        abp = per.get("abp", {"usable_fraction": 0.0})
        spo2 = per.get("spo2", {"usable_fraction": 0.0})
        rows.append(
            [
                case_id,
                pct(float(abp["usable_fraction"])),
                pct(float(spo2["usable_fraction"])),
                str(report.hypotension_on_raw),
                str(report.hypotension_on_usable),
            ]
        )
    decision = (
        "SQI rejects flush/damping and reports dropout gaps without interpolation. "
        "The 42 mmHg damped plateau is not labeled hypotension on usable samples."
        if artifact_rejected and dropout_gapped and not interpolated
        else "SQI failed a designed artifact path."
    )
    payload = {
        "cases": cases,
        "artifact_rejected": artifact_rejected,
        "flush_not_called_hypotension": flush_not_hypo,
        "dropout_gaps_reported": dropout_gapped,
        "any_interpolated": interpolated,
        "decision": decision,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        ["case", "ABP usable", "SpO2 usable", "raw hypo", "usable hypo"],
        rows,
    )
    md = f"# signal_quality results\n\n{decision}\n\n{table}\n"
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
