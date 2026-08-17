#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把搜索页（涌现档）的候选卡逻辑改为委托共用模块 sde-cand.js。

为什么动这一页：这条缝现在有第二个出口（ChatSDE 的每一答与成文）。
身份取用、切节、三段硬门、库未命中的口径，抄第二遍就会漂——而这类漂移是静默的。
所以逻辑只留一份在模块里，页面只留薄壳。**页面上读者看到的话术与行为一字不改。**

幂等；所有替换先 assert 锚点；写回一律先 encode 再 wb。
"""
import sys, io, os

P = os.path.join(os.path.dirname(__file__), "..", "public", "search", "index.html")
h = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new, label):
    global h, n
    assert old in h, "锚点没找到：" + label
    assert h.count(old) == 1, "锚点不唯一：" + label
    h = h.replace(old, new, 1)
    n += 1

if "sde-cand.js" in h:
    print("已经打过这个补丁，跳过。")
    sys.exit(0)

# 1. 引模块（挨着近邻库那一行，两者是一套）
rep(
    '  <script src="/assets/sde-nbr.js"></script>\n',
    '  <script src="/assets/sde-nbr.js"></script>\n'
    '  <script src="/taste/assets/sde-cand.js?v=20260817c"></script>\n',
    "引模块",
)

# 2. 身份与切节改成薄壳
rep(
    'function cdCred(){\n'
    '  try{\n'
    '    var c=sessionStorage.getItem("sde_gauth");\n'
    '    if(c)return c;\n'
    '    var raw=localStorage.getItem("sde_talk_id");\n'
    '    if(raw){var o=JSON.parse(raw); if(o&&o.cred&&(!o.exp||o.exp>Date.now()))return o.cred;}\n'
    '  }catch(e){}\n'
    '  return "";\n'
    '}\n'
    '/* 典范骨架八节 → 候选卡三段。取不到就退回整段文本的前若干字，**绝不编造**。 */\n'
    'function cdSection(txt,names){\n'
    '  for(var i=0;i<names.length;i++){\n'
    '    var re=new RegExp(names[i]+"[：:]?\\\\s*([\\\\s\\\\S]*?)(?=\\\\n\\\\s*[一二三四五六七八九十]{1,3}[、．.]|$)");\n'
    '    var m=String(txt||"").match(re);\n'
    '    if(m&&m[1]&&m[1].trim().length>3)return m[1].trim().replace(/\\s+/g," ");\n'
    '  }\n'
    '  return "";\n'
    '}\n',
    '/* 身份取用与「典范骨架八节 → 候选卡三段」的切节都搬进了全站共用模块\n'
    '   /taste/assets/sde-cand.js——这条缝现在有第二个出口（ChatSDE 的每一答与成文），\n'
    '   同一套纪律抄两遍必漂，而这类漂移是静默的：卡照样落，只是某一关不再把关。\n'
    '   这里只留薄壳，**读者看到的话术与行为一字未改**。 */\nfunction cdCred(){ return (window.SDECand && window.SDECand.cred()) || ""; }\n'
    'function cdSection(txt,names){ return (window.SDECand && window.SDECand.section(txt,names)) || ""; }\n',
    "薄壳化",
)

# 3. 落卡改走模块（查占位库＋三段硬门＋未登录去处都在模块里）
OLD_TC = h[h.index("function toCandidate(ix){"):h.index("function renderParadigms(sel){")]
assert "window.SDENbr" in OLD_TC and "op:\"cd\"" in OLD_TC, "toCandidate 变样了，先看一眼再改"
NEW_TC = '''function toCandidate(ix){
  var p=paradigms[ix]; if(!p)return;
  var msg=document.getElementById("cdmsg"+ix);
  if(!window.SDECand){ msg.textContent="sde-cand.js 没装载上，刷新一次再试。"; return; }
  /* 解析归页面（骨架节名是这一页的事），落卡与闸门归模块。
     三段缺任一段都拒绝落卡，并**各给各的理由**——取不到就说取不到，绝不编造。 */
  var prop=cdSection(p.text,["二、承重命题","承重命题"]);
  var face=cdSection(p.text,["三、它切开的辨别面","它切开的辨别面","辨别面"]);
  var crit=cdSection(p.text,["五、可裁决判据","可裁决判据","六、可裁决判据"]);
  if(!prop){ msg.textContent="这张典范里没解析出「承重命题」，先手动去微信立卡。"; return; }
  if(!face){ msg.textContent="没解析出「它切开的辨别面」——候选卡缺这一段就没法被顶回，先手动立卡。"; return; }
  if(!crit){ msg.textContent="没解析出「可裁决判据」——没有判据别人只能表态，先手动立卡。"; return; }
  msg.textContent="正在查占位库、落卡…";
  window.SDECand.post({prop:prop,face:face,crit:crit,src:"涌现档 · "+wayName(p.way)}).then(function(r){
    if(!r||!r.ok){ msg.innerHTML=(r&&r.msg)||"落卡失败。"; return; }
    msg.innerHTML='已立卡 · 72 小时顶回期开始 → <a href="/sde-wechat/" target="_blank">去「🎯 候选」看</a>';
  });
}
'''
rep(OLD_TC, NEW_TC, "落卡走模块")

io.open(P, "wb").write(h.encode("utf-8"))
print("已改 %d 处 → %s" % (n, os.path.relpath(P)))
