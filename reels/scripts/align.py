"""
Builds src/data/reels.json: word-level timings for every reel.

Ayah/phrase boundaries come from the pause analysis + Whisper transcription
(see analysis/asr2.json and analysis/pauses.json). Inside a phrase, words are
distributed proportionally to their phonetic weight and then snapped to the
nearest energy dip (analysis/onsets.json) when one is close enough.
"""
import json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
onsets = json.load(open(os.path.join(ROOT, "analysis", "onsets.json")))

TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
LONG = set("اوىي")


def weight(word: str) -> float:
    base = TASHKEEL.sub("", word)
    w = len(base)
    if base and base[-1] in LONG:
        w += 1.0
    w += 0.5 * word.count("ّ")  # shadda
    if base.endswith(("ون", "ين", "ير", "ور", "يم", "يل")):
        w += 1.2  # madd at the end of a phrase
    return max(w, 1.5)


def distribute(phrase, dips, min_gap=0.18, snap=0.30):
    words = phrase["text"].split()
    s, e = phrase["s"], phrase["e"]
    ws = [weight(w) for w in words]
    total = sum(ws)
    starts = [s]
    acc = 0.0
    for w in ws[:-1]:
        acc += w
        starts.append(s + (e - s) * acc / total)
    # snap to energy dips (word onsets) when close
    out = [s]
    for k in range(1, len(words)):
        t = starts[k]
        cands = [d for d in dips if abs(d[0] - t) <= snap and d[0] > out[-1] + min_gap and d[0] < e - 0.2]
        if cands:
            t = min(cands, key=lambda d: abs(d[0] - starts[k]))[0]
        out.append(max(t, out[-1] + min_gap))
    res = []
    for k, w in enumerate(words):
        ws_ = out[k]
        we_ = out[k + 1] if k + 1 < len(out) else e
        res.append({"w": w, "s": round(ws_, 3), "e": round(we_, 3)})
    return res


