# -*- coding: utf-8 -*-
"""SDE 经济学频道 /business/sde-economics/ · 建频道页 + 文章页 + PDF + 三种读法。

用法： python3 tools/publish_sde_econ.py --src /home/claude/econ
视觉：账簿主题 —— 米白纸（承商业栏）+ 墨黑 + 朱砂红（赤字之色）+ 铜金（承商业栏）。
源稿为轻标记 Markdown：## h2 / ### h3 / #### h4 / $$公式$$ / |表格| / > 判断 / **粗体**。
"""
import argparse
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "business" / "sde-economics"
PUBDATE_CN = "2026年7月29日"
AUTHOR = "王德生"

ARTICLES = [
    {
        "src": "main", "no": 1, "slug": "feedback-and-bubbles",
        "title": "回写缺失与增长泡沫：SDE 新典范经济发生学",
        "subtitle": "二重回写、代偿增长、发生土壤账户与可证伪研究纲领（修订稿）",
        "score": 151,
        "wanhint": "约 3.6 万字",
        "hook": "现代经济的核心悖论不是增长为何时快时慢，而是增长为何能在成功中制造自己的失败条件。"
                "本文把一个此前只作为分类表一行存在的类型提升为独立的发生类型——代偿增长："
                "修复支出持续上升、土壤读数接近持平、而路径的单位损耗强度从未下降。"
                "它不是可持续增长的低配版本，而是现有一切以净额为判据的核算体系在构造上无法辨识的类型。",
    },
    {
        "src": "src-b", "no": 2, "slug": "compensatory-growth",
        "title": "修得越多，越危险：一种账本看不见的增长",
        "subtitle": "代偿增长的通俗解剖 —— 从心脏的代偿期，到一家公司、一个人、一个行业",
        "score": 149,
        "wanhint": "约 0.9 万字",
        "hook": "有一种增长，每一项指标都正常：产出在涨，投入在涨，存量没降，审计通不出问题。"
                "它不是在透支，也不是在停滞——它在用越来越大的修复量，去追一条从来没变过方向的路。"
                "本文解释一件反直觉的事：在一段可以说清楚的区间里，增加修复投入不是让系统更安全，而是让它更脆弱。",
    },
]

# ── 招牌词零容忍（学派术语不外泄到面向读者的元文案） ──────────────
BANNED_META = ["龙爪手", "改姓", "去母体化", "内功", "金点子"]

# ═══════════════════ LaTeX → HTML（本文所用子集） ═══════════════════
GREEK = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\eta": "η", r"\theta": "θ",
    r"\kappa": "κ", r"\lambda": "λ", r"\mu": "μ", r"\rho": "ρ",
    r"\sigma": "σ", r"\tau": "τ", r"\phi": "φ", r"\chi": "χ", r"\psi": "ψ",
    r"\omega": "ω", r"\Delta": "Δ", r"\Gamma": "Γ", r"\Lambda": "Λ",
    r"\Omega": "Ω", r"\Phi": "Φ", r"\Pi": "Π", r"\Sigma": "Σ",
    r"\partial": "∂", r"\times": "×", r"\cdots": "⋯", r"\cdot": "·",
    r"\sum": "Σ", r"\prod": "Π", r"\max": "max", r"\min": "min",
    r"\exp": "exp", r"\log": "log", r"\in": "∈", r"\to": "→",
    r"\geq": "≥", r"\leq": "≤", r"\approx": "≈", r"\neq": "≠",
    r"\lVert": "‖", r"\rVert": "‖", r"\mathbb{1}": "𝟙",
}
ACCENT = {"hat": "\u0302", "bar": "\u0304", "tilde": "\u0303"}


LB, RB = "\ue000", "\ue001"      # 字面花括号占位符，避免与结构括号混淆


def _grab(s, i):
    """s[i] 必须是 '{'；返回（组内内容, 匹配右括号之后的下标）。"""
    assert s[i] == "{", f"期待 '{{' 于位置 {i}：{s}"
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise AssertionError(f"花括号不配对：{s}")


