#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学科通融智能体两处改动（用户 2026-08-02 指令）：

① **无论是否到 150 都要自动保存**。此前存稿只发生在 deliver()，而 deliver 只在
   跑到最后一格且有正文时才被调用——评审判了不到 150 就转去回炉，稿子押在那个
   决定上；中途按停、某一格抛错，稿子也一并没了。改为：成文完、打磨完、评审读到
   分数、交付，四处各存一次，**与分数无关**；没选文件夹的也在浏览器本地留一份底，
   下次开页面能找回来。

② **是否回炉，由用户选**。此前只有一个「自动重跑」勾选框：勾上就自作主张回炉，
   不勾就只弹一行红字让人自己去点「重跑本格」——两头都不是"让他选"。改为在评审
   那一格当场给两个按钮（回炉重写／就这样交付），等他点；勾了自动的才不问。

用法：python3 tools/patch_conf_autosave_choice.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "tools", "confluence", "confluence.template.html")


def sub1(h, old, new, name):
    assert h.count(old) == 1, "锚点不唯一或找不到：%s（命中 %d）" % (name, h.count(old))
    return h.replace(old, new, 1)


HELPERS = r'''
/* ===================== 自动存稿（与分数无关） ===================== */
/* 稿子是他的，分数是评审的——两件事捆在一起过，是这台机器此前最容易丢东西的地方：
   评审一判不到 150 就转去回炉，那一稿从没被存过；中途按停、某一格抛错，同样没了。
   现在成文完一次、打磨完一次、评审读到分数一次、交付一次，四处各存一次。
   没选文件夹的，也在浏览器本地留一份底——落不了盘不等于可以丢。 */
const DRAFT_KEY = 'sde_conf_draft';
function draftTitle(){
  return (String(ST.article||'').split('\n')[0] || '学科通融').replace(/^#+\s*/,'').replace(/[\\/:*?"<>|]/g,'').slice(0,20);
}
function packMd(){
  const fm = ['---',
    'title: ' + draftTitle(),
    'author: 王德生 ＋ Claude',
    'question: ' + confQ().replace(/\s+/g,' '),
    'qtype: ' + (ST.qtype || '未判'),
    'fields: ' + (ST.discs||[]).join(' × '),
    'model: ' + modelSel.value,
    'iq_self: ' + (ST.score==null ? '未评' : ST.score),
    'polished: ' + (ST.polished ? '是' : '否'),
    'sources:'].concat(ST.sources.map(s=>'  - ' + (s.url || '(无链接)') + '　' + s.title))
    .concat(['---','']).join('\n');
  return [fm, ST.article, srcFooterMd(), '', '## 与既有说法的划界', '', ST.out.demarc||'',
          '', '## 打磨自查', '', ST.out.polishAudit||'（未跑打磨）'].join('\n');
}
async function autosave(tag){
  if(!ST.article || ST.article.replace(/\s/g,'').length < 300) return null;
  const words = ST.article.replace(/\s/g,'').length;
  const md = packMd();
  let where = '浏览器本地';
  try{
    localStorage.setItem(DRAFT_KEY, JSON.stringify({
      t: Date.now(), title: draftTitle(), tag: tag, score: ST.score, words: words, md: md }));
  }catch(e){ where = ''; }          // 存不进去（隐私模式／超额）就如实降级，别谎称存了
  const on = !$('autoSaveChk') || $('autoSaveChk').checked;
  const hasDir = window.WDSSaveDir && window.WDSSaveDir.supported() && window.WDSSaveDir.name();
  if(on && hasDir){
    try{
      await saveBlob('学科通融_' + draftTitle() + '_' + tag + '.md', new Blob([md], {type:'text/markdown'}));
      where = window.WDSSaveDir.name();
    }catch(e){ }
  }
  $('deliver').style.display = '';
  const el = $('draftNote');
  if(el) el.innerHTML = where
    ? ('✓ 已自动存稿（' + escTxt(tag) + ' · ' + words + ' 字 · 存到：' + escTxt(where) + '）。'
       + '<b>存稿与评分无关</b>——不到 150 也照存，回不回炉是另一件事。')
    : ('⚠ 这个浏览器不让本地留底（隐私模式或空间已满）。' + words + ' 字的稿子只在本页内存里——'
       + '选一个文件夹，或现在就点下面的按钮下载。');
  return where;
}
/* 开页面时把上次没带走的那份捞出来。不自动下载——那是他的文件，由他决定。 */
function draftRestore(){
  const bar = $('draftRestore'); if(!bar) return;
  let d = null;
  try{ d = JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null'); }catch(e){ return; }
  if(!d || !d.md) return;
  bar.style.display = '';
  const when = (()=>{ try{ return new Date(d.t).toLocaleString(); }catch(e){ return ''; } })();
  const head = document.createElement('span');
  head.className = 'small';
  head.style.cssText = 'flex:1 1 260px';
  head.innerHTML = '上一次还留着一份稿：<b>' + escTxt(d.title||'') + '</b>（' + (d.words||0) + ' 字'
    + (d.score != null ? ('　创新智商 ' + d.score) : '') + (d.tag ? ('　' + escTxt(d.tag)) : '')
    + (when ? ('　' + escTxt(when)) : '') + '）';
  const a = document.createElement('button'); a.className = 'btn ghost'; a.id = 'draftGet'; a.textContent = '下载它';
  a.addEventListener('click', ()=> saveBlob('学科通融_找回_' + (d.title||'稿') + '.md',
                                            new Blob([d.md], {type:'text/markdown'})));
  const b = document.createElement('button'); b.className = 'btn ghost'; b.id = 'draftDrop'; b.textContent = '丢掉';
  b.addEventListener('click', ()=>{ try{ localStorage.removeItem(DRAFT_KEY); }catch(e){ } bar.style.display='none'; });
  bar.innerHTML = '';
  bar.appendChild(head); bar.appendChild(a); bar.appendChild(b);
}

/* ===================== 当场问一句（回炉与否由他定） ===================== */
/* 此前只有一个「自动重跑」勾选框：勾上就自作主张回炉，不勾就丢一行红字让他自己
   去某一格点「重跑本格」——两头都不是"让他选"。现在把选择摆在那一格里等他点。 */
function askChoice(stageId, html, opts){
  return new Promise(resolve=>{
    const p = panels[stageId];
    if(!p){ resolve(opts[0] && opts[0].value); return; }
    const box = document.createElement('div');
    box.className = 'st-tools';
    box.id = 'choice-' + stageId;
    box.style.cssText = 'margin-top:12px;border-top:1px solid var(--border);padding-top:12px;flex-wrap:wrap';
    const q = document.createElement('div');
    q.className = 'small';
    q.style.cssText = 'flex:1 1 100%;margin-bottom:8px;color:var(--fg)';
    q.innerHTML = html;
    box.appendChild(q);
    let fin = false;
    const done = v => { if(fin) return; fin = true; ST.__choice = null; try{ box.remove(); }catch(e){ } resolve(v); };
    opts.forEach(o=>{
      const b = document.createElement('button');
      b.className = 'btn' + (o.primary ? '' : ' ghost');
      b.setAttribute('data-choice', o.value);
      b.textContent = o.label;
      b.addEventListener('click', ()=> done(o.value));
      box.appendChild(b);
    });
    p.out.parentNode.insertBefore(box, p.out.nextSibling);
    openStage(stageId);
    ST.__choice = ()=> done('stop');     // 按「停下」要能解开这个等待，否则整条产线卡死
    try{ box.scrollIntoView({behavior:'smooth', block:'center'}); }catch(e){ }
  });
}

'''


