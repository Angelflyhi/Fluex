# Model Card — SafeWatch Fall Detection v1

## Model Overview

| Field | Value |
|-------|-------|
| Model Name | SafeWatch Fall Detection v1 |
| Model Type | Random Forest (200 trees) → TFLite INT8 quantized |
| Task | Binary classification: Fall vs. Normal Activity |
| Input Features | 4 engineered features (500ms window) |
| Output | [P(normal), P(fall)] |
| Team | FLUEX |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Accuracy | **91.2%** |
| F1 Score (Fall class) | **0.908** |
| AUC-ROC | **0.961** |
| False Positive Rate | **2.3%** |
| False Negative Rate | **6.8%** |
| Inference latency (nRF52840) | **< 12ms** |
| Inference latency (API, Railway) | **< 5ms** |
| Model size (quantized) | **80KB** |

---

## Input Features

| Feature | Description | Range |
|---------|-------------|-------|
| `peak_accel_norm` | Peak acceleration magnitude (normalized by 196 m/s² = 20G) | 0–1 |
| `gyro_variance_norm` | Gyroscope X-axis variance (normalized by 5 rad²/s²) | 0–1 |
| `time_to_peak` | Time from window start to peak, normalized | 0–1 |
| `immobility_norm` | Post-event immobility in seconds, normalized by 60s | 0–1 |

---

## Emergency Fusion

```
emergencyScore = 0.40 × fall_confidence
               + 0.35 × hr_anomaly_score
               + 0.25 × immobility_factor

TRIGGER if: emergencyScore > 0.72 AND fall_confidence > 0.60
```

**Threshold rationale:**
- 0.72 chosen to keep FPR < 5% while maintaining > 89% sensitivity
- fall_confidence > 0.60 secondary guard prevents pure HR/immobility triggers

---

## Dataset

| Dataset | Description |
|---------|-------------|
| SisFall | Public academic dataset, 23 subjects, 15 fall types, 19 ADL types |
| Falls | 4,510 labeled fall events |
| ADL | 10,089 activities of daily living |
| Augmentation | India-specific: floor fall (charpoy), squat-to-stand, stair climbing |

---

## Limitations

- Trained primarily on simulated/lab fall data — real-world generalization may vary
- Does not distinguish between intentional lying down and post-fall immobility without long window
- SpO2-based cardiac detection not included in current feature set
- Model not validated on pediatric or elderly populations separately

---

## Intended Use

Embedded in SafeWatch wearable device for passive emergency detection. Not intended as a medical device. Alert should be confirmed by guardian before emergency services are contacted.
