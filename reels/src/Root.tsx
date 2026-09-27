import React from 'react';
import {Composition, Folder} from 'remotion';
import data from './data/reels.json';
import {Reel} from './Reel';
import type {ReelData} from './types';

const {fps, width, height} = data;

export const RemotionRoot: React.FC = () => {
  return (
    <Folder name="Surah-Al-Mulk-Reels">
      {(data.reels as ReelData[]).map((reel) => (
        <Composition
          key={reel.id}
          id={reel.id}
          component={Reel}
          durationInFrames={Math.round(reel.duration * fps)}
          fps={fps}
          width={width}
          height={height}
          defaultProps={{reel}}
        />
      ))}
    </Folder>
  );
};
