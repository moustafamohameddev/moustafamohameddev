// Renders every composition registered in src/Root.tsx into out/<id>.mp4
import {execSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'src/data/reels.json'), 'utf8'));
const only = process.argv.slice(2);

const chrome = [process.env.REMOTION_BROWSER_EXECUTABLE, '/opt/pw-browsers/chromium-1194/chrome-linux/chrome']
  .find((c) => c && fs.existsSync(c));
const browser = chrome ? `--browser-executable=${chrome} --chrome-mode=chrome-for-testing` : '';

fs.mkdirSync(path.join(root, 'out'), {recursive: true});
for (const reel of data.reels) {
  if (only.length && !only.includes(reel.id)) continue;
  const out = path.join(root, 'out', `${reel.id}.mp4`);
  console.log(`\n▶ rendering ${reel.id} (${reel.duration}s) → ${out}`);
  execSync(
    `npx remotion render src/index.ts ${reel.id} "${out}" ${browser} --codec=h264 --crf=17 --concurrency=${process.env.CONCURRENCY ?? 4} --log=error`,
    {cwd: root, stdio: 'inherit'},
  );
}
