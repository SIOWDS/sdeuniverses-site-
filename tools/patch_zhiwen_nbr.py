#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中华智问接上近邻检测；两页共用同一份闸门判据。

改前的实情：
  · `RUN.kbCtx` 在 run 启动时按**原初问题**取一次，且**只在第 1 轮**注入
    （`rnd===1 ? (kbCtx + 问题) : buildRoundUserMsg(...)`，而 buildRoundUserMsg 里那个 kb
    也是同一份 RUN.kbCtx）。六轮螺旋深化每一轮都在换焦点，用第一轮的底盘查到第六轮，
    等于后五轮没查。
  · 成文阶段（每台一篇 + 典范第四篇）**完全没有站内近邻名单**。
    它已有一个"第④步·最近邻判别"（本学科 3 个 + 上游母学科 2 个），这一点比金点子还早，
    但全凭基底自己的记忆——站上已发表过什么，它一无所知。

四处改动：
  ① 引入共用模块 `/taste/assets/sde-nbr-gate.js`（window.SDENbr）——判据只留一份，
     避免两页各存一份后各自漂移（这类漂移是静默的：某一关实际不再把关，无人收到报错）。
  ② 每轮按当轮主题重取上下文：种子 = 原初问题 + 上一轮摘要，取不到就沿用上一份。
  ③ 成文材料里注入**站内近邻名单**（`SDERag.neighbors`），并在 paperSystem 的任务说明里
     把近邻检测写成硬要求（含可解析的「（学科：XXX）」标注）。
  ④ 成文之后过三关：不过就**只补写那一节**（有界预算），拼回原文尾部，不整篇重写。
