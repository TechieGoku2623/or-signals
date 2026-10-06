from __future__ import annotations

import os

from or_signals.config import get_settings
from or_signals.logging import configure_logging


def test_settings_point_at_sample_dir() -> None:
    settings = get_settings()
    assert settings.sample_dir.name == "sample"
    assert (settings.research_dir / "run_all.py").is_file()
    assert settings.pretty_logs is True


def test_configure_logging_dev_and_prod() -> None:
    configure_logging()
    os.environ["ORSIGNALS_ENV"] = "prod"
    try:
        configure_logging()
    finally:
        os.environ.pop("ORSIGNALS_ENV", None)
    configure_logging()
