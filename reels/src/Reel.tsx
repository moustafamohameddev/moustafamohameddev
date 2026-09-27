import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, continueRender, delayRender, staticFile} from 'remotion';
import type {ReelData} from './types';
import {fontsReady} from './fonts';
import {Background} from './components/Background';
import {Fog, LightShaft, Vignette} from './components/Atmosphere';
import {Verse} from './components/Verse';
import {Header, FadeInOut} from './components/Chrome';
import {theme} from './theme';

export const Reel: React.FC<{reel: ReelData}> = ({reel}) => {
  const [handle] = useState(() => delayRender('Loading fonts'));
  useEffect(() => {
    fontsReady.then(() => continueRender(handle)).catch(() => continueRender(handle));
  }, [handle]);

  return (
    <AbsoluteFill style={{backgroundColor: theme.bg}}>
      <Audio src={staticFile(reel.audio)} />
      <Background scenes={reel.scenes} mood={reel.mood} />
      <LightShaft />
      <Fog />
      <Vignette />
      <Header surah={reel.surah} title={reel.title} />
      <Verse ayat={reel.ayat} />
      <FadeInOut />
    </AbsoluteFill>
  );
};
