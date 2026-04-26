/**
 * BLE Service — React Native companion app
 * Uses react-native-ble-plx to scan, connect, and receive notifications
 * from the Fluex nRF52840 GATT server.
 */

import { BleManager, State } from "react-native-ble-plx";
import { Buffer }             from "buffer";

const FLUEX_SVC_UUID     = "4C465558-0001-0000-0000-000000000000";
const METRICS_CHAR_UUID  = "4C465558-0001-0000-0000-000000000001";
const ALERT_CHAR_UUID    = "4C465558-0001-0000-0000-000000000002";

class BLEService {
    constructor() {
        this.manager     = new BleManager();
        this.device      = null;
        this.onMetrics   = null;  // Callback: (fallConf, hrBpm, score) => void
        this.onAlert     = null;  // Callback: (score, timestamp) => void
    }

    // ── Initialise & scan ─────────────────────────────────────────────────────
    async startScan(onDeviceFound) {
        const state = await this.manager.state();
        if (state !== State.PoweredOn) {
            throw new Error("Bluetooth is not enabled");
        }

        this.manager.startDeviceScan(
            [FLUEX_SVC_UUID],
            { allowDuplicates: false },
            (error, device) => {
                if (error) {
                    console.warn("[BLE] Scan error:", error.message);
                    return;
                }
                if (device?.name?.includes("Fluex")) {
                    this.manager.stopDeviceScan();
                    onDeviceFound(device);
                }
            }
        );
    }

    // ── Connect & subscribe ───────────────────────────────────────────────────
    async connect(device) {
        this.device = await device.connect();
        await this.device.discoverAllServicesAndCharacteristics();
        console.log("[BLE] Connected to", this.device.name);

        // Subscribe to metrics notifications
        this.device.monitorCharacteristicForService(
            FLUEX_SVC_UUID,
            METRICS_CHAR_UUID,
            (err, char) => {
                if (err || !char?.value) return;
                const raw = Buffer.from(char.value, "base64");
                const fallConf = raw.readFloatLE(0);
                const hrBpm    = raw.readFloatLE(4);
                const score    = raw.readFloatLE(8);
                this.onMetrics?.(fallConf, hrBpm, score);
            }
        );

        // Subscribe to alert notifications
        this.device.monitorCharacteristicForService(
            FLUEX_SVC_UUID,
            ALERT_CHAR_UUID,
            (err, char) => {
                if (err || !char?.value) return;
                const raw       = Buffer.from(char.value, "base64");
                const score     = raw.readFloatLE(0);
                const timestamp = raw.readUInt32LE(4);
                this.onAlert?.(score, timestamp);
            }
        );
    }

    disconnect() {
        this.device?.cancelConnection();
        this.device = null;
    }

    destroy() {
        this.manager.destroy();
    }
}

export default new BLEService();