def main():
    h = open(TPL, encoding="utf-8").read()
    assert "function autosave(" not in h, "已经打过这个补丁了"

    # ---------- 1. DOM：找回条 ＋ 存稿提示 ----------
    h = sub1(h, '  <div id="errBox" class="errbox"></div>',
             '  <div id="errBox" class="errbox"></div>\n'
             '  <div id="draftRestore" class="st-tools" style="display:none;margin:0 0 14px;'
             'border:1px solid var(--border);border-radius:10px;padding:10px 14px"></div>',
             "找回条")
    h = sub1(h, '    <div id="doneBanner" class="small" style="margin-bottom:12px"></div>',
             '    <div id="doneBanner" class="small" style="margin-bottom:12px"></div>\n'
             '    <div id="draftNote" class="small" style="margin-bottom:12px;color:var(--ok)"></div>',
             "存稿提示")

    # ---------- 2. 两个勾选框的说明改准 ----------
    h = sub1(h,
             '<input type="checkbox" id="autoRedoChk" style="width:auto"> 发现问题就自动重跑'
             '（默认关：留了痕迹或不到 150 分时，停下来让你决定）',
             '<input type="checkbox" id="autoRedoChk" style="width:auto"> 不到 150 就自动回炉，别问我'
             '（默认关：<b>评审读到分数后当场给你两个按钮</b>——回炉重写，或就这样交付）',
             "autoRedoChk 说明")
    h = sub1(h,
             '<input type="checkbox" id="autoSaveChk" style="width:auto" checked> 跑完自动存盘'
             '（只在你选了文件夹时生效）',
             '<input type="checkbox" id="autoSaveChk" style="width:auto" checked> 自动存盘到你选的文件夹'
             '（成文 · 打磨 · 评审 · 交付各存一次）—— <b>与分数无关，不到 150 也照存</b>；'
             '没选文件夹时改在浏览器本地留底，下次开页面可找回',
             "autoSaveChk 说明")

    # ---------- 3. 注入函数 ----------
    h = sub1(h, "/* ===================== 学科通融：问题 · 题型 · 两路取材 ===================== */",
             HELPERS.lstrip("\n") + "/* ===================== 学科通融：问题 · 题型 · 两路取材 ===================== */",
             "注入 helpers")

    # ---------- 4. 成文与打磨末尾各存一次 ----------
    h = sub1(h, "  await nbrPostName();\n  $('deliver').style.display='';\n  return ST.article;\n}",
             "  await nbrPostName();\n  $('deliver').style.display='';\n"
             "  await autosave('成文');       // 存在这里，是因为后面每一步都可能不再回来\n"
             "  return ST.article;\n}", "doWrite 存稿")
    h = sub1(h, "  await nbrPostName();\n  $('deliver').style.display='';\n"
                "  ST.out.polish = '【逐条自查】\\n' + audit + '\\n\\n【已按自查整篇重写，终稿见成文格与交付区】';",
             "  await nbrPostName();\n  $('deliver').style.display='';\n"
             "  await autosave('打磨');\n"
             "  ST.out.polish = '【逐条自查】\\n' + audit + '\\n\\n【已按自查整篇重写，终稿见成文格与交付区】';",
             "doPolish 存稿")

    # ---------- 5. 评审：先存稿，再让他选回不回炉 ----------
    old_review = """    if(ST.score !== null && ST.score < 150){
      const autoRedo = $('autoRedoChk') && $('autoRedoChk').checked;
      const back = backStageFrom(txt);
      if(autoRedo && ST.rounds < 2){
        ST.rounds++;
        note('第 '+ST.rounds+' 轮回炉：'+ST.score+' 分，从「'+STAGES[back].n+'」重跑。');
        showErr('创新智商 '+ST.score+'，不到 150——自动回炉：从「'+STAGES[back].n+'」重跑（第 '+ST.rounds+'/2 轮）。');
        ST.redoFrom = back;
      } else if(!autoRedo){
        // 默认：不自动回炉，停下来让用户决定
        showErr('创新智商 '+ST.score+'，不到 150。评审建议从「'+STAGES[back].n+'」回炉——要回炉就到那一格点「重跑本格」、再点「从这里继续往下」；也可以就用这版交付。由你决定。');
      } else {
        showErr('创新智商 '+ST.score+'，回炉两轮仍不到 150。要么手动从某一格重跑，要么就用这版——由你决定。');
      }
    }"""
    new_review = """    // 无论多少分，先把这一稿存下来：回炉与否是后面的事，稿子不该押在这个决定上
    await autosave('评审 ' + (ST.score==null ? '未读到分数' : ST.score + ' 分'));
    if(ST.score !== null && ST.score < 150){
      const autoRedo = $('autoRedoChk') && $('autoRedoChk').checked;
      const back = backStageFrom(txt);
      if(autoRedo && ST.rounds < 2){
        ST.rounds++;
        note('第 '+ST.rounds+' 轮回炉：'+ST.score+' 分，从「'+STAGES[back].n+'」重跑。');
        showErr('创新智商 '+ST.score+'，不到 150——按你勾的「自动回炉」：从「'+STAGES[back].n+'」重跑（第 '+ST.rounds+'/2 轮）。这一稿已经存下来了。');
        ST.redoFrom = back;
      } else {
        const many = ST.rounds >= 2;
        const pick = await askChoice('review',
          '创新智商 <b>'+ST.score+'</b>，不到 150。评审建议从「<b>'+STAGES[back].n+'</b>」回炉'
          + (many ? ('（已经回过 '+ST.rounds+' 轮了）') : '')
          + '。<b>这一稿已经自动存下来了</b>，回不回炉由你定：',
          [{label:'回炉重写（从「'+STAGES[back].n+'」）', value:'redo', primary:true},
           {label:'就这样交付', value:'keep'}]);
        if(pick === 'redo'){
          ST.rounds++;
          note('第 '+ST.rounds+' 轮回炉（你选的）：从「'+STAGES[back].n+'」重跑。');
          setStat('review', '回炉中：从「'+STAGES[back].n+'」重跑…', 'run');
          ST.redoFrom = back;
        } else if(pick === 'stop'){
          ST.abort = true;
          note('在评审那一格停下了；'+ST.score+' 分的这一稿已存。');
        } else {
          note('你选了就这样交付（'+ST.score+' 分，未回炉）。');
          setStat('review', '✓ 创新智商 '+ST.score+' · 你选了就这样交付', 'done');
        }
      }
    }"""
    h = sub1(h, old_review, new_review, "评审回炉选择")

    # ---------- 6. 「停下」要能解开等待 ----------
    h = sub1(h, "$('stopBtn').addEventListener('click', ()=>{ ST.abort = true; });",
             "$('stopBtn').addEventListener('click', ()=>{\n"
             "  ST.abort = true;\n"
             "  if(ST.__choice) ST.__choice();   // 正卡在「回不回炉」那两个按钮上时，停下也要能解开\n"
             "});", "停下解等待")

    # ---------- 7. deliver：存稿改成无条件 ----------
    h = sub1(h,
             "  const auto = $('autoSaveChk') && $('autoSaveChk').checked;\n"
             "  const hasDir = window.WDSSaveDir && window.WDSSaveDir.supported() && window.WDSSaveDir.name();\n"
             "  if(auto && hasDir){\n"
             "    try{ $('dlDocx').click(); $('dlPack').click(); $('dlEngine').click(); }catch(e){ }\n"
             "  }",
             "  await autosave('终稿');        // 与分数无关：过没过 150 都存\n"
             "  const auto = $('autoSaveChk') && $('autoSaveChk').checked;\n"
             "  const hasDir = window.WDSSaveDir && window.WDSSaveDir.supported() && window.WDSSaveDir.name();\n"
             "  if(auto && hasDir){\n"
             "    try{ $('dlDocx').click(); $('dlEngine').click(); }catch(e){ }   // .md 已由 autosave 落盘，别重复\n"
             "  }", "deliver 存稿")

    # ---------- 8. 清空：清面板不清底稿；找回条重新挂 ----------
    h = sub1(h, "  $('deliver').style.display='none';\n  hideErr();\n});",
             "  $('deliver').style.display='none';\n"
             "  const dn = $('draftNote'); if(dn) dn.innerHTML='';\n"
             "  const cb = $('choice-review'); if(cb) cb.remove();\n"
             "  ST.__choice = null;\n"
             "  draftRestore();     // 底稿故意不清：清空重来清的是这一场，不是他上一场的成果\n"
             "  hideErr();\n});", "清空复位")

    # ---------- 9. 起页面时挂找回条 ----------
    h = sub1(h, "loadData();\n</script>", "loadData();\ndraftRestore();\n</script>", "起页面")

    for needle in ["function autosave(", "function askChoice(", "function draftRestore(",
                   "await autosave('成文')", "await autosave('打磨')", "await autosave('终稿')",
                   "data-choice", "id=\"draftRestore\"", "id=\"draftNote\""]:
        assert needle in h, "补丁后缺了：" + needle
    for tag in ["div", "script", "style", "select", "textarea"]:
        o = len(re.findall(r"<%s[\s>]" % tag, h))
        c = len(re.findall(r"</%s>" % tag, h))
        assert o == c, "标签不配对：%s 开 %d 闭 %d" % (tag, o, c)

    open(TPL, "w", encoding="utf-8").write(h)
    print("补好了：四处自动存稿（与分数无关）＋ 评审当场给两个按钮让他选回不回炉")
    return 0


if __name__ == "__main__":
    sys.exit(main())
