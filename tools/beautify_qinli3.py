# -*- coding: utf-8 -*-
"""秦莉三篇 · 页面重制。

改造点（不动作者正文一个字，只改呈现）：
  1. 恢复摘要与关键词——原渲染器解析了却没输出，网页版整块丢失（PDF 版一直有）
  2. 签名元素「对手榜」——这三篇的价值全在它们各自画出的那条分离线，
     把它渲成看得见的东西：左侧本文概念，一道细线，右侧被切过的近邻。
     数据来自论文自己点名的对手，不是装饰
  3. 章节目录——两万到三万四千字的长读需要，用 <details> 折叠，零 JS
  4. 阅读进度条——顶部 2px，尊重 prefers-reduced-motion
  5. 编辑增补改用羊皮灰而非金色 + 左侧竖线 + 小标签：
     它是另一个说话人，视觉上就该是另一个声音，而不是同一家族里的一个盒子

用法： python3 tools/beautify_qinli3.py --src /home/claude/last3
"""
import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qinli3_meta import PAPERS, STUDENTS, PUBDATE_CN
from qinli3_supp import SUPPLEMENTS, REFERENCES
import publish_qinli3 as P          # 复用改姓、清理、解析，保证与已发版本同源

ROOT = Path(__file__).resolve().parents[1]
STU = ROOT / "public" / "students"

# 各篇正面对勘过的近邻（取自论文自身点名者）+ 编辑增补新补的那一组
OPPONENTS = {
    "forced-reclamation": {
        "self": "强制开荒",
        "own": [("伊瑟尔", "空白填充"), ("什克洛夫斯基", "陌生化"), ("伽达默尔", "游戏"),
                ("梅洛-庞蒂", "身体意向性"), ("杜威", "一个经验"), ("布莱希特", "间离效果")],
        "added": [("巴特", "可写文本"), ("艾柯", "开放的作品"), ("朗西埃", "解放的观众")],
    },
    "overflow-genesis": {
        "self": "溢出性生成",
        "own": [("顿悟", "解法预先存在"), ("创造性转化", "改编合法性"), ("作者论", "风格稳定"),
                ("默会知识", "不可言传"), ("皮亚杰", "顺应"), ("转化性学习", "框架重组")],
        "added": [("创伤—创造", "先在事件的加工")],
    },
    "twin-correctness": {
        "self": "孪生正确",
        "own": [("流畅性启发", "加工流畅→正确感"), ("自我欺骗", "有动机的偏离"),
                ("埃斯波西托", "免疫范式"), ("马尔库塞", "去升华"),
                ("斯坦尼方法派", "真实性"), ("德雷福斯", "专家直觉")],
        "added": [("萨特", "自欺 / mauvaise foi")],
    },
}

