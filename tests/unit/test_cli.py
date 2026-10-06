from __future__ import annotations

from typer.testing import CliRunner

from or_signals import SAFETY_DISCLAIMER
from or_signals.cli import app, repo_root

runner = CliRunner()


def test_demo_plan() -> None:
    result = runner.invoke(app, ["demo-plan"])
    assert result.exit_code == 0, result.stdout
    assert "clean.npz" in result.stdout
    assert "artifact.npz" in result.stdout
    assert "dropout.npz" in result.stdout
    assert "bolus.npz" in result.stdout
    assert "no-label.npz" in result.stdout
    assert "not a clinical monitor" in result.stdout.lower()


def test_version_and_sample_path() -> None:
    version = runner.invoke(app, ["version"])
    assert version.exit_code == 0
    assert "or-signals" in version.stdout
    path = runner.invoke(app, ["sample-path"])
    assert path.exit_code == 0
    assert "data/sample" in path.stdout
    assert (repo_root() / "pyproject.toml").is_file()


def test_inspect_clean_glob() -> None:
    result = runner.invoke(app, ["inspect", "--case", "data/sample/clean.*"])
    assert result.exit_code == 0, result.stdout
    assert "abp" in result.stdout
    assert "sfreq" in result.stdout or "100.0" in result.stdout
    assert "usable duration after SQI" in result.stdout
    assert SAFETY_DISCLAIMER in result.stdout
    assert "synthetic=True" in result.stdout


def test_quality_artifact_report() -> None:
    result = runner.invoke(app, ["quality", "--case", "data/sample/artifact.*", "--report"])
    assert result.exit_code == 0, result.stdout
    assert "flush" in result.stdout
    assert "hypotension_on_raw=True" in result.stdout
    assert "hypotension_on_usable=False" in result.stdout
    assert "rule:" in result.stdout
    assert "measured max ABP" in result.stdout
    assert "any_interpolated=False" in result.stdout


def test_quality_dropout_no_interpolation() -> None:
    result = runner.invoke(app, ["quality", "--case", "data/sample/dropout.*"])
    assert result.exit_code == 0, result.stdout
    assert "duration=" in result.stdout
    assert "never interpolated" in result.stdout
    assert "downstream window incomplete: true" in result.stdout.lower() or (
        "downstream_window_incomplete=True" in result.stdout
    )


def test_pkpd_bolus_plot() -> None:
    result = runner.invoke(app, ["pkpd", "--case", "data/sample/bolus.*", "--plot"])
    assert result.exit_code == 0, result.stdout
    assert "diverged_after_bolus: True" in result.stdout
    assert "infusion" in result.stdout.lower()
    assert "Ce" in result.stdout
    assert SAFETY_DISCLAIMER in result.stdout


def test_demo_walkthrough() -> None:
    result = runner.invoke(app, ["demo"])
    assert result.exit_code == 0, result.stdout
    assert "usable duration after SQI" in result.stdout
    assert "diverged_after_bolus" in result.stdout
    assert SAFETY_DISCLAIMER in result.stdout
