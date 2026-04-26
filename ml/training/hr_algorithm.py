"""
Fluex — PPG Heart Rate Algorithm (Python reference implementation)
-------------------------------------------------------------------
Estimates BPM from a MAX30102 PPG signal using a sliding 8-second window.
Motion artifact compensation via accelerometer correlation.

This is the reference Python version. The embedded C++ port lives in:
    firmware/src/sensors/heart_rate.cpp
"""

import numpy as np
from scipy import signal
from scipy.signal import butter, sosfilt, detrend


FS              = 50     # Hz — device sampling rate
WINDOW_SEC      = 8      # Window duration
WINDOW_SAMPLES  = FS * WINDOW_SEC   # 400 samples
HR_MIN_BPM      = 40
HR_MAX_BPM      = 180
HR_MIN_HZ       = HR_MIN_BPM / 60  # 0.67 Hz
HR_MAX_HZ       = HR_MAX_BPM / 60  # 3.0 Hz


# ─── Filters ──────────────────────────────────────────────────────────────────
def bandpass(sig: np.ndarray, lo: float = HR_MIN_HZ,
             hi: float = HR_MAX_HZ, fs: int = FS) -> np.ndarray:
    sos = butter(4, [lo, hi], btype="bandpass", fs=fs, output="sos")
    return sosfilt(sos, sig)


# ─────────────────────────────────────────────────────────────────────────────
def estimate_heart_rate(ppg_window: np.ndarray,
                        accel_window: np.ndarray | None = None) -> tuple[float, float]:
    """
    Estimate heart rate from a single 8-second PPG window.

    Args:
        ppg_window:   1D float array, length = WINDOW_SAMPLES
        accel_window: (3, WINDOW_SAMPLES) float array — optional, for motion
                      artifact rejection

    Returns:
        (hr_bpm, confidence) where confidence ∈ [0, 1]
    """
    # 1. Remove DC and bandpass
    ppg = detrend(ppg_window)
    ppg = bandpass(ppg)

    # 2. Hann window to reduce spectral leakage
    hann = np.hanning(len(ppg))
    ppg_windowed = ppg * hann

    # 3. FFT → frequency domain
    freqs    = np.fft.rfftfreq(len(ppg), d=1.0 / FS)
    fft_vals = np.abs(np.fft.rfft(ppg_windowed))

    # 4. Restrict to HR range
    valid_mask   = (freqs >= HR_MIN_HZ) & (freqs <= HR_MAX_HZ)
    valid_freqs  = freqs[valid_mask]
    valid_fft    = fft_vals[valid_mask]

    if len(valid_fft) == 0:
        return 70.0, 0.0

    peak_idx    = np.argmax(valid_fft)
    hr_hz       = valid_freqs[peak_idx]
    hr_bpm      = hr_hz * 60.0

    # 5. Confidence: spectral SNR (peak power vs. mean of rest)
    peak_power = valid_fft[peak_idx] ** 2
    mean_power = np.mean(valid_fft ** 2)
    snr        = peak_power / (mean_power + 1e-8)
    confidence = min(1.0, (snr - 1.0) / 10.0)  # Normalise; SNR>11 → 100%

    # 6. Motion artifact rejection
    if accel_window is not None:
        accel_mag = np.linalg.norm(accel_window, axis=0)
        accel_filt = bandpass(accel_mag)

        # If dominant accel freq matches HR candidate → likely artifact
        accel_fft  = np.abs(np.fft.rfft(accel_filt * hann))
        accel_peak_hz = freqs[np.argmax(accel_fft)]
        if abs(accel_peak_hz - hr_hz) < 0.1:  # Within 6 BPM
            confidence *= 0.4  # Penalise

    return float(hr_bpm), float(confidence)


# ─── Rolling estimator (streaming) ────────────────────────────────────────────
class RollingHREstimator:
    """Maintains a circular buffer; yields HR estimate every hop."""

    def __init__(self, hop_samples: int = 100):
        self.buffer    = np.zeros(WINDOW_SAMPLES, dtype=np.float32)
        self.accel_buf = np.zeros((3, WINDOW_SAMPLES), dtype=np.float32)
        self.idx       = 0
        self.full      = False
        self.hop       = hop_samples
        self.since_hop = 0
        self.last_hr   = 70.0
        self.last_conf = 0.0

    def update(self, ppg_sample: float, accel_xyz: tuple[float, float, float]) -> bool:
        self.buffer[self.idx]      = ppg_sample
        self.accel_buf[:, self.idx] = accel_xyz
        self.idx = (self.idx + 1) % WINDOW_SAMPLES

        if self.idx == 0:
            self.full = True

        self.since_hop += 1
        if self.full and self.since_hop >= self.hop:
            self.since_hop = 0
            # Re-order circular buffer
            ordered_ppg   = np.roll(self.buffer, -self.idx)
            ordered_accel = np.roll(self.accel_buf, -self.idx, axis=1)
            self.last_hr, self.last_conf = estimate_heart_rate(
                ordered_ppg, ordered_accel)
            return True
        return False

    @property
    def bpm(self) -> float:
        return self.last_hr

    @property
    def confidence(self) -> float:
        return self.last_conf


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Quick smoke test with synthetic 75 BPM signal
    t   = np.linspace(0, WINDOW_SEC, WINDOW_SAMPLES)
    ppg = np.sin(2 * np.pi * 1.25 * t) + 0.1 * np.random.randn(WINDOW_SAMPLES)

    hr, conf = estimate_heart_rate(ppg)
    print(f"Estimated: {hr:.1f} BPM  Confidence: {conf:.3f}")
    print(f"Expected:  75.0 BPM")
