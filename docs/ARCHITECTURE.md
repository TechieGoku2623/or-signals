# Architecture (Phase 1)

Research tooling, **not** a clinical monitor and **not** a medical device.
Sample waveforms are synthetic. Depth-index proxies are not awareness
labels. No credentials are required. No VitalDB bytes are stored.

## Data contracts

| Object | Role |
| --- | --- |
| `CaseSidecar` + `.npz` | Synthetic excerpt: ABP, SpO2, BIS-like proxy, infusion, Ce |
| `QualityReport` | Per-signal usable fraction, rejected intervals, `interpolated=false`, gaps |
| `InspectReport` | Channel inventory, sfreq, coverage, usable duration after SQI |
| `PkpdSeries` | Schnider-style 2-cmt + effect-site; published constants, cited |
| `OperatingPoint` | Ce threshold vs designed post-bolus window (over-sedation pivot) |

`QualityReport.interpolated` is always false. Gaps are listed, never filled.

## Event topology

```
synthetic excerpt --inspect--> channel inventory + coverage
                |
                +-- SQI (flush / damping / dropout)
                |         |
                |         +-- usable windows; downstream incomplete if gapped
                |
                +-- infusion rate --PK/PD--> Ce
                              |
                              +-- operating-point table (over-sedation)
```

## CLI surface (Phase 2)

- `or-signals inspect --case data/sample/clean.*`
- `or-signals quality --case data/sample/artifact.* --report`
- `or-signals quality --case data/sample/dropout.*`
- `or-signals pkpd --case data/sample/bolus.* --plot`

`--case` accepts an id, a `.npz`/`.json` path, or a quoted glob.

## Constraints

1. Never interpolate a dropout or NaN run.
2. Arterial flush / damping is rejected and is not called hypotension.
3. Raw infusion rate is not a substitute for Ce after a bolus.
4. BIS-like values are a Hill-of-Ce proxy, not recall of awareness.
5. No VitalDB download, DUA, or credentials in this repository.
