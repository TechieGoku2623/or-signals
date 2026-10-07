"""Phase 1–3 CLI: inspect, quality, pkpd. Research, not a monitor."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from or_signals import SAFETY_DISCLAIMER, __version__
from or_signals.config import get_settings
from or_signals.inspect import inspect_case
from or_signals.io import resolve_case
from or_signals.logging import configure_logging
from or_signals.plot import write_ppm
from or_signals.render import assess_and_render_quality, render_inspect, render_pkpd
from or_signals.schemas import SampleCase
from or_signals.sqi import assess_case

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=100, highlight=False, soft_wrap=True)


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
        "\nWalkthrough: `or-signals inspect|quality|pkpd --case data/sample/<id>.*`. "
        "Waveforms are synthetic. Depth-index proxies are not awareness labels."
    )
    console.print(f"Sample manifest: {get_settings().sample_dir / 'manifest.json'}")


@app.command("sample-path")
def sample_path() -> None:
    console.print(str(get_settings().sample_dir.resolve()))


@app.command("inspect")
def inspect_cmd(
    case: str = typer.Option(..., "--case", help="Case id, path, or quoted glob (clean.*)."),
) -> None:
    """Channel inventory, sfreq, coverage, usable duration after SQI."""

    record = resolve_case(case)
    print(render_inspect(inspect_case(record)))


@app.command("quality")
def quality_cmd(
    case: str = typer.Option(..., "--case", help="Case id, path, or quoted glob."),
    report: bool = typer.Option(False, "--report", help="Print rule, measured values, ASCII plot."),
    summary: bool = typer.Option(False, "--summary", help="Rules and values, no tall plot"),
) -> None:
    """SQI report. Flush is rejected. Gaps are never interpolated."""

    record = resolve_case(case)
    want_plot = (report or record.sidecar.case_id == "artifact") and not summary
    text = assess_and_render_quality(record, plot=want_plot)
    print(text)
    if report and not summary:
        dest = get_settings().repo_root / "demo" / f"quality-{record.sidecar.case_id}.ppm"
        dest.parent.mkdir(parents=True, exist_ok=True)
        q = assess_case(record)
        abp_q = next(item for item in q.per_signal if item.signal == "abp")
        write_ppm(dest, record.abp, abp_q.rejected, record.sidecar.waveform_hz)
        print(f"wrote {dest.relative_to(get_settings().repo_root)}")


@app.command("pkpd")
def pkpd_cmd(
    case: str = typer.Option(..., "--case", help="Case id, path, or quoted glob."),
    plot: bool = typer.Option(False, "--plot", help="ASCII infusion vs effect-site Ce."),
) -> None:
    """Raw infusion rate vs Schnider-style effect-site concentration."""

    record = resolve_case(case)
    print(render_pkpd(record, plot=plot))


@app.command("eval")
def eval_cmd(
    summary: bool = typer.Option(True, "--summary/--full"),
) -> None:
    """Print the published label-scarcity table."""

    path = get_settings().repo_root / "docs" / "EVALUATION.md"
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Evaluation"):
            continue
        print(line[:100])
        if line.strip():
            n += 1
        if n >= 14:
            break
    print()
    print(SAFETY_DISCLAIMER)


@app.command("demo")
def demo() -> None:
    """Full Phase 3 walkthrough on the committed synthetic cases."""

    sample = get_settings().sample_dir
    steps = [
        ("inspect clean", ["inspect", "--case", str(sample / "clean.*")]),
        (
            "quality artifact --report",
            ["quality", "--case", str(sample / "artifact.*"), "--report"],
        ),
        ("quality dropout", ["quality", "--case", str(sample / "dropout.*")]),
        ("pkpd bolus --plot", ["pkpd", "--case", str(sample / "bolus.*"), "--plot"]),
    ]
    console.print("[bold]or-signals demo walkthrough[/bold]")
    console.print(SAFETY_DISCLAIMER)
    for title, args in steps:
        console.print(f"\n=== {title} ===\n")
        console.print(f"$ or-signals {' '.join(args)}\n")
        app(args, standalone_mode=False)
    console.print("\nThen run `make eval` for operating-point, SQI, and label-availability tables.")
    console.print(SAFETY_DISCLAIMER)


def repo_root() -> Path:
    return get_settings().repo_root


if __name__ == "__main__":
    app()
