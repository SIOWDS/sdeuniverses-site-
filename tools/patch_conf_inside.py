# -*- coding: utf-8 -*-
# 取材范围：站内＋站外（默认）／只用站内（闭库）
import re
p = '/home/claude/site/public/taste/confluence/index.html'
s = open(p, encoding='utf-8').read()
orig = s


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


# ① UI：取材范围下拉，紧跟「三个学科怎么来」那一行
rep("""    <div class="row" id="panelPick" style="margin-top:6px;display:none">""",
    """    <div class="row" style="margin-top:6px;align-items:center">
      <div style="min-width:300px">
        <label class="lbl">取材范围</label>
        <select id="cScope">
          <option value="both" selected>站内＋站外（站内面板打底，联网补站外的活争论）</option>
          <option value="inside">只用站内语料（闭库跑：一次都不联网）</option>
        </select>
      </div>
      <span class="small" style="flex:1;min-width:260px;color:var(--muted)">不选「只用站内」的话，<b>基底会自动去站外找</b>——那正是默认行为。闭库跑的代价要先知道：敌意拓宽的<b>经典层</b>与<b>专著</b>两个方向在库内常常取不到，产出的不可还原性会结构性偏低（站内六次实测，闭库与开库的分差每次都全部落在这一维）。</span>
    </div>
    <div class="row" id="panelPick" style="margin-top:6px;display:none">""")

# ② 读取开关
rep("""function pickMode(){ const e=$('cPickMode'); return e ? e.value : 'auto'; }""",
    """function pickMode(){ const e=$('cPickMode'); return e ? e.value : 'auto'; }
/* 取材范围：'both'＝站内＋站外；'inside'＝闭库，一次都不联网。
   这个开关必须存在，因为不给它，基底在「定三家」那一步会自动去站外找——
   而闭库跑是一个独立的实验条件（取源闭库），不是"少搜一点"。 */
function scopeMode(){ const e=$('cScope'); return e ? e.value : 'both'; }
function insideOnly(){ return scopeMode() === 'inside'; }""")

# ③ 闭库时收起联网相关的两格
rep("""function syncPickMode(){""",
    """function syncScope(){
  const on = insideOnly();
  ['cSiteKey','cSkey'].forEach(id=>{
    const el = $(id); if(!el) return;
    const box = el.closest ? (el.closest('label') || el) : el;
    box.style.display = on ? 'none' : '';
  });
  const kb = $('cUseKB');
  if(kb){ if(on){ kb.checked = true; kb.disabled = true; } else { kb.disabled = false; } }
  const pn = $('cUsePanel');
  if(pn){ if(on){ pn.checked = true; pn.disabled = true; } else { pn.disabled = false; } }
}
function syncPickMode(){""")

rep("""  if(e){ e.addEventListener('change', syncPickMode); syncPickMode(); }""",
    """  if(e){ e.addEventListener('change', syncPickMode); syncPickMode(); }
  const sc = document.getElementById('cScope');
  if(sc){ sc.addEventListener('change', syncScope); syncScope(); }""")

# ④ doSelectConf：闭库时不联网
rep("""  const useWeb = true;""",
    """  const INSIDE = insideOnly();
  const useWeb = !INSIDE;""")

# ⑤ 定学科提示词：闭库时池子是唯一来源，不许写 0
rep("""    CAT.length ? '池子里实在没有对口的那一门，才写 0（表示这一门走联网）。' : '',""",
    """    (CAT.length && !INSIDE) ? '池子里实在没有对口的那一门，才写 0（表示这一门走联网）。' : '',
    (CAT.length && INSIDE) ? '**本次是闭库跑：不联网，池子是唯一来源。三门都必须从上面这个池子里挑，一律不许写 0。**' : '',
    (CAT.length && INSIDE) ? '池子里没有那门学科的对口面板时，**换一门池子里有的**——换掉的那一门只要仍然能回答这道题、且与另两门不站在同一个位置上，就是合格的。' : '',""")

# ⑥ 取材：闭库跳过联网
rep("""  webRes = await Promise.all(rows.map(r =>
    webSearch(r.q, skey).then(x => { prog.web++; paint(); return x; })));""",
    """  if(INSIDE){
    /* 闭库：这一路整条不跑。不是"搜不到"，是"按口径不许搜"——两者在产物里必须分得清，
       所以下面的材料块会写〔本次闭库，未联网〕而不是〔这一门没搜到站外材料〕。 */
    webRes = rows.map(()=>({ ok:true, items:[], reason:'inside-only' }));
  } else {
    webRes = await Promise.all(rows.map(r =>
      webSearch(r.q, skey).then(x => { prog.web++; paint(); return x; })));
  }""")

