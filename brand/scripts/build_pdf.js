#!/usr/bin/env node
// Rebuild BRAND.pdf from BRAND.md (run after editing the guide).
//   npm i marked@12 pdf-lib@1.17.1 playwright   (once; or point NODE_PATH at a folder that has them)
//   node brand/scripts/build_pdf.js
// Two passes: full-bleed dark pages (cover + gallery) with no page margin,
// then the guide itself on paper with margins; pdf-lib joins them.
const fs = require('fs');
const path = require('path');
const { marked } = require('marked');
const { PDFDocument } = require('pdf-lib');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const root = path.resolve(__dirname, '..');
const u = (p) => 'file://' + path.join(root, p);
const md = fs.readFileSync(path.join(root, 'BRAND.md'), 'utf8')
  .replace(/^# .*\n/, '')                      // the cover carries the title
  .replace(/- \[ \] /g, '- ☐ ');

const head = (pageCss) => `<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
@font-face{font-family:Plex;src:url(${u('fonts/IBMPlexSansArabic-Regular.ttf')});font-weight:400}
@font-face{font-family:Plex;src:url(${u('fonts/IBMPlexSansArabic-Medium.ttf')});font-weight:500}
@font-face{font-family:Plex;src:url(${u('fonts/IBMPlexSansArabic-SemiBold.ttf')});font-weight:600}
@font-face{font-family:Plex;src:url(${u('fonts/IBMPlexSansArabic-Bold.ttf')});font-weight:700}
${pageCss}
:root{--night:#0B0907;--paper:#F6F1E8;--ink:#17110C;--ink2:#4A4036;--amber-deep:#9A5510;--rule:#D5C9B6;--ivory:#F4EDE1;--muted:#CFC5B5;--smoke:#9A8F80}
*{box-sizing:border-box}
body{margin:0;font:400 10.5pt/1.7 Plex,sans-serif;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}
</style>`;

const dark = `${head(`@page{size:A4;margin:0}
.pg{width:210mm;height:297mm;background:var(--night);color:var(--ivory);overflow:hidden;page-break-after:always;padding:24mm 20mm;display:flex;flex-direction:column}
.pg:last-child{page-break-after:auto}
.cover{justify-content:space-between}
.cover img{width:118mm;align-self:flex-start}
h1{font:600 26pt/1.25 Plex;margin:0}
.lead{margin:4mm 0 0;color:var(--muted);font-size:12pt}
.meta{color:var(--smoke);font-size:9.5pt}
h2{font:700 15pt/1.3 Plex;margin:0 0 6mm;color:var(--ivory)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5mm}
.two{display:grid;grid-template-columns:1fr 1fr;gap:5mm;margin-top:6mm}
figure{margin:0} figure img{width:100%;display:block;border:1px solid #3A2E23}
figcaption{font-size:8.5pt;margin-top:1.5mm;color:var(--smoke)}`)}</head><body>
<section class="pg cover">
  <img src="${u('assets/signature-ivory.svg')}" alt="مصطفى محمد">
  <div><h1>دليل الهوية والمونتاج</h1>
  <p class="lead">تلاوات وفيديوهات مصطفى محمد على فيسبوك وإنستجرام ويوتيوب وتيك توك</p></div>
  <div class="meta">الإصدار ١ · الملفات المصاحبة في مجلد brand/</div>
</section>
<section class="pg">
  <h2>الشكل النهائي</h2>
  <div class="grid">
    <figure><img src="${u('examples/example-ayah-vertical.png')}"><figcaption>ريل: الآية والترجمة واسم السورة، والتوقيع فوق على اليمين</figcaption></figure>
    <figure><img src="${u('examples/example-cover.png')}"><figcaption>غلاف الريل</figcaption></figure>
    <figure><img src="${u('assets/guide-safe-zones-vertical.png')}" style="background:#2a2420"><figcaption>المناطق الآمنة (للمونتاج بس)</figcaption></figure>
  </div>
  <div class="two">
    <figure><img src="${u('examples/example-ayah-landscape.png')}"><figcaption>يوتيوب عرضي</figcaption></figure>
    <figure><img src="${u('examples/example-thumbnail.png')}"><figcaption>الصورة المصغرة ليوتيوب</figcaption></figure>
  </div>
  <div class="two">
    <figure><img src="${u('assets/youtube-banner-2560x1440.png')}"><figcaption>بانر يوتيوب</figcaption></figure>
    <figure><img src="${u('assets/facebook-cover-1640x624.png')}"><figcaption>غلاف فيسبوك</figcaption></figure>
  </div>
</section></body></html>`;

const guide = `${head(`@page{size:A4;margin:18mm 16mm}
html,body{background:var(--paper)}
h2{font:700 15pt/1.3 Plex;margin:8mm 0 3mm;padding-bottom:2mm;border-bottom:1px solid var(--rule);break-after:avoid}
h3{font:600 11.5pt/1.4 Plex;margin:5mm 0 2mm;color:var(--amber-deep);break-after:avoid}
blockquote{margin:3mm 0;padding:3mm 5mm;background:#ECE4D6;border-radius:4px;color:var(--ink2)}
blockquote p{margin:0}
hr{border:0;margin:2mm 0}
table{border-collapse:collapse;width:100%;margin:2mm 0 4mm;font-size:9.5pt}
tr{break-inside:avoid}
th{font-weight:600;text-align:right;color:var(--ink2);border-bottom:1.5px solid var(--ink)}
th,td{padding:1.6mm 2mm;vertical-align:top;text-align:right}
td{border-bottom:1px solid var(--rule)}
code{font:500 9pt/1.5 ui-monospace,Menlo,monospace;direction:ltr;unicode-bidi:isolate;background:#ECE4D6;padding:0 1mm;border-radius:3px}
pre{direction:ltr;text-align:left;background:var(--ink);color:#E9E1D3;padding:3.5mm 4mm;border-radius:4px;white-space:pre-wrap;word-break:break-all;break-inside:avoid}
pre code{background:none;color:inherit;padding:0;font-size:8pt}
ul,ol{padding-inline-start:5mm}`)}</head><body>${marked.parse(md)}</body></html>`;

(async () => {
  const browser = await chromium.launch();
  const render = async (html) => {
    const tmp = path.join(root, 'scripts', '.cache-pdf.html');
    fs.writeFileSync(tmp, html);
    const p = await browser.newPage();
    await p.goto('file://' + tmp);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForLoadState('networkidle');
    const buf = await p.pdf({ format: 'A4', printBackground: true, preferCSSPageSize: true });
    await p.close(); fs.unlinkSync(tmp);
    return buf;
  };
  const parts = [await render(dark), await render(guide)];
  await browser.close();
  const out = await PDFDocument.create();
  for (const buf of parts) {
    const src = await PDFDocument.load(buf);
    (await out.copyPages(src, src.getPageIndices())).forEach((pg) => out.addPage(pg));
  }
  out.setTitle('مصطفى محمد — دليل الهوية والمونتاج');
  fs.writeFileSync(path.join(root, 'BRAND.pdf'), await out.save());
  console.log(path.join(root, 'BRAND.pdf'));
})();
