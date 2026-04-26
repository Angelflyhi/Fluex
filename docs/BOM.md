# Bill of Materials

| # | Component | Part Number | Qty | Unit Cost (USD) | Supplier |
|---|-----------|------------|-----|-----------------|----------|
| 1 | MCU Board | Adafruit Feather nRF52840 Express | 1 | $24.95 | Adafruit |
| 2 | IMU | ICM-42688-P (SparkFun Breakout) | 1 | $14.95 | SparkFun |
| 3 | PPG / SpO2 | MAX30102 breakout | 1 | $6.50 | Generic |
| 4 | LiPo Battery | 3.7V 400mAh (JST connector) | 1 | $6.95 | Adafruit |
| 5 | Passive Buzzer | 3.3V, 5mm | 1 | $0.50 | Generic |
| 6 | Push Button | 6mm tactile | 2 | $0.10 ea | Generic |
| 7 | LED (red) | 3mm, 2V | 1 | $0.05 | Generic |
| 8 | Resistors (220Ω) | 0805 SMD | 5 | $0.02 ea | Generic |
| 9 | Proto PCB | 5cm × 7cm | 1 | $1.50 | Generic |
| 10 | Wristband enclosure | 3D-printed PLA | 1 | ~$2.00 (filament) | DIY |

**Total BOM cost: ~$58**

---

## Wiring Summary

### ICM-42688-P (SPI)
| Signal | nRF52840 Pin |
|--------|-------------|
| MOSI   | D11 |
| MISO   | D12 |
| SCK    | D13 |
| CS     | D10 |
| INT1   | D9 |
| VDD    | 3.3V |
| GND    | GND |

### MAX30102 (I2C)
| Signal | nRF52840 Pin |
|--------|-------------|
| SDA    | SDA (D20) |
| SCL    | SCL (D21) |
| VIN    | 3.3V |
| GND    | GND |

### Buzzer
| Signal | nRF52840 Pin |
|--------|-------------|
| + | D5 (PWM) via 220Ω |
| – | GND |

### SOS Button
| Signal | nRF52840 Pin |
|--------|-------------|
| One side | D6 |
| Other side | GND (internal pull-up) |
