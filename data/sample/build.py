"""Generate five synthetic OR excerpts (seed 0). Not VitalDB bytes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from or_signals.io import CaseRecord, write_case
from or_signals.pkpd import hill_bis, schnider_parameters, simulate_effect_site
from or_signals.schemas import CaseLabels, CaseSidecar

HERE = Path(__file__).resolve().parent
SEED = 0
DURATION = 60.0
WAVE_HZ = 100.0
NUM_HZ = 1.0


def _time(hz: float) -> NDArray[np.float64]:
    n = int(DURATION * hz)
    return np.arange(n, dtype=np.float64) / hz


def _abp(t: NDArray[np.float64], rng: np.random.Generator) -> NDArray[np.float64]:
    return (100.0 + 20.0 * np.sin(2 * np.pi * 1.2 * t) + 0.4 * rng.normal(size=t.size)).astype(
        np.float64
    )


def _spo2(t: NDArray[np.float64], rng: np.random.Generator) -> NDArray[np.float64]:
    return (97.5 + 0.4 * rng.normal(size=t.size)).astype(np.float64)


def _infusion(n: int, bolus: bool) -> NDArray[np.float64]:
    rate = np.full(n, 6.0, dtype=np.float64)
    if bolus:
        # 20-25 s: 80 mg over 5 s.
        rate[20:25] = 960.0
    return rate


def _sidecar(
    case_id: str,
    path: str,
    expected: str,
    labels: CaseLabels,
) -> CaseSidecar:
    return CaseSidecar(
        case_id=case_id,
        duration_sec=DURATION,
        waveform_hz=WAVE_HZ,
        numeric_hz=NUM_HZ,
        path_exercised=path,
        expected_behavior=expected,
        labels=labels,
        signals=["abp", "spo2", "bis", "infusion_mg_per_min", "ce_ug_per_ml"],
    )


def _record(
    sidecar: CaseSidecar,
    abp: NDArray[np.float64],
    spo2: NDArray[np.float64],
    infusion: NDArray[np.float64],
    time_wave: NDArray[np.float64],
    time_num: NDArray[np.float64],
    has_bis: bool,
    rng: np.random.Generator,
) -> CaseRecord:
    plasma, ce = simulate_effect_site(infusion, 1.0, schnider_parameters())
    if has_bis:
        bis = hill_bis(ce) + rng.normal(0.0, 0.8, size=ce.size)
        bis = np.clip(bis, 40.0, 100.0)
    else:
        bis = np.full(ce.size, np.nan, dtype=np.float64)
    return CaseRecord(
        sidecar=sidecar,
        abp=abp,
        spo2=spo2,
        bis=bis.astype(np.float64),
        infusion_mg_per_min=infusion,
        ce_ug_per_ml=ce,
        time_wave=time_wave,
        time_num=time_num,
    )


def build_cases() -> list[str]:
    rng = np.random.default_rng(SEED)
    tw = _time(WAVE_HZ)
    tn = _time(NUM_HZ)
    n_num = tn.size
    cases: list[tuple[str, CaseRecord]] = []

    clean_abp = _abp(tw, rng)
    clean = _record(
        _sidecar(
            "clean",
            "full signal coverage",
            "SQI keeps almost all samples. Usable depth-index proxy is present.",
            CaseLabels(has_bis=True, has_awareness_label=False, has_usable_sedation_depth=True),
        ),
        clean_abp,
        _spo2(tn, rng),
        _infusion(n_num, bolus=False),
        tw,
        tn,
        True,
        rng,
    )
    cases.append(("clean", clean))

    art_abp = _abp(tw, rng)
    flush = (tw >= 15.0) & (tw < 18.0)
    damp = (tw >= 18.0) & (tw < 30.0)
    art_abp[flush] = 300.0
    art_abp[damp] = 42.0 + 0.3 * rng.normal(size=int(np.count_nonzero(damp)))
    artifact = _record(
        _sidecar(
            "artifact",
            "arterial-line flush and damping",
            "SQI rejects the flush/damping window. Must not call the 42 mmHg plateau hypotension.",
            CaseLabels(has_bis=True, has_awareness_label=False, has_usable_sedation_depth=True),
        ),
        art_abp,
        _spo2(tn, rng),
        _infusion(n_num, bolus=False),
        tw,
        tn,
        True,
        rng,
    )
    cases.append(("artifact", artifact))

    drop_abp = _abp(tw, rng)
    drop_spo2 = _spo2(tn, rng)
    drop_abp[(tw >= 20.0) & (tw < 40.0)] = np.nan
    drop_spo2[(tn >= 20.0) & (tn < 40.0)] = np.nan
    dropout = _record(
        _sidecar(
            "dropout",
            "long sensor dropout",
            "Gaps are reported. Samples are never interpolated.",
            CaseLabels(has_bis=True, has_awareness_label=False, has_usable_sedation_depth=True),
        ),
        drop_abp,
        drop_spo2,
        _infusion(n_num, bolus=False),
        tw,
        tn,
        True,
        rng,
    )
    cases.append(("dropout", dropout))

    bolus = _record(
        _sidecar(
            "bolus",
            "bolus: infusion rate vs effect-site concentration",
            "Raw infusion rate and Ce diverge after the bolus. Depth proxy tracks Ce, not rate.",
            CaseLabels(has_bis=True, has_awareness_label=False, has_usable_sedation_depth=True),
        ),
        _abp(tw, rng),
        _spo2(tn, rng),
        _infusion(n_num, bolus=True),
        tw,
        tn,
        True,
        rng,
    )
    cases.append(("bolus", bolus))

    no_label = _record(
        _sidecar(
            "no-label",
            "no usable depth label",
            "Excluded from training. Reported as unlabeled.",
            CaseLabels(has_bis=False, has_awareness_label=False, has_usable_sedation_depth=False),
        ),
        _abp(tw, rng),
        _spo2(tn, rng),
        _infusion(n_num, bolus=False),
        tw,
        tn,
        False,
        rng,
    )
    cases.append(("no-label", no_label))

    for _case_id, record in cases:
        write_case(HERE, record)
        npz = HERE / f"{record.sidecar.case_id}.npz"
        if npz.stat().st_size >= 1_000_000:
            raise RuntimeError(f"{npz} is >= 1 MB")
    return [case_id for case_id, _ in cases]


def build_index() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for i in range(200):
        has_bis = bool(rng.random() < 0.44)
        has_aware = i == 0
        rows.append(
            {
                "case_id": f"syn-{i:04d}",
                "has_bis": has_bis,
                "has_awareness_label": has_aware,
                "has_usable_sedation_depth": has_bis,
                "source": "synthetic-stand-in",
            }
        )
    (HERE / "case_index.json").write_text(
        json.dumps({"n": 200, "seed": SEED, "cases": rows}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ids = build_cases()
    build_index()
    print(f"wrote synthetic cases {ids} and case_index.json (seed {SEED})")


if __name__ == "__main__":
    main()
