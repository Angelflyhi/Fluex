/**
 * BLE GATT server — Fluex Safety Service
 *
 * Service UUID:       4C46-5558-0001-0000-0000-000000000000  (FLUEX)
 * Characteristics:
 *   METRICS_CHAR:     Notify — {fall_conf: f32, hr_bpm: f32, score: f32}
 *   ALERT_CHAR:       Notify — {score: f32, timestamp: u32}
 *   CONTACTS_CHAR:    Write  — JSON array of phone numbers
 */

#include "ble_protocol.h"
#include <bluefruit.h>
#include <ArduinoJson.h>

// ─── UUIDs ───────────────────────────────────────────────────────────────────
static const uint8_t FLUEX_SVC_UUID[] = {
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x01,0x00,0x58,0x55,0x46,0x4C
};
static const uint8_t METRICS_CHAR_UUID[] = {
    0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x01,0x00,0x58,0x55,0x46,0x4C
};
static const uint8_t ALERT_CHAR_UUID[] = {
    0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x01,0x00,0x58,0x55,0x46,0x4C
};

static BLEService        fluexService(FLUEX_SVC_UUID);
static BLECharacteristic metricsChar(METRICS_CHAR_UUID);
static BLECharacteristic alertChar(ALERT_CHAR_UUID);

struct MetricsPacket {
    float fallConf;
    float hrBpm;
    float score;
} __attribute__((packed));

struct AlertPacket {
    float    score;
    uint32_t timestamp;
} __attribute__((packed));

// ─────────────────────────────────────────────────────────────────────────────
static void connectCallback(uint16_t connHandle) {
    BLEConnection* conn = Bluefruit.Connection(connHandle);
    char central[32];
    conn->getPeerName(central, sizeof(central));
    Serial.printf("[BLE] Connected: %s\n", central);
}

static void disconnectCallback(uint16_t connHandle, uint8_t reason) {
    (void)connHandle; (void)reason;
    Serial.println("[BLE] Disconnected — restarting advertising");
    Bluefruit.Advertising.start(0);
}

// ─────────────────────────────────────────────────────────────────────────────
namespace BLEProtocol {

void init() {
    Bluefruit.begin();
    Bluefruit.setName("Fluex-Safety");
    Bluefruit.setTxPower(4);

    Bluefruit.Periph.setConnectCallback(connectCallback);
    Bluefruit.Periph.setDisconnectCallback(disconnectCallback);

    fluexService.begin();

    // Metrics characteristic — notify only
    metricsChar.setProperties(CHR_PROPS_NOTIFY);
    metricsChar.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
    metricsChar.setFixedLen(sizeof(MetricsPacket));
    metricsChar.begin();

    // Alert characteristic — notify only
    alertChar.setProperties(CHR_PROPS_NOTIFY);
    alertChar.setPermission(SECMODE_OPEN, SECMODE_NO_ACCESS);
    alertChar.setFixedLen(sizeof(AlertPacket));
    alertChar.begin();

    // Advertise
    Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
    Bluefruit.Advertising.addTxPower();
    Bluefruit.Advertising.addService(fluexService);
    Bluefruit.ScanResponse.addName();
    Bluefruit.Advertising.restartOnDisconnect(true);
    Bluefruit.Advertising.setInterval(32, 244); // fast→slow
    Bluefruit.Advertising.setFastTimeout(30);
    Bluefruit.Advertising.start(0);

    Serial.println("[BLE] Advertising as 'Fluex-Safety'");
}

void poll() {
    // Bluefruit handles events via callbacks — no polling needed.
    // Kept for extensibility (e.g., future command processing).
}

void publishMetrics(float fallConf, float hrBpm, float emergencyScore) {
    if (!Bluefruit.connected()) return;

    MetricsPacket pkt = { fallConf, hrBpm, emergencyScore };
    metricsChar.notify((uint8_t*)&pkt, sizeof(pkt));
}

void sendEmergencyAlert(float score) {
    if (!Bluefruit.connected()) return;

    AlertPacket pkt = { score, (uint32_t)(millis() / 1000) };
    alertChar.notify((uint8_t*)&pkt, sizeof(pkt));
}

} // namespace BLEProtocol
