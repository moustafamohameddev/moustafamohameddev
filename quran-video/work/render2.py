"""Reel renderer for a supplied background video + recitation (Al-Ma'idah 5:23).

1080x1920 canvas, ambient blurred background, centered 16:9 rounded panel showing the
source footage, word-synced Uthmani text, label under the panel.
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, "fonts")

FPS = 30
W, H = 1080, 1920
PW, PH = 1000, 562
PX = (W - PW) // 2
PY = 650
RADIUS = 46

cfg = json.load(open(os.path.join(HERE, os.environ.get("TIMELINE", "timeline2.json")), encoding="utf-8"))
STYLE = cfg.get("style", {})
T0 = cfg["trim"]                 # audio trim point (recitation onset)
AUDIO_LEN = cfg["audio_len"] - T0
TAIL = 1.2
DUR = AUDIO_LEN + TAIL
NFRAMES = int(round(DUR * FPS))
CARDS = [(c["text"], c["start"] - T0, c["end"] - T0) for c in cfg["cards"]]
LABEL = cfg["label"]

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

GX, GY = np.meshgrid(np.arange(PW, dtype=np.float32) - PW / 2, np.arange(PH, dtype=np.float32) - PH / 2)
NX, NY = GX / (PW / 2), GY / (PH / 2)
VIGNETTE = (1 - 0.28 * np.clip((NX ** 2 * 0.8 + NY ** 2 * 0.9), 0, 1.6) ** 1.3)[..., None].astype(np.float32)
if cfg.get("style", {}).get("pos") == "bottom":
    TEXTDARK = (1 - 0.38 * smooth(0.25, 1.0, NY))[..., None].astype(np.float32)
else:
    TEXTDARK = (1 - 0.18 * np.exp(-(NX ** 2 / 0.55 ** 2 + NY ** 2 / 0.30 ** 2)))[..., None].astype(np.float32)

def rounded_mask(w, h, r, ss=4):
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0

PMASK = rounded_mask(PW, PH, RADIUS)
inner = np.zeros_like(PMASK)
inner[2:-2, 2:-2] = rounded_mask(PW - 4, PH - 4, RADIUS - 2)
BORDER = np.clip(PMASK - inner, 0, 1)[..., None]

shadow = np.zeros((H, W), np.float32)
shadow[PY + 14:PY + 14 + PH, PX:PX + PW] = PMASK
shadow = cv2.GaussianBlur(shadow, (0, 0), 34)
cy, cx = np.mgrid[0:H, 0:W].astype(np.float32)
CVIG = (1 - 0.55 * np.clip(((cx - W / 2) / (W * 0.62)) ** 2 + ((cy - H * 0.48) / (H * 0.55)) ** 2, 0, 1))[..., None]
CANVAS_MUL = (CVIG * (1 - 0.62 * shadow[..., None])).astype(np.float32)

# ---------------------------------------------------------------- text
def make_card(text, size=None):
    size = size or STYLE.get("size", 72)
    font = ImageFont.truetype(os.path.join(FONTS, STYLE.get("font", "NotoNaskhArabic-VF.ttf")), size)
    wght = STYLE.get("wght", 620 if "NotoNaskh" in STYLE.get("font", "NotoNaskhArabic-VF.ttf") else None)
    if wght:
        try:
            font.set_variation_by_axes([wght])
        except Exception:
            pass
    pad = 60
    bb = ImageDraw.Draw(Image.new("L", (10, 10))).textbbox((0, 0), text, font=font, direction="rtl", language="ar")
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    a = Image.new("L", (w, h), 0)
    ImageDraw.Draw(a).text((pad - bb[0], pad - bb[1]), text, font=font, fill=255, direction="rtl", language="ar")
    alpha = np.asarray(a).astype(np.float32) / 255.0
    sh = np.clip(cv2.GaussianBlur(alpha, (0, 0), 6) * 0.9 + cv2.GaussianBlur(alpha, (0, 0), 18) * 0.45, 0, 1)
    glow = cv2.GaussianBlur(alpha, (0, 0), 16) * STYLE.get("glow", 0.30)
    cyy = float((alpha.sum(1) * np.arange(h)).sum() / alpha.sum())
    return dict(alpha=alpha, shadow=sh, glow=glow, w=w, h=h, cy=cyy)

CARD_IMG = [make_card(t) for t, _, _ in CARDS]

FIN, FOUT, RISE = STYLE.get("fade_in", 0.32), STYLE.get("fade_out", 0.22), STYLE.get("rise", 8)
TEXT_CY = PH - STYLE["bottom_margin"] if STYLE.get("pos") == "bottom" else PH / 2
TEXT_ALPHA = STYLE.get("opacity", 1.0)

def card_alpha(t, s, e):
    fi = smooth(s - 0.10, s - 0.10 + FIN, t)
    fo = 1 - smooth(e - FOUT + 0.06, e + 0.06, t)
    return float(fi * fo * TEXT_ALPHA), float(smooth(s - 0.10, s + 0.40, t))

def make_label():
    font = ImageFont.truetype(os.path.join(FONTS, "Amiri-Regular.ttf"), 40)
    im = Image.new("L", (W, 120), 0)
    ImageDraw.Draw(im).text((W // 2, 60), LABEL, font=font, fill=255, anchor="mm", direction="rtl", language="ar")
    a = np.zeros((H, W), np.float32)
    y = PY + PH + 62
    arr = np.asarray(im).astype(np.float32) / 255
    cols = np.nonzero(arr.max(0) > 0.1)[0]
    a[y - 60:y + 60] = arr * 0.66
    for side in (-1, 1):
        x_in = cols.min() - 26 if side < 0 else cols.max() + 26
        xs = np.arange(150)
        xx = (x_in - xs) if side < 0 else (x_in + xs)
        fade = (1 - xs / 150) ** 1.5 * 0.40
        a[y + 1, xx] = fade
        a[y + 2, xx] = fade * 0.5
    return a[..., None]

LABEL_A = make_label()
LABEL_COLOR = np.array([1.0, 0.95, 0.86], np.float32)
_gr = np.random.default_rng(5)
GRAIN = [cv2.resize(_gr.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None] * 0.010 for _ in range(12)]

def grade(f):
    f = np.clip(f, 0, 1)
    f = f ** 0.93                                               # lift the deep shadows a touch
    lum = (f @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    f = lum + (f - lum) * 0.95
    f = 0.5 + (f - 0.5) * 1.04
    f = f + (1 - lum) ** 2 * np.array([-0.006, 0.002, 0.012], np.float32) + lum ** 2 * np.array([0.02, 0.008, -0.015], np.float32)
    return np.clip(f * VIGNETTE * TEXTDARK, 0, 1)

def render_frame(args):
    n, raw = args
    t = n / FPS
    panel = np.frombuffer(raw, np.uint8).reshape(PH, PW, 3).astype(np.float32) / 255.0
    panel = grade(panel)

    small = cv2.resize(panel, (96, 54), interpolation=cv2.INTER_AREA)
    cw = int(round(54 * W / H))
    crop = cv2.GaussianBlur(small[:, (96 - cw) // 2:(96 - cw) // 2 + cw], (0, 0), 1.6)
    bg = cv2.GaussianBlur(cv2.resize(crop, (270, 480), interpolation=cv2.INTER_CUBIC), (0, 0), 7)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)
    lum = bg.mean(2, keepdims=True)
    bg = (lum + (bg - lum) * 0.8) * 0.55
    canvas = bg * CANVAS_MUL

    tp = np.zeros((PH, PW), np.float32)
    sp = np.zeros((PH, PW), np.float32)
    for i, (txt, s, e) in enumerate(CARDS):
        al, rise = card_alpha(t, s, e)
        if al <= 0.003:
            continue
        c = CARD_IMG[i]
        x0 = PW // 2 - c["w"] // 2
        y0 = int(TEXT_CY - c["cy"]) + int(round((1 - rise) * RISE))
        ys0, ys1 = max(0, y0), min(PH, y0 + c["h"])
        xs0, xs1 = max(0, x0), min(PW, x0 + c["w"])
        cy0, cx0 = ys0 - y0, xs0 - x0
        sl = (slice(cy0, cy0 + ys1 - ys0), slice(cx0, cx0 + xs1 - xs0))
        tp[ys0:ys1, xs0:xs1] = np.maximum(tp[ys0:ys1, xs0:xs1], al * c["alpha"][sl])
        sp[ys0:ys1, xs0:xs1] = np.maximum(sp[ys0:ys1, xs0:xs1], al * c["shadow"][sl])
        g = al * c["glow"][sl]
        panel[ys0:ys1, xs0:xs1] = 1 - (1 - panel[ys0:ys1, xs0:xs1]) * (1 - g[..., None] * np.array([1, .88, .66], np.float32) * 0.5)
    panel = panel * (1 - sp[..., None] * 0.55)
    panel = panel * (1 - tp[..., None]) + np.array([1.0, 0.985, 0.95], np.float32) * tp[..., None]

    m = PMASK[..., None]
    reg = canvas[PY:PY + PH, PX:PX + PW]
    reg = reg * (1 - m) + panel * m
    reg = reg * (1 - BORDER * 0.22) + BORDER * 0.22
    canvas[PY:PY + PH, PX:PX + PW] = reg
    canvas = canvas * (1 - LABEL_A) + LABEL_A * LABEL_COLOR

    canvas = canvas * (smooth(0.0, 0.45, t) * (1 - smooth(DUR - 1.3, DUR - 0.05, t)))
    canvas = canvas + GRAIN[n % len(GRAIN)] * (0.4 + canvas)
    return np.clip(canvas * 255 + 0.5, 0, 255).astype(np.uint8).tobytes()

def frames(src):
    # source → 30fps, upscaled to panel size with lanczos + light sharpen
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", src, "-t", f"{DUR:.3f}",
                          "-vf", f"fps={FPS},scale={PW}:{PH}:flags=lanczos,unsharp=5:5:0.6:5:5:0.0",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = 0
    last = None
    while n < NFRAMES:
        raw = p.stdout.read(PW * PH * 3)
        if len(raw) < PW * PH * 3:
            raw = last          # source shorter than needed: hold last frame
        last = raw
        yield n, raw
        n += 1
    p.stdout.close(); p.wait()

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "full"
    if mode == "stills":
        want = {int(round(float(x) * FPS)) for x in sys.argv[4:]}
        for n, raw in frames(src):
            if n in want:
                fr = np.frombuffer(render_frame((n, raw)), np.uint8).reshape(H, W, 3)
                cv2.imwrite(os.path.join(HERE, f"still_{n / FPS:05.2f}.jpg"), fr[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
                want.discard(n)
            if not want:
                break
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render_frame, frames(src), chunksize=4)):
            ff.stdin.write(buf)
            if i % 300 == 0:
                print(f"frame {i}/{NFRAMES}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", out)
