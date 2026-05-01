from __future__ import annotations

import numpy as np
import pandas as pd
from ucimlrepo import fetch_ucirepo

from .config import FEATURES, RANDOM_SEED


def _derive_distress_from_motion(motion_score: pd.Series, p95: float, p80: float) -> pd.Series:
    # Heuristic pseudo-labeling on open activity streams:
    # upper-tail dynamics are treated as potential distress windows.
    return ((motion_score > p95) | ((motion_score > p80) & (np.random.rand(len(motion_score)) < 0.18))).astype(int)


def _map_agmp() -> pd.DataFrame:
    ds = fetch_ucirepo(id=755)  # Accelerometer Gyro Mobile Phone
    x = ds.data.features.copy()
    rng = np.random.default_rng(RANDOM_SEED)

    acc_norm = np.sqrt(x["accX"] ** 2 + x["accY"] ** 2 + x["accZ"] ** 2)
    gyro_norm = np.sqrt(x["gyroX"] ** 2 + x["gyroY"] ** 2 + x["gyroZ"] ** 2)

    motion_score = 0.7 * acc_norm + 0.3 * gyro_norm
    distress = _derive_distress_from_motion(motion_score, motion_score.quantile(0.95), motion_score.quantile(0.8))

    hr = 66 + acc_norm * 2.3 + rng.normal(0, 4, len(x))
    hrv = 62 - np.clip(acc_norm * 1.7, 0, 38) + rng.normal(0, 3, len(x))
    spo2 = 98 - np.clip(acc_norm * 0.3, 0, 8) + rng.normal(0, 0.5, len(x))

    df = pd.DataFrame(
        {
            "user_id": (np.arange(len(x)) // 128) % 120,
            "day": (np.arange(len(x)) // 24) % 14,
            "fall_g": np.clip(acc_norm / 4.0, 0.1, 6.0),
            "impact_duration_ms": np.clip(50 + acc_norm * 17, 10, 500),
            "gyro_spike_dps": np.clip(gyro_norm * 260, 0, 1600),
            "hr_bpm": np.clip(hr, 38, 210),
            "hrv_rmssd": np.clip(hrv, 5, 120),
            "spo2": np.clip(spo2, 85, 100),
            "skin_temp_c": np.clip(33.6 + rng.normal(0, 0.6, len(x)), 29, 40),
            "immobility_min": np.clip(16 - acc_norm + rng.normal(0, 2, len(x)), 0, 90),
            "posture_change_count": np.clip(acc_norm / 1.8 + rng.normal(0, 1.2, len(x)), 0, 30),
            "gps_speed_mps": np.clip(acc_norm / 3.8 + rng.normal(0, 0.25, len(x)), 0, 9),
            "gps_jitter_m": np.clip(3.5 + rng.normal(0, 1.1, len(x)), 0, 40),
            "night_hour_flag": (rng.random(len(x)) < 0.25).astype(int),
            "step_rate_spm": np.clip(acc_norm * 8 + rng.normal(0, 8, len(x)), 0, 190),
            "distress": distress,
            "dataset_source": "UCI-AGMP-755",
        }
    )
    return df


def _map_gait() -> pd.DataFrame:
    ds = fetch_ucirepo(id=760)  # Multivariate Gait Data
    x = ds.data.features.copy()
    rng = np.random.default_rng(RANDOM_SEED + 1)

    gait_var = x.groupby(["subject", "condition", "replication", "leg", "joint"])["angle"].transform("std").fillna(0.0)
    angle_abs = x["angle"].abs()
    motion_score = 0.55 * angle_abs + 0.45 * gait_var
    distress = _derive_distress_from_motion(motion_score, motion_score.quantile(0.985), motion_score.quantile(0.93))

    df = pd.DataFrame(
        {
            "user_id": x["subject"].astype(int),
            "day": (x["time"].astype(int) // 120) % 14,
            "fall_g": np.clip(angle_abs / 30.0 + gait_var / 18.0, 0.1, 6.0),
            "impact_duration_ms": np.clip(45 + gait_var * 18, 10, 500),
            "gyro_spike_dps": np.clip(angle_abs * 11 + gait_var * 9, 0, 1600),
            "hr_bpm": np.clip(70 + motion_score * 1.4 + rng.normal(0, 4, len(x)), 38, 210),
            "hrv_rmssd": np.clip(50 - motion_score * 0.7 + rng.normal(0, 4, len(x)), 5, 120),
            "spo2": np.clip(97 - motion_score * 0.06 + rng.normal(0, 0.5, len(x)), 85, 100),
            "skin_temp_c": np.clip(33.2 + rng.normal(0, 0.7, len(x)), 29, 40),
            "immobility_min": np.clip(22 - motion_score * 0.18 + rng.normal(0, 3, len(x)), 0, 90),
            "posture_change_count": np.clip(motion_score * 0.16 + rng.normal(0, 1.5, len(x)), 0, 30),
            "gps_speed_mps": np.clip(motion_score * 0.05 + rng.normal(0, 0.3, len(x)), 0, 9),
            "gps_jitter_m": np.clip(4.2 + rng.normal(0, 1.3, len(x)), 0, 40),
            "night_hour_flag": (rng.random(len(x)) < 0.27).astype(int),
            "step_rate_spm": np.clip(motion_score * 0.9 + rng.normal(0, 10, len(x)), 0, 190),
            "distress": distress,
            "dataset_source": "UCI-GAIT-760",
        }
    )
    return df


def _map_nhanes() -> pd.DataFrame:
    ds = fetch_ucirepo(id=887)  # NHANES subset
    x = ds.data.features.copy()
    rng = np.random.default_rng(RANDOM_SEED + 2)

    glucose = x["LBXGLU"].fillna(x["LBXGLU"].median())
    insulin = x["LBXIN"].fillna(x["LBXIN"].median())
    ogtt = x["LBXGLT"].fillna(x["LBXGLT"].median())
    bmi = x["BMXBMI"].fillna(x["BMXBMI"].median())
    active = x["PAQ605"].fillna(2.0)

    metabolic_risk = (
        0.35 * (glucose > 120).astype(float)
        + 0.20 * (insulin > 20).astype(float)
        + 0.20 * (ogtt > 160).astype(float)
        + 0.15 * (bmi > 32).astype(float)
        + 0.10 * (active == 2).astype(float)
    )
    distress = (metabolic_risk > 0.38).astype(int)

    df = pd.DataFrame(
        {
            "user_id": np.arange(len(x)),
            "day": np.arange(len(x)) % 14,
            "fall_g": np.clip(0.5 + rng.normal(0, 0.15, len(x)), 0.1, 6.0),
            "impact_duration_ms": np.clip(60 + rng.normal(0, 20, len(x)), 10, 500),
            "gyro_spike_dps": np.clip(130 + rng.normal(0, 40, len(x)), 0, 1600),
            "hr_bpm": np.clip(66 + (glucose - 90) * 0.35 + rng.normal(0, 5, len(x)), 38, 210),
            "hrv_rmssd": np.clip(52 - (insulin - 8) * 0.55 + rng.normal(0, 4, len(x)), 5, 120),
            "spo2": np.clip(97 - np.maximum(bmi - 24, 0) * 0.08 + rng.normal(0, 0.4, len(x)), 85, 100),
            "skin_temp_c": np.clip(33.4 + rng.normal(0, 0.5, len(x)), 29, 40),
            "immobility_min": np.clip(12 + (active == 2).astype(float) * 10 + rng.normal(0, 2, len(x)), 0, 90),
            "posture_change_count": np.clip(6 - (active == 2).astype(float) * 2 + rng.normal(0, 1, len(x)), 0, 30),
            "gps_speed_mps": np.clip(1.2 - (active == 2).astype(float) * 0.5 + rng.normal(0, 0.2, len(x)), 0, 9),
            "gps_jitter_m": np.clip(4 + rng.normal(0, 1, len(x)), 0, 40),
            "night_hour_flag": (rng.random(len(x)) < 0.28).astype(int),
            "step_rate_spm": np.clip(95 - (active == 2).astype(float) * 35 + rng.normal(0, 10, len(x)), 0, 190),
            "distress": distress,
            "dataset_source": "UCI-NHANES-887",
        }
    )
    return df


def build_open_dataset_training_frame(max_rows_per_dataset: int = 40000) -> pd.DataFrame:
    frames = [_map_agmp(), _map_gait(), _map_nhanes()]
    sampled = []
    for frame in frames:
        if len(frame) > max_rows_per_dataset:
            sampled.append(frame.sample(max_rows_per_dataset, random_state=RANDOM_SEED))
        else:
            sampled.append(frame)

    merged = pd.concat(sampled, ignore_index=True)
    merged = merged.dropna(subset=FEATURES + ["distress"])
    merged["distress"] = merged["distress"].astype(int)
    return merged
