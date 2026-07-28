# -*- coding: utf-8 -*-
"""学科通融专栏 /confluence/ · 建文章页 + PDF + 三种读法 + 专栏索引。

与「每日必读」的分工是硬的：
  · 每日必读 撞的是站内学员论文
  · 学科通融 撞的是站外不同学科的理论体系（须联网检索、须给出真实出处）
两栏共用同一套规矩：三家必须分属不同学科、必须正面打架、
撞出来的判断必须任一家单独看不到、全文零术语、文末交出处与作废数。
版式沿用每日必读，保持全站一致。
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"
TPL = ROOT / "public" / "paradigm" / "taken-out" / "index.html"
PUBDATE = "2026年7月27日"

PAPERS = [{
    "slug": "before-measurement",
    "src": Path("/home/claude/confluence/before-measurement.md"),
    "title": "认不出来的东西，争不出结果",
    "sub": "为什么有些架吵一百年也吵不完，而且吵的人全都在认真做实验",
    "score": 155,
    "cross": "意识科学 × 代谢医学 × 人工智能评估",
    "no": "之二",
    "deck": ("三场架正在打，凶到其中一场有一百多人联名说对方不算科学。"
             "一场吵人为什么有意识，一场吵人为什么会胖，一场吵机器是不是真在思考。"
             "把三场架的形状画出来会看到同一个东西：双方都同意发生了什么，"
             "分歧在于这件事该被算作什么——而这一步在任何测量开始之前就已经做完了，"
             "做的时候手上一份数据也没有。本文由此给出一条判断、三个可随身带的问题、"
             "十一个行当里的同一件事，以及四条可以让自己失败的判据。"),
    "clash": ("第一场里双方事先签字接受被推翻，结果两边核心预测都没活下来，两边都不认输；"
              "第二场把因果箭头整个掉了头——一边说吃多了才胖，一边说脂肪被锁进去才导致吃多；"
              "第三场同一次停止输出，一边读作能力崩溃，一边读作明智止损，"
              "而反驳论文的共同作者是一个模型本身。"),
    "sources": [
        ("意识科学 · 神经科学与心灵哲学",
         "全局神经工作空间理论对阵整合信息理论 —— Cogitate 预注册对抗实验，《Nature》2025，642(8066):133-142",
         "https://www.nature.com/articles/s41586-025-08888-1",
         "两百五十六名参与者、三种脑成像、中立第三方主持，双方事先写好什么算自己被推翻；"
         "结果两边的核心预测都没活下来，而两边都保留了「被测的操作方式不等于理论本身」这个退路。"),
        ("代谢医学 · 肥胖病因学",
         "能量平衡模型对阵碳水化合物-胰岛素模型 —— 因果方向的反转",
         "https://royalsocietypublishing.org/rstb/article/378/1888/20220211/109323/Carbohydrate-insulin-model-does-the-conventional",
         "同一个观察事实——胖的人吃得多——一边读作原因，一边读作结果。"
         "而中立的评估指出，两套模型在它们想要解释的东西上根本不是同一件事。"),
        ("人工智能 · 推理能力评估",
         "《思考的幻觉》对阵《思考的幻觉的幻觉》—— 同一批数据的两种读法",
         "https://arxiv.org/html/2507.01231v1",
         "一边读作推理能力的固有崩溃，一边读作输出格子塞满了；"
         "改掉输出方式之后，原来「完全失败」的十五盘汉诺塔被正确解出。"),
    ],
}]


def strongify(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", s)   # 期刊名用斜体
    return s


def md_to_html(md):
    out, para, li, toc, n = [], [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    def flush_li():
        if li:
            out.append("<ul>" + "".join(f"<li>{strongify(x)}</li>" for x in li) + "</ul>")
            li.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); flush_li(); continue
        if line.strip() == "---":
            flush(); flush_li(); out.append("<hr>"); continue
        if line.startswith("- "):
            flush(); li.append(line[2:].strip()); continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush(); flush_li()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 1:
                continue
            if lvl == 2:
                n += 1
                out.append(f'<h2 id="s{n}">{strongify(txt)}</h2>')
                toc.append((f"s{n}", txt))
            else:
                out.append(f"<h{lvl}>{strongify(txt)}</h{lvl}>")
            continue
        para.append(line.strip())
    flush(); flush_li()
    return "".join(out), toc


def build_page(p, body, toc, pages):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f'<title>{p["title"]}——{p["sub"]} · 学科通融 | SDE Universes</title>', t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(p["deck"][:190], quote=True) + m.group(2), t)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {p["no"]} · {html.escape(p["cross"])}</div>', t, flags=re.S)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{p["title"]}</h1>', t, flags=re.S)
    t = re.sub(r'<p class="art-sub">.*?</p>', f'<p class="art-sub">{p["sub"]}</p>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 2.4 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(p["deck"])}</div>', t, flags=re.S)
    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)
    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = t[:i] + "\n" + body + "\n" + t[j:]
    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{html.escape(g)}</div></a>'
        for k, ti, u, g in p["sources"])
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三个学科的理论体系撞成</div>'
               f'<p class="sd">{strongify(p["clash"])}　'
               f'三家均为站外的公开文献，链接直达原始出处，可自行核对。</p>{ones}</div>\n', t, flags=re.S)
    t = t.replace("‹ 典范文专栏", "‹ 学科通融").replace("返回典范文专栏 →", "返回学科通融 →")
    t = t.replace("典范文专栏 · 作者 Claude ·", "学科通融 · 作者 王德生 ＋ Claude ·")
    assert t.count("<html") == 1 and t.count("</html>") == 1
    for w in ("发生学", "本体论", "存在论", "显露", "纠缠", "裂缝", "金点子", "回写"):
        assert w not in t, f"术语残留 {w}"
    return t


def build_print(p, body):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{p["title"]}</title>
<style>@page{{size:A4;margin:20mm 18mm}}
body{{font-family:"Noto Serif CJK SC","Source Han Serif SC",serif;font-size:11.5pt;line-height:1.85;color:#1a1a1a}}
h1{{font-size:21pt;margin:0 0 6pt;text-align:center}}
.sub{{text-align:center;font-size:12pt;color:#555;margin:0 0 4pt}}
.by{{text-align:center;font-size:10.5pt;color:#666;margin:0 0 18pt}}
h2{{font-size:14pt;margin:20pt 0 8pt;border-bottom:1px solid #ccc;padding-bottom:4pt}}
h3{{font-size:12.5pt;margin:14pt 0 6pt}}
p{{margin:0 0 9pt;text-align:justify}} hr{{border:0;border-top:1px solid #ddd;margin:14pt 0}}
.src{{border:1px solid #bbb;padding:10pt 12pt;margin:0 0 16pt;font-size:10.5pt;background:#fafafa}}
.src ol{{margin:6pt 0;padding-left:16pt}}</style></head><body>
<h1>{p["title"]}</h1><div class="sub">{p["sub"]}</div>
<div class="by">王德生 ＋ Claude　·　{PUBDATE}　·　SDE Universes 学科通融 · {p["no"]}</div>
<div class="src"><b>本篇由三个学科的理论体系撞成</b>（{p["cross"]}）<ol>{''.join(
    f'<li>{k}：{ti}　—— {g}</li>' for k, ti, u, g in p["sources"])}</ol>{strongify(p["clash"])}</div>
{body}</body></html>"""