EXTRA_CSS = """
/* ── 阅读进度：顶部一线，长读时知道自己在哪 ───────────────── */
#prog{position:fixed;top:0;left:0;height:2px;width:0;z-index:60;
  background:linear-gradient(90deg,var(--gold),var(--gold2));transition:width .12s linear}

/* ── 摘要：原渲染器丢了这一块，恢复并给它应有的分量 ───────── */
.abs{margin:26px 0 4px;padding:24px 28px;background:linear-gradient(158deg,#1C1712,#141009);
  border-left:3px solid var(--gold);position:relative}
.abs .lb{font-size:11.5px;letter-spacing:.44em;color:var(--gold2);display:block;margin-bottom:12px}
.abs p{margin:0;text-indent:0;font-size:16.5px;line-height:2.0;color:#E4DCC6;text-align:justify}
.kw{margin:14px 0 0;font-size:14px;color:var(--muted);letter-spacing:.04em;text-indent:0}
.kw b{color:var(--gold);font-weight:400;letter-spacing:.16em}

/* ── 签名元素 · 对手榜：把这篇论文画出的那条分离线渲成看得见的 ── */
.cut{margin:30px 0 6px;border:1px solid rgba(181,134,15,0.22);background:#120E0A}
.cut .cap{font-size:11px;letter-spacing:.42em;color:var(--gold2);padding:14px 20px 0}
.cut .row{display:grid;grid-template-columns:minmax(0,auto) 1px minmax(0,1fr);
  gap:0 22px;align-items:stretch;padding:14px 20px 18px}
.cut .me{align-self:center;font-size:19px;font-weight:800;color:#F2ECDC;letter-spacing:.03em;
  white-space:nowrap;padding-right:4px}
.cut .sep{background:linear-gradient(180deg,transparent,var(--gold) 22%,var(--gold) 78%,transparent)}
.cut ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px 10px}
.cut li{font-size:13px;color:#C8BC9C;border:1px solid rgba(181,134,15,0.26);padding:5px 11px;
  line-height:1.5;background:rgba(181,134,15,0.05)}
.cut li i{font-style:normal;color:var(--muted);margin-left:7px;font-size:12px}
.cut li.add{border-style:dashed;border-color:rgba(142,134,116,0.5);color:#A9A18C;
  background:rgba(142,134,116,0.06)}
.cut .foot{font-size:12.5px;color:var(--muted);padding:0 20px 16px;line-height:1.8}
.cut .foot b{color:#A9A18C;font-weight:400}
@media(max-width:600px){.cut .row{grid-template-columns:1fr;gap:12px}
  .cut .sep{height:1px;background:linear-gradient(90deg,var(--gold),transparent)}
  .cut .me{white-space:normal}}

/* ── 目录：长读的落脚点，纯 CSS 折叠 ─────────────────────── */
.toc{margin:24px 0 8px;border:1px solid rgba(181,134,15,0.20);background:#120E0A}
.toc>summary{cursor:pointer;list-style:none;padding:13px 20px;font-size:12.5px;
  letter-spacing:.32em;color:var(--gold2)}
.toc>summary::-webkit-details-marker{display:none}
.toc>summary::after{content:"＋";float:right;letter-spacing:0;color:var(--muted)}
.toc[open]>summary::after{content:"－"}
.toc ol{margin:0;padding:2px 22px 18px 42px;columns:2;column-gap:30px}
.toc li{font-size:14px;line-height:2.0;color:#C8BC9C;break-inside:avoid}
.toc a{color:#C8BC9C}
.toc a:hover{color:var(--gold2)}
@media(max-width:640px){.toc ol{columns:1}}

/* ── 正文节奏 ────────────────────────────────────────────── */
.wrap h2[id]{scroll-margin-top:70px}
.wrap article>p:first-of-type{text-indent:0}

/* ── 编辑增补：另一个说话人，用羊皮灰而不是金色 ──────────── */
.suppwrap{margin:56px 0 0;border-top:1px solid rgba(142,134,116,0.34);padding-top:6px}
.supphead{font-size:12px;letter-spacing:.40em;color:#A9A18C;margin:18px 0 8px;
  border:0;padding:0}
.supptip{font-size:14px;color:var(--muted);line-height:1.95;text-indent:0;margin:0 0 6px;
  max-width:40em}
.supp{border:0;border-left:2px solid rgba(142,134,116,0.55);background:transparent;
  border-radius:0;padding:2px 0 2px 22px;margin:26px 0}
.supp h2{font-size:17.5px;color:#CFC6AE;border:0;padding:0;margin:0 0 10px;
  font-weight:700;letter-spacing:.02em}
.supp h2::before{content:"编辑增补";display:block;font-size:10.5px;letter-spacing:.34em;
  color:#8E8674;font-weight:400;margin-bottom:7px}
.supp p{text-indent:0;font-size:16px;line-height:2.0;color:#CEC5AD;text-align:justify;margin:0}

/* ── 参考文献 ────────────────────────────────────────────── */
.ref{font-size:14px;padding-left:2em;text-indent:-2em;color:#B3A98D;line-height:1.85;margin:0 0 7px}
.refhead{font-size:12px;letter-spacing:.36em;color:var(--gold2);border:0;padding:0;margin:34px 0 12px}
.refhead.ed{color:#A9A18C}

/* ── 分数条 ──────────────────────────────────────────────── */
.scorebox{border:0;border-left:3px solid var(--gold);background:linear-gradient(158deg,#1B1611,#130F0A);
  padding:16px 24px;margin:22px 0 0;font-size:14.5px;color:#C8BC9C;line-height:1.9}
.scorebox b{color:var(--gold2);font-size:15px;letter-spacing:.03em}
.scorebox p{margin:6px 0 0;text-indent:0;font-size:13.5px;color:var(--muted)}

.endbox{text-align:center;border-top:1px solid rgba(181,134,15,0.24);margin-top:52px;
  padding:38px 20px;color:var(--muted);font-size:14px}
.endbox a{color:var(--gold)}
@media(prefers-reduced-motion:reduce){#prog{transition:none}*{scroll-behavior:auto}}
"""


def parse_fixed(paper, lines):
    """修正版解析：原版跳标题时取前 8 行里最后一个含关键词的行，
    而这些论文的摘要里往往会提到自己的概念名（“本文将这一事件命名为 X”），
    于是整段摘要被当成标题跳掉，网页丢失、PDF 静默回退到 hook。
    改为：只跳真正像标题的行（短、且在摘要之前），遇到「摘要」立即停止扫描。"""
    key = paper["title"].split("：", 1)[0].split("——", 1)[0]
    start = 0
    for i, line in enumerate(lines[:6]):
        if re.match(r'^\*{0,2}摘\s*[　]?\s*要', line) or line.startswith("关键词"):
            break
        if (key in line or line.startswith("作者：")) and len(line) < 90:
            start = i + 1
    return P.parse(paper, ["__TITLE_STRIPPED__"] + lines[start:]) if False else _parse_body(paper, lines[start:])


