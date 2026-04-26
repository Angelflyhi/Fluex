#pragma once
#include <Arduino.h>

namespace HeartRateSensor {
    bool  init();
    void  update();              // Call at 50 Hz in main loop
    float getLastBPM();
    float getSpO2();
    bool  isFingerDetected();
}
