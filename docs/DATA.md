# Data

Phase 0 does **not** download VitalDB. Sample waveforms are synthetic and
match a VitalDB-like schema (ABP, SpO2, BIS-like depth proxy, infusion rate,
effect-site concentration). They are not patient recordings.

## VitalDB redistribution

Two official distributions disagree:

| Distribution | Terms | May we copy excerpts into this MIT repo? |
| --- | --- | --- |
| [PhysioNet vitaldb 1.0.0](https://www.physionet.org/content/vitaldb/1.0.0/) | [CC BY 4.0](https://www.physionet.org/content/vitaldb/view-license/1.0.0/) | Attribution-required reuse is allowed under CC BY, but relicensing the bytes as MIT is a poor fit and this repo does not include them. |
| [vitaldb.net open dataset](https://vitaldb.net/dataset/) | Site DUA + **CC BY-NC-SA 4.0** | ShareAlike / non-commercial terms conflict with MIT redistribution. |

Because the terms conflict, **excerpts are not confirmed as redistributable
here**. Phase 0 generates synthetic waveforms and says so plainly. Do not
start a VitalDB download in CI or in this environment.

## Committed objects

- `data/sample/{clean,artifact,dropout,bolus,no-label}.npz` + `.json` sidecars
- `data/sample/case_index.json` — 200-row synthetic label stand-in
- `data/sample/manifest.json` — demo-plan listing
- `data/sample/build.py` — generator, seed 0

Each excerpt is under 1 MB. No `.vital` reader is implemented.

License and quality notes continue in `docs/phase-0/research-memo.md` §3.
