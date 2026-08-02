#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三批更名：**SDE 微信 → SDE 社区**（用户 2026-08-02 定）。

为什么是「提升」不只是「改名」：
    微信是**通道**（产物是消息：私有、时序、看完即过）；
    社区是**公共物**（共同维护、可继承、后来者接着用）。
    改名只是外面那一半；里面那一半是把公共物摆到门口（另一件事，本脚本不做）。

用户三条裁定：
  ① 「朋友圈」一并改为 **「社区动态」**（同属从微信借来的名字）
  ② **门牌路径 /sde-wechat/ 不动**，只改显示名（改路径会让 sde_wx_pref 等本机键与 33 处链接一起断）
  ③ 先改名、再做「社区首页」

照 tools/rename_chatsde.py 与 tools/rename_sde_brand.py 固化的做法，先分三类：
  · 品牌名  「SDE 微信」「SDE Chat」「朋友圈」（我们自己的界面）  → 改
  · 比喻与真微信  「像微信群一样」「发到微信/群/邮件」「与微信一致」
                  学员文章里讲的朋友圈、金句里引的朋友圈            → **绝不改**
  · 内部标识符与存储键  /sde-wechat/、sde_wx_pref、api/im、mo:、v-moments → **绝不改**

写盘一律先 encode 再 wb 写（补丁里写代理对会 UnicodeEncodeError，而 open(w) 先截断）。
每一组替换都带期望计数断言；任何一处对不上就整批不写。
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
VER = "20260802a"          # 只能往前；上一批是 20260801m

def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, h): open(p, "wb").write(h.encode("utf-8"))

def walk(root, exts=(".html", ".js")):
    for dp, dn, fn in os.walk(root):
        if "/.git" in dp: continue
        for f in fn:
            if f.endswith(exts): yield os.path.join(dp, f)

ERRORS = []
BUF = {}                    # path -> new text（全部通过才落盘）

def get(p):
    if p not in BUF: BUF[p] = rd(p)
    return BUF[p]

def sub(p, old, new, want):
    t = get(p)
    got = t.count(old)
    if got != want:
        ERRORS.append("%s: 期望 %d 处「%s」，实得 %d" % (os.path.relpath(p, ROOT), want, old[:24], got))
        return
    BUF[p] = t.replace(old, new)

# ── 一、品牌名全局（「SDE 微信」在学员文章里不出现，实测 53 处全在我们自己的 15 个文件里）──
BRAND_TOTAL = 0
for p in walk(PUB):
    t = get(p)
    n = t.count(u"SDE 微信")
    if n:
        BUF[p] = t.replace(u"SDE 微信", u"SDE 社区")
        BRAND_TOTAL += n
if BRAND_TOTAL != 53:
    ERRORS.append(u"「SDE 微信」总数期望 53，实得 %d" % BRAND_TOTAL)

sub(os.path.join(PUB, "index.html"), u"SDE Chat", u"SDE Community", 1)

# ── 二、「朋友圈」→「社区动态」：只在我们自己的界面里 ────────────────────
# ⚠️ assets/daily-quotes.js 里那两条金句讲的是真朋友圈（"没发朋友圈的旅行像白去了"），不动。
MOMENTS = {
    "sde-wechat/index.html": 26,
    "sde-wechat/doc.html": 2,
    "search/index.html": 2,
    "taste/assets/sde-vault.js": 2,
    "about/index.html": 1,
}
for rel, n in MOMENTS.items():
    sub(os.path.join(PUB, rel), u"朋友圈", u"社区动态", n)

# ── 三、不带 SDE 前缀、但指的就是本站这套系统的「微信」──────────────────
#      逐串白名单，绝不整词全局替换（同一页里可能并存真微信）。
NAKED = [
    # about：三位一体说明页
    ("about/index.html", u"E 微信围绕", u"E 社区围绕", 1),
    ("about/index.html", u'"微信"不是对现有商业社交产品', u'"社区"不是对现有商业社交产品', 1),
    ("about/index.html", u"微信库", u"社区库", 3),
    ("about/index.html", u"<td><b>微信</b></td>", u"<td><b>社区</b></td>", 1),
    # 共用模块的注释与话术
    ("assets/sde-modes.js", u"并进了微信这一格", u"并进了社区这一格", 1),
    ("assets/sde-nbr.js", u"／微信（候选卡发进会话）", u"／社区（候选卡发进会话）", 1),
    ("assets/sde-portal.js", u"微信＝紫", u"社区＝紫", 1),
    ("assets/sde-portal.js", u"对话烧红 · 微信烧蓝", u"对话烧红 · 社区烧蓝", 1),
    ("challenge/index.html", u"去微信立卡", u"去社区立卡", 3),
    ("nbr/index.html", u"微信里被人顶回", u"社区里被人顶回", 1),
    ('sde-talk/index.html', u'class="imlbl">微信<', u'class="imlbl">社区<', 1),
    ("search/index.html", u"对话 → 微信", u"对话 → 社区", 2),
    ("search/index.html", u"→ 微信＝对撞", u"→ 社区＝对撞", 1),
    ("search/index.html", u"在微信登录过一次", u"在社区登录过一次", 1),
    ("search/index.html", u"在微信里一键升格", u"在社区里一键升格", 1),
    ("search/index.html", u"可稍后在微信里手动补", u"可稍后在社区里手动补", 1),
    ("search/index.html", u"先手动去微信立卡", u"先手动去社区立卡", 1),
    ("taste/assets/sde-cand.js", u"「对话 → 微信」", u"「对话 → 社区」", 1),
    ("taste/assets/sde-cand.js", u"E 微信，默认 D", u"E 社区，默认 D", 1),
    ("taste/assets/sde-vault.js", u"可稍后在微信里手动补", u"可稍后在社区里手动补", 2),
    ("taste/assets/sde-vault.js", u"得在微信里另按一次", u"得在社区里另按一次", 1),
    ("wds-mode.js", u"对话 → 微信", u"对话 → 社区", 1),
    ("wds-mode.js", u"→ 微信＝对撞", u"→ 社区＝对撞", 1),
    ("wds-mode.js", u"再交给微信顶回", u"再交给社区顶回", 1),
    ("taste/wds-companion/wds-read.js", u"浏览 → 微信", u"浏览 → 社区", 2),
    ("taste/wds-companion/wds-read.js", u"送不到微信去被顶回", u"送不到社区去被顶回", 1),
]
for rel, a, b, n in NAKED:
    sub(os.path.join(PUB, rel), a, b, n)

