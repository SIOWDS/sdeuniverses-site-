import sherpa_onnx, soundfile as sf, sys, numpy as np
d='kokoro-multi-lang-v1_1/'
cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
 model=d+'model.onnx',voices=d+'voices.bin',tokens=d+'tokens.txt',data_dir=d+'espeak-ng-data',dict_dir=d+'dict',
 lexicon=d+'lexicon-us-en.txt,'+d+'lexicon-zh.txt'),num_threads=4),rule_fsts=d+'date-zh.fst,'+d+'phone-zh.fst,'+d+'number-zh.fst')
tts=sherpa_onnx.OfflineTts(cfg)
def gen(text,sid,out,speed=1.0):
  a=tts.generate(text,sid=sid,speed=speed); sf.write(out,np.array(a.samples),a.sample_rate); return len(a.samples)/a.sample_rate
if __name__=='__main__':
  print('num speakers',tts.num_speakers)
  import librosa
