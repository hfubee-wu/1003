# -*- coding: utf-8 -*-
"""以 numpy 程式合成原創配樂（無版權疑慮）：古箏撥弦(Karplus-Strong) + 洞簫 + 低沉弦樂墊底，
再與旁白混音（旁白出現時自動壓低音樂），輸出 audio/bgm.wav 與 audio/mix.wav。"""
import os, json
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, lfilter, resample_poly
from timeline import ROOT, DUR
SR = 44100; N = int(SR*DUR); rng = np.random.default_rng(7)
def hz(m): return 440*2**((m-69)/12)
def place(buf, x, t, g=1.0, pan=0.5):
    i = int(t*SR); x = x[:max(0, N-i)]
    buf[i:i+len(x), 0] += x*g*np.cos(pan*np.pi/2); buf[i:i+len(x), 1] += x*g*np.sin(pan*np.pi/2)
def pluck(m, dur=3.0, bright=0.5):           # 古箏：Karplus-Strong 撥弦
    f = hz(m); L = int(SR/f); n = int(dur*SR)
    b = rng.uniform(-1, 1, L); b = lfilter([1-bright*0.6], [1, -bright*0.6], b)
    out = np.empty(n); k = 0; prev = 0.0
    buf = b.copy(); damp = 0.9965 if m > 60 else 0.9982
    for i in range(n):
        v = buf[k]; out[i] = v
        buf[k] = damp*0.5*(v+prev); prev = v; k = (k+1) % L
    bend = 1+0.0  # 保持音高穩定
    return out*np.minimum(1, np.arange(n)/(0.002*SR))
def xiao(m, dur):                            # 洞簫：正弦泛音 + 氣聲 + 顫音
    n = int(dur*SR); t = np.arange(n)/SR
    vib = 1+0.006*np.sin(2*np.pi*5*t)*np.clip((t-0.4)/0.6, 0, 1)
    ph = 2*np.pi*np.cumsum(hz(m)*vib)/SR
    x = np.sin(ph)+0.28*np.sin(2*ph)+0.08*np.sin(3*ph)
    bb, aa = butter(2, [hz(m)*0.9/(SR/2), hz(m)*2.2/(SR/2)], 'band')
    x += 0.5*lfilter(bb, aa, rng.normal(0, 1, n))
    env = np.clip(t/0.35, 0, 1)*np.clip((dur-t)/0.6, 0, 1)
    return x*env
def pad(ms, dur):                            # 低沉弦樂：多重微分音鋸齒波 + 低通
    n = int(dur*SR); t = np.arange(n)/SR; x = np.zeros(n)
    for m in ms:
        for det in (-0.07, 0, 0.06):
            f = hz(m+det); ph = (f*t+rng.random()) % 1
            x += 2*ph-1
    bb, aa = butter(2, 700/(SR/2)); x = lfilter(bb, aa, x)
    env = np.clip(t/2.0, 0, 1)*np.clip((dur-t)/2.0, 0, 1)
    return x*env*(1+0.08*np.sin(2*np.pi*0.25*t))
def drum(dur=2.5):                           # 低音大鼓（段落轉場）
    n = int(dur*SR); t = np.arange(n)/SR
    return np.sin(2*np.pi*(48*t+18*(1-np.exp(-t*18))/18))*np.exp(-t*3.2)

mus = np.zeros((N, 2))
K = DUR/50.0   # 樂譜以 50 秒寫成，依影片長度等比例伸縮
_place = place
def place(buf, x, t, g=1.0, pan=0.5): _place(buf, x, t*K, g, pan)
# 和聲進行（D 羽調式五聲：D F G A C），每段落換一次低音
chords = [(0, 5, [38, 45, 50]), (5, 12, [41, 48, 53]), (12, 22, [38, 45, 53]), (22, 32, [43, 50, 55]),
          (32, 41, [36, 43, 52]), (41, 46.2, [41, 48, 57]), (46.2, 50, [38, 45, 50, 57])]
