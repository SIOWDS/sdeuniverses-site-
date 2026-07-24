from __future__ import annotations

import html
import io
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"E:\六路径方法论入门_学术定稿版_V3_2026.pdf")
ART = ROOT / "tmp" / "six-paths-book" / "cover-art.png"
OUT = ROOT / "public" / "books" / "m" / "52"
COVERS = ROOT / "public" / "books" / "covers"
PDF_NAME = "Six-Path-Methodology-Introduction.pdf"
TITLE = "六路径方法论入门"
SUBTITLE = "从三维发生学到知识智能体的理论、诊断与技术应用"
ISBN = "978-1-970820-65-2"


def font(path: str, size: int):
    return ImageFont.truetype(path, size)


def fit_text(draw, text, max_width, font_path, start_size, min_size=28):
    for size in range(start_size, min_size - 1, -2):
        f = font(font_path, size)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
    return font(font_path, min_size)


def draw_centered(draw, text, y, f, fill, width=1200, spacing=4):
    box = draw.textbbox((0, 0), text, font=f, stroke_width=0)
    x = (width - (box[2] - box[0])) / 2
    draw.text((x, y), text, font=f, fill=fill, spacing=spacing)


def build_cover():
    OUT.mkdir(parents=True, exist_ok=True)
    COVERS.mkdir(parents=True, exist_ok=True)
    source = Image.open(ART).convert("RGB")
    sw, sh = source.size
    target_ratio = 2 / 3
    crop_w = int(sh * target_ratio)
    left = (sw - crop_w) // 2
    source = source.crop((left, 0, left + crop_w, sh)).resize((1200, 1800), Image.Resampling.LANCZOS)
    source = ImageEnhance.Contrast(source).enhance(1.06)
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, 1200, 720), fill=(3, 14, 28, 120))
    od.rectangle((0, 1420, 1200, 1800), fill=(3, 14, 28, 105))
    image = Image.alpha_composite(source.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(image)
    bold = r"C:\Windows\Fonts\Dengb.ttf"
    regular = r"C:\Windows\Fonts\Deng.ttf"
    serif = r"C:\Windows\Fonts\simsun.ttc"
    gold = (221, 187, 111, 255)
    ivory = (248, 244, 230, 255)
    pale = (201, 218, 223, 255)
    small = font(regular, 27)
    draw_centered(draw, "S D E   U N I V E R S E S", 92, small, gold)
    draw.line((330, 148, 870, 148), fill=(195, 154, 73, 165), width=2)
    title_font = fit_text(draw, TITLE, 1040, bold, 104, 72)
    draw_centered(draw, TITLE, 235, title_font, ivory)
    sub_font = fit_text(draw, SUBTITLE, 970, serif, 38, 30)
    draw_centered(draw, SUBTITLE, 386, sub_font, pale)
    draw_centered(draw, "S · D · E  ×  6 PATHS", 492, font(regular, 27), gold)
    draw.line((410, 548, 790, 548), fill=(195, 154, 73, 140), width=1)
    draw_centered(draw, "王 德 生  著", 1470, font(bold, 43), ivory)
    draw_centered(draw, "WANG DESHENG", 1540, font(regular, 22), pale)
    draw_centered(draw, "DEMAI INTERNATIONAL PRESS", 1648, font(regular, 25), gold)
    draw_centered(draw, f"ISBN {ISBN}", 1696, font(regular, 19), pale)
    jpg = image.convert("RGB")
    jpg.save(OUT / "cover.jpg", quality=94, subsampling=0)
    jpg.save(COVERS / "52.jpg", quality=92, subsampling=0)


def cover_pdf_bytes():
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A5)
    c.drawImage(str(OUT / "cover.jpg"), 0, 0, width=A5[0], height=A5[1], preserveAspectRatio=False)
    c.showPage()
    c.save()
    packet.seek(0)
    return packet


