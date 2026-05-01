from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

RANDOM_SEED = 42
N_USERS = 500
DAYS = 14
SAMPLES_PER_DAY = 24
WEEK1_DAYS = 7

FEATURES = [
    "fall_g",
    "impact_duration_ms",
    "gyro_spike_dps",
    "hr_bpm",
    "hrv_rmssd",
    "spo2",
    "skin_temp_c",
    "immobility_min",
    "posture_change_count",
    "gps_speed_mps",
    "gps_jitter_m",
    "night_hour_flag",
    "step_rate_spm",
]

TARGET = "distress"
