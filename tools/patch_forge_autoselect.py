#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「SDE 碰撞出典范」（引擎室）的 B / C / D 三个模式改成**由基底自己选源**。

起因：两次真跑（125 / 128）都死在 I=115 同一道闸门，而失分的根子在选源——
三篇同出一站、同一语汇族，混沌碰撞越撞越收敛到语料重心，而重心正是被占满的地方。
选源由用户手输，等于整条产线最关键的那个自由度被锁死在人手上；改成基底自己找，
天花板才第一次变成可以搜索的东西（可以一晚抽二十组，按分数留最好的）。

改了什么：
  · B 三人各一篇 —— 删掉 3×(学员下拉+文章下拉)，接到 A 模式已有的自动选篇机器上；
    程序随机定第一人 → 随机抽定 A → 阶梯**从"其他学员"起步**找 B、找 C。
  · C 站上三长文 —— 删掉 3×(关键词框+下拉)，种子从站上长文随机抽，阶梯从全站起步。
  · D 站外三领域 —— 议题可留空，留空就由基底自己定一个，且强制避开已经撞过的清单。
  · 两道防重心的硬约束（机械算，不问基底）：同作者剔除（仅 B）＋语汇族重叠率剔除（B/C）。
  · 随机数一律在程序里产生，不交给基底——基底的"随机"是它的偏好，会反复挑同几篇。

用法：python3 tools/patch_forge_autoselect.py && python3 tools/build_forge_page.py
      然后必跑 node tools/sim_paradigm_forge.js
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "tools", "forge", "forge.template.html")
h = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new):
    global h, n
    assert h.count(old) == 1, ("锚点不唯一或找不到 (%d)：%r" % (h.count(old), old[:90]))
    h = h.replace(old, new); n += 1



# ---------- 1. 模式卡文案：B / C 改成「由基底挑」 ----------
rep('<div class="mode" data-mode="B"><b>B · 三人各一篇</b><span>三位学员、三个领域（已发篇目里最出成绩的一类）</span></div>',
    '<div class="mode" data-mode="B"><b>B · 三人各一篇</b><span>三位学员各一篇——<b>三人三篇全由基底挑</b>（硬约束：必须三个不同作者）</span></div>')
rep('<div class="mode" data-mode="C"><b>C · 站上三长文</b><span>三个学科的站上长文</span></div>',
    '<div class="mode" data-mode="C"><b>C · 站上三长文</b><span>站上长文——<b>三篇全由基底挑</b>（硬约束：必须三个不同栏目）</span></div>')

# ---------- 2. 模式 D：议题可留空，由基底自己定 ----------
rep('<label class="lbl">议题（一句话，越具体越好）</label>\n      <input type="text" id="dTopic" placeholder="例：一个东西被度量之后会怎样／人能不能靠听别人说来获得道德知识">',
    '<label class="lbl">议题（<b>可留空</b>——留空就由基底自己定一个）</label>\n      <input type="text" id="dTopic" placeholder="留空＝基底自己定议题；也可以自己给一个，例：一个东西被度量之后会怎样">')

# ---------- 3. renderMode：B / C 不再建下拉，改成自动说明 ----------
old_b = """  if(ST.mode==='B'){
    const host=$('mB');
    if(!host.dataset.built){
      host.innerHTML = [0,1,2].map(i=>
        '<div class="srcrow"><div class="srcnum">'+(i+1)+'</div><div>'+
        '<select id="bStu'+i+'" style="margin-bottom:6px"></select>'+
        '<select id="bArt'+i+'"></select></div></div>').join('');
      host.dataset.built='1';
      [0,1,2].forEach(i=>{
        const ss=$('bStu'+i);
        ss.innerHTML = optionsFor(STUDENTS, s=>s.slug, s=>s.name);
        ss.selectedIndex = Math.min(i, STUDENTS.length-1);
        ss.addEventListener('change', ()=> fillB(i));
        fillB(i);
      });
    }
  }
  if(ST.mode==='C'){
    const host=$('mC');
    if(!host.dataset.built){
      host.innerHTML = '<div class="small" style="margin-bottom:8px">从站上长文里挑三篇——挑观点互相打架的，不是挑分数最高的。</div>' +
        [0,1,2].map(i=>'<div class="srcrow"><div class="srcnum">'+(i+1)+'</div><div>'+
        '<input type="text" id="cQ'+i+'" placeholder="打关键词筛（如：睡眠 / 创造 / 自信）" style="margin-bottom:6px">'+
        '<select id="cSel'+i+'"></select></div></div>').join('');
      host.dataset.built='1';
      [0,1,2].forEach(i=>{
        fillC(i,'');
        $('cQ'+i).addEventListener('input', e=> fillC(i, e.target.value.trim()));
      });
    }
  }"""
