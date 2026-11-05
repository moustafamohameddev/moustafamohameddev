"""Cinematic Quran verse video renderer (Al-Hadid 57:21).

1080x1920 Reels canvas, ambient blurred background, centered 16:9 rounded panel
with depth-parallax animated paradise scenes, word-by-word synced Arabic text.
"""
import json, math, os, subprocess, sys
import numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

FPS = 30
W, H = 1080, 1920
PW, PH = 1000, 562
PX = (W - PW) // 2
PY = 650
RADIUS = 46
T0 = 1.30                     # audio trim point (recitation onset)
AUDIO_LEN = 43.75 - T0
TAIL = 1.25
DUR = AUDIO_LEN + TAIL
NFRAMES = int(round(DUR * FPS))
SRC_W, SRC_H = 1536, 864

cfg = json.load(open(P("work", "timeline.json"), encoding="utf-8"))
CARDS = [(c["text"], c["start"] - T0, c["end"] - T0) for c in cfg["cards"]]
XFADE = 1.0

# ---------------------------------------------------------------- scenes
SCENES = [
    # start/end in output time (t'), camera keyframes in source px
    dict(img="s1", start=0.0, end=9.42, z=(1.08, 1.17), o=((10, 12), (-38, -6)), A=0.07,
         b=((10, 0), (-10, -4)), sky=0.9, rays=0.10, mist=0.10, sun=(452, 260), sway=1.0),
    dict(img="s2", start=9.42, end=25.40, z=(1.07, 1.15), o=((-34, 4), (30, -10)), A=0.05,
         b=((22, 0), (-22, 0)), sky=1.6, rays=0.08, mist=0.0, sun=(254, 380), sway=1.0),
    dict(img="s3", start=25.40, end=34.75, z=(1.08, 1.16), o=((0, 18), (6, -16)), A=0.08,
         b=((0, 10), (0, -10)), sky=0.7, rays=0.07, mist=0.12, sun=(507, 196), sway=0.8),
    dict(img="s4", start=34.75, end=DUR + 0.1, z=(1.06, 1.15), o=((0, 14), (12, -18)), A=0.06,
         b=((-12, 0), (12, 0)), sky=1.0, rays=0.14, mist=0.08, sun=(967, 124), sway=0.0),
]

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def ease(u):
    u = min(max(u, 0.0), 1.0)
    return 0.45 * u + 0.55 * (0.5 - 0.5 * math.cos(math.pi * u))

# ---------------------------------------------------------------- static assets
GX, GY = np.meshgrid(np.arange(PW, dtype=np.float32) - PW / 2, np.arange(PH, dtype=np.float32) - PH / 2)
S0 = PW / SRC_W
NX, NY = GX / (PW / 2), GY / (PH / 2)
VIGNETTE = (1 - 0.30 * np.clip((NX ** 2 * 0.8 + NY ** 2 * 0.9), 0, 1.6) ** 1.3)[..., None].astype(np.float32)
TEXTDARK = (1 - 0.32 * np.exp(-(NX ** 2 / 0.55 ** 2 + NY ** 2 / 0.30 ** 2)))[..., None].astype(np.float32)

def rounded_mask(w, h, r, ss=4):
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0

PMASK = rounded_mask(PW, PH, RADIUS)
inner = np.zeros_like(PMASK)
_in = rounded_mask(PW - 4, PH - 4, RADIUS - 2)
inner[2:-2, 2:-2] = _in
BORDER = np.clip(PMASK - inner, 0, 1)

shadow = np.zeros((H, W), np.float32)
shadow[PY + 14:PY + 14 + PH, PX:PX + PW] = PMASK
shadow = cv2.GaussianBlur(shadow, (0, 0), 34)

# canvas vignette
cy, cx = np.mgrid[0:H, 0:W].astype(np.float32)
CVIG = (1 - 0.55 * np.clip(((cx - W / 2) / (W * 0.62)) ** 2 + ((cy - H * 0.48) / (H * 0.55)) ** 2, 0, 1))[..., None]
CANVAS_MUL = (CVIG * (1 - 0.62 * shadow[..., None])).astype(np.float32)