for a, b, ms in chords:
    place(mus, pad(ms, (b-a)*K+2.0), max(0, a-1.0/K), 0.05)
for t in (0.0, 5.0, 12.0, 22.0, 32.0, 41.0, 46.2):
    place(mus, drum(), t, 0.5)
penta = [62, 65, 67, 69, 72, 74, 77, 79, 81, 84]
def gliss(t, up=True, g=0.16):               # 古箏刮奏
    seq = penta if up else penta[::-1]
    for i, m in enumerate(seq):
        place(mus, pluck(m, 2.5, 0.7), t+i*0.055/K, g*(0.6+0.4*i/len(seq)), 0.3+0.04*i)
for t in (0.15, 11.6, 21.6, 31.6, 40.6): gliss(t, True)
gliss(46.0, False, 0.2)
# 古箏主旋律 (起拍秒, MIDI)
mel = [(1.2,62),(2.0,69),(2.8,67),(3.6,65),(4.2,62),
       (5.6,65),(6.2,69),(6.8,72),(7.6,74),(8.4,72),(9.0,69),(9.8,67),(10.6,69),
       (12.6,62),(13.4,65),(14.2,69),(15.0,67),(16.2,65),(17.0,62),(18.2,60),(19.0,62),(20.2,65),
       (22.6,67),(23.2,69),(23.8,72),(24.6,74),(25.4,72),(26.2,69),(27.0,67),(27.8,69),(28.6,72),(29.4,67),(30.4,65),
       (32.6,60),(33.4,64),(34.2,67),(35.0,69),(36.0,67),(37.0,64),(38.0,62),(39.0,60),
       (41.4,65),(42.0,69),(42.6,72),(43.4,77),(44.2,74),(45.0,72),
       (46.6,74),(47.4,69),(48.2,62)]
for t, m in mel:
    place(mus, pluck(m, 3.5, 0.55), t, 0.22, 0.42)
    place(mus, pluck(m-12, 3.5, 0.3), t+0.01, 0.10, 0.6)
# 洞簫長音
for t, m, d in [(12.2,74,3.2),(15.6,72,2.6),(18.4,69,3.2),(32.2,72,3.4),(35.8,76,2.8),(38.8,74,2.4),(46.4,74,3.6)]:
    place(mus, xiao(m, d*K), t, 0.055, 0.6)
# 殘響
ir = rng.normal(0, 1, (int(2.4*SR), 2))*np.exp(-np.arange(int(2.4*SR))/SR*2.6)[:, None]
wet = np.stack([fftconvolve(mus[:, c], ir[:, c])[:N] for c in (0, 1)], 1)
mus = mus+0.018*wet
mus /= np.abs(mus).max()/0.9
t = np.arange(N)/SR
mus *= (np.clip(t/1.0, 0, 1)*np.clip((DUR-t)/1.2, 0, 1))[:, None]
sf.write(os.path.join(ROOT, 'audio/bgm.wav'), mus, SR)

# 旁白混音 + 自動壓低音樂 (ducking)
vo = np.zeros(N)
for m in json.load(open(os.path.join(ROOT, 'audio/vo_meta.json'))):
    x, sr = sf.read(os.path.join(ROOT, m['file'])); x = resample_poly(x, SR, sr)
    i = int(m['start']*SR); x = x[:N-i]; vo[i:i+len(x)] += x
vo /= np.abs(vo).max()/0.95
bb, aa = butter(1, 3/(SR/2)); envl = np.clip(lfilter(bb, aa, np.abs(vo))*14, 0, 1)
mix = mus*(0.62-0.34*envl)[:, None]+vo[:, None]*0.95
mix /= max(1.0, np.abs(mix).max()/0.97)
sf.write(os.path.join(ROOT, 'audio/mix.wav'), mix, SR)
print('ok', mix.shape, float(np.abs(mix).max()))
