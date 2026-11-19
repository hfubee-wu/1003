# 背景音樂：D 宮五聲音階撥弦 + 低音持續音，並在旁白處自動壓低（ducking）
import numpy as np, soundfile as sf, wave
S="/tmp/claude-0/-home-user-1003/867f30ec-45de-5401-8228-619127247ba4/scratchpad"
SR=44100; D=50.0; n=int(SR*D); t=np.arange(n)/SR; rng=np.random.default_rng(11)
mus=np.zeros(n)
def pluck(f,st,amp,dec=2.2):
    L=int(SR*3.5); tt=np.arange(L)/SR; s=np.zeros(L)
    for h,a in [(1,1),(2,.5),(3,.28),(4,.16),(5,.08),(6,.05)]:
        s+=a*np.sin(2*np.pi*f*h*tt*(1+0.0004*h))*np.exp(-tt*dec*(1+h*0.45))
    s*=np.minimum(1,tt/0.004); i=int(st*SR); e=min(n,i+L); mus[i:e]+=amp*s[:e-i]
scale=[293.66,329.63,369.99,440.0,493.88]
notes=[f/2 for f in scale]+scale+[f*2 for f in scale[:3]]
beat=0.6; k=6
for b in range(int(D/beat)):
    st=b*beat
    if rng.random()<0.72:
        k=int(np.clip(k+rng.integers(-2,3),2,len(notes)-1)); pluck(notes[k],st+rng.uniform(0,.02),0.20)
    if b%8==0: pluck(notes[0],st,0.24,1.2); pluck(notes[3]/2,st+0.01,0.12,1.2)
pad=(0.06*np.sin(2*np.pi*73.42*t)+0.04*np.sin(2*np.pi*110*t)+0.025*np.sin(2*np.pi*146.83*t))*(0.8+0.2*np.sin(2*np.pi*0.15*t))
mus+=pad
vo=np.zeros(n)
for st,f in [(0.40,"s0"),(9.60,"s1"),(22.80,"s2"),(33.30,"s3"),(43.00,"s4")]:
    a,sr=sf.read(f"{S}/vo/{f}.wav"); 
    if sr!=SR: a=np.interp(np.arange(int(len(a)*SR/sr))*sr/SR,np.arange(len(a)),a)
    i=int(st*SR); vo[i:i+len(a)]+=a[:n-i]
env=np.abs(vo); w=int(0.25*SR); env=np.convolve(env,np.ones(w)/w,'same'); env=np.convolve((env>0.01).astype(float),np.ones(int(.4*SR))/int(.4*SR),'same')
duck=1-0.6*np.clip(env,0,1)
mus=mus/np.max(np.abs(mus))*0.32*duck
fade=np.minimum(1,np.minimum(t/1.0,(D-t)/2.0)); mix=vo/np.max(np.abs(vo))*0.85+mus*fade
mix=mix/max(1,np.max(np.abs(mix))/0.95)
sf.write(f"{S}/mix.wav",mix,SR); print("ok")
