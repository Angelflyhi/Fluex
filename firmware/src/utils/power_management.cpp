/**
 * Power management for nRF52840
 *
 * Strategy:
 *   - WFE (wait-for-event) between IMU samples to keep CPU idle
 *   - Deep sleep after 5 minutes of no BLE connection
 *   - Wake on IMU INT1 (motion) or BLE advertisement response
 */

#include "power_management.h"
#include <nrfx_power.h>

static uint32_t lastActivityMs = 0;
static constexpr uint32_t SLEEP_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

namespace PowerManager {

void init() {
    // Configure DC/DC regulator for efficiency
    NRF_POWER->DCDCEN = 1;

    // Enable instruction cache
    NRF_NVMC->ICACHECNF = NVMC_ICACHECNF_CACHEEN_Enabled;

    lastActivityMs = millis();
    Serial.println("[PWR] DC-DC enabled, cache on");
}

void idle() {
    // Low-power wait: CPU halts until next interrupt (timer, SPI, etc.)
    __WFE();
    __SEV();
    __WFE();

    // Check for auto-sleep
    if (millis() - lastActivityMs > SLEEP_TIMEOUT_MS) {
        deepSleep();
    }
}

void deepSleep() {
    Serial.println("[PWR] Entering deep sleep");
    Serial.flush();

    // Disable SPI, I2C
    NRF_SPI0->ENABLE = 0;
    NRF_TWIM0->ENABLE = 0;

    // Enable wakeup on GPIO (IMU INT1)
    nrf_gpio_cfg_sense_input(9, NRF_GPIO_PIN_PULLUP, NRF_GPIO_PIN_SENSE_LOW);

    NRF_POWER->SYSTEMOFF = 1;
    __DSB();
    // Device resets on wakeup
}

} // namespace PowerManager