def build_index(built):
    tpl = (ROOT / "public" / "paradigm" / "index.html").read_text(encoding="utf-8")
    head = tpl[:tpl.index("<body")]
    assert head.count("<html") == 1, "模板头已含 html 标签，不要再加前缀"
    head = re.sub(r"<title>.*?</title>", "<title>学科通融 · 跨学科理论体系碰撞 | SDE Universes</title>", head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m.group(1) + "把三个分属不同学科、观点互相冲突的理论体系放在一起撞，"
                  "撞出来的那条判断单独成文。三家均为站外公开文献，链接直达原始出处。" + m.group(2), head)
    cards = ""
    for p, wan, pages in built:
        ones = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                       for k, ti, u, g in p["sources"])
        cards += (f'<div class="item"><div class="n">之一 · 三学科交叉：{html.escape(p["cross"])}</div>'
                  f'<h2><a href="/confluence/{p["slug"]}/">{html.escape(p["title"])}</a></h2>'
                  f'<p class="sub">{html.escape(p["sub"])}</p>'
                  f'<p class="hk">{html.escape(p["deck"])}</p>'
                  f'<div class="trio">{ones}</div>'
                  f'<a class="rdmore" href="/confluence/{p["slug"]}/">读全文 →</a>'
                  f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · '
                  f'作者 王德生 ＋ Claude · 发表于{PUBDATE} · 三家来源均为站外公开文献</div></div>\n')
    return f"""{head}
<body>
<nav><div class="navin"><a href="/">SDE Universes</a><a href="/paradigm/">每日必读 →</a></div></nav>
<header class="hero"><div class="heroin">
<div class="eyebrow">CONFLUENCE · CROSS-DISCIPLINE</div>
<h1>学科通融</h1>
<p>每一篇，都是三个分属不同学科、且互相冲突的理论体系撞在一起之后剩下的东西。</p>
<div class="how"><span>三家来自不同学科</span><span>三家必须互相打架</span><span>来源全在站外，链接可核对</span></div>
</div></header>
<main class="wrap">
<p class="lead">这个专栏与「每日必读」是一对：那一栏撞的是站内学员的论文，这一栏撞的是站外不同学科的理论体系。
做法只有一件——先在公开文献里找到三个分属不同学科、而且在同一个问题上给出互相排斥答案的理论体系，
把它们各自最承重的判断拆出来两两去撞；只有当两个判断在同一个问题上互相顶住、
顶出一个任何一家单独都看不见的东西时，才算数。</p>
<p class="rule">这个专栏由王德生博士定题、判方向，Claude 执行检索、碰撞与成文，因此每篇署王德生 ＋ Claude。
与「每日必读」不同的是，这一栏的三个来源全部在站外，每一家都给出可以直接点开核对的原始出处——
因为撞的是别人的理论，把出处交清楚是最低限度的规矩。全文不使用任何学派术语，普通读者可一路读下来；
每篇都在文中交出可以让自己失败的判据，文末记着这一次作废了多少条。</p>
<hr class="sep">
{cards}
</main>
<footer>学科通融 · 作者 王德生 ＋ Claude · © 德麦国际 Demai International</footer>
</body></html>"""


