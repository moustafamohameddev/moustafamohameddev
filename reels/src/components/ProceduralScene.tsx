import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';

// Deterministic pseudo-random for stable renders.
const rand = (seed: number) => {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
};

const ridge = (seed: number, baseY: number, amp: number, W: number) => {
  const r = rand(seed);
  const pts: string[] = [];
  const n = 14;
  const offs = Array.from({length: n + 1}, () => (r() - 0.5) * amp);
  for (let i = 0; i <= n; i++) {
    const x = (W / n) * i;
    const y = baseY + offs[i] + Math.sin(i * 1.7 + seed) * amp * 0.25;
    pts.push(`${x},${y}`);
  }
  return `M0,${baseY + amp} L${pts.join(' L')} L${W},${baseY + amp} Z`;
};

/** Fallback plate: layered fog-bound ridges under a pale horizon glow. */
export const ProceduralScene: React.FC<{mood: string}> = ({mood}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const W = 1080;
  const H = 1920;
  const seed = mood.length * 17 + 3;
  const layers = useMemo(
    () => [
      {d: ridge(seed + 1, 1180, 90, W), fill: '#1b2028'},
      {d: ridge(seed + 2, 1300, 120, W), fill: '#14181e'},
      {d: ridge(seed + 3, 1440, 110, W), fill: '#0d1014'},
      {d: ridge(seed + 4, 1600, 90, W), fill: '#07090b'},
    ],
    [seed],
  );
  const stars = useMemo(() => {
    const r = rand(seed + 9);
    return Array.from({length: mood === 'sky' ? 160 : 40}, () => ({
      x: r() * W,
      y: r() * 1000,
      s: 0.6 + r() * 1.6,
      p: r() * Math.PI * 2,
    }));
  }, [seed, mood]);

  const glowY = mood === 'water' ? 1500 : 1150;
  return (
    <AbsoluteFill>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#05070a" />
            <stop offset="0.55" stopColor="#0f141b" />
            <stop offset="1" stopColor="#1a212b" />
          </linearGradient>
          <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor="#b8c2cf" stopOpacity="0.55" />
            <stop offset="0.5" stopColor="#7d8794" stopOpacity="0.18" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width={W} height={H} fill="url(#sky)" />
        {stars.map((s, i) => (
          <circle
            key={i}
            cx={s.x}
            cy={s.y}
            r={s.s}
            fill="#dfe6ee"
            opacity={0.25 + 0.45 * (0.5 + 0.5 * Math.sin(frame / (fps * 1.5) + s.p))}
          />
        ))}
        <ellipse cx={W / 2} cy={glowY} rx={700} ry={260} fill="url(#glow)" />
        {layers.map((l, i) => (
          <path key={i} d={l.d} fill={l.fill} />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
