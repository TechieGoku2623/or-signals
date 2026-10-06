"""Ce operating points for the designed over-sedation window. Research only."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

from or_signals.config import get_settings
from or_signals.io import read_case
from or_signals.score import labeled_windows, operating_points

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]


def main() -> None:
    sample_dir = get_settings().sample_dir
    scores, gold = labeled_windows(read_case(sample_dir, "clean"), read_case(sample_dir, "bolus"))
    rows = operating_points(scores, gold, THRESHOLDS)
    conn = duckdb.connect(":memory:")
    conn.execute(
        "CREATE TABLE op (threshold DOUBLE, tpr DOUBLE, fpr DOUBLE, precision DOUBLE, tp INTEGER)"
    )
    conn.executemany(
        "INSERT INTO op VALUES (?, ?, ?, ?, ?)",
        [(r.threshold_ce, r.tpr, r.fpr, r.precision, r.tp) for r in rows],
    )
    chosen = conn.execute(
        "SELECT threshold, tpr, fpr, precision FROM op "
        "WHERE tpr >= 0.8 ORDER BY fpr ASC, threshold ASC LIMIT 1"
    ).fetchone()
    if chosen is None:
        chosen = conn.execute(
            "SELECT threshold, tpr, fpr, precision FROM op ORDER BY tpr DESC LIMIT 1"
        ).fetchone()
    decision = (
        "Pivot to over-sedation is already decided (awareness labels 1/200). "
        f"On the designed bolus-vs-clean windows, a Ce threshold of {chosen[0]:.1f} µg/ml "
        f"gives TPR={chosen[1]:.3f}, FPR={chosen[2]:.3f}, precision={chosen[3]:.3f}. "
        "This is a research operating point, not a monitor alarm."
    )
    payload = {
        "gold": "bolus t>=25s positive; clean all negative; quality-gated Ce",
        "n_scores": int(scores.size),
        "n_positive": int(gold.sum()),
        "n_negative": int((gold == 0).sum()),
        "chosen_threshold": float(chosen[0]),
        "chosen_tpr": float(chosen[1]),
        "chosen_fpr": float(chosen[2]),
        "chosen_precision": float(chosen[3]),
        "points": [row.model_dump() for row in rows],
        "decision": decision,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        ["Ce threshold", "TP", "FP", "TN", "FN", "TPR", "FPR", "precision"],
        [
            [
                f"{row.threshold_ce:.1f}",
                str(row.tp),
                str(row.fp),
                str(row.tn),
                str(row.fn),
                pct(row.tpr),
                pct(row.fpr),
                pct(row.precision),
            ]
            for row in rows
        ],
    )
    md = (
        "# operating_point results\n\n"
        f"{decision}\n\n"
        "Gold is the designed post-bolus window, not an awareness label.\n\n"
        f"{table}\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