def _parse_body(paper, lines):
    abstract = keywords = ""
    collecting = False
    blocks, mode = [], "body"
    for line in lines:
        if re.fullmatch(r"[-—─]{2,}|---|（全文完）", line):
            continue
        if re.fullmatch(r"(参考文献|References|REFERENCES)[:：]?", line):
            mode = "ref"; blocks.append(("h2", "参考文献")); continue
        if re.fullmatch(r"(注释|注)[:：]?", line):
            mode = "note"; blocks.append(("h2", "注释")); continue
        if mode == "body":
            m = re.match(r'^\*{0,2}摘\s*[　]?\s*要\*{0,2}[：:\s　]*(.*)$', line)
            if m and not abstract:
                # 摘要可能跨多段（本批 Q2 即为两段），收到关键词 / 分隔线 / 章节标题为止
                abstract = m.group(1).strip() or "__NEXT__"
                collecting = True
                continue
            if collecting:
                if (line.startswith("关键词") or re.match(r'^第?[一二三四五六七八九十]+[、.．]', line)
                        or re.fullmatch(r"[-—─]{2,}|---", line)):
                    collecting = False
                    if abstract == "__NEXT__":
                        abstract = ""
                    # 不 continue，让本行继续走后面的关键词 / 标题分支
                else:
                    abstract = line if abstract == "__NEXT__" else abstract + line
                    continue
            m = re.match(r'^\*{0,2}关键词\*{0,2}[：:\s　]*(.*)$', line)
            if m and not keywords:
                keywords = m.group(1).strip() or "__NEXT__"; continue
            if keywords == "__NEXT__":
                keywords = line; continue
        is_h = mode == "body" and len(line) < 72 and (
            bool(re.match(r'^#{1,3}\s', line))
            or bool(re.match(r'^第?[一二三四五六七八九十]+[、.．]', line))
            or bool(re.match(r'^\d+(?:\.\d+)*[、.\s]\S', line))
            or line in ("引言", "结论", "余论", "证伪条件", "证伪条件与边界"))
        line = re.sub(r'^#{1,3}\s*', "", line)
        blocks.append(("h2" if is_h else ("ref" if mode == "ref" else "p"), line))
    return abstract, keywords, blocks


def cut_block(slug):
    o = OPPONENTS[slug]
    own = "".join(f'<li>{html.escape(n)}<i>{html.escape(t)}</i></li>' for n, t in o["own"])
    add = "".join(f'<li class="add">{html.escape(n)}<i>{html.escape(t)}</i></li>' for n, t in o["added"])
    return f"""<div class="cut">
  <div class="cap">这 把 刀 切 过 的 近 邻</div>
  <div class="row">
    <div class="me">{html.escape(o["self"])}</div>
    <div class="sep"></div>
    <ul>{own}{add}</ul>
  </div>
  <p class="foot">实线为作者正文中正面对勘者；<b>虚线为编辑增补补上的最近邻</b>——评审记下的扣分点正在这里。</p>
</div>"""


def toc_block(blocks):
    """只取一级章（一、二、三…），子节不进目录。"""
    items = []
    for k, (tag, line) in enumerate(blocks):
        if tag == "h2" and re.match(r'^[一二三四五六七八九十]+、', line):
            items.append((f"s{k}", line))
    if len(items) < 3:
        return "", {}
    lis = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in items)
    return (f'<details class="toc"><summary>目 录 · 全文 {len(items)} 章</summary>'
            f'<ol>{lis}</ol></details>'), dict(items)


def render(paper, css, abstract, keywords, blocks):
    st = STUDENTS[paper["student"]]
    toc, ids = toc_block(blocks)
    rev = {t: i for i, t in ids.items()}
    body = []
    for tag, line in blocks:
        if tag == "ref":
            body.append(f'<p class="ref">{P.strongify(line)}</p>')
        elif tag == "h2" and line in rev:
            body.append(f'<h2 id="{rev[line]}">{P.strongify(line)}</h2>')
        else:
            body.append(f"<{tag}>{P.strongify(line)}</{tag}>")

    supp = ['<div class="suppwrap">',
            '<h2 class="supphead">深 化 增 补</h2>',
            '<p class="supptip">以下四节为编辑增补，针对评审记下的扣分点定点补强，'
            '与作者正文分开标注，不改动作者原有判断与结构。</p>']
    for h, para in SUPPLEMENTS[paper["slug"]]:
        supp.append(f'<section class="supp"><h2>{html.escape(h)}</h2><p>{P.strongify(para)}</p></section>')
    supp.append('<h2 class="refhead ed">编 辑 增 补 所 依 据 的 核 验 文 献</h2>')
    for label, url in REFERENCES[paper["slug"]]:
        inner = (f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
                 if url else html.escape(label))
        supp.append(f'<p class="ref">{inner}</p>')
    supp.append("</div>")

    slug, sl = paper["slug"], paper["student"]
    kw = (f'<p class="kw"><b>关键词</b>　{html.escape(keywords)}</p>' if keywords else "")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(paper["title"])} · {st["name"]} · SDE 学员专栏</title>
