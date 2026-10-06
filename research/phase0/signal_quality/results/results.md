# signal_quality results

SQI rejects flush/damping and reports dropout gaps without interpolation. The 42 mmHg damped plateau is not labeled hypotension on usable samples.

| case | ABP usable | SpO2 usable | raw hypo | usable hypo |
| --- | --- | --- | --- | --- |
| artifact | 0.750 | 1.000 | True | False |
| bolus | 1.000 | 1.000 | False | False |
| clean | 1.000 | 1.000 | False | False |
| dropout | 0.667 | 0.667 | False | False |
| no-label | 1.000 | 0.967 | False | False |
