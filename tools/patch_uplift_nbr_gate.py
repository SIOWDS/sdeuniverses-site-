#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把近邻检测接进**二次提智**那一步。

为什么二次提智比初稿更要紧：
  这一步的动作就是"撤销先验 → 从矛盾更深处重新结算 → **精确命名**"。
  换句话说，它是整条流水线上**唯一会造出一个新词**的地方——而撞车只可能撞在新词上。
  初稿那一关查的是初稿那个名字；提智把名字换掉之后，先前那次检测就作废了。
  页面自己的注释也早已写着"二次提智是够不够创新/要不要撞已有命名的判定站"，
  但它注入的是 SDERag.ctx(原初问题)——那是语料块、是话题的近邻，
  既不是一张要交代的名单，也不是**新命名**的近邻。

四处改动：
  ① UPLIFT_SPEC 补上近邻检测节。提智是整篇重写，且已知会把学术规范剥掉
     （"补规范"这一步就是为收拾它而存在的）；不在提智的规范里明写，初稿写过的那一节会被删掉。
  ② 提智的近邻清单改**逐篇取**，种子是那篇待提升论文自己的正文，不再是四篇共用的原初问题。
  ③ 补写用 cfg.draftPrompt 当 system —— 原先硬写 paper1wPrompt()，
     在提智阶段会用第一批的规范去补一节，口径与全篇不一致。
  ④ 新增**命名后复查**：从提智稿里抽出那个新命名，拿它再查一次站内近邻；
     若查回来的篇目在稿里根本没被提到，就带着这份名单补写那一节。
     这是这次真正新加的一道——前一道查"有没有做检测"，这一道查"检测的是不是现在这个名字"。
"""
import io, sys

P = "public/taste/idea-generator/index.html"
h = io.open(P, encoding="utf-8").read()
before = h

# ── ① UPLIFT_SPEC 补近邻检测节 ──
i = h.index("const UPLIFT_SPEC = `")
j = h.index("\n`;", i)
seg = h[i:j]
assert "NBR_CHECK_MARK" not in seg, "UPLIFT_SPEC 已有近邻检测节"
UP_NBR = r"""
▍近邻检测（NBR_CHECK_MARK · 提智稿的硬要求，缺此节即为不合格）
这一步你会造出一个新词——而撞车只可能撞在新词上。所以命名之后，必须有一节专门检测这个**新命名**：

· 一、新命名先过站内。输入里若给了【站内近邻】清单，逐条交代：那一篇说到哪一步，你的新命名与它的分离线在哪。
  凡划不出分离线的，直接写明重复，并撤回这个命名、往矛盾更深处再结算一层——不要保留一个同义的新词。
  标注「本人已发」的那几篇尤其要查：同一个人把同一个概念发明两次，是最不容易被自己发现的一种重合。

· 二、库外近邻至少三个，每个给全四件：出处（作者、年份、作品，真实可查；记不准年份就不写年份，但不能编）／
  它已经说到哪一步（如实概述，不设稻草人）／分离线（写成可操作的判别）／
  一个判决性对照预测（"若观察到 X，则本文错、该近邻足够；若 Y，则本文成立"）。
  第四件是重心：没有对照预测的分离线，等于没有分离线。

· 三、这三个里至少一个来自问题所在领域**之外**的学科。同一个机制常常在别的学科里已被人用别的名字研究了几十年，
  而领域内的对手往往离得更远——只在本领域找对手，是这类论文最常见也最致命的漏洞。

