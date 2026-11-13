# 哥窯與哥釉｜50 秒活動紀錄影片

中華傳統文化推廣協會 2026/11/12（四）古亭麥當勞活動。

## 資料夾與命名
```
geyao-film/
├─ assets/
│  ├─ poster/        P01_活動海報.png            （P = 海報，僅作資訊與風格參考）
│  ├─ collection/    K01~K05_<器形>.jpg          （K = 藏品攝影）
│  ├─ event_photo/   E01~E10_<內容>.jpg          （E = 活動現場紀實照片）
│  └─ event_video/   V01_器物橫移實拍.mp4         （V = 活動現場紀實影片）
├─ audio/            vo_01~07.wav 旁白、bgm.wav 配樂、mix.wav 混音、vo_meta.json 時間碼
├─ fonts/            Noto Serif CJK TC（思源宋體，OFL 授權）
├─ docs/             分鏡表.md、旁白稿.md
├─ scripts/          timeline.py（鏡頭表）、build_voice.py、build_music.py、build_video.py
└─ output/           哥窯與哥釉_活動紀錄_50s.mp4、.srt
```
命名規則：`<類別代碼><兩位序號>_<內容描述>.<副檔名>`。

## 重新產生
```
pip install pillow numpy scipy soundfile sherpa-onnx opencc-python-reimplemented
cd scripts
python build_voice.py <kokoro-multi-lang-v1_0 模型資料夾> 49 1.0   # 旁白
python build_music.py                                            # 配樂 + 混音
python build_video.py                                            # 影片 + SRT
```
調整鏡頭順序、時間、字卡、旁白，只需修改 `scripts/timeline.py`。
配樂為程式合成的原創音樂，無版權疑慮。
