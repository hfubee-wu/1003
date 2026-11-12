# -*- coding: utf-8 -*-
"""
哥窯與哥釉鑑賞 —— 30 秒直式活動宣傳短片產生器
輸出：1080x1920、30fps、H.264 + AAC（適合 IG Reels / FB / LINE / YouTube Shorts）

用法：
    python3 render.py --src <素材資料夾> --fonts <字型資料夾> --out promo.mp4
素材檔名對應見 SRC 字典；字型使用 Noto Serif CJK TC（Bold / Black）。
"""
import argparse, math, os, subprocess, wave
import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H, FPS, DUR = 1080, 1920, 30, 30.0
GOLD = (236, 206, 140)
CREAM = (248, 240, 222)
INK = (16, 30, 26)
RED = (168, 36, 30)

ap = argparse.ArgumentParser()
ap.add_argument("--src", required=True)
ap.add_argument("--fonts", required=True)
ap.add_argument("--out", default="promo.mp4")
ap.add_argument("--preview", default="", help="以逗號分隔的秒數，只輸出這些時間點的靜態畫面")
args = ap.parse_args()

SRC = {
    "scope": "28b6bcd0-image.jpg",   # 顯微鏡＋平板開片特寫
    "poster": "27a78307-image.png",  # 活動海報
    "bottle": "6693ca00-image.jpg",  # 竹節長頸瓶
    "jar": "34b80652-image.jpg",     # 水盂
    "censer": "4d259644-image.jpg",  # 三足爐
    "gu": "84b283cf-image.jpg",      # 花觚
    "vase": "1607f819-image.jpg",    # 撇口瓶
    "event1": "3819506e-image.jpg",  # 上次活動：顯微鑑定
    "event2": "b0fad940-image.jpg",  # 上次活動：理事長講解
}
img = {k: Image.open(os.path.join(args.src, v)).convert("RGB") for k, v in SRC.items()}

# --- 素材前處理 -----------------------------------------------------------
# 花觚照片右下角有相機日期戳記 → 裁掉
img["gu"] = img["gu"].crop((150, 0, 1417, 935))
# 活動照片桌上手機螢幕露出電話號碼 → 打馬賽克（個資保護）
ev2 = img["event2"]
box = (1240, 2120, 1760, 2410)
ev2.paste(ev2.crop(box).resize((26, 15)).resize((box[2] - box[0], box[3] - box[1]), Image.NEAREST)
          .filter(ImageFilter.GaussianBlur(6)), box)

F = lambda name, size: ImageFont.truetype(os.path.join(args.fonts, name), size)
BOLD, BLACK = "serif-bold.otf", "serif-black.otf"
SANS = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


# --- 工具函式 -------------------------------------------------------------
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def cover(im, w=W, h=H, cx=0.5, cy=0.5):
    """等比放大填滿 w×h，依中心點裁切。"""
    s = max(w / im.width, h / im.height)
    r = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    x = int((r.width - w) * cx)
    y = int((r.height - h) * cy)
    return r.crop((x, y, x + w, y + h))


