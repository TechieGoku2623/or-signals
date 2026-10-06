from __future__ import annotations

from typer.testing import CliRunner

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
