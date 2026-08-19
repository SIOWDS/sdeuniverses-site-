#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学科通融智能体：取材那一步卡死的修复（2026-08-02 真跑时卡了十几分钟才发现）。

**病灶三条，缺一条都还会卡：**
① 侧路取材（联网检索 / 站内近邻 / 站内语料）**一个超时都没有**——任何一路不回，
   整条产线就静默停在那儿，面板上只有一个转圈，看不出是哪一路。
② 定三家那一步把 **3 路近邻 ＋ 1 路语料同时发出去**。这两个端点每次都要把全站语料
   读一遍（实测单发 6.5s / 4.3s），四个并发是拿自己的后端打自己。
③ 「停下」只在两格之间被检查，**掐不断已经发出去的请求**——卡住时那个按钮是假的。

**处置：** 所有侧路走同一个带闸的 sideFetch（可超时、可中断、失败即空）；站内那一路
改成串行；状态条实时报「联网 n/3　站内 n/3」，哪一路慢一眼看得出；「停下」当场中断
所有在飞的请求。工具设计上的道理与正文那篇一样——**止损靠的是给它一个边界，不是
把它做得更快**。

用法：python3 tools/patch_conf_gather_timeout.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "tools", "confluence", "confluence.template.html")


def sub1(h, old, new, name):
    assert h.count(old) == 1, "锚点不唯一或找不到：%s（命中 %d）" % (name, h.count(old))
    return h.replace(old, new, 1)


SIDE = r'''/* ===================== 侧路取材：一律带闸 ===================== */
/* 2026-08-02 真跑时在「定三家」的取材那一步卡了十几分钟：三路站内近邻＋一路语料同时
   发出去，这两个端点每次都要把全站语料读一遍；而这些调用一个超时都没有，卡住就是
   无限期卡住，面板上只剩一个转圈，连「停下」都掐不断（abort 只在两格之间被检查）。
   处置：统一走这里——可超时、可中断、失败即空串。**止损靠的是给它一个边界。** */
const SIDE_LIVE = [];                 // 在飞的请求，按「停下」时一并掐掉
let SIDE_SLOW = 0;                    // 本轮有几路是被闸掉的（要如实告诉用户，别假装取到了）
function sideAbortAll(){
  while(SIDE_LIVE.length){ const ac = SIDE_LIVE.pop(); try{ ac.abort(); }catch(e){ } }
}
function sideFetch(url, body, ms){
  let ac = null, t = null;
  try{ ac = new AbortController(); }catch(e){ ac = null; }
  if(ac){
    SIDE_LIVE.push(ac);
    t = setTimeout(()=>{ SIDE_SLOW++; try{ ac.abort(); }catch(e){ } }, ms || 30000);
  }
  const done = ()=>{
    if(t) clearTimeout(t);
    const i = ac ? SIDE_LIVE.indexOf(ac) : -1;
    if(i >= 0) SIDE_LIVE.splice(i, 1);
  };
  return fetch(url, { method:'POST', headers:{'content-type':'application/json'},
                      body: JSON.stringify(body), signal: ac ? ac.signal : undefined })
    .then(r => r.ok ? r.json() : null)
    .then(j => { done(); return j; })
    .catch(()  => { done(); return null; });
}
'''

NEW_KBCTX = r'''async function kbCtx(q){
  // 契约与金点子发生器一致：/api/kb/retrieve 返回 {block}。无 Key、只读、失败或超时即空串。
  const j = await sideFetch('/api/kb/retrieve', { q:q, k:12, budget:24, cap:9000 }, 45000);
  return (j && j.block) ? j.block : '';
}'''

NEW_NBRONE = r'''async function nbrOne(q, k){
  // 直接走端点，不经 SDERag —— 那一层没有超时，而这一路正是会卡住的那一路。
  // 端点自己就返回 block（worker 侧 nbBlock），所以没有损失。
  const j = await sideFetch('/api/kb/neighbors', { q:String(q||'').slice(0,2000), k:k||8 }, 45000);
  return (j && j.block) ? j.block : '';
}'''

NEW_WEBSEARCH = r'''async function webSearch(q, skey){
  const j = await sideFetch('/api/wds/websearch',
                            { q:String(q||'').slice(0,70), skey:skey||'', n:8 }, 30000);
  if(!j) return { ok:false, reason:'timeout', items:[] };
  return j;
}'''

OLD_GATHER = """  /* 二、两路取材并发 */
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
"""

NEW_GATHER = """  /* 二、两路取材：联网并发（轻），站内串行（重）。每一路都报进度，卡住时一眼看得出是哪一路。 */
  SIDE_SLOW = 0;
  const prog = { web:0, kb:0, ctx:0 };
  const paint = ()=> setStat(id, '<span class="spinner"></span> 取材：联网 ' + prog.web + '/' + rows.length
    + (useKB ? ('　站内近邻 ' + prog.kb + '/' + rows.length + (prog.ctx ? '　站内语料 ✓' : '　站内语料 …'))
             : '　（站内库这一路你关掉了）'), 'run');
  paint();
  let webRes = [], kbRes = ['','',''], kbCtxBlock = '';
  webRes = await Promise.all(rows.map(r =>
    webSearch(r.q, skey).then(x => { prog.web++; paint(); return x; })));
  if(useKB){
    // **串行**：这一路每查一次都要把全站语料读一遍，三路并发是拿自己的后端打自己——
    // 那正是 2026-08-02 卡住十几分钟的来路。
    kbRes = [];
    for(const r of rows){
      if(ST.abort) break;
      kbRes.push(await nbrList([q.slice(0,300) + ' ' + r.disc], 6));
      prog.kb++; paint();
    }
    while(kbRes.length < rows.length) kbRes.push('');
    if(!ST.abort){ kbCtxBlock = await kbCtx(q.slice(0,600)); prog.ctx = 1; paint(); }
  }
  if(ST.abort) throw new Error('已停下');
  if(SIDE_SLOW) note('取材有 ' + SIDE_SLOW + ' 路超时被掐掉了（按空处理，不假装取到）。');
"""