注意：提智把思想做深，但不许把这一节做掉。整篇重写时，这一节要跟着新命名重写，不是把初稿那一节照搬过来。
"""
h = h[:j] + "\n" + UP_NBR.strip("\n") + h[j:]
print("① UPLIFT_SPEC：已追加近邻检测节")

# ── ② 提智的近邻清单逐篇取 ──
old2 = """    // 二次提智是\"够不够创新/要不要撞已有命名\"的判定站 → 强注入全站上下文
    let _upCtx=''; { const _upq=(window._lastResult && window._lastResult.question)||''; if(window.SDERag && _upq){ try{ _upCtx = await window.SDERag.ctx(_upq); }catch(_){} } }"""
new2 = """    // 二次提智是\"够不够创新/要不要撞已有命名\"的判定站 → 全站语料上下文照旧注入，
    // 但\"要不要撞已有命名\"这件事靠的不是语料块，而是一张要逐条交代的近邻名单：
    // 语料块让基底知道得更多，名单才逼它说清分离线。且名单必须**逐篇**取——
    // 四篇提智的是四个不同的命名，共用一份按原初问题取的清单等于没查。
    const _upq0=(window._lastResult && window._lastResult.question)||'';
    const _upAu=(window._lastResult && window._lastResult.author)||'';
    let _upCtx=''; if(window.SDERag && _upq0){ try{ _upCtx = await window.SDERag.ctx(_upq0); }catch(_){} }
    const _upNbrs = await Promise.all(defs.map(async (d)=>{
      if(!window.SDERag) return '';
      try{ return await window.SDERag.neighbors((_upq0+' '+String((d.src&&d.src.text)||'').slice(0,600)).trim(), { k:8, author:_upAu }); }
      catch(_){ return ''; }
    }));"""
assert old2 in h
h = h.replace(old2, new2, 1)

old2b = "      writeInput: buildUpliftInput(d.src.text, _upCtx),  // 输入 = 第一批那篇全文 + 全站上下文"
new2b = "      writeInput: buildUpliftInput(d.src.text, ((_upNbrs[i]||'') + (_upNbrs[i]&&_upCtx?'\\n\\n':'') + (_upCtx||''))),  // 输入 = 第一批那篇全文 + 本篇的站内近邻名单 + 全站上下文"
assert old2b in h
h = h.replace(old2b, new2b, 1)
print("② 提智的近邻清单：改为逐篇取，并与语料块一起注入")

# ── ③ 补写改用 cfg.draftPrompt ──
old3 = """      const fixed = await streamChat(cfg.writeKey, cfg.writeSel, paper1wPrompt(),
        NBR_FIX_INPUT(paperText, cfg.writeInput), fixSink, dummy, dummy, 4000);"""
new3 = """      // system 用本阶段自己的规范（cfg.draftPrompt）：提智阶段若拿第一批的规范去补，
      // 补出来的那一节口径与全篇不一致。
      const fixed = await streamChat(cfg.writeKey, cfg.writeSel, (cfg.draftPrompt || paper1wPrompt()),
        NBR_FIX_INPUT(paperText, cfg.writeInput), fixSink, dummy, dummy, 4000);"""
assert old3 in h
h = h.replace(old3, new3, 1)
print("③ 补写的 system 改用本阶段规范")

# ── ④ 命名后复查 ──
old4 = """function NBR_FIX_INPUT(paperText, writeInput){"""
new4 = r"""// coinedName：从稿子里抽出那个新造的命名。抽不出就返回空串——
//   抽不出不等于没命名，所以复查这一关只在抽得出时才做（宁可漏查，不可乱查）。
function coinedName(text){
  const t = String(text||'').slice(0, 20000);
  const pats = [
    /(?:本文|我)(?:将(?:其|这|之)?|把(?:它|这|其)?[^。\n]{0,12})?命名为[「“"《【]?([^」”"》】，。；\n]{2,14})/,
    /命名为[「“"《【]?([^」”"》】，。；\n]{2,14})/,
    /(?:本文|我)(?:提出|称(?:之为)?)[「“"《【]([^」”"》】]{2,14})/,
    /将这一(?:机制|结构|动作|状态|过程)称(?:之)?为[「“"《【]?([^」”"》】，。；\n]{2,14})/
  ];
  for(const p of pats){ const m = t.match(p); if(m && m[1]) return m[1].trim(); }
  return '';
}
// nbrPostNameGap：拿新命名再查一次站内近邻，返回"稿里根本没提到"的那几篇。
//   前一道闸查的是"有没有做检测"，这一道查的是"检测的是不是现在这个名字"——
//   提智会把名字换掉，先前那次检测随之作废。
async function nbrPostNameGap(paperText){
  const name = coinedName(paperText);
  if(!name || !window.SDERag) return { name:'', block:'', missed:[] };
  let blk = '';
  try{ blk = await window.SDERag.neighbors(name, { k:6 }); }catch(_){ return { name:name, block:'', missed:[] }; }
  if(!blk) return { name:name, block:'', missed:[] };
  const titles = (blk.match(/《([^》]{2,60})》/g)||[]).map(s=>s.slice(1,-1));
  const missed = [];
  for(const t of titles){
    const head = t.replace(/[：:—\-·].*$/,'').slice(0,10);
    if(head && paperText.indexOf(head) < 0) missed.push(t);
  }
  return { name:name, block:blk, missed:missed };
}
function NBR_FIX_INPUT(paperText, writeInput, extraBlock){"""
assert old4 in h
h = h.replace(old4, new4, 1)

# NBR_FIX_INPUT 末尾接上 extraBlock
old4b = """    + '──── 这篇论文的写作输入（含站内近邻清单，若有）────\\n' + String(writeInput||'').slice(0,4000)"""
new4b = """    + (extraBlock ? ('──── 按本文这个新命名重新查到的站内近邻（这几篇正文里没有提到，必须逐条交代）────\\n' + extraBlock + '\\n\\n') : '')
    + '──── 这篇论文的写作输入（含站内近邻清单，若有）────\\n' + String(writeInput||'').slice(0,4000)"""
assert old4b in h
h = h.replace(old4b, new4b, 1)

# 闸门主体：加第二关
old4c = """  try{
    if(paperText && !nbrSectionOK(paperText)){
      setStat('⚖ 近邻检测未达标，正在补写这一节…');"""
new4c = """  try{
    // 第二关（命名后复查）：拿稿子里那个新命名再查一次站内近邻，
    // 把"稿里根本没提到"的那几篇挑出来。为空则这一关自动通过。
    let _pn = { name:'', block:'', missed:[] };
    try{ _pn = await nbrPostNameGap(paperText); }catch(_){}
    const _needFix = paperText && (!nbrSectionOK(paperText) || _pn.missed.length > 0);
    if(_needFix){
      setStat(_pn.missed.length ? ('⚖ 新命名「'+_pn.name+'」还有 '+_pn.missed.length+' 篇站内近邻未交代，正在补写…')
                                : '⚖ 近邻检测未达标，正在补写这一节…');"""
assert old4c in h
h = h.replace(old4c, new4c, 1)

old4d = """        NBR_FIX_INPUT(paperText, cfg.writeInput), fixSink, dummy, dummy, 4000);"""
new4d = """        NBR_FIX_INPUT(paperText, cfg.writeInput, (_pn.missed.length ? _pn.block : '')), fixSink, dummy, dummy, 4000);"""
assert old4d in h
h = h.replace(old4d, new4d, 1)
print("④ 加入命名后复查（抽出新命名 → 再查一次 → 未交代的篇目带进补写）")

if h == before:
    print("没有改动"); sys.exit(1)
io.open(P, "w", encoding="utf-8").write(h)
print("done")
