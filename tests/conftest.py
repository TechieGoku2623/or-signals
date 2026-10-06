from __future__ import annotations

import runpy
from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"


@pytest.fixture(scope="session", autouse=True)
def built_samples() -> None:
    runpy.run_path(str(SAMPLE / "build.py"), run_name="__main__")