def main():
    h = open(TPL, encoding="utf-8").read()
    assert "function sideFetch(" not in h, "已经打过这个补丁了"

    # ① 注入带闸的 sideFetch（放在 kbCtx 之前）
    h = sub1(h, "async function kbCtx(q){", SIDE + "async function kbCtx(q){", "注入 sideFetch")

    # ② 三个侧路改走它
    old_kbctx = """async function kbCtx(q){
  // 契约与金点子发生器一致：/api/kb/retrieve 返回 {block}。无 Key、只读、失败即空串（安全退回）。
  try{
    const r = await fetch('/api/kb/retrieve', { method:'POST', headers:{'content-type':'application/json'},
      body: JSON.stringify({ q:q, k:12, budget:24, cap:9000 }) });
    if(!r.ok) return '';
    const j = await r.json();
    return (j && j.block) ? j.block : '';
  }catch(e){ return ''; }
}"""
    h = sub1(h, old_kbctx, NEW_KBCTX, "kbCtx 带闸")

    old_nbrone = """async function nbrOne(q, k){
  try{
    if(window.SDERag && window.SDERag.neighbors) return (await window.SDERag.neighbors(q, {k:k||8})) || '';
    const r = await fetch('/api/kb/neighbors', { method:'POST', headers:{'content-type':'application/json'},
      body: JSON.stringify({ q:String(q||'').slice(0,2000), k:k||8 }) });
    if(!r.ok) return '';
    const j = await r.json();
    return (j && j.block) ? j.block : '';
  }catch(e){ return ''; }
}"""
    h = sub1(h, old_nbrone, NEW_NBRONE, "nbrOne 带闸")

    old_ws = """async function webSearch(q, skey){
  try{
    const r = await fetch('/api/wds/websearch', { method:'POST', headers:{'content-type':'application/json'},
      body: JSON.stringify({ q:String(q||'').slice(0,70), skey:skey||'', n:8 }) });
    if(!r.ok) return { ok:false, reason:'http_'+r.status, items:[] };
    return await r.json();
  }catch(e){ return { ok:false, reason:'net', items:[] }; }
}"""
    h = sub1(h, old_ws, NEW_WEBSEARCH, "webSearch 带闸")

    # ③ 取材：串行 + 实时进度
    h = sub1(h, OLD_GATHER, NEW_GATHER, "取材串行与进度")

    # ④ 站内抓全文也要带闸（同一个洞：一篇抓不动就卡住整格）
    h = sub1(h, "async function pullText(url){\n  const r = await fetch(url, {cache:'no-cache'});",
             "async function pullText(url){\n"
             "  let ac = null, t = null;\n"
             "  try{ ac = new AbortController(); SIDE_LIVE.push(ac);\n"
             "       t = setTimeout(()=>{ SIDE_SLOW++; try{ ac.abort(); }catch(e){} }, 30000); }catch(e){ ac = null; }\n"
             "  const r = await fetch(url, {cache:'no-cache', signal: ac ? ac.signal : undefined})\n"
             "    .finally(()=>{ if(t) clearTimeout(t); const i = ac ? SIDE_LIVE.indexOf(ac) : -1; if(i>=0) SIDE_LIVE.splice(i,1); });",
             "pullText 带闸")

    # ⑤ 「停下」当场掐断在飞的请求（此前只在两格之间被检查，卡住时那个按钮是假的）
    h = sub1(h, "  ST.abort = true;\n  if(ST.__choice) ST.__choice();",
             "  ST.abort = true;\n"
             "  sideAbortAll();                  // 掐断在飞的取材请求——否则卡住时这个按钮是假的\n"
             "  if(ST.__choice) ST.__choice();", "停下掐断")

    # ⑥ 清空重来也把在飞的掐掉
    h = sub1(h, "  ST.out = {}; ST.article=''; ST.outline=''; ST.score=null; ST.sources=[];",
             "  sideAbortAll();\n"
             "  ST.out = {}; ST.article=''; ST.outline=''; ST.score=null; ST.sources=[];", "清空掐断")

    # ⑦ 页面上把这件事说清楚
    h = sub1(h, '⚠ 联网搜来的材料只有摘要级，<b>发表前务必自己点开每个链接核对</b>。',
             '⚠ 联网搜来的材料只有摘要级，<b>发表前务必自己点开每个链接核对</b>。'
             '取材那一步每一路都有 30–45 秒的闸，超时按空处理并如实标出，不会无限期转圈；'
             '站内那一路是<b>串行</b>跑的（每查一次都要把全站语料读一遍），三门大约 20–60 秒。',
             "页面说明")

    for needle in ["function sideFetch(", "sideAbortAll()", "站内近邻 ' + prog.kb",
                   "reason:'timeout'", "SIDE_SLOW"]:
        assert needle in h, "补丁后缺了：" + needle
    assert "window.SDERag && window.SDERag.neighbors" not in h, "nbrOne 里还留着没有超时的那条路"
    for tag in ["div", "script", "style", "select", "textarea"]:
        o = len(re.findall(r"<%s[\s>]" % tag, h))
        c = len(re.findall(r"</%s>" % tag, h))
        assert o == c, "标签不配对：%s 开 %d 闭 %d" % (tag, o, c)

    open(TPL, "w", encoding="utf-8").write(h)
    print("补好了：侧路全部带闸（30–45s）· 站内改串行 · 实时进度 · 停下当场掐断")
    return 0


if __name__ == "__main__":
    sys.exit(main())