def load_scene(sc):
    img = cv2.imread(P("scenes", sc["img"] + ".png"))[:, :, ::-1].astype(np.float32) / 255.0
    npy = P("scenes", sc["img"].replace("s", "d") + ".npy")
    d = np.load(npy) if os.path.exists(npy) else cv2.imread(npy[:-4] + ".png", 0).astype(np.float32) / 255.0
    d = cv2.GaussianBlur(d, (0, 0), 2.0)
    sky = (1 - smooth(0.025, 0.09, d)).astype(np.float32)
    band = (smooth(0.03, 0.10, d) * (1 - smooth(0.28, 0.5, d))).astype(np.float32)
    near = smooth(0.55, 0.85, d).astype(np.float32)
    return img, d.astype(np.float32), sky, band, near

# fog texture (wider than panel so it can drift)
FOG = None
def fog_tex():
    rng = np.random.default_rng(7)
    h, w = PH, PW * 3
    out = np.zeros((h, w), np.float32)
    for cells, a in ((5, 1.0), (10, 0.5), (20, 0.25), (40, 0.12)):
        n = rng.random((cells, cells * 6)).astype(np.float32)
        out += a * cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    out = (out - out.min()) / (out.max() - out.min())
    return np.clip((out - 0.35) / 0.65, 0, 1) ** 1.5

# particles
RNG = np.random.default_rng(21)
NP = 46
PART = dict(x=RNG.uniform(0, PW, NP), y=RNG.uniform(0, PH, NP), vx=RNG.uniform(2, 9, NP),
            vy=RNG.uniform(-9, -2, NP), r=RNG.uniform(1.2, 3.4, NP), a=RNG.uniform(0.25, 0.75, NP),
            ph=RNG.uniform(0, 6.28, NP), f=RNG.uniform(0.15, 0.6, NP))
NB = 7
BOKEH = dict(x=RNG.uniform(0, PW, NB), y=RNG.uniform(0, PH, NB), vx=RNG.uniform(1, 5, NB),
             vy=RNG.uniform(-4, -1, NB), r=RNG.uniform(10, 22, NB), a=RNG.uniform(0.05, 0.10, NB),
             ph=RNG.uniform(0, 6.28, NB))

def draw_particles(t):
    layer = np.zeros((PH, PW), np.float32)
    def splat(x, y, r, a):
        x0, x1 = int(max(0, x - 3 * r - 1)), int(min(PW, x + 3 * r + 2))
        y0, y1 = int(max(0, y - 3 * r - 1)), int(min(PH, y + 3 * r + 2))
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        layer[y0:y1, x0:x1] += a * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r * 0.6) ** 2))
    for i in range(NP):
        x = (PART["x"][i] + PART["vx"][i] * t + 6 * math.sin(PART["f"][i] * t + PART["ph"][i])) % (PW + 40) - 20
        y = (PART["y"][i] + PART["vy"][i] * t + 4 * math.cos(0.7 * PART["f"][i] * t + PART["ph"][i])) % (PH + 40) - 20
        tw = 0.6 + 0.4 * math.sin(1.7 * PART["f"][i] * t * 3 + PART["ph"][i])
        splat(x, y, PART["r"][i], PART["a"][i] * tw)
    for i in range(NB):
        x = (BOKEH["x"][i] + BOKEH["vx"][i] * t) % (PW + 80) - 40
        y = (BOKEH["y"][i] + BOKEH["vy"][i] * t) % (PH + 80) - 40
        splat(x, y, BOKEH["r"][i], BOKEH["a"][i] * (0.7 + 0.3 * math.sin(0.5 * t + BOKEH["ph"][i])))
    return layer

# ---------------------------------------------------------------- text cards
FONT_PATH = P("fonts", "NotoNaskhArabic-VF.ttf")
FONT_SIZE = 72

