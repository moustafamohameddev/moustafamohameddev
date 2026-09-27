// Renders every composition in src/Root.tsx to out/<id>.mp4.
// Video is rendered muted by Remotion, then the trimmed ayah clip is muxed in
// with ffmpeg (deterministic — avoids the audio-dropout we hit with in-render audio).
import {execSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'src/data/reels.json'), 'utf8'));
const only = process.argv.slice(2);

const chrome = [process.env.REMOTION_BROWSER_EXECUTABLE, '/opt/pw-browsers/chromium-1194/chrome-linux/chrome']
  .find((c) => c && fs.existsSync(c));
const browser = chrome ? `--browser-executable=${chrome} --chrome-mode=chrome-for-testing` : '';

const ffmpeg = [
  process.env.FFMPEG,
  path.join(root, 'node_modules/ffmpeg-static/ffmpeg'),
  'ffmpeg',
].find((c) => c && (c === 'ffmpeg' || fs.existsSync(c)));

fs.mkdirSync(path.join(root, 'out'), {recursive: true});
for (const reel of data.reels) {
  if (only.length && !only.includes(reel.id)) continue;
  const video = path.join(root, 'out', `${reel.id}.video.mp4`);
  const out = path.join(root, 'out', `${reel.id}.mp4`);
  const audio = path.join(root, 'public', reel.audio);
  console.log(`\n▶ rendering ${reel.id} (${reel.duration}s)`);
  execSync(
    `npx remotion render src/index.ts ${reel.id} "${video}" ${browser} --muted --codec=h264 --crf=14 --concurrency=${process.env.CONCURRENCY ?? 4} --timeout=60000 --log=error`,
    {cwd: root, stdio: 'inherit'},
  );
  console.log(`  ♪ muxing ${reel.audio}`);
  execSync(
    `"${ffmpeg}" -y -loglevel error -i "${video}" -i "${audio}" -map 0:v:0 -map 1:a:0 -vf "eq=contrast=1.10:saturation=0.82:brightness=-0.015,noise=alls=4:allf=t+u" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "${out}"`,
    {cwd: root, stdio: 'inherit'},
  );
  fs.unlinkSync(video);
  console.log(`  ✔ ${out}`);
}
