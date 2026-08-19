#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给碰撞机补两件互相咬合的事（改 tools/forge/forge.template.html）：

① **模式 D · 站外三领域（自动检索）** —— 兑现四种选源模式里唯一还缺的那一种
   「从网外选三个领域」。此前只能靠 F 模式手工粘。worker 上 /api/wds/websearch
   现成（智谱 search_std；用户自己的 GLM Key 或站点管理端 Key 兜底），直接接。

② **成品体例开关（散文体 / 论文体）** —— 这是①逼出来的：站外碰撞按栏目规矩
   进「学科通融」，而那一栏**必须是标准学术创新论文格式**（摘要·关键词·编号章节·
   文献综述·理论框架·分析·结论·参考文献），且三家出处要全给可点开核对的链接；
   站内碰撞进「每日必读」，那一栏是普通人读得懂的散文体、且不列来源。
   原先这一页只会写散文体，F 模式产出的东西体例上进不了学科通融。

   随之把去痕迹词表拆出第四层 `TRACE_PAPER`：论文体里「三家」「文献综述」是正经
   学术动作（已发的之八、之九都有「三家为何各自到不了」这一节），不是车间痕迹；
   而碰撞/对撞/矛盾轴/五重检验/近邻划界这些仍然恒查。手法与上次「哲学文章放行
   哲学词」同一路：**分层，不是一刀切**。

用法：python3 tools/patch_forge_mode_d.py && python3 tools/build_forge_page.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "tools", "forge", "forge.template.html")


def sub1(h, old, new, name):
    assert old in h, "锚不到：" + name
    assert h.count(old) == 1, "锚不唯一（%d）：%s" % (h.count(old), name)
    return h.replace(old, new, 1)


