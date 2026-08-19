#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给「SDE 碰撞出典范」装近邻三关（改 tools/forge/forge.template.html）。

为什么：这一页原先只用 /api/kb/retrieve（语料块，拿不到只是答得浅），
没有用专用的 /api/kb/neighbors（**必须逐条交代分离线的名单**，拿不到→
概念被第二次发明，而且是静默失败，没有人会收到报错）。金点子发生器与
中华智问两处早已接上并共用判据模块 sde-nbr-gate.js，唯独这一页没有。
线上评审自己写着「没有与既有概念逐一划界的，I 封顶 130」——那正是压住
150 的那一维。

与那两页的一处**故意不同**：闸门查的是【近邻划界格的产物】，不是成品。
成品是散文体、要求零工序痕迹（用户 2026-07-29 定），往正文里塞一节叫
「近邻检测」的东西恰恰是被封禁的那种痕迹。所以可解析形状只活在引擎室，
成品里只留散文体的「这与某某说的不是一回事」。

用法：python3 tools/patch_forge_nbr.py && python3 tools/build_forge_page.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "tools", "forge", "forge.template.html")


def sub1(h, old, new, name):
    assert old in h, "锚不到：" + name
    assert h.count(old) == 1, "锚不唯一（%d 处）：%s" % (h.count(old), name)
    return h.replace(old, new, 1)


