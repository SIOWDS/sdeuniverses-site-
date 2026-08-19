#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDE 社区 · 第一档：**社区首页——公共物摆到门口，亮出命题编号**。

为什么要有这一面（判据，不是版面偏好）：
    微信是**通道**，产物是消息——私有、时序、看完即过；
    社区是**公共物**，产物是共同维护、可继承、后来者接着用的东西。
    候选卡 / 思想库存 / 文章库 / 近邻库此前各躲在一个 tab 里，
    进门第一眼看到的是聊天列表——那是通道的门面，不是共同体的门面。
    而**账本编号 pid 在页面上此前出现 0 次**：三个维度说好「指着同一条命题说话」，
    读者却看不见那个号。

两条纪律（与全站口径一致，这里不破例）：
  ① **不显示任何可排序成等级的数字**——没有赞、分、热度、排名、粉丝。
     四个状态计数是**账本状态**（顶回期／已交手／死格／未交手），不是名次。
     自由群体里任何可排序的数字都会让人朝分高者的语汇靠拢，而语汇距离是这套系统唯一的稀缺品。
  ② **空态写明出路**（可见性铁律③），不是一句「暂无内容」。

实现上的克制：**后端一行没动**。四样公共物本来就有 feed 接口（cd/vt/lb），
首页只是把三次已有调用并起来在前端汇总——少一套新 op，就少一处会跟页面对不上的形状。
（记忆里那次「候选/库存/文章库三个 tab 全部加载失败」正是解包形状对不上，见 sde-wechat-3。）

幂等：每一处都先判「改过了吗」，改过就跳过。
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "public", "sde-wechat", "index.html")

t = io.open(P, encoding="utf-8").read()
orig = t
done = []

def rep(old, new, tag, want=1):
    global t
    if new in t:
        done.append("· %s（已在，跳过）" % tag); return
    n = t.count(old)
    if n != want:
        print("✗ 锚点异常：%s 期望 %d 处，实得 %d" % (tag, want, n)); sys.exit(1)
    t = t.replace(old, new)
    done.append("✓ " + tag)

# ── ① 底部标签条：社区排第一；「社区动态」在标签上简写为「动态」（正文仍叫社区动态）──
OLD_TABS = '''<div class="tabs" id="tabs" style="display:none">
    <div class="tab on" data-go="chats"><i>\U0001f4ac</i>\u804a\u5929<span class="tb" id="tb-unread"></span></div>
    <div class="tab" data-go="book"><i>\U0001f465</i>\u901a\u8baf\u5f55</div>
    <div class="tab" data-go="cand"><i>\U0001f3af</i>\u5019\u9009<span class="tb" id="tb-cd"></span></div>
  <div class="tab" data-go="moments"><i>\U0001f33f</i>\u793e\u533a\u52a8\u6001<span class="tb" id="tb-mo"></span></div>
    <div class="tab" data-go="me"><i>\U0001f464</i>\u6211</div>
  </div>'''
NEW_TABS = '''<div class="tabs" id="tabs" style="display:none">
    <div class="tab on" data-go="home"><i>\U0001f3db</i>\u793e\u533a</div>
    <div class="tab" data-go="chats"><i>\U0001f4ac</i>\u804a\u5929<span class="tb" id="tb-unread"></span></div>
    <div class="tab" data-go="book"><i>\U0001f465</i>\u901a\u8baf\u5f55</div>
    <div class="tab" data-go="cand"><i>\U0001f3af</i>\u5019\u9009<span class="tb" id="tb-cd"></span></div>
    <div class="tab" data-go="moments"><i>\U0001f33f</i>\u52a8\u6001<span class="tb" id="tb-mo"></span></div>
    <div class="tab" data-go="me"><i>\U0001f464</i>\u6211</div>
  </div>'''
rep(OLD_TABS, NEW_TABS, "\u5e95\u90e8\u6807\u7b7e\u6761\u52a0\u300c\U0001f3db \u793e\u533a\u300d\u5e76\u6392\u7b2c\u4e00")

# ── ② 视图容器 ──
rep('<div class="view" id="v-cand">',
    '<div class="view" id="v-home">\n      <div class="scroll" id="hm-body"></div>\n    </div>\n    <div class="view" id="v-cand">',
    "\u65b0\u89c6\u56fe v-home")

