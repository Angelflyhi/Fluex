"""
Fluex — Fall Detection CNN Training
Dataset: FallAllD (IEEE DataPort)

Trains a 1D CNN on 6-DOF IMU windows (8 sec @ 50 Hz = 400 samples × 6 axes).
Outputs a Keras model saved to ../model/fall_detection.h5

Classes:
    0 — Normal activity
    1 — Fall
    2 — ADL (Activities of Daily Living that resemble falls)

Usage:
    python train_cnn.py --data_dir ./data/FallAllD --epochs 40
"""

import argparse
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pathlib import Path
from data_preprocessing import load_fallalld_dataset, augment_data

# ─── Hyperparameters ──────────────────────────────────────────────────────────
WINDOW_SIZE    = 400    # samples
N_AXES         = 6      # ax, ay, az, gx, gy, gz
N_CLASSES      = 3
BATCH_SIZE     = 32
LEARNING_RATE  = 1e-3

# ─────────────────────────────────────────────────────────────────────────────
def build_model(window: int = WINDOW_SIZE, axes: int = N_AXES) -> keras.Model:
    """
    1D CNN designed to fit within 1MB flash on nRF52840.
    Quantized INT8 output is ~140KB.
    """
    inp = keras.Input(shape=(window, axes), name="imu_input")

    x = layers.Conv1D(32, kernel_size=3, activation="relu", padding="same")(inp)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2)(x)

    x = layers.Conv1D(64, kernel_size=3, activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(pool_size=2)(x)

    x = layers.Conv1D(64, kernel_size=3, activation="relu", padding="same")(x)
    x = layers.GlobalAveragePooling1D()(x)

    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(N_CLASSES, activation="softmax", name="class_probs")(x)

    model = keras.Model(inputs=inp, outputs=out)
    return model


def train(data_dir: str, output_dir: str, epochs: int) -> None:
    print(f"[train] Loading dataset from {data_dir} ...")
    X_train, X_val, y_train, y_val = load_fallalld_dataset(data_dir)

    # Data augmentation: jitter + time-shift
    X_train, y_train = augment_data(X_train, y_train)

    print(f"[train] Train: {X_train.shape}  Val: {X_val.shape}")

    model = build_model()
    model.summary()

    model.compile(
        optimizer=keras.optimizers.Adam(LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(
            patience=8, restore_best_weights=True, monitor="val_accuracy"
        ),
        keras.callbacks.ReduceLROnPlateau(
            factor=0.5, patience=4, min_lr=1e-5
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=f"{output_dir}/best_model.keras",
            save_best_only=True,
            monitor="val_accuracy",
        ),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
    )

    # Save final model
    out_path = Path(output_dir) / "fall_detection.h5"
    model.save(str(out_path))
    print(f"[train] Saved → {out_path}")

    val_acc = max(history.history["val_accuracy"])
    print(f"[train] Best val accuracy: {val_acc:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir",   default="./data/FallAllD")
    parser.add_argument("--output_dir", default="../model")
    parser.add_argument("--epochs",     type=int, default=40)
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    train(args.data_dir, args.output_dir, args.epochs)