new_b = """  /* B / C 一律由基底挑源：手选会把整条产线最关键的那个自由度锁死在人手上，
     而两次真跑都证明天花板正落在选源上（撞出来的判断被最近邻 1:1 覆盖）。
     这里只交代规则与硬约束，不再放任何下拉。 */
  if(ST.mode==='B'){
    const host=$('mB');
    if(!host.dataset.built){
      host.innerHTML =
        '<div class="small" style="margin:2px 0"><b>三位学员各一篇，全由基底挑。</b>'+
        '程序先<b>随机</b>定一位学员、再从他的篇目里随机抽定一篇 A（固定不换）→ '+
        '在<b>其他学员</b>里找与 A 斜对立的 B → 再找同时顶住 A 和 B 的 C；'+
        '不够硬就逐级放宽（其他学员 → 全站长文 → 基底知识库）。</div>'+
        '<div class="small" style="margin:8px 0;color:var(--muted)">'+
        '⛓ 硬约束：<b>三篇必须出自三位不同作者</b>——同一作者的文章共用一套语汇，'+
        '撞得再多也只会收敛到这套语汇的重心，而重心正是被占满的地方。</div>';
      host.dataset.built='1';
    }
  }
  if(ST.mode==='C'){
    const host=$('mC');
    if(!host.dataset.built){
      host.innerHTML =
        '<div class="small" style="margin:2px 0"><b>站上三篇长文，全由基底挑。</b>'+
        '程序先<b>随机</b>抽定一篇 A（固定不换）→ 在站上长文里找与 A 斜对立的 B → '+
        '再找同时顶住 A 和 B 的 C；站内配不到就退到基底知识库。</div>'+
        '<div class="small" style="margin:8px 0;color:var(--muted)">'+
        '⛓ 硬约束：<b>三篇必须分属三个不同栏目</b>——同栏目的文章多半在同一根轴上，'+
        '只能正面对顶，撞不出新框架。</div>';
      host.dataset.built='1';
    }
  }"""
rep(old_b, new_b)

# ---------- 4. updateSrcState：B / C / D 改成自动 ----------
old_s = """  let n = 0;
  if(ST.mode==='A') n = stuPicked.length;
  else if(ST.mode==='B') n = [0,1,2].filter(i=>$('bArt'+i) && $('bArt'+i).value).length;
  else if(ST.mode==='C') n = [0,1,2].filter(i=>$('cSel'+i) && $('cSel'+i).value).length;
  else if(ST.mode==='D'){
    const t=($('dTopic').value||'').trim();
    $('srcState').textContent = t ? '三家理论由基底联网去找（议题：'+t.slice(0,18)+'）' : '先给一个议题';
    return t.length>=4 ? 3 : 0;
  }"""
new_s = """  if(ST.mode==='B'){
    $('srcState').textContent = '由基底从全站 '+STUDENTS.length+' 位学员里挑三位、各挑一篇';
    return 3;
  }
  if(ST.mode==='C'){
    $('srcState').textContent = '由基底从站上 '+poolSite().length+' 篇长文里挑三篇（三个不同栏目）';
    return 3;
  }
  let n = 0;
  if(ST.mode==='A') n = stuPicked.length;
  else if(ST.mode==='D'){
    const t=($('dTopic').value||'').trim();
    $('srcState').textContent = t ? '三家理论由基底联网去找（议题：'+t.slice(0,18)+'）' : '议题与三个领域都由基底自己定';
    return 3;
  }"""