"""
import io, sys

P = "public/taste/zhiwen/index.html"
h = io.open(P, encoding="utf-8").read()
before = h

# ── ① 引入共用模块 ──
old = '<script src="/taste/assets/sde-rag.js?v=4"></script>'
assert old in h
h = h.replace(old, old + '\n<script src="/taste/assets/sde-nbr-gate.js?v=1"></script>', 1)
print("① 已引入 sde-nbr-gate.js（window.SDENbr，判据单一来源）")

# ── ② 每轮重取上下文 ──
old2 = """    const usr = rnd===1 ? ((RUN.kbCtx ? RUN.kbCtx + '\\n【问题】\\n' : '') + RUN.question) : buildRoundUserMsg(RUN.question, history, pendingFb);"""
new2 = """    // 每轮按**当轮主题**重取站内底盘：六轮螺旋每轮都在换焦点，
    // 拿第一轮的底盘用到第六轮等于后五轮没查。种子 = 原初问题 + 上一轮摘要。
    if(rnd > 1 && window.SDERag){
      try{
        const _seed = (RUN.question + ' ' + String((history[history.length-1]||{}).summary || (history[history.length-1]||{}).answer || '').slice(0,400)).trim();
        const _c = await window.SDERag.ctx(_seed);
        if(_c) RUN.kbCtx = _c;          // 取不到就沿用上一份，不把已有底盘清空
      }catch(_){}
    }
    const usr = rnd===1 ? ((RUN.kbCtx ? RUN.kbCtx + '\\n【问题】\\n' : '') + RUN.question) : buildRoundUserMsg(RUN.question, history, pendingFb);"""
assert old2 in h
h = h.replace(old2, new2, 1)
print("② 每轮按当轮主题重取 kbCtx（取不到沿用上一份）")

# ── ③ 成文注入站内近邻名单 + 规范里写成硬要求 ──
old3 = """function paperMaterials(question, summaries, finalAnswer){
  const parts = ['# 原始议题\\n\\n' + question + '\\n\\n',"""
new3 = """function paperMaterials(question, summaries, finalAnswer, nbrBlock){
  const parts = [];
  // 站内近邻名单前置：它不是语料，是一张要逐条交代的名单。放最前面，避免被两万字材料埋掉。
  if(nbrBlock) parts.push(nbrBlock + '\\n\\n');
  parts.push('# 原始议题\\n\\n' + question + '\\n\\n',"""
assert old3 in h
h = h.replace(old3, new3, 1)

NBR_REQ = r"""    + '\n\n【近邻检测 · NBR_CHECK_MARK（硬要求，缺此节即为不合格）】\n'
    + '文献综述之后、结论之前，必须有一节专门检测本文那个核心命名——证明它不能被现成概念无损替换：\n'
    + '· 一、材料里若给了【站内近邻】清单（sdeuniverses.com 已发表的相关篇目），逐条交代：那一篇说到哪一步、\n'
    + '  本文的判断与它的分离线在哪。划不出分离线的，直接写明重复并撤回命名，往矛盾更深处再结算一层，不要另起同义词。\n'
    + '  标注「本人已发」的尤其要查：同一个人把同一个概念发明两次，是最不容易被自己发现的一种重合。\n'
    + '· 二、库外近邻至少三个，每个给全四件：出处（作者、年份、作品，真实可查；记不准年份就不写年份，但不能编）／\n'
    + '  它已经说到哪一步（如实概述，不设稻草人）／分离线（写成可操作的判别）／一个判决性对照预测\n'
    + '  （"若观察到 X，则本文错、该近邻足够；若 Y，则本文成立"）。第四件是重心：没有对照预测的分离线等于没有分离线。\n'
    + '· 三、这三个里至少一个来自本议题所在领域**之外**的学科。同一个机制常常在别的学科里已被人用别的名字研究了几十年。\n'
    + '  【格式硬要求 · NBR_DISC_MARK】本节开头写一行「本文所属学科：XXX」，每个库外近邻的出处后紧跟「（学科：XXX）」。\n'
    + '  三个标注若全与「本文所属学科」相同，说明只在自家门内找了对手，至少换一个真正跨学科的近邻进来。\n'
"""
old4 = """    + '\\n\\n═══════════════════════ 任务说明 ═══════════════════════\\n\\n'
    + '你的任务是:\\n'"""
new4 = """    + '\\n\\n═══════════════════════ 任务说明 ═══════════════════════\\n\\n'""" + NBR_REQ + """    + '你的任务是:\\n'"""
assert old4 in h
h = h.replace(old4, new4, 1)
print("③ paperMaterials 支持近邻名单；paperSystem 加入近邻检测硬要求（含学科标注）")

# 两处成文调用：取名单 + 传进去
old5 = """    const pr = await streamChat(RUN.key, RUN.sel, paperSystem(agent, RUN.xinde['DS-'+agent]||''),
      paperMaterials(RUN.question, history.map(h=>h.summary||''), finalRound.answer||finalRound.summary||''),
      pb.body, pb.st, pb.meta, pb.el, PAPER_TOKENS);"""
new5 = """    // 成文前取一次站内近邻：种子 = 原初问题 + 末轮判断（论文的核心命名就长在末轮里）
    let _nb = '';
    if(window.SDERag){
      try{ _nb = await window.SDERag.neighbors((RUN.question + ' ' + String(finalRound.answer||finalRound.summary||'').slice(0,600)).trim(), { k:8 }); }catch(_){}
    }
    const pr = await streamChat(RUN.key, RUN.sel, paperSystem(agent, RUN.xinde['DS-'+agent]||''),
      paperMaterials(RUN.question, history.map(h=>h.summary||''), finalRound.answer||finalRound.summary||'', _nb),
      pb.body, pb.st, pb.meta, pb.el, PAPER_TOKENS);"""
assert old5 in h
h = h.replace(old5, new5, 1)

old6 = """        step3),
      pb.body, pb.st, pb.meta, pb.el, PAPER_TOKENS);"""
new6 = """        step3, _nb4),
      pb.body, pb.st, pb.meta, pb.el, PAPER_TOKENS);"""
assert old6 in h
h = h.replace(old6, new6, 1)

old7 = """  pb.open(); pb.st.innerHTML='<span class="spinner"></span> 把典范写成第四篇论文(约 2 万字)';
  let ptext='';"""
new7 = """  pb.open(); pb.st.innerHTML='<span class="spinner"></span> 把典范写成第四篇论文(约 2 万字)';
  // 典范这一篇的命名就在第③步里，拿它去取站内近邻
  let _nb4 = '';
  if(window.SDERag){ try{ _nb4 = await window.SDERag.neighbors((q + ' ' + String(step3||'').slice(0,600)).trim(), { k:8 }); }catch(_){} }
  let ptext='';"""
assert old7 in h
h = h.replace(old7, new7, 1)
print("   两处成文都取了站内近邻并传入")

# ── ④ 成文后过三关 ──
GATE = r"""// 近邻闸（三关）：判据来自共用模块 window.SDENbr（唯一来源）。
//   不过就**只补写那一节**再拼回原文尾部——不整篇重写：满功率配大任务会跑过平台时长上限、
//   落得"只有思考、正文 0 字"。模块没加载成功时整关跳过（宁可不查，不可误伤出稿）。
async function nbrGateFix(text, sys, question, nbrBlock, stEl){
  try{
    if(!text || !window.SDENbr) return text;
    const v = await window.SDENbr.verdict(text);
    if(!v.need) return text;
    if(stEl) stEl.innerHTML = '<span class="spinner"></span> ⚖ ' + v.why + '，正在补写近邻检测一节…';
    const fixUsr = '你刚写完下面这篇论文，但其中的【近邻检测】一节缺失或不合格（'+v.why+'）。\n'
      + '现在只补写这一节，不要重写论文、不要复述已有内容、不要写任何交代过程的话。\n\n'
      + '这一节必须做到：\n'
      + '· 站内近邻（下方清单，若有）逐条交代：它说到哪一步、你的分离线在哪；划不出就写明重复。\n'
      + '· 库外近邻至少三个，每个给全四件：出处（作者+年份+作品，真实可查，记不准年份就不写年份）／\n'
      + '  它已经说到哪一步／分离线（可操作的判别）／一个判决性对照预测。\n'
      + '· 这三个里至少一个来自本议题所在领域之外的学科。\n'
      + '· 本节开头写一行「本文所属学科：XXX」，每个库外近邻的出处后紧跟「（学科：XXX）」。\n\n'
      + (v.cross === false ? '【本次特别注意】上一稿的三个近邻全落在同一个学科里，请把其中至少一个换成真正来自别的学科的对手。\n\n' : '')
      + (v.block ? ('──── 按本文这个新命名重新查到的站内近邻（正文里没有提到，必须逐条交代）────\n' + v.block + '\n\n') : '')
      + (nbrBlock ? ('──── 站内近邻清单 ────\n' + nbrBlock + '\n\n') : '')
      + '直接以一个小节标题开始输出（例如"近邻检测：为什么这个命名不能被现成概念替换"），一千五百字以内。\n\n'
      + '──── 议题 ────\n' + String(question||'') + '\n\n──── 已写成的论文正文 ────\n' + String(text).slice(0,16000);
    const sink = document.createElement('div');
    const r = await streamChat(RUN.key, RUN.sel, sys, fixUsr, sink, { textContent:'' }, { textContent:'' }, null, 4000);
    const add = (r && r.text || '').trim();
    if(add && /近邻/.test(add)) return String(text).replace(/\s*$/, '') + '\n\n' + add + '\n';
  }catch(_){ /* 补不上就照原样：近邻检测是加固，不该成为整篇失败的理由 */ }
  return text;
}
function paperSystem(agentOrNull, xinde){"""
old8 = "function paperSystem(agentOrNull, xinde){"
assert old8 in h
h = h.replace(old8, GATE, 1)

# 两处成文后调用闸
old9 = """  if(!ptext){
    ptext = (finalRound.answer || finalRound.summary || '').trim();
    pb.st.textContent = (pb.st.textContent||'') + ' · 已用末轮收口全文兜底';
  }
  ptext = dejargonOutput(ptext);"""
new9 = """  if(!ptext){
    ptext = (finalRound.answer || finalRound.summary || '').trim();
    pb.st.textContent = (pb.st.textContent||'') + ' · 已用末轮收口全文兜底';
  }
  ptext = await nbrGateFix(ptext, paperSystem(agent, RUN.xinde['DS-'+agent]||''), RUN.question, _nb, pb.st);
  ptext = dejargonOutput(ptext);"""
assert old9 in h
h = h.replace(old9, new9, 1)

old10 = """  if(!ptext){ ptext = step3; pb.st.textContent=(pb.st.textContent||'')+' · 已用第③步典范全文兜底'; }
  ptext = dejargonOutput(ptext);"""
new10 = """  if(!ptext){ ptext = step3; pb.st.textContent=(pb.st.textContent||'')+' · 已用第③步典范全文兜底'; }
  ptext = await nbrGateFix(ptext, paperSystem(null, RUN.xinde['碰撞']||''), q, _nb4, pb.st);
  ptext = dejargonOutput(ptext);"""
assert old10 in h
h = h.replace(old10, new10, 1)
print("④ 两处成文之后都过三关（不过则只补写那一节）")

if h == before:
    print("没有改动"); sys.exit(1)
io.open(P, "w", encoding="utf-8").write(h)

# ── 金点子：三个判据改为优先用共用模块，本地实现留作兜底 ──
P2 = "public/taste/idea-generator/index.html"
g = io.open(P2, encoding="utf-8").read()
g0 = g
g = g.replace('<script src="/taste/assets/sde-rag.js?v=4"></script>',
              '<script src="/taste/assets/sde-rag.js?v=4"></script>\n<script src="/taste/assets/sde-nbr-gate.js?v=1"></script>', 1)
for fn, call in (("function nbrSectionOK(text){", "sectionOK"),
                 ("function coinedName(text){", "coinedName"),
                 ("function nbrCrossOK(text){", "crossOK")):
    assert fn in g, fn
    g = g.replace(fn, fn + "\n  // 判据的唯一来源是共用模块；本地实现只在模块没加载成功时兜底（避免两页各存一份后漂移）。\n"
                  + "  if(window.SDENbr && window.SDENbr." + call + ") return window.SDENbr." + call + "(text);", 1)
assert g != g0
io.open(P2, "w", encoding="utf-8").write(g)
print("⑤ 金点子三个判据改为优先走共用模块，本地实现留作兜底")
print("done")
