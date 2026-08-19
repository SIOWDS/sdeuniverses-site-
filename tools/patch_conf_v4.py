# -*- coding: utf-8 -*-
import re
P = '/home/claude/site/public/taste/confluence/index.html'
s = open(P, encoding='utf-8').read()
orig = s


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, new)


# ══════════ ① 三格文本框 → 两种取源方式 ＋ 三个面板下拉 ══════════
rep("""<div class="row" style="margin-top:6px">
      <div style="flex:1;min-width:170px"><label class="lbl">学科一</label><input type="text" id="cD1" placeholder="例：制度经济学"></div>
      <div style="flex:1;min-width:170px"><label class="lbl">学科二</label><input type="text" id="cD2" placeholder="例：认知心理学"></div>
      <div style="flex:1;min-width:170px"><label class="lbl">学科三</label><input type="text" id="cD3" placeholder="例：生态学"></div>
    </div>""",
"""<div class="row" style="margin-top:6px;align-items:center">
      <div style="min-width:300px">
        <label class="lbl">三个学科怎么来</label>
        <select id="cPickMode">
          <option value="auto" selected>基底自由组合（它按这道题自己挑三门，可跨站外）</option>
          <option value="panel">我自己组合（从站内 600 多块面板里选三门）</option>
        </select>
      </div>
      <span class="small" style="flex:1;min-width:260px;color:var(--muted)">自己组合的好处是材料厚（每块都带真出处与八字段供料层）；坏处是<b>可能撞不起来</b>——三门站在同一个位置上就撞不出东西。<b>撞不起来会自动转成基底自由组合，不会停在那儿。</b></span>
    </div>
    <div class="row" id="panelPick" style="margin-top:6px;display:none">
      <div style="flex:1;min-width:200px"><label class="lbl">面板一</label><select id="cP1"><option value="">载入中…</option></select></div>
      <div style="flex:1;min-width:200px"><label class="lbl">面板二</label><select id="cP2"><option value="">载入中…</option></select></div>
      <div style="flex:1;min-width:200px"><label class="lbl">面板三</label><select id="cP3"><option value="">载入中…</option></select></div>
    </div>
    <div class="row" id="freePick" style="margin-top:6px">
      <div style="flex:1;min-width:170px"><label class="lbl">学科一（可留空）</label><input type="text" id="cD1" placeholder="例：制度经济学"></div>
      <div style="flex:1;min-width:170px"><label class="lbl">学科二（可留空）</label><input type="text" id="cD2" placeholder="例：认知心理学"></div>
      <div style="flex:1;min-width:170px"><label class="lbl">学科三（可留空）</label><input type="text" id="cD3" placeholder="例：生态学"></div>
    </div>""")

# ══════════ ② 面板下拉的装填与切换 ══════════
rep("""/* ===================== 面板 ===================== */""",
"""/* ============ 学员自己组合：三个面板下拉 ============
   两种取源方式并存的理由：自己组合材料最厚（每块带真出处与八字段供料层），
   但三门有可能站在同一个位置上——那种情况撞不出东西，而这不是学员的错，
   所以撞不起来时自动转基底自由组合，不把人卡在那儿。 */
let PANEL_OPTS = null;
async function fillPanelSelects(){
  const cat = await frontierCat();
  const boxes = ['cP1','cP2','cP3'].map(id=>$(id)).filter(Boolean);
  if(!boxes.length) return;
  if(!cat.length){
    boxes.forEach(b=> b.innerHTML = '<option value="">（面板目录取不到，改用基底自由组合）</option>');
    return;
  }
  PANEL_OPTS = cat.slice().sort((a,b)=>a.n-b.n);
  const html = '<option value="">— 请选 —</option>' +
    PANEL_OPTS.map(x=>'<option value="'+x.n+'">'+String(x.n).padStart(3,'0')+'　'+escTxt(x.name)+'</option>').join('');
  boxes.forEach(b=>{ b.innerHTML = html; });
}
function pickMode(){ const e=$('cPickMode'); return e ? e.value : 'auto'; }
function panelChosen(){
  if(pickMode()!=='panel' || !PANEL_OPTS) return [];
  return ['cP1','cP2','cP3'].map(id=>{
    const v = $(id) && $(id).value; if(!v) return null;
    return PANEL_OPTS.find(x=>x.n===parseInt(v,10)) || null;
  }).filter(Boolean);
}
function syncPickMode(){
  const panel = pickMode()==='panel';
  if($('panelPick')) $('panelPick').style.display = panel ? '' : 'none';
  if($('freePick'))  $('freePick').style.display  = panel ? 'none' : '';
  if(panel && !PANEL_OPTS) fillPanelSelects();
}

/* ===================== 面板 ===================== */""")

# 接线（放在已有的初始化里）
rep("""function renderMode(){""",
"""(function wirePickMode(){
  const e = document.getElementById('cPickMode');
  if(e){ e.addEventListener('change', syncPickMode); syncPickMode(); }
})();
function renderMode(){""")

# ══════════ ③ 选源：学员选定的三块直接用，跳过"定学科"那一次调用 ══════════
rep("""  const CAT = usePanel ? await frontierCat() : [];""",
"""  const CAT = (usePanel || pickMode()==='panel') ? await frontierCat() : [];
  const CHOSEN = ST.forceAuto ? [] : panelChosen();   // ST.forceAuto：上一轮撞不起来，已降级""")

