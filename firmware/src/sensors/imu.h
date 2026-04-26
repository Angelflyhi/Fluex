#pragma once
#include <Arduino.h>

struct IMUData {
    float ax, ay, az;   // Acceleration (g)
    float gx, gy, gz;   // Gyroscope (°/s)
};

namespace IMUSensor {
    bool    init();
    IMUData read();
    float   getMagnitude();
}
