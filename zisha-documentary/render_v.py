# 紫砂壺・千年泥韻 — 9:16 直式版（1080x1920），沿用 render.py 的素材、字幕與工具函式
import sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
import render as R
from render import ease, lerp, fadein, text, seal, font, FB, FK, load, MATS, FLOW, PILLARS

W, H = 1080, 1920
R.W, R.H = W, H  # 讓 vignette / kb 等共用函式使用直式尺寸
S, FPS, DUR = R.S, R.FPS, R.DUR
PAPER = (238, 228, 205)

def cover(k, t, a, b):
    """直式滿版裁切：a、b = (cx, cy, zoom)，zoom=1 為可容納的最大裁切"""
    im = load(k); iw, ih = im.size
    cx, cy, z = [lerp(a[i], b[i], ease(t)) for i in range(3)]
    ch = ih; cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    cw /= z; ch /= z
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw); y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

_bg = {}
def fit(k, t, a, b):
    """橫式照片：模糊放大當背景，原圖完整置中（人物不被裁掉）"""
    im = load(k)
    if k not in _bg:
        bg = cover(k, 0, (0.5, 0.5, 1), (0.5, 0.5, 1)).resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(10)).resize((W, H))
        _bg[k] = Image.fromarray((np.asarray(bg) * 0.45).astype(np.uint8))
    fr = _bg[k].copy()
    cx, cy, z = [lerp(a[i], b[i], ease(t)) for i in range(3)]
    fw = int(W * z); fh = int(fw * im.height / im.width)
    fg = im.resize((fw, fh), Image.BICUBIC)
    fr.paste(fg, (int(W / 2 - cx * fw), int(860 - cy * fh)))
    return fr

INKV = None
def ink_v():
    ink = R.ink_mountains()  # 2300x1080
    bg = Image.new("RGB", (W + 300, H), PAPER)
    bg.paste(ink.crop((0, 0, W + 300, 1080)), (0, H - 1080))
    a = np.asarray(bg).astype(float)
    y = np.linspace(0, 1, H)[:, None, None]
    fog = np.clip(1 - np.abs(y - (H - 1080 + 300) / H) * 6, 0, 1)  # 銜接處霧化
    a = a * (1 - fog * .7) + np.array(PAPER) * fog * .7
    return Image.fromarray(a.astype(np.uint8))

SHOTS = [
    (0.0, 3.9, "ink", None),
    (3.4, 9.6, "fit", ("manseng", (0.5, 0.5, 1.0), (0.52, 0.5, 1.35))),
    (9.3, 12.8, "cover", ("red", (0.47, 0.45, 1.0), (0.47, 0.43, 1.2))),
    (12.5, 16.0, "cover", ("potlid", (0.45, 0.58, 1.0), (0.43, 0.58, 1.18))),
    (15.7, 19.2, "fit", ("duan", (0.5, 0.5, 1.15), (0.5, 0.5, 1.45))),
    (18.9, 22.8, "cover", ("black", (0.5, 0.42, 1.0), (0.5, 0.40, 1.15))),
    (22.5, 25.4, "cover", ("micro", (0.53, 0.5, 1.0), (0.53, 0.42, 1.2))),
    (25.1, 28.0, "cover", ("seal", (0.45, 0.5, 1.0), (0.42, 0.52, 1.25))),
    (27.7, 30.5, "cover", ("pet", (0.5, 0.5, 1.0), (0.55, 0.45, 1.2))),
    (30.2, 33.4, "fit", ("box", (0.5, 0.5, 1.2), (0.42, 0.5, 1.55))),
    (33.1, 36.4, "fit", ("lineup", (0.5, 0.5, 1.0), (0.55, 0.5, 1.2))),
    (36.1, 39.4, "fit", ("group2", (0.55, 0.5, 1.0), (0.6, 0.5, 1.25))),
    (39.1, 42.9, "fit", ("party", (0.5, 0.5, 1.25), (0.5, 0.5, 1.0))),
    (42.6, 47.6, "fit", ("lineup", (0.6, 0.8, 2.2), (0.55, 0.72, 1.0))),
    (47.0, 50.0, "end", None),
]