def main():
    h = open(TPL, encoding="utf-8").read()

    # ══════════ 一、UI ══════════
    h = sub1(h,
             """      <div class="mode" data-mode="F"><b>F · 自由投喂</b><span>你自己粘三篇进来（站外理论也走这里）</span></div>""",
             """      <div class="mode" data-mode="D"><b>D · 站外三领域</b><span>给一个议题——<b>三个领域的对立理论由基底联网去找</b>（撞站外理论，成品走学科通融）</span></div>
      <div class="mode" data-mode="F"><b>F · 自由投喂</b><span>你自己粘三篇进来（手上已有站外理论时用这个，材料比检索到的厚）</span></div>""",
             "模式 D 卡片")

    h = sub1(h,
             """    <div id="mF" class="srcbox hidden">""",
             """    <div id="mD" class="srcbox hidden">
      <label class="lbl">议题（一句话，越具体越好）</label>
      <input type="text" id="dTopic" placeholder="例：一个东西被度量之后会怎样／人能不能靠听别人说来获得道德知识">
      <div class="small" style="margin-top:8px">基底先把这个议题拆成三个**不同领域**的检索词，各搜一轮，再从搜到的东西里挑三家<b>斜着对立</b>的理论。</div>
      <label class="small" style="display:flex;gap:6px;align-items:center;margin:10px 0">
        <input type="checkbox" id="dSiteKey" style="width:auto" checked> 用本站的检索通道（不勾则用你自己的智谱 Key 检索——填在下面）
      </label>
      <input type="password" id="dSkey" placeholder="智谱 API Key（仅用于联网检索，只存在你自己的浏览器里）" style="display:none">
      <div class="small" style="margin-top:8px;color:var(--muted)">⚠ 这一路的源在站外：材料只有摘要级，抽脊会比站内薄；发表前<b>务必自己点开每个链接核对</b>。手上已有全文就改用 F 模式。</div>
    </div>

    <div id="mF" class="srcbox hidden">""",
             "模式 D 输入区")

    # 体例开关：放在「② 选三个源」的模式卡下方
    h = sub1(h,
             """    <div class="row" style="margin-top:14px">
      <button class="btn" id="goBtn">""",
             """    <div class="row" style="margin-top:14px;align-items:center">
      <div style="min-width:280px">
        <label class="lbl">成品体例</label>
        <select id="genreSel">
          <option value="essay">每日必读体 · 散文（普通人读得懂，不列来源）</option>
          <option value="paper">学科通融体 · 学术论文（摘要·关键词·编号章节·文献综述·参考文献）</option>
        </select>
      </div>
      <span class="small" id="genreNote" style="flex:1;min-width:240px;color:var(--muted)"></span>
    </div>

    <div class="row" style="margin-top:14px">
      <button class="btn" id="goBtn">""",
             "体例开关 UI")

    # ══════════ 二、体例：一个函数说了算 ══════════
    h = sub1(h,
             """function isPhilPiece(){""",
             """/* 成品体例：essay＝每日必读体（散文、不列来源）｜paper＝学科通融体（学术论文、出处全给）。
   模式变了给一个默认值，但用户改过之后就以用户为准——他比程序知道这一篇要发哪儿。 */
function genre(){ const s=$('genreSel'); return (s && s.value==='paper') ? 'paper' : 'essay'; }
function isPaper(){ return genre()==='paper'; }
function syncGenre(){
  const s=$('genreSel'); if(!s) return;
  const outside = (ST.mode==='D' || ST.mode==='F');
  if(!s.dataset.touched) s.value = outside ? 'paper' : 'essay';
  $('genreNote').innerHTML = isPaper()
    ? '论文体：摘要·关键词·编号章节·文献综述·理论框架·结论·参考文献；<b>三家出处必须给可点开核对的链接</b>。撞站外理论走这一体例。'
    : '散文体：不列来源、不用学术引注、长句 ≤90 字，普通人读得懂。撞站内篇目走这一体例。';
}

function isPhilPiece(){""",
             "genre 函数")

    h = sub1(h,
             """$('modes').addEventListener('click', e=>{
  const m = e.target.closest('.mode'); if(!m) return;
  ST.mode = m.getAttribute('data-mode');
  $('modes').querySelectorAll('.mode').forEach(x=>x.classList.toggle('on', x===m));
  renderMode();
});""",
             """$('modes').addEventListener('click', e=>{
  const m = e.target.closest('.mode'); if(!m) return;
  ST.mode = m.getAttribute('data-mode');
  $('modes').querySelectorAll('.mode').forEach(x=>x.classList.toggle('on', x===m));
  renderMode();
});
$('genreSel').addEventListener('change', e=>{ e.target.dataset.touched='1'; syncGenre(); });
$('dSiteKey').addEventListener('change', e=>{
  $('dSkey').style.display = e.target.checked ? 'none' : '';
});""",
             "体例与检索 Key 的事件")

    h = sub1(h,
             """function renderMode(){
  ['A','B','C','F'].forEach(m=> $('m'+m).classList.toggle('hidden', m!==ST.mode));""",
             """function renderMode(){
  ['A','B','C','D','F'].forEach(m=> $('m'+m).classList.toggle('hidden', m!==ST.mode));
  syncGenre();""",
             "renderMode 认 D")

    h = sub1(h,
             """  else if(ST.mode==='C') n = [0,1,2].filter(i=>$('cSel'+i) && $('cSel'+i).value).length;
  else n = [1,2,3].filter(i=>($('f'+i).value||'').trim().length>200).length;""",
             """  else if(ST.mode==='C') n = [0,1,2].filter(i=>$('cSel'+i) && $('cSel'+i).value).length;
  else if(ST.mode==='D'){
    const t=($('dTopic').value||'').trim();
    $('srcState').textContent = t ? '三家理论由基底联网去找（议题：'+t.slice(0,18)+'）' : '先给一个议题';
    return t.length>=4 ? 3 : 0;
  }
  else n = [1,2,3].filter(i=>($('f'+i).value||'').trim().length>200).length;""",
             "updateSrcState 认 D")

    h = sub1(h,
             """  } else if(ST.mode==='C'){""",
             """  } else if(ST.mode==='D'){
    return [];                                    // 三家由「选篇」那一格联网去找
  } else if(ST.mode==='C'){""",
             "collectSources 认 D")

    # ══════════ 三、去痕迹词表第四层 ══════════
    h = sub1(h,
             """function traceHits(text){ return hitList(TRACE, text); }""",
             """/* 论文体里放行的那几个 —— 「三家」「文献综述」在学术论文里是正经动作
   （已发的之八、之九都有「三家为何各自到不了」这一节），不是车间痕迹。
   碰撞/对撞/撞出/矛盾轴/五重检验/三视角/近邻划界/本文的方法 仍然恒查。 */
const TRACE_PAPER_OK = ['三个源','三篇来源','三篇文章','本文综合','这三篇'];
function traceHits(text){
  const words = isPaper() ? TRACE.filter(w=>TRACE_PAPER_OK.indexOf(w)<0) : TRACE;
  return hitList(words, text);
}""",
             "TRACE 第四层")

    # ══════════ 四、成文：体例分叉 ══════════
    h = sub1(h,
             """function writerSystem(){
  const phil = isPhilPiece();
  return [
    '你在为一个面向普通读者的专栏写文章。',""",
             """function writerSystem(){
  const phil = isPhilPiece();
  if(isPaper()) return paperWriterSystem(phil);
  return [
    '你在为一个面向普通读者的专栏写文章。',""",
             "writerSystem 分叉")

    h = sub1(h,
             """/* ============ 抽脊产物的结构化读出：主题观点 ＋ 三支撑 ＋ 冲突校验 ============ */""",
             """/* 论文体（学科通融）的系统提示。与散文体的差别不只是文风：
   那一栏的规矩是**三家出处全部给出可直接点开核对的原始链接**——撞的是别人的理论，
   把出处交清楚是最低限度的规矩。所以这里不但不禁"三家"，还要求把它们各自说到哪一步
   写成正式的文献综述。仍然禁的是学派专名与工序痕迹（碰撞/矛盾轴/五重检验…）。 */
function paperWriterSystem(phil){
  return [
    '你在写一篇跨学科的学术创新论文，投给一个只发原创理论的栏目。',
    sdeSystem(),
    '',
    '【本次输出的硬规矩，违反即作废重写】',
    (phil
      ? '① 本体论、发生学、涌现、显露、纠缠这类概念是正经学术词汇，可以正常使用；但**不许出现学派专名**——SDE、差异序列、特征纠缠、三大方程、六路径、介生态、去母体化、改姓、龙爪手、金点子、德麦、意义三律；'
      : '① 不许出现学派专名，也不要通篇套用某一家的术语体系：SDE、显露、差异序列、特征纠缠、三大方程、六路径、介生态、显影、回写、底盘 一律不用——要用这门学科自己的话把事情说清；'),
    '①之二 **不许留下这篇文章是怎么做出来的痕迹**：不许出现碰撞、对撞、撞出、矛盾轴、候选、二阶涌现、三视角、五重检验、近邻划界这类工艺词。',
    '　　但**三家理论要正面写出来**——那是文献综述该做的事，不是车间痕迹：各家说到哪一步、彼此在哪一点上不能同时为真，都要交代清楚。',
    '② 体例是标准的学术创新论文，按这个顺序：摘 要 · 关键词 · 一、导论 · 二、文献综述（2.1／2.2／2.3 各一家）· 三、冲突定位 · 四、理论框架（命名与定义）· 五、逐领域兑现 · 六、判据与可证伪条件 · 七、三家各自为何到不了这一条 · 八、推论与适用边界 · 结论 · 注释 · 参考文献。',
    '③ **三家的出处必须可核对**：正文首次提到时给出作者与年份，参考文献里给出完整条目**并附原始链接**。链接只许用材料里出现过的，一个字都不许编。',
    '④ 宁可少写一句，也不许编造文献、数据、页码。材料里没有的，就说"据本文所据材料尚不能确定"。',
    '⑤ 论点要硬，语气要平；术语第一次出现就给定义；不用排比煽情、不写"我们必须"、不写"综上所述"。',
    '⑥ 结论里必须有适用边界（这条判断在哪种情形下不适用），以及一条写死日期的可证伪赌注。'
  ].join('\\n');
}

/* ============ 抽脊产物的结构化读出：主题观点 ＋ 三支撑 ＋ 冲突校验 ============ */""",
             "paperWriterSystem")

    # 目录与成文的调令按体例分叉
    h = sub1(h,
             """  const outlineP = [
    '按下面的材料，列一份文章目录：15–22 章，每章一行，形如「一、章名 —— 这一章要落哪一件事（≤20字）」。',
    '结构要求：前两章把现象摆出来（用具体场景，不许先给结论）；中段给机制与判据；',
    '必须各留一章给：与最近的既有说法划清界线／不适用的边界／证伪条件／自反（本文自己是不是它所描述的东西的标本）。',
    '**不许出现\"三篇来源\"\"方法说明\"\"研究方法\"\"如何得出本文判断\"这类章目**——成品里不留做法的痕迹。',
    '末章给一条写死日期的赌注。只输出目录，不写正文。',
    '', head
  ].join('\\n');""",
             """  const outlineP = (isPaper() ? [
    '按下面的材料，列一份学术论文的节次目录，形如「二、文献综述 —— 这一节要落哪一件事（≤20字）」。',
    '照这个骨架来（可细分到 2.1／2.2／2.3，共 14–20 个条目）：',
    '摘 要 · 关键词 · 一、导论（三个不该同时为真的命题）· 二、文献综述（每家一节）· 三、冲突定位 ·',
    '四、理论框架（命名并定义这条判断）· 五、逐领域兑现 · 六、判据与可证伪条件 ·',
    '七、三家各自为何到不了这一条 · 八、推论与适用边界 · 结论 · 注释 · 参考文献。',
    '**不许出现\"研究方法\"\"如何得出本文判断\"这类节次**——工序不进成品；文献综述是正经章节，照写。',
    '只输出目录，不写正文。',
    '', head
  ] : [
    '按下面的材料，列一份文章目录：15–22 章，每章一行，形如「一、章名 —— 这一章要落哪一件事（≤20字）」。',
    '结构要求：前两章把现象摆出来（用具体场景，不许先给结论）；中段给机制与判据；',
    '必须各留一章给：与最近的既有说法划清界线／不适用的边界／证伪条件／自反（本文自己是不是它所描述的东西的标本）。',
    '**不许出现\"三篇来源\"\"方法说明\"\"研究方法\"\"如何得出本文判断\"这类章目**——成品里不留做法的痕迹。',
    '末章给一条写死日期的赌注。只输出目录，不写正文。',
    '', head
  ]).join('\\n');""",
             "目录分叉")

    h = sub1(h,
             """  const cp = [
    '照下面的目录，把整篇文章**一次写完**，从第一章到最后一章，一气呵成。',
    '· 每章 1000–1400 字，全篇约两万字；直接写正文，章名可作小标题，不要复述目录、不要写\"接下来\"\"下一章\"。',""",
             """  const cp = [
    '照下面的目录，把整篇文章**一次写完**，从第一章到最后一章，一气呵成。',
    isPaper()
      ? '· 每节 1000–1500 字，全篇约两万字；开头是「摘 要」与「关键词」，结尾有完整的参考文献（含可点开的原始链接）。'
      : '· 每章 1000–1400 字，全篇约两万字；直接写正文，章名可作小标题，不要复述目录、不要写\"接下来\"\"下一章\"。',""",
             "成文分叉")

    # 成文素材头：论文体要把三家出处交给写手（散文体故意不给）
    h = sub1(h,
             """    '', '【可用的素材：底下这些判断可以用，但**不许在正文里交代它们的出处**，也不许说它们来自几篇文章】',
    (ST.out.spine||'').slice(0,4000)
  ].join('\\n');""",
             """    isPaper()
      ? '\\n【三家的出处（文献综述与参考文献要用它，链接只许照抄、不许编）】\\n' + srcCite()
      : '',
    '', (isPaper()
      ? '【可用的素材：底下这些判断可以用；出处按上面那份清单如实标注】'
      : '【可用的素材：底下这些判断可以用，但**不许在正文里交代它们的出处**，也不许说它们来自几篇文章】'),
    (ST.out.spine||'').slice(0,4000)
  ].join('\\n');""",
             "成文素材头分叉")

    # srcCite：给论文体用的出处清单
    h = sub1(h,
             """/* 站内正文抓取：同源 fetch → 去掉脚本/导航/尾栏 → 纯文本 */""",
             """/* 论文体要用的出处清单。绝不替基底补链接：手上没有就写"（无链接，须自行补）"，
   宁可让它写"尚不能确定"，也不能给它一个看起来像真的假出处。 */
function srcCite(){
  return ST.sources.map((s,i)=>{
    const bits = [];
    if(s.author) bits.push(s.author);
    if(s.kind) bits.push(s.kind);
    return '['+(i+1)+'] 《'+s.title+'》'+(bits.length?('（'+bits.join('·')+'）'):'')
         + '　' + (s.url ? s.url : '（无链接，须自行补）');
  }).join('\\n');
}

/* 站内正文抓取：同源 fetch → 去掉脚本/导航/尾栏 → 纯文本 */""",
             "srcCite")

    # ══════════ 五、模式 D 的选篇：联网检索 ══════════
    h = sub1(h,
             """async function doSelect(){""",
             """/* ============ 模式 D：站外三领域，联网检索 ============
   两趟基底 + 三趟检索：拆检索词 → 各搜一轮 → 从搜到的东西里挑三家斜对立的理论并写成三个源。
   检索走 /api/wds/websearch（智谱 search_std）。它的口径：skey 传了就用用户自己的，
   没传就用站点管理端的 Key；两个都没有时返回 need_search_key —— 那时**如实说，指路 F 模式**，
   不假装搜过。 */
async function webSearch(q, skey){
  try{
    const r = await fetch('/api/wds/websearch', { method:'POST', headers:{'content-type':'application/json'},
      body: JSON.stringify({ q:String(q||'').slice(0,70), skey:skey||'', n:8 }) });
    if(!r.ok) return { ok:false, reason:'http_'+r.status, items:[] };
    return await r.json();
  }catch(e){ return { ok:false, reason:'net', items:[] }; }
}
function webBlockOf(tag, items){
  let s = '', n = 0;
  (items||[]).forEach(it=>{
    if(s.length > 4200) return;
    s += '['+tag+(++n)+'] '+(it.t||'') + (it.d?('（'+it.d+'）'):'') + (it.m?(' · '+it.m):'') + '\\n'
       + (it.s||'') + '\\n' + (it.u||'') + '\\n\\n';
  });
  return s;
}
async function doSelectWeb(){
  const id='select', p=panels[id];
  openStage(id);
  const topic = ($('dTopic').value||'').trim();
  if(topic.length < 4) throw new Error('模式 D 要先给一个议题（至少四个字）。');
  const skey = $('dSiteKey').checked ? '' : ($('dSkey').value||'').trim();

  // 一、拆成三个不同领域的检索词
  setStat(id, '<span class="spinner"></span> 拆检索词', 'run');
  const qp = [
    '议题：'+topic,
    '',
    '把它拆成**三个检索词**，交给搜索引擎去找三家**不同学科**的现行理论。要求：',
    '· 三个词必须落在三个不同的学科/领域上（例如认知心理学 × 制度经济学 × 现象学），不许是同一领域的三种问法；',
    '· 每个词要能搜到**有名有姓的理论或有争论的文献**，不是科普介绍——加上学科名、理论名、"理论""争论""critique"这类词；',
    '· 每个词 ≤ 12 个字（搜索引擎超长了召回反而差）。',
    '',
    sdeOppositeBlock(),
    '',
    '输出正好三行，每行形如：',
    '1｜学科名｜检索词',
    '2｜学科名｜检索词',
    '3｜学科名｜检索词',
    '不要写别的。'
  ].join('\\n');
  const qr = await askFast(sdeSystem(), qp, p.out, p.stat, p.meta, 1200, '拆检索词');
  const rows = (qr.text||'').split('\\n').map(x=>x.trim())
    .map(x=>x.match(/^[1-3]\\s*[｜|]\\s*([^｜|]{2,16})\\s*[｜|]\\s*(.+)$/))
    .filter(Boolean).map(m=>({ disc:m[1].trim(), q:m[2].trim().replace(/[。，、]$/,'') }));
  if(rows.length < 3) throw new Error('没能从基底那里读出三个检索词（它给的是：'+(qr.text||'').slice(0,80)+'）。重跑本格，或改用 F 模式自己粘三篇。');

  // 二、各搜一轮
  setStat(id, '<span class="spinner"></span> 联网检索三个领域', 'run');
  selLog('检索词：' + rows.map(r=>r.disc+'「'+r.q+'」').join('　'));
  const res = await Promise.all(rows.slice(0,3).map(r=>webSearch(r.q, skey)));
  const bad = res.find(x=>!x || !x.ok);
  if(bad && /need_search_key|bad_search_key/.test(bad.reason||'')){
    throw new Error('联网检索这一路暂时用不了（'+bad.reason+'）：本站的检索通道没配好、或你填的智谱 Key 不能用。'
                  + '把「用本站的检索通道」的勾去掉、填一把可用的智谱 Key，或改用 F 模式自己粘三篇站外理论。');
  }
  const hit = res.reduce((n,x)=>n+((x&&x.items)?x.items.length:0), 0);
  if(hit < 3) throw new Error('三轮检索一共只搜到 '+hit+' 条，撑不起三个源。换个更具体的议题重跑本格，或改用 F 模式。');
  const blocks = res.map((x,i)=>'【'+rows[i].disc+'｜检索词：'+rows[i].q+'】\\n'+webBlockOf('W'+(i+1)+'-', (x&&x.items)||[])).join('\\n');
  selLog('搜到 '+hit+' 条，交给基底挑三家。');

  // 三、挑三家斜对立的，写成三个源
  setStat(id, '<span class="spinner"></span> 从检索结果里挑三家斜对立的理论', 'run');
  const pp = [
    '下面是三轮联网检索的结果。请从里面挑出**三家现行理论**，让它们两两斜着对立。',
    '',
    sdeOppositeBlock(),
    '',
    '**铁律：一个字都不许编。** 作者、年份、书名/篇名、结论、链接，只许用检索结果里真出现过的；',
    '拿不准的就不要写进去。宁可只挑到两家、明说第三家没搜到，也不许造一个像真的出处。',
    '',
    '每一家写成一个源，形状必须照这个来（三段，段间空一行）：',
    '===源N',
    '标题：这一家的理论名（≤30字）',
    '学科：一个学科名',
    '出处：作者 年份 · 篇名或书名',
    '链接：检索结果里那条的网址（照抄，不许改）',
    '论点：这一家在本议题上的核心主张，一句话（≤60字），要是个能被反驳的判断',
    '正文：把这一家的论证展开 600–900 字——它凭什么这么说、它的关键条件是什么、它最强的证据是什么、它在哪儿最脆。',
    '　　　只许用检索材料里有的东西，加上这门学科的公共常识；不许添具体数据与页码。',
    '===',
    '',
    '最后另起一行写：对立点：一句话说清这三家为什么不能同时为真（≤80字）。',
    '',
    blocks
  ].join('\\n');
  const pr = await askStream(sdeSystem(), pp, p.out, p.stat, p.meta, TOK_HARD, '挑三家');
  const txt = pr.text||'';

  const got = [];
  txt.split(/^===\\s*源\\s*[0-9一二三]/m).slice(1).forEach(seg=>{
    const g = k=>{ const m = seg.match(new RegExp('^\\\\s*'+k+'[：:]\\\\s*(.+)$','m')); return m ? m[1].trim() : ''; };
    const body = (seg.match(/^\\s*正文[：:]\\s*([\\s\\S]*?)(?:\\n\\s*===|$)/m)||[])[1] || '';
    const title = g('标题');
    if(!title) return;
    got.push({ title: title.slice(0,60), url: g('链接'), author: g('出处'), kind: g('学科'),
               text: ('【'+g('学科')+'｜'+g('出处')+'】\\n' + g('论点') + '\\n' + body).slice(0, MAX_SRC),
               outside: true });
  });
  if(got.length < 3) throw new Error('只从基底那里读出 '+got.length+' 个成形的源（要三个）。重跑本格，或改用 F 模式自己粘三篇。');
  ST.sources = got.slice(0,3);
  const noLink = ST.sources.filter(s=>!/^https?:\\/\\//.test(s.url||''));
  $('srcState').textContent = '三家已就位：' + ST.sources.map(s=>s.title.slice(0,12)).join(' × ');
  selLog('<b>三家：</b>' + ST.sources.map(s=>(s.kind?('['+s.kind+']'):'')+s.title).join('　×　'));
  note('模式 D：三家理论来自站外检索，发表走「学科通融」（论文体、出处须逐条核对）。');
  showErr('三家理论是联网搜来的：' + (noLink.length
      ? ('其中 '+noLink.length+' 家没拿到可点开的链接——')
      : '') + '发表前请自己点开每个链接核对一遍。这一路的材料只有摘要级，抽脊会比站内薄；'
      + '手上已有全文就改用 F 模式。成品体例已切到「学科通融体」。');
  setStat(id, '✓ 三家已就位（站外）', 'done');
  ST.out.select = txt;
  return txt;
}

async function doSelect(){""",
             "doSelectWeb")

    h = sub1(h,
             """  if(s.id==='select'){
    if(ST.mode!=='A' || ST.manual){ setStat('select', '跳过（源已指定）'); ST.out.select=''; return ''; }
    return await doSelect();
  }""",
             """  if(s.id==='select'){
    if(ST.mode==='D') return await doSelectWeb();
    if(ST.mode!=='A' || ST.manual){ setStat('select', '跳过（源已指定）'); ST.out.select=''; return ''; }
    return await doSelect();
  }""",
             "runStage 认 D")

    # 交付横幅：把体例与站外来源报出来
    h = sub1(h,
             """    ST.mode==='A' && !ST.manual ? ('三个种子由基底找（试了 '+ST.tried.length+' 组，定标烈度 '+ST.seedScore+'/10）') : '三篇由你指定',""",
             """    isPaper() ? '体例：学科通融体（论文）' : '体例：每日必读体（散文）',
    ST.mode==='D' ? '三家由基底联网找（站外，链接须自行核对）'
      : (ST.mode==='A' && !ST.manual ? ('三个种子由基底找（试了 '+ST.tried.length+' 组，定标烈度 '+ST.seedScore+'/10）') : '三篇由你指定'),""",
             "横幅报体例")

    # 首屏把体例提示刷一次（renderMode 在 loadData 后才跑，这里保底）
    h = sub1(h,
             """function isGid(d){ return typeof d==='string'; }""",
             """function isGid(d){ return typeof d==='string'; }
try{ syncGenre(); }catch(_){ }""",
             "首屏刷体例提示")

    open(TPL, "w", encoding="utf-8").write(h)
    print("patched:", os.path.relpath(TPL, ROOT), len(h), "字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