def blur_bg(im, dark=0.42):
    bg = cover(im.resize((im.width // 4, im.height // 4)), W // 4, H // 4)
    bg = bg.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
    return ImageEnhance.Brightness(bg).enhance(dark)


def crop_rect(im, cx, cy, h):
    """以 (cx, cy) 為中心、高度 h、9:16 比例裁切並縮放成整個畫面。"""
    w = h * W / H
    return im.resize((W, H), Image.BILINEAR, box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))


def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2)
    a = np.clip((d - 0.45) * 1.4, 0, 0.75)
    return Image.fromarray((a * 255).astype("uint8"), "L")


VIG = vignette()
BLACK_FRAME = Image.new("RGB", (W, H), (0, 0, 0))


def apply_vignette(frame):
    return Image.composite(BLACK_FRAME, frame, VIG)


def text(frame, s, font, y, color=CREAM, alpha=1.0, rise=0.0, x=None, stroke=0,
         shadow=True, spacing=0, anchor="mt"):
    """在畫面上繪製文字；alpha 淡入、rise 往上浮的像素距離。"""
    if alpha <= 0.01:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    xx = W / 2 if x is None else x
    yy = y + rise
    if spacing:  # 字距：逐字繪製
        widths = [font.getlength(c) for c in s]
        total = sum(widths) + spacing * (len(s) - 1)
        cur = xx - total / 2
        for c, cw in zip(s, widths):
            if shadow:
                d.text((cur + 3, yy + 4), c, font=font, fill=(0, 0, 0, 170), anchor="lt")
            d.text((cur, yy), c, font=font, fill=color + (255,), anchor="lt",
                   stroke_width=stroke, stroke_fill=(30, 20, 10, 255))
            cur += cw + spacing
    else:
        if shadow:
            d.text((xx + 3, yy + 4), s, font=font, fill=(0, 0, 0, 170), anchor=anchor)
        d.text((xx, yy), s, font=font, fill=color + (255,), anchor=anchor,
               stroke_width=stroke, stroke_fill=(30, 20, 10, 255))
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(layer, (0, 0), layer)


def fade_in(t, start, d=0.5):
    return ease((t - start) / d)


def rule(frame, y, alpha, width=520, color=GOLD):
    """金色分隔線，中間一顆菱形。"""
    if alpha <= 0.01:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    hw = width / 2 * alpha
    c = color + (int(230 * alpha),)
    d.line((W / 2 - hw, y, W / 2 - 18, y), fill=c, width=3)
    d.line((W / 2 + 18, y, W / 2 + hw, y), fill=c, width=3)
    d.polygon([(W / 2, y - 10), (W / 2 + 10, y), (W / 2, y + 10), (W / 2 - 10, y)], fill=c)
    frame.paste(layer, (0, 0), layer)


def seal(frame, s, cx, cy, size, alpha=1.0):
    """紅色方印。"""
    if alpha <= 0.01:
        return
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 10, fill=RED + (235,))
    d.rounded_rectangle((6, 6, size - 7, size - 7), radius=size // 12, outline=CREAM + (220,), width=3)
    f = F(BLACK, int(size * 0.36))
    if len(s) == 4:
        for i, c in enumerate(s):
            d.text((size * (0.72 - 0.44 * (i // 2)), size * (0.29 + 0.42 * (i % 2))), c,
                   font=f, fill=CREAM + (255,), anchor="mm")
    else:
        f = F(BLACK, int(size * 0.5 / max(1, len(s) / 2)))
        d.text((size / 2, size / 2), s, font=f, fill=CREAM + (255,), anchor="mm")
    sc = 1 + 0.6 * (1 - ease(alpha))  # 蓋印效果：由大變小
    sz = int(size * sc)
    layer = layer.resize((sz, sz), Image.LANCZOS)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * ease(alpha))))
    frame.paste(layer, (int(cx - sz / 2), int(cy - sz / 2)), layer)


def card(frame, im, cy, width, zoom=1.0, alpha=1.0, border=GOLD):
    """把照片做成帶金邊、陰影的卡片放在畫面上，緩慢放大。"""
    w = int(width * zoom)
    h = int(im.height * w / im.width)
    c = im.resize((w, h), Image.BILINEAR)
    x, y = (W - w) // 2, int(cy - h / 2)
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((40, 40, w + 40, h + 40), fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    frame.paste(sh, (x - 40 + 8, y - 40 + 14), sh)
    frame.paste(c, (x, y))
    ImageDraw.Draw(frame).rectangle((x - 3, y - 3, x + w + 2, y + h + 2), outline=border, width=3)


# --- 預先計算的背景 ---------------------------------------------------------
POSTER_BG = ImageEnhance.Brightness(
    cover(img["poster"]).filter(ImageFilter.GaussianBlur(18))).enhance(0.26)
INK_BG = Image.new("RGB", (W, H), INK)
VESSELS = [
    ("bottle", "竹節長頸瓶", "細密開片．如冰似網"),
    ("jar", "水　盂", "溫潤釉色．淡淡冰裂"),
    ("censer", "三足爐", "大開片紋．線條分明"),
    ("gu", "花　觚", "網狀開片．口沿施彩"),
    ("vase", "撇口瓶", "通體開片．層次細膩"),
]
VBG = {k: blur_bg(img[k], 0.55) for k, *_ in VESSELS}
EV = {k: blur_bg(img[k], 0.35) for k in ("event1", "event2")}

# --- 各場景 ---------------------------------------------------------------
# 每個場景 (開始秒, 結束秒, 繪製函式)。相鄰場景重疊 0.5 秒做交叉淡化。


def s_hook(t, d):
    # 從平板上的顯微開片特寫，慢慢拉遠揭露顯微鏡實況
    k = ease(t / d)
    im = img["scope"]
    cx = 1490 + (1452 - 1490) * k
    cy = 1430 + (2050 - 1430) * k
    h = 1080 + (3900 - 1080) * k
    f = apply_vignette(crop_rect(im, cx, cy, h))
    f = ImageEnhance.Brightness(f).enhance(0.85)
    text(f, "一道裂紋", F(BLACK, 128), 560, GOLD, fade_in(t, 0.3, 0.6), rise=30 * (1 - fade_in(t, 0.3, 0.6)), stroke=2)
    text(f, "藏著千年的密碼", F(BOLD, 84), 740, CREAM, fade_in(t, 1.2, 0.6), rise=30 * (1 - fade_in(t, 1.2, 0.6)), stroke=2)
    text(f, "—— 顯微鏡下的開片紋理 ——", F(BOLD, 40), 1700, CREAM, fade_in(t, 2.6, 0.6))
    return f


def s_title(t, d):
    f = POSTER_BG.copy()
    z = 1 + 0.04 * t / d
    f = f.resize((int(W * z), int(H * z)), Image.BILINEAR).crop(
        (int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
    text(f, "中華傳統文化推廣協會", F(BOLD, 48), 430, CREAM, fade_in(t, 0.1), spacing=8)
    rule(f, 520, fade_in(t, 0.3, 0.7))
    text(f, "週四晚上", F(BOLD, 64), 580, CREAM, fade_in(t, 0.5), rise=20 * (1 - fade_in(t, 0.5)))
    a = fade_in(t, 0.9, 0.7)
    text(f, "哥窯", F(BLACK, 230), 690, GOLD, a, rise=40 * (1 - a), stroke=3)
    a2 = fade_in(t, 1.2, 0.7)
    text(f, "與哥釉", F(BLACK, 200), 950, GOLD, a2, rise=40 * (1 - a2), stroke=3)
    seal(f, "鑑賞", 900, 1050, 130, fade_in(t, 1.9, 0.35))
    rule(f, 1235, fade_in(t, 2.2, 0.6), 640)
    text(f, "古董珠寶概論", F(BOLD, 76), 1275, CREAM, fade_in(t, 2.3), spacing=14)
    seal(f, "傳承廣承", W / 2, 1560, 150, fade_in(t, 2.9, 0.35))
    return apply_vignette(f)


def make_vessel(key, name, desc, idx):
    def fn(t, d):
        f = VBG[key].copy()
        im = img[key]
        portrait = im.height > im.width
        width = 800 if portrait else 980
        cy = 1060 if portrait else 1000
        card(f, im, cy, width, zoom=1.0 + 0.05 * t / d)
        a = fade_in(t, 0.15, 0.45)
        text(f, f"開片之美　{idx}／5", F(BOLD, 40), 170, GOLD, 1.0)
        text(f, name, F(BLACK, 96), 240, CREAM, a, rise=24 * (1 - a), stroke=2)
        if not portrait:
            text(f, desc, F(BOLD, 52), 1440, GOLD, fade_in(t, 0.4, 0.45))
        else:
            text(f, desc, F(BOLD, 48), 380, GOLD, fade_in(t, 0.4, 0.45))
        return apply_vignette(f)
    return fn


def s_bridge(t, d):
    f = INK_BG.copy()
    a = fade_in(t, 0.1, 0.4)
    text(f, "哥窯？哥釉？", F(BLACK, 120), 700, GOLD, a, rise=30 * (1 - a), stroke=2)
    text(f, "真偽與年代，怎麼看？", F(BOLD, 72), 900, CREAM, fade_in(t, 0.6, 0.4))
    rule(f, 1060, fade_in(t, 0.9, 0.5), 560)
    text(f, "現場一次看懂", F(BOLD, 64), 1110, CREAM, fade_in(t, 1.0, 0.4), spacing=10)
    return apply_vignette(f)


def make_event(key, l1, l2, cy_card):
    def fn(t, d):
        f = EV[key].copy()
        card(f, img[key], cy_card, 1000, zoom=1.0 + 0.05 * t / d)
        a = fade_in(t, 0.2, 0.45)
        text(f, l1, F(BLACK, 84), 250, GOLD, a, rise=24 * (1 - a), stroke=2)
        text(f, l2, F(BOLD, 54), 1600, CREAM, fade_in(t, 0.6, 0.45))
        return apply_vignette(f)
    return fn


QR = qrcode.make("https://reurl.cc/3yN920", border=2, box_size=12).convert("RGB")


def s_end(t, d):
    f = POSTER_BG.copy()
    a = lambda s: fade_in(t, s, 0.45)
    text(f, "哥窯與哥釉鑑賞", F(BLACK, 100), 170, GOLD, a(0.0), stroke=2)
    rule(f, 320, a(0.2), 600)
    text(f, "2026 / 11 / 12（四）", F(BLACK, 80), 370, CREAM, a(0.3))
    text(f, "19:00－20:00　新舊學員聯誼", F(BOLD, 52), 505, CREAM, a(0.5))
    text(f, "20:00－21:30　鑑賞古董", F(BOLD, 52), 585, CREAM, a(0.6))
    text(f, "地點｜古亭麥當勞", F(BLACK, 64), 690, GOLD, a(0.8))
    # 可攜帶藏品
    if a(1.1) > 0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle((90, 815, W - 90, 1035), 24,
                                                fill=(16, 40, 34, int(220 * a(1.1))),
                                                outline=GOLD + (int(255 * a(1.1)),), width=3)
        f.paste(layer, (0, 0), layer)
    text(f, "歡迎攜帶藏品，現場鑑定解析", F(BOLD, 46), 845, GOLD, a(1.2))
    text(f, "玉器・瓷器・銅器・錢幣・雜項", F(BOLD, 50), 930, CREAM, a(1.3))
    # QR code
    qa = a(1.7)
    if qa > 0:
        q = QR.resize((380, 380), Image.NEAREST)
        frame = Image.new("RGB", (420, 420), CREAM)
        frame.paste(q, (20, 20))
        lay = frame.convert("RGBA")
        lay.putalpha(int(255 * qa))
        f.paste(lay, ((W - 420) // 2, 1110), lay)
    text(f, "掃碼報名　reurl.cc/3yN920", F(BOLD, 46), 1560, CREAM, a(1.9))
    text(f, "鑑古識真・交流分享・共賞文化之美", F(BOLD, 44), 1680, GOLD, a(2.4))
    seal(f, "傳承廣承", 940, 1780, 120, fade_in(t, 2.8, 0.35))
    # 片尾淡出
    out = ease((t - (d - 0.6)) / 0.6)
    if out > 0:
        f = Image.blend(f, BLACK_FRAME, out)
    return f


SCENES = [(0.0, 4.5, s_hook), (4.0, 8.8, s_title)]
t0 = 8.3
for i, (k, n, ds) in enumerate(VESSELS):
    SCENES.append((t0, t0 + 2.2, make_vessel(k, n, ds, i + 1)))
    t0 += 1.8
# t0 = 17.3
SCENES.append((t0, t0 + 2.3, s_bridge)); t0 += 1.8          # 17.3–19.6
SCENES.append((t0, t0 + 3.0, make_event("event1", "顯微放大．科學鑑定", "王理事長　親自示範解析", 930))); t0 += 2.5
SCENES.append((t0, t0 + 3.0, make_event("event2", "會員攜寶．交流分享", "新舊學員　實物上手學習", 940))); t0 += 2.5
SCENES.append((t0, DUR, s_end))                                 # 24.1–30


def render_frame(t):
    active = [(s, e, fn) for s, e, fn in SCENES if s <= t < e]
    out = None
    for s, e, fn in active:
        fr = fn(t - s, e - s)
        if out is None:
            out = fr
        else:
            out = Image.blend(out, fr, ease((t - s) / 0.5))
    if t < 0.4:
        out = Image.blend(BLACK_FRAME, out, ease(t / 0.4))
    return out


# --- 配樂：以 Karplus-Strong 合成五聲音階撥弦（類古箏）＋低音持續音 --------------
def make_music(path, sr=44100):
    n = int(sr * DUR)
    mix = np.zeros(n)
    rng = np.random.default_rng(7)

    def pluck(freq, start, dur=2.5, amp=0.35):
        N = int(sr / freq)
        buf = rng.uniform(-1, 1, N)
        L = int(sr * dur)
        out = np.zeros(L)
        for i in range(L):
            out[i] = buf[i % N]
            buf[i % N] = 0.996 * 0.5 * (buf[i % N] + buf[(i + 1) % N])
        s = int(start * sr)
        e = min(n, s + L)
        mix[s:e] += amp * out[: e - s]

    D = 293.66
    scale = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2, 9 / 4, 5 / 2, 3]  # 宮商角徵羽
    melody = [(0.4, 5), (1.2, 4), (1.6, 3), (2.4, 2), (3.2, 3), (4.0, 0),
              (4.5, 5), (5.3, 7), (5.7, 6), (6.5, 5), (7.3, 3), (8.3, 4),
              (9.1, 5), (9.9, 3), (10.7, 4), (11.5, 2), (12.3, 3), (13.1, 0),
              (13.9, 2), (14.7, 3), (15.5, 5), (16.3, 4), (17.3, 7), (17.7, 8),
              (18.5, 6), (19.3, 5), (20.1, 3), (20.9, 4), (21.7, 5), (22.5, 3),
              (23.3, 2), (24.1, 5), (24.9, 6), (25.7, 5), (26.5, 3), (27.3, 2), (28.1, 0)]
    for st, deg in melody:
        pluck(D * scale[deg], st, amp=0.32)
    for st in (4.0, 17.3, 24.1):  # 轉場重音：低八度
        pluck(D / 2, st, 3.5, 0.45)
    # 低音持續音（D + A）帶緩慢顫動
    tt = np.arange(n) / sr
    drone = 0.06 * (np.sin(2 * np.pi * 73.4 * tt) + 0.6 * np.sin(2 * np.pi * 110 * tt)) * (1 + 0.2 * np.sin(2 * np.pi * 0.25 * tt))
    mix += drone
    # 簡易殘響（多重回授延遲）
    wet = np.zeros(n)
    for dl, g in ((0.031, 0.5), (0.047, 0.4), (0.071, 0.33), (0.113, 0.25)):
        k = int(dl * sr)
        tmp = mix.copy()
        for rep in range(1, 6):
            tmp[k * rep:] += (g ** rep) * mix[: n - k * rep]
        wet += tmp
    mix = 0.6 * mix + 0.12 * wet
    env = np.minimum(1, tt / 1.0) * np.minimum(1, (DUR - tt) / 2.0)
    mix *= env
    mix = mix / np.max(np.abs(mix)) * 0.8
    pcm = (mix * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


if __name__ == "__main__" and args.preview:
    for ts in args.preview.split(","):
        render_frame(float(ts)).resize((540, 960)).save(f"preview_{ts}.jpg")
elif __name__ == "__main__":
    wav = os.path.splitext(args.out)[0] + "_music.wav"
    make_music(wav)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.out,
    ], stdin=subprocess.PIPE)
    total = int(DUR * FPS)
    for i in range(total):
        ff.stdin.write(render_frame(i / FPS).tobytes())
        if i % 90 == 0:
            print(f"frame {i}/{total}", flush=True)
    ff.stdin.close()
    ff.wait()
    os.remove(wav)
    print("done:", args.out)
