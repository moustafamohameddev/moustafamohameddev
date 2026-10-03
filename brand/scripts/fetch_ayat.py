#!/usr/bin/env python3
"""Fetch the exact on-screen text for a range of ayat.

    python3 brand/scripts/fetch_ayat.py 94 5 6          # surah 94, ayat 5..6
    python3 brand/scripts/fetch_ayat.py 18 10 10 --json  # machine-readable

Arabic: King Fahd Complex (KFGQPC) Hafs text, version 18 — the same version as
fonts/UthmanicHafs1Ver18.ttf, so every mark has a glyph. The ayah number is
part of the text and the font draws it inside the ayah-end ornament.
English: The Clear Quran, Dr. Mustafa Khattab ("Allah" edition).

Never type, paraphrase or auto-transcribe ayat. Always take them from here.
Standard library only; the Arabic dataset is cached next to this script.
"""
import json, os, sys, urllib.request

HAFS_URL = "https://raw.githubusercontent.com/thetruetruth/quran-data-kfgqpc/main/hafs/data/hafsData_v18.json"
TR_URL = "https://raw.githubusercontent.com/fawazahmed0/quran-api/1/editions/eng-mustafakhattaba/{s}/{a}.json"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-hafsData_v18.json")


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8")


def hafs():
    if not os.path.exists(CACHE):
        with open(CACHE, "w", encoding="utf-8") as f:
            f.write(get(HAFS_URL))
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        sys.exit(__doc__)
    surah, first, last = map(int, args)
    rows = [r for r in hafs() if r["sora"] == surah and first <= r["aya_no"] <= last]
    out = []
    for r in sorted(rows, key=lambda r: r["aya_no"]):
        tr = json.loads(get(TR_URL.format(s=surah, a=r["aya_no"])))["text"]
        out.append({
            "key": f"{surah}:{r['aya_no']}",
            "surah_ar": r["sora_name_ar"],
            "surah_en": r["sora_name_en"],
            "ayah": r["aya_text"].replace(" ", " "),
            "translation": tr,
        })
    if "--json" in sys.argv:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for o in out:
            print(f"{o['key']}  {o['surah_ar']}\n  {o['ayah']}\n  {o['translation']}\n")


if __name__ == "__main__":
    main()
