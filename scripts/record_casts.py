"""Write asciinema v2 casts of the Phase 3 walkthrough. No credentials."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
WIDTH = 120
HEIGHT = 40


def _run(args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "TERM": "xterm-256color"},
    )
    return proc.stdout


def _cast(path: Path, title: str, blocks: list[tuple[str, str]]) -> None:
    header = {
        "version": 2,
        "width": WIDTH,
        "height": HEIGHT,
        "timestamp": int(time.time()),
        "title": title,
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    events: list[list[object]] = []
    clock = 0.05
    for command, output in blocks:
        events.append([round(clock, 4), "o", f"$ {command}\r\n"])
        clock += 0.12
        text = output.replace("\n", "\r\n")
        if not text.endswith("\r\n"):
            text += "\r\n"
        events.append([round(clock, 4), "o", text])
        clock += max(0.35, min(8.0, 0.015 * len(text)))
        events.append([round(clock, 4), "o", "\r\n"])
        clock += 0.08
    lines = [json.dumps(header, separators=(",", ":"))]
    lines.extend(json.dumps(event, separators=(",", ":")) for event in events)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    inspect = _run([py, "-m", "or_signals.cli", "inspect", "--case", "data/sample/clean.*"])
    _cast(
        DEMO / "01-inspect-signals.cast",
        "or-signals inspect",
        [("or-signals inspect --case data/sample/clean.*", inspect)],
    )
    artifact = _run(
        [py, "-m", "or_signals.cli", "quality", "--case", "data/sample/artifact.*", "--report"]
    )
    dropout = _run([py, "-m", "or_signals.cli", "quality", "--case", "data/sample/dropout.*"])
    _cast(
        DEMO / "02-artifact-rejection.cast",
        "or-signals artifact rejection",
        [
            ("or-signals quality --case data/sample/artifact.* --report", artifact),
            ("or-signals quality --case data/sample/dropout.*", dropout),
        ],
    )
    pkpd = _run([py, "-m", "or_signals.cli", "pkpd", "--case", "data/sample/bolus.*", "--plot"])
    _cast(
        DEMO / "03-pkpd-divergence.cast",
        "or-signals pkpd divergence",
        [("or-signals pkpd --case data/sample/bolus.* --plot", pkpd)],
    )
    eval_out = _run(["make", "eval"])
    _cast(
        DEMO / "04-evaluation.cast",
        "or-signals evaluation",
        [("make eval", eval_out)],
    )


if __name__ == "__main__":
    main()