# ── ③ show() 白名单（这四处必须一次改齐，页面栽过三次）──
rep('["gate","chats","book","talk"', '["gate","home","chats","book","talk"', "show() \u767d\u540d\u5355")
rep('el("t-plaza").style.display=(v==="chats"||v==="book"||v==="me")',
    'el("t-plaza").style.display=(v==="home"||v==="chats"||v==="book"||v==="me")',
    "\u9876\u680f\u5e7f\u573a\u6309\u94ae\u5728\u9996\u9875\u4e5f\u663e\u793a")
# t-back / t-ttl：home 是顶层 tab，无需返回键；标题走既有的默认分支「SDE 社区」

# ── ④ 标签点击分派 ──
rep('if(g==="moments"){moGo("","");return;}',
    'if(g==="home"){homeGo();return;}\n    if(g==="moments"){moGo("","");return;}',
    "\u6807\u7b7e\u5206\u6d3e\u63a5 homeGo")

# ── ⑤ 登录后的落点：从聊天列表改成社区首页 ──
rep('show("chats");loadInbox();loadGroups();',
    'show("home");homeLoad();loadInbox();loadGroups();',
    "\u767b\u5f55\u540e\u843d\u5728\u793e\u533a\u9996\u9875")

# ── ⑥ 样式 ──
CSS = """
/* 社区首页：公共物的门面。刻意没有任何「热度/排名」样式——见 patch_community_home.py 的纪律① */
.hm-wrap{padding:14px 16px 26px}
.hm-lead{font-size:0.8rem;color:var(--muted);line-height:1.85;margin:0 0 14px}
.hm-stat{display:flex;gap:8px;margin:0 0 6px}
.hm-s{flex:1;text-align:center;background:var(--card2);border:1px solid var(--border2);border-radius:10px;padding:9px 2px}
.hm-s b{display:block;font-size:1.15rem;line-height:1.4}
.hm-s span{font-size:0.66rem;color:var(--muted)}
.hm-note{font-size:0.7rem;color:var(--muted);line-height:1.7;margin:0 0 18px}
.hm-h{font-size:0.82rem;font-weight:700;margin:18px 0 8px;display:flex;align-items:baseline;gap:8px}
.hm-h em{font-style:normal;font-weight:400;font-size:0.7rem;color:var(--muted)}
.hm-card{background:var(--card2);border:1px solid var(--border2);border-radius:10px;padding:11px 13px;margin-bottom:8px;cursor:pointer}
.hm-prop{font-size:0.86rem;line-height:1.65}
.hm-meta{font-size:0.68rem;color:var(--muted);margin-top:6px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.hm-pid{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:0.64rem;color:var(--muted);background:rgba(127,127,127,0.12);border-radius:4px;padding:1px 5px;cursor:pointer}
.hm-sep{font-size:0.75rem;color:var(--muted);line-height:1.7;margin-top:6px;padding-left:9px;border-left:2px solid #1a7f5a}
.hm-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}
.hm-g{background:var(--card2);border:1px solid var(--border2);border-radius:10px;padding:11px 12px;cursor:pointer}
.hm-g b{font-size:0.8rem}
.hm-g span{display:block;font-size:0.68rem;color:var(--muted);line-height:1.6;margin-top:4px}
.hm-empty{font-size:0.76rem;color:var(--muted);line-height:1.85;background:var(--card2);border:1px dashed var(--border2);border-radius:10px;padding:12px 13px}
"""
rep("/* 社区首页：公共物的门面", CSS + "/* 社区首页：公共物的门面（占位注释，勿删）*/\n", "\u6837\u5f0f", want=0) if False else None
if ".hm-wrap{" not in t:
    i = t.find("</style>")
    if i < 0:
        print("✗ 找不到 </style>"); sys.exit(1)
    t = t[:i] + CSS + t[i:]
    done.append("\u2713 \u6837\u5f0f")
else:
    done.append("\u00b7 \u6837\u5f0f\uff08\u5df2\u5728\uff0c\u8df3\u8fc7\uff09")

