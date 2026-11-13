# -*- coding: utf-8 -*-
"""以離線 TTS（sherpa-onnx + Kokoro 多語模型）產生男聲國語旁白，逐句輸出 wav。
用法：python build_voice.py <kokoro模型資料夾> [speaker_id] [speed]"""
import sys, os, json
import numpy as np, soundfile as sf, sherpa_onnx
from opencc import OpenCC
from timeline import ROOT, NARRATION
d = sys.argv[1]; sid = int(sys.argv[2]) if len(sys.argv) > 2 else 49
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
        model=d+'/model.onnx', voices=d+'/voices.bin', tokens=d+'/tokens.txt',
        data_dir=d+'/espeak-ng-data', dict_dir=d+'/dict',
        lexicon=d+'/lexicon-zh.txt,'+d+'/lexicon-us-en.txt'), num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
t2s = OpenCC('t2s')  # 模型詞典以簡體為主，僅在送入 TTS 時轉換；字幕仍為繁體
meta = []
for i, (t0, text) in enumerate(NARRATION, 1):
    a = tts.generate(t2s.convert(text), sid=sid, speed=speed)
    x = np.asarray(a.samples, dtype=np.float32)
    # 去除頭尾靜音
    idx = np.where(np.abs(x) > 0.01)[0]
    x = x[max(0, idx[0]-int(.03*a.sample_rate)): idx[-1]+int(.12*a.sample_rate)]
    fn = f'audio/vo_{i:02d}.wav'
    sf.write(os.path.join(ROOT, fn), x, a.sample_rate)
    meta.append(dict(file=fn, start=t0, dur=round(len(x)/a.sample_rate, 3), text=text))
    print(i, t0, meta[-1]['dur'], 'end', round(t0+meta[-1]['dur'], 2))
json.dump(meta, open(os.path.join(ROOT, 'audio/vo_meta.json'), 'w'), ensure_ascii=False, indent=1)