rep("""') : '') + '联网 ' + prog.web + '/' + rows.length""",
    """') : '') + (INSIDE ? '（闭库：不联网）' : ('联网 ' + prog.web + '/' + rows.length))""")

# ⑦ 闭库时的失败判据换一套：不再看联网，只看面板与站内库
rep("""  if(badWeb && /need_search_key|bad_search_key/.test((badWeb.reason)||'')){""",
    """  if(INSIDE){
    /* 闭库的失败判据与开库不同：联网这一路本来就是空的，所以只能看另两路。
       两路都空时**必须停下**——绝不许静默地退回去联网，那会把实验条件换掉而没人知道。 */
    if(!panHitsPre && !kbHits) throw new Error(
      '本次选了「只用站内语料」，而面板供料层与站内库两路都没取到东西——闭库跑撑不起三家。'
      + '三条路：①换三门在站内面板里有对口块的学科；②把问题写得更具体些重跑本格；'
      + '③确实需要站外材料就把取材范围改回「站内＋站外」——但那是换了实验条件，成品里要写明。');
    if(panHitsPre < 3) note('闭库跑，但只有 ' + panHitsPre + ' 门落到了面板供料层上——'
      + '没落上的那几门只有站内篇目可用，位置与自曝两栏会薄，工序 7.5 的推翻材料可能取不到。');
  } else if(badWeb && /need_search_key|bad_search_key/.test((badWeb.reason)||'')){""")

# panHits 在 badWeb 判断之后才算 —— 闭库要提前算一次
rep("""  const badWeb = (!webRes.length) || webRes.find(x=>!x || !x.ok);""",
    """  const panHitsPre = panRes.filter(x=>x && x.length>60).length;
  const badWeb = (!webRes.length) || webRes.find(x=>!x || !x.ok);""")

rep("""  } else if(webHits < 3 && !kbHits){""",
    """  } else if(!INSIDE && webHits < 3 && !kbHits){""")

# ⑧ 材料块：闭库时如实写「未联网」，不写「没搜到」
rep("""    const w = (webRes[i] && webRes[i].ok) ? webBlockOf('W'+(i+1)+'-', (webRes[i].items)||[]) : '（这一门没搜到站外材料）';""",
    """    const w = INSIDE ? '（本次闭库，未联网——不是没搜到，是按口径不许搜）'
            : ((webRes[i] && webRes[i].ok) ? webBlockOf('W'+(i+1)+'-', (webRes[i].items)||[]) : '（这一门没搜到站外材料）');""")

# ⑨ 定三家提示词：闭库加一段硬纪律
rep("""    '**铁律：一个字都不许编。** 作者、年份、书名/篇名、结论、链接，只许用上面材料里真出现过的；""",
    """    INSIDE ? '**本次是闭库跑：三家必须全部来自站内材料（面板供料层与站内篇目）。**' : '',
    INSIDE ? '「来源」一栏一律写「站内」；**不许写任何站外出处、站外链接或你记忆里的站外文献**——' : '',
    INSIDE ? '哪怕你确知某位学者说过同样的话，只要它不在上面的材料里，本次就不许用它当三家之一。' : '',
    INSIDE ? '这不是材料不够，是这一跑的口径：**取源闭库**。它要检验的正是「只用站内的料能撞出什么」。' : '',
    INSIDE ? '' : '',
    '**铁律：一个字都不许编。** 作者、年份、书名/篇名、结论、链接，只许用上面材料里真出现过的；""")

# ⑩ 敌意拓宽那一格：闭库时把已知的结构性缺口写给它
rep("""    '【本站已发清单（方向五用）】',""",
    """    insideOnly() ? '**⚠ 本次是闭库跑（不联网）。** 五个方向仍要逐个走，但你只能在站内材料与你自己已有的知识里找。' : '',
    insideOnly() ? '**方向①经典层与方向④专著／外文这两格，闭库时最容易取不到**——取不到就如实写〔检索不足，未核验〕，' : '',
    insideOnly() ? '**不许写成「未找到」**。这两者差别很大：「未找到」是查过而没有，「检索不足」是没查成；把后者写成前者，等于替这篇文章伪造了一次清白。' : '',
    insideOnly() ? '' : '',
    '【本站已发清单（方向五用）】',""")

open(p, 'w', encoding='utf-8').write(s)
print('%d → %d 字节（+%d）' % (len(orig.encode()), len(s.encode()), len(s.encode())-len(orig.encode())))
