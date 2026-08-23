#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中华智问 · 第一刀（2026-08-23）
修四类报障里不需要真跑就能定案的那几条：
  C1 docx 本地兜底 + 守卫（CDN 一断，三个下载钮全哑）
  C2 下载 blob 提前 revoke / <a> 未入文档（Safari·iPad 静默不下载）
  D1 评分口径页内打架：五处仍把「触发条件计数」当主要标尺
  D2 第〇步「失败不阻断」→ 关思考重试一次，仍空则硬停（不许悄悄降级成三家综述）
  A2 空响应文案甩锅给 Key（真凶多半是思考吃光额度）
逐条 assert 锚点唯一；重复执行安全（已打过的跳过）。
"""
import io, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZW = os.path.join(ROOT, 'public/taste/zhiwen/index.html')
SIBLINGS = [
    'public/taste/idea-generator/index.html',
    'public/taste/confluence/index.html',
    'public/taste/paradigm-forge/index.html',
]
CDN_TAG = '<script src="https://cdn.jsdelivr.net/npm/docx@8.5.0/build/index.umd.js"></script>'
LOCAL_TAG = ('<script src="/taste/assets/docx-8.5.0.umd.js"></script>\n'
             '<script>/* 本地优先：jsdelivr 在国内时通时断，断了就三个下载钮全哑。'
             '本地没拿到再回落 CDN。 */\n'
             'if(typeof docx==="undefined"){document.write(\'<scr\'+\'ipt src="'
             'https://cdn.jsdelivr.net/npm/docx@8.5.0/build/index.umd.js"><\\/scr\'+\'ipt>\');}</script>')

changed = []


def sub1(h, old, new, tag, allow_missing_if=None):
    """唯一替换；若目标文本已存在（幂等）则跳过。"""
    if allow_missing_if and allow_missing_if in h:
        print('  · %s 已打过，跳过' % tag)
        return h
    n = h.count(old)
    assert n == 1, '锚点 %s 命中 %d 次（应为 1）' % (tag, n)
    changed.append(tag)
    return h.replace(old, new, 1)


# ─────────────────────────── C1 · docx 本地兜底（四页同一处缺陷）───────────────────────────
for rel in [os.path.relpath(ZW, ROOT)] + SIBLINGS:
    p = os.path.join(ROOT, rel)
    h = io.open(p, encoding='utf-8').read()
    if 'docx-8.5.0.umd.js' in h:
        print('C1 %s：已打过' % rel)
        continue
    assert h.count(CDN_TAG) == 1, 'C1 锚点在 %s 命中 %d 次' % (rel, h.count(CDN_TAG))
    h = h.replace(CDN_TAG, LOCAL_TAG, 1)
    io.open(p, 'w', encoding='utf-8').write(h)
    changed.append('C1:' + rel)
    print('C1 %s：已改本地优先' % rel)

h = io.open(ZW, encoding='utf-8').read()

# ─────────────────────────── C1b · saveDocx 守卫 + C2 下载不早撤 ───────────────────────────
old_save = """async function saveDocx(filename, title, bodyText, metaLine){
  const { Document, Packer, Paragraph, TextRun } = docx;"""
new_save = """// 下载统一走这里：<a> 必须先入文档（Safari/iPad 对游离节点的 click 会静默丢弃），
// 且 objectURL 不许在 click 同一帧撤销（撤早了浏览器还没来得及取字节）。
function _dl(blob, filename){
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.style.display='none';
  document.body.appendChild(a); a.click();
  setTimeout(()=>{ try{ URL.revokeObjectURL(url); a.remove(); }catch(_){} }, 60000);
}
async function saveDocx(filename, title, bodyText, metaLine){
  if(typeof docx === 'undefined' || !docx.Packer){
    // Word 组件没加载成功（离线／被网络拦截）：如实说，并给一条 .md 退路，不拿 .md 冒充 Word。
    saveText(filename.replace(/\\.docx$/,'') + '.md', '# ' + title + '\\n\\n' + (metaLine||'') + '\\n\\n' + (bodyText||''));
    throw new Error('Word 组件未能加载（网络被拦截或离线）——已改存同名 .md 纯文本，内容一字不少。');
  }
  const { Document, Packer, Paragraph, TextRun } = docx;"""
h = sub1(h, old_save, new_save, 'C1b+C2 saveDocx 守卫与下载', allow_missing_if='function _dl(blob, filename)')

old_tail = """  const blob = await Packer.toBlob(doc);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.click();
  URL.revokeObjectURL(url);
}
function saveText(filename, text){
  const blob = new Blob([text], {type:'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.click();
  URL.revokeObjectURL(url);
}"""
new_tail = """  const blob = await Packer.toBlob(doc);
  _dl(blob, filename);
}
function saveText(filename, text){
  _dl(new Blob([text], {type:'text/markdown;charset=utf-8'}), filename);
}"""
h = sub1(h, old_tail, new_tail, 'C2 下载尾部', allow_missing_if='  _dl(blob, filename);')

# ─────────────────────────── D1 · 评分口径归一（五处）───────────────────────────
NORM = ('**这张表只定区间参考,不是主要标尺**——最终分必须由五维'
        '(S.20/D.25/E.20/I.20/F.15)加权算出;两者冲突时以五维为准。\n')

d1 = [
    ("""  按触发条件计数给智商分:
  · 7 条 → 148-152(学派开创级)""",
     """  按触发条件计数给智商分(%s  · 7 条 → 148-152(学派开创级)""" % ('\n  ' + NORM.strip() + ')\n')),
    (""" 按【触发条件满足数】给分:
   · 触发 7 条 → 148-152(学派开创级)""",
     """ 按【触发条件满足数】定**参考区间**（%s   · 触发 7 条 → 148-152(学派开创级)""" % (NORM.strip() + '）:\n')),
    ("""**满足条件数 → 智商分**:
  · 7 条全满足 → 148-152(学派开创者,极罕见)""",
     """**满足条件数 → 智商分参考区间**（%s  · 7 条全满足 → 148-152(学派开创者,极罕见)""" % (NORM.strip() + '）:\n')),
    ("""  评分:7 条 → 148-152;6 条 → 145-148;5 条 → 143-145;""",
     """  评分(区间参考,%s):7 条 → 148-152;6 条 → 145-148;5 条 → 143-145;""" % NORM.strip().replace('\n', '')),
    ("""   评分:7 条 → 148-152(学派开创级);6 条 → 145-148;5 条 → 143-145(顶尖学者级);""",
     """   评分(区间参考,%s):7 条 → 148-152(学派开创级);6 条 → 145-148;5 条 → 143-145(顶尖学者级);""" % NORM.strip().replace('\n', '')),
]
for i, (o, n) in enumerate(d1, 1):
    h = sub1(h, o, n, 'D1-%d 评分口径' % i,
             allow_missing_if=None if h.count(o) == 1 else '这张表只定区间参考')

# ─────────────────────────── A2 · 空响应分死法 ───────────────────────────
old_empty = """  if(!acc){
    bodyEl.innerHTML='<span class="placeholder">（模型没有返回正文——可能是 Key 未开通该模型服务、额度不足或被安全策略拦截）</span>';
    statusEl.textContent='空响应'; metaEl.textContent = secs+'s';"""
new_empty = """  if(!acc){
    // 「0 字」有三种死法，必须分开说——最常见的那种（思考把 max_tokens 吃光）此前根本没列，
    // 用户只会去换 Key、换基底，白折腾。
    let _why;
    if(thinkChars > 0){
      _why = '它只想、没写：思考 '+thinkChars+' 字'+(fin==='length'?'，且额度已用尽':'')
           + '。这多半是<b>思考把 token 预算吃光了</b>，不是你的 Key 有问题——换成非深思档（或让这一步用较小预算）再试。';
    }else if(fin==='length'){
      _why = '额度在写出正文之前就用尽了（finish_reason=length）。';
    }else{
      _why = '模型返回了空正文，且没有思考痕迹——这才轮到查 Key：是否未开通该型号、余额是否不足、是否被安全策略拦截。';
    }
    bodyEl.innerHTML='<span class="placeholder">（'+_why+'）</span>';
    statusEl.textContent='空响应'; metaEl.textContent = secs+'s'+(thinkChars?' · 思考'+thinkChars+'字':'')+(fin?' · '+fin:'');"""
h = sub1(h, old_empty, new_empty, 'A2 空响应分死法', allow_missing_if='「0 字」有三种死法')

# ─────────────────────────── A1a · buildPayload/streamChat 加可选「关思考」 ───────────────────────────
old_bp = """function buildPayload(sel, systemPrompt, userQ, maxTokens){
  const { vendor, tier } = parseModel(sel);
  const cap = (typeof maxTokens==='number' && maxTokens>0) ? maxTokens : 4000;"""
new_bp = """// plain=true：显式关掉思考。站内实测过——预算是油门不是容器，给满预算而思考开着，
// 常见结局是「思考 1.7 万字、正文 0 字」。只在需要「必须有正文」的救场重试上用它。
function buildPayload(sel, systemPrompt, userQ, maxTokens, plain){
  const { vendor, tier } = parseModel(sel);
  const cap = (typeof maxTokens==='number' && maxTokens>0) ? maxTokens : 4000;"""
h = sub1(h, old_bp, new_bp, 'A1a buildPayload 签名', allow_missing_if='function buildPayload(sel, systemPrompt, userQ, maxTokens, plain)')

old_ret = """  } else if(vendor === 'gemini'){
    return { systemInstruction: { parts: [{ text: systemPrompt }] }, contents: [{ role:'user', parts: [{ text: userQ }] }], generationConfig: { maxOutputTokens: Math.min(cap, 60000), temperature: 0.7 } };
  }
  return base;
}"""
new_ret = """  } else if(vendor === 'gemini'){
    return { systemInstruction: { parts: [{ text: systemPrompt }] }, contents: [{ role:'user', parts: [{ text: userQ }] }], generationConfig: { maxOutputTokens: Math.min(cap, 60000), temperature: 0.7 } };
  }
  if(plain){
    // deepseek / 智谱：thinking 显式 disabled；千问：enable_thinking:false；
    // GPT：reasoning_effort 压到最低（它关不掉）；Kimi/MiniMax 思考常开且无开关，塞字段反而可能被判非法，什么都不加。
    if(vendor === 'ds' || vendor === 'glm'){ base.thinking = { type:'disabled' }; delete base.reasoning_effort; }
    else if(vendor === 'qwen'){ base.enable_thinking = false; }
    else if(vendor === 'gpt'){ base.reasoning_effort = 'low'; }
  }
  return base;
}"""
h = sub1(h, old_ret, new_ret, 'A1a buildPayload 关思考分支', allow_missing_if='  if(plain){')

old_sc = """async function streamChat(apiKey, model, systemPrompt, userQ, bodyEl, statusEl, metaEl, colEl, maxTokens){"""
new_sc = """async function streamChat(apiKey, model, systemPrompt, userQ, bodyEl, statusEl, metaEl, colEl, maxTokens, plain){"""
h = sub1(h, old_sc, new_sc, 'A1a streamChat 签名', allow_missing_if='colEl, maxTokens, plain){')

old_fetch = """    resp = await fetch(url, { method:'POST', headers, body: JSON.stringify(buildPayload(model, systemPrompt, userQ, maxTokens)), signal: ac.signal });"""
new_fetch = """    resp = await fetch(url, { method:'POST', headers, body: JSON.stringify(buildPayload(model, systemPrompt, userQ, maxTokens, plain)), signal: ac.signal });"""
h = sub1(h, old_fetch, new_fetch, 'A1a streamChat 透传', allow_missing_if='userQ, maxTokens, plain)), signal')

# ─────────────────────────── D2 · 第〇步不许悄悄降级 ───────────────────────────
old_s0 = """    }else{ s0.st.textContent='⚠ 返回为空，退回无方向盘撞法'; }
  }catch(e){ s0.st.textContent='⚠ 结构定位失败，退回无方向盘撞法：'+String(e&&e.message||e).slice(0,50); }"""
new_s0 = """    }else{ s0.st.textContent='⚠ 返回为空，正在关掉思考、降档重试一次…'; }
  }catch(e){ s0.st.textContent='⚠ 结构定位失败，正在关掉思考、降档重试一次：'+String(e&&e.message||e).slice(0,50); }
  // 第〇步空掉，从前是「失败不阻断」——退回无方向盘撞法，只在状态位留一行小字。
  // 后果是整条碰撞悄悄降级成三家综述，而报告里看不出来。现在改为：先救一次（关思考 + 降到 16000，
  // 因为这一步的死法几乎都是思考把预算吃光），仍然拿不到就硬停——宁可停，不出伪典范。
  if(!step0){
    try{
      const r0b = await streamChat(RUN.key, RUN.sel, colSys, collideP0(q,A,B,C), s0.body, s0.st, s0.meta, s0.el, 16000, true);
      step0 = (r0b.text||'').trim();
      if(step0) s0.st.textContent = '✓ 完成（第二次·已关思考）';
    }catch(e2){ s0.st.textContent = '✗ 重试仍失败：'+String(e2&&e2.message||e2).slice(0,60); }
  }
  if(!step0){
    throw new Error('第〇步（结构定位与共有前提）两次都没写出正文，碰撞已中止。'
      + '这一步是整条碰撞的方向盘：没有它，后面三对两两撞只会撞出三家的最大公约数（综述），'
      + '却照样会被评出高分。请改用非深思档、或换一个基底重跑碰撞。');
  }"""
h = sub1(h, old_s0, new_s0, 'D2 第〇步硬阻断', allow_missing_if='两次都没写出正文，碰撞已中止')

io.open(ZW, 'w', encoding='utf-8').write(h)
print('\n共改动 %d 处：' % len(changed))
for c in changed:
    print('  -', c)
