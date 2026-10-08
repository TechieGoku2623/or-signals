# or-signals

Waveform-first research on intraoperative awareness and over-sedation risk.
Artifact/SQI is a first-class module. Exposure is PK/PD effect-site
concentration, not raw infusion rate.

[![ci](https://github.com/techiegoku2623/or-signals/actions/workflows/ci.yml/badge.svg)](https://github.com/techiegoku2623/or-signals/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


![or-signals demo](demo/out/or-signals-demo.gif)

Regenerable terminal video: `make record`. [Full mp4](demo/out/or-signals-demo.mp4). Per-shot loops live in `demo/out/`. See `demo/README.md`.

## Status

| Phase | Deliverable | Status |
| --- | --- | --- |
| 0 | Research memo and harnesses | Merged |
| 1 | Architecture, schemas, data contracts | Merged — docs/ARCHITECTURE.md |
| 2 | First vertical slice | Merged |
| 3 | Evaluation and demo | Merged |


## The problem this solves

OR monitors already show pressure, saturation, a pump rate, and a processed
EEG number. They do not join those streams into a quality-gated, effect-site
exposure with an honest label. An arterial flush looks like a crisis. A
bolus makes rate and brain concentration diverge. Awareness labels are so
rare that a model of awareness is usually a model of BIS.

This is research, not a clinical monitor and not a medical device.
Depth-index proxies are not awareness labels. Sample waveforms in this
repository are synthetic, not VitalDB excerpts (see `docs/DATA.md`). No
patient-identifiable data is used. No credentials are required.

## Walkthrough

`make demo` is the full Phase 3 walkthrough. Actual stdout from this
environment (PATH includes `$HOME/.local/bin`):

```
=== or-signals inspect clean ===
uv run or-signals inspect --case 'data/sample/clean.*'
Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.

case: clean  synthetic=True
duration_sec=60.0  waveform_hz=100.0  numeric_hz=1.0

channel                  sfreq       n   cover  usable_s usable%
abp                      100.0    6000   1.000     60.00   1.000
spo2                       1.0      60   1.000     60.00   1.000
bis                        1.0      60   1.000     60.00   1.000
infusion_mg_per_min        1.0      60   1.000     60.00   1.000
ce_ug_per_ml               1.0      60   1.000     60.00   1.000

usable duration after SQI (min of ABP/SpO2): 60.00s
Waveforms are synthetic. Depth-index proxies are not awareness labels.

Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.

=== or-signals quality artifact --report ===
uv run or-signals quality --case 'data/sample/artifact.*' --report
Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.

case: artifact
hypotension_on_raw=True  hypotension_on_usable=False
any_interpolated=False
downstream_window_incomplete=True

per-signal SQI
  abp    usable=0.750  n=6000  interpolated=False  rejected=[flush 15.0-18.0s, damping 15.0-30.0s, flatline 15.0-18.0s]
  spo2   usable=1.000  n=60  interpolated=False  rejected=[none]
  bis    usable=1.000  n=60  interpolated=False  rejected=[none]

gaps (never interpolated):
  flatline  15.0-18.0s  duration=3.0s
downstream window incomplete: true (gap removes samples from later joins)

artifact rules + measured values
  rule: flush if jump>=80 mmHg and level>=200 mmHg
  rule: damping if pulse pressure < 8 mmHg on a 1 s window
  measured max ABP=300.0 mmHg  min=41.1 mmHg  max step=201.3 mmHg
  rejected reasons: damping,flatline,flush

ABP mmHg  lo=41.06  hi=300.00  (# usable, x rejected, . gap)
   300.0 |                  xxxx                                                  
         |                     x                                                  
         |                     x                                                  
         |                     x                                                  
         |                     x                                                  
         |                     x                                                  
         |                     x                                                  
         |                     x                                                  
         |##################   x              ####################################
         |##################   x              ####################################
         |                     x                                                  
41.056133950412466 |                     xxxxxxxxxxxxxxx                                    
         +------------------------------------------------------------------------
          0s                                                                  60s

Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.
wrote demo/quality-artifact.ppm

=== or-signals quality dropout ===
uv run or-signals quality --case 'data/sample/dropout.*'
Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.

case: dropout
hypotension_on_raw=False  hypotension_on_usable=False
any_interpolated=False
downstream_window_incomplete=True

per-signal SQI
  abp    usable=0.667  n=6000  interpolated=False  rejected=[nan 20.0-40.0s]
  spo2   usable=0.667  n=60  interpolated=False  rejected=[nan 20.0-40.0s]
  bis    usable=1.000  n=60  interpolated=False  rejected=[none]

gaps (never interpolated):
  nan  20.0-40.0s  duration=20.0s
  nan  20.0-40.0s  duration=20.0s
downstream window incomplete: true (gap removes samples from later joins)

artifact rules + measured values
  rule: flush if jump>=80 mmHg and level>=200 mmHg
  rule: damping if pulse pressure < 8 mmHg on a 1 s window
  measured max ABP=121.0 mmHg  min=78.4 mmHg  max step=3.3 mmHg
  rejected reasons: nan

Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.

=== or-signals pkpd bolus --plot ===
uv run or-signals pkpd --case 'data/sample/bolus.*' --plot
Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.

case: bolus
model: schnider-2cmt-effect-site
citation: Schnider et al., Anesthesiology 1998;88:1170-82 and 1999;90:1502-16 (2-compartment reduction: V3/CL3 omitted)
raw infusion peak at t=20s  value=960.0 mg/min
effect-site Ce peak at t=59s  value=3.921 µg/ml
diverged_after_bolus: True
recomputed Ce matches stored: True
Depth-index proxies are not awareness labels. Waveforms are synthetic.

infusion mg/min (*) vs Ce µg/ml (o); + marks overlap. Not a clinical plot.
         |                        ******                                       ooo
         |                                                               oooooo   
         |                                                          ooooo         
         |                                                     ooooo              
         |                                                ooooo                   
         |                                             ooo                        
         |                                         oooo                           
         |                                      ooo                               
         |                                  oooo                                  
         |                              oooo                                      
         |                           ooo                                          
         |++++++++++++++++++++++++ooo   ******************************************
         +------------------------------------------------------------------------
          0s                                                                  60s

Research tool only. Not a clinical monitor and not a medical device. Depth-index proxies are not awareness labels. This output is not clinical advice.
```

Then `make eval` for the operating-point table, SQI table, and
label-availability (pivot to over-sedation already decided). Recordings:

- `demo/01-inspect-signals.cast`
- `demo/02-artifact-rejection.cast`
- `demo/03-pkpd-divergence.cast`
- `demo/04-evaluation.cast`

## Layout

1. `docs/ARCHITECTURE.md` — contracts and CLI
2. `docs/phase-0/research-memo.md` — label pivot, SQI rules, PK/PD choice
3. `data/sample/README.md` — why each excerpt exists
4. `src/or_signals/sqi.py` — flush, damping, dropout; no interpolation
5. `src/or_signals/pkpd.py` — Schnider-style 2-compartment + effect site
6. `src/or_signals/inspect.py` / `score.py` — inventory and operating points
7. `research/phase0/` — the measurements

## Results

Regenerated by `make eval`. Baseline column is mandatory.

<!-- EVAL_TABLE_BEGIN -->

| Measurement | Result | Baseline |
| --- | --- | --- |
| Clean ABP usable fraction | 1.000 | treat all samples as usable |
| Artifact ABP usable fraction | 0.750 | treat flush as hypotension |
| Awareness labels (index) | 1/200 | assume labeled |
| Pivot to over-sedation | True | model awareness |
| corr(Ce, depth proxy) | 0.990 | corr(rate, proxy) -0.294 |
| Over-sedation Ce operating point | thr 0.5 TPR 1.000 | FPR 0.000 |

<!-- EVAL_TABLE_END -->

## 🏗️ Architecture & Event Topology

```mermaid
flowchart LR
    wave[ABP / SpO2 / BIS / rate] --> sqi[SQI flush dropout]
    sqi --> usable[usable windows]
    rate[infusion rate] --> pkpd[2-cmt + Ce]
    pkpd --> ce[effect-site conc]
    usable --> join[quality-gated features]
    ce --> join
    join --> score[over-sedation operating points]
```

`QualityReport.interpolated` is always false. Gaps are listed, not filled.

## ⚖️ Architecture Trade-offs & Pragmatic Decisions

| Chosen | Given up | What would change the answer |
| --- | --- | --- |
| Synthetic excerpts | VitalDB bytes in the demo | One license, plus a review that MIT redistribution is allowed (it is not confirmed today) |
| Pivot to over-sedation | Awareness classifier | A corpus with usable awareness labels above the §4.2 gate |
| 2-compartment Schnider + ke0 | Full 3-compartment Schnider | Bolus-peak error vs 3-cmt large enough to matter |
| numpy + JSON sidecar | `.vital` reader | Need for native VitalDB files |
| Rule SQI | Learned artifact model | Real-byte flush signatures the rules miss |
| ASCII / PPM plots | matplotlib | A display that needs a raster library |

## 🛡️ Edge Cases & Failure Modes

- Arterial flush (square ~300 mmHg) then damped 42 mmHg: reject, do not call hypotension.
- Long NaN dropout: report the gap, never interpolate; downstream window incomplete.
- Bolus: rate spikes and returns; Ce lags; depth proxy tracks Ce.
- `no-label`: no BIS, no awareness tag; excluded from training.
- BIS-like values are a Hill-of-Ce proxy, not recall of intraoperative awareness.
- Female LBM uses the James formula branch; samples use the male reference adult.

## Limitations

Not a monitor. Not a VitalDB redistributor. Not an awareness detector.
Arterial propofol concentrations are unmeasured. A live VitalDB label audit
is unmeasured.

## License and citation

MIT. Cite Schnider et al., Anesthesiology 1998;88:1170-1182 and 1999;90:1502-1516
for the PK/PD constants, Lee et al., Sci Data 2022;9:279 for VitalDB when
you use that corpus under its own terms, and this repository for the SQI
and research pipeline.
