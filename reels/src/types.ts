export type Word = {w: string; s: number; e: number};
export type Phrase = {s: number; e: number; words: Word[]};
export type Ayah = {n: string; tr: string; s: number; e: number; phrases: Phrase[]};
export type Mood = 'mountains' | 'sky' | 'room' | 'desert' | 'birds' | 'water';
export type ReelData = {
  id: string;
  surah: string;
  title: string;
  audio: string;
  bg: string;
  bgExists: boolean;
  mood: Mood | string;
  duration: number;
  ayat: Ayah[];
};
