#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SDE 社区 · 第二档：**个人 SDE 主页（成员面）**。

对应《SDE社区设计方案》第四节「个人系统」，也是我上一轮列的三件缺口之三。
方案要的六样里，站上已有料的四样先做：思想库／成果库／发生流／关系图。
（个人 AI 与个人文明树另有落点：前者是 ChatSDE 的记忆线，后者站上已有 /growth-tree/。）

**这一面凭什么不是「个人主页」而是「成员面」**：
    传统平台用粉丝数、点赞数、阅读量定义一个人；方案第四节明写要换成
    「产生了什么、影响了谁」。而本站已定死的口径更硬一层——**不做声望分、不做排行榜**
    （自由群体里任何可排序的数字都会让所有人朝分高者的语汇靠拢，
     而语汇距离是这套系统唯一的稀缺品）。
    所以这一面显示的是**痕迹与距离**：他立过哪些命题（带账本编号）、
    哪些活下来了、他在站上留下了什么、**以及他和你有多远**。

距离不是估的：`/props/index.json` 里每人有 800 个语汇二元组的指纹（TF-IDF top-800），
两人的 Jaccard 在前端当场算，并与全站中位数 0.034 对照。**零调用、不烧 Key。**
指纹不全的人（作品太少）如实说「还没有指纹」，不编一个数出来。

后端一行没动：他的命题走已有的 `cd feed {who:uid}`，两份静态索引各取一次并缓存。
幂等：每处先判「改过了吗」。
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
        done.append("\u00b7 %s\uff08\u5df2\u5728\uff09" % tag); return
    n = t.count(old)
    if n != want:
        print("\u2717 \u951a\u70b9\u5f02\u5e38\uff1a%s \u671f\u671b %d \u5904\uff0c\u5b9e\u5f97 %d" % (tag, want, n)); sys.exit(1)
    t = t.replace(old, new, 1)
    done.append("\u2713 " + tag)

# ① 视图容器
rep('<div class="view" id="v-home">',
    '<div class="view" id="v-who">\n      <div class="scroll" id="wh-body"></div>\n    </div>\n    <div class="view" id="v-home">',
    "\u65b0\u89c6\u56fe v-who")

# ② show() 四处一次改齐：白名单 ＋ 返回键 ＋ 标题（who 是二级页，要有返回）
rep('["gate","home","chats"', '["gate","who","home","chats"', "show() \u767d\u540d\u5355")
rep('||v==="vault"||v==="lib"||(v==="moments"&&moWho)',
    '||v==="vault"||v==="lib"||v==="who"||(v==="moments"&&moWho)',
    "\u8fd4\u56de\u952e\u5728\u6210\u5458\u9762\u4e0a\u663e\u793a")
rep('else if(v==="vault")el("t-ttl").textContent="\U0001f4a1 \u601d\u60f3\u5e93\u5b58";',
    'else if(v==="who")el("t-ttl").textContent=whoName||"\u6210\u5458";\n  else if(v==="vault")el("t-ttl").textContent="\U0001f4a1 \u601d\u60f3\u5e93\u5b58";',
    "\u6807\u9898\u5206\u652f")

# ③ 「我」页入口
rep('<div class="me-item"><span>SDE \u8ba8\u8bba\uff08\u516c\u5f00\u5e7f\u573a\uff09</span>',
    '<div class="me-item"><span>\U0001f9ed \u6211\u7684\u4e3b\u9875\uff08\u75d5\u8ff9\u4e0e\u8ddd\u79bb\uff09</span><button id="b-who">\u6253\u5f00</button></div>\n            <div class="me-item"><span>SDE \u8ba8\u8bba\uff08\u516c\u5f00\u5e7f\u573a\uff09</span>',
    "\u300c\u6211\u300d\u9875\u5165\u53e3")

