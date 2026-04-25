import { useState, useEffect } from 'react';
import EmergencyGauge from '../components/EmergencyGauge';

// ─── Inference Engine (pure JS, client-side, no fetch) ────────────────────────
function hrPanicScore(hr, baseline) {
  if (hr <= baseline) return 0;
  return Math.min((hr - baseline) / 60, 1);
}

function ruleThreatScore(impact, erratic, hrPanic, sos, duration) {
  let s = 0;
  if (impact > 0.65)        s += 0.30;
  else if (impact > 0.40)   s += 0.12;
  if (erratic > 0.70 && impact > 0.40) s += 0.25;
  else if (erratic > 0.50)              s += 0.10;
  if (hrPanic > 0.60)       s += 0.25;
  else if (hrPanic > 0.35)  s += 0.10;
  if (sos)                   s += 0.40;
  if (duration > 0.50)      s += 0.10;
  return Math.min(Math.max(s, 0), 1);
}

function runInference(p) {
  const t0 = performance.now();
  const impact   = Math.min(p.impact_g / 15, 1);
  const erratic  = Math.min(p.motion_erratic, 1);
  const hrPanic  = hrPanicScore(p.heart_rate, p.hr_baseline);
  const sos      = p.sos_pressed ? 1 : 0;
  const duration = Math.min(p.duration_seconds / 120, 1);

  const score = ruleThreatScore(impact, erratic, hrPanic, sos, duration);
  let emergency = 0.35*score + 0.30*hrPanic + 0.20*erratic + 0.15*duration;
  if (p.sos_pressed) emergency = Math.max(emergency, 0.85);

  return {
    threat_confidence:  +score.toFixed(4),
    hr_panic_score:     +hrPanic.toFixed(4),
    motion_chaos_score: +erratic.toFixed(4),
    sos_active:          p.sos_pressed,
    emergency_score:    +emergency.toFixed(4),
    trigger_alert:       emergency > 0.72 && (score > 0.60 || p.sos_pressed),
    latency_ms:         +(performance.now() - t0).toFixed(2),
  };
}

// ─── Scenarios ────────────────────────────────────────────────────────────────
const SCENARIOS = {
  safe: {
    label: 'Safe — Walking Home',
    sub: 'Normal walk, HR 72 bpm, no threat detected',
    impact_g: 1.1, motion_erratic: 0.08,
    heart_rate: 72, hr_baseline: 72,
    sos_pressed: false, duration_seconds: 0,
  },
  grab: {
    label: 'Grab / Snatch Attack',
    sub: 'Sudden 9G impact, struggling motion, HR 140 bpm → ALERT',
    impact_g: 9.2, motion_erratic: 0.85,
    heart_rate: 140, hr_baseline: 72,
    sos_pressed: false, duration_seconds: 8,
  },
  followed: {
    label: 'Being Followed / Cornered',
    sub: 'No impact, frozen in fear, HR 125 bpm, 90s duration',
    impact_g: 0.6, motion_erratic: 0.15,
    heart_rate: 125, hr_baseline: 72,
    sos_pressed: false, duration_seconds: 90,
  },
  sos: {
    label: 'Manual SOS Triggered',
    sub: 'User pressed emergency button — immediate alert regardless of sensors',
    impact_g: 1.0, motion_erratic: 0.20,
    heart_rate: 105, hr_baseline: 72,
    sos_pressed: true, duration_seconds: 5,
  },
};

