import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';

/** Light, drifting fog banks near the ground — kept thin so the plate stays sharp. */
export const Fog: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const banks = [
    {x: 0.5 + 0.12 * Math.sin(t / 11), y: 0.86 + 0.02 * Math.cos(t / 9), w: 2000, h: 620, o: 0.16},
    {x: 0.3 + 0.16 * Math.cos(t / 15 + 1), y: 0.72 + 0.03 * Math.sin(t / 8), w: 1500, h: 420, o: 0.09},
    {x: 0.75 + 0.1 * Math.sin(t / 13 + 2), y: 0.22 + 0.04 * Math.sin(t / 10 + 1), w: 1400, h: 520, o: 0.05},
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
            background: `radial-gradient(ellipse at center, rgba(178,188,204,${b.o}) 0%, rgba(178,188,204,${b.o * 0.4}) 40%, rgba(178,188,204,0) 70%)`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

/** A faint volumetric shaft from the top, swaying very slowly. */
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
          left: 540 - 240,
          top: -300,
          width: 480,
          height: 2100,
          transformOrigin: '50% 0%',
          transform: `rotate(${rot}deg)`,
          background:
            'radial-gradient(ellipse 50% 62% at 50% 8%, rgba(235,240,248,0.10) 0%, rgba(235,240,248,0.045) 45%, rgba(235,240,248,0) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

/** Edge vignette + a darker band behind the text zones for legibility. */
export const Vignette: React.FC = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill
      style={{
        background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.42) 80%, rgba(0,0,0,0.78) 100%)',
      }}
    />
    <AbsoluteFill
      style={{
        background:
          'linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 20%, rgba(0,0,0,0) 44%, rgba(0,0,0,0.3) 60%, rgba(0,0,0,0.68) 100%)',
      }}
    />
  </AbsoluteFill>
);

/** Subtle 35mm grain — regenerated each frame at half resolution. */
export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'overlay', opacity: 0.09}}>
      <svg width="1080" height="1920" viewBox="0 0 540 960" preserveAspectRatio="none">
        <filter id="grain" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={frame % 200} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="540" height="960" filter="url(#grain)" />
      </svg>
    </AbsoluteFill>
  );
};
