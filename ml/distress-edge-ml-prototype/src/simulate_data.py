import numpy as np
import pandas as pd

from .config import DAYS, N_USERS, RANDOM_SEED, SAMPLES_PER_DAY


def _clip(v, lo, hi):
    return max(lo, min(hi, v))


def generate_dataset(n_users: int = N_USERS, days: int = DAYS, samples_per_day: int = SAMPLES_PER_DAY) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []

    for user_id in range(n_users):
        base_hr = rng.normal(72, 8)
        base_hrv = rng.normal(38, 9)
        base_spo2 = rng.normal(97, 1.2)
        base_temp = rng.normal(33.5, 0.8)
        base_steps = rng.normal(78, 18)

        risk_factor = np.clip(rng.normal(0.5, 0.15), 0.1, 0.95)

        for day in range(days):
            for slot in range(samples_per_day):
                night = 1 if slot < 6 or slot > 21 else 0

                fall_g = _clip(rng.normal(1.2, 0.6) + risk_factor * 0.2, 0.1, 6.0)
                impact_duration_ms = _clip(rng.normal(80, 45) + fall_g * 22, 10, 500)
                gyro_spike_dps = _clip(rng.normal(120, 70) + fall_g * 90, 0, 1600)

                hr_bpm = _clip(base_hr + rng.normal(0, 10) + (night * -4), 38, 210)
                hrv_rmssd = _clip(base_hrv + rng.normal(0, 8), 5, 120)
                spo2 = _clip(base_spo2 + rng.normal(0, 1.1), 84, 100)
                skin_temp_c = _clip(base_temp + rng.normal(0, 1.2), 28, 40)

                immobility_min = _clip(abs(rng.normal(8 + night * 12, 10)), 0, 90)
                posture_change_count = _clip(abs(rng.normal(7 - night * 4, 3)), 0, 30)
                gps_speed_mps = _clip(abs(rng.normal(0.9, 1.1)), 0, 9)
                gps_jitter_m = _clip(abs(rng.normal(4.5, 3.5)), 0, 40)
                step_rate_spm = _clip(base_steps + rng.normal(0, 25) - (night * 25), 0, 190)

                distress_signal = (
                    0.32 * (fall_g > 2.4)
                    + 0.14 * (impact_duration_ms > 180)
                    + 0.11 * (gyro_spike_dps > 600)
                    + 0.18 * (hr_bpm > base_hr + 30 or hr_bpm < base_hr - 22)
                    + 0.07 * (hrv_rmssd < base_hrv - 16)
                    + 0.06 * (spo2 < 93)
                    + 0.08 * (immobility_min > 26)
                    + 0.04 * (posture_change_count < 2)
                    + 0.06 * (gps_speed_mps < 0.08 and immobility_min > 20)
                    + 0.05 * (night == 1)
                )

                probability = np.clip(
                    0.02 + distress_signal * (0.65 + risk_factor * 0.4) + rng.normal(0, 0.06),
                    0.0,
                    0.98,
                )
                distress = int(rng.random() < probability)

                rows.append(
                    {
                        "user_id": user_id,
                        "day": day,
                        "slot": slot,
                        "fall_g": fall_g,
                        "impact_duration_ms": impact_duration_ms,
                        "gyro_spike_dps": gyro_spike_dps,
                        "hr_bpm": hr_bpm,
                        "hrv_rmssd": hrv_rmssd,
                        "spo2": spo2,
                        "skin_temp_c": skin_temp_c,
                        "immobility_min": immobility_min,
                        "posture_change_count": posture_change_count,
                        "gps_speed_mps": gps_speed_mps,
                        "gps_jitter_m": gps_jitter_m,
                        "night_hour_flag": night,
                        "step_rate_spm": step_rate_spm,
                        "distress": distress,
                    }
                )

    return pd.DataFrame(rows)
