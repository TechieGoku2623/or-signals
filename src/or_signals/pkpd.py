"""2-compartment + effect-site propofol model with published Schnider constants.

Schnider is a three-compartment mammillary model. Phase 0 drops the slow
third compartment (V3/CL3) and keeps central, rapid peripheral, and effect
site. Constants are published values for a reference adult, not fitted here.

Citations:
- Schnider TW et al. Anesthesiology 1998;88:1170-1182 (PK covariates).
- Schnider TW et al. Anesthesiology 1999;90:1502-1516 (ke0).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from or_signals.schemas import PkpdSeries

# Reference adult used to instantiate the published covariate equations.
REF_AGE_Y = 40.0
REF_WEIGHT_KG = 70.0
REF_HEIGHT_CM = 170.0
KE0_PER_MIN = 0.456
V1_L = 4.27
CITATION = (
    "Schnider et al., Anesthesiology 1998;88:1170-82 and 1999;90:1502-16 "
    "(2-compartment reduction: V3/CL3 omitted)"
)


def lean_body_mass_kg(weight_kg: float, height_cm: float, male: bool = True) -> float:
    """James LBM formula as used in the Schnider covariate set."""

    ratio = weight_kg / height_cm
    if male:
        return 1.1 * weight_kg - 128.0 * ratio * ratio
    return 1.07 * weight_kg - 148.0 * ratio * ratio


def schnider_parameters(
    age_y: float = REF_AGE_Y,
    weight_kg: float = REF_WEIGHT_KG,
    height_cm: float = REF_HEIGHT_CM,
    male: bool = True,
) -> dict[str, float]:
    lbm = lean_body_mass_kg(weight_kg, height_cm, male)
    v2 = 18.9 - 0.391 * (age_y - 53.0)
    cl1 = 1.89 + 0.0456 * (weight_kg - 77.0) - 0.0681 * (lbm - 59.0) + 0.0264 * (height_cm - 177.0)
    cl2 = 1.29 - 0.024 * (age_y - 53.0)
    v1 = V1_L
    return {
        "age_y": age_y,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "lbm_kg": lbm,
        "v1_l": v1,
        "v2_l": v2,
        "cl1_l_per_min": cl1,
        "cl2_l_per_min": cl2,
        "k10_per_min": cl1 / v1,
        "k12_per_min": cl2 / v1,
        "k21_per_min": cl2 / v2,
        "ke0_per_min": KE0_PER_MIN,
    }


def simulate_effect_site(
    infusion_mg_per_min: NDArray[np.float64],
    dt_sec: float,
    parameters: dict[str, float] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Euler integration of the 2-compartment + effect-site system.

    Amounts are mg; concentrations are µg/ml (= mg/L).
    """

    params = parameters if parameters is not None else schnider_parameters()
    k10 = params["k10_per_min"]
    k12 = params["k12_per_min"]
    k21 = params["k21_per_min"]
    ke0 = params["ke0_per_min"]
    v1 = params["v1_l"]
    dt_min = dt_sec / 60.0
    n = int(infusion_mg_per_min.size)
    plasma = np.zeros(n, dtype=np.float64)
    effect = np.zeros(n, dtype=np.float64)
    a1 = 0.0
    a2 = 0.0
    ce = 0.0
    for i in range(n):
        rate = float(infusion_mg_per_min[i])
        da1 = rate - (k10 + k12) * a1 + k21 * a2
        da2 = k12 * a1 - k21 * a2
        a1 += da1 * dt_min
        a2 += da2 * dt_min
        cp = a1 / v1
        ce += ke0 * (cp - ce) * dt_min
        plasma[i] = cp
        effect[i] = ce
    return plasma, effect


def hill_bis(
    ce_ug_per_ml: NDArray[np.float64],
    e0: float = 98.0,
    emax: float = 40.0,
    ec50: float = 3.0,
    hill_n: float = 2.0,
) -> NDArray[np.float64]:
    """Synthetic depth-index proxy. Not an awareness label."""

    ce = np.asarray(ce_ug_per_ml, dtype=np.float64)
    denom = np.power(ec50, hill_n) + np.power(np.maximum(ce, 0.0), hill_n)
    out = e0 - emax * np.power(np.maximum(ce, 0.0), hill_n) / denom
    return np.asarray(out, dtype=np.float64)


def series_from_infusion(
    infusion_mg_per_min: NDArray[np.float64],
    dt_sec: float,
    parameters: dict[str, float] | None = None,
) -> PkpdSeries:
    params = parameters if parameters is not None else schnider_parameters()
    plasma, effect = simulate_effect_site(infusion_mg_per_min, dt_sec, params)
    time = np.arange(infusion_mg_per_min.size, dtype=np.float64) * dt_sec
    return PkpdSeries(
        time_sec=[float(x) for x in time],
        infusion_mg_per_min=[float(x) for x in infusion_mg_per_min],
        plasma_ug_per_ml=[float(x) for x in plasma],
        effect_site_ug_per_ml=[float(x) for x in effect],
        model="schnider-2cmt-effect-site",
        citation=CITATION,
        parameters=params,
    )


def diverge_after_bolus(
    infusion: NDArray[np.float64],
    effect: NDArray[np.float64],
    bolus_index: int,
) -> bool:
    """True when peak infusion and peak Ce do not coincide after a bolus."""

    if bolus_index <= 0 or bolus_index >= infusion.size:
        return False
    rate_peak = int(np.argmax(infusion[bolus_index:])) + bolus_index
    ce_peak = int(np.argmax(effect[bolus_index:])) + bolus_index
    return ce_peak > rate_peak and not math.isclose(float(ce_peak), float(rate_peak))
