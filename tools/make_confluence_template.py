#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性派生：从 tools/forge/forge.template.html 派生出
tools/confluence/confluence.template.html（「SDE 学科通融」智能体的骨架）。

两台机器的差别只有五处，别的全部沿用（引擎、面板、术语闸、近邻三关、docx 导出）：
  ① 入口从「选三个源」换成「一个问题 ＋ 三个学科领域」；
  ② 前加一道工序「题型」（What／How／Why）——问题决定答案的形状，配错不报错只会答非所问；
  ③ 定源改成两路取材：站内库（近邻名单＋语料，站内源可抓全文）＋ 联网检索；
  ④ 成文之后加一道「打磨」：按封顶清单逐条自查，再整篇重写一遍；
  ⑤ 成品体例锁死为论文体（学科通融栏目的规矩）。

**这是一次性脚本**：派生出来的模板此后直接维护，不要再跑本脚本覆盖它
（跑了会把后来的改动全冲掉）。上游 forge 模板若有值得同步的改动，手工挪。

用法：python3 tools/make_confluence_template.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "forge", "forge.template.html")
OUT = os.path.join(ROOT, "tools", "confluence", "confluence.template.html")


def sub1(h, old, new, name):
    assert h.count(old) == 1, "锚点不唯一或找不到：%s（命中 %d 次）" % (name, h.count(old))
    return h.replace(old, new, 1)


# ============================ 新的入口 UI ============================
NEW_UI = '''    <h2>② 你要解决的问题，和撞它的三个学科</h2>
    <label class="lbl">问题 <span class="req">*</span></label>
    <textarea id="cQuestion" rows="3" placeholder="写清你要解决的那个问题。例：为什么组织越是想把经验留下来，经验反而流失得越快？"></textarea>
    <div class="small" style="margin:8px 0;color:var(--muted)">问题决定这篇文章要交出什么形状的答案——<b>一个东西</b>（What）／<b>一条路</b>（How）／<b>一个驱动</b>（Why）。第二格先把它判出来。判错不会报错，只会答得很通顺而答非所问。</div>
    <div class="row" style="margin-top:6px">
      <div style="flex:1;min-width:170px"><label class="lbl">学科一</label><input type="text" id="cD1" placeholder="例：制度经济学"></div>
      <div style="flex:1;min-width:170px"><label class="lbl">学科二</label><input type="text" id="cD2" placeholder="例：认知心理学"></div>
      <div style="flex:1;min-width:170px"><label class="lbl">学科三</label><input type="text" id="cD3" placeholder="例：生态学"></div>
    </div>
    <div class="small" style="margin:8px 0">三格都留空 → 由基底按这道问题自己定三门（它要挑离得远、又都真能回答这道题的）。填了几个就锁几个，其余由基底补齐。</div>
    <div class="row" style="margin-top:6px;align-items:center">
      <div style="min-width:250px">
        <label class="lbl">题型</label>
        <select id="cType">
          <option value="auto" selected>自动判别（推荐）</option>
          <option value="What">What · 要一个东西（辨别维度）</option>
          <option value="How">How · 要一条路（可干预次序）</option>
          <option value="Why">Why · 要一个驱动（谁逼动谁＋轮次）</option>
        </select>
      </div>
      <span class="small" style="flex:1;min-width:250px;color:var(--muted)">自测句：把「__ 与 __ 的矛盾驱动了 __ 改变」填实——填得进去就是 Why 题。</span>
    </div>
    <label class="small" style="display:flex;gap:6px;align-items:center;margin:12px 0 6px">
      <input type="checkbox" id="cUseKB" style="width:auto" checked> 同时从<b>站内库</b>取材（全站语料＋近邻名单；三家里允许有一家来自站内，站内源会抓全文，材料比检索到的厚）
    </label>
    <label class="small" style="display:flex;gap:6px;align-items:center;margin:6px 0">
      <input type="checkbox" id="cSiteKey" style="width:auto" checked> 用本站的检索通道<b>联网</b>找站外理论（不勾则用你自己的智谱 Key）
    </label>
    <input type="password" id="cSkey" placeholder="智谱 API Key（仅用于联网检索，只存在你自己的浏览器里）" style="display:none">
    <label class="small" style="display:flex;gap:6px;align-items:center;margin:10px 0">
      <input type="checkbox" id="philChk" style="width:auto"> 这是哲学文章（放行本体论、涌现、发生学这类词——只保留学派专名与工序痕迹的封禁）
    </label>
    <label class="small" style="display:flex;gap:6px;align-items:center;margin:6px 0">
      <input type="checkbox" id="autoRedoChk" style="width:auto"> 发现问题就自动重跑（默认关：留了痕迹或不到 150 分时，停下来让你决定）
    </label>
    <div class="small" style="margin-top:10px;color:var(--muted)">⚠ 联网搜来的材料只有摘要级，<b>发表前务必自己点开每个链接核对</b>。本站检索通道要管理端配过智谱 Key 才通；不通时上面那一格会自动露出来。</div>

'''

