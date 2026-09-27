import {Config} from '@remotion/cli/config';
import fs from 'node:fs';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);
Config.setPixelFormat('yuv420p');
Config.setCodec('h264');
Config.setCrf(17);

// Use a pre-installed Chromium when one is available (no download needed).
const candidates = [
  process.env.REMOTION_BROWSER_EXECUTABLE,
  '/opt/pw-browsers/chromium/chrome',
  '/opt/pw-browsers/chromium/chrome-linux/chrome',
];
for (const c of candidates) {
  if (c && fs.existsSync(c)) {
    Config.setBrowserExecutable(c);
    break;
  }
}
