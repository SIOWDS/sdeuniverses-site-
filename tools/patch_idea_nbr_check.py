#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「近邻检测」装进金点子发生器的**写文章**阶段。

为什么改的是写文章这一步，而不是九宫格提问：
  九宫格那一步产出的是判断，还没命名；真正会撞车的是**论文里那个被命名的新概念**。
  2026-07-29 全天十几批发稿的账很清楚：扣分几乎从不在论证质量，全在"最近的那个对手没上桌"。
  而且两次差点出事都出在同一处——张琼《自噬性稳态》与她自己已发的《自噬性适应》，
  是人工审稿发现的，不是流程发现的。

四处改动：
  ① sde-rag.js 的 neighbors() 改打新端点 /api/kb/neighbors
     —— 旧实现是从 /api/kb/retrieve 的块里筛几行，**只给标题、不给链接也不给那篇的判断**，
     基底看不出每篇主张什么，也就无从划分离线；且召回走语料匹配，会漏掉
     概念名只写在副标题或关键词里的那些篇（恰恰是最该召回的）。新端点两样都补上，
     并且标注"本人已发"。旧路保留为兜底。
  ② 提问里新增**必须交付的一节「近邻检测」**：站内逐条交代 + 库外四件套
     （出处／它已经说到哪一步／分离线／一个判决性对照预测）+ 至少一个跨学科近邻。
     跨学科那一条是照着当天的账加的——所有人的扣分都压在跨域这一维上。
  ③ 近邻清单改成**逐篇取**：原先四篇共用一份按"原初问题"取的清单，
     那是话题的近邻，不是这篇论文那个命名的近邻。改为每篇拿自己的核心判断去取。
  ④ 初稿后加一道**近邻闸**：没有那一节、或点名不足 3 个，就单独补写这一节再拼回去。
     为什么是"补写一节"而不是"整篇重写"：满功率 + 大任务 = 只有思考、正文 0 字，
     站上踩过两次（见 knowledge-base-structuring）。补写是小任务、有界预算，安全。
"""
import io, sys

# ═══ ① sde-rag.js ═══
P1 = "public/taste/assets/sde-rag.js"
s = io.open(P1, encoding="utf-8").read()
old = s[s.index("  async function neighbors(q) {"):s.index("  // 便捷包装：把上下文拼到一段用户文本前")]
new = '''  // neighbors(q, opts)：站内近邻清单。走专用端点 /api/kb/neighbors——
  //   它给的是【标题 + 链接 + 那篇自己的一句话判断 + 是否本人已发】，并已同题去重。
  //   这三样缺一样，基底就没法真的划分离线：只有标题时它只能猜那篇讲什么。
  //   opts.author 传学员 slug/姓名 → 自己已发的篇目会被标注（不排除：自我重复最难自查）。
  //   端点不可用或无命中时，退回旧的 retrieve 筛行法，保证老行为不丢。
  async function neighbors(q, opts) {
    opts = opts || {};
    var k = _ckey(q, 'nbr2|' + (opts.author || '') + '|' + (opts.k || 8), 16, 4000);
    if (k in _cache) return _cache[k];
    try {
      var r = await fetch('/api/kb/neighbors', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ q: String(q || '').slice(0, 2000), k: opts.k || 8, author: opts.author || '' })
      });
      if (r.ok) {
        var j = await r.json();
        if (j && j.block) return (_cache[k] = j.block);
      }
    } catch (e) {}
    return (_cache[k] = await _neighborsLegacy(q));
  }
  // 旧实现（兜底）：从 retrieve 的块里筛九库结构行 + 标题清单。
  async function _neighborsLegacy(q) {
    var r = await _fetch(q, 16, 4000);
    var block = r.block || '';
    var srcs = r.srcs || [];
    if (!block && !srcs.length) return '';
    var lines = block.split('\\n');
    var kept = [];
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      if (/^【全站原文片段】/.test(ln)) break;
      if (/^[▶·]/.test(ln)) kept.push(ln);
    }
    var srcList = srcs.slice(0, 10).map(function (s) { return '· ' + (s.t || ''); }).join('\\n');
    var out = '';
    if (kept.length || srcList) {
      out = '【SDE 站内已有最近邻（避免与下列已发表的命名/判断重复；如与之相邻，请显式划清分工，不要重造同义词）】\\n'
        + (kept.length ? kept.join('\\n') + '\\n' : '')
        + (srcList ? '\\n【已有相关文章】\\n' + srcList : '');
    }
    return out;
  }

'''
assert old in s
s = s.replace(old, new, 1)
io.open(P1, "w", encoding="utf-8").write(s)
print("① sde-rag.js：neighbors() 改打 /api/kb/neighbors，旧路留作兜底")

# ═══ ②③④ idea-generator ═══
P2 = "public/taste/idea-generator/index.html"
h = io.open(P2, encoding="utf-8").read()
before = h

# ② 近邻检测节的规范（单一来源，两份论文规范都追加它）
NBR_SPEC = r"""
▍近邻检测（NBR_CHECK_MARK · 硬要求，缺此节即为不合格）
在正文的理论建构立起来之后、结论之前，必须有一节专门做近邻检测。这一节不是文献综述，是一次自证：
证明你这个命名不能被现成的东西无损替换掉。写法有三条硬规矩：

