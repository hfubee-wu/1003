# -*- coding: utf-8 -*-
"""主剪輯程式：PIL/numpy 逐格合成 → 以管線送入 FFmpeg (libx264 + AAC) 輸出 1080x1920 / 30fps / 50s。
用法：
  python build_video.py                 # 輸出完整影片與 SRT
  python build_video.py --stills 1,6,13 # 只輸出指定秒數的檢查用靜態圖
"""
import os, sys, json, subprocess, glob, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from timeline import ROOT, W, H, FPS, DUR, SHOTS, TITLES, NARRATION

R = lambda p: os.path.join(ROOT, p)
F = lambda w, s: ImageFont.truetype(R(f'fonts/NotoSerifCJKtc-{w}.otf'), s)
GOLD, CREAM, INK, RED = (240, 205, 130), (245, 236, 214), (22, 58, 50), (170, 38, 30)
rng = np.random.default_rng(11)
ease = lambda x: (lambda x: x*x*(3-2*x))(min(1.0, max(0.0, x)))
lerp = lambda a, b, u: a+(b-a)*u

# ---------- 文字圖層 ----------
def text_layer(lines, pad=30, spacing=18, shadow=True, align='center'):
    """lines: [(文字, 字型, 顏色)] → 帶陰影的 RGBA 圖層"""
    d = ImageDraw.Draw(Image.new('RGBA', (8, 8)))
    sizes = [d.textbbox((0, 0), t, font=f) for t, f, c in lines]
    w = max(b[2] for b in sizes)+pad*2; h = sum(b[3] for b in sizes)+spacing*(len(lines)-1)+pad*2
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); y = pad
    for (t, f, c), b in zip(lines, sizes):
        x = (w-b[2])//2 if align == 'center' else pad
        dr.text((x, y), t, font=f, fill=c); y += b[3]+spacing
    if shadow:
        a = im.split()[3]
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(a.filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v*2.2))))
        sh2 = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh2.putalpha(a.filter(ImageFilter.GaussianBlur(2)))
        im = Image.alpha_composite(Image.alpha_composite(sh, sh2), im)
    return im

def paste(frame, layer, cx, cy, alpha=1.0):
    if alpha <= 0.003: return
    if alpha < 0.997:
        layer = layer.copy(); layer.putalpha(layer.split()[3].point(lambda v: int(v*alpha)))
    frame.paste(layer, (int(cx-layer.width/2), int(cy-layer.height/2)), layer)

def seal(txt='傳承', s=150):
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, s-1, s-1), 16, fill=RED+(235,))
    d.rounded_rectangle((9, 9, s-10, s-10), 10, outline=CREAM+(230,), width=3)
    f = F('Black', int(s*0.36))
    for i, ch in enumerate(txt):
        b = d.textbbox((0, 0), ch, font=f)
        d.text(((s-b[2])/2, s*0.10+i*s*0.40-b[1]*0.2), ch, font=f, fill=CREAM)
    n = (rng.random((s, s)) > 0.06).astype(np.uint8)*255  # 印泥斑駁
    a = np.minimum(np.asarray(im.split()[3]), np.asarray(Image.fromarray(n).filter(ImageFilter.GaussianBlur(0.6))))
    im.putalpha(Image.fromarray(a)); return im

