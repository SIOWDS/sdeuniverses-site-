# -*- coding: utf-8 -*-
"""《显影闭锁》排版重制。

在 md→html 的基础上做一层结构识别，把论文里本来就有的体例
（碰撞三段式、暗流的支撑与不变量、编号条件、自反层级、学科兑现）
提升为有视觉层级的组件，并补上长文必需的目录、锚点、进度条与回顶。

用法： python3 tools/restyle_lockin.py --src /home/claude/paper/manifestation-lock-in.md
"""
import argparse
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "ideas" / "manifestation-lock-in"
SKELETON = ROOT / "public" / "ideas" / "fate-as-entanglement" / "index.html"

TITLE = "显影闭锁：被持续看见的过程为什么不能结束自己"
SUB = "一个过程结束自己的能力，以它拥有一段不必向任何人产出证据的时间为条件。"
NO, CL, PUB = "No.21", "逆向 · 三域碰撞", "2026年7月27日"
ROMAN = ["", "Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ", "Ⅺ", "Ⅻ", "ⅩⅢ", "ⅩⅣ", "ⅩⅤ"]

DECK = (
    "这一条与前二十条的工序相反。前二十条是从一个新思想出发，向下延伸到教育、健康、"
    "商业三处用法；这一条是倒着走的——从站上教育、健康、商业三个栏目里各取一篇，"
    "各提三个已走到本领域极限处的判断，把这九个判断两两相撞，看它们之间的空隙里长出什么。"
    "长出来的是一个等式：<b>终止能力，就是不被显现地存在的能力。</b>一个过程之所以能自行结束，"
    "是因为结束意味着停止产出证据；而一个必须持续产出证据的过程，在结构上被禁止结束——"
    "它失去的不是意愿，是「停」这个动作在它所处的语法里根本不存在。"
)
MOTIF = (
    "系统只能通过<b>使之显现</b>来管理某物，而显现动作本身对被显现者课以<b>持续产出证据的义务</b>。"
    "由于终止在结构上是一个<b>零产出事件</b>，而体制只承认显现物，"
    "「停止产出证据」在体制内无法被表述为一个合法事件。于是关不掉的炎症、停不下来的自我审判、"
    "砍不掉的失败项目、退不了场的过时理论、休不了耕的土地——它们共享同一个成因："
    "<b>所处的体制里没有「停」这个动作的合法语法。</b>修复方向因此很具体：不是减少监控，"
    "而是在核算体系的语法里为零产出事件设立词法——为终止设科目，为放弃设奖励，为回落设读数，"
    "为「这条路我不走了」设一个不等于失败的名字。"
)
SRC_NOTE = (
    "<b>关于本文</b>　本文是「思想·应用」专栏第 21 篇，也是其中唯一一篇<b>逆向</b>产出："
    "前二十篇从一个新思想出发向下延伸到三个领域，本篇从三个领域各取一篇文章反向碰撞出一个新思想。"
    "三篇取自站内——教育栏《自律杀死自己：最痛苦的悖论》、健康栏《关不掉的病：终止失败作为一个病族》、"
    "商业栏胡志英《审计性剥离：论创新识别如何从价值发生的完整体中切走骨》。"
    "工序为三阶：二十七对跨域碰撞（作废一对）、二十六个涌现物、四条暗流、一个新典范，"
    "并附五条可证伪条件、三条禁止清单与一节自反检验。"
    "第九节的边界与禁止条款优先级高于全文其余内容；本文不构成任何医疗、法律或投资建议。"
)

# 需要提为大号引文的关键句（原文照录，出现即提升）
PULLS = [
    "终止能力，就是不被显现地存在的能力。",
    "科学林业真正杀死的，不是森林的多样性，是森林让单棵树单独死掉的能力。",
    "不是不想停，是「停」这个动作在它所处的语法里不存在。",
]