# ④ 样式
CSS = """
/* 成员面：显示痕迹与距离，不显示任何可排序成等级的数字 */
.wh-wrap{padding:14px 16px 26px}
.wh-nm{font-size:1.12rem;font-weight:700}
.wh-fd{font-size:0.72rem;color:var(--muted);margin-top:4px;line-height:1.7}
.wh-dist{background:var(--card2);border:1px solid var(--border2);border-radius:10px;padding:12px 13px;margin:14px 0 4px}
.wh-j{font-size:1.3rem;font-weight:700;font-family:ui-monospace,Menlo,Consolas,monospace}
.wh-bar{height:6px;border-radius:3px;background:rgba(127,127,127,0.18);margin:8px 0 7px;position:relative;overflow:hidden}
.wh-bar i{position:absolute;top:0;bottom:0;left:0;background:#1a7f5a;border-radius:3px}
.wh-bar u{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--muted);text-decoration:none}
.wh-say{font-size:0.72rem;color:var(--muted);line-height:1.75}
.wh-h{font-size:0.82rem;font-weight:700;margin:20px 0 8px}
.wh-it{background:var(--card2);border:1px solid var(--border2);border-radius:10px;padding:10px 12px;margin-bottom:7px;cursor:pointer}
.wh-t{font-size:0.84rem;line-height:1.6}
.wh-m{font-size:0.67rem;color:var(--muted);margin-top:5px;display:flex;gap:9px;flex-wrap:wrap}
.wh-act{display:flex;gap:8px;margin-top:18px}
.wh-act button{flex:1;padding:9px 0;border-radius:9px}
"""
if ".wh-wrap{" not in t:
    i = t.find("</style>")
    t = t[:i] + CSS + t[i:]
    done.append("\u2713 \u6837\u5f0f")
else:
    done.append("\u00b7 \u6837\u5f0f\uff08\u5df2\u5728\uff09")