rep("""  const dr = await askFast(sdeSystem(), dp, p.out, p.stat, p.meta, 900, '定学科');""",
"""  let dr;
  if(CHOSEN.length === 3){
    /* 学员已经把三门定死了——这一步不必再问基底，省一次调用，也省得它改名。 */
    selLog('学员自选三块面板：<b>' + CHOSEN.map(x=>'第'+x.n+'号《'+escTxt(x.name)+'》').join('　×　') + '</b>');
    dr = { text: CHOSEN.map((x,i)=>(i+1)+'｜'+x.n+'｜'+x.name+'｜'+x.name+' 理论 争论').join('\\n') };
  } else {
    dr = await askFast(sdeSystem(), dp, p.out, p.stat, p.meta, 900, '定学科');
  }""")

# ══════════ ④ 体检不过 → 自动降级为自由组合，重跑选源 ══════════
rep("""      showErr('闸一只给了 '+sc+'/10——三个源多半是互补不是打架。可以照旧往下跑，但成品破 150 的机会不大，建议换一位学员或改手挑。');""",
"""      /* 学员自己组合时，撞不起来不是他的错——自动降级为基底自由组合重挑一次，
         只降一次（ST.forceAuto 是一次性的），避免来回打转。 */
      if(pickMode()==='panel' && !ST.forceAuto && panelChosen().length===3){
        ST.forceAuto = true;
        note('你选的三块面板撞不起来（闸一 '+sc+'/10，多半是三门站在同一个位置上）——已自动转为「基底自由组合」，重新挑三家。这不是你的错，位置撞车靠换学科是换不掉的。');
        setStat('select','<span class=\\"spinner\\"></span> 撞不起来，改由基底自由组合重挑','run');
        await doSelectConf();
        return await runStage(i);
      }
      showErr('闸一只给了 '+sc+'/10——三个源多半是互补不是打架。可以照旧往下跑，但成品分数不会高，建议换三门离得更远的。');""")

# ══════════ ⑤ 阈值 150 → 140，且一律不回炉 ══════════
rep("""{id:'review',  n:'评审',     hint:'创新智商 · 不到 150 点名回炉',      tok:4000}""",
    """{id:'review',  n:'评审',     hint:'创新智商 · 只报分数，不回炉',        tok:4000}""")

rep("""    '若总分 < 150：必须点名回炉到哪一道工序（体检／抽脊／混沌碰撞／扩候选／候选互撞／自组织／涌现／近邻划界／成文），并给一句具体动作。',
    '再给三条"最该补的一刀"。',""",
    """    '**不必点名回炉**——本机不回炉，分数只作读数用。',
    '再给三条"最该补的一刀"（供作者自己判断要不要改，不构成退回）。',""")

rep("""    <input type="checkbox" id="autoRedoChk" style="width:auto"> 不到 150 就自动回炉，别问我（默认关：<b>评审读到分数后当场给你两个按钮</b>——回炉重写，或就这样交付）""",
    """    <input type="checkbox" id="autoRedoChk" style="width:auto" disabled> <s>不到线自动回炉</s>（<b>本机已关掉回炉</b>：评审只报分数，达不达标都照常交付，稿子归你判断）""")

rep("""<b>与分数无关，不到 150 也照存</b>""", """<b>与分数无关，不到 140 也照存</b>""")

# 评审后的回炉分支整段停用
rep("""if(ST.score !== null && ST.score < 150){""",
    """if(false && ST.score !== null && ST.score < 140){""")

# 分数展示
rep("""  const bad = ST.score < 150;
  setStat('review', (bad?'⚠ ':'✓ ')+'创新智商 '+ST.score, bad? 'run':'done');""",
    """  const bad = ST.score < 140;
  setStat('review', (bad?'· ':'✓ ')+'创新智商 '+ST.score, 'done');""")

rep("""  note.innerHTML = bad
    ? '不到 150。评审已点名回炉工序——回到那一格点「重跑本格」，再点「从这里继续往下」。'
    : '过线。可以进交付了。';""",
    """  note.innerHTML = bad
    ? '低于 140。<b>本机不回炉</b>——这一稿照常交付，改不改由你定；评审给的三条「最该补的一刀」在上面。'
    : '到 140 线。可以进交付了。';""")

rep("""ST.score==null ? '评审未读到分数' : ('创新智商 '+ST.score+(ST.score>=150?'（过线）':'（未过线，已回炉 '+ST.rounds+' 轮）')),""",
    """ST.score==null ? '评审未读到分数' : ('创新智商 '+ST.score+(ST.score>=140?'（到 140 线）':'（未到 140 线，按口径照常交付）')),""")

rep("""await autosave('终稿');        // 与分数无关：过没过 150 都存""",
    """await autosave('终稿');        // 与分数无关：到没到 140 都存""")

# ST 里加 forceAuto
rep("""const ST = { mode:'X', sources:[], out:{},""", """const ST = { mode:'X', forceAuto:false, sources:[], out:{},""")

open(P, 'w', encoding='utf-8').write(s)
print('%d → %d 字节（+%d）' % (len(orig.encode()), len(s.encode()), len(s.encode())-len(orig.encode())))
