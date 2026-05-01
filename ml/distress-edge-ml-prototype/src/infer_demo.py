import json

import joblib
import numpy as np

from .config import ARTIFACT_DIR, FEATURES


def run_demo():
    model = joblib.load(ARTIFACT_DIR / "model.joblib")
    metrics = json.loads((ARTIFACT_DIR / "metrics.json").read_text(encoding="utf-8"))
    edge = json.loads((ARTIFACT_DIR / "edge_model.json").read_text(encoding="utf-8"))

    sample = np.array(
        [
            [
                2.8,   # fall_g
                240,   # impact_duration_ms
                880,   # gyro_spike_dps
                142,   # hr_bpm
                18,    # hrv_rmssd
                92,    # spo2
                34.1,  # skin_temp_c
                34,    # immobility_min
                1,     # posture_change_count
                0.04,  # gps_speed_mps
                8.2,   # gps_jitter_m
                1,     # night_hour_flag
                5,     # step_rate_spm
            ]
        ]
    )

    prob = float(model.predict_proba(sample)[0, 1])
    print("Feature order:", FEATURES)
    print(f"Distress probability: {prob:.4f}")
    print("Personalized FPR:", metrics["personalized_week1_thresholds"]["false_positive_rate"])
    print("Exported trees:", len(edge["estimators"]))


if __name__ == "__main__":
    run_demo()
