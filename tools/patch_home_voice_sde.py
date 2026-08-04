#!/usr/bin/env python3
# 首页挂「SDE 语音解析」入口：顶部智能体条一颗 chip ＋ 品尝区一张卡（其十六，置顶）。
# 铁律：新页面必须同 commit 挂导航——孤儿页 = 没交付。
# 所有替换都先 assert 锚定，改完做标签配对检查。
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
IDX = ROOT / "public/index.html"
h = IDX.read_text(encoding="utf-8")
orig = h

# ── ① 顶部智能体条：插在「免费品尝全部」那颗之前 ──
FLAME = ('<span class="ag-flame" aria-hidden="true">'
         '<i class="ag-ember" style="left:22%;animation-delay:0s"></i>'
         '<i class="ag-ember" style="left:50%;animation-delay:0.5s"></i>'
         '<i class="ag-ember" style="left:78%;animation-delay:1.0s"></i></span>')
CHIP = ('  <a href="/taste/voice-sde/" class="ag-chip ag-pill ag-c5" role="group" aria-label="SDE语音解析">'
        + FLAME +
        '<span class="ag-label zh-only">🎙 SDE语音解析</span>'
        '<span class="ag-label en-only">🎙 Voice to SDE</span></a>\n')

anchor_all = '  <a href="#taste" class="ag-chip ag-tag ag-c6" role="group" aria-label="SDE智能体免费品尝">'
assert anchor_all in h, "找不到智能体条的『免费品尝全部』锚点"
assert "/taste/voice-sde/" not in h, "首页上已经有语音解析入口了，别重复插"
h = h.replace(anchor_all, CHIP + anchor_all, 1)

# ── ② 品尝区：新卡置顶（放在卡1之前）──
CARD = '''      <!-- 卡0：SDE 语音解析（可用·置顶新上线） -->
      <a href="/taste/voice-sde/" style="display:block;background:#161B22;border:1px solid rgba(155,123,212,0.45);border-top:3px solid #9B7BD4;border-radius:14px;padding:28px 24px;text-decoration:none;transition:transform .15s,border-color .2s" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size:30px;margin-bottom:14px">🎙</div>
        <div class="zh-only" style="font-size:11px;letter-spacing:0.2em;color:#B79BE8;margin-bottom:8px">其十六 · 现已上线</div>
        <div class="en-only" style="font-size:11px;letter-spacing:0.2em;color:#B79BE8;margin-bottom:8px">NO.16 · LIVE</div>
        <div class="zh-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:8px">SDE 语音解析</div>
        <div class="en-only" style="font-size:19px;font-weight:700;color:#E6EDF3;margin-bottom:8px">Voice to SDE</div>
        <div class="zh-only" style="font-size:13.5px;color:#8B98A5;line-height:1.7"><b style="color:#C4B0E0">录下来，出文字，再把这番话拆开看。</b>开麦克风或摄像头讲，也可以直接拖进已有的音视频文件——它在你停顿的地方自己切段、切一段转一段，边讲边出字。转写稿再交给 WDS：<b style="color:#C4B0E0">他到底主张了什么、哪些前提根本没说出口、这番话的 S/D/E 各是什么、缝隙与断链在哪、当场可以问他哪三个问题</b>。说出来的话不能按文章读——观点埋在重复与迂回里，语气强度本身就是信息。三条转写通道任选（本机 Whisper 免费离线／智谱 GLM-ASR／浏览器听写），音视频只在你这台机器上</div>
        <div class="en-only" style="font-size:13.5px;color:#8B98A5;line-height:1.7">Record from your mic or camera, or drop in an audio/video file. It cuts at your pauses and transcribes segment by segment as you speak. Then WDS reads the transcript the way speech has to be read: what was actually claimed, which premises were never said out loud, the S/D/E of the talk, where the gaps and broken links are, and three questions you could ask on the spot. Three transcription channels; the media never leaves your machine</div>
        <div style="margin-top:16px;color:#B79BE8;font-size:14px;font-weight:700">立即品尝 →</div>
      </a>

'''
anchor_card = '      <!-- 卡1：创新智商评分官（可用·置顶） -->'
assert anchor_card in h, "找不到品尝区卡1锚点"
h = h.replace(anchor_card, CARD + anchor_card, 1)

# ── ③ 自检 ──
# 编号不许重复（book-club 那次撞过：作文共创与占位卡都写着「其十一」）
nums = re.findall(r'>(其[一二三四五六七八九十]+) · (?:现已上线|即将上线)<', h)
dup = {n for n in nums if nums.count(n) > 1}
assert not dup, f"品尝区编号重复：{dup}"
assert nums.count("其十六") == 1, "其十六 应当只出现一次"

# 中英双份（首页铁律⑥）
assert h.count('/taste/voice-sde/') == 2, f"入口数不对：{h.count('/taste/voice-sde/')}（应为 2：智能体条 + 品尝卡）"
assert h.count('SDE 语音解析') >= 1 and h.count('Voice to SDE') >= 2, "中英文案没配齐"

# 标签配对：改完的开闭标签数必须与改前差值一致（新卡是一个 <a>，chip 是一个 <a>）
for tag in ("div", "a", "script", "style", "section"):
    o_open = len(re.findall(rf'<{tag}[\s>]', orig)); o_close = orig.count(f'</{tag}>')
    n_open = len(re.findall(rf'<{tag}[\s>]', h));    n_close = h.count(f'</{tag}>')
    assert (n_open - o_open) == (n_close - o_close), f"<{tag}> 开闭数不平衡：+{n_open-o_open} 开 / +{n_close-o_close} 闭"

IDX.write_text(h, encoding="utf-8")
print(f"首页已挂入口：智能体条 chip + 品尝区其十六（+{len(h)-len(orig)} 字节）")
