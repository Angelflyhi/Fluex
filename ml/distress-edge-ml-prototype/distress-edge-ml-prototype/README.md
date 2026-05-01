# Distress Edge ML Prototype (Week-1 Personalization)

Prototype pipeline for a smartwatch safety model that:
- learns a personal baseline in the first 7 days,
- detects distress/emergency events from multi-modal signals,
- runs all inference locally (edge-first design).

## What this prototype includes

- Open-source multi-dataset training (UCI repositories) + synthetic fallback
- 10+ distress signal channels (IMU, heart, GPS, context)
- Random Forest classifier (fast, low-memory inference profile)
- Week-1 personalization via user baseline calibration
- Emergency score fusion:
  - Fall: 40%
  - Heart-rate anomaly: 35%
  - Immobility: 25%
  - Alert when score > 0.72
- Export artifacts for firmware handoff (`artifacts/`)

## Project structure

- `src/config.py` - feature names and constants
- `src/open_data.py` - open-source dataset ingestion and feature harmonization
- `src/simulate_data.py` - synthetic sensor/event data generator
- `src/train.py` - train/evaluate/personalize and save artifacts
- `src/infer_demo.py` - load artifact and run local inference demo
- `requirements.txt` - Python dependencies

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.train
python -m src.infer_demo
python -m src.laptop_evidence
python -m src.local_demo
```

## One-command local demo

For hackathon stage/demo on a laptop:

```bash
demo.bat
```

This runs training and then evaluates a bundled local dataset at `data/demo_sensor_windows.csv`.

## Expected output

- `artifacts/model.joblib` - trained Random Forest model
- `artifacts/metrics.json` - global + personalized metrics
- `artifacts/edge_model.json` - compact tree parameter export
- `artifacts/laptop_evidence.json` - machine-readable laptop proof report
- `artifacts/laptop_evidence.md` - judge-friendly laptop demo proof
- `artifacts/demo_results.csv` - per-case local demo predictions
- `artifacts/demo_results.md` - local demo summary for judges
- `artifacts/demo_results.json` - local demo run metadata

## Open datasets used

This training pipeline consumes these open datasets:

1. **UCI Accelerometer Gyro Mobile Phone (`id=755`)**
   - Type: wearable smartphone IMU (accelerometer + gyroscope) time-series.
   - Used for: motion intensity, impact, rotational spike, locomotion proxies.

2. **UCI Multivariate Gait Data (`id=760`)**
   - Type: gait-joint angle multivariate time-series.
   - Used for: instability, posture-change behavior, abnormal movement windows.

3. **UCI NHANES Age Prediction Subset (`id=887`)**
   - Type: physiological/metabolic clinical variables.
   - Used for: heart/metabolic anomaly priors (HR/HRV/SpO2 proxy features).

The three sources are harmonized into one wearable feature schema:
`fall_g`, `impact_duration_ms`, `gyro_spike_dps`, `hr_bpm`, `hrv_rmssd`, `spo2`, `skin_temp_c`, `immobility_min`, `posture_change_count`, `gps_speed_mps`, `gps_jitter_m`, `night_hour_flag`, `step_rate_spm`.

## Hackathon pitch points

- Personal calibration reduces false alerts compared to fixed thresholds
- 100% local inference path (privacy-first, no cloud dependency)
- Emergency fusion logic is interpretable and clinician-auditable
- Compatible with nRF52840 deployment flow (tree export + C conversion)
