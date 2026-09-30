import sherpa_onnx, numpy as np
def kokoro():
  d='kokoro-multi-lang-v1_1/'
  return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
   model=d+'model.onnx',voices=d+'voices.bin',tokens=d+'tokens.txt',data_dir=d+'espeak-ng-data',dict_dir=d+'dict',
   lexicon=d+'lexicon-us-en.txt,'+d+'lexicon-zh.txt'),num_threads=4),rule_fsts=d+'date-zh.fst,'+d+'phone-zh.fst,'+d+'number-zh.fst'))
def baker():
  d='matcha-icefall-zh-baker/'
  return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
   acoustic_model=d+'model-steps-3.onnx',vocoder='vocos-22khz-univ.onnx',lexicon=d+'lexicon.txt',tokens=d+'tokens.txt',dict_dir=d+'dict'),num_threads=4),
   rule_fsts=d+'phone.fst,'+d+'date.fst,'+d+'number.fst'))
def melo():
  d='vits-melo-tts-zh_en/'
  return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(
   model=d+'model.onnx',lexicon=d+'lexicon.txt',tokens=d+'tokens.txt',dict_dir=d+'dict'),num_threads=4),
   rule_fsts=d+'date.fst,'+d+'phone.fst,'+d+'new_heteronym.fst,'+d+'number.fst'))
