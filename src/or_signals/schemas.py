"""Typed case, quality, and PK/PD payloads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from or_signals import SAFETY_DISCLAIMER

ArtifactReason = Literal["flush", "damping", "dropout", "flatline", "nan"]


class Interval(BaseModel):
    start_sec: float
    end_sec: float
    reason: ArtifactReason


class SignalQuality(BaseModel):
    signal: str
    n_samples: int
    usable_fraction: float
    rejected: list[Interval]
    interpolated: Literal[False] = False


class CaseLabels(BaseModel):
    has_bis: bool
    has_awareness_label: bool
    has_usable_sedation_depth: bool
    awareness_label: str | None = None


class CaseSidecar(BaseModel):
    case_id: str
    duration_sec: float
    waveform_hz: float
    numeric_hz: float
    synthetic: Literal[True] = True
    path_exercised: str
    expected_behavior: str
    labels: CaseLabels
    signals: list[str]


class SampleCase(BaseModel):
    sample_id: str
    file: str
    path_exercised: str
    expected_behavior: str


class QualityReport(BaseModel):
    disclaimer: str = SAFETY_DISCLAIMER
    case_id: str
    per_signal: list[SignalQuality]
    hypotension_on_raw: bool
    hypotension_on_usable: bool
    gaps_reported: list[Interval]


class IndexRow(BaseModel):
    case_id: str
    has_bis: bool
    has_awareness_label: bool
    has_usable_sedation_depth: bool
    source: str = "synthetic-stand-in"


class PkpdSeries(BaseModel):
    time_sec: list[float]
    infusion_mg_per_min: list[float]
    plasma_ug_per_ml: list[float]
    effect_site_ug_per_ml: list[float]
    model: str
    citation: str
    parameters: dict[str, float] = Field(default_factory=dict)