TOPO_SVG = """<div class="topo">
<div class="topo-cap">四条暗流的依赖拓扑</div>
<svg viewBox="0 0 640 400" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="四条暗流的依赖关系：可见性课税与账本盲区互为两面，共同指向终止权失效，其空缺由替代—萎缩螺旋填补">
<defs>
<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
<path d="M0,0 L10,5 L0,10 z" fill="#8A6A1E"/></marker>
</defs>
<rect x="176" y="14" width="288" height="62" rx="9" fill="#F2EAD6" stroke="#B0892F"/>
<text x="320" y="40" text-anchor="middle" font-size="15.5" font-weight="700" fill="#22222A">暗流三 · 可见性课税</text>
<text x="320" y="61" text-anchor="middle" font-size="12.5" fill="#5A5545">被看见者须持续产出证据</text>

<rect x="176" y="324" width="288" height="62" rx="9" fill="#F2EAD6" stroke="#B0892F"/>
<text x="320" y="350" text-anchor="middle" font-size="15.5" font-weight="700" fill="#22222A">暗流四 · 账本的结构性盲区</text>
<text x="320" y="371" text-anchor="middle" font-size="12.5" fill="#5A5545">只登记显现物与增量</text>

<rect x="150" y="150" width="340" height="66" rx="9" fill="#FBF9F3" stroke="#8A6A1E" stroke-width="1.6"/>
<text x="320" y="177" text-anchor="middle" font-size="15.5" font-weight="700" fill="#22222A">暗流一 · 终止权的外移与失效</text>
<text x="320" y="198" text-anchor="middle" font-size="12.5" fill="#5A5545">能宣布结束的位置，被不能宣布结束的结构占据</text>

<rect x="150" y="248" width="340" height="52" rx="9" fill="#FBF9F3" stroke="#B0892F"/>
<text x="320" y="270" text-anchor="middle" font-size="14.5" font-weight="700" fill="#22222A">暗流二 · 替代—萎缩螺旋</text>
<text x="320" y="289" text-anchor="middle" font-size="12" fill="#5A5545">代劳侵蚀被代劳的能力</text>

<line x1="320" y1="76" x2="320" y2="146" stroke="#8A6A1E" stroke-width="1.6" marker-end="url(#ar)"/>
<text x="332" y="118" font-size="12" fill="#8A6A1E">课税使「停止产出」成为违约</text>
<line x1="320" y1="216" x2="320" y2="244" stroke="#8A6A1E" stroke-width="1.6" marker-end="url(#ar)"/>
<text x="332" y="236" font-size="12" fill="#8A6A1E">权限空缺由代劳装置填补</text>
<line x1="120" y1="355" x2="120" y2="274" stroke="#8A6A1E" stroke-width="1.6" marker-end="url(#ar)"/>
<line x1="176" y1="355" x2="120" y2="355" stroke="#8A6A1E" stroke-width="1.6"/>
<line x1="120" y1="274" x2="146" y2="274" stroke="#8A6A1E" stroke-width="1.6" marker-end="url(#ar)"/>
<text x="16" y="318" font-size="12" fill="#8A6A1E">代价不显现</text>
<text x="16" y="336" font-size="12" fill="#8A6A1E">故代劳恒占优</text>

<path d="M470 45 C556 45 556 355 470 355" fill="none" stroke="#B0892F" stroke-width="1.4" stroke-dasharray="5 4"/>
<text x="500" y="196" font-size="12" fill="#8A6A1E" text-anchor="middle">同一枚</text>
<text x="500" y="214" font-size="12" fill="#8A6A1E" text-anchor="middle">硬币两面</text>
</svg></div>"""

MATRIX = """<div class="matrix">
<div class="mx-cap">九个输入判断 · 三领域各三</div>
<div class="mx-grid">
<div class="mx-col edu"><div class="mx-h">教育<span>《自律杀死自己》</span></div>
<div class="mx-i"><b>E1</b>行动层反馈被提升为存在层裁决</div>
<div class="mx-i"><b>E2</b>目的化败坏：副产品状态被显题化即改变生成条件</div>
<div class="mx-i"><b>E3</b>错位掩盖：提高错误方向上的效率，并压低方向问题的显现强度</div></div>
<div class="mx-col hea"><div class="mx-h">健康<span>《关不掉的病》</span></div>
<div class="mx-i"><b>H1</b>终止是可单独坏掉的独立程序</div>
<div class="mx-i"><b>H2</b>替代终止侵蚀重建终止</div>
<div class="mx-i"><b>H3</b>指标测幅度，不测收尾</div></div>
<div class="mx-col biz"><div class="mx-h">商业<span>《审计性剥离》</span></div>
<div class="mx-i"><b>B1</b>剥离是结构必然，不是失灵</div>
<div class="mx-i"><b>B2</b>剥余锁：保护即照亮，照亮即切割</div>
<div class="mx-i"><b>B3</b>损失不入账</div></div>
</div></div>"""