def make_card(text):
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    try:
        font.set_variation_by_axes([620])
    except Exception:
        pass
    pad = 60
    tmp = Image.new("L", (10, 10))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font, direction="rtl", language="ar")
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    a = Image.new("L", (w, h), 0)
    ImageDraw.Draw(a).text((pad - bb[0], pad - bb[1]), text, font=font, fill=255, direction="rtl", language="ar")
    alpha = np.asarray(a).astype(np.float32) / 255.0
    sh = np.clip(cv2.GaussianBlur(alpha, (0, 0), 6) * 0.9 + cv2.GaussianBlur(alpha, (0, 0), 18) * 0.45, 0, 1)
    glow = cv2.GaussianBlur(alpha, (0, 0), 16) * 0.25
    # vertical centre of the text body (ignore diacritics extremes): use alpha mass centroid
    ys = np.nonzero(alpha.sum(1) > 0)[0]
    cyy = float((alpha.sum(1) * np.arange(h)).sum() / alpha.sum())
    return dict(alpha=alpha, shadow=sh, glow=glow, w=w, h=h, cy=cyy)

CARD_IMG = {}

def card_alpha(t, s, e):
    fi = smooth(s - 0.10, s + 0.22, t)
    fo = 1 - smooth(e - 0.16, e + 0.06, t)
    return float(fi * fo), float(smooth(s - 0.10, s + 0.40, t))

# ---------------------------------------------------------------- per-scene frame
SC_DATA = {}

