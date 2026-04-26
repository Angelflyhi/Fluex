# Fluex — Smart Wearable Safety System

A multi-modal wearable safety device that detects falls and physiological emergencies in real time, then automatically broadcasts alerts to emergency contacts via BLE + SMS.

---

## Overview

Fluex combines an on-device convolutional neural network (TensorFlow Lite Micro), PPG-based heart rate monitoring, and IMU-derived immobility scoring into a unified emergency detection pipeline. All inference runs locally on an nRF52840 microcontroller — no cloud dependency for detection.

```
IMU (6-DOF) ──┐
               ├──► CNN Inference  ──┐
PPG Sensor ───┤                      ├──► Emergency Score ──► BLE ──► App ──► SMS
               └──► HR Algorithm ───┘
ICM-42688 ────┘   ──► Immobility ───┘
```

---

## Repository Structure

```
fluex/
├── firmware/               # nRF52840 C++ firmware (PlatformIO)
│   ├── src/
│   │   ├── main.cpp
│   │   ├── sensors/
│   │   │   ├── imu.cpp / imu.h          # ICM-42688 driver
│   │   │   ├── heart_rate.cpp / .h      # MAX30102 PPG + HR estimation
│   │   │   └── gps.cpp / .h             # Optional GPS module
│   │   ├── ml/
│   │   │   ├── inference.cpp / .h       # TFLite Micro inference engine
│   │   │   └── model.h                  # Quantized model (140KB TFLite)
│   │   ├── comms/
│   │   │   └── ble_protocol.cpp / .h    # BLE GATT service
│   │   └── utils/
│   │       └── power_management.cpp     # Sleep / wake logic
│   └── platformio.ini
│
├── ml/                     # Model training + inference server
│   ├── training/
│   │   ├── data_preprocessing.py        # FallAllD dataset pipeline
│   │   ├── train_cnn.py                 # Keras CNN training
│   │   ├── quantize_export.py           # TFLite quantization + .h export
│   │   └── hr_algorithm.py             # PPG heart rate algorithm (Python)
│   ├── inference_api/
│   │   ├── main.py                      # FastAPI inference server
│   │   └── requirements.txt
│   └── notebooks/
│       └── fall_detection.ipynb         # Colab-ready training notebook
│
├── mobile-app/             # React Native companion app
│   ├── src/
│   │   ├── screens/
│   │   │   └── HomeScreen.js
│   │   ├── services/
│   │   │   └── BLEService.js            # BLE scan + GATT client
│   │   └── redux/
│   │       ├── store.js
│   │       ├── emergencySlice.js
│   │       └── userSlice.js
│   └── package.json
│
├── backend/                # Node.js alert dispatch server
│   ├── routes/
│   │   ├── emergency.js                 # Twilio SMS broadcast
│   │   └── auth.js
│   ├── models/
│   │   ├── User.js
│   │   └── Emergency.js
│   ├── middleware/
│   └── index.js
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BLE_PROTOCOL.md
│   ├── API_SPEC.md
│   └── BOM.md
│
└── website/                # Demo landing page (Vite + React)
```

---

## Hardware

| Component | Part | Notes |
|-----------|------|-------|
| MCU | nRF52840 (Adafruit Feather) | ARM Cortex-M4, 1MB flash, BLE 5.0 |
| IMU | ICM-42688-P | 6-DOF, SPI, ±16g / ±2000°/s |
| PPG | MAX30102 | IR + Red LED, I2C |
| GPS | L76K | UART, optional |
| Battery | LiPo 400mAh | ~18h operation |
| Buzzer | Passive 3.3V | Alert feedback |

---

## ML Model

- **Architecture:** 1D CNN (Conv1D × 2 → Dense × 1)
- **Input:** 400 samples × 6 axes (8 seconds @ 50Hz)
- **Classes:** `[normal, fall, ADL]`
- **Size:** ~140KB quantized TFLite
- **Training data:** FallAllD dataset (60+ subjects, 6 fall types)

### Emergency Score Fusion

```
score = 0.40 × fall_confidence
      + 0.35 × hr_anomaly
      + 0.25 × immobility

alert if score > 0.72
```

---

## Setup

### Firmware

```bash
# Install PlatformIO CLI
pip install platformio

cd firmware
pio run --target upload
```

### ML Training

```bash
cd ml/training
pip install -r requirements.txt
python train_cnn.py          # Outputs model.tflite
python quantize_export.py    # Outputs firmware/src/ml/model.h
```

### Backend

```bash
cd backend
npm install
cp .env.example .env         # Fill in Twilio credentials
node index.js
```

### Mobile App

```bash
cd mobile-app
npm install
npx expo start
```

---

## Team

**Team FLUEX**

---

## License

MIT