rep(old_s, new_s)

# ---------- 5. collectSources：B / C 交给选篇工序 ----------
old_c = """  } else if(ST.mode==='B'){
    for(const i of [0,1,2]){
      const url = $('bArt'+i).value;
      const title = ($('bArt'+i).selectedOptions[0]||{}).textContent||'';
      const author = ($('bStu'+i).selectedOptions[0]||{}).textContent||'';
      if(!url) throw new Error('模式 B 的第 '+(i+1)+' 个源还没选。');
      out.push({ title, url, author, text: await pullText(url) });
    }
  } else if(ST.mode==='D'){
    return [];                                    // 三家由「选篇」那一格联网去找
  } else if(ST.mode==='C'){
    for(const i of [0,1,2]){
      const url = $('cSel'+i).value;
      const title = ($('cSel'+i).selectedOptions[0]||{}).textContent||'';
      if(!url) throw new Error('模式 C 的第 '+(i+1)+' 个源还没选。');
      out.push({ title, url, author:'', text: await pullText(url) });
    }
  } else {"""
new_c = """  } else if(ST.mode==='B' || ST.mode==='C' || ST.mode==='D'){
    return [];                                    // 三篇/三家全由「选篇」那一格去挑
  } else {"""
rep(old_c, new_c)

# ---------- 6. runStage 分派：B / C 也走 doSelect ----------
rep("""    if(ST.mode==='D') return await doSelectWeb();
    if(ST.mode!=='A' || ST.manual){ setStat('select', '跳过（源已指定）'); ST.out.select=''; return ''; }
    return await doSelect();""",
    """    if(ST.mode==='D') return await doSelectWeb();
    // 手挑只在 A 模式里存在（勾选框在 mA 里）；B/C 一律自动，不认这个残留标志。
    if(ST.mode==='A' && ST.manual){ setStat('select', '跳过（源已指定）'); ST.out.select=''; return ''; }
    if(ST.mode==='F'){ setStat('select', '跳过（源已指定）'); ST.out.select=''; return ''; }
    return await doSelect();""")

# ---------- 7. 选源阶梯与硬约束：随模式而变 ----------
old_r = """/* 随机抽一个本人栏 gid（避开已当过 A 的） */
function randSelfGid(usedGids){
  const self=poolSelf().filter(x=>(usedGids||[]).indexOf(x.gid)<0);
  if(!self.length) return null;
  return self[Math.floor(Math.random()*self.length)].gid;
}"""
new_r = """/* ============ 选源：随模式而变的种子池、阶梯起点、三篇之间的硬约束 ============
   A 一人三篇：种子出自选定学员本人栏，阶梯 本人栏→其他学员→全站→知识库，无额外约束。
   B 三人各一篇：先随机定一位学员，种子出自他本人栏；阶梯**从其他学员起步**，
     并强制三篇三位不同作者。
   C 站上三长文：种子出自全站长文；阶梯从全站起步，并强制三篇分属三个不同栏目。
   ——随机数一律在程序里产生、不交给基底：基底的"随机"是它的偏好，会反复挑同几篇。 */
function seedPool(){ return ST.mode==='C' ? poolSite() : poolSelf(); }
function rungStart(){ return ST.mode==='B' ? 1 : ST.mode==='C' ? 2 : 0; }
/* 模式 B：随机定一位有篇目的学员当第一人（整趟只定一次，定完 L# 编号才稳） */
function pickRandomStudent(){
  const sel=$('stuSel'); if(!sel || !STUDENTS.length) return;
  if(!sel.options.length){
    sel.innerHTML = optionsFor(STUDENTS, s=>s.slug, s=>s.name+'（'+(s.items||[]).length+' 篇）');
  }
  const ok=STUDENTS.filter(s=>(s.items||[]).length);
  if(!ok.length) return;
  sel.value = ok[Math.floor(Math.random()*ok.length)].slug;
}
/* 防重心的硬约束：把与已选篇目"同作者"（B）或"同栏目"（C）的候选整片剔出候选清单。
   剔在给基底看之前——写进调令让它"注意避开"没用，它会挑一篇最顺手的然后解释一下。 */
function distinctFilter(list, chosen){
  const key = ST.mode==='B' ? 'author' : ST.mode==='C' ? 'kind' : '';
  if(!key) return list;
  const taken=(chosen||[]).map(g=>{ const x=isGid(g)?poolByGid(g):g; return x?String(x[key]||''):''; })
                          .filter(Boolean);
  if(!taken.length) return list;
  return list.filter(x=> taken.indexOf(String(x[key]||''))<0);
}
/* 随机抽一个种子 gid（避开已当过 A 的） */
function randSelfGid(usedGids){
  const pool=seedPool().filter(x=>(usedGids||[]).indexOf(x.gid)<0);
  if(!pool.length) return null;
  return pool[Math.floor(Math.random()*pool.length)].gid;
}"""
rep(old_r, new_r)

