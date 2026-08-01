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
SRC = Path("/home/claude/conf_bearing.md")
PUBDATE = "2026年8月1日"

P = {
    "slug": "load-bearing-right",
    "title": "承载权",
    "sub": "为什么有些损伤是被压垮的，有些是被绕开而死的",
    "cross": "经济学 × 医学 × 物理学",
    "no": "之十四",
    "deck": Path("/home/claude/conf_deck.txt").read_text(encoding="utf-8").strip(),
    "clash": (
        "同样是「反复受载的结构上出现一处损伤」，第一家说后续变形会全部转移到那里，"
        "第二家说后续载荷会绕开那里——这两句话不能同时对同一处损伤为真。"
        "第一家与第三家的分歧更深一层：软化处吸引变形是纯粹的力学后果，在一块无人看管的金属里照样发生；"
        "而受损者被避开必须经过一次判断——是有人看了简历上的日期之后决定不叫他来面试。"
        "第二家与第三家看起来同向，却对「能不能重新接上」给出相反判断：一家说那一块已经感觉不到，"
        "单靠多加载进不去；一家明确认为只要需求足够强，滞后可以被逆转。"),
    "sources": [
        ("物理 · 损伤把载荷吸过去",
         "应变局部化判据 —— Rudnicki & Rice, Conditions for the localization of deformation "
         "in pressure-sensitive dilatant materials (J. Mech. Phys. Solids 23:6, 1975)",
         "https://www.sciencedirect.com/science/article/abs/pii/0022509675900010",
         "局部化的条件是软化压过硬化：某处一旦净软化，整块材料的后续变形会在很短时间里"
         "全部集中到一条窄带，带外保持完好；而提高硬化率或应变率敏感性可以抑制它。"),
        ("医学 · 损伤被载荷绕开",
         "肌腱的加载适应与被剥夺应力 —— Kjaer, Role of extracellular matrix in adaptation of "
         "tendon and skeletal muscle to mechanical loading (Physiological Reviews 84:2, 2004)",
         "https://journals.physiology.org/doi/full/10.1152/physrev.00031.2003",
         "退化区因正常结构丧失而处于被剥夺应力的状态，细胞受到的机械刺激不足、收不到启动重塑的信号，"
         "于是可以有大量基质周转却始终形成不了成熟组织；这一支的处方因此是调整后的加载，而不是不加载。"),
        ("经济学 · 载荷是被人导离的",
         "长期失业的持续依赖与招聘歧视 —— Kroft, Lange & Notowidigdo, Duration Dependence and "
         "Labor Market Conditions (QJE 128:3, 2013)；就业滞后见 Yagan (JPE 127:5, 2019)",
         "https://academic.oup.com/qje/article/128/3/1123/1848791",
         "同样的简历，标注失业时间更长的那一组收到面试邀请的概率显著更低：第一次冲击留下的不只是收入损失，"
         "还有一个使后来的需求绕开这个人的标签；而深衰退的就业损失在多年之后仍集中在特定人群身上。"),
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
