# 紫砂壺・千年泥韻 — 50 秒活動紀錄片 渲染腳本
import math, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from multiprocessing import Pool

S = "/tmp/claude-0/-home-user-1003/867f30ec-45de-5401-8228-619127247ba4/scratchpad"
U = "/root/.claude/uploads/867f30ec-45de-5401-8228-619127247ba4/"
W, H, FPS, DUR = 1920, 1080, 25, 50.0
FB = f"{S}/fonts/NotoSerifTC-Bold.otf"; FK = f"{S}/fonts/NotoSerifTC-Black.otf"
font = lambda p, s: ImageFont.truetype(p, s)

IMG = {k: U + v for k, v in {
    "group": "5aae7835-image.jpg", "potlid": "6866a205-image.jpg", "manseng": "3734fe33-image.jpg",
    "micro": "401c7abc-image.jpg", "pet": "4e6eb915-image.jpg", "group2": "1870ea72-image.jpg",
    "seal": "a2cec912-image.jpg", "red": "e40be55c-image.jpg", "black": "3e3ec961-image.jpg",
    "duan": "5d0be36e-image.jpg", "box": "8d6fa867-image.jpg", "party": "3dc3c399-image.jpg",
    "lineup": "f48ab722-image.jpg"}.items()}
_cache = {}
def load(k):
    if k not in _cache:
        im = ImageOps.exif_transpose(Image.open(IMG[k])).convert("RGB")
        _cache[k] = im
    return _cache[k]

def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

def kb(k, t, a, b):
    """Ken Burns：a、b = (cx, cy, w) 以圖寬為 1 的正規化座標"""
    im = load(k); iw, ih = im.size
    cx, cy, w = [lerp(a[i], b[i], ease(t)) for i in range(3)]
    cw = w * iw; ch = cw * H / W
    if ch > ih: ch = ih; cw = ch * W / H
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    fr = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    return fr, (x0, y0, cw / W)

# ---------- 水墨山水（程序生成） ----------
def ink_mountains():
    rng = np.random.default_rng(7); w, h = 2300, 1080
    paper = np.ones((h, w, 3)) * np.array([238, 228, 205]) / 255
    paper += rng.normal(0, 0.012, (h, w, 1))
    img = Image.fromarray((np.clip(paper, 0, 1) * 255).astype(np.uint8))
    for li, (base, amp, tone, blur) in enumerate([(430, 230, 150, 7), (570, 190, 105, 4), (720, 150, 65, 3), (880, 110, 30, 2)]):
        x = np.arange(w); y = np.zeros(w)
        for f in [1, 2, 4, 8, 16, 32]:
            y += amp / f * np.sin(x / w * f * math.pi * 1.3 + rng.uniform(0, 6)) * rng.uniform(.6, 1)
        y = base - np.abs(y)
        mask = Image.new("L", (w, h), 0); d = ImageDraw.Draw(mask)
        d.polygon([(0, h)] + list(zip(x[::4], y[::4])) + [(w, h)], fill=255)
        grad = np.linspace(1, 0.25, h)[:, None] * np.ones((1, w))
        m = (np.array(mask) / 255 * grad)
        ridge = np.array(mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(2))) / 255
        m = np.clip(m * 0.55 + ridge * 1.2, 0, 1)
        m = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))) / 255
        arr = np.array(img).astype(float)
        arr = arr * (1 - m[..., None] * 0.85) + tone * m[..., None] * 0.85
        img = Image.fromarray(arr.astype(np.uint8))
    # 霧氣
    fog = np.clip(1 - np.abs(np.linspace(-1, 1, h) - 0.15) * 2.2, 0, 1)[:, None, None]
    arr = np.array(img).astype(float); arr = arr * (1 - fog * .45) + 240 * fog * .45
    return Image.fromarray(arr.astype(np.uint8))

