import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

export const ARABIC = 'Amiri Quran';
export const ARABIC_ALT = 'Scheherazade New';
export const LATIN = 'Cormorant Garamond';

const all = Promise.all([
  loadFont({family: ARABIC, url: staticFile('fonts/AmiriQuran.ttf'), weight: '400'}),
  loadFont({family: 'Amiri', url: staticFile('fonts/Amiri-Regular.ttf'), weight: '400'}),
  loadFont({family: 'Amiri', url: staticFile('fonts/Amiri-Bold.ttf'), weight: '700'}),
  loadFont({family: ARABIC_ALT, url: staticFile('fonts/ScheherazadeNew-Regular.ttf'), weight: '400'}),
  loadFont({family: ARABIC_ALT, url: staticFile('fonts/ScheherazadeNew-Bold.ttf'), weight: '700'}),
  loadFont({family: LATIN, url: staticFile('fonts/Cormorant-Regular.ttf'), weight: '400'}),
  loadFont({family: LATIN, url: staticFile('fonts/Cormorant-Italic.ttf'), weight: '400', style: 'italic'}),
]);

export const fontsReady = all;
