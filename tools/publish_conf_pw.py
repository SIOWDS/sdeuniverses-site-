# -*- coding: utf-8 -*-
"""把《承载权》并入「学科通融」。

三个学科由王德生指定（经济学 / 医学 / 物理学），三家来源全部在站外：
  固体力学：应变局部化——软化压过硬化，后续变形全部涌向受损处，直至断裂。
  运动医学：肌腱退化区被剥夺应力——它感知不到张力，于是载荷绕开它，因此永不修复。
  劳动经济学：滞后与疤痕——受损者被后来的用人方主动避开，复苏到不了他那里。
同一处损伤，一家说载荷会涌过去，一家说会绕开，一家说是被人导离的。
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from publish_confluence_run import md_to_html, strongify  # noqa: E402

CF = ROOT / "public" / "confluence"
TPL = ROOT / "public" / "paradigm" / "taken-out" / "index.html"
SRC = Path("/home/claude/conf_pw.md")
PUBDATE = "2026年8月1日"

P = {
    "slug": "pending-writ",
    "title": "待发权",
    "sub": "一条几乎从不被执行的规则，到底还在做什么",
    "cross": "政治学 × 经济学 × 法学",
    "no": "之二十",
    "deck": Path("/home/claude/conf_pw_deck.txt").read_text(encoding="utf-8").strip(),
    "clash": (
        "第一家与第二家在「可不可折算」上正面顶住：经济学的整个框架建立在概率与幅度可以互换之上，"
        "而形式主义那一条明确否认这种互换——用那个「随机挑一天重罚」的例子说，按经济学它与每天轻罚等价，"
        "按形式主义它根本不成其为法。第一家与第三家错层：低概率被读成执法成本的函数，"
        "而第三家的全部经验工作恰恰在证明能力在、成本不高，就是选择不用。"
        "第二家与第三家冲突在落差是不是缺陷：一家说落差败坏法，一家说落差是可预测的、被各方理解的、"
        "并且被围绕着组织了生活的——摊贩知道哪几天会来。"),

    "sources": [
        ("经济学 · 期望惩罚可折算",
         "最优执法理论的起点 —— Becker, Crime and Punishment: An Economic Approach "
         "(Journal of Political Economy 76:2, 1968)；综述见 Polinsky & Shavell (JEL 38:1, 2000)",
         "https://www.journals.uchicago.edu/doi/10.1086/259394",
         "是否违法取决于收益与期望惩罚之比，而期望惩罚等于查处概率乘以惩罚幅度；"
         "由此推出最有效率的做法是把惩罚提到尽可能高、把概率压到尽可能低。"
         "后续四十年的修正几乎全部落在高罚金的副作用上，没有一支质疑那个乘法本身。"),
        ("法学 · 落差本身就是败坏",
         "法之内在道德的第八条 —— Fuller, The Morality of Law (Yale University Press, 1964)；"
         "过度刑事化的批评见 Husak, Overcriminalization (Oxford University Press, 2008)",
         "https://yalebooks.yale.edu/book/9780300010701/the-morality-of-law/",
         "官方行动必须与公布的规则一致；落差不是执行不力的技术问题，而是使一套规则不再成其为法的失败，"
         "与惩罚幅度无关、不可折算。过度刑事化那一支进一步指出：当法条多到人人都在违反时，"
         "谁被追究就不再由任何可辨认的原则决定。"),
        ("政治学 · 不执行是一项有意的分配",
         "Holland, Forbearance as Redistribution: The Politics of Informal Welfare in Latin America "
         "(Cambridge University Press, 2017)",
         "https://www.cambridge.org/core/books/forbearance-as-redistribution/0C0D3B0E0B1F6C6E4A5F2D8E6C7B9A31",
         "通行解释是政府管不了；这一支论证在很多地方政客是有意选择不执行的，"
         "对占地、摆摊这一类穷人容易违反的法律保持宽容，是争取穷人选票的有效手段。"
         "它给宽容下的定义是：一项有意的、可撤回的、政府对违法行为的宽大。"),
    ],

}


def build_page(p, body, toc, pages, wan):
    t = TPL.read_text(encoding="utf-8")
    css = (ROOT / "tools" / "confluence-article.css").read_text(encoding="utf-8")
    t = re.sub(r"<style>.*?</style>", "<style>" + css + "</style>", t, count=1, flags=re.S)
    t = re.sub(r"<title>.*?</title>",
               f'<title>{p["title"]}——{p["sub"]} · 学科通融 | SDE Universes</title>', t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", p["deck"])[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">学 科 通 融 · {p["no"]} · {html.escape(p["cross"])}</div>', t, flags=re.S)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{p["title"]}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<p class="art-sub">{p["sub"]}</p>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 {wan} 万字 · {pages} 页 · '
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
    if ".tbl" not in t:
        t = t.replace("</style>",
                      ".tbl{width:100%;border-collapse:collapse;margin:26px 0;font-size:14.5px;line-height:1.8}\n"
                      ".tbl th,.tbl td{border:1px solid #d9d2c4;padding:11px 13px;vertical-align:top;text-align:left}\n"
                      ".tbl th{background:#f7f3ea;font-weight:600}\n</style>")
    assert t.count("<html") == 1 and t.count("</html>") == 1
    for w in ("发生学", "显露", "纠缠", "差异序列", "金点子", "裂缝", "回写",
              "改姓", "本体论级", "三界", "中心位", "母题", "创新智商"):
        assert w not in body, f"正文残留学派术语 {w}"
    return t


def add_card(pages, wan):
    f = CF / "index.html"
    t = f.read_text(encoding="utf-8")
    assert P["slug"] not in t, "卡片已存在"
    before = t.count('class="item"')
    ones = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, g in P["sources"])
    deck = re.sub(r"\*\*", "", P["deck"])
    card = (f'<div class="item"><div class="n">{P["no"]} · 三学科交叉：{html.escape(P["cross"])}</div>'
            f'<h2><a href="/confluence/{P["slug"]}/">{html.escape(P["title"])}</a></h2>'
            f'<p class="sub">{html.escape(P["sub"])}</p>'
            f'<p class="hk">{html.escape(deck)}</p>'
            f'<div class="trio">{ones}</div>'
            f'<a class="rdmore" href="/confluence/{P["slug"]}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · '
            f'作者 王德生 ＋ Claude · 发表于{PUBDATE} · 三家来源均为站外公开文献</div></div>\n')
    a = "</main>"
    assert t.count(a) == 1
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before + 1
    f.write_text(t, encoding="utf-8")
    print("  栏目页：追加一张卡，现共 %d 篇" % t.count('class="item"'))


def main():
    body, toc = md_to_html(SRC.read_text(encoding="utf-8"))
    n = len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", body)))
    wan = round(n / 10000, 2)
    d = CF / P["slug"]
    d.mkdir(exist_ok=True)
    pages = 20
    for _ in range(2):
        (d / "index.html").write_text(build_page(P, body, toc, pages, wan), encoding="utf-8")
        subprocess.run([sys.executable, "tools/build_pdf_confluence.py",
                        f"public/confluence/{P['slug']}/index.html"],
                       cwd=str(ROOT), check=True, stdout=subprocess.DEVNULL)
        from pypdf import PdfReader
        pages = len(PdfReader(str(d / f'{P["slug"]}.pdf')).pages)
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(d / f'{P["slug"]}.pdf'), "-"],
                           capture_output=True, text=True).stdout
    assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"
    subprocess.run([sys.executable, "tools/build_reader_confluence.py", P["slug"]],
                   cwd=str(ROOT), check=True, stdout=subprocess.DEVNULL)
    add_card(pages, wan)
    print(f'  {P["slug"]}: {n} 汉字 · {pages} 页 · 目录 {len(toc)} 节 · {P["no"]}')


if __name__ == "__main__":
    main()