VIG = None
def vignette():
    y, x = np.mgrid[0:H, 0:W]; r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return np.clip(1 - (r - 0.55) * 0.55, 0.55, 1)[..., None]

def grade(fr, warm=True):
    a = np.asarray(fr).astype(np.float32)
    if warm: a = a * np.array([1.04, 1.0, 0.92]) + np.array([6, 2, -4])
    a = a * VIG
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# ---------- 蒸氣 ----------
rng0 = random.Random(3)
PUFFS = [(rng0.uniform(0, 3), rng0.uniform(-40, 40), rng0.uniform(.6, 1.2)) for _ in range(26)]
def steam(fr, t, x, y, scale=1.0):
    lay = Image.new("L", (600, 700), 0); d = ImageDraw.Draw(lay)
    for b, dx, s in PUFFS:
        age = (t + b) % 3.0; p = age / 3.0
        cx = 300 + dx + 40 * math.sin(age * 2 + b * 5) * p; cy = 650 - p * 600
        r = (18 + p * 70) * s; a = int(150 * math.sin(p * math.pi) ** 1.5)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a)
    lay = lay.filter(ImageFilter.GaussianBlur(28))
    if scale != 1: lay = lay.resize((int(600 * scale), int(700 * scale)))
    white = Image.new("RGB", lay.size, (255, 252, 245))
    fr.paste(white, (int(x - lay.width / 2), int(y - lay.height)), lay.point(lambda v: v * 0.55))

# ---------- 文字工具 ----------
def text(d, xy, s, f, fill=(255, 248, 230), anchor="mm", stroke=4, sfill=(25, 15, 8), alpha=1.0):
    if alpha <= 0: return
    c = tuple(int(v) for v in fill) + (int(255 * alpha),); sc = sfill + (int(200 * alpha),)
    d.text(xy, s, font=f, fill=c, anchor=anchor, stroke_width=stroke, stroke_fill=sc)

def fadein(t, t0, t1, d=0.5): return min(ease((t - t0) / d), ease((t1 - t) / d))

def seal(d, x, y, s, label, a, size=None):
    """朱紅印章"""
    if a <= 0: return
    size = size or s
    d.rounded_rectangle([x - s / 2, y - s / 2, x + s / 2, y + s / 2], radius=8, fill=(168, 28, 24, int(230 * a)))
    d.rounded_rectangle([x - s / 2 + 6, y - s / 2 + 6, x + s / 2 - 6, y + s / 2 - 6], radius=5, outline=(255, 235, 215, int(230 * a)), width=3)
    f = font(FK, int(size * 0.36))
    if len(label) == 2:
        for i, ch in enumerate(label): d.text((x, y - s * 0.2 + i * s * 0.4), ch, font=f, fill=(255, 238, 220, int(255 * a)), anchor="mm")
    else:
        d.text((x, y), label, font=font(FK, int(size * 0.5)), fill=(255, 238, 220, int(255 * a)), anchor="mm")

# ---------- 旁白字幕 ----------
VO = [  # (起始秒, 檔案, 文字)
    (0.40, "s0", "一抔泥土，淬鍊五百年。紫砂壺興於明代，到了清代與文人茶文化交融，成為兼具實用、藝術與收藏價值的傳世茶器。"),
    (9.60, "s1", "認識紫砂，先認識泥料。朱泥，色澤朱紅、質地細膩。紫泥，紫褐沉穩、砂質肌理分明。緞泥，米黃雅緻、溫潤如玉。黑鐵砂，以紫泥調配礦料燒成，深沉內斂。"),
    (22.80, "s2", "從練泥、拍打成型、修坯到入窯燒成，每一道工序，都是匠心的累積。真正的鑑賞，要懂泥料、看工藝、辨器型、究款識。"),
    (33.30, "s3", "本次由王理事長親自示範，以數位顯微鏡帶領會員觀察砂粒、印款與刻銘，在交流中體驗傳統工藝的魅力。"),
    (43.00, "s4", "中華傳統文化推廣協會，鑑古識真、交流分享。讓收藏成為學問，讓文化代代傳承！"),
]
def wavdur(p):
    with wave.open(p) as w: return w.getnframes() / w.getframerate()