· 一、站内近邻逐条交代。输入里若给了【站内近邻】清单，对其中每一篇都要处理：说清它已经说到哪一步，
  以及你这一次的判断与它的分离线在哪。凡划不出分离线的，直接写明"本文与该篇重复"，撤回你的命名、
  往矛盾更深处再结算一层——不要另起一个同义的新词。标注「本人已发」的那几篇尤其要查：
  同一个作者在同一个领域里把一个概念发明两次，是最不容易被自己发现的一种重合。

· 二、库外近邻至少三个，每个都要给全四件东西：
  （1）出处——作者、年份、作品名，必须是真实存在可查证的；想不起确切年份就不要写年份，但不能编。
  （2）它已经说到哪一步——用一两句话如实概述那个概念的主张，不要贬低成稻草人。
  （3）分离线——你的判断切开了它装不下的什么。要写成可操作的判别，不要只说"不同"。
  （4）一个判决性对照预测——"若观察到 X，则本文错、该近邻足够；若观察到 Y，则本文成立"。
      这一条是整节的重心：没有对照预测的分离线，等于没有分离线。

· 三、这三个近邻里，**至少一个必须来自问题所在领域之外的学科**。原因很实在：
  同一个机制常常在别的学科里已经被人用别的名字研究了几十年，而领域内的对手往往离得更远。
  只在本领域内找对手，是这类论文最常见也最致命的漏洞。

