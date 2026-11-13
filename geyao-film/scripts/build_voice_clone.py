# -*- coding: utf-8 -*-
"""聲音複製版旁白：以講師本人（已同意）在現場影片中的說話聲為參考音，
用 sherpa-onnx + ZipVoice（zero-shot）合成旁白，並以 SenseVoice 語音辨識回聽檢查內容。
用法：python build_voice_clone.py <zipvoice模型資料夾> <sensevoice模型資料夾> [speed] [num_steps]"""
import sys, os, json
import numpy as np, soundfile as sf, sherpa_onnx
from opencc import OpenCC
from timeline import ROOT, NARRATION
d, asr_d = sys.argv[1], sys.argv[2]
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
steps = int(sys.argv[4]) if len(sys.argv) > 4 else 16
REF = os.path.join(ROOT, 'audio/ref/ref_講師_V01.wav')
REF_TEXT = open(os.path.join(ROOT, 'audio/ref/ref_講師_V01.txt'), encoding='utf-8').read().strip()
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    zipvoice=sherpa_onnx.OfflineTtsZipvoiceModelConfig(
        tokens=d+'/tokens.txt', encoder=d+'/encoder.int8.onnx', decoder=d+'/decoder.int8.onnx',
        vocoder=d+'/vocos_24khz.onnx', lexicon=d+'/lexicon.txt'), num_threads=4))
tts = sherpa_onnx.OfflineTts(cfg)
import difflib, re
from pypinyin import lazy_pinyin
clean = lambda t: lazy_pinyin(re.sub(r'[^\u4e00-\u9fff]', '', t))   # 以拼音比對，忽略同音字
rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=asr_d+'/model.onnx', tokens=asr_d+'/tokens.txt', use_itn=True, language='zh', num_threads=4)
MAXDUR = [4.55, 6.2, 9.4, 9.4, 7.95, 4.95, 4.4]   # 各段旁白可用的最長秒數
ref, rsr = sf.read(REF, dtype='float32'); t2s = OpenCC('t2s'); meta = []
only = [int(x) for x in os.environ.get('ONLY', '').split(',') if x]
old = json.load(open(os.path.join(ROOT, 'audio/vo_meta.json'))) if only else None
for i, (t0, text) in enumerate(NARRATION, 1):
    fn = f'audio/vo_{i:02d}.wav'
    if only and i not in only: meta.append(old[i-1]); continue
    best = None; sp = speed; mx = MAXDUR[i-1]
    for k in range(8):   # 多次嘗試：內容需通過語音辨識回聽，長度需落在該段時間格內
        g = sherpa_onnx.GenerationConfig(); g.reference_audio = ref; g.reference_sample_rate = rsr
        g.reference_text = t2s.convert(REF_TEXT); g.num_steps = steps; g.speed = sp
        a = tts.generate(t2s.convert(text), g); x = np.asarray(a.samples, dtype=np.float32)
        idx = np.where(np.abs(x) > 0.012)[0]
        x = x[max(0, idx[0]-int(.03*a.sample_rate)): idx[-1]+int(.12*a.sample_rate)]
        st = rec.create_stream(); st.accept_waveform(a.sample_rate, x); rec.decode_stream(st)
        sc = difflib.SequenceMatcher(None, clean(t2s.convert(text)), clean(st.result.text)).ratio()
        dur = len(x)/a.sample_rate; over = max(0.0, dur/mx-1)
        rank = sc-over*2
        if best is None or rank > best[4]: best = (sc, x, st.result.text, a.sample_rate, rank, sp)
        if sc >= float(os.environ.get("MINSC", "0.97")) and over == 0: break
        sp = min(1.3, sp*max(1.0, dur/mx)*1.03) if over > 0 else sp*(1.02 if k % 2 else 0.97)
    sc, x, heard, sr_, _, sp = best
    x = x/np.abs(x).max()*0.9
    sf.write(os.path.join(ROOT, fn), x, sr_)
    class _A: sample_rate = sr_
    a = _A()
    dur = round(len(x)/a.sample_rate, 3); meta.append(dict(file=fn, start=t0, dur=dur, text=text))
    print(i, t0, dur, 'end', round(t0+dur, 2), f'| 語速 {sp:.2f} 吻合度 {sc:.2f} | 回聽:', heard)
json.dump(meta, open(os.path.join(ROOT, 'audio/vo_meta.json'), 'w'), ensure_ascii=False, indent=1)