def _conv(s):
    """平衡括号递归扫描：自然支持 \\frac / 上下标 / \\underbrace 的任意嵌套。"""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            m = re.match(r"\\[A-Za-z]+", s[i:])
            assert m, f"孤立反斜杠：{s[i:i + 6]}"
            cmd, j = m.group(0), i + len(m.group(0))
            if cmd == r"\underbrace":
                a, j = _grab(s, j)
                assert s[j] == "_", f"\\underbrace 后缺 _：{s}"
                b, j = _grab(s, j + 1)
                out.append(f'<span class="ub"><span class="ubt">{_conv(a)}</span>'
                           f'<span class="ubl">{_conv(b)}</span></span>')
            elif cmd == r"\frac":
                a, j = _grab(s, j)
                b, j = _grab(s, j)
                out.append(f'<span class="fr"><span class="fn">{_conv(a)}</span>'
                           f'<span class="fd">{_conv(b)}</span></span>')
            elif cmd in (r"\text", r"\mathrm"):
                a, j = _grab(s, j)
                out.append(_conv(a))
            elif cmd == r"\mathbb":
                a, j = _grab(s, j)
                out.append("𝟙" if a == "1" else _conv(a))
            elif cmd in (r"\hat", r"\bar", r"\tilde"):
                a, j = _grab(s, j)
                out.append(_conv(a) + ACCENT[cmd[1:]])
            elif cmd in GREEK:
                out.append(GREEK[cmd])
            else:
                raise AssertionError(f"公式含未支持命令 {cmd}：{s}")
            i = j
            continue
        if c in "^_":
            tag = "sup" if c == "^" else "sub"
            if i + 1 < n and s[i + 1] == "{":
                a, j = _grab(s, i + 1)
                out.append(f"<{tag}>{_conv(a)}</{tag}>")
                i = j
            else:
                out.append(f"<{tag}>{s[i + 1]}</{tag}>")
                i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _tex(s):
    """把本文使用的 LaTeX 子集转成可在浏览器与 wkhtmltopdf 中一致渲染的 HTML。"""
    s = html.escape(s)
    s = s.replace(r"\{", LB).replace(r"\}", RB)
    for a, b in ((r"\left", ""), (r"\right", ""), (r"\!", ""),
                 (r"\,", "\u2009"), (r"\;", "\u2009"), ("\\ ", " ")):
        s = s.replace(a, b)
    s = _conv(s).replace(LB, "{").replace(RB, "}")
    assert "\\" not in s, f"公式残留反斜杠：{s}"
    return s


# ═══════════════════ 轻标记解析 ═══════════════════
MATHTOK = re.compile(
    r"([A-Za-zΑ-Ωα-ω][A-Za-z0-9]*)"
    r"((?:\^\{[^{}]+\}|\^[A-Za-z0-9]+|_\{[^{}]+\}|_[A-Za-z0-9])+)")
SUBSUP = re.compile(r"([\^_])(?:\{([^{}]+)\}|([A-Za-z0-9]+))")


def _inline_math(t):
    """把正文里的 X_{k,t} / R^eff_{jkt} 一类记号转成上下标，不动普通文字。"""
    def rep(m):
        out = m.group(1)
        for mm in SUBSUP.finditer(m.group(2)):
            tag = "sup" if mm.group(1) == "^" else "sub"
            out += f"<{tag}>{mm.group(2) or mm.group(3)}</{tag}>"
        return out
    return MATHTOK.sub(rep, t)


LINK = re.compile(r"\[([^\[\]]+)\]\((/[^()\s]+)\)")


def strongify(t):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _inline_math(html.escape(t)))
    return LINK.sub(r'<a class="xl" href="\2">\1</a>', s)