# ---------- 8. doSelect：整趟开头定第一人；阶梯起点随模式 ----------
rep("""  ST.usedA=ST.usedA||[]; ST.badC=ST.badC||[];
  const limit=Math.max(maxR, ST.tried.length+2);""",
    """  ST.usedA=ST.usedA||[]; ST.badC=ST.badC||[];
  // 模式 B 的第一人整趟只随机定一次：定完之后 L# 编号才稳（L3 在不同学员栏里指的不是同一篇）。
  if(ST.mode==='B' && !ST.pair && !ST.usedA.length){
    pickRandomStudent();
    selLog('随机定第一人：<b>'+escTxt((curStudent().name)||'')+'</b>（另两篇必须换人）。');
  }
  const limit=Math.max(maxR, ST.tried.length+2);""")

rep("""      const aGid=randSelfGid(ST.usedA);
      if(!aGid){ selLog('这位学员的篇目已经全部当过 A 了。'); break; }""",
    """      const aGid=randSelfGid(ST.usedA);
      if(!aGid){ selLog(ST.mode==='C' ? '站上长文已经全部当过 A 了。' : '这位学员的篇目已经全部当过 A 了。'); break; }""")

rep("""      for(let rung=0; rung<=3 && !locked && !ST.abort; rung++){
        ST.__rung=rung;
        if(rung<=2){
          ST.__pool=poolDelta(rung).filter(x=>x.gid!==aGid && triedB.indexOf(x.gid)<0);""",
    """      for(let rung=rungStart(); rung<=3 && !locked && !ST.abort; rung++){
        ST.__rung=rung;
        if(rung<=2){
          ST.__pool=distinctFilter(poolDelta(rung).filter(x=>x.gid!==aGid && triedB.indexOf(x.gid)<0), [aGid]);""")

# ---------- 9. findCForPair：阶梯起点与硬约束 ----------
rep("""  for(let rung=0; rung<=2 && !ST.abort; rung++){
    ST.__crung=rung;
    ST.__pool=poolDelta(rung).filter(x=>x.gid!==aGid && !(isGid(bDesc)&&x.gid===bDesc) && ST.badC.indexOf(x.gid)<0);""",
    """  for(let rung=rungStart(); rung<=2 && !ST.abort; rung++){
    ST.__crung=rung;
    ST.__pool=distinctFilter(
      poolDelta(rung).filter(x=>x.gid!==aGid && !(isGid(bDesc)&&x.gid===bDesc) && ST.badC.indexOf(x.gid)<0),
      [aGid, bDesc]);""")

# ---------- 10. 调令里把硬约束交代清楚 ----------
rep("""      (ST.__rung>0 ? ('\\n（这一层找的是 **'+RUNG_CN[ST.__rung]+'** 的文章——本人栏里没找到能顶 A 的，往外扩了一层。跨作者、跨学科反而更容易真打架。）') : ''),""",
    """      (ST.__rung>ST.__rung0 ? ('\\n（这一层找的是 **'+RUNG_CN[ST.__rung]+'** 的文章——更近的范围里没找到能顶 A 的，往外扩了一层。跨作者、跨学科反而更容易真打架。）') : ''),
      constraintBlock(),""")
