"""
SafeWatch — Women's Safety Threat Detection API
Team FLUEX

Detects: assault, grab attacks, being followed/cornered, panic states.
5-feature neural network (5->16->8->2), pure Python, no frameworks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import math, json, time, os

app = FastAPI(
    title="SafeWatch Women's Safety API",
    description=(
        "Real-time threat detection for women's personal safety. Team FLUEX. "
        "Detects assault, grab attacks, being followed, and panic states."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ─── Neural Network Inference (pure Python) ───────────────────────────────────

def relu(x): return max(0.0, x)

def softmax(v):
    m = max(v)
    ev = [math.exp(x - m) for x in v]
    s = sum(ev)
    return [e / s for e in ev]

def nn_predict(x, W1, b1, W2, b2, W3, b3):
    h1  = [relu(sum(W1[i][j]*x[j] for j in range(len(x))) + b1[i]) for i in range(len(W1))]
    h2  = [relu(sum(W2[i][j]*h1[j] for j in range(len(h1))) + b2[i]) for i in range(len(W2))]
    z3  = [sum(W3[i][j]*h2[j] for j in range(len(h2))) + b3[i] for i in range(len(W3))]
    return softmax(z3)[1]  # P(threat)

# ─── Load Trained Weights ──────────────────────────────────────────────────────

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "weights.json")
W1=W2=W3=b1=b2=b3=None
META = {}

def load_model():
    global W1,b1,W2,b2,W3,b3,META
    if not os.path.exists(MODEL_PATH):
        print(f"[WARN] weights.json not found — using rule-based fallback")
        return False
    with open(MODEL_PATH) as f:
        d = json.load(f)
    w = d["weights"]
    W1,b1 = w["W1"],w["b1"]
    W2,b2 = w["W2"],w["b2"]
    W3,b3 = w["W3"],w["b3"]
    META = {k:v for k,v in d.items() if k!="weights"}
    print(f"[ML] Loaded women's safety model — accuracy: {d.get('accuracy','?')}")
    return True

USING_NN = load_model()

# ─── Rule-Based Fallback ───────────────────────────────────────────────────────

def rule_threat_score(impact, erratic, hr_panic, sos, duration):
    score = 0.0
    if impact > 0.65:       score += 0.30
    elif impact > 0.40:     score += 0.12
    if erratic > 0.70 and impact > 0.40: score += 0.25
    elif erratic > 0.50:                  score += 0.10
    if hr_panic > 0.60:     score += 0.25
    elif hr_panic > 0.35:   score += 0.10
    if sos >= 0.5:           score += 0.40  # SOS is a hard signal
    if duration > 0.50:     score += 0.10
    return min(max(score, 0.0), 1.0)

def threat_score(impact, erratic, hr_panic, sos, duration):
    if USING_NN:
        return nn_predict([impact, erratic, hr_panic, sos, duration], W1,b1,W2,b2,W3,b3)
    return rule_threat_score(impact, erratic, hr_panic, sos, duration)

def hr_panic_score(hr, baseline):
    """How much above baseline? Running is expected; fear spike is different."""
    if hr < baseline:
        return 0.0  # bradycardia from calm
    delta = hr - baseline
    return min(delta / 60.0, 1.0)  # 60bpm above baseline = max panic

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class SimpleThreatPayload(BaseModel):
    """Demo UI payload — scalar features."""
    impact_g:           float = Field(default=1.0,  ge=0, le=20,  description="Peak impact in G-force")
    motion_erratic:     float = Field(default=0.1,  ge=0, le=1.0, description="Motion erratic score 0-1")
    heart_rate:         float = Field(default=72.0, ge=0, le=220)
    hr_baseline:        float = Field(default=72.0, ge=0, le=120)
    sos_pressed:        bool  = Field(default=False, description="Manual SOS button")
    duration_seconds:   float = Field(default=0.0,  ge=0, le=300, description="Threat event duration")

class SensorPayload(BaseModel):
    """Full sensor array payload from device."""
    accel_x: List[float]
    accel_y: List[float]
    accel_z: List[float]
    gyro_x:  List[float] = Field(default_factory=lambda: [0.0]*50)
    heart_rate:       float = Field(default=72.0)
    hr_baseline:      float = Field(default=72.0)
    sos_pressed:      bool  = Field(default=False)
    duration_seconds: float = Field(default=0.0)

class ThreatResult(BaseModel):
    threat_confidence:  float
    hr_panic_score:     float
    motion_chaos_score: float
    sos_active:         bool
    emergency_score:    float
    trigger_alert:      bool
    latency_ms:         float
    model_used:         str

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/infer/simple", response_model=ThreatResult, tags=["Inference"])
async def infer_simple(payload: SimpleThreatPayload):
    """Demo UI inference — scalar inputs, instant response."""
    start = time.perf_counter()

    impact_norm   = min(payload.impact_g / 15.0, 1.0)
    erratic_norm  = min(payload.motion_erratic, 1.0)
    hr_panic      = hr_panic_score(payload.heart_rate, payload.hr_baseline)
    sos           = 1.0 if payload.sos_pressed else 0.0
    duration_norm = min(payload.duration_seconds / 120.0, 1.0)

    score = threat_score(impact_norm, erratic_norm, hr_panic, sos, duration_norm)

    # Fusion weights
    emergency = (0.35 * score + 0.30 * hr_panic + 0.20 * erratic_norm
                 + 0.15 * duration_norm)
    if sos: emergency = max(emergency, 0.85)  # SOS always triggers

    return ThreatResult(
        threat_confidence=round(score, 4),
        hr_panic_score=round(hr_panic, 4),
        motion_chaos_score=round(erratic_norm, 4),
        sos_active=payload.sos_pressed,
        emergency_score=round(emergency, 4),
        trigger_alert=(emergency > 0.72 and (score > 0.60 or sos)),
        latency_ms=round((time.perf_counter() - start) * 1000, 2),
        model_used="neural-net-5x16x8x2" if USING_NN else "rule-based"
    )

@app.post("/infer", response_model=ThreatResult, tags=["Inference"])
async def infer(payload: SensorPayload):
    """Full inference from raw sensor arrays."""
    start = time.perf_counter()

    ax, ay, az = payload.accel_x, payload.accel_y, payload.accel_z
    mags = [math.sqrt(ax[i]**2 + ay[i]**2 + az[i]**2) for i in range(len(ax))]
    peak = max(mags) if mags else 9.81

    # Erratic score: variance of magnitude (rhythmic=low, struggling=high)
    mean_m = sum(mags) / max(len(mags), 1)
    var_m  = sum((v - mean_m)**2 for v in mags) / max(len(mags), 1)

    impact_norm   = min(peak / 147.0, 1.0)   # 15G max
    erratic_norm  = min(var_m / 20.0, 1.0)
    hr_panic      = hr_panic_score(payload.heart_rate, payload.hr_baseline)
    sos           = 1.0 if payload.sos_pressed else 0.0
    duration_norm = min(payload.duration_seconds / 120.0, 1.0)

    score = threat_score(impact_norm, erratic_norm, hr_panic, sos, duration_norm)
    emergency = 0.35*score + 0.30*hr_panic + 0.20*erratic_norm + 0.15*duration_norm
    if sos: emergency = max(emergency, 0.85)

    return ThreatResult(
        threat_confidence=round(score, 4),
        hr_panic_score=round(hr_panic, 4),
        motion_chaos_score=round(erratic_norm, 4),
        sos_active=payload.sos_pressed,
        emergency_score=round(emergency, 4),
        trigger_alert=(emergency > 0.72 and (score > 0.60 or sos)),
        latency_ms=round((time.perf_counter() - start) * 1000, 2),
        model_used="neural-net-5x16x8x2" if USING_NN else "rule-based"
    )

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "model_loaded": USING_NN, "team": "FLUEX", "version": "2.0.0"}

@app.get("/model-card", tags=["System"])
async def model_card():
    return {
        "model_name": "SafeWatch Women's Safety Threat Detector v2",
        "task": "Detect assault, grab attacks, being followed, panic states",
        "model_type": "5->16->8->2 Neural Network (ReLU, Softmax)",
        "input_features": 5,
        "features": ["impact_norm", "erratic_norm", "hr_panic_norm", "sos_active", "duration_norm"],
        "classes": ["safe", "threat"],
        "trigger_threshold": 0.72,
        "sos_override": "SOS button always triggers regardless of score",
        "team": "FLUEX",
        **META
    }

@app.get("/", tags=["System"])
async def root():
    return {"message": "SafeWatch Women's Safety API v2 — Team FLUEX", "docs": "/docs"}