近邻找不到不是本事，是没找够——最像的那几个一定存在。若通篇找不出任何近邻，说明你的命名太模糊，
先把它收紧到能被对手瞄准的程度。
"""

for mark, spec_name in (("const PAPER_SPEC_1W = `", "PAPER_SPEC_1W"), ("const PAPER_SPEC = `", "PAPER_SPEC")):
    i = h.index(mark)
    j = h.index("\n`;", i)
    body = h[i:j]
    assert "NBR_CHECK_MARK" not in body, spec_name + " 已经有近邻检测节了"
    h = h[:j] + "\n" + NBR_SPEC.strip("\n") + h[j:]
    print("② %s：已追加近邻检测节" % spec_name)

# ③ 逐篇取近邻（原先四篇共用一份按原初问题取的）
old3 = """    // 四篇的写作输入（轻注入：带一份站内已有最近邻清单，避免撞已发命名/便于补真实引注）
    let _fpNbr=''; if(window.SDERag){ try{ _fpNbr = await window.SDERag.neighbors(r.question||''); }catch(_){} }
    const paperDefs = [
      { title:'论文① · 金点子①（'+(r.rows[0].view||'视角一')+'）', input: buildSingleIdeaInput(r.rows, 0, r.question, _fpNbr) },
      { title:'论文② · 金点子②（'+(r.rows[1].view||'视角二')+'）', input: buildSingleIdeaInput(r.rows, 1, r.question, _fpNbr) },
      { title:'论文③ · 金点子③（'+(r.rows[2].view||'视角三')+'）', input: buildSingleIdeaInput(r.rows, 2, r.question, _fpNbr) },
      { title:'论文④ · 新典范（三金点子涌现）', input: buildParadigmInput1w(r.rows, r.question, em, _fpNbr) },
    ];"""
new3 = """    // 四篇的近邻清单**逐篇取**。原先四篇共用一份、按\"原初问题\"取——那是话题的近邻，
    // 不是这篇论文里那个命名的近邻。要检测的是命名会不会撞车，所以每篇拿自己的核心判断去问。
    const _nbrFor = async (seed)=>{
      if(!window.SDERag) return '';
      try{ return await window.SDERag.neighbors(((r.question||'')+' '+String(seed||'').slice(0,400)).trim(), { k:8, author:(r.author||'') }); }
      catch(_){ return ''; }
    };
    const [_nb0,_nb1,_nb2,_nb3] = await Promise.all([
      _nbrFor(r.rows[0] && r.rows[0].sde), _nbrFor(r.rows[1] && r.rows[1].sde),
      _nbrFor(r.rows[2] && r.rows[2].sde), _nbrFor(em)
    ]);
    const paperDefs = [
      { title:'论文① · 金点子①（'+(r.rows[0].view||'视角一')+'）', input: buildSingleIdeaInput(r.rows, 0, r.question, _nb0) },
      { title:'论文② · 金点子②（'+(r.rows[1].view||'视角二')+'）', input: buildSingleIdeaInput(r.rows, 1, r.question, _nb1) },
      { title:'论文③ · 金点子③（'+(r.rows[2].view||'视角三')+'）', input: buildSingleIdeaInput(r.rows, 2, r.question, _nb2) },
      { title:'论文④ · 新典范（三金点子涌现）', input: buildParadigmInput1w(r.rows, r.question, em, _nb3) },
    ];"""
assert old3 in h
h = h.replace(old3, new3, 1)
print("③ 四篇的近邻清单改为逐篇取（各拿自己的核心判断去问）")

# ④ 近邻闸：初稿之后
old4 = """  stopTicker();
  let paperText = draft.text || '';"""
new4 = """  stopTicker();
  let paperText = draft.text || '';
  // ── 近邻闸 ──
  // 全天审稿的账：扣分几乎从不在论证质量，全在\"最近的那个对手没上桌\"。所以这一节不能靠提醒，要检测。
  // 缺了就**只补写这一节**再拼回去——不整篇重写：满功率配大任务会跑过平台时长上限、
  // 落得\"只有思考、正文 0 字\"（站上踩过两次）。补写是小任务、预算有界，安全。
  try{
    if(paperText && !nbrSectionOK(paperText)){
      setStat('⚖ 近邻检测未达标，正在补写这一节…');
      const fixSink = document.createElement('div');
      const fixed = await streamChat(cfg.writeKey, cfg.writeSel, paper1wPrompt(),
        NBR_FIX_INPUT(paperText, cfg.writeInput), fixSink, dummy, dummy, 4000);
      const add = (fixed && fixed.text || '').trim();
      if(add && /近邻/.test(add)) paperText = paperText.replace(/\\s*$/, '') + '\\n\\n' + add + '\\n';
    }
  }catch(_){ /* 补不上就照原样往下走：近邻检测是加固，不该成为整篇失败的理由 */ }"""
assert old4 in h
h = h.replace(old4, new4, 1)

# 闸门的两个纯函数放在 runOnePaper 之前
old5 = "async function runOnePaper(cfg){"
new5 = r"""// nbrSectionOK：初稿里那节近邻检测算不算写到位。判据故意保守——
//   只在\"明显没写\"时才触发补写，避免把已经写好的论文反复加尾巴。
//   ① 得有那一节（标题里带\"近邻\"）；② 该节里至少点到 3 个可指认的对手
//   （以\"作者+年份\"或\"《作品》\"或\"某某的某概念\"计）；③ 得出现判决性对照预测的字样。
function nbrSectionOK(text){
  const t = String(text||'');
  const m = t.match(/(近邻检测|最近邻[^\n]{0,12}(切割|检测|对质)|近邻切割)[\s\S]{0,6000}/);
  if(!m) return false;
  const seg = m[0];
  const named = (seg.match(/[（(]\s*[^）)]{0,30}(1[6-9]|20)\d{2}[^）)]{0,12}[）)]/g)||[]).length
              + (seg.match(/《[^》]{2,40}》/g)||[]).length;
  const hasPred = /(若|如果)[^\n]{0,80}(则本文|本文即错|本文错|本文不成立|说明本文)/.test(seg)
              || /对照预测|判决性/.test(seg);
  return named >= 3 && hasPred;
}
function NBR_FIX_INPUT(paperText, writeInput){
  return '你刚写完下面这篇论文，但其中的【近邻检测】一节缺失或不合格。\n'
    + '现在只补写这一节，不要重写论文、不要复述已有内容、不要写任何交代过程的话。\n\n'
    + '这一节必须做到：\n'
    + '· 站内近邻（若下方输入里给了清单）逐条交代：它说到哪一步、你的分离线在哪；划不出就写明重复。\n'
    + '· 库外近邻至少三个，每个给全四件：出处（作者+年份+作品，真实可查，记不准年份就不写年份）／\n'
    + '  它已经说到哪一步／分离线（可操作的判别）／一个判决性对照预测（若观察到 X 则本文错、该近邻足够；若 Y 则本文成立）。\n'
    + '· 这三个里至少一个来自问题所在领域**之外**的学科。\n\n'
    + '直接以一个小节标题开始输出（例如"近邻检测：为什么这个命名不能被现成概念替换"），一千五百字以内。\n\n'
    + '──── 这篇论文的写作输入（含站内近邻清单，若有）────\n' + String(writeInput||'').slice(0,4000)
    + '\n\n──── 已写成的论文正文 ────\n' + String(paperText||'').slice(0,12000);
}
async function runOnePaper(cfg){"""
assert old5 in h
h = h.replace(old5, new5, 1)
print("④ 初稿后加近邻闸（不合格则单独补写这一节）")

if h == before:
    print("页面没有任何改动"); sys.exit(1)
io.open(P2, "w", encoding="utf-8").write(h)
print("done")
