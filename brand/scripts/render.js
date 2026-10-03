#!/usr/bin/env node
// Render a brand template to PNG (transparent where the template is) or PDF.
//
//   node brand/scripts/render.js <template.html> <out.png> <width> <height> [key=value ...]
//   node brand/scripts/render.js brand/templates/ayah-overlay.html out/a5.png 1080 1920 \
//        ayah="فَإِنَّ مَعَ ٱلۡعُسۡرِ يُسۡرًا ٥" tr="So, surely with hardship comes *ease*" label="سورة الشرح"
//
// Output size is exactly <width>x<height>. Needs: npm i playwright (Chromium).
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

(async () => {
  const [tpl, out, w, h, ...kv] = process.argv.slice(2);
  if (!tpl || !out) { console.error('usage: render.js <template> <out.png|out.pdf> <w> <h> [k=v ...]'); process.exit(1); }
  const params = new URLSearchParams();
  for (const pair of kv) { const i = pair.indexOf('='); params.set(pair.slice(0, i), pair.slice(i + 1)); }
  const url = 'file://' + path.resolve(tpl) + (kv.length ? '?' + params.toString() : '');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +w || 1080, height: +h || 1920 } });
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForLoadState('networkidle');
  if (out.endsWith('.pdf')) await page.pdf({ path: out, printBackground: true, preferCSSPageSize: true });
  else await page.screenshot({ path: out, omitBackground: true });
  await browser.close();
  console.log(out);
})();
