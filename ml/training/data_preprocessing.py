"""
Fluex — FallAllD Dataset Preprocessing
---------------------------------------
Converts raw FallAllD CSV files into sliding-window numpy arrays
suitable for training the fall detection CNN.

FallAllD structure:
    data/<SubjectID>/<Activity>/<Sensor>.csv
    Activity codes: Fwd, Bwd, Lat, Right, Left, Syn, W, Jog, Sit, Std, ...

Output:
    X: float32 array of shape (N, WINDOW_SIZE, 6)
    y: int32 class labels [0=normal, 1=fall, 2=ADL]
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from scipy.signal import butter, sosfilt

# ─── Constants ────────────────────────────────────────────────────────────────
FS           = 50      # Hz — match device sampling rate
WINDOW_SIZE  = 400     # 8 seconds @ 50 Hz
STEP_SIZE    = 100     # 2-second hop (75% overlap)
FALL_CODES   = {"Fwd", "Bwd", "Lat", "Right", "Left", "Syn"}
ADL_CODES    = {"W", "Jog", "Sit", "Std", "Up", "Dn"}

CLASS_NORMAL = 0
CLASS_FALL   = 1
CLASS_ADL    = 2


# ─── Low-pass filter ──────────────────────────────────────────────────────────
def _lowpass(data: np.ndarray, cutoff: float = 20.0) -> np.ndarray:
    sos = butter(4, cutoff, fs=FS, output="sos")
    return sosfilt(sos, data, axis=0)


# ─────────────────────────────────────────────────────────────────────────────
def _load_csv(path: Path) -> np.ndarray | None:
    """Load a sensor CSV and return (N, 6) float array."""
    try:
        df = pd.read_csv(path, header=None)
        arr = df.values.astype(np.float32)
        if arr.shape[1] < 6:
            return None
        return arr[:, :6]  # ax, ay, az, gx, gy, gz
    except Exception:
        return None


def _windows(signal: np.ndarray, label: int):
    """Slide a window over signal, yield (window, label) pairs."""
    n = len(signal)
    for start in range(0, n - WINDOW_SIZE + 1, STEP_SIZE):
        yield signal[start : start + WINDOW_SIZE], label


# ─────────────────────────────────────────────────────────────────────────────
def load_fallalld_dataset(data_dir: str, test_size: float = 0.2):
    """
    Walk the FallAllD directory, extract windows, return train/val splits.

    Returns:
        X_train, X_val: (N, WINDOW_SIZE, 6) float32
        y_train, y_val: (N,) int32
    """
    root  = Path(data_dir)
    X_all = []
    y_all = []

    for subject_dir in sorted(root.iterdir()):
        if not subject_dir.is_dir():
            continue

        for activity_dir in subject_dir.iterdir():
            code = activity_dir.name.split("_")[0]

            if code in FALL_CODES:
                label = CLASS_FALL
            elif code in ADL_CODES:
                label = CLASS_ADL
            else:
                label = CLASS_NORMAL

            for csv_file in activity_dir.glob("*.csv"):
                signal = _load_csv(csv_file)
                if signal is None or len(signal) < WINDOW_SIZE:
                    continue

                signal = _lowpass(signal)

                # Normalise per-axis (zero mean, unit variance)
                signal = (signal - signal.mean(axis=0)) / (signal.std(axis=0) + 1e-8)

                for window, lbl in _windows(signal, label):
                    X_all.append(window)
                    y_all.append(lbl)

    X = np.array(X_all, dtype=np.float32)
    y = np.array(y_all, dtype=np.int32)

    print(f"[data] Total windows: {len(X)}")
    for cls, name in enumerate(["normal", "fall", "ADL"]):
        print(f"       {name}: {(y == cls).sum()}")

    return train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)


# ─────────────────────────────────────────────────────────────────────────────
def augment_data(X: np.ndarray, y: np.ndarray):
    """
    Simple augmentation for fall class (typically under-represented):
        - Gaussian noise injection
        - Time reversal
    """
    fall_mask = y == CLASS_FALL
    X_fall = X[fall_mask]
    y_fall = y[fall_mask]

    # Noise injection
    noise = np.random.normal(0, 0.02, X_fall.shape).astype(np.float32)
    X_aug = np.concatenate([X, X_fall + noise, X_fall[:, ::-1, :]], axis=0)
    y_aug = np.concatenate([y, y_fall, y_fall], axis=0)

    idx = np.random.permutation(len(X_aug))
    return X_aug[idx], y_aug[idx]
