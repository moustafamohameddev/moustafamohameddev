"""Vertical Instagram cover (1080x1920) for the Ibrahim 42-45 reel."""
import os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
W, H = 1080, 1920

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- background
img = cv2.imread(P("scenes", "cover_ibrahim_bg.png"))[:, :, ::-1].astype(np.float32) / 255
img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)
blur = cv2.GaussianBlur(img, (0, 0), 1.2)
img = np.clip(img + (img - blur) * 0.6, 0, 1)
lum = (img @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
img = lum + (img - lum) * 0.9
img = 0.5 + (img * 0.97 - 0.5) * 1.08
img = img + (1 - lum) ** 2 * np.array([-0.01, 0.0, 0.02], np.float32) + lum ** 2 * np.array([0.03, 0.012, -0.02], np.float32)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
ny, nx = yy / H, (xx - W / 2) / (W / 2)
shade = 1 - 0.46 * np.exp(-((ny - 0.33) / 0.20) ** 2) * (1 - 0.25 * nx ** 2)
shade *= 1 - 0.50 * smooth(0.80, 1.0, ny)
shade *= 1 - 0.30 * smooth(0.10, 0.0, ny)
vig = 1 - 0.38 * np.clip(nx ** 2 * 0.7 + ((ny - 0.45) / 0.6) ** 2, 0, 1.5)
canvas = np.clip(img * (shade * vig)[..., None], 0, 1)

def text_mask(text, font, xy):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).text(xy, text, font=font, fill=255, anchor="mm", direction="rtl", language="ar")
    return np.asarray(im).astype(np.float32) / 255

def place(mask, color, alpha=1.0):
    global canvas
    a = (mask * alpha)[..., None]
    canvas = canvas * (1 - a) + np.asarray(color, np.float32) * a

def shadow(mask, sigma, strength, dy=0):
    global canvas
    s = cv2.GaussianBlur(mask, (0, 0), sigma)
    if dy:
        s = np.roll(s, dy, axis=0)
    canvas = canvas * (1 - np.clip(s * strength, 0, 1))[..., None]

def glow(mask, sigma, strength, color):
    global canvas
    g = cv2.GaussianBlur(mask, (0, 0), sigma)[..., None] * strength * np.array(color, np.float32)
    canvas = 1 - (1 - canvas) * (1 - g)

GOLD_TOP = np.array([1.00, 0.93, 0.72], np.float32)
GOLD_MID = np.array([0.96, 0.78, 0.42], np.float32)
GOLD_BOT = np.array([0.80, 0.58, 0.26], np.float32)

def gold_fill(y0, y1):
    t = np.clip((yy - y0) / (y1 - y0), 0, 1)[..., None]
    g = np.where(t < 0.5, GOLD_TOP + (GOLD_MID - GOLD_TOP) * (t / 0.5), GOLD_MID + (GOLD_BOT - GOLD_MID) * ((t - 0.5) / 0.5))
    return np.clip(g + (0.06 * np.exp(-((xx - W * 0.42) / 160) ** 2))[..., None], 0, 1)

def rows_of(m):
    r = np.nonzero(m.max(1) > 0.1)[0]
    return r.min(), r.max()

def gold_text(mask):
    r0, r1 = rows_of(mask)
    shadow(mask, 22, 0.75, dy=10)
    shadow(mask, 5, 0.5, dy=4)
    glow(mask, 40, 0.20, (1.0, 0.82, 0.5))
    place(mask, gold_fill(r0, r1), 1.0)
    place(np.clip(mask - np.roll(mask, 3, axis=0), 0, 1), (1, 0.97, 0.88), 0.35)

# ---------------------------------------------------------------- top label with ornament lines
LAB_Y = 360
lab = text_mask("سورة إبراهيم", ImageFont.truetype(P("fonts", "Amiri-Regular.ttf"), 46), (W // 2, LAB_Y))
cols = np.nonzero(lab.max(0) > 0.1)[0]
line = np.zeros((H, W), np.float32)
for side in (-1, 1):
    x_in = (cols.min() - 30) if side < 0 else (cols.max() + 30)
    for i in range(170):
        x = x_in - i if side < 0 else x_in + i
        line[LAB_Y + 4, x] = (1 - i / 170) ** 1.4
        line[LAB_Y + 5, x] = (1 - i / 170) ** 1.4 * 0.5
    cx = (cols.min() - 18) if side < 0 else (cols.max() + 18)
    tmp = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(tmp, np.array([[cx, LAB_Y - 2], [cx + 6, LAB_Y + 4], [cx, LAB_Y + 10], [cx - 6, LAB_Y + 4]], np.int32), 255, cv2.LINE_AA)
    line = np.maximum(line, tmp.astype(np.float32) / 255)
shadow(lab, 6, 0.6)
place(lab, GOLD_TOP, 0.92)
place(line, GOLD_MID, 0.85)

# ---------------------------------------------------------------- title: two gold Ruqaa lines
ruqaa = lambda s: ImageFont.truetype(P("fonts", "ArefRuqaa-Bold.ttf"), s)
t1 = text_mask("وَلَا تَحْسَبَنَّ اللهَ", ruqaa(150), (W // 2, 560))
t2 = text_mask("غَافِلًا", ruqaa(270), (W // 2, 790))
gold_text(t1)
gold_text(t2)

# ---------------------------------------------------------------- subtitle in the Mushaf font (as in the video)
sub_font = ImageFont.truetype(P("fonts", "ScheherazadeNew-Regular.ttf"), 76)
_, t2_bottom = rows_of(t2)
sub = text_mask("عَمَّا يَعْمَلُ ٱلظَّٰلِمُونَ", sub_font, (W // 2, t2_bottom + 88))
shadow(sub, 10, 0.85)
shadow(sub, 3, 0.55, dy=2)
place(sub, (1.0, 0.985, 0.95), 1.0)

# ---------------------------------------------------------------- inset rounded frame
ss = 3
fr = Image.new("L", (W * ss, H * ss), 0)
ImageDraw.Draw(fr).rounded_rectangle([46 * ss, 46 * ss, (W - 46) * ss, (H - 46) * ss], 52 * ss, outline=255, width=int(2.2 * ss))
place(np.asarray(fr.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255, GOLD_TOP, 0.42)

rng = np.random.default_rng(3)
gr = cv2.resize(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None] * 0.012
canvas = np.clip(canvas + gr * (0.4 + canvas), 0, 1)
dst = sys.argv[1] if len(sys.argv) > 1 else P("work", "cover_ibrahim.jpg")
Image.fromarray((canvas * 255 + 0.5).astype(np.uint8)).save(dst, quality=95, subsampling=0)
print("saved", dst)