# ============================ 新的 JS 段 ============================
NEW_JS = r'''
/* ===================== 学科通融：问题 · 题型 · 两路取材 ===================== */
/* 这台机器与「碰撞出典范」的分别只在入口与两头：入口是**一个问题**而不是三个源，
   头一道工序是题型判别（问题决定答案的形状），末一道是打磨（按封顶清单重写一遍）。
   中段的碰撞工序原样沿用——那部分已经跑熟了。 */
function confQ(){ return ((($('cQuestion')||{}).value)||'').trim(); }
function confDiscs(){ return ['cD1','cD2','cD3'].map(id=>((($(id)||{}).value)||'').trim()).filter(Boolean); }
const TYPE_SHAPE = {
  'What':'一个东西——一条能把两样看起来一样的东西分开的辨别维度',
  'How' :'一条路——从哪儿起、经过什么、实现什么，以及在哪一步可以插手',
  'Why' :'一个驱动——什么逼动了什么，以及先后与轮次'
};
/* 三型的分别不在「产物落在哪」，在「三个对立点各自站在哪」；产物一律不落在任何一个对立点上。 */
const TYPE_POS = {
  'What':'三个对立点分处 S／D／E 三个不同位置（不是三个学科各占一个——学科可以撞车，位置不许撞车）',
  'How' :'三个对立点是三组**终点不同**的路径',
  'Why' :'三个对立点是三条不同的动力机制（谁逼动谁），且被驱动项互不相同'
};
/* 问题要穿到每一格的调令里去。挂在 sdeSystem 上而不是各格分别塞，
   是因为漏一格就会有一格在替另一道题干活，而那种漏是静默的。 */
function confTask(){
  const q = confQ();
  if(!q) return '';
  const t = ST.qtype;
  return ['【本次要解决的问题——每一格都为它服务；答得再漂亮，答不到它就是答非所问】',
    q,
    t ? ('【题型】'+t+'：这道题要的答案是 '+TYPE_SHAPE[t]+'。三个对立点的位置要求：'+TYPE_POS[t]) : ''
  ].filter(Boolean).join('\n');
}

/* 工序 −1：题型判别。判据不是疑问词，是答案的形状——同一句中文常常三种都答得上，
   只是答出来的东西不同。定不出就停，别往下选源。 */
async function doTypeGate(){
  const id='qtype', p=panels[id];
  openStage(id);
  const q = confQ();
  if(q.length < 4) throw new Error('先在上面写清你要解决的那个问题（至少四个字）——这台机器按问题定型，没有问题就无从判型。');
  const forced = ((($('cType')||{}).value)||'auto');
  if(forced !== 'auto'){
    ST.qtype = forced;
    ST.out.qtype = '题型：'+forced+'（你自己指定的）\n要交出的答案形状：'+TYPE_SHAPE[forced]+'\n三个对立点的位置要求：'+TYPE_POS[forced];
    p.out.textContent = ST.out.qtype;
    setStat(id, '✓ 题型 '+forced+' · 手动指定', 'done');
    return ST.out.qtype;
  }
  setStat(id, '<span class="spinner"></span> 判这道题要的答案是什么形状', 'run');
  const pr = [
    '这道题：'+q,
    '',
    '先判它要的答案是什么形状。只有三种：',
    '· What —— 要**一个东西**：一条能把两样看起来一样的东西分开的辨别维度；',
    '· How —— 要**一条路**：从哪儿起、经过什么、实现什么，以及在哪一步可以插手；',
    '· Why —— 要**一个驱动**：什么逼动了什么，以及先后与轮次。',
    '',
    '**判据不是疑问词，是答案的形状。** 同一句中文常常三种都答得上，只是答出来的东西不同。',
    '最有用的一条自测：把「____ 与 ____ 的矛盾驱动了 ____ 改变」这句话拿这道题去填——**填得进去就是 Why 题**，别的都不必再问。',
    '',
    '输出正好三行，不要写别的：',
    '题型：What（或 How 或 Why）',
    '理由：一句话——为什么提问的人要的是这个形状而不是另外两个（≤50字）',
    '自测：把那句话填实（填不进就写"填不进"）'
  ].join('\n');
  const r = await askFast(sdeSystem(), pr, p.out, p.stat, p.meta, 1200, '题型判别');
  const m = /题型\s*[：:]\s*(What|How|Why)/i.exec(r.text||'');
  if(!m) throw new Error('没能判出题型（基底给的是："'+(r.text||'').slice(0,60)+'"）。在上面的「题型」那一格自己选一个再跑——'
    + '自测句：把「__ 与 __ 的矛盾驱动了 __ 改变」填实，填得进去就选 Why。');
  ST.qtype = m[1].charAt(0).toUpperCase() + m[1].slice(1).toLowerCase();
  ST.out.qtype = (r.text||'') + '\n\n【位置要求】' + TYPE_POS[ST.qtype];
  setStat(id, '✓ 题型 '+ST.qtype+' · 要的是'+TYPE_SHAPE[ST.qtype].split('——')[0], 'done');
  note('题型判为 '+ST.qtype+'；三个对立点按「'+TYPE_POS[ST.qtype].split('（')[0]+'」来找。');
  return ST.out.qtype;
}

/* 定三家：站内库 ＋ 联网，两路都走。
   站内那一路给的是**名单**（有链接、可抓全文、材料厚）；联网那一路给的是**站外现行理论**。
   两路互不替代：只走联网会把自己库里已经说过的话第二次说一遍；只走站内撞不到站外的活争论。 */
async function doSelectConf(){
  const id='select', p=panels[id];
  openStage(id);
  const q = confQ();
  if(q.length < 4) throw new Error('先写清你要解决的那个问题。');
  const useKB = !!($('cUseKB') && $('cUseKB').checked);
  const useWeb = true;
  const skey = ($('cSiteKey') && $('cSiteKey').checked) ? '' : ((($('cSkey')||{}).value)||'').trim();
  const locked = confDiscs();

  /* 一、定三个学科，并给每科一条检索词（锁定的照抄，不许换） */
  setStat(id, '<span class="spinner"></span> 定三个学科与检索词', 'run');
  const dp = [
    '要解决的问题：'+q,
    ST.qtype ? ('题型：'+ST.qtype+'——要的答案是 '+TYPE_SHAPE[ST.qtype]) : '',
    locked.length ? ('**已经锁定的学科（照抄，一个字都不许改、不许换顺序）**：'+locked.join('、')) : '',
    '',
    '定出**三个学科**（连同已锁定的一共三个），要求：',
    '· 三门都真的能回答这道题，且各自有**现行的、有争论的**理论，不是科普层面的常识；',
    '· 三门离得越远越好，不许是同一门的三个分支；',
    '· 三门在这道题上的现行答案**不能同时为真**。',
    '',
    '再给每一门配一条检索词，用来去搜这门学科在这道题上的现行理论：',
    '· 要能搜到**有名有姓的理论或有争论的文献**——加上学科名、理论名、"理论""争论""critique"这类词；',
    '· 每条 ≤ 14 个字（搜索引擎超长了召回反而差）。',
    '',
    '输出正好三行，每行形如：',
    '1｜学科名｜检索词',
    '2｜学科名｜检索词',
    '3｜学科名｜检索词',
    '不要写别的。'
  ].filter(Boolean).join('\n');
  const dr = await askFast(sdeSystem(), dp, p.out, p.stat, p.meta, 900, '定学科');
  let rows = (dr.text||'').split('\n').map(x=>x.trim())
    .map(x=>x.match(/^[1-3]\s*[｜|]\s*([^｜|]{2,18})\s*[｜|]\s*(.+)$/))
    .filter(Boolean).map(m=>({ disc:m[1].trim(), q:m[2].trim().replace(/[。，、]$/,'') }));
  // 锁定的学科以人给的为准：基底改了名就改回去（它常把「法学」写成「法理学」）
  locked.forEach((d,i)=>{ if(rows[i]) rows[i].disc = d; else rows[i] = { disc:d, q:(q.slice(0,18)+' '+d+' 理论') }; });
  rows = rows.slice(0,3);
  if(rows.length < 3) throw new Error('没能定出三个学科（基底给的是："'+(dr.text||'').slice(0,70)+'"）。自己在上面把三个学科名填了再跑。');
  ST.discs = rows.map(r=>r.disc);
  ['cD1','cD2','cD3'].forEach((eid,i)=>{ if($(eid) && rows[i]) $(eid).value = rows[i].disc; });
  selLog('三个学科：<b>'+ST.discs.map(escTxt).join('　×　')+'</b>　检索词：'+rows.map(r=>escTxt(r.q)).join('　'));

  /* 二、两路取材并发 */
  setStat(id, '<span class="spinner"></span> 取材：联网检索三门 ＋ 站内库', 'run');
  const webP = Promise.all(rows.map(r=>webSearch(r.q, skey)));
  const kbP  = useKB
    ? Promise.all(rows.map(r=>nbrList([q.slice(0,300)+' '+r.disc], 6)))
    : Promise.resolve(['','','']);
  const ctxP = useKB ? kbCtx(q.slice(0,600)) : Promise.resolve('');
  let webRes = [], kbRes = ['','',''], kbCtxBlock = '';
  try{ webRes = await webP; }catch(e){ webRes = []; }
  try{ kbRes = await kbP; }catch(e){ kbRes = ['','','']; }
  try{ kbCtxBlock = await ctxP; }catch(e){ kbCtxBlock = ''; }

  const badWeb = (!webRes.length) || webRes.find(x=>!x || !x.ok);
  const webHits = webRes.reduce((n,x)=>n+((x&&x.items)?x.items.length:0), 0);
  const kbHits  = kbRes.filter(x=>x && x.length>40).length;

  if(badWeb && /need_search_key|bad_search_key/.test((badWeb.reason)||'')){
    // 死路要当场变成一步能走通的路：替他切到「用自己的 Key」并把输入框露出来。
    if($('cSiteKey') && $('cSiteKey').checked){
      $('cSiteKey').checked = false;
      $('cSkey').style.display = '';
      try{ $('cSkey').focus(); }catch(_){ }
    }
    if(!kbHits) throw new Error('联网检索不通（'+badWeb.reason+'），站内库这一路也没取到东西——两路都空，撑不起三家。'
      + (badWeb.reason==='need_search_key' ? '本站的检索通道还没配智谱 Key：' : '你填的那把智谱 Key 不能用（或没开联网搜索权限）：')
      + '已经替你切到「用自己的智谱 Key」，填进上面那一格再点「重跑本格」。');
    showErr('联网这一路现在不通（'+badWeb.reason+'）——已替你切到「用自己的智谱 Key」，填了再重跑这一格会更实在。'
      + '本次只用站内库的材料往下走：三家会偏站内，站外的活争论撞不到，发表前请自己补几条站外出处。');
  } else if(webHits < 3 && !kbHits){
    throw new Error('三轮检索一共只搜到 '+webHits+' 条、站内库也没命中，撑不起三家。把问题写得更具体些重跑本格，或自己指定三个学科。');
  }

  const matBlocks = rows.map((r,i)=>{
    const w = (webRes[i] && webRes[i].ok) ? webBlockOf('W'+(i+1)+'-', (webRes[i].items)||[]) : '（这一门没搜到站外材料）';
    const k = (kbRes[i] && kbRes[i].length>40) ? kbRes[i] : '（这一门站内库没命中）';
    return '【'+r.disc+'｜检索词：'+r.q+'】\n〔站外·联网检索〕\n'+w+'\n〔站内·本站已有的相关篇目（链接以 / 开头，可直接点开）〕\n'+k;
  }).join('\n\n');
  selLog('取材完成：站外 '+webHits+' 条，站内 '+kbHits+' 门命中。');

  /* 三、从两路材料里为每门学科定一家，要两两斜对立、且都在回答这道题 */
  setStat(id, '<span class="spinner"></span> 为三门各定一家理论（要两两斜对立）', 'run');
  const pp = [
    '下面是三门学科的取材：每门都有〔站外·联网检索〕与〔站内·本站已有篇目〕两路。',
    '请为**每一门各挑出一家**在这道题上的现行理论或明确判断，一共三家，让它们两两斜着对立。',
    '',
    '**三家必须都在回答同一道题**——就是上面那道问题。一家答的是别的问题，它就不算一家，重挑。',
    ST.qtype ? ('**位置要求（这一条比学科更要紧）**：'+TYPE_POS[ST.qtype]+'。学科可以撞车而位置不许撞车；两家站在同一个位置，撞不出东西来。') : '',
    '',
    sdeOppositeBlock(),
    '',
    '**铁律：一个字都不许编。** 作者、年份、书名/篇名、结论、链接，只许用上面材料里真出现过的；',
    '拿不准就不要写进去。宁可明说某一门没挑到，也不许造一个像真的出处。',
    '站内那一路的链接以 / 开头（例 /students/xxx/），照抄即可；站外的链接照抄 http(s) 网址。',
    '',
    '每一家写成一个源，形状必须照这个来（段间空一行）：',
    '===源N',
    '标题：这一家的理论名或判断名（≤30字）',
    '学科：这一门学科名',
    '来源：站外　或　站内',
    '出处：作者 年份 · 篇名或书名',
    '链接：材料里那一条的网址（照抄，不许改；实在没有就写"无"）',
    '论点：这一家对**本问题**给出的答案，一句话（≤60字），要是个能被反驳的判断',
    '位置：这一家的对立点站在哪（照上面的位置要求写，一句话）',
    '正文：把这一家的论证展开 600–900 字——它凭什么这么说、它的关键条件是什么、它最强的证据是什么、它在哪儿最脆。',
    '　　　只许用材料里有的东西，加上这门学科的公共常识；不许添具体数据与页码。',
    '===',
    '',
    '最后另起一行写：对立点：一句话说清这三家为什么不能同时为真（≤80字）。',
    '',
    matBlocks,
    kbCtxBlock ? ('\n【站内已有的相关判断（背景，可印证可反驳，不要当作三家之一）】\n'+kbCtxBlock.slice(0,6000)) : ''
  ].filter(Boolean).join('\n');
  const pr = await askStream(sdeSystem(), pp, p.out, p.stat, p.meta, TOK_HARD, '定三家');
  const txt = pr.text||'';

  const got = [];
  txt.split(/^===\s*源\s*[0-9一二三]/m).slice(1).forEach(seg=>{
    const g = k=>{ const m = seg.match(new RegExp('^\\s*'+k+'[：:]\\s*(.+)$','m')); return m ? m[1].trim() : ''; };
    const body = (seg.match(/^\s*正文[：:]\s*([\s\S]*?)(?:\n\s*===|$)/m)||[])[1] || '';
    const title = g('标题');
    if(!title) return;
    // 只认真链接：http(s) 或站内以 / 开头的路径。基底拿不到链接时爱填「（材料里没有）」，
    // 那不是链接——一个看起来像出处的假出处，比明说无链接坏得多。
    const raw = g('链接');
    const url = /^https?:\/\//.test(raw) ? raw
              : (/^\/[A-Za-z0-9_\-\/\.]+$/.test(raw) ? raw : '');
    const inside = /站内/.test(g('来源')) || /^\//.test(url);
    got.push({ title:title.slice(0,60), url:url, author:g('出处'), kind:g('学科'),
               inside:inside, outside:!inside, pos:g('位置'),
               text: ('【'+g('学科')+'｜'+g('出处')+'】\n' + g('论点') + (g('位置')?('\n〔位置〕'+g('位置')):'') + '\n' + body).slice(0, MAX_SRC) });
  });
  if(got.length < 3) throw new Error('只从基底那里读出 '+got.length+' 个成形的源（要三个）。点「重跑本格」再试一次，或把三个学科自己指定得更具体些。');
  ST.sources = got.slice(0,3);

  /* 四、站内那几家去抓全文——站内源的材料能比摘要厚一个量级，不抓白不抓 */
  let pulled = 0;
  for(const s of ST.sources){
    if(!/^\//.test(s.url||'')) continue;
    try{
      const full = await pullText(s.url);
      if(full && full.length > s.text.length){ s.text = ('【'+(s.kind||'')+'｜站内】\n'+full).slice(0, MAX_SRC); pulled++; }
    }catch(e){ /* 抓不到就用摘要，不让它挡住整格 */ }
  }
  if(pulled) selLog('站内 '+pulled+' 家已抓到全文（材料比摘要厚）。');

  const noLink = ST.sources.filter(s=>!s.url);
  $('srcState').textContent = '三家已就位：' + ST.sources.map(s=>s.title.slice(0,12)).join(' × ');
  selLog('<b>三家：</b>' + ST.sources.map(s=>(s.kind?('['+s.kind+']'):'')+(s.inside?'〔站内〕':'〔站外〕')+s.title).join('　×　'));
  note('三家已定：'+ST.sources.map(s=>s.kind||'?').join(' × ')+'；成品走学科通融体（论文，出处须逐条核对）。');
  if(noLink.length) showErr('三家里有 '+noLink.length+' 家没拿到可点开的链接——本栏的规矩是三家出处全部可核对，发表前请自己补上。');
  setStat(id, '✓ 三家已就位（站内 '+ST.sources.filter(s=>s.inside).length+' · 站外 '+ST.sources.filter(s=>!s.inside).length+'）', 'done');
  ST.out.select = txt;
  return txt;
}

/* 打磨：成文之后的最后一道。先按封顶清单逐条自查，再照自查整篇重写一遍。
   为什么要整篇重写而不是打补丁：这些封顶项（题型错配、现象证伪、位置撞车）都是**承重**的，
   补一段话盖不住，只会让文章多一处自相矛盾。 */
async function doPolish(){
  const id='polish', p=panels[id];
  openStage(id);
  if(!ST.article || ST.article.replace(/\s/g,'').length < 500) throw new Error('还没有正文可打磨——先把成文那一格跑出来。');

  setStat(id, '<span class="spinner"></span> 逐条自查（封顶清单）', 'run');
  const auditP = [
    '这是一篇已经写完的跨学科论文。逐条查下面十项，每一项写成一行：',
    '「N. 项名 ｜ 过 / 不过 ｜ 一句话理由 ｜ 该怎么改（不过才写）」。不许恭维，不许写"总体不错"。',
    '',
    '1. **题型对口**：这道题要的是 '+(ST.qtype ? (ST.qtype+'（'+TYPE_SHAPE[ST.qtype]+'）') : '什么形状的答案')+'。把本文的承重命题拿去填「__ 与 __ 的矛盾驱动了 __ 改变」——填得进去而本文走的不是驱动型，就是错配（答得很通顺，但答的不是这道题）。',
    '2. **位置三分**：三个对立点是不是分处三个不同位置（'+(ST.qtype?TYPE_POS[ST.qtype]:'三个不同位置')+'）？两家站在同一个位置就是撞车，学科离得再远也没用。',
    '3. **反转模板查名**：把承重命题剥掉本学科的一切名词，只留「什么对什么做了什么导致什么」。剥出来若是「X 越成功越失败」「手段吞噬目的」这类模板，模板本身早有名字（成功陷阱 Levinthal & March 1993／伊卡洛斯悖论 Miller 1990／能力刚性 Leonard-Barton 1992／内卷化 Geertz 1963／目标置换 Merton 1940、Selznick 1949）——正文有没有点名最贴的那一个？没点名＝这条不过。',
    '4. **证伪两档**：只验证"这个现象存在"是现象证伪，不算数。合格的是机制证伪两步——先写出最强竞争解释那句「其实不就是 X 吗」，再要求控制掉它之后本机制独有的变量仍成立。格式：「控制 [竞争变量] 后，若 [独有变量] 与 [结果] 无 [剂量-反应]，则本判断为伪」。',
    '5. **样本纪律**：有没有拿两个国家／地区的对比来充证据？N=2 的异质对比只能当启发式，不能当证据。',
    '6. **划界黑名单**：与既有说法的分界里，有没有靠"更强调／更深入／更系统／视角不同／层次更根本／侧重点不一样"来划？出现即视同被占位，该条不算划界。',
    '7. **新读数还是新存在物**：本文的核心判断若是「X 不是 Y 而是 Z」，Z 只是同一样东西的一个新读数（操作化），还是一类原来不存在的存在物？判据一句话——**删掉这个读数之后，那个东西是不是就不存在了？**',
    '8. **出处可核对**：三家的作者、年份、篇名、链接，有没有一处是编的？有没有把"材料里没有"写成一个像真的出处？参考文献里的链接是不是都能对上正文？',
    '9. **零术语零痕迹**：正文有没有学派专名（SDE、差异序列、特征纠缠、去母体化、龙爪手、金点子、德麦…），有没有做法的痕迹（碰撞、对撞、矛盾轴、五重检验、三视角、近邻划界、本文的方法…）。',
    '10. **收尾两件**：结论里有没有适用边界（这条判断在哪种情形下不适用），有没有一条写死日期的可证伪赌注？',
    '',
    '十行写完，最后另起一行：**最要紧的三处**：…（按承重程度排，只列三处）。',
    '',
    '【要解决的问题】', confQ(),
    '', '【三家的出处】', srcCite(),
    '', '【全文】', ST.article
  ].join('\n');
  const a = await askStream(reviewSystem(), auditP, p.out, p.stat, p.meta, TOK_HARD, '逐条自查');
  const audit = a.text||'';
  ST.out.polishAudit = audit;

  setStat(id, '<span class="spinner"></span> 照自查整篇重写一遍', 'run');
  const box = document.createElement('div'); box.className='out'; box.style.marginTop='8px';
  p.out.parentNode.insertBefore(box, p.out.nextSibling);
  const rewriteP = [
    '照下面的自查结果，把这篇文章**整篇重写一遍**——从摘要到参考文献，一次写完，别只改被点到的那几段。',
    '· 不过的每一条都要在正文里真正改掉，不是加一句话盖过去；',
    '· 已经过的地方不要动，别把好句子改软；',
    '· 篇幅不许缩水：原稿多长，重写稿就至少多长（约两万字）；',
    '· 中途不要停下来征求意见、不要写"（未完待续）"，直接把参考文献也写完；',
    '· 不许出现"修改说明""本次改了什么"这类交代——重写稿就是终稿本身。',
    '',
    '【自查结果】', audit,
    '', '【要解决的问题】', confQ(),
    ST.qtype ? ('【题型】'+ST.qtype+'——要交出的答案是 '+TYPE_SHAPE[ST.qtype]) : '',
    '', '【三家的出处（链接只许照抄，不许编）】', srcCite(),
    '', '【原稿全文】', ST.article
  ].filter(Boolean).join('\n');
  const r = await askStream(paperWriterSystem(isPhilPiece()), rewriteP, box, p.stat, p.meta, WRITE_TOK, '整篇重写');
  const txt = r.text||'';
  const wc = txt.replace(/\s/g,'').length, oldwc = ST.article.replace(/\s/g,'').length;

  // 重写稿比原稿短一大截＝多半是被基底的输出上限钳断了，不采用（宁可留原稿，也别交半篇）
  if(wc < oldwc * 0.6 || wc < 3000){
    ST.out.polish = audit + '\n\n————\n【重写稿被判为不完整（'+wc+' 字 / 原稿 '+oldwc+' 字），未采用】\n' + txt;
    note('打磨这一趟只写出 '+wc+' 字（原稿 '+oldwc+' 字），像是被截断——保留原稿，未采用这一版。');
    showErr('打磨稿只有 '+wc+' 字（原稿 '+oldwc+' 字），疑似被这个基底一次输出的上限钳断——已保留原稿。'
      + '换 DeepSeek 这类能一次长输出的基底，点这一格的「重跑本格」；自查结果照样可用，可以按它自己改。');
    setStat(id, '⚠ 重写稿疑似被截断 · 已保留原稿（自查结果可用）', 'done');
    return ST.out.polish;
  }

  ST.article = txt;
  ST.out.write = txt;
  ST.polished = true;
  const terms = termHits(ST.article), traces = traceHits(ST.article);
  const hits = terms.concat(traces);
  setStat(id, '✓ 已打磨 · '+wc+' 字'+(hits.length ? ('　⚠ 仍有残留：'+hits.join('、')) : '　术语零残留 · 无工艺痕迹'), 'done');
  if(hits.length){
    ST.termFix = hits;
    showErr('打磨后正文里仍留着：'+hits.join('、')+'。用这一格的「编辑产物」手改，或回成文那一格「重跑本格」——这一条是上站硬门槛。');
  }
  await nbrPostName();
  $('deliver').style.display='';
  ST.out.polish = '【逐条自查】\n' + audit + '\n\n【已按自查整篇重写，终稿见成文格与交付区】';
  return ST.out.polish;
}

'''