def build_subs():
    import re
    subs = []
    for st, f, txt in VO:
        dur = wavdur(f"{S}/vo/{f}.wav")
        parts = [p for p in re.split(r"(?<=[，。！、])", txt) if p]
        chunks, cur = [], ""
        for p in parts:
            if len(cur) + len(p) > 17 and cur: chunks.append(cur); cur = p
            else: cur += p
            if cur.endswith(("。", "！")): chunks.append(cur); cur = ""
        if cur: chunks.append(cur)
        tot = sum(len(c) for c in chunks); t = st
        for c in chunks:
            dt = dur * len(c) / tot; subs.append((t, t + dt, c.rstrip("，、。"))); t += dt
    return subs
SUBS = None

# ---------- 分鏡 ----------
# (開始, 結束, 類型, 參數)
SHOTS = [
    (0.0, 3.9, "ink", None),
    (3.4, 9.6, "kb", ("manseng", (0.5, 0.5, 1.0), (0.51, 0.47, 0.86))),
    (9.3, 12.8, "kb", ("red", (0.47, 0.42, 1.0), (0.47, 0.40, 0.82))),
    (12.5, 16.0, "kb", ("potlid", (0.45, 0.6, 0.9), (0.42, 0.58, 0.68))),
    (15.7, 19.2, "kb", ("duan", (0.5, 0.52, 1.0), (0.48, 0.5, 0.8))),
    (18.9, 22.8, "kb", ("black", (0.5, 0.42, 1.0), (0.5, 0.38, 0.85))),
    (22.5, 25.4, "kb", ("micro", (0.55, 0.45, 0.95), (0.53, 0.38, 0.7))),
    (25.1, 28.0, "kb", ("seal", (0.5, 0.52, 1.0), (0.45, 0.52, 0.72))),
    (27.7, 30.5, "kb", ("pet", (0.5, 0.5, 1.0), (0.55, 0.42, 0.75))),
    (30.2, 33.4, "kb", ("box", (0.5, 0.55, 1.0), (0.4, 0.55, 0.75))),
    (33.1, 36.4, "kb", ("lineup", (0.5, 0.45, 1.0), (0.6, 0.42, 0.8))),
    (36.1, 39.4, "kb", ("group2", (0.55, 0.5, 0.85), (0.6, 0.48, 0.7))),
    (39.1, 42.9, "kb", ("party", (0.5, 0.45, 0.85), (0.55, 0.45, 1.0))),
    (42.6, 47.6, "kb", ("lineup", (0.62, 0.84, 0.5), (0.54, 0.75, 1.0))),
    (47.0, 50.0, "end", None),
]
INK = None
MATS = [  # 泥料字卡
    (9.5, 12.8, "朱泥", "色澤朱紅・質地細膩", "紅泥系　收縮率高、成型難度大"),
    (12.7, 16.0, "紫泥", "紫褐沉穩・砂質分明", "最常見的紫砂主力泥料"),
    (15.9, 19.2, "緞泥", "米黃雅緻・溫潤如玉", "本山綠泥 / 紫泥調配而成"),
    (19.1, 22.6, "黑鐵砂", "深沉內斂・調配礦料", "多以紫泥添加金屬氧化物呈色"),
]
FLOW = ["原礦", "練泥", "成型", "修坯", "燒成"]
PILLARS = ["懂泥料", "看工藝", "辨器型", "究款識"]

