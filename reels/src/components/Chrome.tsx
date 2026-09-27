import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {LATIN} from '../fonts';
import {theme} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Top label: surah name + latin caption with hairline ornaments. */
export const Header: React.FC<{surah: string; title: string}> = ({surah, title}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const o = interpolate(t, [0.5, 1.4], [0, 1], clamp);
  const w = interpolate(t, [0.6, 2.2], [0, 140], clamp);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div style={{position: 'absolute', top: 170, left: 0, right: 0, textAlign: 'center', opacity: o}}>
        <div
          style={{
            fontFamily: '"Amiri", "Amiri Quran", serif',
            fontSize: 44,
            color: theme.gold,
            letterSpacing: 1,
            textShadow: '0 0 18px rgba(217,190,120,0.3)',
          }}
        >
          {surah}
        </div>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 18, marginTop: 8}}>
          <div style={{width: w, height: 1, background: `linear-gradient(to right, transparent, ${theme.goldDim})`}} />
          <div
            style={{
              fontFamily: `${LATIN}, Georgia, serif`,
              fontSize: 24,
              letterSpacing: 7,
              color: theme.ivoryDim,
              textTransform: 'uppercase',
            }}
          >
            {title}
          </div>
          <div style={{width: w, height: 1, background: `linear-gradient(to left, transparent, ${theme.goldDim})`}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Black fade in at the start and fade out at the end. */
export const FadeInOut: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames, fps} = useVideoConfig();
  const inO = interpolate(frame, [0, Math.round(fps * 0.9)], [1, 0], clamp);
  const outO = interpolate(frame, [durationInFrames - Math.round(fps * 1.3), durationInFrames - 1], [0, 1], clamp);
  return <AbsoluteFill style={{background: '#000', opacity: Math.max(inO, outO), pointerEvents: 'none'}} />;
};
