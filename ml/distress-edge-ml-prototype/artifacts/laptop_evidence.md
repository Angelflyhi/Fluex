# Laptop Execution Evidence

- Generated at (UTC): 2026-04-27T04:10:39.726053+00:00
- Execution device: Laptop/PC (Python local runtime)
- Dataset sources: UCI-AGMP-755, UCI-GAIT-760, UCI-NHANES-887
- Total training rows: 74269
- ROC-AUC: 0.9662261700012337
- Personalized false positive rate: 0.03707392651615759
- Avg inference latency on laptop (ms/sample): 0.046

## Scenario Results

- normal_walk: prob=0.4281, score=0.0, trigger=False, latency_ms=58.721
- possible_fall_distress: prob=0.5437, score=1.0, trigger=True, latency_ms=33.916
- night_immobility_only: prob=0.1147, score=0.25, trigger=False, latency_ms=33.353