# ── ⑦ 逻辑 ──
JS = r"""
/* ── 社区首页：公共物摆到门口 ─────────────────────────────────
   判据见 tools/patch_community_home.py 的文件头。两条不许破的纪律：
     ① 这一面上不出现任何可排序成等级的数字（赞/分/热度/排名/粉丝一个都没有）。
        四个计数是**账本状态**，不是名次。
     ② 空态写明出路，不是「暂无内容」。
   后端一行没动：三次已有的 feed 调用在前端汇总即可。 */
var hmBusy = false;
function homeGo(){ show("home"); homeLoad(); }
function homeLoad(){
  if (hmBusy) return;
  hmBusy = true;
  var box = el("hm-body");
  if (!box.getAttribute("data-once")) box.innerHTML = '<div class="hint">正在取共同体此刻的状态…</div>';
  Promise.all([
    cdApi("feed", { limit: 30 }).catch(function(){ return null; }),
    vtApi("feed", { pick: 1, limit: 6 }).catch(function(){ return null; }),
    lbApi("pub",  { limit: 6 }).catch(function(){ return null; })
  ]).then(function(r){
    hmBusy = false;
    box.setAttribute("data-once", "1");
    homeRender(
      (r[0] && r[0].ok && r[0].cards) || [],
      (r[1] && r[1].ok && r[1].items) || [],
      (r[2] && r[2].ok && r[2].items) || []
    );
  }).catch(function(){
    hmBusy = false;
    box.innerHTML = '<div class="hint">加载失败，请重试。</div>';
  });
}
/* 命题编号：点一下复制。它是三个维度指着同一条命题说话的唯一凭据，
   老卡（账本上线之前立的）还没有号——如实说「还没编号」，不假装有。 */
function hmPid(c){
  if (!c.pid) return '<span class="hm-pid" title="账本上线前立的卡，读到时才补号">未编号</span>';
  return '<span class="hm-pid hm-copy" data-p="' + esc(c.pid) + '" title="点一下复制；浏览、对话、社区三处指的是同一条命题">' + esc(c.pid) + '</span>';
}
function homeRender(cards, vault, pubs){
  var n = { open: 0, alive: 0, dead: 0, untouched: 0 };
  cards.forEach(function(c){ if (n[c.state] !== undefined) n[c.state]++; });
  var opens = cards.filter(function(c){ return c.state === "open"; })
                   .sort(function(a, b){ return (a.due || 0) - (b.due || 0); }).slice(0, 5);
  var alives = cards.filter(function(c){ return c.state === "alive"; })
                    .sort(function(a, b){ return (b.settled || 0) - (a.settled || 0); }).slice(0, 3);

  var h = '<div class="hm-wrap">';
  h += '<p class="hm-lead">这里不是聊天的门口，是<b>共同体的门口</b>。'
     + '一条命题在这套系统里有四个年龄段：被立出来、被顶回、活下来或者死掉——下面这四个数说的就是它们此刻各有几条。</p>';

  h += '<div class="hm-stat">'
     + '<div class="hm-s"><b>' + n.open + '</b><span>顶回期</span></div>'
     + '<div class="hm-s"><b style="color:#1a7f5a">' + n.alive + '</b><span>已交手</span></div>'
     + '<div class="hm-s"><b style="color:#b3261e">' + n.dead + '</b><span>死格</span></div>'
     + '<div class="hm-s"><b style="color:#8a8a8a">' + n.untouched + '</b><span>未交手</span></div>'
     + '</div>';
  h += '<p class="hm-note">这四个不是分数，是<b>账本状态</b>。这套系统里没有赞、没有热度、没有排行——'
     + '可排序的数字会让所有人朝分高的那套说法靠拢，而这里唯一稀缺的东西正是<b>说法之间的距离</b>。</p>';

  h += '<div class="hm-h">⏳ 正在交手 <em>72 小时内可顶回</em></div>';
  if (opens.length) {
    opens.forEach(function(c){
      h += '<div class="hm-card cd-open" data-id="' + esc(c.id) + '">'
         + '<div class="hm-prop">' + esc(c.prop || "（无承重命题）") + '</div>'
         + '<div class="hm-meta">' + hmPid(c)
         + '<span>' + esc(c.name || "（未署名）") + '</span>'
         + '<span>' + (((c.backs || []).length) ? ("已被顶回 " + c.backs.length + " 次") : "还没有人顶回") + '</span>'
         + '<span>' + esc(cdLeft(c)) + '</span></div></div>';
    });
  } else {
    h += '<div class="hm-empty">此刻没有一条命题在交手期。<br>'
       + '去「🎯 候选」立一张——或者在文章页、ChatSDE 里撞出一条，那两处都有「立成候选卡」的出口。</div>';
  }

  h += '<div class="hm-h">✅ 带着分离线活下来的 <em>这是共同体真正的产出</em></div>';
  if (alives.length) {
    alives.forEach(function(c){
      var sp = (c.seps || [])[0];
      h += '<div class="hm-card cd-open" data-id="' + esc(c.id) + '">'
         + '<div class="hm-prop">' + esc(c.prop || "") + '</div>'
         + (sp ? '<div class="hm-sep">分离线：' + esc(sp.text || sp.sep || "") + '</div>' : "")
         + '<div class="hm-meta">' + hmPid(c) + '<span>' + esc(c.name || "") + '</span></div></div>';
    });
  } else {
    h += '<div class="hm-empty">还没有命题走完整条链。<br>'
       + '一条命题要活下来，得<b>被人顶回、而作者说得出一条分离线</b>——没人顶回只算「未交手」，被占位者击中又说不出分离线就是「死格」。</div>';
  }

  h += '<div class="hm-h">📦 共同体攒下的</div><div class="hm-grid">'
     + '<div class="hm-g" data-go2="vault"><b>💡 思想库存 · ' + vault.length + '＋</b><span>还没成型的命题、命名与观察。够硬的可以一键升格成候选卡。</span></div>'
     + '<div class="hm-g" data-go2="lib"><b>📚 文章库 · ' + pubs.length + '＋</b><span>推给大家的篇目，每一条都附着推荐人写的那句「它切开了什么」。</span></div>'
     + '<div class="hm-g" data-go2="cand"><b>🎯 候选卡</b><span>三段硬门：承重命题、它切开的辨别面、可裁决的判据。</span></div>'
     + '<div class="hm-g" data-go2="nbr"><b>🔗 近邻库</b><span>先查这块地被谁占过。库未命中≠没被占，不得据以放行。</span></div>'
     + '</div>';
  h += '</div>';
  el("hm-body").innerHTML = h;

  Array.prototype.forEach.call(document.querySelectorAll("#hm-body .cd-open"), function(a){
    a.onclick = function(){ cdOne(a.getAttribute("data-id")); };
  });
  Array.prototype.forEach.call(document.querySelectorAll("#hm-body .hm-copy"), function(a){
    a.onclick = function(e){
      e.stopPropagation();
      var p = a.getAttribute("data-p");
      try { navigator.clipboard.writeText(p); a.textContent = "已复制"; setTimeout(function(){ a.textContent = p; }, 1200); } catch (err) {}
    };
  });
  Array.prototype.forEach.call(document.querySelectorAll("#hm-body .hm-g"), function(a){
    a.onclick = function(){
      var g = a.getAttribute("data-go2");
      if (g === "vault") { vtGo("me", null); return; }
      if (g === "lib")   { lbGo("me", null); return; }
      if (g === "cand")  { cdGo("", ""); return; }
      if (g === "nbr")   { window.open("/nbr/", "_blank"); return; }
    };
  });
}
"""
if "function homeRender(" not in t:
    anchor = "/* \u2500\u2500 \u5168\u6743\u7ba1\u7406 \u2500\u2500 */"
    if anchor not in t:
        print("✗ 找不到插入锚点（全权管理）"); sys.exit(1)
    t = t.replace(anchor, JS + "\n" + anchor, 1)
    done.append("\u2713 \u903b\u8f91")
else:
    done.append("\u00b7 \u903b\u8f91\uff08\u5df2\u5728\uff0c\u8df3\u8fc7\uff09")

if t == orig:
    print("（无改动，已是最新）"); sys.exit(0)

open(P, "wb").write(t.encode("utf-8"))
for d in done: print(d)
print("页面 %.1f KB → %.1f KB" % (len(orig.encode()) / 1024, len(t.encode()) / 1024))
