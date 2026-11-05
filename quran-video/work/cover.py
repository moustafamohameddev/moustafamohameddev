"""Vertical Instagram cover (1080x1920) for the Al-Hadid 57:21 reel."""
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
img = cv2.imread(P("scenes", "cover_bg.png"))[:, :, ::-1].astype(np.float32) / 255
img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)
# gentle sharpen after upscale
blur = cv2.GaussianBlur(img, (0, 0), 1.2)
img = np.clip(img + (img - blur) * 0.6, 0, 1)
# cinematic grade (same family as the video)
lum = (img @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
img = lum + (img - lum) * 0.92
img = 0.5 + (img * 0.95 - 0.5) * 1.06
img = img + (1 - lum) ** 2 * np.array([-0.01, 0.004, 0.02], np.float32) + lum ** 2 * np.array([0.02, 0.008, -0.018], np.float32)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
ny, nx = yy / H, (xx - W / 2) / (W / 2)
# darken behind the title block (upper half) and toward the bottom
shade = 1 - 0.50 * np.exp(-((ny - 0.37) / 0.21) ** 2) * (1 - 0.25 * nx ** 2)
shade *= 1 - 0.55 * smooth(0.72, 1.0, ny)
shade *= 1 - 0.35 * smooth(0.12, 0.0, ny)
vig = 1 - 0.35 * np.clip(nx ** 2 * 0.7 + ((ny - 0.45) / 0.6) ** 2, 0, 1.5)
img = np.clip(img * (shade * vig)[..., None], 0, 1)

canvas = img.copy()

def text_mask(text, font, size_box, anchor_xy, axes=None, stroke=0):
    im = Image.new("L", size_box, 0)
    d = ImageDraw.Draw(im)
    d.text(anchor_xy, text, font=font, fill=255, anchor="mm", direction="rtl", language="ar", stroke_width=stroke, stroke_fill=255)
    return np.asarray(im).astype(np.float32) / 255

def place(mask_full, color, alpha=1.0):
    global canvas
    a = (mask_full * alpha)[..., None]
    col = color if isinstance(color, np.ndarray) and color.ndim == 3 else np.array(color, np.float32)
    canvas = canvas * (1 - a) + col * a

def shadow(mask_full, sigma, strength, dy=0):
    global canvas
    s = cv2.GaussianBlur(mask_full, (0, 0), sigma)
    if dy:
        s = np.roll(s, dy, axis=0)
    canvas = canvas * (1 - np.clip(s * strength, 0, 1))[..., None]

def glow(mask_full, sigma, strength, color):
    global canvas
    g = cv2.GaussianBlur(mask_full, (0, 0), sigma)[..., None] * strength * np.array(color, np.float32)
    canvas = 1 - (1 - canvas) * (1 - g)

GOLD_TOP = np.array([1.00, 0.93, 0.72], np.float32)
GOLD_MID = np.array([0.96, 0.78, 0.42], np.float32)
GOLD_BOT = np.array([0.80, 0.58, 0.26], np.float32)

def gold_fill(y0, y1):
    t = np.clip((yy - y0) / (y1 - y0), 0, 1)[..., None]
    g = np.where(t < 0.5, GOLD_TOP + (GOLD_MID - GOLD_TOP) * (t / 0.5), GOLD_MID + (GOLD_BOT - GOLD_MID) * ((t - 0.5) / 0.5))
    sheen = (0.06 * np.exp(-((xx - W * 0.42) / 160) ** 2))[..., None]
    return np.clip(g + sheen, 0, 1)

# ---------------------------------------------------------------- top label
lab_font = ImageFont.truetype(P("fonts", "Amiri-Regular.ttf"), 44)
lab = text_mask("سورة الحديد", lab_font, (W, H), (W // 2, 400))
cols = np.nonzero(lab.max(0) > 0.1)[0]
line = np.zeros((H, W), np.float32)
for side in (-1, 1):
    x_in = (cols.min() - 30) if side < 0 else (cols.max() + 30)
    for i in range(170):
        x = x_in - i if side < 0 else x_in + i
        line[404, x] = (1 - i / 170) ** 1.4
        line[405, x] = (1 - i / 170) ** 1.4 * 0.5
# small diamond ornaments at line starts
for side in (-1, 1):
    cx = (cols.min() - 18) if side < 0 else (cols.max() + 18)
    pts = np.array([[cx, 398], [cx + 6, 404], [cx, 410], [cx - 6, 404]], np.int32)
    tmp = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(tmp, pts, 255, cv2.LINE_AA)
    line = np.maximum(line, tmp.astype(np.float32) / 255)
shadow(lab, 6, 0.6)
place(lab, GOLD_TOP, 0.92)
place(line, GOLD_MID, 0.85)

# ---------------------------------------------------------------- big title
title_font = ImageFont.truetype(P("fonts", "ArefRuqaa-Bold.ttf"), 300)
title = text_mask("سَابِقُوا", title_font, (W, H), (W // 2, 730))
rows = np.nonzero(title.max(1) > 0.1)[0]
shadow(title, 22, 0.75, dy=10)
shadow(title, 5, 0.5, dy=4)
glow(title, 40, 0.22, (1.0, 0.82, 0.5))
place(title, gold_fill(rows.min(), rows.max()), 1.0)
# fine highlight edge on top of letters
hl = np.clip(title - np.roll(title, 3, axis=0), 0, 1)
place(hl, np.array([1, 0.97, 0.88], np.float32), 0.35)

# ---------------------------------------------------------------- verse subtitle
sub_font = ImageFont.truetype(P("fonts", "NotoNaskhArabic-VF.ttf"), 58)
try:
    sub_font.set_variation_by_axes([560])
except Exception:
    pass
l1 = "إِلَىٰ مَغْفِرَةٍۢ مِّن رَّبِّكُمْ وَجَنَّةٍ"
l2 = "عَرْضُهَا كَعَرْضِ ٱلسَّمَآءِ وَٱلْأَرْضِ"
y_l1 = rows.max() + 105
sub = np.maximum(text_mask(l1, sub_font, (W, H), (W // 2, y_l1)), text_mask(l2, sub_font, (W, H), (W // 2, y_l1 + 100)))
shadow(sub, 10, 0.8)
shadow(sub, 3, 0.5, dy=2)
place(sub, np.array([1.0, 0.985, 0.95], np.float32), 1.0)

# ---------------------------------------------------------------- inset rounded frame (echoes the video's rounded panel)
ss = 3
fr = Image.new("L", (W * ss, H * ss), 0)
dr = ImageDraw.Draw(fr)
m = 46
dr.rounded_rectangle([m * ss, m * ss, (W - m) * ss, (H - m) * ss], 52 * ss, outline=255, width=int(2.2 * ss))
frame = np.asarray(fr.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
place(frame, GOLD_TOP, 0.42)

# ---------------------------------------------------------------- grain + out
rng = np.random.default_rng(3)
gr = cv2.resize(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None] * 0.012
canvas = np.clip(canvas + gr * (0.4 + canvas), 0, 1)
out = (canvas * 255 + 0.5).astype(np.uint8)
dst = sys.argv[1] if len(sys.argv) > 1 else P("work", "cover.jpg")
Image.fromarray(out).save(dst, quality=95, subsampling=0)
print("saved", dst)