def render_shot(sh, t):
    st, en, kind, p = sh; u = (t - st) / (en - st)
    if kind == "ink":
        x = int(lerp(0, 300, ease(u))); return INKV.crop((x, 0, x + W, H))
    if kind == "end":
        a = np.asarray(INKV.crop((150, 0, 150 + W, H))).astype(float) * 0.18 + np.array([24, 16, 11]) * 0.82
        return Image.fromarray(a.astype(np.uint8))
    k, a, b = p
    return R.grade((cover if kind == "cover" else fit)(k, u, a, b))

def frame(i):
    t = i / FPS
    base = None
    for s in [s for s in SHOTS if s[0] <= t < s[1]]:
        fr = render_shot(s, t)
        base = fr if base is None else Image.blend(base, fr, ease((t - s[0]) / 0.35))
    fr = base.convert("RGBA"); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    C = W / 2

    a = fadein(t, 0.3, 3.7, 0.7)  # 片頭
    if a > 0:
        text(d, (C, 560), "紫砂壺", font(FK, 190), fill=(40, 26, 16), stroke=0, alpha=a)
        text(d, (C, 770), "千年泥韻", font(FK, 130), fill=(60, 36, 22), stroke=0, alpha=a)
        seal(d, C + 330, 560, 120, "傳承", a)
        text(d, (C, 920), "中華傳統文化推廣協會", font(FB, 50), fill=(90, 50, 30), stroke=0, alpha=a)
        text(d, (C, 990), "紫砂壺鑑賞活動紀實", font(FB, 44), fill=(110, 70, 45), stroke=0, alpha=a)
    a = fadein(t, 4.2, 9.2)
    if a > 0:
        d.rounded_rectangle([C - 300, 250, C + 300, 340], radius=12, fill=(20, 12, 8, int(150 * a)))
        text(d, (C, 295), "明代興起　→　清代文人壺", font(FB, 42), alpha=a, stroke=0)

    for (s0, s1, name, l1, l2) in MATS:  # 泥料字卡
        a = fadein(t, s0 + 0.2, s1 - 0.1, 0.4)
        if a <= 0: continue
        d.rounded_rectangle([70, 1080, W - 70, 1380], radius=18, fill=(22, 14, 9, int(175 * a)))
        seal(d, 170, 1165, 110, name[0] if len(name) > 2 else name, a)
        text(d, (250, 1165), name, font(FK, 96), anchor="lm", alpha=a, stroke=0)
        text(d, (110, 1270), l1, font(FB, 44), anchor="lm", fill=(255, 225, 170), alpha=a, stroke=0)
        text(d, (110, 1335), l2, font(FB, 32), anchor="lm", fill=(235, 225, 210), alpha=a, stroke=0)
    a = fadein(t, 9.4, 22.6)
    if a > 0:
        d.rounded_rectangle([C - 140, 250, C + 140, 330], radius=40, fill=(150, 30, 24, int(210 * a)))
        text(d, (C, 290), "認識泥料", font(FK, 42), alpha=a, stroke=0)

    a0 = fadein(t, 22.7, 28.2)  # 工序流程
    if a0 > 0:
        n = len(FLOW); bw, gap = 156, 44; x0 = C - (n * bw + (n - 1) * gap) / 2
        for j, s in enumerate(FLOW):
            aj = a0 * ease((t - 22.9 - j * 0.55) / 0.4)
            if aj <= 0: continue
            x = x0 + j * (bw + gap)
            d.rounded_rectangle([x, 250, x + bw, 335], radius=14, fill=(150, 30, 24, int(225 * aj)))
            text(d, (x + bw / 2, 292), s, font(FK, 44), alpha=aj, stroke=0)
            if j < n - 1:
                cx = x + bw + gap / 2; d.polygon([(cx - 10, 278), (cx + 12, 292), (cx - 10, 306)], fill=(255, 235, 210, int(230 * aj)))
    a0 = fadein(t, 28.2, 33.2)
    if a0 > 0:
        n = 4; bw, gap = 220, 26; x0 = C - (n * bw + (n - 1) * gap) / 2
        for j, s in enumerate(PILLARS):
            aj = a0 * ease((t - 28.3 - j * 0.6) / 0.4)
            if aj <= 0: continue
            x = x0 + j * (bw + gap)
            d.rounded_rectangle([x, 250, x + bw, 340], radius=14, fill=(20, 12, 8, int(190 * aj)), outline=(214, 170, 90, int(255 * aj)), width=3)
            text(d, (x + bw / 2, 295), s, font(FK, 48), fill=(255, 222, 160), alpha=aj, stroke=0)
    for (s0, s1, lab) in [(25.3, 27.9, "數位顯微鏡下的「中國宜興」印款"), (27.9, 30.4, "茶寵・鋪砂雕塑工藝"), (30.4, 33.2, "印泥盒・刻繪梅花與款識")]:
        a = fadein(t, s0, s1, 0.35)
        if a > 0:
            d.rounded_rectangle([C - 420, 380, C + 420, 455], radius=10, fill=(20, 12, 8, int(165 * a)))
            text(d, (C, 417), lab, font(FB, 38), alpha=a, stroke=0)

    for (s0, s1, l1, l2) in [(33.4, 39.3, "王理事長　專業示範", "數位顯微鏡・實物上手"), (39.4, 42.6, "會員交流　分享收藏", "攜帶藏品・共同研討")]:
        a = fadein(t, s0, s1, 0.4)
        if a <= 0: continue
        d.rectangle([0, 1180, 760, 1290], fill=(150, 30, 24, int(220 * a)))
        text(d, (70, 1235), l1, font(FK, 56), anchor="lm", alpha=a, stroke=0)
        text(d, (70, 1335), l2, font(FB, 40), anchor="lm", alpha=a)

    a = ease((t - 47.3) / 0.8)  # 片尾
    if a > 0:
        seal(d, C, 640, 130, "傳承", a)
        text(d, (C, 820), "中華傳統文化推廣協會", font(FK, 92), fill=(245, 222, 170), stroke=0, alpha=a)
        text(d, (C, 950), "鑑古識真・交流分享", font(FB, 60), stroke=0, alpha=a)
        text(d, (C, 1040), "共賞文化之美", font(FB, 60), stroke=0, alpha=a)
        text(d, (C, 1160), "2026.10.08　紫砂壺鑑賞活動紀實", font(FB, 36), fill=(200, 180, 150), stroke=0, alpha=a)

    for s0, s1, c in R.SUBS:  # 字幕（避開短影音平台底部 UI）
        if s0 <= t < s1 and t < 47.2:
            a = min(1, (t - s0) / 0.12, (s1 - t) / 0.12)
            f = font(FB, 52); tw = d.textlength(c, font=f)
            d.rounded_rectangle([C - tw / 2 - 30, 1470, C + tw / 2 + 30, 1555], radius=12, fill=(10, 6, 4, int(140 * a)))
            text(d, (C, 1512), c, f, alpha=a, stroke=3)

    fr = Image.alpha_composite(fr, ov).convert("RGB")
    g = min(1, t / 0.6, (DUR - t) / 0.8)
    if g < 1: fr = Image.eval(fr, lambda v: int(v * max(g, 0)))
    return fr.tobytes()

def init():
    global INKV
    INKV = ink_v(); R.VIG = R.vignette(); R.SUBS = R.build_subs()

if __name__ == "__main__":
    init()
    if len(sys.argv) > 1:
        for s in sys.argv[1:]:
            Image.frombytes("RGB", (W, H), frame(int(float(s) * FPS))).save(f"{S}/v_{s}.jpg", quality=85)
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", f"{S}/video_v.mp4"], stdin=subprocess.PIPE)
    with Pool(4, initializer=init) as pool:
        for i, b in enumerate(pool.imap(frame, range(int(DUR * FPS)), chunksize=8)):
            ff.stdin.write(b)
    ff.stdin.close(); ff.wait(); print("done")
