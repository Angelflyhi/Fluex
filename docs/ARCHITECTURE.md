# Fluex — System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Fluex Wearable                          │
│                                                             │
│  ┌──────────┐   SPI    ┌───────────────┐                   │
│  │ICM-42688 │ ───────► │               │                   │
│  │  6-DOF   │          │  nRF52840     │   BLE 5.0         │
│  │  IMU     │   I2C    │  (ARM M4)     │ ──────────────►   │
│  ├──────────┤ ───────► │               │                   │
│  │MAX30102  │          │  TFLite Micro │                   │
│  │  PPG/HR  │          │  140KB model  │                   │
│  └──────────┘          └───────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              ↓ BLE GATT
┌─────────────────────────────────────────────────────────────┐
│                   Mobile App (React Native)                  │
│                                                             │
│   BLE GATT client → Redux state → Emergency dispatch        │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                 Backend (Node.js + Express)                  │
│                                                             │
│   POST /api/emergency/alert                                 │
│       ↓                          ↓                          │
│   MongoDB (event log)       Twilio SMS                      │
│                              (broadcast to contacts)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Detection Pipeline

### 1. Data Collection (50 Hz)
- ICM-42688-P provides 6-DOF IMU at 50 Hz via SPI
- MAX30102 PPG sampled at 50 Hz via I2C
- Data buffered in circular SRAM arrays

### 2. CNN Inference (every 8 seconds)
- 400 samples × 6 axes fed into TFLite Micro interpreter
- INT8 quantized model — 140KB, runs in ~35ms on M4 core
- Output: `[normal_confidence, fall_confidence, ADL_confidence]`

### 3. HR Estimation (continuous)
- 8-second sliding window of PPG samples
- Hann-windowed FFT → peak frequency in 0.7–3.0 Hz band
- BPM = peak_freq × 60
- Motion artifact rejection via accel correlation

### 4. Emergency Score Fusion

```
score = 0.40 × fall_confidence
      + 0.35 × hr_anomaly          # |ΔHR| / 40 BPM
      + 0.25 × immobility          # accel < 0.1g → 1.0

alert triggered when score > 0.72
```

### 5. BLE Notification
- Metrics characteristic notifies app every 8 seconds
- Alert characteristic fires immediately on threshold breach
- App dispatches POST to backend → Twilio SMS to all contacts

---

## Memory Budget (nRF52840)

| Region | Budget | Usage |
|--------|--------|-------|
| Flash (1MB) | 1024KB | Firmware ~400KB + Model ~140KB |
| RAM (256KB) | 256KB | IMU buffer 9.4KB + Tensor arena 40KB |
| BLE softdevice | ~100KB flash | Reserved |

---

## Power Budget

| Mode | Current | Duration | Energy |
|------|---------|----------|--------|
| Active sensing (50Hz) | ~8mA | Continuous | 8mAh/h |
| BLE connected + adv | ~4mA | Continuous | 4mAh/h |
| Inference (35ms burst) | +15mA | 35ms/8s | negligible |
| **Total avg** | **~12mA** | | |

With 400mAh LiPo → **~18 hours** estimated runtime.
