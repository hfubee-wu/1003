# 以 numpy 合成 30 秒五聲音階撥弦配樂（Karplus-Strong），輸出 WAV
import sys, wave
import numpy as np
sr, dur = 44100, 30
rng = np.random.default_rng(7)
out = np.zeros(sr * (dur + 4))

def pluck(freq, length, amp):
    n = int(sr / freq)
    buf = rng.uniform(-1, 1, n)
    buf = np.convolve(buf, np.ones(4) / 4, mode="same")      # 柔化音色
    y = np.empty(int(sr * length))
    for i in range(len(y)):
        y[i] = buf[i % n]
        buf[i % n] = 0.996 * 0.5 * (buf[i % n] + buf[(i + 1) % n])
    return amp * y

D = 146.83                                                   # D 宮五聲：D E F# A B
scale = [D * 2 ** (s / 12) for s in (0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24)]
melody = [5, 7, 8, 7, 5, 4, 5, 2, 3, 5, 7, 9, 8, 7, 5, 7,
          8, 9, 10, 9, 8, 7, 5, 4, 5, 7, 5, 4, 2, 3, 5, 5]
beat = 0.9
for i, k in enumerate(melody):
    t = 0.6 + i * beat
    if t > dur - 2: break
    s = int(t * sr); y = pluck(scale[k], 3.0, 0.5)
    out[s:s + len(y)] += y
    if i % 4 == 0:                                           # 低音根音
        b = pluck(scale[[0, 3, 1, 3][(i // 4) % 4]] / 2, 4.0, 0.55)
        out[s:s + len(b)] += b
    if i % 2 == 1:                                           # 輕巧裝飾音
        g = pluck(scale[min(k + 2, 10)], 1.5, 0.18)
        s2 = s + int(beat / 2 * sr); out[s2:s2 + len(g)] += g

t = np.arange(len(out)) / sr                                 # 持續低音鋪底
out += 0.05 * (np.sin(2 * np.pi * D / 2 * t) + 0.5 * np.sin(2 * np.pi * D * 0.75 * t)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t))
for d, g in ((0.25, 0.3), (0.41, 0.2), (0.63, 0.12)):        # 簡易殘響
    k = int(d * sr); out[k:] += g * out[:-k]
out = out[: sr * dur]
env = np.minimum(1, np.arange(len(out)) / (sr * 0.8)) * np.minimum(1, (len(out) - np.arange(len(out))) / (sr * 2.0))
out = out * env; out = out / np.abs(out).max() * 0.8
st = np.stack([out, np.roll(out, 300)], 1)                   # 微幅立體聲
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((st * 32767).astype("<i2").tobytes())
