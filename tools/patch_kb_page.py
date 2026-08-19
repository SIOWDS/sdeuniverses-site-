#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""社区页的知识库那一半（v-kb）。幂等可复跑。

  · show() 的白名单**四处一次改齐**（视图切换 / 返回键 / 标题 / 返回目标）——
    文章库那次就是靠这条规矩落地的，漏一处就会出现"进得去出不来"。
  · API 走 `kbApi(a, extra).then(unwrap)`：**信封只拆一次**。
    （候选/库存/文章库三个 tab 全部"加载失败"那次，根因就是拆了两次形状对不上。）
  · 页面上不出现任何可排序成等级的数字——这条对私人库同样成立。
"""
import io

P = "public/sde-wechat/index.html"
h = io.open(P, encoding="utf-8").read()
orig = h
done = []


def rep(old, new, tag, probe, cnt=1):
    global h
    if probe in h:
        print("  · %s 已在，跳过" % tag); return
    assert old in h, "锚点找不到：" + tag
    assert h.count(old) == cnt, "锚点不唯一（%d 处）：%s" % (h.count(old), tag)
    h = h.replace(old, new, 1); done.append(tag); print("  ✔ %s" % tag)


# ── 1. 视图容器 ───────────────────────────────────────────────
rep(
    '''    <div class="view" id="v-vault">''',
    '''    <div class="view" id="v-kb">
      <div class="scroll" id="kb-body"></div>
    </div>
    <div class="view" id="v-vault">''',
    "① 视图容器 v-kb", 'id="v-kb"',
)

# ── 2. show() 白名单四处 ─────────────────────────────────────
rep(
    '''"cdnews","vault","lib"].forEach''',
    '''"cdnews","vault","lib","kb"].forEach''',
    "② 白名单·视图切换", '"lib","kb"].forEach',
)
rep(
    '''||v==="vault"||v==="lib"||v==="who"''',
    '''||v==="vault"||v==="lib"||v==="kb"||v==="who"''',
    "③ 白名单·返回键", '||v==="lib"||v==="kb"||v==="who"',
)
rep(
    '''   else if(v==="lib")el("t-ttl").textContent="📚 文章库";''',
    '''   else if(v==="lib")el("t-ttl").textContent="📚 文章库";   else if(v==="kb")el("t-ttl").textContent="📦 我的知识库";''',
    "④ 白名单·标题", 'else if(v==="kb")el("t-ttl").textContent',
)
rep(
    '''  if(el("v-lib").classList.contains("on")){show(lbFrom||"me");return;}''',
    '''  if(el("v-kb").classList.contains("on")){if(kbOpen){kbOpen=null;kbLoad();return;}show("me");return;}
  if(el("v-lib").classList.contains("on")){show(lbFrom||"me");return;}''',
    "⑤ 白名单·返回目标（打开某一件时先退回列表）", 'if(el("v-kb").classList.contains("on"))',
)

# ── 3. 「我」页入口 ───────────────────────────────────────────
rep(
    '''            <div class="me-item"><span>📚 文章库''',
    '''            <div class="me-item"><span>📦 我的知识库<br><span style="font-size:0.74rem;color:var(--muted)">画布上锻出来的稿子存在这儿——只有你看得见，换台机器也还在</span></span><button id="b-kb">进入</button></div>
            <div class="me-item"><span>📚 文章库''',
    "⑥ 「我」页入口", 'id="b-kb"',
)
rep(
    '''  var b=el("b-lib");if(b)b.onclick=function(){lbMode="pub";lbGo("me",null);};''',
    '''  var bk=el("b-kb");if(bk)bk.onclick=function(){kbOpen=null;show("kb");kbLoad();};
  var b=el("b-lib");if(b)b.onclick=function(){lbMode="pub";lbGo("me",null);};''',
    "⑦ 「我」页入口接线", 'var bk=el("b-kb")',
)

# ── 4. 逻辑 ───────────────────────────────────────────────────
rep(
    '''function lbApi(a,extra){return api("lb",Object.assign({a:a},extra||{})).then(unwrap);}''',
    '''/* ══ 个人知识库 ══════════════════════════════════════════
   装的是**本人产出的成品文档**（画布上那些）。与另外两个库分工别混：
     💡 思想库存＝一句话（200 字上限，全站共用一池）
     📚 文章库＝站上已有篇目的指针（只存 slug＋题名）
     📦 知识库＝文档本身，**私人**——键里带 uid，别人查不到也删不掉。
   ⚠ 信封只拆一次：`.then(unwrap)` 之后各调用点直接读 `d.ok`。
     （候选/库存/文章库三个 tab 全部"加载失败"那次，根因就是拆了两次。） */
var kbOpen=null,kbCap=null;
function kbApi(a,extra){return api("kb",Object.assign({a:a},extra||{})).then(unwrap);}
function kbKindName(k){return ({md:"文稿",html:"网页",svg:"图",mermaid:"结构图",csv:"表",json:"数据",code:"代码",note:"笔记"})[k]||"笔记";}
function kbLoad(){
  var box=el("kb-body");box.innerHTML='<div class="hint">正在加载…</div>';
  kbApi("mine",{}).then(function(d){
    if(!d.ok){box.innerHTML='<div class="hint">加载失败，请重试。</div>';return;}
    kbCap=d.cap||null;
    var head='<div style="padding:12px 14px 0">'
      +'<p style="font-size:0.8rem;color:var(--muted);line-height:1.8;margin:0 0 10px">'
      +'这里存的是<b>你自己锻出来的稿子</b>——ChatSDE 画布上的报告、结构图、网页、长稿。'
      +'<b>只有你看得见</b>，别人打不开也删不掉。<br>'
      +'站上<b>已经有的篇目不必存进来</b>：那是「📚 文章库」的活，贴链接就行，链接不会过期。'
      +'</p>'
      +'<p style="font-size:0.76rem;color:var(--muted);margin:0 0 12px">'
      +'已用 '+(d.n||0)+' / '+((d.cap&&d.cap.count)||0)+' 件　·　'+(d.chars||0)+' 字'
      +'</p></div>';
    if(!(d.items||[]).length){
      box.innerHTML=head+'<div class="hint" style="line-height:1.9">还是空的。<br><br>'
        +'去 <a href="/taste/chatsde/" target="_blank">ChatSDE</a> 问一句能出长文的，'
        +'答完点「⧉ 落到画布」，再在画布工具条上点「⇧ 存进知识库」。</div>';
      return;
    }
    var html=head;
    (d.items||[]).forEach(function(it){
      html+='<div class="me-item" style="align-items:flex-start">'
        +'<span><b>'+esc(it.title||"未命名")+'</b>'
        +'<br><span style="font-size:0.74rem;color:var(--muted)">'
        +kbKindName(it.kind)+'　·　'+(it.chars||0)+' 字　·　'+fmtT(it.ts)
        +(it.from?('　·　'+esc(it.from)):"")
        +(it.ver?('　·　第 '+it.ver+' 版'):"")
        +'</span></span>'
        +'<button data-kbopen="'+esc(it.id)+'">打开</button></div>';
    });
    box.innerHTML=html;
    Array.prototype.forEach.call(box.querySelectorAll("[data-kbopen]"),function(b){
      b.onclick=function(){kbShow(b.getAttribute("data-kbopen"));};
    });
  },function(){box.innerHTML='<div class="hint">加载失败，请重试。</div>';});
}
function kbShow(id){
  var box=el("kb-body");box.innerHTML='<div class="hint">正在打开…</div>';
  kbApi("get",{id:id}).then(function(d){
    if(!d.ok){box.innerHTML='<div class="hint">'+esc(d.msg||"打不开。")+'</div>';return;}
    kbOpen=d.item;
    var it=d.item,txt=d.text||"";
    box.innerHTML='<div style="padding:12px 14px">'
      +'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px">'
      +'<b style="flex:1;min-width:0">'+esc(it.title||"未命名")+'</b>'
      +'<button id="kb-ren">✎ 改名</button><button id="kb-dl">⤓ 下载</button><button id="kb-del">🗑 删除</button>'
      +'</div>'
      +'<p style="font-size:0.74rem;color:var(--muted);margin:0 0 10px">'
      +kbKindName(it.kind)+'　·　'+(it.chars||0)+' 字　·　'+fmtT(it.ts)+'</p>'
      +'<pre style="white-space:pre-wrap;word-break:break-word;font:0.78rem/1.75 ui-monospace,Menlo,Consolas,monospace;'
      +'background:var(--card,#161310);padding:12px 14px;border-radius:8px;margin:0">'+esc(txt)+'</pre>'
      +'</div>';
    el("kb-ren").onclick=function(){
      var n=prompt("这一件叫什么？",it.title||"");
      if(!n||!n.trim())return;
      kbApi("ren",{id:it.id,title:n.trim()}).then(function(r){if(r.ok)kbShow(it.id);else alert(r.msg||"改不了。");});
    };
    el("kb-dl").onclick=function(){
      var ext=({md:".md",html:".html",svg:".svg",mermaid:".mmd",csv:".csv",json:".json",code:".txt"})[it.kind]||".txt";
      var a=document.createElement("a");
      a.href=URL.createObjectURL(new Blob([txt],{type:"text/plain;charset=utf-8"}));
      a.download=String(it.title||"未命名").replace(/[^\\w\\u4e00-\\u9fff-]/g,"_")+ext;
      document.body.appendChild(a);a.click();document.body.removeChild(a);
    };
    el("kb-del").onclick=function(){
      if(!confirm("删掉《"+(it.title||"未命名")+"》？删了就没有了。"))return;
      kbApi("del",{id:it.id}).then(function(r){if(r.ok){kbOpen=null;kbLoad();}else alert(r.msg||"删不了。");});
    };
  },function(){box.innerHTML='<div class="hint">打不开，请重试。</div>';});
}
function lbApi(a,extra){return api("lb",Object.assign({a:a},extra||{})).then(unwrap);}''',
    "⑧ 知识库逻辑（列表/打开/改名/下载/删除）", "function kbLoad()",
)

# ── 5. 社区首页四格加一格 ─────────────────────────────────────
rep(
    '''     + '<div class="hm-g" data-go2="lib">''',
    '''     + '<div class="hm-g" data-go2="kb"><b>📦 我的知识库</b><span>画布上锻出来的稿子存在这儿——只有你看得见，换台机器也还在。</span></div>'
     + '<div class="hm-g" data-go2="lib">''',
    "⑨ 社区首页加一格", 'data-go2="kb"',
)
rep(
    '''      if (g === "lib")   { lbGo("me", null); return; }''',
    '''      if (g === "kb")    { kbOpen = null; show("kb"); kbLoad(); return; }
      if (g === "lib")   { lbGo("me", null); return; }''',
    "⑩ 社区首页那一格接线", 'if (g === "kb")',
)

if h == orig:
    print("无改动（已是最新）")
else:
    io.open(P, "w", encoding="utf-8").write(h)
    print("\n共 %d 处，%d → %d 字符" % (len(done), len(orig), len(h)))
