#pragma once
#include <Arduino.h>

namespace BLEProtocol {
    void init();
    void poll();
    void publishMetrics(float fallConf, float hrBpm, float emergencyScore);
    void sendEmergencyAlert(float score);
}