def main():
    h = open(SRC, encoding="utf-8").read()

    # ---------- 1. 头部品牌 ----------
    h = sub1(h, "<title>SDE 碰撞出典范 · 品尝系列 | SDE Universes</title>",
             "<title>SDE 学科通融 · 品尝系列 | SDE Universes</title>", "title")
    h = sub1(h,
             '<meta name="description" content="选三个源——一位学员的三篇、三位学员各一篇、站上三个学科的长文，或你自己粘进来的三篇——让它们两两对撞，撞出一句谁单看都说不出的判断，并写成一篇两万字。七大基底任选，用你自己的 API Key。">',
             '<meta name="description" content="给一个问题，再给三个学科领域——机器从站内库与联网两路找出三家在这道题上互相顶撞的理论，撞出一条三家都不会同意、而三家的证据合起来只能得出的判断，写成一篇两万字的学术创新论文。七大基底任选，用你自己的 API Key。">',
             "meta-desc")
    h = sub1(h, '<meta property="og:title" content="SDE 碰撞出典范 · 品尝系列">',
             '<meta property="og:title" content="SDE 学科通融 · 品尝系列">', "og-title")
    h = sub1(h, '<meta property="og:description" content="三篇文章，撞出谁单看都说不出的那一句，并写成一篇。">',
             '<meta property="og:description" content="一个问题 ＋ 三个学科，撞出解决这道题的那一句，并写成一篇论文。">', "og-desc")
    h = sub1(h, '<h1>SDE <span class="grad">碰撞出典范</span></h1>',
             '<h1>SDE <span class="grad">学科通融</span></h1>', "h1")
    h = sub1(h,
             '  <p class="hero-sub">选三个源，让它们两两对撞——撞出一句三个源单看都说不出的判断，再写成一篇两万字。<br>这是「每日必读」与「学科通融」两个栏目背后的那道工序。</p>',
             '  <p class="hero-sub">给一个<b>问题</b>，再给<b>三个学科</b>——机器从站内库与联网两路，找出三家在这道题上互相顶撞的理论，'
             '撞出一条三家都不会同意、而三家的证据合起来只能得出的判断，写成一篇两万字的学术论文，最后再打磨一遍。'
             '<br>这是顶栏「学科通融」栏目背后的那道工序。</p>', "hero-sub")

    # ---------- 2. 入口 UI：新块在前，旧的选源块整体收进隐藏容器 ----------
    a = h.find('    <div class="modes" id="modes">')
    assert a > 0, "找不到旧的模式块起点"
    gomark = '    <div class="row" style="margin-top:14px">\n      <button class="btn" id="goBtn">'
    b = h.find(gomark)
    assert b > a, "找不到操作行（goBtn）"
    legacy = h[a:b]

    # 两个开关搬进新块，旧块里删掉（同一个 id 不能有两份）
    phil_lbl = ('      <label class="small" style="display:flex;gap:6px;align-items:center;margin:8px 0">\n'
                '        <input type="checkbox" id="philChk" style="width:auto"> 这是哲学文章（放行本体论、涌现、发生学这类词——只在成品里保留学派专名与工序痕迹的封禁）\n'
                '      </label>\n')
    redo_lbl = ('      <label class="small" style="display:flex;gap:6px;align-items:center;margin:8px 0">\n'
                '        <input type="checkbox" id="autoRedoChk" style="width:auto"> 发现问题就自动重跑（默认关：留了痕迹或不到 150 分时，停下来让你决定要不要重写/回炉）\n'
                '      </label>\n')
    for lbl, nm in [(phil_lbl, "philChk"), (redo_lbl, "autoRedoChk")]:
        assert legacy.count(lbl) == 1, "旧块里找不到 " + nm + " 那一段"
        legacy = legacy.replace(lbl, "", 1)

    h = h[:a] + NEW_UI + '    <div style="display:none" id="legacyPick">\n' + legacy + '    </div>\n\n' + h[b:]
    h = sub1(h, "    <h2>② 选三个源</h2>\n" + NEW_UI.split("\n", 1)[0] + "\n",
             NEW_UI.split("\n", 1)[0] + "\n", "旧 h2 去重") if False else h
    # 旧的 ② 标题在 NEW_UI 之前，直接删掉
    h = sub1(h, "    <h2>② 选三个源</h2>\n    <h2>② 你要解决的问题，和撞它的三个学科</h2>",
             "    <h2>② 你要解决的问题，和撞它的三个学科</h2>", "去掉旧 h2")

    h = sub1(h, '<button class="btn" id="goBtn">一键跑 · 挑三篇 → 碰撞 → 成文 → 评审</button>',
             '<button class="btn" id="goBtn">一键跑 · 判题型 → 定三家 → 碰撞 → 成文 → 打磨</button>', "goBtn 文案")
    h = sub1(h, "    <h2>③ 撞的是这三篇（每篇：一个主题观点 ＋ 三个支撑观点）</h2>",
             "    <h2>③ 撞的是这三家（每家：一个主题观点 ＋ 三个支撑观点）</h2>", "trio 标题")

    # ---------- 3. 页脚 ----------
    h = sub1(h,
             "  这台机器把「每日必读」（站内碰撞）与「学科通融」（站外碰撞）的人工工序封装成产品。<br>",
             "  这台机器把顶栏「学科通融」栏目的人工工序封装成产品：一个问题、三个学科，站内库与联网两路取材。<br>",
             "foot")

    # ---------- 4. 工序表 ----------
    h = sub1(h,
             "  {id:'select',  n:'选篇',     hint:'随机 A → 找对立 B → 找同时顶两篇的 C，逐级放宽范围', tok:4000},",
             "  {id:'qtype',   n:'题型',     hint:'先判这道题要的答案是什么形状：一个东西(What)／一条路(How)／一个驱动(Why)', tok:1500},\n"
             "  {id:'select',  n:'定三家',   hint:'站内库＋联网两路取材，为三个学科各定一家，要两两斜对立', tok:TOK_HARD},",
             "STAGES-select")
    h = sub1(h,
             "  {id:'write',   n:'成文',     hint:'一趟写完整篇两万字（不分段）',          tok:4000},",
             "  {id:'write',   n:'成文',     hint:'一趟写完整篇两万字（不分段）',          tok:4000},\n"
             "  {id:'polish',  n:'打磨',     hint:'按封顶清单逐条自查，再照自查整篇重写一遍', tok:4000},",
             "STAGES-polish")

    # ---------- 5. 状态初值 ----------
    h = sub1(h, "const ST = { mode:'A', sources:[], out:{}, outline:'', article:'', score:null, running:false, abort:false,",
             "const ST = { mode:'X', sources:[], out:{}, outline:'', article:'', score:null, running:false, abort:false,\n"
             "             qtype:'', discs:[], polished:false,",
             "ST-init")
    h = sub1(h,
             "  ST.spineRows=[]; ST.conflict=''; ST.truncated=false;\n"
             "  ST.coined=''; ST.finalName='';",
             "  ST.spineRows=[]; ST.conflict=''; ST.truncated=false;\n"
             "  ST.qtype=''; ST.discs=[]; ST.polished=false;\n"
             "  ST.coined=''; ST.finalName='';",
             "reset")

    # ---------- 6. 体例锁死为论文体 ----------
    h = sub1(h, "  const outside = (ST.mode==='D' || ST.mode==='F');",
             "  const outside = true;   // 学科通融一律论文体（栏目规矩），不随模式变", "syncGenre")

    # ---------- 7. 源状态与取源 ----------
    h = sub1(h, "function updateSrcState(){\n  if(ST.mode==='A' && !ST.manual){",
             "function updateSrcState(){\n"
             "  if(ST.mode==='X'){\n"
             "    const q = confQ(), ds = confDiscs();\n"
             "    $('srcState').textContent = q\n"
             "      ? ('三家由基底去找（' + (ds.length ? ds.join('×') : '学科也由它定') + '）')\n"
             "      : '先写一个要解决的问题';\n"
             "    return 3;\n"
             "  }\n"
             "  if(ST.mode==='A' && !ST.manual){",
             "updateSrcState")
    h = sub1(h, "  } else if(ST.mode==='B' || ST.mode==='C' || ST.mode==='D'){",
             "  } else if(ST.mode==='B' || ST.mode==='C' || ST.mode==='D' || ST.mode==='X'){",
             "collectSources")

    # ---------- 8. 问题穿进每一格的 system ----------
    h = sub1(h, "    ST.xinde ? ('【你自己内化后写下的心得（本次作业的引擎底盘，按它办事）】\\n' + ST.xinde) : '',",
             "    confTask(),\n"
             "    ST.xinde ? ('【你自己内化后写下的心得（本次作业的引擎底盘，按它办事）】\\n' + ST.xinde) : '',",
             "sdeSystem")

    # ---------- 8之二. 评审也要拿到那道题 ----------
    # 评审读到的是成品，读不出提问的人原本要什么形状的答案；不给它，它只会评"写得好不好"，
    # 而这条产线最隐蔽的失手正是「答得很通顺而答非所问」。
    h = sub1(h, "    '你是严格的评审，只评不写。不许恭维，不许给\"很有启发\"这类空话。',",
             "    '你是严格的评审，只评不写。不许恭维，不许给\"很有启发\"这类空话。',\n"
             "    confTask(),\n"
             "    '评的第一件事是**答没答到那道题**：文不对题、或答出来的形状与题型不对口（要一个驱动却交了一个漂亮概念），"
             "先扣 I 与 F，别被行文的通顺唬住。',",
             "reviewSystem")

    # ---------- 9. 工序调度 ----------
    h = sub1(h, "  if(s.id==='warmup') return await doWarmup();\n  if(s.id==='select'){\n    if(ST.mode==='D') return await doSelectWeb();",
             "  if(s.id==='warmup') return await doWarmup();\n"
             "  if(s.id==='qtype')  return await doTypeGate();\n"
             "  if(s.id==='polish') return await doPolish();\n"
             "  if(s.id==='select'){\n"
             "    if(ST.mode==='X') return await doSelectConf();\n"
             "    if(ST.mode==='D') return await doSelectWeb();",
             "runStage")

    # ---------- 10. 新函数 ----------
    h = sub1(h, "async function doSelect(){", NEW_JS.lstrip("\n") + "async function doSelect(){", "inject-js")

    # ---------- 11. 检索 Key 那一格的显隐 ----------
    h = sub1(h, "$('dSiteKey').addEventListener('change', e=>{\n  $('dSkey').style.display = e.target.checked ? 'none' : '';\n});",
             "$('dSiteKey').addEventListener('change', e=>{\n  $('dSkey').style.display = e.target.checked ? 'none' : '';\n});\n"
             "$('cSiteKey').addEventListener('change', e=>{\n  $('cSkey').style.display = e.target.checked ? 'none' : '';\n});\n"
             "['cQuestion','cD1','cD2','cD3'].forEach(id=>{ const el=$(id); if(el) el.addEventListener('input', updateSrcState); });",
             "cSiteKey")

    # ---------- 12. 交付横幅 ----------
    h = sub1(h,
             "    ST.mode==='D' ? '三家由基底联网找（站外，链接须自行核对）'\n"
             "      : (ST.mode==='A' && !ST.manual ? ('三个种子由基底找（试了 '+ST.tried.length+' 组，定标烈度 '+ST.seedScore+'/10）') : '三篇由你指定'),",
             "    ST.mode==='X'\n"
             "      ? ('题型 '+(ST.qtype||'未判')+'　三家：'+(ST.discs||[]).join('×')\n"
             "         +'（站内 '+ST.sources.filter(s=>s.inside).length+' · 站外 '+ST.sources.filter(s=>!s.inside).length+'）'\n"
             "         +(ST.polished ? '　已打磨' : '　未打磨'))\n"
             "      : (ST.mode==='D' ? '三家由基底联网找（站外，链接须自行核对）'\n"
             "      : (ST.mode==='A' && !ST.manual ? ('三个种子由基底找（试了 '+ST.tried.length+' 组，定标烈度 '+ST.seedScore+'/10）') : '三篇由你指定')),",
             "deliver-banner")

    # ---------- 13. 一键跑的按钮文案 ----------
    h = h.replace("goBtn.textContent = '取三个源的正文……';", "goBtn.textContent = '准备中……';")
    h = h.replace("goBtn.textContent='一键跑 · 挑三篇 → 碰撞 → 成文 → 评审'; return;",
                  "goBtn.textContent='一键跑 · 判题型 → 定三家 → 碰撞 → 成文 → 打磨'; return;")
    h = h.replace("goBtn.textContent = '一键跑 · 挑三篇 → 碰撞 → 成文 → 评审';",
                  "goBtn.textContent = '一键跑 · 判题型 → 定三家 → 碰撞 → 成文 → 打磨';")

    # ---------- 14. 文件名与署名 ----------
    h = h.replace("由 SDE 碰撞出典范生成", "由 SDE 学科通融生成")
    h = h.replace("'碰撞出典范_'+title.slice(0,12)+'.docx'", "'学科通融_'+title.slice(0,12)+'.docx'")
    h = h.replace("{id:'sde-paradigm-forge'}", "{id:'sde-confluence'}")
    h = h.replace('SDEHandoff.receive("forge")', 'SDEHandoff.receive("confluence")')
    h = h.replace("'碰撞出的典范'", "'学科通融'")

    # ---------- 自检 ----------
    for needle in ["doTypeGate", "doSelectConf", "doPolish", "confTask()", "cQuestion", "cUseKB",
                   "id='qtype'", "id:'polish'", "ST.mode==='X'"]:
        assert needle in h, "派生后缺了：" + needle
    assert "id=\"philChk\"" in h and h.count('id="philChk"') == 1, "philChk 不是恰好一个"
    assert h.count('id="autoRedoChk"') == 1, "autoRedoChk 不是恰好一个"
    for tagname in ["div", "script", "style", "select", "textarea"]:
        o = len(re.findall(r"<%s[\s>]" % tagname, h))
        c = len(re.findall(r"</%s>" % tagname, h))
        assert o == c, "标签不配对：%s 开 %d 闭 %d" % (tagname, o, c)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(h)
    print("derived:", os.path.relpath(OUT, ROOT), len(h), "字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
