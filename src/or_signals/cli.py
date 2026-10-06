"""Phase 0 CLI. Scoring commands land in Phase 2."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from or_signals import SAFETY_DISCLAIMER, __version__
from or_signals.config import get_settings
from or_signals.logging import configure_logging
from or_signals.schemas import SampleCase

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=140)


def _load_samples() -> list[SampleCase]:
    path = get_settings().sample_dir / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [SampleCase.model_validate(item) for item in raw["samples"]]


@app.callback()
def _main() -> None:
    configure_logging()


@app.command("version")
def version() -> None:
    console.print(f"or-signals {__version__}")


@app.command("demo-plan")
def demo_plan() -> None:
    """Print the five designed case excerpts and the path each exercises."""

    samples = _load_samples()
    console.print("[bold]or-signals designed sample cases[/bold]\n")
    for sample in samples:
        console.print(f"[bold]{sample.file}[/bold]  {sample.sample_id}")
        console.print(f"  path:     {sample.path_exercised}")
        console.print(f"  expected: {sample.expected_behavior}\n")
    console.print()
    console.print(SAFETY_DISCLAIMER)
    console.print(
        "\n`or-signals score` is Phase 2. This listing is the dry-run. "
        "Waveforms are synthetic. Depth-index proxies are not awareness labels."
    )
    console.print(f"Sample manifest: {get_settings().sample_dir / 'manifest.json'}")


@app.command("sample-path")
def sample_path() -> None:
    console.print(str(get_settings().sample_dir.resolve()))


def repo_root() -> Path:
    return get_settings().repo_root
