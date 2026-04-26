/**
 * Fluex Wearable Safety System — Main Entry Point
 * Target: Adafruit Feather nRF52840
 *
 * Pipeline:
 *   IMU (ICM-42688) + PPG (MAX30102)
 *       → CNN inference (TFLite Micro, 140KB quantized)
 *       → Multi-modal emergency score
 *       → BLE GATT notification → Mobile app → Twilio SMS
 */

#include <Arduino.h>
#include "sensors/imu.h"
#include "sensors/heart_rate.h"
#include "ml/inference.h"
#include "comms/ble_protocol.h"
#include "utils/power_management.h"

// ─── Configuration ────────────────────────────────────────────────────────────
static constexpr uint32_t IMU_SAMPLE_INTERVAL_MS  = 20;   // 50 Hz
static constexpr uint32_t PPG_SAMPLE_INTERVAL_MS  = 20;   // 50 Hz
static constexpr uint32_t INFERENCE_WINDOW_SAMPLES = 400;  // 8 seconds
static constexpr float    ALERT_THRESHOLD          = 0.72f;

// ─── Global state ─────────────────────────────────────────────────────────────
static float     imuBuffer[INFERENCE_WINDOW_SAMPLES * 6]; // ax,ay,az,gx,gy,gz
static uint16_t  bufferIndex = 0;
static float     prevHeartRate = 70.0f;
static uint32_t  lastImuSample = 0;
static uint32_t  lastPpgSample = 0;
static bool      alertActive   = false;

// ─── Forward declarations ──────────────────────────────────────────────────────
float computeEmergencyScore(float fallConf, float hrBpm, float accelMag);
void  handleEmergency(float score);

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);

    PowerManager::init();
    BLEProtocol::init();

    if (!IMUSensor::init()) {
        Serial.println("[ERROR] IMU init failed");
        while (true) delay(1000);
    }

    if (!HeartRateSensor::init()) {
        Serial.println("[ERROR] PPG sensor init failed");
        // Non-fatal — continue without HR
    }

    if (!InferenceEngine::init()) {
        Serial.println("[ERROR] TFLite model init failed");
        while (true) delay(1000);
    }

    Serial.println("[FLUEX] System ready.");
}

// ─────────────────────────────────────────────────────────────────────────────
void loop() {
    uint32_t now = millis();

    // ── Sample IMU at 50 Hz ──
    if (now - lastImuSample >= IMU_SAMPLE_INTERVAL_MS) {
        lastImuSample = now;

        IMUData imu = IMUSensor::read();
        float* slot  = &imuBuffer[bufferIndex * 6];
        slot[0] = imu.ax;  slot[1] = imu.ay;  slot[2] = imu.az;
        slot[3] = imu.gx;  slot[4] = imu.gy;  slot[5] = imu.gz;
        bufferIndex++;

        // ── Run inference when window is full ──
        if (bufferIndex >= INFERENCE_WINDOW_SAMPLES) {
            bufferIndex = 0;

            float fallConf = InferenceEngine::runInference(imuBuffer,
                                INFERENCE_WINDOW_SAMPLES);

            float hrBpm    = HeartRateSensor::getLastBPM();
            float accelMag = sqrt(imu.ax * imu.ax +
                                  imu.ay * imu.ay +
                                  imu.az * imu.az);

            float score = computeEmergencyScore(fallConf, hrBpm, accelMag);

            // Publish metrics over BLE
            BLEProtocol::publishMetrics(fallConf, hrBpm, score);

            if (score > ALERT_THRESHOLD && !alertActive) {
                handleEmergency(score);
            }
        }
    }

    // ── Sample PPG continuously ──
    if (now - lastPpgSample >= PPG_SAMPLE_INTERVAL_MS) {
        lastPpgSample = now;
        HeartRateSensor::update();
    }

    // ── Handle BLE events ──
    BLEProtocol::poll();

    // ── Low-power idle ──
    PowerManager::idle();
}

// ─────────────────────────────────────────────────────────────────────────────
/**
 * Multi-modal emergency score fusion.
 *
 * score = 0.40 × fall_confidence
 *       + 0.35 × hr_anomaly      (±40 BPM spike from baseline)
 *       + 0.25 × immobility      (accel magnitude < 0.1 g)
 */
float computeEmergencyScore(float fallConf, float hrBpm, float accelMag) {
    float hrAnomaly  = min(1.0f, fabsf(hrBpm - prevHeartRate) / 40.0f);
    float immobility = (accelMag < 0.1f) ? 1.0f : 0.0f;

    prevHeartRate = hrBpm; // Update baseline

    return (0.40f * fallConf) +
           (0.35f * hrAnomaly) +
           (0.25f * immobility);
}

// ─────────────────────────────────────────────────────────────────────────────
void handleEmergency(float score) {
    alertActive = true;
    Serial.printf("[ALERT] Emergency score: %.2f — notifying app\n", score);

    BLEProtocol::sendEmergencyAlert(score);

    // Physical feedback
    digitalWrite(LED_RED, HIGH);
    tone(PIN_BUZZER, 880, 1000);

    // Cooldown: suppress re-alerts for 60 seconds
    delay(60000);
    alertActive = false;
    digitalWrite(LED_RED, LOW);
}