rep("""      (ST.__crung>0 ? ('（这一层找的是 **'+RUNG_CN[ST.__crung]+'** 的文章——更近的范围里没有能同时顶两篇的，往外扩了一层。）') : ''),""",
    """      (ST.__crung>ST.__rung0 ? ('（这一层找的是 **'+RUNG_CN[ST.__crung]+'** 的文章——更近的范围里没有能同时顶两篇的，往外扩了一层。）') : ''),
      constraintBlock(),""")

rep("""function promptFor(id){
  const O = ST.out;""",
    """/* 硬约束交代给基底一句（清单其实已经剔干净了，这句只是让它知道为什么清单是这样） */
function constraintBlock(){
  if(ST.mode==='B') return '（下面这份清单已经把与已选篇目**同作者**的文章整片剔掉了——这一路要的是三位不同作者各一篇。）';
  if(ST.mode==='C') return '（下面这份清单已经把与已选篇目**同栏目**的文章整片剔掉了——这一路要的是三个不同栏目各一篇。）';
  return '';
}
function promptFor(id){
  const O = ST.out;
  ST.__rung0 = rungStart();""")



old = """/* 防重心的硬约束：把与已选篇目"同作者"（B）或"同栏目"（C）的候选整片剔出候选清单。
   剔在给基底看之前——写进调令让它"注意避开"没用，它会挑一篇最顺手的然后解释一下。 */
function distinctFilter(list, chosen){
  const key = ST.mode==='B' ? 'author' : ST.mode==='C' ? 'kind' : '';
  if(!key) return list;
  const taken=(chosen||[]).map(g=>{ const x=isGid(g)?poolByGid(g):g; return x?String(x[key]||''):''; })
                          .filter(Boolean);
  if(!taken.length) return list;
  return list.filter(x=> taken.indexOf(String(x[key]||''))<0);
}"""

new = """/* ============ 防重心：把与已选篇目同族的候选剔出清单 ============
   剔在给基底看之前——写进调令让它"注意避开"没用，它会挑一篇最顺手的然后解释一下。

   两道，都机械算，不问基底：
   ① 同作者（只在 B 模式）——三人各一篇，作者字段是真的，直接剔。
      （C 模式本想剔"同栏目"，但 catalog 里没有栏目字段：站上长文 306 篇有 270 篇
        的 c 都是"今日长文"，按它剔会把池子掏掉九成。所以 C 只走第②道。）
   ② 语汇族重叠——标题＋摘要的汉字二元组 Jaccard。站内实测：中位 0、p95 0.035、
      p99 0.091，所以 0.06 只剔掉最像的约 2%，正是同语汇族那条尾巴，不会掏空池子。
      **它只抓表层近重复，抓不到"收编/加固/闭环其实是同一套话语"那一层**——
      那一层要靠近邻库，不是靠这把尺子。 */
var VOCAB_SIM_MAX = 0.06, VOCAB_POOL_MIN = 8;
function cjkBigrams(s){
  const t=String(s||'').replace(/[^\\u4e00-\\u9fff]/g,''), out={};
  for(let i=0;i+1<t.length;i++) out[t.slice(i,i+2)]=1;
  return out;
}
function vocabSig(x){ return cjkBigrams(String(x.title||'')+String(x.summary||'').slice(0,150)); }
function jaccard(a,b){
  const ka=Object.keys(a), kb=Object.keys(b);
  if(!ka.length || !kb.length) return 0;
  let inter=0; for(const k of ka) if(b[k]) inter++;
  return inter/(ka.length+kb.length-inter);
}
function distinctFilter(list, chosen){
  const picked=(chosen||[]).map(g=>isGid(g)?poolByGid(g):g).filter(Boolean);
  if(!picked.length) return list;
  let out=list;
  // ① 同作者（仅 B）
  if(ST.mode==='B'){
    const authors=picked.map(x=>String(x.author||'')).filter(Boolean);
    if(authors.length) out=out.filter(x=> authors.indexOf(String(x.author||''))<0);
  }
  // ② 语汇族重叠（B / C 都走）——池子太小就逐级放宽，宁可放行也不制造死锁，
  //    但每次放宽都留一行日志，免得这道闸悄悄变成橡皮图章。
  if(ST.mode==='B' || ST.mode==='C'){
    const sigs=picked.map(vocabSig);
    for(let thr=VOCAB_SIM_MAX; thr<=0.5; thr+=0.06){
      const kept=out.filter(x=>{ const s=vocabSig(x); return sigs.every(p=>jaccard(s,p)<thr); });
      if(kept.length>=Math.min(VOCAB_POOL_MIN, out.length)){
        if(thr>VOCAB_SIM_MAX) selLog('语汇族这道闸放宽到 '+thr.toFixed(2)+' 才留得下候选（池子偏小）。');
        return kept;
      }
    }
    selLog('⚠ 语汇族这道闸这一层拦不住了（候选太少），本层放行未过滤的清单。');
  }
  return out;
}"""
rep(old,new)

