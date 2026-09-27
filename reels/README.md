# Surah Al‑Mulk Reels — Remotion

Six cinematic 9:16 reels (≤ 30 s each) cut from a full recitation of Surah Al‑Mulk, with
word‑by‑word Arabic text (gold), an English translation, and a dark spiritual‑realism look:
slow dolly‑in, volumetric light shaft, drifting fog, film grain, and a heavy vignette.

| Composition | Ayat | Length | Scene |
|---|---|---|---|
| `mulk-1-2` | 1–2 | 28.5 s | lone figure on a mountain ridge, light breaking through clouds |
| `mulk-3` | 3 | 21.8 s | figure gazing at a layered night sky |
| `mulk-12-13` | 12–13 | 28.2 s | hooded figure praying in a dim stone room |
| `mulk-15` | 15 | 20.3 s | traveller walking across a foggy desert at dawn |
| `mulk-19` | 19 | 28.6 s | birds soaring in storm light |
| `mulk-30` | 30 | 24.8 s | a single spring in a cracked, misty valley |

## Layout

```
public/
  audio/   trimmed + loudness‑normalised ayah clips (AAC)
  bg/      1080×1920 background plates (AI generated from the cinematic prompt)
  fonts/   Amiri Quran, Amiri, Scheherazade New, Cormorant Garamond
src/
  Root.tsx           registers one <Composition> per reel from src/data/reels.json
  Reel.tsx           layer stack: audio → background → light → fog → vignette → header → verse → grain → fades
  components/        Background, ProceduralScene (fallback plate), Atmosphere, Verse, Chrome
  data/reels.json    word‑level timings (generated)
scripts/
  align.py           builds reels.json from the ayah/phrase table + energy dips
  render-all.mjs     renders every composition to out/<id>.mp4
analysis/            transcription, pause/onset analysis and the reference‑video breakdown
```

## Commands

```bash
npm install
npm run studio          # preview in Remotion Studio
npm run render          # render all six reels → out/*.mp4
npm run render -- mulk-19   # render one
npm run align           # regenerate src/data/reels.json after editing timings
```

If Chrome cannot be downloaded, point Remotion at a local build:
`REMOTION_BROWSER_EXECUTABLE=/path/to/chrome npm run render`.

## Adjusting timings

Phrase boundaries live in `scripts/align.py` (`REELS` table, absolute seconds in the source
MP3). Words inside a phrase are spread by phonetic weight and snapped to detected energy dips.
Edit a phrase start/end, run `npm run align`, and re‑render.
