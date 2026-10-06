"""Read/write synthetic case excerpts: numpy archive + JSON sidecar."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from or_signals.schemas import CaseSidecar

ARRAYS = ("abp", "spo2", "bis", "infusion_mg_per_min", "ce_ug_per_ml", "time_wave", "time_num")


class CaseRecord:
    def __init__(
        self,
        sidecar: CaseSidecar,
        abp: NDArray[np.float64],
        spo2: NDArray[np.float64],
        bis: NDArray[np.float64],
        infusion_mg_per_min: NDArray[np.float64],
        ce_ug_per_ml: NDArray[np.float64],
        time_wave: NDArray[np.float64],
        time_num: NDArray[np.float64],
    ) -> None:
        self.sidecar = sidecar
        self.abp = abp
        self.spo2 = spo2
        self.bis = bis
        self.infusion_mg_per_min = infusion_mg_per_min
        self.ce_ug_per_ml = ce_ug_per_ml
        self.time_wave = time_wave
        self.time_num = time_num


def case_paths(sample_dir: Path, case_id: str) -> tuple[Path, Path]:
    return sample_dir / f"{case_id}.npz", sample_dir / f"{case_id}.json"


def write_case(sample_dir: Path, record: CaseRecord) -> None:
    npz_path, json_path = case_paths(sample_dir, record.sidecar.case_id)
    np.savez_compressed(
        npz_path,
        abp=record.abp,
        spo2=record.spo2,
        bis=record.bis,
        infusion_mg_per_min=record.infusion_mg_per_min,
        ce_ug_per_ml=record.ce_ug_per_ml,
        time_wave=record.time_wave,
        time_num=record.time_num,
    )
    json_path.write_text(record.sidecar.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_case(sample_dir: Path, case_id: str) -> CaseRecord:
    npz_path, json_path = case_paths(sample_dir, case_id)
    sidecar = CaseSidecar.model_validate(json.loads(json_path.read_text(encoding="utf-8")))
    with np.load(npz_path) as blob:
        arrays = {name: np.asarray(blob[name], dtype=np.float64) for name in ARRAYS}
    return CaseRecord(
        sidecar=sidecar,
        abp=arrays["abp"],
        spo2=arrays["spo2"],
        bis=arrays["bis"],
        infusion_mg_per_min=arrays["infusion_mg_per_min"],
        ce_ug_per_ml=arrays["ce_ug_per_ml"],
        time_wave=arrays["time_wave"],
        time_num=arrays["time_num"],
    )


def list_case_ids(sample_dir: Path) -> list[str]:
    skip = {"manifest", "case_index"}
    return sorted(path.stem for path in sample_dir.glob("*.json") if path.stem not in skip)


def resolve_case(spec: str, sample_dir: Path | None = None) -> CaseRecord:
    """Load a case from an id, a .npz/.json path, or a quoted glob (`clean.*`)."""

    from or_signals.config import get_settings

    root = sample_dir if sample_dir is not None else get_settings().sample_dir
    raw = spec.strip()
    if any(char in raw for char in "*?["):
        patterned = Path(raw)
        matches = sorted(patterned.parent.glob(patterned.name))
        if not matches:
            matches = sorted(Path().glob(raw))
        if not matches:
            matches = sorted(root.glob(patterned.name))
        stems = sorted({path.stem for path in matches if path.suffix in {".npz", ".json"}})
        stems = [stem for stem in stems if stem not in {"manifest", "case_index"}]
        if len(stems) != 1:
            raise FileNotFoundError(f"glob {raw!r} did not resolve to one case (got {stems})")
        parent = next(path.parent for path in matches if path.stem == stems[0])
        return read_case(parent, stems[0])
    path = Path(raw)
    if path.suffix in {".npz", ".json"} and path.exists():
        return read_case(path.parent, path.stem)
    if (root / f"{path.name}.npz").exists() and (root / f"{path.name}.json").exists():
        return read_case(root, path.name)
    if (root / f"{raw}.npz").exists():
        return read_case(root, raw)
    raise FileNotFoundError(f"cannot resolve case spec {spec!r}")
