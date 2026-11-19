import sys, sherpa_onnx, soundfile as sf
from opencc import OpenCC
M=sys.argv[1]; txt=OpenCC('t2s').convert(sys.argv[2]); out=sys.argv[3]; speed=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f"{M}/model.onnx",lexicon=f"{M}/lexicon.txt",tokens=f"{M}/tokens.txt",dict_dir=f"{M}/dict"),num_threads=4),rule_fsts=f"{M}/date.fst,{M}/phone.fst,{M}/number.fst,{M}/new_heteronym.fst")
a=sherpa_onnx.OfflineTts(cfg).generate(txt,sid=0,speed=speed)
sf.write(out,a.samples,a.sample_rate); print(out, len(a.samples)/a.sample_rate)