BOOKMARKS = [
    ("版权与书目信息", 2, 0), ("内容提要", 3, 0), ("学术定稿版说明", 4, 0),
    ("核心术语与符号约定", 7, 0), ("目录", 8, 0), ("前言 世界不只从一条路发生", 10, 0),
    ("导论 为什么人类需要六路径方法论", 16, 0),
    ("第一章 被误认成“方法论本身”的单一路径", 17, 1),
    ("第二章 六路径方法论试图解决什么", 24, 1),
    ("第一编 六路径的理论地基", 31, 0),
    ("第三章 SDE本体论入门：发生的三维世界", 32, 1),
    ("第四章 三方程：六路径运行形成的稳定互生关系", 39, 1),
    ("第五章 三原理：六路径的推动力", 45, 1),
    ("第六章 动力—路径—关系：总装模型", 52, 1),
    ("第二编 六条路径逐一精讲", 57, 0),
    ("第七章 E→D→S：沉淀型路径", 58, 1), ("第八章 E→S→D：锚定型路径", 61, 1),
    ("第九章 D→E→S：倒逼型路径", 63, 1), ("第十章 D→S→E：原型型路径", 66, 1),
    ("第十一章 S→E→D：进入型路径", 68, 1), ("第十二章 S→D→E：再创型路径", 71, 1),
    ("第三编 诊断、选路、切换与误判", 74, 0),
    ("第十三章 任务特征诊断", 75, 1), ("第十四章 六路径选择法", 78, 1),
    ("第十五章 路径切换、组合与尺度", 80, 1), ("第十六章 路径误判的十二种失败", 82, 1),
    ("第四编 西方、中华与印度思想传统的路径比较", 85, 0),
    ("第十七章 西方思想传统", 87, 1), ("第十八章 中华思想传统", 97, 1),
    ("第十九章 印度思想传统", 107, 1), ("第二十章 从真理之争到路径条件之争", 115, 1),
    ("第五编 六路径的跨领域应用", 118, 0),
    ("第二十一章 教育", 119, 1), ("第二十二章 健康", 122, 1),
    ("第二十三章 商业与组织", 125, 1), ("第二十四章 科研与学术创造", 127, 1),
    ("第六编 六路径与人工智能技术", 130, 0),
    ("第二十五章 为什么大模型需要路径方法论", 131, 1),
    ("第二十六章 六路径智能体的工程化方法", 135, 1),
    ("第二十七章 中华智问知识发生器", 138, 1),
    ("第二十八章 六路径智能体的评估、安全与迭代", 142, 1),
    ("第七编 检验、边界与未来研究", 144, 0),
    ("第二十九章 六路径方法论如何被检验", 145, 1),
    ("第三十章 边界、反例与可能的错误", 148, 1),
    ("第三十一章 从六路径到路径生态", 150, 1),
    ("结语 从唯一正确的道路到有条件的多路径智慧", 152, 0),
    ("参考文献", 154, 0), ("附录", 160, 0),
]


def build_pdf():
    reader = PdfReader(str(SOURCE))
    cover_reader = PdfReader(cover_pdf_bytes())
    writer = PdfWriter()
    writer.add_page(cover_reader.pages[0])
    for page in reader.pages[1:]:
        writer.add_page(page)
    parents = {}
    for title, page, level in BOOKMARKS:
        parent = None
        if level:
            parent = parents.get(level - 1)
        item = writer.add_outline_item(title, page - 1, parent=parent)
        parents[level] = item
    writer.add_metadata({
        "/Title": f"{TITLE}：{SUBTITLE}",
        "/Author": "王德生",
        "/Subject": "SDE本体论、六路径方法论、三原理、三方程与知识智能体",
        "/Keywords": "SDE本体论; 六路径方法论; 三原理; 三方程; 中华智问; 可审计人工智能",
        "/Creator": "Demai International Press",
        "/Producer": "Demai International Press / SDE Universes",
    })
    with (OUT / PDF_NAME).open("wb") as f:
        writer.write(f)


