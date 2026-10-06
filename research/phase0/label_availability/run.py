"""Awareness vs sedation-depth label availability on samples + 200-row index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

from or_signals.config import get_settings
from or_signals.io import list_case_ids, read_case
from or_signals.schemas import IndexRow

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, pct, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def main() -> None:
    sample_dir = get_settings().sample_dir
    sample_rows = []
    for case_id in list_case_ids(sample_dir):
        labels = read_case(sample_dir, case_id).sidecar.labels
        sample_rows.append(
            {
                "case_id": case_id,
                "has_bis": labels.has_bis,
                "has_awareness_label": labels.has_awareness_label,
                "has_usable_sedation_depth": labels.has_usable_sedation_depth,
            }
        )
    raw = json.loads((sample_dir / "case_index.json").read_text(encoding="utf-8"))
    index = [IndexRow.model_validate(item) for item in raw["cases"]]
    conn = duckdb.connect(":memory:")
    conn.execute(
        "CREATE TABLE idx (case_id VARCHAR, has_bis BOOLEAN, "
        "has_awareness_label BOOLEAN, has_usable_sedation_depth BOOLEAN)"
    )
    conn.executemany(
        "INSERT INTO idx VALUES (?, ?, ?, ?)",
        [
            (row.case_id, row.has_bis, row.has_awareness_label, row.has_usable_sedation_depth)
            for row in index
        ],
    )
    n_index = int(conn.execute("SELECT COUNT(*) FROM idx").fetchone()[0])  # type: ignore[index]
    n_aware = int(conn.execute("SELECT COUNT(*) FROM idx WHERE has_awareness_label").fetchone()[0])  # type: ignore[index]
    n_depth = int(
        conn.execute("SELECT COUNT(*) FROM idx WHERE has_usable_sedation_depth").fetchone()[0]  # type: ignore[index]
    )
    n_sample = len(sample_rows)
    n_sample_aware = sum(1 for row in sample_rows if row["has_awareness_label"])
    n_sample_depth = sum(1 for row in sample_rows if row["has_usable_sedation_depth"])
    n_sample_unlabeled = sum(1 for row in sample_rows if not row["has_usable_sedation_depth"])
    pivot = n_aware <= 2
    decision = (
        "Awareness labels are essentially absent "
        f"({n_aware}/{n_index} index, {n_sample_aware}/{n_sample} samples). "
        "The project pivots to over-sedation / depth-index risk. "
        "Awareness remains an unmeasured rare-event target."
        if pivot
        else "Enough awareness labels exist to attempt an awareness model."
    )
    payload = {
        "n_samples": n_sample,
        "n_samples_awareness": n_sample_aware,
        "n_samples_sedation_depth": n_sample_depth,
        "n_samples_unlabeled": n_sample_unlabeled,
        "n_index": n_index,
        "n_index_awareness": n_aware,
        "n_index_sedation_depth": n_depth,
        "pivot_to_over_sedation": pivot,
        "decision": decision,
        "samples": sample_rows,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    table = md_table(
        ["set", "n", "awareness labels", "usable depth labels"],
        [
            ["sample cases", str(n_sample), str(n_sample_aware), str(n_sample_depth)],
            ["synthetic index", str(n_index), str(n_aware), str(n_depth)],
        ],
    )
    md = (
        f"# label_availability results\n\n{decision}\n\n{table}\n\n"
        f"Index depth-label rate = {pct(n_depth / n_index)}.\n"
    )
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
