"""Effect-site concentration vs depth-index proxy on the bolus case."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from or_signals.config import get_settings
from or_signals.io import read_case
from or_signals.pkpd import diverge_after_bolus

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _corr(left: np.ndarray, right: np.ndarray) -> float:
    mask = np.isfinite(left) & np.isfinite(right)
    if int(np.count_nonzero(mask)) < 3:
        return float("nan")
    return float(np.corrcoef(left[mask], right[mask])[0, 1])


def main() -> None:
    record = read_case(get_settings().sample_dir, "bolus")
    rate = record.infusion_mg_per_min
    ce = record.ce_ug_per_ml
    depth = 100.0 - record.bis
    corr_ce = _corr(ce, depth)
    corr_rate = _corr(rate, depth)
    diverged = diverge_after_bolus(rate, ce, bolus_index=20)
    ok = diverged and corr_ce > corr_rate
    decision = (
        "PK/PD layer is doing useful work: after the bolus, Ce diverges from "
        "raw infusion rate and tracks the depth-index proxy more closely. "
        "The proxy is not an awareness label."
        if ok
        else "Ce did not beat raw infusion rate on the bolus case."
    )
    payload = {
        "case_id": "bolus",
        "corr_ce_vs_depth": corr_ce,
        "corr_rate_vs_depth": corr_rate,
        "diverged_after_bolus": diverged,
        "ce_beats_rate": bool(corr_ce > corr_rate),
        "decision": decision,
        "model": "schnider-2cmt-effect-site",
        "citation": (
            "Schnider et al., Anesthesiology 1998;88:1170-82 and 1999;90:1502-16 "
            "(2-compartment reduction: V3/CL3 omitted)"
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        ["predictor", "corr vs (100-BIS proxy)"],
        [["effect-site Ce", pct(corr_ce)], ["raw infusion rate", pct(corr_rate)]],
    )
    md = f"# pkpd_validation results\n\n{decision}\n\n{table}\n"
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