def render_shot(sh, t):
    st, en, kind, p = sh; u = (t - st) / (en - st)
    if kind == "ink":
        x = int(lerp(0, 380, ease(u))); fr = INK.crop((x, 0, x + W, H))
        return fr
    if kind == "end":
        fr = Image.new("RGB", (W, H), (24, 16, 11))
        a = np.asarray(INK.crop((150, 0, 150 + W, H))).astype(float)
        a = a * 0.18 + np.array([24, 16, 11]) * 0.82
        return Image.fromarray(a.astype(np.uint8))
    k, a, b = p; fr, tf = kb(k, u, a, b)
    if k == "manseng":  # 壺蓋上方的蒸氣
        x0, y0, sc = tf; im = load(k)
        sx = (1010 - x0) / sc; sy = (330 - y0) / sc
        pass  # 照片構圖無壺上空間，不加假蒸氣
    return grade(fr)

def frame(i):
    t = i / FPS
    act = [s for s in SHOTS if s[0] <= t < s[1]]
    base = None
    for s in act:
        fr = render_shot(s, t)
        if base is None: base = fr
        else:
            al = ease((t - s[0]) / 0.35)
            base = Image.blend(base, fr, al)
    fr = base.convert("RGBA"); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)

    # 片頭標題
    a = fadein(t, 0.3, 3.7, 0.7)
    if a > 0:
        text(d, (W / 2, 420), "紫砂壺・千年泥韻", font(FK, 128), fill=(40, 26, 16), stroke=0, alpha=a)
        text(d, (W / 2, 560), "中華傳統文化推廣協會｜紫砂壺鑑賞活動紀實", font(FB, 46), fill=(90, 50, 30), stroke=0, alpha=a)
        seal(d, W / 2 + 610, 420, 110, "傳承", a)
    a = fadein(t, 4.2, 9.2)
    if a > 0:
        d.rounded_rectangle([80, 80, 640, 170], radius=12, fill=(20, 12, 8, int(150 * a)))
        text(d, (360, 125), "明代興起　→　清代文人壺", font(FB, 40), alpha=a, stroke=0)

    # 泥料字卡
    for (s0, s1, name, l1, l2) in MATS:
        a = fadein(t, s0 + 0.2, s1 - 0.1, 0.4)
        if a <= 0: continue
        d.rounded_rectangle([90, 250, 690, 650], radius=18, fill=(22, 14, 9, int(170 * a)))
        seal(d, 190, 340, 120, name[0] if len(name) > 2 else name, a)
        text(d, (280, 340), name, font(FK, 104), anchor="lm", alpha=a, stroke=0)
        text(d, (130, 470), l1, font(FB, 44), anchor="lm", fill=(255, 225, 170), alpha=a, stroke=0)
        text(d, (130, 560), l2, font(FB, 32), anchor="lm", fill=(235, 225, 210), alpha=a, stroke=0)
    a = fadein(t, 9.4, 22.6)
    if a > 0: text(d, (W - 90, 80), "認識泥料", font(FB, 40), anchor="rm", alpha=a)

    # 工序流程
    a0 = fadein(t, 22.7, 28.2)
    if a0 > 0:
        n = len(FLOW); bw, gap = 200, 70; x0 = W / 2 - (n * bw + (n - 1) * gap) / 2
        for j, s in enumerate(FLOW):
            aj = a0 * ease((t - 22.9 - j * 0.55) / 0.4)
            if aj <= 0: continue
            x = x0 + j * (bw + gap)
            d.rounded_rectangle([x, 70, x + bw, 160], radius=14, fill=(150, 30, 24, int(220 * aj)))
            text(d, (x + bw / 2, 115), s, font(FK, 48), alpha=aj, stroke=0)
            if j < n - 1:
                cx = x + bw + gap / 2; d.polygon([(cx - 12, 98), (cx + 14, 115), (cx - 12, 132)], fill=(255, 235, 210, int(230 * aj)))
    a0 = fadein(t, 28.2, 33.2)
    if a0 > 0:
        n = 4; bw, gap = 260, 40; x0 = W / 2 - (n * bw + (n - 1) * gap) / 2
        for j, s in enumerate(PILLARS):
            aj = a0 * ease((t - 28.3 - j * 0.6) / 0.4)
            if aj <= 0: continue
            x = x0 + j * (bw + gap)
            d.rounded_rectangle([x, 70, x + bw, 165], radius=14, fill=(20, 12, 8, int(185 * aj)), outline=(214, 170, 90, int(255 * aj)), width=3)
            text(d, (x + bw / 2, 117), s, font(FK, 52), fill=(255, 222, 160), alpha=aj, stroke=0)
    for (s0, s1, lab) in [(25.3, 27.9, "數位顯微鏡下的「中國宜興」印款"), (27.9, 30.4, "茶寵・鋪砂雕塑工藝"), (30.4, 33.2, "印泥盒・刻繪梅花與款識")]:
        a = fadein(t, s0, s1, 0.35)
        if a > 0:
            d.rounded_rectangle([W - 760, 200, W - 80, 270], radius=10, fill=(20, 12, 8, int(160 * a)))
            text(d, (W - 420, 235), lab, font(FB, 34), alpha=a, stroke=0)

    # 王理事長示範 lower third
    for (s0, s1, l1, l2) in [(33.4, 39.3, "王理事長　專業示範", "數位顯微鏡・實物上手"), (39.4, 42.6, "會員交流　分享收藏", "攜帶藏品・共同研討")]:
        a = fadein(t, s0, s1, 0.4)
        if a <= 0: continue
        d.rectangle([0, 150, 720, 260], fill=(150, 30, 24, int(215 * a)))
        text(d, (80, 205), l1, font(FK, 54), anchor="lm", alpha=a, stroke=0)
        text(d, (80, 300), l2, font(FB, 36), anchor="lm", alpha=a)

    # 片尾
    a = ease((t - 47.3) / 0.8)
    if a > 0:
        text(d, (W / 2, 400), "中華傳統文化推廣協會", font(FK, 104), fill=(245, 222, 170), stroke=0, alpha=a)
        text(d, (W / 2, 540), "鑑古識真・交流分享・共賞文化之美", font(FB, 56), stroke=0, alpha=a)
        text(d, (W / 2, 640), "2026.10.08　紫砂壺鑑賞活動紀實", font(FB, 34), fill=(200, 180, 150), stroke=0, alpha=a)
        seal(d, W / 2 + 610, 400, 100, "傳承", a)

    # 旁白字幕
    for s0, s1, c in SUBS:
        if s0 <= t < s1 and t < 47.2:
            a = min(1, (t - s0) / 0.12, (s1 - t) / 0.12)
            f = font(FB, 50); tw = d.textlength(c, font=f)
            d.rounded_rectangle([W / 2 - tw / 2 - 36, 948, W / 2 + tw / 2 + 36, 1028], radius=12, fill=(10, 6, 4, int(130 * a)))
            text(d, (W / 2, 988), c, f, alpha=a, stroke=3)

    fr = Image.alpha_composite(fr, ov).convert("RGB")
    # 全片淡入淡出
    g = min(1, t / 0.6, (DUR - t) / 0.8)
    if g < 1: fr = Image.eval(fr, lambda v: int(v * max(g, 0)))
    return fr.tobytes()

def init():
    global INK, VIG, SUBS
    INK = ink_mountains(); VIG = vignette(); SUBS = build_subs()

if __name__ == "__main__":
    init()
    n = int(DUR * FPS)
    if len(sys.argv) > 1:  # 預覽單幀
        for s in sys.argv[1:]:
            Image.frombytes("RGB", (W, H), frame(int(float(s) * FPS))).save(f"{S}/prev_{s}.jpg", quality=85)
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", f"{S}/video.mp4"], stdin=subprocess.PIPE)
    with Pool(8, initializer=init) as pool:
        for i, b in enumerate(pool.imap(frame, range(n), chunksize=8)):
            ff.stdin.write(b)
            if i % 250 == 0: print(i, flush=True)
    ff.stdin.close(); ff.wait(); print("done")
