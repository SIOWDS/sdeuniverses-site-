# -*- coding: utf-8 -*-
"""孔凡鹤 44 篇文章页 · 补方向标注 + 同组导航。

两件事：
  一、36 篇的题头只写「学员专栏 · 孔凡鹤」（另有 4 篇连 art-series 都没有），
      读者点进来看不出这篇属于哪个研究方向。按 kfh_regroup.py 的九个方向补上。
  二、每篇文末加一块「同一方向的其他文章」，把同组的兄弟篇列出来。
      44 篇分属九个互不相干的方向，没有这块，读者只能退回索引再找。

用法： python3 tools/kfh_crosslink.py [--dry]
"""
import argparse
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kfh_regroup import GROUPS

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "public" / "students" / "kong-fanhe"

# 题头用的短名（索引里的组名带副题，太长）
SHORT = {
    "心理治疗 · 技艺与流派": "心理治疗",
    "灾害治理 · 谁被点名": "灾害治理",
    "存在感 · 为什么越来越淡": "存在感研究",
    "按小时照护 · 制度替人担责之后": "照护与制度",
    "多子女家庭 · 手足伦理如何长出来": "家庭伦理",
    "女性生殖健康 · 组织土壤的一种读法": "女性健康",
    "身体与锻炼 · 修复之外": "身体与锻炼",
    "心理咨询 · 改变到底怎么发生": "心理咨询",
    "青少年与手机 · 被给予的悖论": "青少年与手机",
}

SIB_CSS = """
.kin{margin:44px 0 8px;padding:22px 26px;border:1px solid rgba(128,128,128,.24);
border-left:3px solid currentColor;border-radius:0 11px 11px 0;background:rgba(128,128,128,.05)}
.kin .kl{font-size:11.5px;letter-spacing:.34em;opacity:.72;margin-bottom:6px}
.kin .kn{font-size:17px;font-weight:700;margin-bottom:12px}
.kin a{display:block;padding:8px 0;text-decoration:none;font-size:15px;line-height:1.7;
border-top:1px dashed rgba(128,128,128,.26);opacity:.88}
.kin a:first-of-type{border-top:0}
.kin a:hover{opacity:1}
.kin .more{margin-top:12px;font-size:13.5px;opacity:.72}
"""


def title_of(slug):
    h = (BASE / slug / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<h1 class="art-title">(.*?)</h1>', h, re.S)
    if not m:
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        return re.sub("<[^>]+>", "", m.group(1)).split(" · ")[0].strip()
    return re.sub("<[^>]+>", "", m.group(1)).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    titles = {}
    for g in GROUPS.values():
        for s in g["slugs"]:
            titles[s] = title_of(s)

    n_series, n_kin, n_css = 0, 0, 0
    for name, g in GROUPS.items():
        short = SHORT[name]
        for slug in g["slugs"]:
            f = BASE / slug / "index.html"
            h = f.read_text(encoding="utf-8")
            orig = h

            # ── 一、方向标注 ──
            # 有些早期页用 .ey 作题头，本来就写了方向，别再插一行
            ey = re.search(r'<div class="ey">(.*?)</div>', h, re.S)
            if ey and short in re.sub("<[^>]+>", "", ey.group(1)):
                pass
            elif (m := re.search(r'(<div class="art-series">)(.*?)(</div>)', h, re.S)):
                cur = re.sub("<[^>]+>", "", m.group(2)).strip()
                if short not in cur:
                    new = (cur + " · " + short) if cur else ("学员专栏 · 孔凡鹤 · " + short)
                    h = h[:m.start(2)] + new + h[m.end(2):]
                    n_series += 1
            else:
                # 没有 art-series 的页：插在 <h1 class="art-title"> 之前
                m2 = re.search(r'<h1 class="art-title">', h)
                if m2:
                    h = (h[:m2.start()] +
                         f'<div class="art-series">学员专栏 · 孔凡鹤 · {short}</div>\n' +
                         h[m2.start():])
                    n_series += 1

            # ── 二、同组导航 ──
            if 'class="kin"' not in h:
                sibs = [s for s in g["slugs"] if s != slug]
                links = "".join(
                    f'<a href="/students/kong-fanhe/{s}/">{html.escape(titles[s])}</a>'
                    for s in sibs)
                block = (f'<div class="kin"><div class="kl">同 一 方 向</div>'
                         f'<div class="kn">{html.escape(name)}</div>{links}'
                         f'<div class="more">'
                         f'<a href="/students/kong-fanhe/works/#g{list(GROUPS).index(name)+1}" '
                         f'style="display:inline;border:0;padding:0">'
                         f'在作品索引里看这一组（共 {len(g["slugs"])} 篇）→</a></div></div>')
                # 插在 .wrap 容器收尾之前；找不到就插在 </body> 之前
                m3 = re.search(r'(</div>\s*)(?=<script|<footer|</body>)', h[::-1])
                idx = h.rfind("</body>")
                anchor = h.rfind("</div>", 0, idx)
                if anchor > 0:
                    h = h[:anchor] + block + "\n" + h[anchor:]
                else:
                    h = h[:idx] + block + "\n" + h[idx:]
                n_kin += 1

            # ── 三、样式 ──
            if ".kin{" not in h:
                j = h.rfind("</style>")
                assert j > 0, f"{slug} 没有 style 块"
                h = h[:j] + SIB_CSS + h[j:]
                n_css += 1

            if h != orig and not a.dry:
                # 标签配对自检，任何一页不过就整体中止
                for tag in ("div", "body", "html", "style"):
                    o = len(re.findall(rf"<{tag}[\s>]", h)); c = h.count(f"</{tag}>")
                    assert o == c, f"{slug} <{tag}> 不配对 {o}/{c}"
                f.write_text(h, encoding="utf-8")

    print(f"{'[dry] ' if a.dry else ''}方向标注 {n_series} 处 · 同组导航 {n_kin} 页 · 样式注入 {n_css} 页")


if __name__ == "__main__":
    main()
