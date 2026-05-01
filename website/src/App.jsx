import { useState, useCallback } from 'react';
import ParticleCanvas from './components/ParticleCanvas';
import DemoSection from './pages/DemoSection';

const TECH = ['nRF52840', 'FreeRTOS', 'Neural Net (pure Python)', 'React Native', 'Node.js', 'FastAPI', 'MongoDB', 'Twilio', 'Socket.io', 'BLE 5.3'];

const STEPS = [
  {
    icon: '⌚',
    num: 'Step 01',
    title: 'Passive Sensing',
    desc: 'SafeWatch continuously monitors IMU (impact + motion chaos), heart rate, and GPS — no action required from the wearer.'
  },
  {
    icon: '🧠',
    num: 'Step 02',
    title: 'Threat Detection',
    desc: '5-feature neural network detects grab attacks, panic states, and being followed in <12ms. SOS button overrides all thresholds immediately.'
  },
  {
    icon: '📱',
    num: 'Step 03',
    title: 'Instant Guardian Alert',
    desc: 'BLE 5.3 → phone → Node.js backend → Twilio SMS with live GPS to all trusted contacts in under 8 seconds.'
  }
];

export default function App() {
  const [liveStats, setLiveStats] = useState({
    fall: 0, hr: 0, imm: 0, score: 0
  });

  const handleResult = useCallback((res) => {
    setLiveStats({
      fall:  res.fall_confidence,
      hr:    res.hr_anomaly_score,
      imm:   res.immobility_factor,
      score: res.emergency_score
    });
  }, []);

  // Share result handler with DemoSection via window
  window.__safewatch_onResult = handleResult;

  function scrollTo(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  }

  return (
    <>
      {/* ── Navbar ────────────────────────────────────────────────────── */}
      <nav className="navbar">
        <a className="navbar-logo" href="/">Safe<span>Watch</span></a>
        <div className="navbar-links">
          <button className="nav-link" onClick={() => scrollTo('demo')}>Live Demo</button>
          <button className="nav-link" onClick={() => scrollTo('how')}>How It Works</button>
          <a className="nav-link" href="https://github.com/Angelflyhi/Fluex" target="_blank" rel="noopener">GitHub</a>
          <a
            className="btn btn-primary btn-sm"
            href="#demo"
            onClick={e => { e.preventDefault(); scrollTo('demo'); }}
          >
            Try Demo
          </a>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <section className="hero">
        <ParticleCanvas />
        <div className="hero-content">
          <div className="hero-badge">
            <span>🔴</span> Team FLUEX · Hackathon 2024
          </div>

          <h1 className="hero-title">
            Safety That<br />
            <span className="highlight">Never Sleeps</span>
          </h1>

          <p className="hero-subtitle">
            ML-powered women's safety wearable. No button press required.
            SafeWatch passively detects grab attacks, panic states, and threat situations
            — alerting trusted contacts with live GPS in under 8 seconds.
          </p>

          <div className="hero-cta">
            <button
              className="btn btn-primary"
              style={{ fontSize: '1.1rem' }}
              onClick={() => scrollTo('demo')}
            >
              ⚡ Try Live Demo
            </button>
            <a
              className="btn btn-outline"
              href="https://github.com/Angelflyhi/Fluex"
              target="_blank"
              rel="noopener"
            >
              ⭐ View GitHub
            </a>
          </div>

          <div className="hero-stats">
            <span className="stat-pill">91%+ Accuracy</span>
            <span className="stat-pill">&lt;12ms Inference</span>
            <span className="stat-pill">&lt;8s Alert Time</span>
            <span className="stat-pill">$67.30 BOM</span>
          </div>
        </div>
      </section>

      {/* ── Stats Bar ─────────────────────────────────────────────────── */}
      <div className="stats-bar">
        {[
          { label: 'Threat Confidence', val: liveStats.fall  },
          { label: 'Panic HR Score',    val: liveStats.hr    },
          { label: 'Motion Chaos',      val: liveStats.imm   },
          { label: 'Emergency Score',   val: liveStats.score },
        ].map(({ label, val }) => (
          <div className="stat-item" key={label}>
            <div className="stat-value">{val.toFixed(2)}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* ── Demo ──────────────────────────────────────────────────────── */}
      <DemoSection />

      {/* ── How It Works ──────────────────────────────────────────────── */}
      <section className="section" id="how">
        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <div className="hero-badge" style={{ display: 'inline-flex', marginBottom: '1rem' }}>⚙️ System Design</div>
          <h2 style={{ fontSize: 'clamp(2rem,4vw,2.75rem)', fontWeight: 900, marginBottom: '0.75rem' }}>
            How It Works
          </h2>
          <p style={{ color: 'var(--muted)' }}>
            From wrist sensor to guardian alert in under 8 seconds.
          </p>
        </div>

        <div className="steps-grid">
          {STEPS.map(s => (
            <div key={s.num} className="step-card">
              <div className="step-icon">{s.icon}</div>
              <div className="step-num">{s.num}</div>
              <h3 className="step-title">{s.title}</h3>
              <p className="step-desc">{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Architecture diagram */}
        <div className="card" style={{ marginTop: '3rem', fontFamily: 'Space Mono', fontSize: '0.8rem', color: 'var(--muted)', padding: '2rem' }}>
          <div style={{ color: 'var(--primary)', fontWeight: 700, marginBottom: '1rem' }}>Detection Pipeline</div>
          <pre style={{ lineHeight: 1.8, overflow: 'auto' }}>{`IMU (100Hz) + HR (50Hz) + GPS
        |  FreeRTOS nRF52840
        v
  5-Feature Neural Net (<12ms)
  impact_norm    x 0.35
  hr_panic_norm  x 0.30
  motion_chaos   x 0.20
  duration_norm  x 0.15
  + SOS override -> immediate
  ──────────────────────────
  threatScore > 0.72 -> TRIGGER
        |  BLE 5.3
        v
  React Native App
        |  HTTPS + Socket.io
        v
  Node.js Backend (Railway)
  +- MongoDB: log incident
  +- Twilio: SMS + GPS to contacts
  \`- Socket.io: live location map`}</pre>
        </div>

        {/* Tech stack */}
        <div className="tech-pills">
          {TECH.map(t => (
            <span key={t} className="tech-pill">{t}</span>
          ))}
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer className="footer">
        <div className="footer-logo">SafeWatch</div>
        <p className="footer-sub">Women's Safety Wearable — Passive Threat Detection</p>
        <p className="footer-sub">Built by <strong>Team FLUEX</strong> (Leader: Angel) · Hackathon 2024</p>
        <p style={{ marginTop: '0.75rem', fontSize: '0.875rem' }}>
          <a
            className="footer-link"
            href="https://github.com/Angelflyhi/Fluex"
            target="_blank"
            rel="noopener"
          >
            ⭐ github.com/Angelflyhi/Fluex
          </a>
        </p>
      </footer>
    </>
  );
}