def main():
    CF.mkdir(exist_ok=True)
    built = []
    for p in PAPERS:
        body, toc = md_to_html(p["src"].read_text(encoding="utf-8"))
        d = CF / p["slug"]; d.mkdir(exist_ok=True)
        pf = d / "_p.html"; pf.write_text(build_print(p, body), encoding="utf-8")
        pdf = d / f'{p["slug"]}.pdf'
        subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "--encoding", "utf-8",
                        "--footer-center", "[page]", "--footer-font-size", "9", str(pf), str(pdf)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pf.unlink()
        pages = int(subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
                    .stdout.split("Pages:")[1].split()[0])
        (d / "index.html").write_text(build_page(p, body, toc, pages), encoding="utf-8")
        rd = (ROOT / "public" / "paradigm" / "taken-out" / "read.html").read_text(encoding="utf-8")
        rd = rd.replace("/paradigm/taken-out", f'/confluence/{p["slug"]}') \
               .replace("taken-out", p["slug"]).replace("一拿出来，就不是它了", p["title"]) \
               .replace("典范文专栏", "学科通融")
        (d / "read.html").write_text(rd, encoding="utf-8")
        n = len(re.sub(r"<[^>]+>", "", body))
        built.append((p, round(n / 10000, 1), pages))
        print(f'  {p["slug"]}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · 来源 {len(p["sources"])} 家')
    idx = CF / "index.html"
    if idx.exists() and "measurable-face" in idx.read_text(encoding="utf-8"):
        old = idx.read_text(encoding="utf-8")
        for p, wan, pages in built:
            if f'/confluence/{p["slug"]}/' in old:
                continue
            ones = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                           for k, ti, u, g in p["sources"])
            card = (f'<div class="item"><div class="n">{p["no"]} · 三学科交叉：{html.escape(p["cross"])}</div>'
                    f'<h2><a href="/confluence/{p["slug"]}/">{html.escape(p["title"])}</a></h2>'
                    f'<p class="sub">{html.escape(p["sub"])}</p>'
                    f'<p class="hk">{html.escape(p["deck"])}</p>'
                    f'<div class="trio">{ones}</div>'
                    f'<a class="rdmore" href="/confluence/{p["slug"]}/">读全文 →</a>'
                    f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · '
                    f'作者 王德生 ＋ Claude · 发表于{PUBDATE} · 三家来源均为站外公开文献</div></div>\n')
            old = old.replace("</main>", card + "</main>", 1)
        idx.write_text(old, encoding="utf-8")
        print("  已并入既有索引")
    else:
        idx.write_text(build_index(built), encoding="utf-8")
    print(f"学科通融建成：/confluence/ · {len(built)} 篇")


if __name__ == "__main__":
    main()