REELS = [
    {
        "id": "mulk-1-2", "surah": "سُورَةُ الْمُلْك", "title": "AL-MULK · 1–2",
        "clipStart": 16.85, "clipEnd": 45.30, "audio": "audio/mulk-1-2.m4a", "bg": "bg/mulk-1-2.jpg",
        "mood": "mountains",
        "ayat": [
            {"n": "١", "tr": "Blessed is He in whose hand is dominion, and He is over all things competent.",
             "phrases": [
                 {"s": 17.05, "e": 22.55, "text": "تَبَارَكَ الَّذِي بِيَدِهِ الْمُلْكُ"},
                 {"s": 22.65, "e": 28.40, "text": "وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ"},
             ]},
            {"n": "٢", "tr": "[He] who created death and life to test you [as to] which of you is best in deed — and He is the Exalted in Might, the Forgiving.",
             "phrases": [
                 {"s": 29.10, "e": 36.05, "text": "الَّذِي خَلَقَ الْمَوْتَ وَالْحَيَاةَ لِيَبْلُوَكُمْ أَيُّكُمْ"},
                 {"s": 36.40, "e": 38.45, "text": "أَحْسَنُ عَمَلًا"},
                 {"s": 39.20, "e": 44.70, "text": "وَهُوَ الْعَزِيزُ الْغَفُورُ"},
             ]},
        ],
    },
    {
        "id": "mulk-3", "surah": "سُورَةُ الْمُلْك", "title": "AL-MULK · 3",
        "clipStart": 44.80, "clipEnd": 66.60, "audio": "audio/mulk-3.m4a", "bg": "bg/mulk-3.jpg",
        "mood": "sky",
        "ayat": [
            {"n": "٣", "tr": "[And] who created seven heavens in layers. You do not see in the creation of the Most Merciful any inconsistency. So return your vision to the sky; do you see any breaks?",
             "phrases": [
                 {"s": 45.20, "e": 51.70, "text": "الَّذِي خَلَقَ سَبْعَ سَمَاوَاتٍ طِبَاقًا"},
                 {"s": 52.45, "e": 58.40, "text": "مَّا تَرَىٰ فِي خَلْقِ الرَّحْمَٰنِ مِن تَفَاوُتٍ"},
                 {"s": 59.15, "e": 65.75, "text": "فَارْجِعِ الْبَصَرَ هَلْ تَرَىٰ مِن فُطُورٍ"},
             ]},
        ],
    },
    {
        "id": "mulk-12-13", "surah": "سُورَةُ الْمُلْك", "title": "AL-MULK · 12–13",
        "clipStart": 197.45, "clipEnd": 225.60, "audio": "audio/mulk-12-13.m4a", "bg": "bg/mulk-12-13.jpg",
        "mood": "room",
        "ayat": [
            {"n": "١٢", "tr": "Indeed, those who fear their Lord unseen will have forgiveness and great reward.",
             "phrases": [
                 {"s": 197.90, "e": 206.40, "text": "إِنَّ الَّذِينَ يَخْشَوْنَ رَبَّهُم بِالْغَيْبِ"},
                 {"s": 206.90, "e": 211.50, "text": "لَهُم مَّغْفِرَةٌ وَأَجْرٌ كَبِيرٌ"},
             ]},
            {"n": "١٣", "tr": "And conceal your speech or publicize it; indeed, He is Knowing of that within the breasts.",
             "phrases": [
                 {"s": 212.10, "e": 216.40, "text": "وَأَسِرُّوا قَوْلَكُمْ أَوِ اجْهَرُوا بِهِ"},
                 {"s": 217.00, "e": 224.80, "text": "إِنَّهُ عَلِيمٌ بِذَاتِ الصُّدُورِ"},
             ]},
        ],
    },
    {
        "id": "mulk-15", "surah": "سُورَةُ الْمُلْك", "title": "AL-MULK · 15",
        "clipStart": 232.95, "clipEnd": 253.20, "audio": "audio/mulk-15.m4a", "bg": "bg/mulk-15.jpg",
        "mood": "desert",
        "ayat": [
            {"n": "١٥", "tr": "It is He who made the earth tame for you — so walk among its slopes and eat of His provision — and to Him is the resurrection.",
             "phrases": [
                 {"s": 233.40, "e": 244.65, "text": "هُوَ الَّذِي جَعَلَ لَكُمُ الْأَرْضَ ذَلُولًا فَامْشُوا فِي مَنَاكِبِهَا"},
                 {"s": 245.20, "e": 252.35, "text": "وَكُلُوا مِن رِّزْقِهِ وَإِلَيْهِ النُّشُورُ"},
             ]},
        ],
    },
    {
        "id": "mulk-19", "surah": "سُورَةُ الْمُلْك", "title": "AL-MULK · 19",
        "clipStart": 297.15, "clipEnd": 325.70, "audio": "audio/mulk-19.m4a", "bg": "bg/mulk-19.jpg",
        "mood": "birds",
        "ayat": [
            {"n": "١٩", "tr": "Do they not see the birds above them with wings outspread and folded in? None holds them aloft except the Most Merciful. Indeed He is, of all things, Seeing.",
             "phrases": [
                 {"s": 297.70, "e": 309.00, "text": "أَوَلَمْ يَرَوْا إِلَى الطَّيْرِ فَوْقَهُمْ صَافَّاتٍ وَيَقْبِضْنَ"},
                 {"s": 309.35, "e": 317.15, "text": "مَا يُمْسِكُهُنَّ إِلَّا الرَّحْمَٰنُ"},
                 {"s": 317.70, "e": 324.80, "text": "إِنَّهُ بِكُلِّ شَيْءٍ بَصِيرٌ"},
             ]},
        ],
    },
    {
        "id": "mulk-30", "surah": "سُورَةُ الْمُلْك", "title": "AL-MULK · 30",
        "clipStart": 486.25, "clipEnd": 511.00, "audio": "audio/mulk-30.m4a", "bg": "bg/mulk-30.jpg",
        "mood": "water",
        "ayat": [
            {"n": "٣٠", "tr": "Say, “Have you considered: if your water was to become sunken into the earth, then who could bring you flowing water?”",
             "phrases": [
                 {"s": 486.75, "e": 496.10, "text": "قُلْ أَرَأَيْتُمْ إِنْ أَصْبَحَ مَاؤُكُمْ غَوْرًا"},
                 {"s": 496.60, "e": 507.55, "text": "فَمَن يَأْتِيكُم بِمَاءٍ مَّعِينٍ"},
             ]},
        ],
    },
]

out = {"fps": 30, "width": 1080, "height": 1920, "reels": []}
for r in REELS:
    dips = onsets[r["id"]]["dips"]
    c0 = r["clipStart"]
    reel = {k: r[k] for k in ("id", "surah", "title", "audio", "bg", "mood")}
    reel["duration"] = round(r["clipEnd"] - r["clipStart"], 3)
    reel["bgExists"] = os.path.exists(os.path.join(ROOT, "public", r["bg"]))
    reel["ayat"] = []
    for a in r["ayat"]:
        phrases = []
        for p in a["phrases"]:
            words = distribute(p, dips)
            phrases.append({
                "s": round(p["s"] - c0, 3), "e": round(p["e"] - c0, 3),
                "words": [{"w": w["w"], "s": round(w["s"] - c0, 3), "e": round(w["e"] - c0, 3)} for w in words],
            })
        reel["ayat"].append({"n": a["n"], "tr": a["tr"], "s": phrases[0]["s"], "e": phrases[-1]["e"], "phrases": phrases})
    out["reels"].append(reel)
    print(reel["id"], reel["duration"], "s", "bg" if reel["bgExists"] else "(procedural bg)")
    for a in reel["ayat"]:
        for p in a["phrases"]:
            print("   ", " | ".join(f'{w["w"]}@{w["s"]:.2f}' for w in p["words"]))

dst = os.path.join(ROOT, "src", "data", "reels.json")
json.dump(out, open(dst, "w"), ensure_ascii=False, indent=1)
print("wrote", dst)