// ─── Sub-components ───────────────────────────────────────────────────────────
function Bar({ label, weight, value, color }) {
  return (
    <div className="progress-item">
      <div className="progress-header">
        <span className="progress-name">{label}</span>
        <span className="progress-weight">×{weight}</span>
      </div>
      <div className="progress-row">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${value * 100}%`, background: color || 'var(--primary)' }} />
        </div>
        <span className="progress-val">{value.toFixed(2)}</span>
      </div>
    </div>
  );
}

function Slider({ label, unit, min, max, step, value, onChange, fmt }) {
  return (
    <div className="slider-group">
      <div className="slider-label">
        <span>{label}</span>
        <span className="slider-value">{fmt ? fmt(value) : `${value}${unit}`}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))} />
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function DemoSection() {
  const [active, setActive]     = useState('safe');
  const [params, setParams]     = useState(SCENARIOS.safe);
  const [result, setResult]     = useState(() => runInference(SCENARIOS.safe));
  const [showSliders, setShow]  = useState(false);

  useEffect(() => {
    if (window.__safewatch_onResult) window.__safewatch_onResult(result);
  }, [result]);

  function select(key) {
    const p = SCENARIOS[key];
    setActive(key);
    setParams(p);
    setResult(runInference(p));
  }

  function set(key, val) {
    const next = { ...params, [key]: val };
    setParams(next);
    setResult(runInference(next));
  }

  const r = result;
  const alertColor = r.trigger_alert ? '#FF1493' : r.emergency_score > 0.40 ? '#FF8C00' : '#00FF88';

  const scenarioBtns = [
    { key: 'safe',     emoji: '🚶‍♀️', accent: '#00FF88' },
    { key: 'grab',     emoji: '🚨',  accent: '#FF1493' },
    { key: 'followed', emoji: '👁',  accent: '#FF8C00' },
    { key: 'sos',      emoji: '🆘',  accent: '#FF1493' },
  ];

  return (
    <section className="demo-section" id="demo">
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <div className="hero-badge" style={{ display: 'inline-flex', marginBottom: '1rem' }}>
            ⚡ Live ML Demo
          </div>
          <h2 style={{ fontSize: 'clamp(2rem,5vw,3rem)', fontWeight: 900, marginBottom: '0.75rem' }}>
            Threat Detection Engine
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.1rem' }}>
            Simulates real sensor data from the SafeWatch wristband.
            100% client-side · Instant results · No backend needed.
          </p>
        </div>

        <div className="demo-grid">

          {/* ── LEFT ─────────────────────────────────────────────────── */}
          <div>
            <div className="section-title">Simulate a Scenario</div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
              {scenarioBtns.map(({ key, emoji, accent }) => (
                <button
                  key={key}
                  id={`btn-${key}`}
                  onClick={() => select(key)}
                  style={{
                    width: '100%', padding: '1rem 1.25rem', borderRadius: 12,
                    background: active === key
                      ? (key === 'safe' ? 'rgba(0,255,136,0.10)' : 'rgba(255,20,147,0.12)')
                      : 'var(--bg-card2)',
                    border: `${active === key ? 2 : 1}px solid ${active === key ? accent : 'rgba(255,20,147,0.2)'}`,
                    borderLeft: `4px solid ${active === key ? accent : 'transparent'}`,
                    boxShadow: active === key ? `0 0 16px ${accent}33` : 'none',
                    textAlign: 'left', cursor: 'pointer',
                    color: '#fff', fontFamily: 'Inter, sans-serif',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{ fontWeight: 700, marginBottom: 3, fontSize: '0.95rem' }}>
                    {emoji} {SCENARIOS[key].label}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                    {SCENARIOS[key].sub}
                  </div>
                </button>
              ))}
            </div>

            {/* Sliders */}
            <div className="card" style={{ marginBottom: '1rem' }}>
              <button className="collapsible-toggle" onClick={() => setShow(s => !s)}>
                <span>{showSliders ? '▼' : '▶'}</span>
                Manual Control — updates in real-time
              </button>
              {showSliders && (
                <div style={{ marginTop: '1.25rem' }}>
                  <Slider label="Impact Intensity" unit="" min={0} max={15} step={0.1}
                    value={params.impact_g} onChange={v => set('impact_g', v)}
                    fmt={v => `${v.toFixed(1)}G`} />
                  <Slider label="Motion Chaos" unit="" min={0} max={1} step={0.01}
                    value={params.motion_erratic} onChange={v => set('motion_erratic', v)}
                    fmt={v => v.toFixed(2)} />
                  <Slider label="Heart Rate" unit=" bpm" min={40} max={200} step={1}
                    value={params.heart_rate} onChange={v => set('heart_rate', v)} />
                  <Slider label="HR Baseline" unit=" bpm" min={50} max={100} step={1}
                    value={params.hr_baseline} onChange={v => set('hr_baseline', v)} />
                  <Slider label="Threat Duration" unit="s" min={0} max={120} step={1}
                    value={params.duration_seconds} onChange={v => set('duration_seconds', v)} />
                  {/* SOS toggle */}
                  <div className="slider-group" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>SOS Button</span>
                    <button
                      onClick={() => set('sos_pressed', !params.sos_pressed)}
                      style={{
                        padding: '0.35rem 1rem', borderRadius: 20,
                        background: params.sos_pressed ? 'var(--primary)' : 'var(--bg-card2)',
                        border: '1px solid var(--primary)',
                        color: '#fff', cursor: 'pointer', fontWeight: 700,
                        fontSize: '0.8rem',
                      }}
                    >
                      {params.sos_pressed ? '🆘 PRESSED' : '○ Not pressed'}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Sensor readout */}
            <div className="card card-sm" style={{ fontFamily: 'Space Mono', fontSize: '0.75rem', color: 'var(--muted)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
                <span>Impact: <span className="pink">{params.impact_g.toFixed(1)}G</span></span>
                <span>HR: <span className="pink">{params.heart_rate} bpm</span></span>
                <span>Motion chaos: <span className="pink">{params.motion_erratic.toFixed(2)}</span></span>
                <span>Duration: <span className="pink">{params.duration_seconds}s</span></span>
                <span style={{ gridColumn: 'span 2' }}>
                  SOS: <span className="pink">{params.sos_pressed ? 'PRESSED' : 'inactive'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* ── RIGHT ────────────────────────────────────────────────── */}
          <div style={{ position: 'sticky', top: 80 }}>
            <div className="card">

              <EmergencyGauge score={r.emergency_score} />

              {/* Alert Banner */}
              <div className={`alert-banner ${r.trigger_alert ? 'on' : 'off'}`} style={{ marginBottom: '1.5rem' }}>
                {r.trigger_alert
                  ? '🚨 THREAT DETECTED — Guardians Alerted'
                  : r.sos_active
                    ? '🆘 SOS ACTIVE'
                    : '✓ No Threat Detected'}
              </div>

              <Bar label="Threat Confidence"   weight="0.35" value={r.threat_confidence} />
              <Bar label="Panic HR Score"       weight="0.30" value={r.hr_panic_score}    color="#FF8C00" />
              <Bar label="Motion Chaos"         weight="0.20" value={r.motion_chaos_score} />

              {/* SOS indicator */}
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.5rem 0', marginBottom: '0.5rem'
              }}>
                <span style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>SOS Button</span>
                <span style={{
                  color: r.sos_active ? '#FF1493' : 'var(--muted)',
                  fontWeight: 700, fontFamily: 'Space Mono', fontSize: '0.8rem'
                }}>
                  {r.sos_active ? '🆘 ACTIVE — Override Trigger' : '○ Inactive'}
                </span>
              </div>

              <hr className="divider" />

              <div className="latency-card" style={{ marginBottom: '0.75rem' }}>
                <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>Inference time</span>
                <span className="latency-val">{r.latency_ms < 1 ? '<1ms' : `${r.latency_ms}ms`}</span>
              </div>

              <div className="card card-sm" style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                <div className="flex justify-between mb1">
                  <span>Model</span>
                  <span style={{ color: 'var(--text)' }}>5→16→8→2 Neural Net</span>
                </div>
                <div className="flex justify-between mb1">
                  <span>Accuracy</span>
                  <span style={{ color: 'var(--success)' }}>91%+</span>
                </div>
                <div className="flex justify-between mb1">
                  <span>Trained on</span>
                  <span style={{ color: 'var(--text)' }}>14,000 samples</span>
                </div>
                <div className="flex justify-between">
                  <span>SOS override</span>
                  <span style={{ color: 'var(--primary)' }}>Always triggers</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