def scene_frame(k, t):
    sc = SCENES[k]
    if k not in SC_DATA:
        SC_DATA[k] = load_scene(sc)
    img, d, sky, band, near = SC_DATA[k]
    span = sc["end"] - sc["start"] + XFADE
    u = ease((t - (sc["start"] - XFADE / 2)) / span)
    tl = t - (sc["start"] - XFADE / 2)
    lerp = lambda a, b: a + (b - a) * u
    z = lerp(*sc["z"])
    ox, oy = lerp(sc["o"][0][0], sc["o"][1][0]), lerp(sc["o"][0][1], sc["o"][1][1])
    bx, by = lerp(sc["b"][0][0], sc["b"][1][0]), lerp(sc["b"][0][1], sc["b"][1][1])
    A = sc["A"] * u
    cxs, cys = SRC_W / 2 + ox, SRC_H / 2 + oy
    base_x = GX / (S0 * z)
    base_y = GY / (S0 * z)
    disp = cv2.remap(d, (cxs + base_x).astype(np.float32), (cys + base_y).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    for _ in range(2):
        mx = cxs + base_x / (1 + A * disp) + bx * disp
        my = cys + base_y / (1 + A * disp) + by * disp
        disp = cv2.remap(d, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    mx = cxs + base_x / (1 + A * disp) + bx * disp
    my = cys + base_y / (1 + A * disp) + by * disp
    # gentle wind sway in the near foreground
    if sc["sway"]:
        nm = cv2.remap(near, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        sw = (np.sin(1.3 * t + my * 0.045 + mx * 0.012) * 0.7 + np.sin(2.1 * t + mx * 0.03) * 0.4) * sc["sway"]
        mx = mx + sw * nm
    mx = mx.astype(np.float32); my = my.astype(np.float32)
    frame = cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # cloud drift: sample the sky shifted, only where both points are sky
    if sc["sky"]:
        sh = sc["sky"] * tl
        skm = cv2.remap(sky, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        skm2 = cv2.remap(sky, mx - sh, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        moved = cv2.remap(img, mx - sh, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        wsk = (skm * skm2)[..., None]
        frame = frame * (1 - wsk) + moved * wsk
    # drifting mist in the mid distance
    if sc["mist"]:
        global FOG
        if FOG is None:
            FOG = fog_tex()
        off = int(tl * 9) % PW
        fg = FOG[:, off:off + PW]
        bm = cv2.remap(band, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fa = (sc["mist"] * fg * bm)[..., None]
        frame = frame * (1 - fa) + np.array([1.0, 0.93, 0.84], np.float32) * fa
    # sun glow + god rays (screen blend)
    sx = (sc["sun"][0] - cxs) * S0 * z + PW / 2
    sy = (sc["sun"][1] - cys) * S0 * z + PH / 2
    q = 4
    gxs, gys = GX[::q, ::q], GY[::q, ::q]
    dx, dy = gxs + PW / 2 - sx, gys + PH / 2 - sy
    r = np.sqrt(dx * dx + dy * dy) + 1e-3
    th = np.arctan2(dy, dx)
    rays = (0.5 + 0.5 * np.sin(th * 23 + 0.35 * t)) * (0.5 + 0.5 * np.sin(th * 37 - 0.22 * t + 1.3)) * (0.6 + 0.4 * np.sin(th * 11 + 0.15 * t))
    pulse = 1 + 0.08 * math.sin(t * 0.9)
    glow = np.exp(-r / 260.0) * 0.20 * pulse + rays * np.exp(-r / 420.0) * sc["rays"] * (1 - np.exp(-r / 40.0))
    glow = cv2.resize(glow.astype(np.float32), (PW, PH), interpolation=cv2.INTER_LINEAR)
    glow = glow[..., None] * np.array([1.0, 0.86, 0.62], np.float32)
    frame = 1 - (1 - frame) * (1 - glow)
    return frame

def grade(f):
    f = np.clip(f, 0, 1)
    lum = (f @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    f = lum + (f - lum) * 0.90                                   # slight desaturation
    f = f * 0.94
    f = 0.5 + (f - 0.5) * 1.06                                   # contrast
    sh = (1 - lum) ** 2
    hl = lum ** 2
    f = f + sh * np.array([-0.010, 0.004, 0.022], np.float32) + hl * np.array([0.020, 0.008, -0.018], np.float32)
    f = f * VIGNETTE * TEXTDARK
    return np.clip(f, 0, 1)

def render_frame(n):
    t = n / FPS
    # scene mix
    act = []
    for k, sc in enumerate(SCENES):
        a = smooth(sc["start"] - XFADE / 2, sc["start"] + XFADE / 2, t) if k > 0 else 1.0
        b = 1 - smooth(sc["end"] - XFADE / 2, sc["end"] + XFADE / 2, t) if k < len(SCENES) - 1 else 1.0
        w = a * b
        if w > 0.001:
            act.append((k, w))
    tot = sum(w for _, w in act)
    panel = None
    for k, w in act:
        fr = scene_frame(k, t) * (w / tot)
        panel = fr if panel is None else panel + fr
    # light bloom during dissolves
    for k, sc in enumerate(SCENES[1:], 1):
        bump = math.exp(-((t - sc["start"]) / 0.32) ** 2) * 0.10
        if bump > 0.002:
            panel = 1 - (1 - panel) * (1 - bump * np.array([1.0, 0.9, 0.75], np.float32))
    pl = draw_particles(t)
    panel = 1 - (1 - panel) * (1 - (pl[..., None] * np.array([1.0, 0.94, 0.80], np.float32)))
    panel = grade(panel)

    # ambient background from the panel
    small = cv2.resize(panel, (96, 54), interpolation=cv2.INTER_AREA)
    cw = int(round(54 * W / H))
    crop = small[:, (96 - cw) // 2:(96 - cw) // 2 + cw]
    crop = cv2.GaussianBlur(crop, (0, 0), 1.6)
    bg = cv2.resize(crop, (270, 480), interpolation=cv2.INTER_CUBIC)
    bg = cv2.GaussianBlur(bg, (0, 0), 7)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR)
    lum = bg.mean(2, keepdims=True)
    bg = (lum + (bg - lum) * 0.75) * 0.40
    canvas = bg * CANVAS_MUL

    # text
    tp = np.zeros((PH, PW), np.float32)
    sp = np.zeros((PH, PW), np.float32)
    for i, (txt, s, e) in enumerate(CARDS):
        al, rise = card_alpha(t, s, e)
        if al <= 0.003:
            continue
        c = CARD_IMG[i]
        oyy = int(round((1 - rise) * 8))
        x0 = PW // 2 - c["w"] // 2
        y0 = int(PH / 2 - c["cy"]) + oyy
        ys0, ys1 = max(0, y0), min(PH, y0 + c["h"])
        xs0, xs1 = max(0, x0), min(PW, x0 + c["w"])
        cy0, cx0 = ys0 - y0, xs0 - x0
        tp[ys0:ys1, xs0:xs1] = np.maximum(tp[ys0:ys1, xs0:xs1], al * c["alpha"][cy0:cy0 + ys1 - ys0, cx0:cx0 + xs1 - xs0])
        sp[ys0:ys1, xs0:xs1] = np.maximum(sp[ys0:ys1, xs0:xs1], al * c["shadow"][cy0:cy0 + ys1 - ys0, cx0:cx0 + xs1 - xs0])
        g = al * c["glow"][cy0:cy0 + ys1 - ys0, cx0:cx0 + xs1 - xs0]
        panel[ys0:ys1, xs0:xs1] = 1 - (1 - panel[ys0:ys1, xs0:xs1]) * (1 - g[..., None] * np.array([1, .9, .7], np.float32) * 0.5)
    panel = panel * (1 - sp[..., None] * 0.55)
    panel = panel * (1 - tp[..., None]) + np.array([1.0, 0.985, 0.95], np.float32) * tp[..., None]

    # composite panel
    m = PMASK[..., None]
    reg = canvas[PY:PY + PH, PX:PX + PW]
    reg = reg * (1 - m) + panel * m
    reg = reg * (1 - BORDER[..., None] * 0.22) + BORDER[..., None] * 0.22
    canvas[PY:PY + PH, PX:PX + PW] = reg
    canvas = canvas * (1 - LABEL_A) + LABEL_A * LABEL_COLOR

    # global fades
    fin = smooth(0.0, 0.45, t)
    fout = 1 - smooth(DUR - 1.35, DUR - 0.05, t)
    canvas = canvas * (fin * fout)
    # grain
    gr = GRAIN[n % len(GRAIN)]
    canvas = canvas + gr * (0.4 + canvas)
    out = np.clip(canvas * 255 + 0.5, 0, 255).astype(np.uint8)
    return out.tobytes()

# label under the panel
def make_label():
    font = ImageFont.truetype(P("fonts", "Amiri-Regular.ttf"), 40)
    im = Image.new("L", (W, 120), 0)
    d = ImageDraw.Draw(im)
    txt = "سورة الحديد ﴿٢١﴾"
    d.text((W // 2, 60), txt, font=font, fill=255, anchor="mm", direction="rtl", language="ar")
    a = np.zeros((H, W), np.float32)
    y = PY + PH + 62
    arr = np.asarray(im).astype(np.float32) / 255
    cols = np.nonzero(arr.max(0) > 0.1)[0]
    a[y - 60:y + 60] = arr * 0.66
    # thin fading ornament lines either side of the label
    gap, ln = 26, 150
    for side in (-1, 1):
        x_in = cols.min() - gap if side < 0 else cols.max() + gap
        xs = np.arange(ln)
        xx = (x_in - xs) if side < 0 else (x_in + xs)
        fade = (1 - xs / ln) ** 1.5 * 0.40
        a[y + 1, xx] = fade
        a[y + 2, xx] = fade * 0.5
    return a[..., None]

LABEL_A = make_label()
_gr = np.random.default_rng(5)
GRAIN = [cv2.resize(_gr.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.010 for _ in range(12)]
LABEL_COLOR = np.array([1.0, 0.95, 0.86], np.float32)

def init():
    for i, (txt, s, e) in enumerate(CARDS):
        CARD_IMG[i] = make_card(txt)

init()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    if mode == "stills":
        ts = [float(x) for x in sys.argv[2:]]
        for t in ts:
            n = int(round(t * FPS))
            fr = np.frombuffer(render_frame(n), np.uint8).reshape(H, W, 3)
            cv2.imwrite(P("work", f"still_{t:05.2f}.jpg"), fr[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 92])
        sys.exit()
    out = sys.argv[2] if len(sys.argv) > 2 else P("work", "video_noaudio.mp4")
    nf = NFRAMES if mode == "full" else int(float(mode) * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                           "-pix_fmt", "yuv420p", "-tune", "film", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for i, buf in enumerate(pool.imap(render_frame, range(nf), chunksize=4)):
            ff.stdin.write(buf)
            if i % 60 == 0:
                print(f"frame {i}/{nf}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", out)
