import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ProceduralScene} from './ProceduralScene';

/**
 * Slow, stabilised dolly-in over the still plate (or a procedural scene when
 * no plate is available). Adds a cinematic grade: crushed blacks, desaturated
 * slate tones.
 */
export const Background: React.FC<{src: string; exists: boolean; mood: string}> = ({src, exists, mood}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const t = frame / durationInFrames;
  const scale = interpolate(t, [0, 1], [1.04, 1.18], {easing: Easing.inOut(Easing.quad)});
  const y = interpolate(t, [0, 1], [0, -28]);

  return (
    <AbsoluteFill style={{backgroundColor: '#050608', overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          transform: `translateY(${y}px) scale(${scale})`,
          transformOrigin: '50% 42%',
          filter: 'saturate(0.72) contrast(1.1) brightness(0.86)',
        }}
      >
        {exists ? (
          <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : (
          <ProceduralScene mood={mood} />
        )}
      </AbsoluteFill>
      {/* slate tint for a unified colour grade */}
      <AbsoluteFill style={{background: 'rgba(40,50,66,0.18)', mixBlendMode: 'multiply'}} />
    </AbsoluteFill>
  );
};
