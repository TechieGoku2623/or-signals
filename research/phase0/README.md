# Phase 0 harnesses

`make research` runs these in order:

1. `data/sample/build.py` — rebuild the five synthetic excerpts and the 200-row index
2. `signal_quality/run.py` — usable fraction after artifact rejection
3. `label_availability/run.py` — awareness vs sedation-depth labels
4. `pkpd_validation/run.py` — effect-site concentration vs depth-index proxy
5. `render_docs.py` — write `docs/phase-0/research-memo.md`, `docs/EVALUATION.md`, and the measured tables in `README.md`

No number in the memo is typed by hand. If a quantity cannot be produced here, the memo says **unmeasured** and names the measurement that would settle it.
