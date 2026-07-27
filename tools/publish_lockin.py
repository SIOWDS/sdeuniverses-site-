# -*- coding: utf-8 -*-
"""《显影闭锁》· 上 /ideas/ 与今日长文。

用法： python3 tools/publish_lockin.py --src /home/claude/paper/manifestation-lock-in.md

落点选择：/ideas/ 的体例是「一个新思想 → 教育／健康／商业三篇实践文」，
本文的工序恰好反向——三个领域各取一篇，碰撞出一个新思想。放在同一栏目里
作为逆向的一条，比另开栏目更省事，也更说得清它与那二十条的关系。
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
KICKER_NO = "No.21"
KICKER_CL = "逆向 · 三域碰撞"
PUBDATE = "2026年7月27日"
DECK = (
    "这一条与前二十条的工序相反。前二十条是从一个新思想出发，向下延伸到教育、健康、"
    "商业三处用法；这一条是倒着走的——从站上教育、健康、商业三个栏目里各取一篇，"
    "各提三个已走到本领域极限处的判断，把这九个判断两两相撞，看它们之间的空隙里长出什么。"
    "长出来的是一个等式：终止能力，就是不被显现地存在的能力。一个过程之所以能自行结束，"
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


def head_css():
    src = SKELETON.read_text(encoding="utf-8")
    i, j = src.find("<style>"), src.find("</style>")
    assert 0 < i < j, "骨架缺 style"
    return src[i + 7:j]


EXTRA = """
.body h2{font-size:26px;margin:52px 0 18px;padding-left:14px;border-left:5px solid var(--bronze);line-height:1.5}
.body h3{font-size:20px;margin:34px 0 12px;color:var(--bronze)}
.body p{margin:0 0 15px;text-align:justify;line-height:1.98}
.body blockquote{margin:24px 0;padding:20px 24px;background:var(--bronzeSoft);
border-left:4px solid var(--bronze);border-radius:5px;font-size:16.5px;line-height:1.95}
.body blockquote p:last-child{margin:0}
.body pre{background:#F7F4EA;border:1px solid rgba(138,106,30,.25);border-radius:6px;
padding:18px 20px;overflow-x:auto;font-family:"SF Mono",Menlo,Consolas,monospace;font-size:13px;line-height:1.7}
.body table{width:100%;border-collapse:collapse;margin:22px 0;font-size:15px}
.body th{background:var(--bronzeSoft);text-align:left;padding:11px 13px;border:1px solid rgba(138,106,30,.28)}
.body td{padding:11px 13px;border:1px solid rgba(138,106,30,.18);vertical-align:top}
.body hr{border:0;border-top:1px solid rgba(138,106,30,.24);margin:44px 0}
.body ul{margin:0 0 16px;padding-left:1.4em}
.body li{margin:0 0 9px;line-height:1.95}
.body em{font-style:normal;opacity:.78;font-size:15px}
.readbar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;
max-width:820px;margin:0 auto 6px;padding:12px 0}
.readbar a,.readbar span{font-size:13.5px;text-decoration:none;padding:7px 14px;border-radius:5px;
border:1px solid rgba(138,106,30,.35);color:var(--bronze)}
.readbar .cur{background:var(--bronze);color:#FBF9F3;border-color:var(--bronze)}
"""


def md_to_html(md: str) -> str:
    md = md.split("\n", 1)[1] if md.startswith("# ") else md
    out, lines = [], md.split("\n")
    i, in_pre, in_tbl = 0, False, False

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(r"`([^`]+?)`", r"<code>\1</code>", s)
        return s

    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            if not in_pre:
                out.append("<pre>"); in_pre = True
            else:
                out.append("</pre>"); in_pre = False
            i += 1; continue
        if in_pre:
            out.append(html.escape(ln)); i += 1; continue
        if re.match(r"^\s*\|", ln):
            rows = []
            while i < len(lines) and re.match(r"^\s*\|", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if len(rows) >= 2 and set("".join(rows[1]).replace(" ", "")) <= set("-:"):
                head, body = rows[0], rows[2:]
            else:
                head, body = None, rows
            out.append("<table>")
            if head:
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>")
            for r in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</table>")
            continue
        if re.match(r"^---+\s*$", ln):
            out.append("<hr>"); i += 1; continue
        m = re.match(r"^(#{2,4})\s+(.*)$", ln)
        if m:
            lvl = min(len(m.group(1)), 4)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); i += 1; continue
        if ln.startswith("> "):
            buf = []
            while i < len(lines) and (lines[i].startswith("> ") or lines[i].strip() == ">"):
                buf.append(lines[i][2:] if len(lines[i]) > 1 else "")
                i += 1
            out.append("<blockquote>" + "".join(
                f"<p>{inline(x)}</p>" for x in buf if x.strip()) + "</blockquote>")
            continue
        if re.match(r"^\s*[-*]\s+", ln):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                out.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("</ul>"); continue
        if ln.strip():
            out.append(f"<p>{inline(ln.strip())}</p>")
        i += 1
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 思想·应用 {no} | SDE Universes</title>
<meta name="description" content="{desc}">
<style>{css}{extra}</style></head><body>
<nav><div class="wn"><a class="nav-logo" href="/">SDE Universes</a><a class="nav-back" href="/ideas/">← 思想·应用</a></div></nav>
<header class="art"><div class="w">
<div class="art-kicker"><span class="no">{no}</span><span class="cl">{cl}</span></div>
<h1 class="art-title">显影闭锁<br>被持续看见的过程为什么不能结束自己</h1>
<div class="art-sub">{sub}</div>
<div class="art-meta"><span class="zh">王德生 著</span> · SDE UNIVERSES · 思想·应用 {no} · <span class="zh">全文约 {wan} 万字 · 发表于{pub}</span></div>
</div></header>
<div class="body"><div class="w">
<div class="readbar"><span class="cur">📖 网页长文</span>
<a href="read.html">📄 在线 PDF</a>
<a href="manifestation-lock-in.pdf" download>⬇ 下载 PDF</a></div>
<div class="deck">{deck}</div>
<div class="motif"><div class="ml">总 母 题</div><p>{motif}</p></div>
{body}
</div></div>
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
p{text-indent:2em;text-align:justify;margin:0 0 8pt}
blockquote{background:#F2ECDC;border-left:3pt solid #8A6A1E;padding:9pt 12pt;margin:10pt 0}
blockquote p{text-indent:0}
pre{background:#F5F2E8;border:.5pt solid #D8C89A;padding:8pt;font-size:8pt;line-height:1.55;white-space:pre-wrap}
table{width:100%;border-collapse:collapse;margin:10pt 0;font-size:8.8pt}
th{background:#F2ECDC;text-align:left;padding:5pt;border:.5pt solid #C9B customs}
td{padding:5pt;border:.5pt solid #DDD3B4;vertical-align:top}
ul{margin:0 0 9pt}li{margin:0 0 4pt}
hr{border:0;border-top:.5pt solid #DDD3B4;margin:14pt 0}
""".replace("#C9B customs", "#C9B77A")

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    md = Path(args.src).read_text(encoding="utf-8")
    body = md_to_html(md)
    chars = len(re.sub(r"<[^>]+>|\s", "", body))
    wan = f"{chars / 10000:.1f}"

    OUT.mkdir(parents=True, exist_ok=True)

    # PDF
    tmp = Path("/tmp/lockin.html")
    tmp.write_text(f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(TITLE)}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · 思想·应用 {KICKER_NO} · {KICKER_CL}</div>
<h1>显影闭锁<br>被持续看见的过程为什么不能结束自己</h1>
<p class="sub">{html.escape(SUB)}</p>
<div class="by"><b>王德生</b> 著　·　思想·应用 {KICKER_NO}　·　{PUBDATE}</div></div>
{body}</body></html>""", encoding="utf-8")
    pdf = OUT / "manifestation-lock-in.pdf"
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "20", "--margin-bottom", "18",
                    "--margin-left", "19", "--margin-right", "19", "--quiet",
                    str(tmp), str(pdf)], check=True)
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    pages = int(re.search(r"Pages:\s+(\d+)", info.stdout).group(1))

    page = PAGE.format(title=html.escape(TITLE), no=KICKER_NO, cl=KICKER_CL,
                       desc=html.escape(DECK[:200]), css=head_css(), extra=EXTRA,
                       sub=html.escape(SUB), wan=wan, pub=PUBDATE,
                       deck=DECK, motif=MOTIF, body=body)
    for tag in ("div", "html", "body", "style", "header", "nav", "table", "pre", "blockquote", "ul"):
        o, c = page.count(f"<{tag}"), page.count(f"</{tag}>")
        assert o == c, f"<{tag}> 不配对 {o}/{c}"
    for w in ("发生学", "发现学", "本体论", "显露", "纠缠", "裂缝"):
        assert w not in body, f"招牌词残留：{w}"
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "read.html").write_text(READ.format(pages=pages), encoding="utf-8")
    print(f"  /ideas/manifestation-lock-in/  {chars} 字 · {pages} 页 · 三种读法")
    return wan, pages


if __name__ == "__main__":
    main()
