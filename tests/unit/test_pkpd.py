from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from or_signals.io import read_case
from or_signals.pkpd import (
    diverge_after_bolus,
    hill_bis,
    lean_body_mass_kg,
    schnider_parameters,
    series_from_infusion,
    simulate_effect_site,
)

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample"


def test_bolus_rate_and_ce_diverge() -> None:
    record = read_case(SAMPLE, "bolus")
    assert diverge_after_bolus(record.infusion_mg_per_min, record.ce_ug_per_ml, 20)
    rate_peak = int(np.argmax(record.infusion_mg_per_min))
    ce_peak = int(np.argmax(record.ce_ug_per_ml))
    assert ce_peak > rate_peak


def test_ce_tracks_depth_better_than_rate() -> None:
    record = read_case(SAMPLE, "bolus")
    depth = 100.0 - record.bis
    corr_ce = float(np.corrcoef(record.ce_ug_per_ml, depth)[0, 1])
    corr_rate = float(np.corrcoef(record.infusion_mg_per_min, depth)[0, 1])
    assert corr_ce > corr_rate


def test_published_constants_and_female_lbm() -> None:
    male = schnider_parameters()
    assert male["v1_l"] == 4.27
    assert male["ke0_per_min"] == 0.456
    female_lbm = lean_body_mass_kg(60.0, 165.0, male=False)
    assert female_lbm > 0
    female = schnider_parameters(age_y=50.0, weight_kg=60.0, height_cm=165.0, male=False)
    assert female["lbm_kg"] == pytest.approx(female_lbm)


def test_series_and_hill() -> None:
    infusion = np.full(30, 6.0, dtype=np.float64)
    infusion[10:12] = 400.0
    series = series_from_infusion(infusion, 1.0)
    assert series.model == "schnider-2cmt-effect-site"
    assert "Schnider" in series.citation
    assert len(series.effect_site_ug_per_ml) == 30
    plasma, ce = simulate_effect_site(infusion, 1.0)
    bis = hill_bis(ce)
    assert bis.shape == ce.shape
    assert diverge_after_bolus(infusion, ce, 10)
    assert diverge_after_bolus(infusion, ce, 0) is False
    assert np.all(plasma >= 0)
