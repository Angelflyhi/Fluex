/**
 * IMU driver — ICM-42688-P via SPI
 *
 * Range config:
 *   Accelerometer : ±16 g
 *   Gyroscope     : ±2000 °/s
 *   Output rate   : 50 Hz
 */

#include "imu.h"
#include <SPI.h>

// ─── Pin mapping (Feather nRF52840) ──────────────────────────────────────────
static constexpr uint8_t PIN_IMU_CS   = 10;
static constexpr uint8_t PIN_IMU_INT1 = 9;

// ─── ICM-42688 register addresses ────────────────────────────────────────────
static constexpr uint8_t REG_WHO_AM_I      = 0x75;
static constexpr uint8_t REG_PWR_MGMT0     = 0x4E;
static constexpr uint8_t REG_ACCEL_CONFIG0 = 0x50;
static constexpr uint8_t REG_GYRO_CONFIG0  = 0x4F;
static constexpr uint8_t REG_ACCEL_DATA_X1 = 0x1F;

// ─── Scale factors ───────────────────────────────────────────────────────────
static constexpr float ACCEL_SCALE = 16.0f / 32768.0f;  // ±16g
static constexpr float GYRO_SCALE  = 2000.0f / 32768.0f; // ±2000°/s

static SPISettings icmSpiSettings(8000000, MSBFIRST, SPI_MODE0);

// ─────────────────────────────────────────────────────────────────────────────
static uint8_t icmReadReg(uint8_t reg) {
    SPI.beginTransaction(icmSpiSettings);
    digitalWrite(PIN_IMU_CS, LOW);
    SPI.transfer(reg | 0x80); // Read bit
    uint8_t val = SPI.transfer(0x00);
    digitalWrite(PIN_IMU_CS, HIGH);
    SPI.endTransaction();
    return val;
}

static void icmWriteReg(uint8_t reg, uint8_t val) {
    SPI.beginTransaction(icmSpiSettings);
    digitalWrite(PIN_IMU_CS, LOW);
    SPI.transfer(reg & 0x7F);
    SPI.transfer(val);
    digitalWrite(PIN_IMU_CS, HIGH);
    SPI.endTransaction();
}

// ─────────────────────────────────────────────────────────────────────────────
namespace IMUSensor {

bool init() {
    pinMode(PIN_IMU_CS, OUTPUT);
    digitalWrite(PIN_IMU_CS, HIGH);
    SPI.begin();

    delay(10);

    uint8_t whoami = icmReadReg(REG_WHO_AM_I);
    if (whoami != 0x47) { // ICM-42688-P device ID
        Serial.printf("[IMU] Unexpected WHO_AM_I: 0x%02X\n", whoami);
        return false;
    }

    // Enable accel + gyro in low-noise mode
    icmWriteReg(REG_PWR_MGMT0, 0x0F);
    delay(1);

    // Accel: ±16g, 50 Hz
    icmWriteReg(REG_ACCEL_CONFIG0, 0x06);

    // Gyro: ±2000°/s, 50 Hz
    icmWriteReg(REG_GYRO_CONFIG0, 0x06);

    Serial.println("[IMU] ICM-42688-P ready");
    return true;
}

IMUData read() {
    uint8_t raw[12];

    SPI.beginTransaction(icmSpiSettings);
    digitalWrite(PIN_IMU_CS, LOW);
    SPI.transfer(REG_ACCEL_DATA_X1 | 0x80);
    for (int i = 0; i < 12; i++) raw[i] = SPI.transfer(0x00);
    digitalWrite(PIN_IMU_CS, HIGH);
    SPI.endTransaction();

    auto toInt16 = [](uint8_t hi, uint8_t lo) -> int16_t {
        return (int16_t)((hi << 8) | lo);
    };

    IMUData d;
    d.ax = toInt16(raw[0],  raw[1])  * ACCEL_SCALE;
    d.ay = toInt16(raw[2],  raw[3])  * ACCEL_SCALE;
    d.az = toInt16(raw[4],  raw[5])  * ACCEL_SCALE;
    d.gx = toInt16(raw[6],  raw[7])  * GYRO_SCALE;
    d.gy = toInt16(raw[8],  raw[9])  * GYRO_SCALE;
    d.gz = toInt16(raw[10], raw[11]) * GYRO_SCALE;
    return d;
}

float getMagnitude() {
    IMUData d = read();
    return sqrt(d.ax * d.ax + d.ay * d.ay + d.az * d.az);
}

} // namespace IMUSensor
