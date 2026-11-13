# -*- coding: utf-8 -*-
"""共用設定：旁白、分段標題、鏡頭表。所有時間單位為秒。"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS, DUR = 1080, 1920, 30, 60.0

# (預定起始秒, 旁白文字)
NARRATION = [
    (0.7,  "一件古董，承載的不只是歲月，更是一段文化與歷史。"),
    (6.4,  "走進哥窯與哥釉的世界，探索源自宋代名窯的開片之美。"),
    (14.8, "透過專家講解，從歷史淵源、製作工藝到鑑賞特色，深入認識哥窯與哥釉的文化價值。"),
    (26.8, "從實物觀察到經驗交流，每一次分享，都是知識的累積，也是收藏文化的延續。"),
    (38.7, "結合顯微放大等科學工具，從細節辨識器物特徵，讓傳統鑑賞與現代方法相互印證。"),
    (49.4, "讓收藏不只是個人喜好，更成為跨越世代的文化橋梁。"),
    (55.0, "中華傳統文化推廣協會，邀您共賞古董之美。"),
]

# 分段標題字卡 (起, 迄, 主標, 副標)
TITLES = [
    (9.2, 13.9,  "哥窯與哥釉", "器物鑑賞"),
    (14.9, 25.9, "專家親臨分享", "歷史淵源・工藝特色・收藏價值"),
    (26.9, 37.9, "實物鑑賞", "會員交流・收藏分享"),
    (38.9, 48.7, "科學化工具", "實物鑑賞・細節解析"),
    (49.6, 55.0, "鑑古識真・交流分享", "共賞文化之美"),
]

TAG_REAL = "活動紀實｜2026.11.12 古亭"
TAG_COLL = "藏品攝影"
TAG_POSTER = "活動海報"
TAG_MOOD = "情境畫面"

A = "assets/"
# kind: ink_intro / ink_outro / cover / frame / video
# cover: c0,c1 = (cx, cy) 正規化中心點；z0,z1 = 縮放倍率（1.0 為剛好鋪滿）
SHOTS = [
    dict(t0=0.0,  t1=3.7,  kind="ink_intro", tag=TAG_MOOD),
    dict(t0=3.7,  t1=6.0,  kind="cover", src=A+"collection/K01_撇口瓶.jpg", c0=(.5,.55), c1=(.5,.5), z0=1.35, z1=1.12, tag=TAG_COLL, xf=0.7),
    dict(t0=6.0,  t1=9.0,  kind="cover", src=A+"poster/P01_活動海報.png", c0=(.5,.5), c1=(.5,.17), z0=1.0, z1=1.45, tag=TAG_POSTER, xf=0.6),
    dict(t0=9.0,  t1=10.1, kind="frame", src=A+"collection/K03_觚.jpg", crop=(.12,.02,.80,.885), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=10.1, t1=11.2, kind="frame", src=A+"collection/K04_三足爐.jpg", crop=(.1,.05,.9,.95), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=11.2, t1=12.3, kind="frame", src=A+"collection/K02_水盂.jpg", crop=(.1,.05,.9,.95), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=12.3, t1=13.35,kind="cover", src=A+"collection/K05_弦紋長頸瓶.jpg", c0=(.52,.5), c1=(.52,.5), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=13.35,t1=14.4, kind="cover", src=A+"collection/K01_撇口瓶.jpg", c0=(.5,.5), c1=(.5,.5), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=14.4, t1=17.2, kind="cover", src=A+"event_photo/E02_講解青花盤.jpg", c0=(.55,.45), c1=(.6,.42), z0=1.0, z1=1.12, tag=TAG_REAL, xf=0.6),
    dict(t0=17.2, t1=21.4, kind="video", src=A+"event_video/V02_講師持觚講解實拍.mp4", ss=2.0, tag=TAG_REAL),
    dict(t0=21.4, t1=23.2, kind="cover", src=A+"event_photo/E08_講解交流.jpg", c0=(.50,.5), c1=(.62,.5), z0=1.0, z1=1.05, tag=TAG_REAL),
    dict(t0=23.2, t1=24.9, kind="cover", src=A+"event_photo/E05_會員聆聽.jpg", c0=(.5,.5), c1=(.5,.45), z0=1.0, z1=1.1, tag=TAG_REAL),
    dict(t0=24.9, t1=26.4, kind="cover", src=A+"event_photo/E04_觚特寫.jpg", c0=(.55,.5), c1=(.55,.48), z0=1.0, z1=1.08, tag=TAG_REAL),
    dict(t0=26.4, t1=33.0, kind="video", src=A+"event_video/V01_器物橫移實拍.mp4", ss=0.6, tag=TAG_REAL, xf=0.6),
    dict(t0=33.0, t1=35.8, kind="cover", src=A+"event_photo/E10_六件器物陳列.jpg", c0=(.30,.5), c1=(.62,.5), z0=1.0, z1=1.0, tag=TAG_REAL),
    dict(t0=35.8, t1=38.4, kind="cover", src=A+"event_photo/E09_器物上手.jpg", c0=(.36,.6), c1=(.42,.6), z0=1.1, z1=1.2, tag=TAG_REAL),
    dict(t0=38.4, t1=41.2, kind="cover", src=A+"event_photo/E01_顯微觀察粉彩瓶.jpg", c0=(.52,.55), c1=(.60,.55), z0=1.0, z1=1.12, tag=TAG_REAL, xf=0.6),
    dict(t0=41.2, t1=44.0, kind="cover", src=A+"event_photo/E03_顯微畫面平板.jpg", c0=(.45,.5), c1=(.45,.55), z0=1.0, z1=1.3, tag=TAG_REAL),
    dict(t0=44.0, t1=46.6, kind="cover", src=A+"event_photo/E06_瓶特寫.jpg", c0=(.6,.5), c1=(.6,.5), z0=1.06, z1=1.0, tag=TAG_REAL),
    dict(t0=46.6, t1=49.2, kind="cover", src=A+"event_photo/E04_觚特寫.jpg", c0=(.40,.62), c1=(.40,.58), z0=1.55, z1=1.75, tag=TAG_REAL),
    dict(t0=49.2, t1=52.3, kind="cover", src=A+"event_photo/E07_洗式器物觀察.jpg", c0=(.40,.5), c1=(.55,.5), z0=1.0, z1=1.05, tag=TAG_REAL, xf=0.6),
    dict(t0=52.3, t1=55.4, kind="frame", src=A+"event_photo/E10_六件器物陳列.jpg", crop=(0,0,1,1), z0=1.0, z1=1.08, tag=TAG_REAL),
    dict(t0=55.4, t1=60.0, kind="ink_outro", tag=None, xf=0.8),
]