# 调令里那句交代同步改口径
rep("""  if(ST.mode==='C') return '（下面这份清单已经把与已选篇目**同栏目**的文章整片剔掉了——这一路要的是三个不同栏目各一篇。）';""",
    """  if(ST.mode==='C') return '（下面这份清单已经把与已选篇目**语汇高度重合**的文章整片剔掉了——同一套话语里撞不出新框架。）';""")
rep("""  if(ST.mode==='B') return '（下面这份清单已经把与已选篇目**同作者**的文章整片剔掉了——这一路要的是三位不同作者各一篇。）';""",
    """  if(ST.mode==='B') return '（下面这份清单已经把与已选篇目**同作者**、以及**语汇高度重合**的文章整片剔掉了——这一路要的是三位不同作者各一篇。）';""")

# C 模式面板文案跟着改
rep("""        '⛓ 硬约束：<b>三篇必须分属三个不同栏目</b>——同栏目的文章多半在同一根轴上，'+
        '只能正面对顶，撞不出新框架。</div>';""",
    """        '⛓ 硬约束：候选清单里<b>与已选篇目语汇高度重合的会被整片剔掉</b>（标题＋摘要的'+
        '汉字二元组重叠率 ≥0.06，站内实测这一刀只切掉最像的约 2%）——同一套话语里撞不出新框架。</div>';""")
rep("""        '⛓ 硬约束：<b>三篇必须出自三位不同作者</b>——同一作者的文章共用一套语汇，'+
        '撞得再多也只会收敛到这套语汇的重心，而重心正是被占满的地方。</div>';""",
    """        '⛓ 硬约束：<b>三篇必须出自三位不同作者</b>，且语汇高度重合的候选会被整片剔掉——'+
        '同一套语汇撞得再多，也只会收敛到这套语汇的重心，而重心正是被占满的地方。</div>';""")


# ---------- 11. 删掉随手选下拉一起作废的 fillB / fillC ----------
rep("""function fillB(i){
  const slug = $('bStu'+i).value;
  const st = STUDENTS.find(s=>s.slug===slug) || {items:[]};
  $('bArt'+i).innerHTML = optionsFor(st.items||[], x=>x.url, x=>x.title);
}
function fillC(i, q){
  let list = CATALOG;
  if(q) list = CATALOG.filter(x=> (x.t+' '+(x.d||'')).indexOf(q) >= 0);
  list = list.slice(0, 300);
  const sel = $('cSel'+i);
  const keep = sel.value;
  sel.innerHTML = optionsFor(list, x=>x.u, x=>'['+x.c+'] '+x.t);
  if(keep && list.some(x=>x.u===keep)) sel.value = keep;
  else if(list.length) sel.selectedIndex = Math.min(i*3, list.length-1);
}
""", "/* fillB / fillC 随 B、C 两个模式的手选下拉一起删了（改成基底自动选源，2026-07-30）。 */\n")

