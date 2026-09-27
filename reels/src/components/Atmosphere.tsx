import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';

/** Drifting volumetric fog banks + a soft light shaft from above. */
export const Fog: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const banks = [
    {x: 0.5 + 0.12 * Math.sin(t / 11), y: 0.64 + 0.03 * Math.cos(t / 9), w: 1900, h: 820, o: 0.30},
    {x: 0.35 + 0.16 * Math.cos(t / 15 + 1), y: 0.84 + 0.03 * Math.sin(t / 8), w: 1700, h: 640, o: 0.36},
    {x: 0.7 + 0.1 * Math.sin(t / 13 + 2), y: 0.30 + 0.04 * Math.sin(t / 10 + 1), w: 1500, h: 700, o: 0.14},
    {x: 0.2 + 0.1 * Math.sin(t / 17 + 4), y: 0.50 + 0.05 * Math.cos(t / 12 + 2), w: 1300, h: 520, o: 0.16},
  ];
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {banks.map((b, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: b.x * 1080 - b.w / 2,
            top: b.y * 1920 - b.h / 2,
            width: b.w,
            height: b.h,
            borderRadius: '50%',
            background: `radial-gradient(ellipse at center, rgba(178,188,204,${b.o}) 0%, rgba(178,188,204,${b.o * 0.45}) 35%, rgba(178,188,204,0) 68%)`,
            filter: 'blur(28px)',
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

export const LightShaft: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const rot = -14 + 3 * Math.sin(t / 9);
  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          left: 540 - 260,
          top: -300,
          width: 520,
          height: 2100,
          transformOrigin: '50% 0%',
          transform: `rotate(${rot}deg)`,
          background: 'linear-gradient(to bottom, rgba(235,240,248,0.16) 0%, rgba(235,240,248,0.06) 45%, rgba(235,240,248,0) 80%)',
          filter: 'blur(26px)',
        }}
      />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 38%, rgba(0,0,0,0.55) 78%, rgba(0,0,0,0.88) 100%)',
      }}
    />
    <AbsoluteFill
      style={{
        background:
          'linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 40%, rgba(0,0,0,0.42) 62%, rgba(0,0,0,0.78) 100%)',
      }}
    />
  </AbsoluteFill>
);

/** Subtle 35mm grain — regenerated each frame at half resolution. */
export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'overlay', opacity: 0.16}}>
      <svg width="1080" height="1920" viewBox="0 0 540 960" preserveAspectRatio="none">
        <filter id="grain" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={frame % 200} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="540" height="960" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};
