#pragma once
#include <Arduino.h>

namespace InferenceEngine {
    /**
     * Load model from model.h and allocate tensor arena.
     * Must be called once in setup().
     * Returns false on allocation failure.
     */
    bool  init();

    /**
     * Run CNN inference on a flat buffer of IMU data.
     *
     * @param imuData   Pointer to float[samples * 6] (ax,ay,az,gx,gy,gz)
     * @param samples   Number of time steps (typically 400)
     * @return          Fall confidence score [0.0, 1.0]
     */
    float runInference(const float* imuData, int samples);
}
