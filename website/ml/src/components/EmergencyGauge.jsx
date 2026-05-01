import { useEffect, useRef } from 'react';

const ZONES = [
  { max: 0.40, color: '#00FF88', label: 'Normal' },
  { max: 0.72, color: '#FF8C00', label: 'Elevated' },
  { max: 1.00, color: '#FF1493', label: 'EMERGENCY' },
];

function getZone(score) {
  if (score < 0.40) return ZONES[0];
  if (score < 0.72) return ZONES[1];
  return ZONES[2];
}

export default function EmergencyGauge({ score = 0, animated = false }) {
  const scoreRef   = useRef(0);
  const displayRef = useRef(null);
  const animRef    = useRef(null);
  const arcRef     = useRef(null);

  const SIZE   = 220;
  const cx     = SIZE / 2;
  const cy     = SIZE / 2 + 20;
  const R      = 85;
  const SW     = 14;   // stroke width

  // Arc helper — semicircle from left (180°) to right (0°)
  function arcPath(pct, r) {
    const startAngle = Math.PI;           // 9 o'clock
    const endAngle   = startAngle + pct * Math.PI;
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    const large = pct > 0.5 ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
  }

  // Count-up animation
  useEffect(() => {
    const target  = score;
    const start   = scoreRef.current;
    const dur     = 500;
    const t0      = performance.now();

    cancelAnimationFrame(animRef.current);

    function step(now) {
      const pct = Math.min((now - t0) / dur, 1);
      const ease = 1 - Math.pow(1 - pct, 3);   // ease-out cubic
      const current = start + (target - start) * ease;

      scoreRef.current = current;

      if (displayRef.current) {
        displayRef.current.textContent = current.toFixed(2);
      }
      if (arcRef.current) {
        arcRef.current.setAttribute('d', arcPath(current, R));
        arcRef.current.setAttribute('stroke', getZone(current).color);
      }

      if (pct < 1) animRef.current = requestAnimationFrame(step);
      else scoreRef.current = target;
    }
    animRef.current = requestAnimationFrame(step);

    return () => cancelAnimationFrame(animRef.current);
  }, [score]);

  const zone = getZone(score);

  return (
    <div className="gauge-wrapper">
      <svg
        className="gauge-svg"
        width={SIZE}
        height={SIZE / 2 + 50}
        viewBox={`0 0 ${SIZE} ${SIZE / 2 + 50}`}
      >
        {/* Background arc */}
        <path
          d={arcPath(1, R)}
          stroke="#1A1E3A"
          strokeWidth={SW}
          fill="none"
          strokeLinecap="round"
        />

        {/* Zone markers */}
        {[0.40, 0.72].map(v => {
          const angle = Math.PI + v * Math.PI;
          const mx = cx + (R + SW) * Math.cos(angle);
          const my = cy + (R + SW) * Math.sin(angle);
          return (
            <circle key={v} cx={mx} cy={my} r={3}
              fill="rgba(255,255,255,0.3)" />
          );
        })}

        {/* Active arc (animated via ref) */}
        <path
          ref={arcRef}
          d={arcPath(0, R)}
          stroke={zone.color}
          strokeWidth={SW}
          fill="none"
          strokeLinecap="round"
          style={{
            filter: score > 0.72
              ? `drop-shadow(0 0 8px ${zone.color})`
              : 'none',
            transition: 'filter 0.3s'
          }}
        />

        {/* Score label */}
        <text
          ref={displayRef}
          x={cx}
          y={cy - 8}
          textAnchor="middle"
          fontSize="42"
          fontWeight="900"
          fontFamily="'Space Mono', monospace"
          fill={zone.color}
        >
          0.00
        </text>

        {/* Min/Max labels */}
        <text x={cx - R - 4} y={cy + 20} textAnchor="middle"
          fontSize="10" fill="#555577" fontFamily="Inter">0.0</text>
        <text x={cx + R + 4} y={cy + 20} textAnchor="middle"
          fontSize="10" fill="#555577" fontFamily="Inter">1.0</text>
      </svg>

      <div className={`gauge-status ${
        score < 0.40 ? 'normal' : score < 0.72 ? 'elevated' : 'emergency'
      }`}>
        {zone.label}
      </div>
    </div>
  );
}