<meta name="description" content="{html.escape(paper["hook"])}">
<style>{css}{EXTRA_CSS}</style></head>
<body>
<div id="prog"></div>
<div class="readbar">
  <a class="nav-back" href="/students/{sl}/works/">‹ {st["name"]} · 全部作品</a>
  <div class="rb-modes">
    <span class="rb-btn cur">📖 长文阅读</span>
    <a class="rb-btn" href="read.html">📄 在线 PDF</a>
    <a class="rb-btn" href="{slug}.pdf" download>⬇ 下载 PDF</a>
  </div>
</div>
<header class="art">
  <div class="art-series">学员专栏 · {st["name"]} · {html.escape(paper["kind"])}</div>
  <h1 class="art-title">{html.escape(paper["title"])}</h1>
  <div class="art-subtitle">{html.escape(paper["subtitle"])}</div>
  <div class="art-meta">作者 {st["name"]} · {st["role"]} · 约 {paper["wan"]} 万字 · 发表于{PUBDATE_CN} · 深化增补版</div>
</header>
<div class="wrap">
<div class="abs"><span class="lb">摘 要</span><p>{P.strongify(abstract or paper["hook"])}</p></div>
{kw}
{cut_block(slug)}
{toc}
<div class="scorebox"><b>SDE 创新智商 {paper["old_score"]} → {paper["score"]}</b>
<p>提升集中于补上被放跑的最近邻理论、核心命题的操作化与可执行的证伪设计。提升后分数为编辑自评，待独立复评。</p></div>
<article>{''.join(body)}</article>
{''.join(supp)}
<div class="endbox"><p>三种读法 · 网页长文 · 在线 PDF 翻页 · PDF 下载</p>
<p><a href="/students/{sl}/works/">返回 {st["name"]} 全部作品 →</a></p></div>
</div>
<script>
(function(){{
  var bar=document.getElementById('prog');
  if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches){{bar.style.display='none';return;}}
  var tick=false;
  function upd(){{
    var d=document.documentElement, max=d.scrollHeight-d.clientHeight;
    bar.style.width=(max>0?(d.scrollTop/max*100):0)+'%'; tick=false;
  }}
  addEventListener('scroll',function(){{if(!tick){{tick=true;requestAnimationFrame(upd);}}}},{{passive:true}});
  upd();
}})();
</script>
<script src="/wds-mode.js" defer></script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True)
    src = Path(ap.parse_args().src)
    css = P.skeleton_css("qin-li")   # 直接读她自己既有论文页的 <style>
    CITED = "《古典汉语审美发生学》"
    for paper in PAPERS:
        sid = paper["src"]
        lines = [P.rename(x) for x in P.apply_cleanup(sid, P.load_source(src, sid))]
        paper["title"] = P.rename(paper["title"])
        abstract, keywords, blocks = parse_fixed(paper, lines)
        paper["wan"] = f'{sum(len(t) for _, t in blocks) / 10000:.1f}'
        page = render(paper, css, abstract, keywords, blocks)
        probe = page.replace(CITED, "《…》")
        leaked = [w for w in ("发生学", "发现学", "本体论", "显露", "纠缠", "裂缝") if w in probe]
        assert not leaked, f"{sid} 招牌词残留: {leaked}"
        assert len(abstract) > 60, f"{sid} 摘要未解析出（得到 {len(abstract)} 字）"
        assert page.count("<html") == 1 and page.count("</html>") == 1
        out = STU / paper["student"] / paper["slug"] / "index.html"
        out.write_text(page, encoding="utf-8")
        print(f'  {paper["slug"]:<22} 摘要 {len(abstract):>4}字 · 关键词 {"有" if keywords else "无"}'
              f' · 目录 {page.count("<li><a href=")} 章 · 对手 {len(OPPONENTS[paper["slug"]]["own"])}+{len(OPPONENTS[paper["slug"]]["added"])}')


if __name__ == "__main__":
    main()
