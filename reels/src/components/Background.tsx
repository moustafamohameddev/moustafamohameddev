import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {ProceduralScene} from './ProceduralScene';
import type {Scene} from '../types';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const XFADE = 0.9; // seconds of cross-dissolve between b-roll scenes

/** Camera move for one still plate: returns a CSS transform for progress p ∈ [0,1]. */
const camera = (move: Scene['move'], p: number) => {
  const e = Easing.inOut(Easing.sin);
  const q = e(p);
  switch (move) {
    case 'dollyOut':
      return `translate(0, ${interpolate(q, [0, 1], [-14, 8])}px) scale(${interpolate(q, [0, 1], [1.22, 1.08])})`;
    case 'panLeft':
      return `translate(${interpolate(q, [0, 1], [34, -34])}px, ${interpolate(q, [0, 1], [-6, 6])}px) scale(1.16)`;
    case 'panRight':
      return `translate(${interpolate(q, [0, 1], [-34, 34])}px, ${interpolate(q, [0, 1], [6, -6])}px) scale(1.16)`;
    case 'tiltUp':
      return `translate(0, ${interpolate(q, [0, 1], [40, -40])}px) scale(${interpolate(q, [0, 1], [1.14, 1.18])})`;
    case 'dollyIn':
    default:
      return `translate(0, ${interpolate(q, [0, 1], [6, -22])}px) scale(${interpolate(q, [0, 1], [1.06, 1.22])})`;
  }
};

const Plate: React.FC<{scene: Scene; t: number; first: boolean; last: boolean}> = ({scene, t, first, last}) => {
  const fadeIn = first ? 1 : interpolate(t, [scene.s - XFADE / 2, scene.s + XFADE / 2], [0, 1], clamp);
  const fadeOut = last ? 1 : interpolate(t, [scene.e - XFADE / 2, scene.e + XFADE / 2], [1, 0], clamp);
  const o = Math.min(fadeIn, fadeOut);
  if (o <= 0) return null;
  const p = interpolate(t, [scene.s - XFADE / 2, scene.e + XFADE / 2], [0, 1], clamp);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <AbsoluteFill style={{transform: camera(scene.move, p), transformOrigin: '50% 45%'}}>
        <Img src={staticFile(scene.src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/**
 * B-roll layer: a sequence of still plates, each with its own slow camera move,
 * cross-dissolved at the cut points. Falls back to a procedural scene.
 */
export const Background: React.FC<{scenes: Scene[]; mood: string}> = ({scenes, mood}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill style={{backgroundColor: '#050608', overflow: 'hidden'}}>
      <AbsoluteFill>
        {scenes.length === 0 ? (
          <ProceduralScene mood={mood} />
        ) : (
          scenes.map((sc, i) => <Plate key={i} scene={sc} t={t} first={i === 0} last={i === scenes.length - 1} />)
        )}
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'rgba(40,50,66,0.08)', mixBlendMode: 'multiply'}} />
    </AbsoluteFill>
  );
};