# ---------- 12. 测试探针 ----------
rep("function distinctFilter(list, chosen){", """/* 测试探针：顶层 const 不会挂上 window，模拟脚本够不着内部状态。
   语汇族这道闸是纯函数，直测比端到端可靠——所以把它和只读的 ST 一起露出来。
   页面自身一律不读 __forge，它只服务 tools/sim_paradigm_forge.js 与手工排障。 */
window.__forge = {
  get ST(){ return ST; },
  get VOCAB_SIM_MAX(){ return VOCAB_SIM_MAX; },
  cjkBigrams: cjkBigrams, vocabSig: vocabSig, jaccard: jaccard,
  distinctFilter: function(list, chosen){ return distinctFilter(list, chosen); }
};
function distinctFilter(list, chosen){""")

# ---------- 13. 模式 D：议题可留空，由基底自己定 ----------
rep("""async function doSelectWeb(){
  const id='select', p=panels[id];
  openStage(id);
  const topic = ($('dTopic').value||'').trim();
  if(topic.length < 4) throw new Error('模式 D 要先给一个议题（至少四个字）。');
  const skey = $('dSiteKey').checked ? '' : ($('dSkey').value||'').trim();""",
"""/* 议题也不该由用户输入：留空就让基底自己定一个，并且**强制避开已经撞过的那些地**——
   同一块地再撞一次，撞出来的只会是同一个东西。 */
async function pickTopic(p){
  setStat('select', '<span class="spinner"></span> 基底自己定议题', 'run');
  const pp = [
    '这一路要撞的是**站外三个不同领域的现行理论**。第一步：由你自己定一个议题。',
    '',
    '要求：',
    '· 一句话，≤30 字，是一个**能被不同学科分别回答、而各科答案会互相打架**的问题；',
    '· 不要已经有公认答案的；也不要大到一句话答不了的（"什么是意识"这种不行）；',
    '· **必须避开下面这份已经撞过的清单**——同一块地再撞一次只会撞出同一个东西。',
    '',
    '【已经撞过的（别再选同一块地）】',
    prevList() || '（暂无）',
    '',
    '【输出：正好一行，不要解释，不要加粗】',
    '议题：……'
  ].join('\\n');
  const r = await askFast(sdeSystem(), pp, p.out, p.stat, p.meta, 600, '定议题');
  const m = /议题[：:]\\s*(.+)/.exec(r.text||'');
  const raw = (m ? m[1] : ((r.text||'').split('\\n').map(x=>x.trim()).filter(Boolean)[0] || ''));
  return raw.replace(/^[「《\\u201c"'*\\s]+|[」》\\u201d"'*。\\s]+$/g,'').slice(0,60);
}
async function doSelectWeb(){
  const id='select', p=panels[id];
  openStage(id);
  let topic = ($('dTopic').value||'').trim();
  if(topic.length < 4){
    topic = await pickTopic(p);
    if(topic.length < 4) throw new Error('基底没能定出一个议题——自己在议题那一格给一个再跑，或改用 F 模式。');
    $('dTopic').value = topic;
    selLog('基底自定议题：<b>'+escTxt(topic)+'</b>');
  }
  const skey = $('dSiteKey').checked ? '' : ($('dSkey').value||'').trim();""")

rep("""      <div class="small" style="margin-top:8px">基底先把这个议题拆成三个**不同领域**的检索词，各搜一轮，再从搜到的东西里挑三家<b>斜着对立</b>的理论。</div>""",
    """      <div class="small" style="margin-top:8px">留空 → 基底先自己定一个议题（强制避开站上已经撞过的那些）；然后把议题拆成三个<b>不同领域</b>的检索词，各搜一轮，再从搜到的东西里挑三家<b>斜着对立</b>的理论。</div>""")

io.open(P, "w", encoding="utf-8").write(h)
print("模板替换 %d 处 OK" % n)
