#pragma once
#include <Arduino.h>

namespace PowerManager {
    void init();
    void idle();        // Call at end of each loop() to yield CPU
    void deepSleep();   // Suspend until BLE or IMU interrupt
}
