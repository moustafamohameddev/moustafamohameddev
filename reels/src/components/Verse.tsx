import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import type {Ayah, Phrase, Word} from '../types';
import {ARABIC, LATIN} from '../fonts';
import {theme} from '../theme';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const WordSpan: React.FC<{word: Word; t: number; last: boolean}> = ({word, t, last}) => {
  const a = interpolate(t, [word.s - 0.06, word.s + 0.28], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const y = interpolate(a, [0, 1], [14, 0]);
  const blur = interpolate(a, [0, 1], [8, 0]);
  const active = t >= word.s && t < word.e + 0.15;
  const color = active ? theme.goldHi : theme.gold;
  const glow = active
    ? '0 0 22px rgba(243,218,150,0.55), 0 0 60px rgba(243,218,150,0.22)'
    : '0 0 14px rgba(217,190,120,0.25)';
  return (
    <span
      style={{
        display: 'inline-block',
        opacity: a,
        transform: `translateY(${y}px)`,
        filter: `blur(${blur}px)`,
        color,
        textShadow: glow,
        whiteSpace: 'nowrap',
        transition: 'none',
      }}
    >
      {word.w}
    </span>
  );
};

const PhraseBlock: React.FC<{phrase: Phrase; t: number; ayahNumber?: string}> = ({phrase, t, ayahNumber}) => {
  const fadeIn = interpolate(t, [phrase.s - 0.35, phrase.s], [0, 1], clamp);
  const fadeOut = interpolate(t, [phrase.e + 0.15, phrase.e + 0.55], [1, 0], clamp);
  const o = Math.min(fadeIn, fadeOut);
  if (o <= 0) return null;
  const lastWord = phrase.words[phrase.words.length - 1];
  const numA = ayahNumber ? interpolate(t, [lastWord.e - 0.2, lastWord.e + 0.25], [0, 1], clamp) : 0;
  return (
    <div
      style={{
        position: 'absolute',
        left: 70,
        right: 70,
        top: '38%',
        transform: 'translateY(-50%)',
        opacity: o,
        direction: 'rtl',
        display: 'flex',
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'center',
        alignItems: 'baseline',
        columnGap: 24,
        fontFamily: `${ARABIC}, "Scheherazade New", serif`,
        fontSize: 78,
        lineHeight: 1.85,
      }}
    >
      {phrase.words.map((w, i) => (
        <WordSpan key={i} word={w} t={t} last={i === phrase.words.length - 1} />
      ))}
      {ayahNumber ? (
        <span
          style={{
            display: 'inline-block',
            opacity: numA,
            color: theme.goldDim,
            fontSize: 60,
            fontFamily: `"Amiri", ${ARABIC}, serif`,
          }}
        >
          ﴿{ayahNumber}﴾
        </span>
      ) : null}
    </div>
  );
};

const Translation: React.FC<{ayah: Ayah; t: number}> = ({ayah, t}) => {
  const o = Math.min(
    interpolate(t, [ayah.s + 0.15, ayah.s + 0.9], [0, 1], clamp),
    interpolate(t, [ayah.e + 0.35, ayah.e + 0.9], [1, 0], clamp),
  );
  if (o <= 0) return null;
  const y = interpolate(o, [0, 1], [10, 0]);
  return (
    <div
      style={{
        position: 'absolute',
        left: 120,
        right: 120,
        top: '61%',
        opacity: o,
        transform: `translateY(${y}px)`,
        textAlign: 'center',
        fontFamily: `${LATIN}, Georgia, serif`,
        fontStyle: 'italic',
        fontSize: 34,
        lineHeight: 1.45,
        color: theme.ivoryDim,
        letterSpacing: 0.4,
        textShadow: '0 2px 18px rgba(0,0,0,0.8)',
      }}
    >
      {ayah.tr}
    </div>
  );
};

export const Verse: React.FC<{ayat: Ayah[]}> = ({ayat}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  return (
    <AbsoluteFill>
      {ayat.map((a, ai) =>
        a.phrases.map((p, pi) => (
          <PhraseBlock key={`${ai}-${pi}`} phrase={p} t={t} ayahNumber={pi === a.phrases.length - 1 ? a.n : undefined} />
        )),
      )}
      {ayat.map((a, ai) => (
        <Translation key={ai} ayah={a} t={t} />
      ))}
    </AbsoluteFill>
  );
};
