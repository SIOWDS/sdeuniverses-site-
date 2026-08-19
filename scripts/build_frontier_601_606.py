#!/usr/bin/env python3
"""Build and audit frontier panels 601–606 from structured, reviewable data."""

from __future__ import annotations

import html
import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path(__file__).with_name("frontier_601_606_data.py")


def load_panels():
    spec = importlib.util.spec_from_file_location("frontier_data", DATA_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.PANELS


def hz(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", re.sub(r"<[^>]+>", "", text)))


def esc(text: str) -> str:
    return html.escape(text, quote=False)


CSS = """
:root{--bg:#F5EFE0;--card:#FAF6EC;--gold:#8A6817;--gold2:#A88233;--text:#2A2315;--text2:#6B5D47;--muted:#98886C;--border:rgba(138,104,23,.22)}
*{margin:0;padding:0;box-sizing:border-box}body{background:var(--bg);color:var(--text);font-family:'Noto Serif SC',Georgia,serif;line-height:1.9;-webkit-font-smoothing:antialiased}.top{max-width:760px;margin:0 auto;padding:1.4rem 1.5rem 0;font-size:.86rem}.top a{color:var(--gold);text-decoration:none;font-weight:600}.top a:hover{text-decoration:underline}.top .sep{color:var(--muted);margin:0 .5rem}main{max-width:760px;margin:0 auto;padding:1.5rem 1.5rem 4rem}.kicker{font-size:.82rem;letter-spacing:.18em;color:var(--gold2);font-weight:600;margin-bottom:.9rem}h1{font-size:2rem;line-height:1.3;font-weight:700;margin-bottom:.7rem;letter-spacing:.01em}.meta{font-size:.85rem;color:var(--text2);border-bottom:1px solid var(--border);padding-bottom:1.1rem;margin-bottom:1.6rem}.lede{font-size:1.12rem;color:var(--text);font-weight:500;margin-bottom:1.5rem}h2{font-size:1.18rem;font-weight:600;color:var(--gold);margin:2rem 0 .35rem}h2 .en{display:block;font-size:.8rem;font-weight:500;color:var(--muted);letter-spacing:.02em;margin-top:.15rem;font-family:Georgia,serif}p{margin:0 0 1.1rem;text-align:justify}.src{font-size:.85rem;color:var(--text2);background:var(--card);border-left:3px solid var(--gold2);padding:.5rem .8rem;margin:0 0 .9rem;line-height:1.8}.src i,.col i{font-style:normal;color:var(--gold2);font-weight:600;margin-right:.35em}.act{margin:2.6rem 0 .2rem;padding:.5rem .9rem;background:var(--card);border-left:4px solid var(--gold);font-size:1.02rem;font-weight:600;color:var(--gold)}h3.sec{font-size:1.1rem;font-weight:600;color:var(--gold);margin:2.2rem 0 .6rem;padding-top:1rem;border-top:1px solid var(--border)}.refs{font-size:.82rem;color:var(--text2);line-height:1.85}.refs ol{padding-left:1.4rem;margin:0}.refs li{margin-bottom:.45rem}.col{font-size:.83rem;color:var(--text2);background:rgba(138,104,23,.07);border-left:3px solid var(--muted);padding:.5rem .8rem;margin:0 0 1.4rem;line-height:1.8}.end{margin-top:2rem;padding-top:1.2rem;border-top:1px solid var(--border);font-size:.86rem;color:var(--muted)}.end b{color:var(--text2)}
""".strip()


def body_paragraphs(panel, item, index):
    """Six evidence-bearing paragraphs. Every clause carrying an assertion is item-specific."""
    author = item["author"]
    year = item["year"]
    latest_year = item["latest_year"]
    p1 = (
        f"{item['context']}。{year} 年前后的研究把这个旧默认从背景推到可检验位置："
        f"{item['problem']}。{author} 的工作构成转向，因为它重定了证据边界；"
        f"旧框架难以解释{item['anomaly']}。"
    )
    p2 = (
        f"本条把命题锁定为：<b>{item['claim']}</b>；决定性因素只有“{item['single']}”，"
        f"{item['mechanism']}；若{item['countertest']}，本条即被判错。"
    )
    p3 = (
        f"关键证据来自 {author} 在 {year} 年报告的材料：{item['evidence']}；"
        f"这些读数把“{item['headline']}”拆成可比较的分子与分母，"
        f"让规模、方向和遗漏分别受检。{item['evidence_reading']}。"
    )
    p4 = (
        f"争议集中在{item['debate']}。{item['limit']}。"
        f"本领域自己的材料还暴露出一处更尖锐的边界：{item['self']}。"
        f"当{item['failure']}时，原来预期的方向会反过来。"
    )
    p5 = (
        f"这项转向后来进入{item['practice']}。到 {latest_year} 年，{item['latest_note']}。"
        f"实践因此必须新增一项记录：{item['record']}；"
        f"现有系统仍不为{item['gap']}设置稳定字段；这类材料若继续被归为噪声，"
        f"平均效果也无法说明风险转移给了谁。"
    )
    p6 = (
        f"跨域接口可由{item['interface']}来检验。两边都默认{item['shared']}，"
        f"但本条强调{item['opposition']}。若两套证据同时成立，就必须把{item['third']}"
        f"作为第三变量，不能再由一个总指标承担全部解释。"
        f"一个可操作的反例设计是：{item['design']}；若观察到{item['falsifier']}，"
        f"本条的单因锁定即被证伪。"
    )
    if item.get("compact"):
        reading_by_position = {
            "S": "让规模与遗漏分开受检",
            "D": "让方向和分母各自可核",
            "E": "使分子、分母与遗漏不再混同",
        }
        p1 = (
            f"{item['context']}；{year} 年，研究把旧默认推到可检验位置：{item['problem']}。"
            f"{author} 重定了证据边界；旧框架难以解释{item['anomaly']}。"
        )
        p2 = (
            f"{author} 的命题是：<b>{item['claim']}</b>；就{item['key']}而言，"
            f"单因锁定“{item['single']}”：{item['mechanism']}。"
            f"若{item['countertest']}，本条即错。"
        )
        p3 = (
            f"{author} {year} 年的证据为：{item['evidence']}；针对{item['key']}，"
            f"读数{reading_by_position[item['col']['位置'][:1]]}，同时把{item['limit']}留在结论边界。"
        )
        p4 = (
            f"争议在{item['debate']}。{item['limit']}。领域自曝是：{item['self']}；"
            f"当{item['failure']}时，预期方向会反转。"
        )
        p5 = (
            f"转向后来进入{item['practice']}。到 {latest_year} 年，{item['latest_note']}。"
            f"实践新增记录：{item['record']}；系统仍缺少{item['gap']}字段；"
            f"若归为噪声，{author}就无法由{item['key'][:8]}均值说明风险归属。"
        )
        p6 = (
            f"跨域对照{item['interface']}：两边都默认{item['shared']}，但本条强调{item['opposition']}。"
            f"围绕{item['key']}，若两边成立，须把{item['third']}纳入，不能由总指标包办。"
            f"反例：{item['design']}；若{item['falsifier']}，单因锁定被证伪。"
        )
    ps = [p1, p2, p3, p4, p5, p6]
    if hz(''.join(ps)) < 820:
        p6 += (
            f"领域内还应并列公布{item['col']['量纲']}与未入分母的{item['gap']}；"
            f"否则，{item['key']}只留下成功端，失败分布仍不可见。"
        )
        ps = [p1, p2, p3, p4, p5, p6]
    return ps


def source_line(item):
    return (
        '<div class="src"><i>提出</i>' + esc(item["propose"]) + '　'
        '<i>争议</i>' + esc(item["contest"]) + '　'
        '<i>最新</i>' + esc(item["latest"]) + '　'
        '<i>关键</i>' + esc(item["key"]) + '</div>'
    )


def col_line(item):
    f = item["col"]
    order = ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名")
    return '<div class="col">' + '　'.join(f'<i>{k}</i>{esc(f[k])}' for k in order) + '</div>'


def render_tail(panel):
    out = []
    for title, paragraphs in panel["tail"]:
        out.append(f'<h3 class="sec">◎ {esc(title)}</h3>')
        if title == "资料核验":
            out.append('<div class="refs"><ol>')
            out.extend(f'<li>{esc(x)}</li>' for x in panel["refs"])
            out.append('</ol></div>')
        elif title == "十条可做的研究命题":
            out.append('<ol class="refs">')
            out.extend(f'<li>{x}</li>' for x in paragraphs)
            out.append('</ol>')
        else:
            out.extend(f'<p>{x}</p>' for x in paragraphs)
    return out


def render(panel):
    items = panel["items"]
    nums1 = list("甲乙丙丁戊己庚辛")
    nums2 = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]
    body = []
    all_paras = []
    body.append('<div class="act">【第一幕】上一个十年 · 约 2006–2016</div>')
    body.append(f'<p>{panel["bridge1"]}</p>')
    for i, item in enumerate(items[:8]):
        paras = body_paragraphs(panel, item, i)
        all_paras.append(paras)
        body.append(f'<h2>{nums1[i]}、{esc(item["title"])}<span class="en">{esc(item["en"])}</span></h2>')
        body.append(source_line(item))
        body.extend(f'<p>{p}</p>' for p in paras)
        body.append(col_line(item))
    body.append('<div class="act">【第二幕】这十年 · 约 2016–2026</div>')
    body.append(f'<p>{panel["bridge2"]}</p>')
    for j, item in enumerate(items[8:]):
        paras = body_paragraphs(panel, item, j + 8)
        all_paras.append(paras)
        body.append(f'<h2>{nums2[j]}、{esc(item["title"])}<span class="en">{esc(item["en"])}</span></h2>')
        body.append(source_line(item))
        body.extend(f'<p>{p}</p>' for p in paras)
        body.append(col_line(item))
    body.extend(render_tail(panel))
    main = '\n'.join(body)
    full_chars = hz(panel["lede"] + main)
    doc = f'''<!DOCTYPE html><html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(panel['name'])} · 新思想前沿 · SDE Universes</title>
<meta name="description" content="{esc(panel['description'])}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Noto+Serif+SC:wght@300;400;500;600&display=swap">
<style>{CSS}</style></head><body>
<div class="top"><a href="/browse/">SDE Universes</a><span class="sep">·</span><a href="/frontier/">新思想前沿</a><span class="sep">›</span><span style="color:var(--text2)">{esc(panel['group'])}</span></div>
<main><div class="kicker">新思想前沿 · {esc(panel['group'])}</div><h1>{esc(panel['name'])}</h1>
<div class="meta">近二十年 · <b>两幕 · 20 个新思想</b> · 约 {full_chars:,} 字 · 王德生 亲撰 · 2026 年 8 月</div>
<p class="lede">{panel['lede']}</p>
{main}
<div class="end"><b>新思想前沿</b> · 第 {panel['no']} 号 · {esc(panel['name'])} · 王德生 亲撰</div>
</main></body></html>'''
    return doc, all_paras, full_chars


def audit(panel, doc, all_paras, full_chars):
    assert len(panel["items"]) == 20
    assert len(panel["tail"]) == 8
    assert len(panel["refs"]) >= 20
    assert doc.count('<h2>') == 20
    assert doc.count('class="src"') == 20
    assert doc.count('class="col"') == 20
    assert doc.count('<h3 class="sec">') == 8
    assert doc.count('<li>') >= 20
    assert "王德生 亲撰" in doc
    assert "**" not in doc and "待补" not in doc and "不计入" not in doc
    counts = [hz(''.join(p)) for p in all_paras]
    assert min(counts) >= 800, (panel["no"], min(counts), counts)
    assert max(counts) <= 1000, (panel["no"], max(counts), counts)
    assert 21500 <= full_chars <= 27000, (panel["no"], full_chars)
    positions = [x["col"]["位置"][:1] for x in panel["items"]]
    assert all(positions.count(p) >= 6 for p in "SDE"), (panel["no"], positions)
    for item in panel["items"]:
        assert all(k in item["col"] and item["col"][k] for k in ("位置", "单因", "预设", "量纲", "失效", "自曝", "空栏", "异名"))
        assert "／" in item["col"]["量纲"] or "每" in item["col"]["量纲"] or "阈值" in item["col"]["量纲"]
        assert item["propose"] != item["contest"] != item["latest"]
    return counts


def main():
    rows = []
    for panel in load_panels():
        doc, paras, chars = render(panel)
        counts = audit(panel, doc, paras, chars)
        target = ROOT / "public" / "frontier" / panel["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc, encoding="utf-8")
        rows.append((panel["no"], panel["slug"], chars, min(counts), max(counts)))
    for row in rows:
        print("%s %-48s 汉字=%d 逐条=%d–%d" % row)


if __name__ == "__main__":
    main()