def parse(path):
    """→ (abstract, keywords, blocks)；blocks 元素为 (kind, payload)。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    abstract, keywords, blocks = "", "", []
    mode, buf, i, hn = None, [], 0, 0
    while i < len(lines):
        raw = lines[i].rstrip()
        line = raw.strip()
        i += 1
        if not line:
            continue
        if line == "摘要":
            mode = "abs"
            continue
        if line == "关键词":
            mode = "kw"
            continue
        if mode == "abs" and not line.startswith("#"):
            abstract = (abstract + line) if abstract else line
            continue
        if mode == "kw" and not line.startswith("#"):
            keywords = line
            mode = None
            continue
        mode = None
        if line.startswith("$$") and line.endswith("$$") and len(line) > 4:
            blocks.append(("fml", _tex(line[2:-2].strip())))
            continue
        if line.startswith("|"):
            buf = []
            j = i - 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                buf.append(lines[j].strip())
                j += 1
            i = j
            rows = []
            for r in buf:
                cells = [c.strip() for c in r.strip("|").split("|")]
                if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    continue
                rows.append(cells)
            blocks.append(("table", rows))
            continue
        if line.startswith(">"):
            blocks.append(("claim", strongify(line.lstrip("> ").strip())))
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            if lvl == 2:
                hn += 1
                blocks.append(("h2", (f"s{hn}", m.group(2))))
            else:
                blocks.append((f"h{lvl}", m.group(2)))
            continue
        blocks.append(("p", strongify(line)))
    return abstract, keywords, blocks


def render_body(blocks, ref_mode=True):
    out = []
    in_ref = False
    for kind, pl in blocks:
        if kind == "h2":
            sid, txt = pl
            in_ref = ref_mode and "参考文献" in txt
            out.append(f'<h2 id="{sid}">{html.escape(txt)}</h2>')
        elif kind in ("h3", "h4"):
            out.append(f"<{kind}>{html.escape(pl)}</{kind}>")
        elif kind == "fml":
            out.append(f'<div class="fml">{pl}</div>')
        elif kind == "claim":
            out.append(f'<div class="claim">{pl}</div>')
        elif kind == "table":
            head, *body = pl
            th = "".join(f"<th>{strongify(c)}</th>" for c in head)
            tr = "".join("<tr>" + "".join(f"<td>{strongify(c)}</td>" for c in r) + "</tr>"
                         for r in body)
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead>'
                       f"<tbody>{tr}</tbody></table></div>")
        else:
            out.append(f'<p class="ref">{pl}</p>' if in_ref else f"<p>{pl}</p>")
    return "".join(out)


def toc(blocks):
    items = [f'<a href="#{sid}">{html.escape(t)}</a>'
             for k, (sid, t) in ((k, pl) for k, pl in blocks if k == "h2")]
    return '<nav class="toc"><b>目录</b>' + "".join(items) + "</nav>"


# ═══════════════════ 视觉 ═══════════════════
PAGE_CSS = """
:root{--paper:#F5EFE0;--card:#FBF7ED;--ink:#23201A;--ink2:#5E5748;--seal:#9A2B26;
--brass:#A0651F;--line:rgba(35,32,26,.15);--rule:rgba(154,43,38,.16)}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.95}
a{color:inherit}
.readbar{position:sticky;top:0;z-index:20;background:rgba(245,239,224,.95);backdrop-filter:blur(10px);
border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;
gap:10px;padding:11px 22px;font-size:14px;flex-wrap:wrap}
.nav-back{text-decoration:none;color:var(--seal);font-weight:600}
.rb-modes{display:flex;gap:8px;flex-wrap:wrap}
.rb-btn{padding:6px 13px;border:1px solid var(--line);border-radius:4px;text-decoration:none;font-size:13px;color:var(--ink2);background:var(--card)}
.rb-btn.cur{background:var(--ink);color:#F5EFE0;border-color:var(--ink)}
.art{max-width:840px;margin:auto;padding:56px 24px 20px;text-align:center}
.art-series{color:var(--seal);letter-spacing:.3em;font-size:12px}
.art-title{font-size:clamp(28px,4.2vw,42px);line-height:1.38;margin:18px 0 14px;font-weight:700}
.art-subtitle{color:var(--ink2);font-size:16.5px;line-height:1.9;max-width:660px;margin:0 auto}
.art-meta{color:var(--ink2);font-size:13px;margin-top:18px;letter-spacing:.04em}
.wrap{max-width:780px;margin:auto;padding:6px 24px 40px}
.abstract{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--seal);
border-radius:6px;padding:19px 25px;margin:24px 0}
.abstract .lb{color:var(--seal);letter-spacing:.3em;font-size:13px;font-weight:700}
.abstract p{margin:9px 0 0;font-size:15px;line-height:1.95;text-align:justify}
.kw{font-size:14px;color:var(--ink2);margin:9px 0 0}
.scorebox{border:1px solid rgba(160,101,31,.42);border-left:3px solid var(--brass);border-radius:6px;
padding:14px 20px;margin:20px 0;font-size:15px;background:rgba(160,101,31,.05)}
.scorebox b{color:var(--brass)}
.scorebox p{margin:5px 0 0;font-size:13.5px;color:var(--ink2)}
.toc{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:16px 22px;margin:22px 0;font-size:14px}
.toc b{display:block;color:var(--seal);letter-spacing:.24em;font-size:12.5px;margin-bottom:9px}
.toc a{display:block;text-decoration:none;color:var(--ink2);padding:3px 0;border-bottom:1px dotted var(--rule)}
.toc a:last-child{border-bottom:0}
.toc a:hover{color:var(--seal)}
h2{font-size:22px;margin:44px 0 15px;padding:0 0 8px;border-bottom:2px solid var(--seal);line-height:1.5;scroll-margin-top:70px}
h3{font-size:18px;margin:30px 0 11px;color:var(--ink);padding-left:11px;border-left:3px solid var(--brass);line-height:1.55}
h4{font-size:16px;margin:22px 0 9px;color:var(--ink2)}
p{margin:0 0 15px;text-align:justify}
strong{color:var(--seal)}
.claim{background:#fff;border:1px solid var(--rule);border-left:4px solid var(--seal);border-radius:5px;
padding:15px 22px;margin:20px 0;font-size:16.5px;line-height:1.9}
.claim strong{color:var(--seal)}
.fml{margin:18px 0;padding:13px 16px;text-align:center;background:var(--card);
border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);font-size:16px;overflow-x:auto}
.fr{display:inline-block;vertical-align:middle;text-align:center;margin:0 3px}
.fr .fn{display:block;border-bottom:1px solid currentColor;padding:0 5px 1px}
.fr .fd{display:block;padding:1px 5px 0}
.ub{display:inline-block;text-align:center;margin:0 2px;vertical-align:middle}
.ub .ubt{display:block}
.ub .ubl{display:block;border-top:1px solid var(--brass);font-size:11px;color:var(--brass);padding-top:2px}
sup,sub{font-size:.72em}
.tw{overflow-x:auto;margin:20px 0}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--card)}
th,td{border:1px solid var(--line);padding:8px 11px;text-align:left;line-height:1.7;vertical-align:top}
th{background:rgba(154,43,38,.08);color:var(--seal);font-weight:700}
.xl{color:var(--seal);text-decoration:none;border-bottom:1px solid var(--rule);font-weight:600}
.ref{font-size:13.5px;padding-left:2em;text-indent:-2em;color:var(--ink2);margin:0 0 6px;text-align:left}
.endbox{text-align:center;border-top:1px solid var(--line);margin-top:50px;padding:34px 20px;color:var(--ink2)}
.endbox a{color:var(--seal);text-decoration:none;font-weight:600}
footer{text-align:center;border-top:1px solid var(--line);padding:28px;color:var(--ink2);font-size:12px}
@media(max-width:720px){.art{padding:38px 18px 16px}.wrap{padding:6px 18px 30px}.fml{font-size:14px}}
"""

PRINT_CSS = """
@page{size:A4}
body{font-family:"Noto Serif CJK SC","Noto Serif SC",serif;color:#23201A;font-size:10.5pt;line-height:1.82;margin:0}
.cover{text-align:center;padding-bottom:12pt;border-bottom:1.2pt solid #9A2B26;margin-bottom:15pt}
.eyebrow{color:#9A2B26;letter-spacing:.3em;font-size:7.8pt;margin-bottom:9pt}
h1{font-size:18pt;line-height:1.44;margin:0 0 8pt}
.sub{font-size:9.8pt;color:#5E5748;margin:0 auto 9pt;max-width:34em;line-height:1.7}
.by{font-size:9pt;color:#5E5748}.by b{color:#9A2B26}
.abs{background:#F3EEE3;border-left:3pt solid #9A2B26;padding:10pt 12pt;margin:0 0 10pt;font-size:9.3pt;line-height:1.72;text-align:justify}
.abs .lb{letter-spacing:.32em;font-weight:700}
.kw{font-size:9pt;color:#5E5748;margin:0 0 14pt}
h2{font-size:13pt;padding-bottom:4pt;border-bottom:1.6pt solid #9A2B26;margin:17pt 0 8pt;page-break-after:avoid}
h3{font-size:11pt;padding-left:6pt;border-left:2.6pt solid #A0651F;margin:12pt 0 6pt;page-break-after:avoid}
h4{font-size:10pt;color:#5E5748;margin:9pt 0 5pt;page-break-after:avoid}
p{text-indent:2em;text-align:justify;margin:0 0 7pt}
strong{color:#9A2B26}
.claim{border-left:2.6pt solid #9A2B26;background:#F7F2E8;padding:8pt 11pt;margin:9pt 0;font-size:10pt;page-break-inside:avoid}
.claim p{text-indent:0}
.fml{text-align:center;margin:9pt 0;padding:6pt 0;border-top:.6pt solid #D9C6BE;border-bottom:.6pt solid #D9C6BE;font-size:10pt;page-break-inside:avoid}
.fr{display:inline-block;vertical-align:middle;text-align:center;margin:0 2pt}
.fr .fn{display:block;border-bottom:.6pt solid #23201A;padding:0 3pt 1pt}
.fr .fd{display:block;padding:1pt 3pt 0}
.ub{display:inline-block;text-align:center;margin:0 1pt;vertical-align:middle}
.ub .ubt{display:block}
.ub .ubl{display:block;border-top:.6pt solid #A0651F;font-size:7pt;color:#A0651F}
sup,sub{font-size:.72em}
table{border-collapse:collapse;width:100%;font-size:8.6pt;margin:8pt 0;page-break-inside:avoid}
th,td{border:.6pt solid #9C948A;padding:4pt 5pt;text-align:left;line-height:1.55;vertical-align:top}
th{background:#F0E2DF;color:#9A2B26;font-weight:700}
.xl{color:#9A2B26;text-decoration:none}
.ref{text-indent:-1.6em;padding-left:1.6em;font-size:8.6pt;color:#4A4843;margin:0 0 3pt;text-align:left}
"""

READ_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 在线 PDF · SDE 经济学频道</title>
<style>html,body{{margin:0;height:100%;background:#23201A}}
header{{height:56px;background:#2E2A22;display:flex;align-items:center;justify-content:space-between;
padding:0 18px;font-family:"Songti SC","Noto Serif SC",serif;font-size:14px;
border-bottom:1px solid rgba(154,43,38,.5);color:#E8E1D2}}
header a{{color:#C98A4B;text-decoration:none}}
iframe{{width:100%;height:calc(100% - 56px);border:0;display:block}}</style></head>
<body><header><a href="index.html">‹ 返回网页长文</a><span>{pages} 页 · {author}</span>
<a href="{pdf}" download>⬇ 下载 PDF</a></header>
<iframe src="{pdf}#view=FitH"></iframe></body></html>"""


def render_page(a, abstract, keywords, blocks):
    kw = f'<p class="kw"><b>关键词：</b>{html.escape(keywords)}</p>' if keywords else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(a["title"])} · SDE 经济学频道 | SDE Universes</title>
<meta name="description" content="{html.escape(a["hook"][:155])}">
<meta name="sde:paper-weight" content="{a["weight"]}">
<meta property="og:title" content="{html.escape(a["title"])}">
<meta property="og:description" content="{html.escape(a["hook"][:155])}">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap">
<style>{PAGE_CSS}</style></head>
<body>
<div class="readbar">
  <a class="nav-back" href="/business/sde-economics/">‹ SDE 经济学频道</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{a["slug"]}.pdf" download>⬇ 下载 PDF</a>
    <a class="rb-btn" href="/business/">商业专栏</a>
  </div>
</div>
<header class="art">
  <div class="art-series">SDE 经济学频道 · 之{a["no"]}</div>
  <h1 class="art-title">{html.escape(a["title"])}</h1>
  <div class="art-subtitle">{html.escape(a["subtitle"])}</div>
  <div class="art-meta">作者 {AUTHOR} · {a["wan"]} · {a["pages"]} 页 · 发表于{PUBDATE_CN}</div>
</header>
<div class="wrap">
<div class="abstract"><span class="lb">摘 要</span><p>{strongify(abstract)}</p>{kw}</div>
<div class="scorebox"><b>SDE 创新智商：{a["score"]}</b>
<p>依五维加权评定（结构精确度 · 差异锐度 · 纠缠深度 · 不可还原性 · 可证伪性）。编辑评分，待独立复评。</p></div>
{toc(blocks)}
{render_body(blocks)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/business/sde-economics/">返回 SDE 经济学频道 →</a></p></div>
</div>
<footer>© 德麦国际 Demai International · SDE 经济学频道 · <a href="/">sdeuniverses.com</a></footer>
<script src="/wds-mode.js" defer></script>
</body></html>"""


def render_print(a, abstract, keywords, blocks):
    kw = f'<div class="kw"><b>关键词：</b>{html.escape(keywords)}</div>' if keywords else ""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html.escape(a["title"])}</title><style>{PRINT_CSS}</style></head><body>
<div class="cover"><div class="eyebrow">SDE UNIVERSES · S D E 经 济 学 频 道</div>
<h1>{html.escape(a["title"])}</h1><p class="sub">{html.escape(a["subtitle"])}</p>
<div class="by"><b>{AUTHOR}</b> 著　·　SDE 经济学频道 之{a["no"]}　·　{PUBDATE_CN}</div></div>
<div class="abs"><span class="lb">摘 要</span>　{strongify(abstract)}</div>
{kw}
{render_body(blocks)}</body></html>"""


def build_pdf(ph, pdf):
    subprocess.run(["wkhtmltopdf", "--encoding", "utf-8", "--page-size", "A4",
                    "--margin-top", "19", "--margin-bottom", "17",
                    "--margin-left", "18", "--margin-right", "18", "--quiet",
                    str(ph), str(pdf)], check=True)
    o = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True)
    m = re.search(r"Pages:\s+(\d+)", o.stdout)
    return int(m.group(1)) if m else 0


HUB_TPL = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SDE 经济学频道 · 商业专栏 | SDE Universes</title>
<meta name="description" content="SDE 经济学频道：把经济过程写成「在土壤中，经路径，成结构」的发生闭环，并追问一件被所有账本漏掉的事——这条路本身，这十年变了没有。">
<meta property="og:title" content="SDE 经济学频道">
<meta property="og:description" content="增长了多少、代价补了多少之外，还有第三件事：这条路本身变了没有。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap">
<style>
:root{{--paper:#F5EFE0;--card:#FBF7ED;--ink:#23201A;--ink2:#5E5748;--seal:#9A2B26;
--brass:#A0651F;--line:rgba(35,32,26,.15);--rule:rgba(154,43,38,.18)}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.9}}
a{{color:inherit}}
nav{{position:sticky;top:0;z-index:10;background:rgba(245,239,224,.95);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}}
.navin{{max-width:1100px;margin:auto;padding:13px 24px;display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;font-size:14px}}
.navin a{{text-decoration:none;color:var(--seal);font-weight:600}}
.hero{{min-height:560px;display:grid;place-items:center;text-align:center;padding:66px 22px;color:#F2EADA;position:relative;overflow:hidden;
background:radial-gradient(circle at 50% 32%,rgba(154,43,38,.30),transparent 40%),
radial-gradient(ellipse at 50% 100%,rgba(160,101,31,.22),transparent 48%),
linear-gradient(152deg,#1A1814,#332E25 58%,#23201A)}}
.hero:before{{content:"";position:absolute;inset:8% 8%;border:1px solid rgba(201,138,75,.22);transform:rotate(-.8deg)}}
.hero:after{{content:"";position:absolute;inset:0;opacity:.16;
background-image:repeating-linear-gradient(to bottom,transparent 0 33px,rgba(201,138,75,.5) 33px 34px)}}
.heroin{{position:relative;z-index:1;max-width:900px}}
.eyebrow{{font-size:12px;letter-spacing:.48em;color:#D19A62}}
.hero h1{{font-size:clamp(40px,7.4vw,74px);margin:20px 0 8px;line-height:1.12;text-shadow:0 7px 30px #0C0B09}}
.hero .en{{font-family:"Playfair Display",serif;font-size:clamp(13px,1.7vw,17px);letter-spacing:.16em;color:#C7B9A0;margin-bottom:16px}}
.hero p{{font-size:clamp(16px,2vw,21px);color:#E4DAC6;line-height:2}}
.stats{{display:flex;justify-content:center;gap:42px;margin-top:30px;flex-wrap:wrap}}
.stat b{{display:block;color:#D8A96A;font-size:28px}}
.stat span{{font-size:12px;letter-spacing:.16em;color:#BFB4A2}}
.wrap{{max-width:1100px;margin:auto;padding:62px 24px}}
.lead{{max-width:850px;margin:0 auto 30px;font-size:17.5px;line-height:2.12;text-align:justify}}
.lead:first-letter{{float:left;font-size:52px;line-height:.86;color:var(--seal);padding:9px 10px 0 0;font-weight:700}}
.thesis{{max-width:850px;margin:0 auto 52px;background:#fff;border:1px solid var(--rule);border-left:4px solid var(--seal);
border-radius:6px;padding:20px 26px;font-size:17px;line-height:1.95}}
.thesis b{{color:var(--seal)}}
.section-title{{text-align:center;margin-bottom:30px}}
.section-title small{{color:var(--brass);letter-spacing:.32em;font-size:12px}}
.section-title h2{{font-size:33px;margin:8px 0 0}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.paper{{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);
border-top:4px solid var(--seal);border-radius:7px;padding:26px;transition:.2s}}
.paper:hover{{transform:translateY(-4px);box-shadow:0 15px 36px rgba(35,32,26,.13)}}
.paper .num{{color:var(--brass);font-size:12px;letter-spacing:.14em}}
.paper h3{{font-size:22px;line-height:1.5;margin:9px 0;color:var(--ink)}}
.paper p{{color:var(--ink2);font-size:14px;margin:0;line-height:1.85}}
.paper .go{{display:inline-block;margin-top:14px;color:var(--seal);font-weight:700;font-size:13px}}
.modes{{margin-top:13px;display:flex;gap:8px;flex-wrap:wrap}}
.modes span{{font-size:12px;color:var(--ink2);border:1px solid var(--line);border-radius:4px;padding:3px 9px}}
.terms{{margin-top:56px;background:var(--card);border:1px solid var(--line);border-radius:7px;padding:26px 28px}}
.terms h3{{margin:0 0 6px;font-size:20px;color:var(--seal)}}
.terms .tl{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px 26px;margin-top:16px}}
.terms dt{{font-weight:700;color:var(--ink);font-size:15px}}
.terms dd{{margin:3px 0 0;font-size:14px;color:var(--ink2);line-height:1.8}}
.rulenote{{margin-top:26px;text-align:center;border:1px dashed var(--brass);border-radius:7px;padding:18px 20px;color:var(--ink2);font-size:14.5px}}
.rulenote b{{color:var(--brass)}}
.sisters{{margin-top:26px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center}}
.sisters a{{text-decoration:none;font-size:13.5px;padding:8px 16px;border:1px solid var(--line);border-radius:22px;color:var(--ink2);background:var(--card)}}
.sisters a:hover{{border-color:var(--seal);color:var(--seal)}}
footer{{text-align:center;border-top:1px solid var(--line);padding:30px;color:var(--ink2);font-size:12px}}
@media(max-width:760px){{.hero{{min-height:480px}}.grid,.terms .tl{{grid-template-columns:1fr}}.wrap{{padding:44px 18px}}.hero h1{{font-size:38px}}.stats{{gap:20px}}}}
</style></head><body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/business/">‹ 返回商业专栏</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">ECONOMIC GENERATIVICS</div>
<h1>SDE 经济学频道</h1>
<div class="en">The Genesis of Economies · Feedback, Soil, and Path</div>
<p>增长了多少，代价补了多少——<br>这两件事都被算得越来越准。<br>还有第三件：这条路本身，这十年变了没有。</p>
<div class="stats"><div class="stat"><b>{n}</b><span>频道文章</span></div>
<div class="stat"><b>{wan}万+</b><span>文字</span></div>
<div class="stat"><b>3</b><span>种阅读方式</span></div></div>
</div></header>
<main class="wrap">
<p class="lead">经济学有两套成熟的账：一套记产出，一套记代价。前者从国民收入核算长到今天，后者从绿色核算、自然资本与综合财富一路推进，都已经相当精细。本频道要加的是第三套账，它记的东西在前两套里都没有科目——路径。一个经济体选择用什么技术、在什么空间、以什么信贷结构、按什么规则去形成新的结构，这个「下一步往哪走」的选择规则，不是存量，也不是流量，因此任何资产负债表都装不下它。</p>
<div class="thesis">装不下的代价是具体的：存在一种增长，它的损耗被完整识别、被计量、被公开报告，修复预算逐年上升并接受审计，受损方获得补偿——<b>所有环节都在运转，唯独没有任何一个环节的职责是追问这条路径本身是否应当继续</b>。这种状态在现行的每一本账上都读数正常。本频道给它一个名字：<b>代偿增长</b>；并论证一件反直觉的事：在一段可以界定的区间里，增加修复投入不是让系统更安全，而是让它更脆弱。</div>
<section><div class="section-title"><small>ARTICLES · 2026</small><h2>频道文章</h2></div>
<div class="grid">{cards}</div></section>
<section class="terms"><h3>频道关键词</h3>
<p style="margin:0;color:var(--ink2);font-size:14.5px">本频道反复用到的几个词，先在这里给出短定义，读文章时不必回头。</p>
<dl class="tl">
<div><dt>二重回写</dt><dd>成果对条件的修复（土壤回写）与成果对路径的纠偏（路径回写）。两者不可相互替代——修得再多，路不改，仍是半个循环。</dd></div>
<div><dt>回写债</dt><dd>已经发生、尚未被任何账户确认的修复义务。它有承受者，因而有债权人；债权人常常是未来居民、劳动者身体与被削弱的社会关系。</dd></div>
<div><dt>代偿增长</dt><dd>修复与损耗同步放大、净额接近零、而路径的单位损耗强度不下降的增长状态。所有净额判据对它失明。</dd></div>
<div><dt>代偿陷阱</dt><dd>在路径不变的前提下，增加修复投入反而提高系统脆弱性的那段区间。由挤出转型、延迟退出、锁定累积与不可逆性四条机制造成。</dd></div>
<div><dt>路径回写弹性</dt><dd>损耗信号变强时，造成损耗的那条路径收缩多少。它是本频道唯一一个对象不是存量的指标，也是唯一能把代偿态识别出来的指标。</dd></div>
<div><dt>发生泡沫</dt><dd>可见估值与生成能力之间的裂隙。它比价格偏离更深一层：问的不是价格是否偏离基本面，而是基本面本身建立在什么条件上。</dd></div>
</dl></section>
<div class="rulenote"><b>频道规矩。</b>本频道每篇都必须写明它可以被什么推翻——具体到哪一个系数的符号、哪一组样本的比较。<br>
一个不能被数据杀死的经济学判断，不进这个频道。<br>
<span style="display:block;margin-top:12px;font-size:13.5px">这条规矩不是姿态。本频道的理论此前已被自己的检验击中过一次：
<a href="/creation/research-philosophy/writeback-deficit/" style="color:#9A2B26;font-weight:600">那次跨国回归的结果不支持它</a>，
相关主张已被撤回。开栏长文写在那次失败之后，并解释了失败与新预测之间的关系。</span></div>
<div class="sisters">
<a href="/creation/research-philosophy/writeback-deficit/">一次失败的证伪实验</a>
<a href="/business/">商业专栏 · 总目</a>
<a href="/business/from-students/">频道 · 来自学员专栏</a>
<a href="/column/discovery-vs-genesis-business/">商业：发现还是发生？</a>
<a href="/paradigm/">每日必读</a>
</div>
</main>
<footer>SDE 经济学频道 · 商业专栏 · SDE Universes · © 德麦国际 Demai International</footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    args = ap.parse_args()
    src = Path(args.src)
    tmp = Path("/tmp/econ_print")
    tmp.mkdir(exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    for a in ARTICLES:
        abstract, keywords, blocks = parse(src / f'{a["src"]}.md')
        chars = len(re.findall(r"[\u4e00-\u9fff]", (src / f'{a["src"]}.md').read_text(encoding="utf-8")))
        a["wan"] = f"约 {chars/10000:.1f} 万字"
        a["weight"] = max(1, round(chars / 10000 * 1.6))
        out = OUT / a["slug"]
        out.mkdir(parents=True, exist_ok=True)
        ph = tmp / f'{a["slug"]}.html'
        ph.write_text(render_print(a, abstract, keywords, blocks), encoding="utf-8")
        a["pages"] = build_pdf(ph, out / f'{a["slug"]}.pdf')
        page = render_page(a, abstract, keywords, blocks)
        for w in BANNED_META:
            assert w not in a["hook"] + a["title"] + a["subtitle"], f"元文案含学派术语 {w}"
        for tag in ("div", "header", "html", "body", "style", "footer", "table", "nav", "p", "h2", "h3"):
            o, c = page.count(f"<{tag}"), page.count(f"</{tag}>")
            assert o == c, f'{a["slug"]} <{tag}> 不配对 {o}/{c}'
        (out / "index.html").write_text(page, encoding="utf-8")
        (out / "read.html").write_text(READ_TPL.format(
            title=html.escape(a["title"]), author=AUTHOR,
            pages=a["pages"], pdf=f'{a["slug"]}.pdf'), encoding="utf-8")
        print(f'  {a["slug"]:24s} {chars:>6d}字 {a["pages"]:>3d}页 IQ{a["score"]} 权重{a["weight"]}')

    cards = "".join(
        f'<a class="paper" href="/business/sde-economics/{a["slug"]}/">'
        f'<span class="num">之{a["no"]} · {a["wan"]} · {a["pages"]} 页 · 创新智商 {a["score"]}</span>'
        f'<h3>{html.escape(a["title"])}</h3><p>{html.escape(a["hook"])}</p>'
        f'<div class="modes"><span>📖 长文</span><span>📄 在线 PDF</span><span>⬇ 下载</span></div>'
        f'<span class="go">阅读全文 →</span></a>' for a in ARTICLES)
    total = sum(int(re.search(r"([\d.]+)", a["wan"]).group(1).replace(".", "")) for a in ARTICLES) / 10
    (OUT / "index.html").write_text(HUB_TPL.format(
        n=len(ARTICLES), wan=f"{total:.0f}", cards=cards), encoding="utf-8")

    (ROOT / "tools" / "sde_econ_report.json").write_text(json.dumps(
        {"articles": [{k: a[k] for k in ("no", "slug", "title", "subtitle", "hook",
                                         "wan", "pages", "score", "weight")} for a in ARTICLES]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f'\nSDE 经济学频道建成 · {len(ARTICLES)} 篇 · '
          f'{sum(a["pages"] for a in ARTICLES)} 页 · 约 {total:.1f} 万字')


if __name__ == "__main__":
    main()