EXTRA = """
.lead-h2{display:none}
.body h2{font-size:27px;margin:60px 0 20px;line-height:1.45;scroll-margin-top:20px}
.body h2 .hn{font-family:"Playfair Display",Georgia,serif;font-weight:500;color:var(--bronze2);font-size:21px;margin-right:14px}
.body h3{font-size:20px;margin:38px 0 13px;color:var(--ink);scroll-margin-top:20px}
.body h4{font-size:17px;margin:26px 0 10px;color:var(--bronze)}
.body p{margin:0 0 15px;text-align:justify;line-height:2.0}
.body ul{margin:0 0 16px;padding-left:1.4em}
.body li{margin:0 0 9px;line-height:1.95}
.body hr{border:0;border-top:1px solid var(--line);margin:46px 0}
.body em{font-style:normal;opacity:.74;font-size:14.6px}
.pull{margin:38px 0;padding:4px 0 4px 26px;border-left:4px solid var(--bronze2);
font-size:21px;line-height:1.72;font-weight:700;color:var(--ink)}
/* 碰撞卡 */
.collide{border:1px solid var(--line);border-radius:12px;padding:4px 26px 20px;margin:22px 0;background:var(--paper2)}
.collide h3{margin:22px 0 14px;font-size:19.5px;color:var(--ink)}
.collide h3 .cx{color:var(--bronze2);font-weight:600;letter-spacing:.04em}
.cl-row{margin:0 0 12px;padding-left:78px;position:relative;line-height:1.92;text-align:justify}
.cl-row .lb{position:absolute;left:0;top:2px;width:64px;text-align:right;font-size:12px;
letter-spacing:.16em;color:var(--bronze);font-weight:700}
.cl-out{margin:16px 0 0;padding:15px 20px;background:#F2EAD6;border-radius:9px;
border-left:4px solid var(--bronze);line-height:1.9;text-align:justify}
.cl-out .nm{font-size:17.5px;font-weight:700;color:var(--ink);display:block;margin-bottom:5px}
.void{opacity:.6;font-size:14.5px;border-left:3px solid var(--line);padding-left:14px;margin:14px 0}
/* 暗流卡 */
.flow{border:1px solid var(--bronze2);border-radius:12px;padding:6px 26px 20px;margin:26px 0;
background:linear-gradient(150deg,#F7F2E4,#FBF9F3)}
.flow h3{color:var(--bronze);font-size:21px;margin:20px 0 12px}
.flow .sup{font-size:13.5px;color:var(--ink2);background:rgba(176,137,47,.10);
border-radius:7px;padding:10px 14px;margin:0 0 13px;line-height:1.85}
/* 典范卡 */
.para{border:2px solid var(--bronze);border-radius:14px;padding:26px 30px;margin:30px 0;
background:linear-gradient(150deg,#F2EAD6,#FBF9F3);box-shadow:0 6px 26px rgba(138,106,30,.10)}
.para .pl{font-size:11.5px;letter-spacing:.42em;color:var(--bronze);font-weight:600;margin-bottom:12px}
.para p{font-size:17px;line-height:1.95;margin:0 0 10px}
.para p:last-child{margin:0}
/* 编号卡（证伪条件 / 禁止 / 自反层 / 学科兑现） */
.num{border-left:4px solid var(--bronze2);background:var(--paper2);border-radius:0 10px 10px 0;
padding:16px 22px;margin:16px 0}
.num .nh{font-size:16.5px;font-weight:700;color:var(--ink);margin-bottom:7px}
.num p{margin:0 0 10px}
.num p:last-child{margin:0}
.num.stop{border-left-color:#A8613C;background:#FAF2ED}
.num.stop .nh{color:#8E4B2C}
.disc{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:20px 0}
.disc .d{border:1px solid var(--line);border-radius:11px;padding:17px 20px;background:var(--paper2)}
.disc .dh{font-size:15.5px;font-weight:700;color:var(--bronze);margin-bottom:7px}
.disc .d p{margin:0;font-size:14.6px;line-height:1.88}
/* 九判断矩阵 */
.matrix{margin:26px 0 30px}
.mx-cap,.topo-cap{font-size:11.5px;letter-spacing:.4em;color:var(--bronze);font-weight:600;margin-bottom:13px}
.mx-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}
.mx-col{border:1px solid var(--line);border-radius:11px;overflow:hidden;background:var(--paper2)}
.mx-h{padding:12px 16px;font-weight:700;font-size:16px;color:#fff}
.mx-h span{display:block;font-size:12px;font-weight:400;opacity:.9;margin-top:3px}
.mx-col.edu .mx-h{background:#33608F}.mx-col.hea .mx-h{background:#2E7D54}.mx-col.biz .mx-h{background:#8A6A1E}
.mx-i{padding:11px 16px;font-size:14.2px;line-height:1.8;border-top:1px solid var(--line)}
.mx-i b{color:var(--bronze);margin-right:7px}
/* 拓扑图 */
.topo{margin:26px 0 32px}
.topo svg{width:100%;height:auto;background:var(--paper2);border:1px solid var(--line);border-radius:12px;padding:10px}
/* 阅读辅助 */
#pbar{position:fixed;top:0;left:0;height:3px;width:0;background:var(--bronze2);z-index:99}
#totop{position:fixed;right:22px;bottom:26px;width:42px;height:42px;border-radius:50%;
background:var(--bronze);color:#FBF9F3;border:0;font-size:17px;cursor:pointer;display:none;z-index:98;
box-shadow:0 4px 16px rgba(0,0,0,.2)}
.toc a{display:block;padding:7px 0;color:var(--ink2);font-size:15px;border-bottom:1px dashed var(--line2);text-decoration:none}
.toc a:hover{color:var(--bronze)}
@media(max-width:760px){
.mx-grid,.disc{grid-template-columns:1fr}
.cl-row{padding-left:0}.cl-row .lb{position:static;display:block;text-align:left;width:auto;margin-bottom:3px}
.body h2{font-size:23px}.pull{font-size:18px}
}
"""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+?)`", r"<code>\1</code>", s)
    return s


def md_to_blocks(md):
    """先转成中间块序列，便于后续结构识别。"""
    md = md.split("\n", 1)[1] if md.startswith("# ") else md
    lines, out, i, in_pre = md.split("\n"), [], 0, False
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_pre = not in_pre
            if not in_pre:
                out.append(("pre", ""))
            i += 1
            continue
        if in_pre:
            i += 1
            continue
        if re.match(r"^---+\s*$", ln):
            out.append(("hr", "")); i += 1; continue
        m = re.match(r"^(#{2,4})\s+(.*)$", ln)
        if m:
            out.append((f"h{len(m.group(1))}", m.group(2))); i += 1; continue
        if ln.startswith("> "):
            buf = []
            while i < len(lines) and (lines[i].startswith("> ") or lines[i].strip() == ">"):
                buf.append(lines[i][2:] if len(lines[i]) > 1 else ""); i += 1
            out.append(("quote", "\n".join(x for x in buf if x.strip())))
            continue
        if re.match(r"^\s*[-*]\s+", ln):
            buf = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(re.sub(r"^\s*[-*]\s+", "", lines[i])); i += 1
            out.append(("ul", "\n".join(buf)))
            continue
        if ln.strip():
            out.append(("p", ln.strip()))
        i += 1
    return out


def render(blocks):
    """结构识别 + 组件化输出，同时收集目录。"""
    html_out, toc = [], []
    chap = 0
    i = 0
    open_wrap = None   # 'collide' / 'flow' / None
    in_disc = [False]

    def close_inner():
        """只关碰撞卡／暗流卡，不动 disc 网格容器。"""
        nonlocal open_wrap
        if open_wrap:
            html_out.append("</div>")
            open_wrap = None

    def close_wrap():
        if in_disc[0]:
            html_out.append("</div>"); in_disc[0] = False
        close_inner()

    while i < len(blocks):
        kind, txt = blocks[i]

        if kind == "pre":
            close_wrap(); html_out.append(TOPO_SVG); i += 1; continue

        if kind == "hr":
            close_wrap(); html_out.append("<hr>"); i += 1; continue

        if kind == "h2":
            close_wrap()
            # md 的第一个 h2 是主标题的下半句，不进目录也不编号
            if chap == 0 and not re.match(r"^[一二三四五六七八九十]", txt):
                html_out.append(f'<h2 class="lead-h2">{inline(txt)}</h2>')
                i += 1
                continue
            chap += 1
            aid = f"c{chap}"
            body = re.sub(r"^[一二三四五六七八九十点]+、?\s*", "", txt)
            toc.append((ROMAN[min(chap, 15)], txt, aid))
            html_out.append(f'<h2 id="{aid}"><span class="hn">{ROMAN[min(chap,15)]}</span>{inline(txt)}</h2>')
            i += 1
            # 第二节后插九判断矩阵；第七节后插典范前导（拓扑图由 pre 触发）
            if txt.startswith("二、"):
                html_out.append(MATRIX)
            continue

        if kind == "h3":
            # 碰撞小节：形如「3.1 E1 × H1 → 不可结案性」
            m = re.match(r"^([\d.]+)\s+(.+?)\s*→\s*(.+)$", txt)
            if m:
                close_wrap()
                html_out.append('<div class="collide">')
                open_wrap = "collide"
                html_out.append(
                    f'<h3><span class="cx">{inline(m.group(1))}　{inline(m.group(2))}</span>'
                    f'　→　{inline(m.group(3))}</h3>')
                i += 1
                continue
            if txt.startswith("暗流"):
                close_wrap()
                html_out.append('<div class="flow">')
                open_wrap = "flow"
                html_out.append(f"<h3>{inline(txt)}</h3>")
                i += 1
                continue
            close_wrap()
            html_out.append(f"<h3>{inline(txt)}</h3>")
            i += 1
            continue

        if kind == "h4":
            html_out.append(f"<h4>{inline(txt)}</h4>"); i += 1; continue

        if kind == "quote":
            close_wrap()
            # 新典范定义 → 典范卡
            if "显影闭锁" in txt or "终止能力" in txt:
                paras = "".join(f"<p>{inline(x)}</p>" for x in txt.split("\n") if x.strip())
                html_out.append(f'<div class="para"><div class="pl">新 典 范</div>{paras}</div>')
            else:
                paras = "".join(f"<p>{inline(x)}</p>" for x in txt.split("\n") if x.strip())
                html_out.append(f'<div class="para">{paras}</div>')
            i += 1
            continue

        if kind == "ul":
            close_wrap()
            items = "".join(f"<li>{inline(x)}</li>" for x in txt.split("\n"))
            html_out.append(f"<ul>{items}</ul>")
            i += 1
            continue

        # ---- 段落层的结构识别 ----
        # 碰撞三段式
        m = re.match(r"^\*\*(焦点|撞击|涌现物|支撑|共同不变量)\*\*[：:]\s*(.*)$", txt)
        if m and open_wrap in ("collide", "flow"):
            lab, rest = m.group(1), m.group(2)
            if lab == "涌现物":
                mm = re.match(r"^\*\*(.+?)\*\*\s*[—–-]{1,2}\s*(.*)$", rest)
                if mm:
                    html_out.append(
                        f'<div class="cl-out"><span class="nm">{inline(mm.group(1))}</span>'
                        f'{inline(mm.group(2))}</div>')
                else:
                    html_out.append(f'<div class="cl-out">{inline(rest)}</div>')
            elif lab == "支撑":
                html_out.append(f'<div class="sup"><b>支撑涌现物</b>　{inline(rest)}</div>')
            else:
                html_out.append(f'<p class="cl-row"><span class="lb">{lab}</span>{inline(rest)}</p>')
            i += 1
            continue

        # 作废标注
        if txt.startswith("**判定：") or txt.startswith("*（本对"):
            html_out.append(f'<p class="void">{inline(txt.strip("*（）"))}</p>')
            i += 1
            continue

        # 编号卡：证伪条件 / 禁止 / 自反层
        m = re.match(r"^\*\*(条件[一二三四五]（[^）]+）。|禁止[一二三]：[^*]+|第[一二三四五]层：[^*]+)\*\*\s*(.*)$", txt)
        if m:
            close_wrap()
            head = m.group(1).rstrip("。")
            cls = "num stop" if head.startswith("禁止") else "num"
            html_out.append(f'<div class="{cls}"><div class="nh">{inline(head)}</div>'
                            f'<p>{inline(m.group(2))}</p></div>')
            i += 1
            continue

        # 学科兑现：**一 · 临床医学** + 随后一段
        m = re.match(r"^\*\*([一二三四五六七八])\s*·\s*(.+?)\*\*$", txt)
        if m and i + 1 < len(blocks) and blocks[i + 1][0] == "p":
            close_inner()
            if not in_disc[0]:
                html_out.append('<div class="disc">'); in_disc[0] = True
            i += 1
            paras = []
            while (i < len(blocks) and blocks[i][0] == "p"
                   and not re.match(r"^\*\*[一二三四五六七八]\s*·", blocks[i][1])):
                paras.append(f"<p>{inline(blocks[i][1])}</p>"); i += 1
            html_out.append(f'<div class="d"><div class="dh">{m.group(1)} · {inline(m.group(2))}</div>'
                            f'{"".join(paras)}</div>')
            nxt = blocks[i] if i < len(blocks) else ("", "")
            if not (nxt[0] == "p" and re.match(r"^\*\*[一二三四五六七八]\s*·", nxt[1])):
                html_out.append("</div>"); in_disc[0] = False
            continue

        # 关键句提为大号引文
        plain = re.sub(r"\*\*", "", txt)
        if any(p in plain for p in PULLS) and len(plain) < 120:
            close_wrap()
            html_out.append(f'<p class="pull">{inline(txt)}</p>')
            i += 1
            continue

        html_out.append(f"<p>{inline(txt)}</p>")
        i += 1

    close_wrap()
    return "\n".join(html_out), toc


PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 思想·应用 {no} | SDE Universes</title>
<meta name="description" content="{desc}">
<style>{css}{extra}</style></head><body>
<div id="pbar"></div>
<nav><div class="wn"><a class="nav-logo" href="/">SDE Universes</a><a class="nav-back" href="/ideas/">← 思想·应用</a></div></nav>
<header class="art"><div class="w">
<div class="art-kicker"><span class="no">{no}</span><span class="cl">{cl}</span></div>
<h1 class="art-title">显影闭锁<br>被持续看见的过程为什么不能结束自己</h1>
<div class="art-sub">{sub}</div>
<div class="art-meta"><span class="zh">王德生 著</span> · SDE UNIVERSES · 思想·应用 {no} · <span class="zh">全文约 {wan} 万字 · {pages} 页 · 发表于{pub}</span></div>
</div></header>
<div class="body"><div class="w">
<div class="readbar"><span class="cur">📖 网页长文</span>
<a href="read.html">📄 在线 PDF</a>
<a href="manifestation-lock-in.pdf" download>⬇ 下载 PDF</a></div>
<div class="deck">{deck}</div>
<div class="motif"><div class="ml">总 母 题</div><p>{motif}</p></div>
<div class="toc"><div class="tl">目 录</div>{toc}</div>
{body}
<div class="src">{src}</div>
</div></div>
<button id="totop" aria-label="回到顶部">↑</button>
<script>
(function(){{
var b=document.getElementById('pbar'),t=document.getElementById('totop');
function u(){{var d=document.documentElement,h=d.scrollHeight-d.clientHeight;
b.style.width=(h>0?(d.scrollTop/h*100):0)+'%';t.style.display=d.scrollTop>700?'block':'none';}}
addEventListener('scroll',u,{{passive:true}});u();
t.onclick=function(){{scrollTo({{top:0,behavior:'smooth'}});}};
}})();
</script>
<script src="/wds-mode.js" defer></script>
</body></html>"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#22222A;font-size:10.5pt;line-height:1.85;margin:0}
.cover{text-align:center;padding-bottom:13pt;border-bottom:1.2pt solid #8A6A1E;margin-bottom:16pt}
.eyebrow{color:#8A6A1E;letter-spacing:.3em;font-size:7.8pt;margin-bottom:10pt}
h1{font-size:19pt;line-height:1.42;margin:0 0 8pt}
.sub{font-size:10pt;color:#3A3A44;margin:0 auto 10pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#3A3A44}.by b{color:#8A6A1E}
h2{font-size:13pt;padding-left:8pt;border-left:3.5pt solid #8A6A1E;margin:18pt 0 9pt;page-break-after:avoid}
h3{font-size:11.2pt;color:#8A6A1E;margin:13pt 0 7pt;page-break-after:avoid}
h4{font-size:10.4pt;margin:10pt 0 6pt}
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
.para,.flow,.collide,.num,.d{background:#F5F0E2;border-left:3pt solid #8A6A1E;padding:8pt 11pt;margin:9pt 0;page-break-inside:avoid}
.para p,.flow p,.collide p,.num p,.d p,.cl-out,.sup{text-indent:0}
.cl-out{background:#EDE4CC;padding:7pt 10pt;margin:6pt 0}
.cl-out .nm{font-weight:700;display:block;margin-bottom:3pt}
.cl-row .lb{font-weight:700;color:#8A6A1E;margin-right:6pt}
.pull{text-indent:0;font-size:12pt;font-weight:700;border-left:3pt solid #B0892F;padding-left:10pt;margin:12pt 0}
.pl,.mx-cap,.topo-cap{font-size:7.5pt;letter-spacing:.3em;color:#8A6A1E;margin-bottom:5pt}
.nh,.dh,.mx-h{font-weight:700;margin-bottom:4pt}
.mx-col{border:.5pt solid #D8C89A;margin:5pt 0;padding:6pt 9pt}
.mx-i{font-size:9pt;margin:3pt 0}
.void{font-size:9pt;color:#6A6350;text-indent:0}
svg{max-width:100%;height:auto}
ul{margin:0 0 9pt}li{margin:0 0 4pt}
hr{border:0;border-top:.5pt solid #DDD3B4;margin:14pt 0}
.src{font-size:9pt;color:#4A4636;border-top:.5pt dashed #C9B77A;margin-top:20pt;padding-top:10pt;text-indent:0}
"""

READ = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>显影闭锁 · 在线PDF | SDE Universes</title>
<style>html,body{{margin:0;height:100%;background:#22222A}}
header{{height:56px;background:#2E2A20;display:flex;align-items:center;justify-content:space-between;
padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;
border-bottom:1px solid rgba(176,137,47,.45);color:#EFE7D2}}
header a{{color:#B0892F;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · 思想·应用 No.21</span>
<a href="manifestation-lock-in.pdf" download>⬇ 下载 PDF</a></header>
<iframe src="manifestation-lock-in.pdf#view=FitH"></iframe></body></html>"""


def head_css():
    src = SKELETON.read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    return src[i + 7:j]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    a = ap.parse_args()
    md = Path(a.src).read_text(encoding="utf-8")
    body, toc = render(md_to_blocks(md))
    chars = len(re.sub(r"<[^>]+>|\s", "", body))
    wan = f"{chars / 10000:.1f}"
    toc_html = "".join(f'<a href="#{i}"><span class="tn">{r}</span>{html.escape(t)}</a>'
                       for r, t, i in toc)

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path("/tmp/lockin2.html")
    tmp.write_text(f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(TITLE)}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 思想·应用 {NO} · {CL}</div>
<h1>显影闭锁<br>被持续看见的过程为什么不能结束自己</h1>
<p class="sub">{html.escape(SUB)}</p>
<div class="by"><b>王德生</b> 著　·　思想·应用 {NO}　·　{PUB}</div></div>
{body}<div class="src">{SRC_NOTE}</div></body></html>""", encoding="utf-8")
    pdf = OUT / "manifestation-lock-in.pdf"
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19",
                    "--enable-local-file-access", "--quiet",
                    str(tmp), str(pdf)], check=True)
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout).group(1))

    page = PAGE.format(title=html.escape(TITLE), no=NO, cl=CL,
                       desc=html.escape(re.sub("<[^>]+>", "", DECK))[:200],
                       css=head_css(), extra=EXTRA, sub=html.escape(SUB),
                       wan=wan, pages=pages, pub=PUB, deck=DECK, motif=MOTIF,
                       toc=toc_html, body=body, src=SRC_NOTE)
    for tag in ("div", "body", "html", "nav", "header", "button", "svg", "ul", "table"):
        o = len(re.findall(rf"<{tag}[\s>]", page)); c = page.count(f"</{tag}>")
        assert o == c, f"<{tag}> 不配对 {o}/{c}"
    assert page.count("<head>") == page.count("</head>") == 1
    for w in ("发生学", "发现学", "本体论", "显露", "纠缠", "裂缝"):
        assert w not in body, f"招牌词残留：{w}"
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "read.html").write_text(READ.format(pages=pages), encoding="utf-8")
    print(f"  {chars} 字 · {pages} 页 · 目录 {len(toc)} 章 · "
          f"碰撞卡 {body.count('class=\"collide\"')} · 暗流卡 {body.count('class=\"flow\"')} · "
          f"涌现物 {body.count('class=\"cl-out\"')} · 编号卡 {body.count('class=\"num')} · "
          f"学科卡 {body.count('class=\"d\"')} · 引文 {body.count('class=\"pull\"')}")


if __name__ == "__main__":
    main()