# ── 四、后端 src/worker.js：只改**对外可见**的话术与平台自述 ─────────────
#      「微信式私聊」「与微信一致」这类是拿真微信作比，保留。
WK = os.path.join(ROOT, "src", "worker.js")
WK_SUBS = [
    (u"请先在「SDE 微信」用名字和密码登录", u"请先在「SDE 社区」用名字和密码登录", 4),
    (u"已从 SDE 微信库清除", u"已从 SDE 社区库清除", 1),
    (u"// ===== SDE 微信库：社区动态附件", u"// ===== SDE 社区库：社区动态附件", 0),   # 占位，见下
    (u"SDE 微信库（新件都进这里）", u"SDE 社区库（新件都进这里）", 1),
    (u"手动清一次 SDE 微信库", u"手动清一次 SDE 社区库", 1),
    (u"与「SDE 微信」同一套身份", u"与「SDE 社区」同一套身份", 1),
    (u"接回「SDE 微信」", u"接回「SDE 社区」", 1),
    (u"口令登录通道（「SDE 微信」专用", u"口令登录通道（「SDE 社区」专用", 1),
    (u"私聊页已升级为「SDE 微信」整套系统", u"私聊页已升级为「SDE 社区」整套系统", 1),
    (u"SDE 微信库：朋友圈附件", u"SDE 社区库：社区动态附件", 1),
    # 平台自述块（ChatSDE 每答一次都会念到它）
    (u"SDE微信＝纠缠", u"SDE社区＝纠缠", 1),
    (u"该被顶的送去微信", u"该被顶的送去社区", 1),
    (u"【三 · SDE微信】", u"【三 · SDE社区】", 1),
    (u"· 微信那边不是点赞评论", u"· 社区那边不是点赞评论", 1),
    (u"· 微信侧另有", u"· 社区侧另有", 1),
    (u"群聊、私聊、朋友圈、通讯录", u"群聊、私聊、社区动态、通讯录", 1),
    (u"ChatSDE / SDE微信 / SDE浏览", u"ChatSDE / SDE社区 / SDE浏览", 1),
    (u"（浏览＝显露／ChatSDE＝发生／微信＝纠缠）", u"（浏览＝显露／ChatSDE＝发生／社区＝纠缠）", 1),
    # 金句生产机的提示（学员看得见它的产物落在哪里）
    (u"在朋友圈的「说点什么」处", u"在社区动态的「说点什么」处", 1),
    (u"能被发在朋友圈而不像在发论文", u"能被发在社区动态而不像在发论文", 1),
    (u"未知的朋友圈动作。", u"未知的社区动态动作。", 1),
    (u"朋友圈「说点什么」从里面取", u"社区动态「说点什么」从里面取", 1),
    (u"\\n**/sde-wechat/**：群聊、私聊、朋友圈、通讯录", u"\\n**/sde-wechat/**：群聊、私聊、社区动态、通讯录", 0),
]
for a, b, n in WK_SUBS:
    if n == 0: continue
    sub(WK, a, b, n)

# ── 五、撞全站缓存串（顶栏那些字是 JS 注入的，不撞串等于没改名）───────────
BUMP = 0
PAT = re.compile(r"\?v=2026[0-9a-z]+")
for p in walk(PUB):
    t = get(p)
    n = len(PAT.findall(t))
    if n:
        BUF[p] = PAT.sub("?v=" + VER, t)
        BUMP += n

# ── 落盘（全部通过才写）──────────────────────────────────────────
if ERRORS:
    print("✗ 未写任何文件，以下断言未过：")
    for e in ERRORS: print("   ·", e)
    sys.exit(1)

changed = 0
for p, t in BUF.items():
    if t != rd(p):
        wr(p, t); changed += 1

print("✓ 品牌名「SDE 微信」→「SDE 社区」 %d 处" % BRAND_TOTAL)
print("✓ 「朋友圈」→「社区动态」 %d 处 / %d 文件" % (sum(MOMENTS.values()), len(MOMENTS)))
print("✓ 非前缀「微信」逐串白名单 %d 组" % len(NAKED))
print("✓ 后端对外话术 %d 组" % len([x for x in WK_SUBS if x[2]]))
print("✓ 缓存串 %d 处 → ?v=%s" % (BUMP, VER))
print("✓ 落盘文件 %d 个" % changed)