def clean_page_text(text):
    text = re.sub(r"^六路径方法论入门 · 王德生\s*\n\d+\s*\n", "", text.strip())
    lines = [x.strip() for x in text.splitlines()]
    paras, buf = [], []
    for line in lines:
        if not line:
            if buf:
                paras.append("".join(buf))
                buf = []
            continue
        if re.match(r"^(第[一二三四五六七八九十百]+章|[一二三四五六七八九十]+、|\d+(?:\.\d+)+\s)", line):
            if buf:
                paras.append("".join(buf))
                buf = []
            paras.append(line)
        else:
            buf.append(line)
    if buf:
        paras.append("".join(buf))
    return paras


SELECTIONS = [
    ("chapter-03", "专著选读一", "第三章　SDE本体论入门：发生的三维世界", 32, 38,
     "六路径为何不是六种任意技巧？本章建立S、D、E三维底盘，说明显露、差异序列与特征纠缠为何必须共同进入一次完整发生。"),
    ("chapter-27", "专著选读二", "第二十七章　中华智问知识发生器：六路径的完整技术应用", 138, 141,
     "六路径如何从哲学框架变成智能体控制层？本章展开任务路由、路径锁定、交叉校正、证据审计与人工接管的完整工程流程。"),
    ("chapter-30", "专著选读三", "第三十章　边界、反例与可能的错误", 148, 149,
     "一套方法论必须写出自己可能失败的地方。本章正面处理形式完备与经验有效之间的距离，并规定撤销、收缩和修订条件。"),
]


ARTICLE_CSS = """
:root{--ink:#211c15;--muted:#6f6658;--gold:#a9802e;--paper:#f7f1e5;--card:#fffaf0;--navy:#07182d}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.95}
a{color:#856115;text-decoration:none}.top{position:sticky;top:0;background:#fbf6e9ed;border-bottom:1px solid #d7c59c;z-index:4}
.topin{max-width:880px;margin:auto;padding:13px 22px;display:flex;justify-content:space-between}.hero{background:var(--navy);color:#f7efd9;padding:58px 22px;text-align:center}
.hero .ey{color:#d9b45a;letter-spacing:.28em;font-size:12px}.hero h1{max-width:900px;margin:18px auto;font-size:clamp(28px,5vw,44px);line-height:1.4}.hero p{max-width:760px;margin:auto;color:#c6d1d7}
main{max-width:820px;margin:auto;padding:46px 23px 74px}article p{text-align:justify;font-size:17px;margin:0 0 19px}article h2{font-size:23px;margin:45px 0 16px;border-bottom:1px solid #d8c69c;padding-bottom:8px}
.end{margin-top:50px;background:#fffaf0;border:1px solid #d9c89f;padding:25px;text-align:center}.buttons{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:18px}.btn{border:1px solid #a9802e;padding:9px 15px}.btn.primary{background:#a9802e;color:white}
"""


def selection_html(label, title, hook, paragraphs):
    body = []
    for p in paragraphs:
        if p == title.replace("　", " ") or p.startswith(title.split("　", 1)[0]):
            continue
        if re.match(r"^(第[一二三四五六七八九十百]+章|[一二三四五六七八九十]+、|\d+(?:\.\d+)+\s)", p) and len(p) < 70:
            body.append(f"<h2>{html.escape(p)}</h2>")
        else:
            body.append(f"<p>{html.escape(p)}</p>")
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · 《{TITLE}》专著选读</title><style>{ARTICLE_CSS}</style></head><body>
<nav class="top"><div class="topin"><a href="/books/m/52/">← 返回专著导读</a><span>《{TITLE}》</span></div></nav>
<header class="hero"><div class="ey">{label} · SELECTED CHAPTER</div><h1>{html.escape(title)}</h1><p>{html.escape(hook)}</p></header>
<main><article>{''.join(body)}</article><div class="end">本页节选自《{TITLE}：{SUBTITLE}》，王德生著，Demai International Press，ISBN {ISBN}。<div class="buttons"><a class="btn primary" href="/books/m/52/read.html">在线翻阅全书</a><a class="btn" href="/books/m/52/{PDF_NAME}" target="_blank">下载PDF</a><a class="btn" href="/books/m/52/">查看另两章</a></div></div></main>
<script src="/wds-mode.js" defer></script></body></html>"""


def build_selections():
    reader = PdfReader(str(SOURCE))
    for slug, label, title, start, end, hook in SELECTIONS:
        paras = []
        for page_no in range(start, end + 1):
            paras.extend(clean_page_text(reader.pages[page_no - 1].extract_text() or ""))
        dest = OUT / slug
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "index.html").write_text(selection_html(label, title, hook, paras), encoding="utf-8")


def build_read_html():
    (OUT / "read.html").write_text(f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>在线阅读 · {TITLE}</title>
<style>html,body{{margin:0;height:100%;background:#07182d}}header{{height:58px;background:#f7f0df;display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-family:serif}}header a{{color:#765817;text-decoration:none}}iframe{{width:100%;height:calc(100% - 58px);border:0}}</style></head>
<body><header><a href="/books/m/52/">← 返回专著导读</a><span>{TITLE}</span><a href="{PDF_NAME}" download>下载PDF</a></header><iframe src="{PDF_NAME}#view=FitH"></iframe></body></html>""", encoding="utf-8")