def main():
    h = open(TPL, encoding="utf-8").read()

    # ── 一、加载共用模块（与金点子/中华智问同两行，版本号一致） ──
    h = sub1(h,
             '<script src="/assets/wds-savedir.js"></script>',
             '<script src="/assets/wds-savedir.js"></script>\n'
             '<!-- 站内近邻：端点客户端 + 三关判据。判据只有一份来源，复制两份必漂，而那种漂是静默的 -->\n'
             '<script src="/taste/assets/sde-rag.js?v=20260817c"></script>\n'
             '<script src="/taste/assets/sde-nbr-gate.js?v=20260817c"></script>',
             "script 标签")

    # ── 二、nbrList()：多种子并发取名单，合并去重 ──
    old_kb_tail = """    const j = await r.json();
    return (j && j.block) ? j.block : '';
  }catch(e){ return ''; }
}
"""
    new_kb_tail = old_kb_tail + """
/* 站内近邻名单 —— 与 kbCtx 的分工是硬的：
     retrieve 交付「可垫进调令的语料块」，拿不到只是答得浅；
     neighbors 交付「必须逐条交代分离线的名单」，拿不到就会把同一个概念第二次发明。
   所以两样都取、**并存不替换**，且名单**前置**在语料之前——放在后面会被语料埋掉。 */
const NBR_CHECK_MARK = '近邻检测';        // 让判据认得出这一节（sde-nbr-gate.js 的 sectionOK 按它找）
const NBR_DISC_MARK  = '本文所属学科';    // 学科标注的锚：想让什么被检查，先让它有个可解析的形状
async function nbrOne(q, k){
  try{
    if(window.SDERag && window.SDERag.neighbors) return (await window.SDERag.neighbors(q, {k:k||8})) || '';
    const r = await fetch('/api/kb/neighbors', { method:'POST', headers:{'content-type':'application/json'},
      body: JSON.stringify({ q:String(q||'').slice(0,2000), k:k||8 }) });
    if(!r.ok) return '';
    const j = await r.json();
    return (j && j.block) ? j.block : '';
  }catch(e){ return ''; }
}
/* 多种子：一个种子只查一个角度。撞车最常发生在**最终那个命名**上——
   概念名往往不在标题里、只在副标题或关键词里，用「话题」去查根本召回不到。
   所以命名必须单独当一个种子查一遍。失败即空串，安全退回（名单缺失不该让整格失败）。 */
async function nbrList(seeds, k){
  const qs = [];
  (seeds||[]).forEach(s=>{
    const t = String(s||'').replace(/\\s+/g,' ').trim();
    if(t.length > 3 && qs.indexOf(t) < 0) qs.push(t.slice(0,600));
  });
  if(!qs.length) return '';
  let blocks = [];
  try{ blocks = await Promise.all(qs.slice(0,4).map(q=>nbrOne(q, k))); }catch(e){ return ''; }
  const seen = {}, head = [], rows = [];
  blocks.filter(Boolean).join('\\n').split('\\n').forEach(ln=>{
    const t = ln.replace(/\\s+$/,'');
    if(!t.trim()) return;
    const body = t.replace(/^\\s*\\d+、/, '').trim();          // 各块各自从 1 起编号，去掉再统一重编
    const key = body.replace(/\\s+/g,'').slice(0,40);
    if(!key || seen[key]) return;
    seen[key] = 1;
    if(/^【|^对下列每一篇|^凡划不出|^同一个作者/.test(body)) head.push(t);
    else rows.push(body);
  });
  if(!rows.length) return '';
  const out = [];
  let n = 0;
  rows.forEach(r=>{ if(/^　　/.test(r) || /^该篇的判断/.test(r)) out.push('　　'+r.replace(/^　*/,'')); else out.push((++n)+'、'+r); });
  return head.join('\\n') + '\\n' + out.slice(0, 90).join('\\n');
}
/* 抽出这一次的命名：涌现格要求「命名涌现物：≤20字，结构性命名」，成品里也会用它。
   共用模块的 coinedName 认五种措辞；它抽不出时退回涌现格产物里的「命名：X」一行。 */
function forgeCoined(){
  const em = ST.out.emerge || '';
  if(window.SDENbr && window.SDENbr.coinedName){
    const n = window.SDENbr.coinedName(em);
    if(n) return n;
  }
  const m = em.match(/命名[：:]\\s*[「“"《【]?([^」”"》】，。；\\n]{2,20})/)
        || em.match(/[「“"《【]([^」”"》】]{2,20})[」”"》】]\\s*[（(]?(?:性|症|悖论|陷阱|耦合)/);
  return m ? m[1].trim() : '';
}
"""
    h = sub1(h, old_kb_tail, new_kb_tail, "nbrList 注入")

    # ── 三、近邻划界调令：名单前置 + 可解析形状 + 判决性预测 ──
    old_demarc = """  if(id==='demarc') return [
    '下面是撞出来的判断。请把它与既有说法逐一划清界线——这一步决定它是不是换皮。',
    '要求：选 6–10 个最容易被读者混为一谈的既有概念（学界成名概念优先，也可包括本站已发的近邻篇目），逐一写：',
    '  · 那个概念讲的是什么（一句话，公允）',
    '  · 本判断讲的是什么',
    '  · 判据差在哪（必须落到一个可分辨的差别上，不许停在\"侧重不同\"）',
    '并在最后指出：其中哪一个是最近的邻居、为什么本判断仍不可被它吸收。',
    '',
    '【本判断】', O.emerge || '',
    '', (window.__KB ? ('【站内可参照的近邻材料】\\n'+window.__KB) : '')
  ].join('\\n');
"""
    new_demarc = """  if(id==='demarc') return [
    '下面是撞出来的判断。请把它与既有说法逐一划清界线——这一步决定它是不是换皮。',
    '**这一格是引擎室的中间产物，不是成品**，所以要写成可被逐条核对的形状；成品那一步会把它改写成散文。',
    '',
    '输出的第一行必须是：'+NBR_CHECK_MARK,
    '第二行必须是：'+NBR_DISC_MARK+'：XXX（一个学科名，如社会学／法学／认知心理学）',
    '',
    '然后选 6–10 个最容易被读者混为一谈的既有概念，逐一写。**其中至少 3 个必须点到名**——',
    '点名的形状是「（作者 年份）」或《作品》，一个该领域的人一听就知道指什么才算点到；',
    '**至少一个必须来自本文学科之外**（否则这条判断只是本行当内部的一次整理）。每条写四件：',
    '  · 出处：概念名（作者 年份）或《作品》，紧跟一个「（学科：XXX）」标注',
    '  · 它说到哪一步（一句话，公允；不许写成稻草人）',
    '  · 本判断说的是什么，分离线落在哪（必须是一个**可分辨的差别**，不许停在\"侧重不同\"\"更强调\"）',
    '  · 判决性对照预测：一句「若……则本文错」——一个两者会给出相反答案的具体情形',
    '',
    '站内近邻名单是**硬要求**：名单里的每一篇都要在上面出现一次，或明说它与本判断重复；',
    '标注「本人已发」的尤其要查——同一个作者重复发明概念，是最不容易被自己发现的一种重合。',
    '最后指出：哪一个是最近的邻居、为什么本判断仍不可被它吸收。',
    '',
    '【本判断】', O.emerge || '',
    ST.coined ? ('【这一次的命名（分离线要针对它，不是针对话题）】'+ST.coined) : '',
    '', (window.__NBR ? window.__NBR : ''),
    '', (window.__KB ? ('【站内可参照的语料（背景，不是待交代的名单）】\\n'+window.__KB) : '')
  ].join('\\n');
"""
    h = sub1(h, old_demarc, new_demarc, "demarc 调令")

    # ── 四、评审调令：把名单交给评审去核对（它自己有 I 封顶 130 那条铁律） ──
    old_rev = """    '  · 没有与既有概念逐一划界的，I 封顶 130；'"""
    new_rev = """    '  · 没有与既有概念逐一划界的，I 封顶 130；下面附了站内近邻名单，名单里没被交代的篇目每一篇再减 2；'"""
    h = sub1(h, old_rev, new_rev, "review 铁律")

    old_rev2 = """    '',
    '【待评文章】',
    (ST.article || '').slice(0, 24000)
  ].join('\\n');
"""
    new_rev2 = """    '',
    (window.__NBR ? (window.__NBR + '\\n') : ''),
    '【待评文章】',
    (ST.article || '').slice(0, 24000)
  ].join('\\n');
"""
    h = sub1(h, old_rev2, new_rev2, "review 附名单")

    # ── 五、runStage：涌现后抽命名；近邻格两样都取；产出过两关 ──
    old_run = """  if(s.id==='demarc'){
    try{ window.__KB = await kbCtx(((ST.out.emerge||'').slice(0,600))); }catch(e){ window.__KB=''; }
  }
"""
    new_run = """  if(s.id==='demarc'){
    // 名单与语料两样都取：名单是待交代的清单（缺了会静默地把概念第二次发明），语料只是背景。
    ST.coined = forgeCoined();
    const seeds = [ (ST.out.emerge||'').slice(0,600), ST.coined,
                    (ST.spineRows||[]).map(r=>r.theme||'').join(' ').slice(0,300) ];
    try{
      const [nb, kb] = await Promise.all([ nbrList(seeds, 8), kbCtx(((ST.out.emerge||'').slice(0,600))) ]);
      window.__NBR = nb || ''; window.__KB = kb || '';
    }catch(e){ window.__NBR=''; window.__KB=''; }
    if(!window.__NBR) note('站内近邻名单这次取不到（端点或索引不可用）——划界照做，但\"最近的那个对手\"没上桌，发表前请自己核一遍。');
  }
"""
    h = sub1(h, old_run, new_run, "runStage 取名单")

    old_after = """  if(s.id==='gate'){
    const m = txt.match(/闸一[：:]\\s*分数\\s*(\\d+)/) || txt.match(/(\\d+)\\s*\\/\\s*10/);"""
    new_after = """  if(s.id==='demarc'){
    // 两关就地查（第三关"最终命名有没有被查过"要等成品出来才知道，放在成文之后）：
    //   关一 有没有真做检测（点名≥3 + 判决性预测）· 关三 三个近邻是不是全挤在同一学科。
    // 判据只有一份来源：共用模块 sde-nbr-gate.js。模块没加载成功就整关跳过——
    // 闸门冤枉一篇好文章的代价，比放过一篇没跨域的更大。
    const G = window.SDENbr;
    if(G){
      const okSec = G.sectionOK(txt);
      const cross = G.crossOK(txt);          // true / false / null（看不出→放行）
      const why = !okSec ? '没点够名或缺判决性对照预测' : (cross === false ? '六到十个近邻全挤在同一学科内' : '');
      ST.nbrWhy = why;
      setStat('demarc', (why ? '⚠ ' : '✓ ') + (why || '划界达标 · 已点名并给出判决性预测'), 'done');
      if(why){
        note('近邻划界没过闸：'+why+'。');
        if($('autoRedoChk') && $('autoRedoChk').checked && ST.nbrRetry < 1){
          ST.nbrRetry++;
          showErr('近邻划界没过闸（'+why+'）——正在重跑这一格。');
          ST.redoFrom = STAGES.findIndex(x=>x.id==='demarc');
        } else {
          showErr('近邻划界没过闸：'+why+'。划界是评审 I 维的硬门槛（不划界 I 封顶 130）——'
                + '要重做就点这一格的「重跑本格」，或用「编辑产物」自己补上，或就这样往下走——由你决定。');
        }
      }
    }
  }
  if(s.id==='gate'){
    const m = txt.match(/闸一[：:]\\s*分数\\s*(\\d+)/) || txt.match(/(\\d+)\\s*\\/\\s*10/);"""
    h = sub1(h, old_after, new_after, "demarc 两关")

    # ── 六、成文之后：第三关（最终命名有没有被查过） ──
    old_deliver = """  $('deliver').style.display='';
  return ST.article;
}
"""
    new_deliver = """  await nbrPostName();
  $('deliver').style.display='';
  return ST.article;
}

/* 第三关：查的是不是最后真用上的那个名字。
   这一关是为「成文时改了名」造的——划界那一格照 A 名查得再干净，成品里叫了 B 名，
   等于没查。抽不出名字就放行（宁可漏查，不可乱查）。
   注意这里**不往正文里加节**：成品要零工序痕迹，分界只能以散文形态混在行文里，
   所以补法是带着点名重跑成文，而不是往尾巴上贴一节。 */
async function nbrPostName(){
  const G = window.SDENbr;
  if(!G || !ST.article) return;
  let name = '';
  try{ name = G.coinedName(ST.article) || ''; }catch(e){ return; }
  if(!name) return;
  ST.finalName = name;
  const checked = String(ST.coined||'');
  if(checked && (name.indexOf(checked) >= 0 || checked.indexOf(name) >= 0)) return;   // 与查过的是同一个名字
  let blk = '';
  try{ blk = await nbrList([name], 6); }catch(e){ return; }
  if(!blk) return;
  const titles = (blk.match(/《([^》]{2,60})》/g) || []).map(s=>s.slice(1,-1));
  const missed = titles.filter(t=>{
    const head = t.replace(/[：:—\\-·].*$/,'').slice(0,10);
    return head && ST.article.indexOf(head) < 0;
  });
  if(!missed.length) return;
  ST.nbrMissed = missed;
  note('成品里的命名「'+name+'」与划界那一格查的不是同一个（查的是「'+(checked||'（未抽出）')+'）」，重查后还有 '+missed.length+' 篇站内近邻没被交代。');
  if($('autoRedoChk') && $('autoRedoChk').checked && ST.nbrRetry2 < 1){
    ST.nbrRetry2++;
    ST.nameFix = { name:name, missed:missed.slice(0,6) };
    showErr('成品的命名「'+name+'」还有 '+missed.length+' 篇站内近邻没交代——正在带着这些篇目重写一遍。');
    ST.redoFrom = STAGES.findIndex(s=>s.id==='write');
    return;
  }
  showErr('成品里管这件事叫「'+name+'」，而划界那一格查的是另一个名字。拿这个名字重查，站内还有这些篇目没被交代：'
        + missed.slice(0,6).map(t=>'《'+t+'》').join('、')
        + '。同名或近名重复发明是最难自查的一种撞车——要带着它们重写就点成文格的「重跑本格」，或自己核一遍。');
}
"""
    h = sub1(h, old_deliver, new_deliver, "成文后第三关")

    # 成文调令要能吃下 nameFix（重写时带着那些篇目点名）
    old_head = """  const fix = ST.termFix;
  ST.termFix = null;
  const head = ["""
    new_head = """  const fix = ST.termFix;
  ST.termFix = null;
  const nf = ST.nameFix;
  ST.nameFix = null;
  const head = [
    nf ? ('【上一稿把这件事命名为「'+nf.name+'」，而站内这些篇目讲的是很近的东西、正文里一句没提：'
        + nf.missed.map(t=>'《'+t+'》').join('、')
        + '。这一稿要在行文里把与它们的分界交代清楚——**当散文写**，不许另起一节、不许标\"近邻\"\"划界\"这类节名，就写成\"这与某某说的不是一回事，因为……\"。】') : '',"""
    h = sub1(h, old_head, new_head, "成文吃 nameFix")

    # ── 七、清空复位：把新状态一并清掉（旧代码漏了 truncated / __KB） ──
    old_reset = """  ST.redoFrom=null; ST.rounds=0; ST.termRetry=0; ST.termFix=null; ST.notes=[];
  ST.spineRows=[]; ST.conflict='';"""
    new_reset = """  ST.redoFrom=null; ST.rounds=0; ST.termRetry=0; ST.termFix=null; ST.notes=[];
  ST.spineRows=[]; ST.conflict=''; ST.truncated=false;
  ST.coined=''; ST.finalName=''; ST.nbrWhy=''; ST.nbrMissed=null; ST.nameFix=null; ST.nbrRetry=0; ST.nbrRetry2=0;
  window.__NBR=''; window.__KB='';"""
    h = sub1(h, old_reset, new_reset, "清空复位")

    # ST 初值也补上（别让第一次跑读到 undefined）
    old_st = """             redoFrom:null, rounds:0, termRetry:0, termFix:null, notes:[],
             spineRows:[], conflict:'' };"""
    new_st = """             redoFrom:null, rounds:0, termRetry:0, termFix:null, notes:[],
             spineRows:[], conflict:'', truncated:false,
             coined:'', finalName:'', nbrWhy:'', nbrMissed:null, nameFix:null, nbrRetry:0, nbrRetry2:0 };"""
    h = sub1(h, old_st, new_st, "ST 初值")

    # ── 八、交付横幅：把划界结果也报出来 ──
    old_bits = """    ST.conflict ? ('主题冲突：'+ST.conflict) : ''
  ].filter(Boolean);"""
    new_bits = """    ST.conflict ? ('主题冲突：'+ST.conflict) : '',
    ST.nbrWhy ? ('⚠ 近邻划界：'+ST.nbrWhy) : (window.__NBR ? '近邻划界已过闸' : '近邻名单未取到'),
    (ST.nbrMissed && ST.nbrMissed.length) ? ('⚠ 命名「'+(ST.finalName||'')+'」还有 '+ST.nbrMissed.length+' 篇近邻未交代') : ''
  ].filter(Boolean);"""
    h = sub1(h, old_bits, new_bits, "交付横幅")

    open(TPL, "w", encoding="utf-8").write(h)
    print("patched:", os.path.relpath(TPL, ROOT), len(h), "字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