# ⑤ 逻辑
JS = r"""
/* ── 成员面（个人 SDE 主页）─────────────────────────────────
   判据见 tools/patch_member_page.py 的文件头。一条不许破的纪律：
   **这一面上不出现任何可排序成等级的数字**——没有粉丝、没有阅读量、没有点赞、没有分。
   显示的是痕迹（他立过哪些命题、哪些活下来了、他在站上留下了什么）
   与距离（他和你的语汇族重叠率，当场按指纹算，与全站中位数对照）。 */
var whoUid = "", whoName = "", whoIdx = null, whoPubs = null;
function whoGo(uid, name){ whoUid = uid || ""; whoName = name || ""; show("who"); whoLoad(); }
function whoMe(){ if (ME) whoGo(ME.uid, ME.name); }
/* 两份静态索引：各取一次、缓存住、失败不拦路（少一块就少显示一块） */
function whoJ(url, cache, set){
  if (cache) return Promise.resolve(cache);
  return fetch(url, { cache: "force-cache" }).then(function(r){ return r.json(); })
    .then(function(d){ set(d); return d; }).catch(function(){ return null; });
}
/* 语汇族重叠率：两个人的指纹取 Jaccard。这就是全站「离你最远」用的同一把尺子。 */
function whoJac(a, b){
  if (!a || !b || !a.length || !b.length) return -1;
  var s = {}, i, hit = 0;
  for (i = 0; i < a.length; i++) s[a[i]] = 1;
  for (i = 0; i < b.length; i++) if (s[b[i]]) hit++;
  var uni = a.length + b.length - hit;
  return uni > 0 ? (hit / uni) : -1;
}
function whoFind(idx, name){
  if (!idx || !idx.people) return null;
  for (var i = 0; i < idx.people.length; i++) if (idx.people[i].name === name) return idx.people[i];
  return null;
}
function whoLoad(){
  var box = el("wh-body");
  box.innerHTML = '<div class="hint">正在取他的痕迹…</div>';
  Promise.all([
    whoJ("/props/index.json", whoIdx, function(d){ whoIdx = d; }),
    whoJ("/students/publications.json", whoPubs, function(d){ whoPubs = d; }),
    cdApi("feed", { who: whoUid, limit: 30 }).catch(function(){ return null; })
  ]).then(function(r){
    whoRender(r[0], r[1], (r[2] && r[2].ok && r[2].cards) || []);
  }).catch(function(){ box.innerHTML = '<div class="hint">加载失败，请重试。</div>'; });
}
function whoRender(idx, pubs, cards){
  var him = whoFind(idx, whoName);
  var me  = (ME && ME.name) ? whoFind(idx, ME.name) : null;
  var mine = (ME && whoUid === ME.uid);
  var h = '<div class="wh-wrap">';
  h += '<div class="wh-nm">' + esc(whoName || "（未署名）") + (mine ? '　<span class="wh-say">（这是你自己）</span>' : "") + '</div>';
  h += '<div class="wh-fd">'
     + (him ? (esc((him.fields || []).join(" · ") || "—") + '　站上 ' + esc(String(him.n || 0)) + ' 篇') : '站上还没有作品索引')
     + '</div>';

  /* ── 距离：不是评分，是这套系统唯一的稀缺品 ── */
  h += '<div class="wh-dist">';
  if (mine) {
    h += '<div class="wh-say">自己跟自己没有距离。<b>去看别人</b>——离你越远的人，越可能拿得出你语汇里没有的占位者。</div>';
  } else if (him && me && him.fp && me.fp) {
    var j = whoJac(me.fp, him.fp);
    var med = (idx.calib && idx.calib.j_median) || 0.034;
    var mx  = (idx.calib && idx.calib.j_max) || 0.1;
    var pct = Math.max(2, Math.min(100, Math.round(j / mx * 100)));
    var medp = Math.max(0, Math.min(100, Math.round(med / mx * 100)));
    h += '<div class="wh-j">' + j.toFixed(4) + '</div>';
    h += '<div class="wh-bar"><i style="width:' + pct + '%"></i><u style="left:' + medp + '%"></u></div>';
    h += '<div class="wh-say">你和他的<b>语汇族重叠率</b>（灰线是全站中位 ' + med.toFixed(3) + '）。'
       + (j < med ? '他<b>比一半人离你更远</b>——这正是该找他顶回的理由。'
                  : '你们说话用的是相近的一套词，互相顶回时更容易只是彼此附和。')
       + '<br>这不是评分，也不排名：<b>重叠率低不等于他更好，只等于他更可能看见你看不见的那一格。</b></div>';
  } else {
    h += '<div class="wh-say">还算不出你们之间的距离——'
       + (him ? '你' : '他') + '在站上的作品还不够烘出一份语汇指纹。<br>指纹要 800 个语汇二元组，作品太少时宁可不给数，也不编一个出来。</div>';
  }
  h += '</div>';

  /* ── 他的命题（账本）── */
  var alive = cards.filter(function(c){ return c.state === "alive"; });
  h += '<div class="wh-h">🧭 他立过的命题 · ' + cards.length + ' 条'
     + (alive.length ? '（' + alive.length + ' 条带着分离线活下来）' : "") + '</div>';
  if (cards.length) {
    cards.slice(0, 6).forEach(function(c){
      var lab = (typeof CD_STATE !== "undefined" && CD_STATE[c.state]) ? CD_STATE[c.state][0] : c.state;
      h += '<div class="wh-it cd-open" data-id="' + esc(c.id) + '">'
         + '<div class="wh-t">' + esc(c.prop || "") + '</div>'
         + '<div class="wh-m"><span>' + esc(lab) + '</span>'
         + (c.pid ? '<span class="hm-pid">' + esc(c.pid) + '</span>' : '<span class="hm-pid">未编号</span>')
         + '</div></div>';
    });
  } else {
    h += '<div class="hm-empty">' + (mine ? '你' : '他') + '还没有立过候选卡。<br>'
       + '一条命题只有被立成卡、被人顶回、再被一条分离线救回来，才会留在账本上。</div>';
  }

  /* ── 他在站上留下的（S 维度：只存指针，不搬副本）── */
  var items = [];
  if (pubs && pubs.students) {
    for (var i = 0; i < pubs.students.length; i++) {
      if (pubs.students[i].name === whoName) { items = pubs.students[i].items || []; break; }
    }
  }
  h += '<div class="wh-h">📄 他在站上留下的 · ' + items.length + ' 篇</div>';
  if (items.length) {
    items.slice(0, 6).forEach(function(it){
      h += '<div class="wh-it" onclick="window.open(\'' + esc(it.url) + '\',\'_blank\')">'
         + '<div class="wh-t">' + esc(it.title || "") + '</div>'
         + '<div class="wh-m"><span>' + esc(it.kind || "") + '</span><span>去读 →</span></div></div>';
    });
  } else {
    h += '<div class="hm-empty">站上还没有署他名字的篇目。</div>';
  }

  if (!mine) {
    h += '<div class="wh-act"><button id="wh-dm">私聊他</button><button id="wh-cd">看他的候选</button></div>';
  }
  h += '</div>';
  el("wh-body").innerHTML = h;

  Array.prototype.forEach.call(document.querySelectorAll("#wh-body .cd-open"), function(a){
    a.onclick = function(){ cdOne(a.getAttribute("data-id")); };
  });
  if (el("wh-dm")) el("wh-dm").onclick = function(){ openDm(whoUid, whoName); };
  if (el("wh-cd")) el("wh-cd").onclick = function(){ cdGo(whoUid, whoName); };
}
"""
if "function whoRender(" not in t:
    anchor = "/* \u2500\u2500 \u5168\u6743\u7ba1\u7406 \u2500\u2500 */"
    t = t.replace(anchor, JS + "\n" + anchor, 1)
    done.append("\u2713 \u903b\u8f91")
