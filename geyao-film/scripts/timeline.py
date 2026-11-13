# -*- coding: utf-8 -*-
"""共用設定：旁白、分段標題、鏡頭表。所有時間單位為秒。"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS, DUR = 1080, 1920, 30, 50.0

# (預定起始秒, 旁白文字)
NARRATION = [
    (0.6,  "一件古董，承載的不只是歲月，更是一段文化與歷史。"),
    (5.4,  "走進哥窯與哥釉的世界，探索源自宋代名窯的開片之美。"),
    (12.3, "透過專家講解，從歷史淵源、製作工藝到鑑賞特色，深入認識哥窯與哥釉的文化價值。"),
    (22.3, "從實物觀察到經驗交流，每一次分享，都是知識的累積，也是收藏文化的延續。"),
    (32.1, "結合顯微放大等科學工具，從細節辨識器物特徵，讓傳統鑑賞與現代方法相互印證。"),
    (40.3, "讓收藏不只是個人喜好，更成為跨越世代的文化橋梁。"),
    (45.5, "中華傳統文化推廣協會，邀您共賞古董之美。"),
]

# 分段標題字卡 (起, 迄, 主標, 副標)
TITLES = [
    (7.7, 11.6,  "哥窯與哥釉", "器物鑑賞"),
    (12.4, 21.6, "專家親臨分享", "歷史淵源・工藝特色・收藏價值"),
    (22.4, 31.6, "實物鑑賞", "會員交流・收藏分享"),
    (32.4, 40.6, "科學化工具", "實物鑑賞・細節解析"),
    (41.3, 45.9, "鑑古識真・交流分享", "共賞文化之美"),
]

TAG_REAL = "活動紀實｜2026.11.12 古亭"
TAG_COLL = "藏品攝影"
TAG_POSTER = "活動海報"
TAG_MOOD = "情境畫面"

A = "assets/"
# kind: ink_intro / ink_outro / cover / frame / video
# cover: c0,c1 = (cx, cy) 正規化中心點；z0,z1 = 縮放倍率（1.0 為剛好鋪滿）
SHOTS = [
    dict(t0=0.0,  t1=3.1,  kind="ink_intro", tag=TAG_MOOD),
    dict(t0=3.1,  t1=5.0,  kind="cover", src=A+"collection/K01_撇口瓶.jpg", c0=(.5,.55), c1=(.5,.5), z0=1.35, z1=1.12, tag=TAG_COLL, xf=0.7),
    dict(t0=5.0,  t1=7.6,  kind="cover", src=A+"poster/P01_活動海報.png", c0=(.5,.5), c1=(.5,.17), z0=1.0, z1=1.45, tag=TAG_POSTER, xf=0.6),
    dict(t0=7.6,  t1=8.5,  kind="frame", src=A+"collection/K03_觚.jpg", crop=(.12,.02,.80,.885), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=8.5,  t1=9.4,  kind="frame", src=A+"collection/K04_三足爐.jpg", crop=(.1,.05,.9,.95), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=9.4,  t1=10.3, kind="frame", src=A+"collection/K02_水盂.jpg", crop=(.1,.05,.9,.95), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=10.3, t1=11.15,kind="cover", src=A+"collection/K05_弦紋長頸瓶.jpg", c0=(.52,.5), c1=(.52,.5), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=11.15,t1=12.0, kind="cover", src=A+"collection/K01_撇口瓶.jpg", c0=(.5,.5), c1=(.5,.5), z0=1.0, z1=1.06, tag=TAG_COLL, xf=0.3),
    dict(t0=12.0, t1=14.6, kind="cover", src=A+"event_photo/E02_講解青花盤.jpg", c0=(.55,.45), c1=(.6,.42), z0=1.0, z1=1.12, tag=TAG_REAL, xf=0.6),
    dict(t0=14.6, t1=18.2, kind="video", src=A+"event_video/V02_講師持觚講解實拍.mp4", ss=2.2, tag=TAG_REAL),
    dict(t0=18.2, t1=20.1, kind="cover", src=A+"event_photo/E05_會員聆聽.jpg", c0=(.5,.5), c1=(.5,.45), z0=1.0, z1=1.1, tag=TAG_REAL),
    dict(t0=20.1, t1=22.0, kind="cover", src=A+"event_photo/E04_觚特寫.jpg", c0=(.55,.5), c1=(.55,.48), z0=1.0, z1=1.08, tag=TAG_REAL),
    dict(t0=22.0, t1=27.6, kind="video", src=A+"event_video/V01_器物橫移實拍.mp4", ss=0.6, tag=TAG_REAL, xf=0.6),
    dict(t0=27.6, t1=30.0, kind="cover", src=A+"event_photo/E10_六件器物陳列.jpg", c0=(.30,.5), c1=(.62,.5), z0=1.0, z1=1.0, tag=TAG_REAL),
    dict(t0=30.0, t1=32.0, kind="cover", src=A+"event_photo/E09_器物上手.jpg", c0=(.36,.6), c1=(.42,.6), z0=1.1, z1=1.2, tag=TAG_REAL),
    dict(t0=32.0, t1=34.4, kind="cover", src=A+"event_photo/E01_顯微觀察粉彩瓶.jpg", c0=(.52,.55), c1=(.60,.55), z0=1.0, z1=1.12, tag=TAG_REAL, xf=0.6),
    dict(t0=34.4, t1=36.8, kind="cover", src=A+"event_photo/E03_顯微畫面平板.jpg", c0=(.45,.5), c1=(.45,.55), z0=1.0, z1=1.3, tag=TAG_REAL),
    dict(t0=36.8, t1=39.0, kind="cover", src=A+"event_photo/E06_瓶特寫.jpg", c0=(.6,.5), c1=(.6,.5), z0=1.06, z1=1.0, tag=TAG_REAL),
    dict(t0=39.0, t1=41.0, kind="cover", src=A+"event_photo/E04_觚特寫.jpg", c0=(.40,.62), c1=(.40,.58), z0=1.55, z1=1.75, tag=TAG_REAL),
    dict(t0=41.0, t1=43.6, kind="cover", src=A+"event_photo/E07_洗式器物觀察.jpg", c0=(.40,.5), c1=(.55,.5), z0=1.0, z1=1.05, tag=TAG_REAL, xf=0.6),
    dict(t0=43.6, t1=46.2, kind="frame", src=A+"event_photo/E10_六件器物陳列.jpg", crop=(0,0,1,1), z0=1.0, z1=1.08, tag=TAG_REAL),
    dict(t0=46.2, t1=50.0, kind="ink_outro", tag=None, xf=0.8),
]