def build_index_html():
    picks = "".join(
        f'<article class="pick"><div class="pk">{label}</div><h3>{html.escape(title)}</h3><p>{html.escape(hook)}</p><a href="{slug}/">阅读全文 →</a></article>'
        for slug, label, title, _, _, hook in SELECTIONS
    )
    content = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} · 王德生 | 德麦国际专著</title><meta name="description" content="《{TITLE}：{SUBTITLE}》· 王德生著 · ISBN {ISBN} · 176页 · 三十一章 · 七附录 · 全书在线翻阅与三章选读"><meta property="og:title" content="{TITLE}"><meta property="og:type" content="book">
<style>
:root{{--bg:#f5efe2;--card:#fffaf0;--navy:#07182d;--gold:#c49a43;--ink:#241f18;--muted:#756a58;--line:#d7c59d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Songti SC",serif;line-height:1.9}}a{{color:#8a6817;text-decoration:none}}
.top{{position:sticky;top:0;z-index:5;background:#f8f2e6ed;border-bottom:1px solid var(--line)}}.wrap{{max-width:960px;margin:auto;padding:0 24px}}.top .wrap{{height:58px;display:flex;align-items:center;justify-content:space-between}}
.hero{{background:radial-gradient(circle at 25% 45%,#173650,#07182d 62%);color:#f6efda;padding:66px 0}}.grid{{display:grid;grid-template-columns:240px 1fr;gap:50px;align-items:center}}.cover{{width:240px;box-shadow:0 24px 60px #0009;border:1px solid #94743d}}
.ey{{font-size:11px;color:#ddb95e;letter-spacing:.3em}}h1{{font-size:clamp(34px,6vw,58px);margin:14px 0 4px;line-height:1.25}}.sub{{font-size:18px;color:#c8d4d8}}.meta{{font-size:13px;color:#abbcc3;margin-top:14px}}.buttons{{display:flex;gap:10px;flex-wrap:wrap;margin-top:25px}}.btn{{padding:10px 17px;border:1px solid #dcb75a;color:#e6c66e}}.btn.primary{{background:#dcb75a;color:#081a2d;font-weight:bold}}
main{{padding:58px 0 76px}}.lede{{font-size:20px;border-left:4px solid #a9802e;padding:2px 0 2px 22px;margin-bottom:34px}}.thesis{{background:#0b2138;color:#e7edf0;padding:28px 30px;margin:34px 0}}.thesis b{{display:block;color:#ddba62;letter-spacing:.25em;font-size:11px;margin-bottom:10px}}
.pub{{display:grid;grid-template-columns:1fr 1fr;border:1px solid var(--line);background:var(--line);gap:1px;margin:40px 0}}.pub div{{background:var(--card);padding:12px 16px;font-size:14px}}.pub strong{{color:var(--muted);display:inline-block;min-width:78px}}.sec{{font-size:12px;color:#9a711b;letter-spacing:.3em;margin:46px 0 17px}}
.picks{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.pick{{background:var(--card);border:1px solid var(--line);border-top:3px solid #a9802e;padding:22px;display:flex;flex-direction:column}}.pk{{font-size:11px;color:#9a711b;letter-spacing:.18em}}.pick h3{{font-size:20px;line-height:1.55}}.pick p{{color:#5c5242;text-align:justify;flex:1}}.feature{{background:var(--card);border:1px solid var(--line);padding:28px;margin-top:42px}}.feature h2{{margin-top:0}}footer{{background:#061525;color:#91a5af;text-align:center;padding:30px}}
@media(max-width:760px){{.grid{{grid-template-columns:1fr;text-align:center}}.cover{{width:175px;margin:auto}}.buttons{{justify-content:center}}.picks,.pub{{grid-template-columns:1fr}}}}
</style></head><body><nav class="top"><div class="wrap"><a href="/">SDE Universes</a><a href="/#monograph">← 专著栏目</a></div></nav>
<header class="hero"><div class="wrap grid"><img class="cover" src="cover.jpg" alt="《{TITLE}》正式封面"><div><div class="ey">DEMAI INTERNATIONAL PRESS · 专著第52号</div><h1>{TITLE}</h1><div class="sub">{SUBTITLE}</div><div class="meta">王德生 著 · ISBN {ISBN} · 176页 · 31章 · 7附录</div><div class="buttons"><a class="btn primary" href="read.html">在线翻阅全书 →</a><a class="btn" href="{PDF_NAME}" target="_blank">下载PDF</a><a class="btn" href="#selections">专著选读</a></div></div></div></header>
<main><div class="wrap"><div class="lede">世界并不只从一条路发生。真正的方法能力，不是把一种熟练程序推向所有对象，而是辨认此刻应从显露、差异序列还是特征纠缠进入，并为选择承担理由。</div>
<section class="thesis"><b>核心命题 · CORE THESIS</b>SDE本体论提供发生的三维世界；三原理点燃动力；六路径组织动力的进入与推进；三方程结算为稳定互生关系；新的稳定关系再回写为下一轮发生的底盘。</section>
<div class="pub"><div><strong>书名</strong>{TITLE}</div><div><strong>作者</strong>王德生（Wang Desheng）</div><div><strong>副题</strong>{SUBTITLE}</div><div><strong>出版</strong>Demai International Press · Singapore</div><div><strong>版本</strong>2026年学术定稿版</div><div><strong>ISBN</strong>{ISBN}</div><div><strong>规模</strong>176页</div><div><strong>结构</strong>7编31章 · 7附录</div></div>
<div class="sec" id="selections">专 著 选 读 · THREE CHAPTERS</div><section class="picks">{picks}</section>
<section class="feature"><h2>本书完成了什么</h2><p>全书严格区分SDE本体论、三原理、六路径与三方程的四层责任，逐条说明六条路径的适用条件、转换机制、失败模式和修复办法；以任务特征向量组织选路与切换，并把教育、健康、商业、科研和人工智能纳入同一套可诊断、可审计的方法框架。</p><p>在技术部分，中华智问知识发生器被作为完整工程案例：任务识别、路径路由、路径锁定、分步校正、证据审计、多路径凝缩、人工接管与长期回写共同构成可追溯工作流。全书同时写入预注册实验、数据字典、安全门和失败条件，使理论不仅能够解释，也能够被比较、否定和修订。</p></section>
<section class="feature"><h2>作者简介</h2><p><strong>王德生</strong>，计算数学博士，SDE发生学创立者，德麦国际创办人。早年从事网格生成、有限元与自适应算法研究，曾在中国科学院开展博士后研究，后任职英国斯旺西大学，并在新加坡南洋理工大学从事教学、科研与博士培养工作十三年。现于新加坡推进跨学科写作、SDE Universes与SDE智能体集群建设。</p></section></div></main>
<footer>© 2026 王德生 · Demai International Press · ISBN {ISBN}</footer><script src="/wds-mode.js" defer></script></body></html>"""
    (OUT / "index.html").write_text(content, encoding="utf-8")


def main():
    build_cover()
    build_pdf()
    build_read_html()
    build_selections()
    build_index_html()
    print(f"Published package created at {OUT}")


if __name__ == "__main__":
    main()