else:
    done.append("\u00b7 \u903b\u8f91\uff08\u5df2\u5728\uff09")

# ⑥ 「我」页按钮接线 ＋ 社区首页的作者名点进主页
rep('if(b)b.onclick=function(){\n    el("cd-prop").value="";',
    'if(b)b.onclick=function(){\n    el("cd-prop").value="";', "占位", want=0) if False else None
if 'el("b-who")' not in t:
    anchor2 = 'function cdWire(){'
    t = t.replace(anchor2,
        'function whoWire(){ var b = el("b-who"); if (b) b.onclick = whoMe; }\n' + anchor2, 1)
    t = t.replace('cdWire();cdBadge();', 'cdWire();cdBadge();whoWire();', 1)
    done.append("\u2713 \u300c\u6211\u300d\u9875\u6309\u94ae\u63a5\u7ebf")
else:
    done.append("\u00b7 \u6309\u94ae\u63a5\u7ebf\uff08\u5df2\u5728\uff09")

# 社区首页：作者名可点进成员面
OLD_NAME = "+ '<span>' + esc(c.name || \"\uff08\u672a\u7f72\u540d\uff09\") + '</span>'"
NEW_NAME = "+ '<span class=\"hm-who\" data-u=\"' + esc(c.uid) + '\" data-n=\"' + esc(c.name || \"\") + '\" style=\"cursor:pointer;text-decoration:underline\">' + esc(c.name || \"\uff08\u672a\u7f72\u540d\uff09\") + '</span>'"
rep(OLD_NAME, NEW_NAME, "\u793e\u533a\u9996\u9875\u4f5c\u8005\u540d\u53ef\u70b9")
if 'querySelectorAll("#hm-body .hm-who")' not in t:
    a3 = 'Array.prototype.forEach.call(document.querySelectorAll("#hm-body .hm-copy"), function(a){'
    t = t.replace(a3,
        'Array.prototype.forEach.call(document.querySelectorAll("#hm-body .hm-who"), function(a){\n'
        '    a.onclick = function(e){ e.stopPropagation(); whoGo(a.getAttribute("data-u"), a.getAttribute("data-n")); };\n'
        '  });\n  ' + a3, 1)
    done.append("\u2713 \u9996\u9875\u4f5c\u8005\u540d\u63a5\u7ebf")

if t == orig:
    print("\uff08\u65e0\u6539\u52a8\uff09"); sys.exit(0)
open(P, "wb").write(t.encode("utf-8"))
for d in done: print(d)
print("\u9875\u9762 %.1f KB \u2192 %.1f KB" % (len(orig.encode()) / 1024, len(t.encode()) / 1024))