# ---------- 程式生成的水墨山水（情境畫面，非實拍） ----------
def smooth_noise(n, scale, amp):
    k = rng.normal(0, 1, n//scale+3); x = np.arange(n)/scale; i = x.astype(int); u = x-i; u = u*u*(3-2*u)
    return amp*(k[i]*(1-u)+k[i+1]*u)
class Ink:
    LW = 1500
    def __init__(self):
        g = rng.normal(0, 1, (H//8, W//8)); g = np.asarray(Image.fromarray(((g-g.min())/(np.ptp(g))*255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(30)), dtype=np.float32)/255
        paper = np.array([236, 224, 196], np.float32)*(0.90+0.16*g)[..., None]+rng.normal(0, 3, (H, W, 1))
        yy, xx = np.mgrid[0:H, 0:W]
        sun = np.clip(1-(np.hypot(xx-850, yy-330)-74)/3, 0, 1)[..., None]*0.78
        paper = paper*(1-sun)+np.array([186, 62, 44], np.float32)*sun
        self.paper = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8))
        self.layers = []
        cols = [(168, 178, 160), (120, 142, 128), (78, 108, 98), (44, 78, 70), (20, 48, 42)]
        for i, c in enumerate(cols):
            x = np.arange(self.LW)
            ridge = 1010+i*165-(smooth_noise(self.LW, 230-i*25, 95+i*18)+smooth_noise(self.LW, 60, 22)+smooth_noise(self.LW, 14, 5))
            y = np.arange(H)[:, None]; dy = y-ridge[None, :]
            a = np.clip(dy/2.0, 0, 1)*(np.clip(1-dy/(330+i*60), 0.18 if i < 4 else 1, 1) if i < 4 else 1.0)
            if i == 4: a = np.clip(dy/2.0, 0, 1)
            tex = 1+0.10*np.asarray(Image.fromarray((rng.random((H//4, self.LW//4))*255).astype(np.uint8)).resize((self.LW, H), Image.BICUBIC), dtype=np.float32)/255
            rgb = np.clip(np.array(c, np.float32)[None, None]*tex[..., None], 0, 255).astype(np.uint8)
            self.layers.append(Image.fromarray(np.dstack([rgb, (a*255).astype(np.uint8)])))
        m = rng.random((H//40, W//40)); m = np.asarray(Image.fromarray((m*255).astype(np.uint8)).resize((W//4, H//4), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6)), dtype=np.float32)/255
        self.rev = m*0.5+np.linspace(0, 0.9, W//4)[None, :]*0.6+np.linspace(0.3, 0, H//4)[:, None]   # 墨暈展開遮罩
        self.pp = rng.random((70, 4))
    def scene(self, t):
        im = self.paper.copy()
        for i, L in enumerate(self.layers):
            off = int(210-(i+1)*9*t) % (self.LW-W)
            im.paste(L.crop((off, 0, off+W, H)), (0, 0), L.crop((off, 0, off+W, H)))
        return im
    def particles(self, im, t, strength=1.0):
        L = Image.new('L', (W//2, H//2), 0); d = ImageDraw.Draw(L)
        for x0, y0, v, s in self.pp:
            x = (x0*W/2+18*np.sin(t*0.8+s*20)) % (W/2); y = (y0*H/2-(14+30*v)*t) % (H/2); r = 1.2+2.6*s
            b = int(255*(0.45+0.55*np.sin(t*2+s*30)**2)); d.ellipse((x-r, y-r, x+r, y+r), fill=b)
        g = np.asarray(L.filter(ImageFilter.GaussianBlur(1.6)).resize((W, H), Image.BILINEAR), dtype=np.float32)/255*strength
        a = np.asarray(im, dtype=np.float32); a += g[..., None]*np.array([255, 205, 110], np.float32)*1.5
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

INKS = Ink()
SEAL = seal()
f_big = F('Black', 150)
INTRO_CH = [[text_layer([(ch, f_big, INK)], shadow=False) for ch in col] for col in ('鑑古識真', '傳承文化')]
OUT_NAME = text_layer([('中華傳統文化推廣協會', F('Black', 98), INK)], shadow=False)
OUT_TOP = text_layer([('哥窯與哥釉鑑賞', F('Bold', 44), (120, 86, 36))], shadow=False)
OUT_SUB = text_layer([('傳承文化・共賞古董之美', F('Bold', 58), (150, 104, 40))], shadow=False)

def ink_intro(t):
    im = INKS.scene(t)
    for ci, col in enumerate(INTRO_CH):          # 直書標題，右起
        for i, L in enumerate(col):
            a = ease((t-0.7-ci*0.45-i*0.12)/0.5)
            paste(im, L, 640-ci*200, 330+i*172-(1-a)*14, a)
    paste(im, SEAL, 440, 1050, ease((t-2.0)/0.5))
    im = INKS.particles(im, t, ease(t/1.5))
    u = np.clip((t*0.95-INKS.rev)*3.0, 0, 1)      # 墨暈由暗綠底展開
    if u.min() < 1:
        m = Image.fromarray((u*255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        im = Image.composite(im, Image.new('RGB', (W, H), (10, 30, 27)), m)
    return im
def ink_outro(t):
    im = INKS.scene(t+6)
    haze = Image.new('RGB', (W, H), (240, 230, 205))
    im = Image.blend(im, haze, 0.25)
    paste(im, OUT_TOP, W/2, 520, ease((t-0.5)/0.6))
    a = ease((t-0.8)/0.7); paste(im, OUT_NAME, W/2, 650-(1-a)*14, a)
    d = ImageDraw.Draw(im); lw = int(360*ease((t-1.1)/0.7))
    if lw > 2: d.line((W/2-lw, 745, W/2+lw, 745), fill=(176, 132, 56), width=3)
    paste(im, OUT_SUB, W/2, 820, ease((t-1.3)/0.6))
    paste(im, SEAL, W/2, 990, ease((t-1.6)/0.5))
    return INKS.particles(im, t, 0.9)

# ---------- 鏡頭 ----------
VID_DIR = tempfile.mkdtemp(prefix='gy_vid_')
class Shot:
    def __init__(s, cfg):
        s.__dict__.update(cfg); s.xf = cfg.get('xf', 0.4); s.ready = False
    def prep(s):
        s.ready = True
        if s.kind in ('cover', 'frame'):
            im = ImageOps.exif_transpose(Image.open(R(s.src))).convert('RGB')
        if s.kind == 'cover':
            s.zm = max(s.z0, s.z1); k = max(W/im.width, H/im.height)*s.zm
            s.pre = im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)
        elif s.kind == 'frame':
            x0, y0, x1, y1 = s.crop; im = im.crop((int(x0*im.width), int(y0*im.height), int(x1*im.width), int(y1*im.height)))
            s.zm = max(s.z0, s.z1); k = min(990/im.width, 1250/im.height)*s.zm
            s.pre = im.resize((round(im.width*k), round(im.height*k)), Image.LANCZOS)
            kb = max(W/im.width, H/im.height); bg = im.resize((round(im.width*kb), round(im.height*kb)), Image.BILINEAR)
            bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width-W)//2+W, (bg.height-H)//2+H)).filter(ImageFilter.GaussianBlur(45))
            s.bg = Image.blend(bg, Image.new('RGB', (W, H), (12, 24, 22)), 0.55)
        elif s.kind == 'video':
            n = int((s.t1-s.t0+1.2)*FPS); vd = tempfile.mkdtemp(dir=VID_DIR)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s.ss), '-i', R(s.src), '-frames:v', str(n), '-vf',
                            f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}', '-q:v', '2',
                            os.path.join(vd, 'f%04d.jpg')], check=True)
            s.frames = sorted(glob.glob(os.path.join(vd, 'f*.jpg')))
    def free(s):
        for k in ('pre', 'bg'): s.__dict__.pop(k, None)
        s.ready = False
    def frame(s, t):
        if not s.ready: s.prep()
        lt = t-s.t0; u = ease(lt/(s.t1-s.t0+0.4))*0.5+0.5*min(1.0, max(0.0, lt/(s.t1-s.t0+0.4)))
        if s.kind == 'ink_intro': return ink_intro(lt)
        if s.kind == 'ink_outro': return ink_outro(lt)
        if s.kind == 'video':
            return Image.open(s.frames[min(len(s.frames)-1, max(0, int(lt*FPS)))]).convert('RGB')
        z = lerp(s.z0, s.z1, u)
        if s.kind == 'cover':
            cw, ch = min(W*s.zm/z, s.pre.width), min(H*s.zm/z, s.pre.height)
            cx = lerp(s.c0[0], s.c1[0], u)*s.pre.width; cy = lerp(s.c0[1], s.c1[1], u)*s.pre.height
            x0 = max(0, min(cx-cw/2, s.pre.width-cw)); y0 = max(0, min(cy-ch/2, s.pre.height-ch))
            return s.pre.resize((W, H), Image.BILINEAR, box=(x0, y0, x0+cw, y0+ch))
        im = s.bg.copy(); k = z/s.zm
        fg = s.pre.resize((round(s.pre.width*k), round(s.pre.height*k)), Image.BILINEAR)
        x, y = (W-fg.width)//2, (H-fg.height)//2-40
        ImageDraw.Draw(im).rectangle((x-5, y-5, x+fg.width+4, y+fg.height+4), outline=(196, 160, 90), width=2)
        im.paste(fg, (x, y)); return im

shots = [Shot(c) for c in SHOTS]

# ---------- 全域疊加：暗角、標題字卡、來源標示、字幕 ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vig = 1-0.30*np.clip((np.hypot((xx-W/2)/(W*0.75), (yy-H/2)/(H*0.75))-0.45)/0.55, 0, 1)**1.5
top = 1-0.42*np.clip(1-yy/520, 0, 1)**1.3; bot = 1-0.55*np.clip((yy-1380)/540, 0, 1)**1.2
MAP_PHOTO = (vig*top*bot*256).astype(np.uint16)[..., None]
MAP_INK = (vig*(1-0.5*np.clip((yy-1480)/440, 0, 1))*256).astype(np.uint16)[..., None]

TITLE_L = [(a, b, text_layer([(m, F('Black', 84), GOLD)]), text_layer([(sub, F('Bold', 42), CREAM)])) for a, b, m, sub in TITLES]
_tags = {}
def tag_layer(txt):
    if txt not in _tags:
        f = F('Bold', 30); b = ImageDraw.Draw(Image.new('L', (8, 8))).textbbox((0, 0), txt, font=f)
        im = Image.new('RGBA', (b[2]+44, 58), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width-1, 57), 8, fill=(10, 30, 27, 150), outline=GOLD+(200,), width=2)
        d.text((22, 29), txt, font=f, fill=CREAM, anchor='lm'); _tags[txt] = im
    return _tags[txt]

def cues():
    meta = json.load(open(R('audio/vo_meta.json'))); out = []
    for m in meta:
        parts = [p for p in m['text'].replace('。', '，').split('，') if p]
        n = sum(len(p) for p in parts); t = m['start']
        for p in parts:
            d = m['dur']*len(p)/n; out.append((t, t+d, p)); t += d
    return out
CUES = cues(); f_sub = F('Bold', 52)
SUB_L = [(a, b, text_layer([(p, f_sub, (255, 255, 255))])) for a, b, p in CUES]

def write_srt():
    ts = lambda x: '%02d:%02d:%02d,%03d' % (x//3600, x % 3600//60, x % 60, round(x % 1*1000) % 1000)
    with open(R('output/哥窯與哥釉_活動紀錄_60s.srt'), 'w', encoding='utf-8') as f:
        for i, (a, b, p) in enumerate(CUES, 1): f.write(f'{i}\n{ts(a)} --> {ts(min(b, DUR))}\n{p}\n\n')

def render(t):
    i = max(k for k, s in enumerate(shots) if s.t0 <= t+1e-6)
    s = shots[i]; im = s.frame(t)
    ink_w = 1.0 if s.kind.startswith('ink') else 0.0
    if i > 0 and t-s.t0 < s.xf:
        a = ease((t-s.t0)/s.xf); p = shots[i-1]; im = Image.blend(p.frame(t), im, a)
        ink_w = lerp(1.0 if p.kind.startswith('ink') else 0.0, ink_w, a)
    elif i > 0 and shots[i-1].ready: shots[i-1].free()
    m = MAP_PHOTO if ink_w < 0.5 else MAP_INK
    im = Image.fromarray(((np.asarray(im, dtype=np.uint16)*m) >> 8).astype(np.uint8))
    if s.tag:
        paste(im, tag_layer(s.tag), 48+tag_layer(s.tag).width/2, 92, ease((t-s.t0)/0.4)*ease((s.t1-t)/0.3+0.01))
    for a, b, L1, L2 in TITLE_L:
        if a <= t <= b:
            al = ease((t-a)/0.5)*ease((b-t)/0.4)
            paste(im, L1, W/2, 250-(1-ease((t-a)/0.5))*16, al); paste(im, L2, W/2, 352, al*ease((t-a-0.25)/0.5))
            lw = int(150*ease((t-a-0.1)/0.6)); ImageDraw.Draw(im).line((W/2-lw, 308, W/2+lw, 308), fill=GOLD, width=2) if lw > 2 and al > 0.6 else None
    for a, b, L in SUB_L:
        if a <= t < b: paste(im, L, W/2, 1700, min(ease((t-a)/0.15), ease((b-t)/0.12+0.3)))
    if t < 0.4: im = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), im, t/0.4)
    return im

if __name__ == '__main__':
    os.makedirs(R('output'), exist_ok=True)
    if '--stills' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills')+1].split(',')]
        out = sys.argv[sys.argv.index('--out')+1] if '--out' in sys.argv else R('output/stills')
        os.makedirs(out, exist_ok=True)
        sheet = Image.new('RGB', (270*len(ts), 480))
        for k, t in enumerate(ts):
            fr = render(t); fr.save(os.path.join(out, f'still_{t:05.1f}.jpg'), quality=88); sheet.paste(fr.resize((270, 480), Image.LANCZOS), (270*k, 0))
        sheet.save(os.path.join(out, 'sheet.jpg'), quality=85); sys.exit()
    write_srt()
    outp = R('output/哥窯與哥釉_活動紀錄_60s.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', R('audio/mix.wav'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-t', str(DUR), '-movflags', '+faststart', outp], stdin=subprocess.PIPE)
    for n in range(int(DUR*FPS)):
        ff.stdin.write(render(n/FPS).tobytes())
        if n % 150 == 0: print('frame', n, flush=True)
    ff.stdin.close(); ff.wait(); print('done', outp)
