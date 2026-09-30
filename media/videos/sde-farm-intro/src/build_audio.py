import json,re,sys,numpy as np,soundfile as sf
sys.path.insert(0,'.');import voices
SPEED=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
LET={'S':'艾斯','D':'低','E':'伊'}
def speak(t):
  t=t.replace('SDE','艾斯低伊').replace('：','，')
  return re.sub(r'[SDE]',lambda m:LET[m.group(0)],t)
tts=voices.baker()
T=json.load(open('timeline.json'));L=T['lines']
HEAD,GAP,TAIL=0.5,0.3,1.3
t=HEAD;subs=[];sr=None
for i,l in enumerate(L):
  a=tts.generate(speak(l['text']),sid=0,speed=SPEED);sr=a.sample_rate
  y=np.array(a.samples);sf.write(f'aud2/{i}.wav',y,sr);d=len(y)/sr;l['dur']=d;l['start']=t
  parts=[p for p in re.split(r'(?<=[。：])',l['text']) if p.strip()];out=[]
  for p in parts:
    if len(p)>18:
      cur=''
      for s in re.split(r'(?<=，)',p):
        if len(cur)+len(s)>18 and cur: out.append(cur);cur=s
        else: cur+=s
      if cur: out.append(cur)
    else: out.append(p)
  n=sum(len(o) for o in out);c=t
  for o in out: dd=d*len(o)/n;subs.append({'s':c,'e':c+dd,'text':o.rstrip('，。')});c+=dd
  t+=d+GAP
total=t-GAP+TAIL
json.dump({'lines':L,'subs':subs,'total':total},open('timeline.json','w'),ensure_ascii=False,indent=1)
y=np.zeros(int(total*sr))
for i,l in enumerate(L):
  a,_=sf.read(f'aud2/{i}.wav');s=int(l['start']*sr);y[s:s+len(a)]+=a[:len(y)-s]
sf.write('narration.wav',y/np.max(np.abs(y))*0.89,sr)
print('sr',sr,'total',round(total,2),[round(l['dur'],2) for l in L])
