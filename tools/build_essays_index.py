#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建 SDE 文学分站两个「公众号原档」索引页。

  qinli : /students/qin-li/essays/        秦莉 · 评论随笔（87 篇）
  wds   : /students/wang-desheng/essays/  王德生 · 早期讲稿与合著原档（15 篇）

数据源：tools/data/<key>_essays.json（唯一真相）
排序  ：按发表年份倒序分组，年内按月日倒序 —— 最早的一篇在页面最后。
幂等  ：反复运行输出一致；新增篇目只改 JSON 后重跑。

用法：python3 tools/build_essays_index.py [qinli|wds|all] [--dry]
"""
import json, os, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CN = "零一二三四五六七八九"

PAGES = {
    "qinli": dict(
        data="qinli_essays.json",
        out="public/students/qin-li/essays/index.html",
        canonical="https://liter.sdeuniverses.com/students/qin-li/essays/",
        doctitle="秦莉 · 评论随笔 · %d篇 | 作者专栏 · SDE 文学",
        desc="秦莉（笔名斐索）评论与随笔 %d 篇，按 %s 年份编排：文学评论、思想随笔、生命叙事、意义哲学、艺术理论与残雪四论。",
        eyebrow="评 论 · 随 笔 · ESSAYS",
        h1="秦莉 · 评论随笔",
        who="笔名 斐索 · 共 %d 篇 · %s",
        back=("/students/qin-li/", "← 秦莉 · Profile", "← 返回秦莉 Profile"),
        base="/students/qin-li/essays/",
        footer="© 德麦国际 Demai International · SDE 文学 · 作者专栏 · 秦莉",
    ),
    "wds": dict(
        data="wds_essays.json",
        out="public/students/wang-desheng/essays/index.html",
        canonical="https://liter.sdeuniverses.com/students/wang-desheng/essays/",
        doctitle="王德生 · 早期讲稿与合著原档 · %d篇 | SDE 文学",
        desc="王德生早期三视角讲稿与合著原档 %d 篇（%s）：美学、教育、健康、营销、逻辑与认知方法。",
        eyebrow="EARLY LECTURES · 早 期 原 档",
        h1="王德生 · 早期讲稿与合著原档",
        who="共 %d 篇 · %s · 美学、教育、健康、营销、逻辑与认知方法",
        back=("/students/wang-desheng/", "← 王德生", "← 返回王德生作品页"),
        base="/students/wang-desheng/essays/",
        footer="© 德麦国际 Demai International · SDE 文学 · 王德生原始文献",
        note="本辑按原载日期保存「321互动艺术」早期讲稿与合著稿的 PDF 原貌。健康与人体相关内容属于历史思想资料，不构成医疗建议。",
    ),
}

CSS = """
:root{--gold:#8A6817;--gold2:#C89117;--ink:#2A2315;--ink2:#5C5039;--bg:#F5EFE0;--muted:#8A7B54;--line:rgba(138,104,23,.26);--wash:rgba(200,145,23,.07)}
*{margin:0;padding:0;box-sizing:border-box}
::selection{background:rgba(138,104,23,.28)}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:"Noto Serif SC","Songti SC",Georgia,serif;line-height:1.9;
  background-image:radial-gradient(ellipse at 50% -14%,rgba(138,104,23,.10),transparent 60%)}
a{color:inherit;text-decoration:none}
nav{position:sticky;top:0;z-index:30;background:rgba(245,239,224,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
nav .w{max-width:860px;margin:0 auto;padding:12px 26px;display:flex;justify-content:space-between;align-items:center}
nav a{color:var(--gold);font-size:13.5px;letter-spacing:.06em}
header{max-width:760px;margin:0 auto;padding:64px 26px 4px;text-align:center}
.eyebrow{font-size:11px;letter-spacing:.42em;color:var(--gold)}
h1{font-size:clamp(29px,5vw,44px);font-weight:800;letter-spacing:.09em;margin-top:20px;line-height:1.4}
.who{font-size:13px;color:var(--muted);letter-spacing:.16em;margin-top:16px}
.rule{width:52px;height:1px;background:var(--gold);opacity:.55;margin:28px auto}
.lede{font-size:15px;color:var(--ink2);line-height:2.05;text-align:left;max-width:640px;margin:0 auto}
.note{max-width:640px;margin:18px auto 0;border-left:2px solid var(--gold);padding:6px 0 6px 16px;
  font-size:13.5px;color:var(--muted);line-height:1.95;text-align:left}
.years{position:sticky;top:47px;z-index:20;background:rgba(245,239,224,.94);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);margin-top:40px}
.years .w{max-width:860px;margin:0 auto;padding:11px 26px;display:flex;gap:22px;overflow-x:auto;
  font-size:13px;letter-spacing:.12em;color:var(--muted);-webkit-overflow-scrolling:touch}
.years a{white-space:nowrap;padding-bottom:2px;border-bottom:1px solid transparent}
.years a:hover{color:var(--gold);border-bottom-color:var(--gold)}
.years em{font-style:normal;font-size:11px;color:var(--muted);opacity:.75;margin-left:5px}
main{max-width:860px;margin:0 auto;padding:8px 26px 92px}
.yblock{padding-top:54px;scroll-margin-top:104px}
.yhead{display:flex;align-items:baseline;gap:16px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.yhead b{font-size:40px;font-weight:800;color:var(--gold);letter-spacing:.06em;font-variant-numeric:tabular-nums;line-height:1}
.yhead span{font-size:12px;letter-spacing:.24em;color:var(--muted)}
.item{display:grid;grid-template-columns:74px 1fr;gap:22px;padding:24px 16px 24px 12px;border-bottom:1px solid rgba(138,104,23,.13);
  border-left:2px solid transparent;transition:background .18s,border-color .18s}
.item:hover{background:var(--wash);border-left-color:var(--gold)}
.when{font-size:15px;color:var(--gold);font-variant-numeric:tabular-nums;letter-spacing:.06em;padding-top:3px;white-space:nowrap}
.cat{font-size:11px;letter-spacing:.24em;color:var(--muted)}
.cat i{font-style:normal;color:var(--gold2);margin-left:10px}
.t{font-size:20.5px;font-weight:800;line-height:1.55;letter-spacing:.02em;margin-top:8px}
.item:hover .t{color:var(--gold)}
.st{font-size:14px;color:var(--ink2);margin-top:6px;line-height:1.75}
.tz{font-size:14.5px;color:var(--ink2);line-height:1.95;margin-top:11px}
.src{font-size:12px;color:var(--muted);letter-spacing:.05em;margin-top:12px}
.back{text-align:center;margin-top:52px}
.back a{color:var(--gold);font-size:14.5px;letter-spacing:.06em;border-bottom:1px solid rgba(138,104,23,.4);padding-bottom:2px}
footer{border-top:1px solid var(--line);padding:30px 26px;text-align:center;color:var(--muted);font-size:13px}
footer a{color:var(--gold)}
@media(max-width:640px){
  .item{grid-template-columns:1fr;gap:0;padding:22px 4px}
  .when{padding:0 0 8px}
  .yhead b{font-size:33px}
  .lede{font-size:14.5px}
}
""".strip()


def cn_num(n):
    if n < 10:
        return CN[n]
    if n < 20:
        return "十" + (CN[n % 10] if n % 10 else "")
    return CN[n // 10] + "十" + (CN[n % 10] if n % 10 else "")


def esc(s):
    return html.escape(s, quote=True)


def render(cfg):
    rows = json.load(open(os.path.join(ROOT, "tools", "data", cfg["data"]), encoding="utf-8"))
    rows.sort(key=lambda r: (-r["y"], -r["m"], -r["d"], r["title"]))
    years = []
    for r in rows:
        if not years or years[-1][0] != r["y"]:
            years.append((r["y"], []))
        years[-1][1].append(r)

    n = len(rows)
    n_wechat = sum(1 for r in rows if r["src"].startswith("原载"))
    n_site = n - n_wechat
    span = "%d—%d" % (rows[-1]["y"], rows[0]["y"]) if rows[-1]["y"] != rows[0]["y"] else str(rows[0]["y"])

    nav_years = "".join('<a href="#y%d">%d<em>%d 篇</em></a>' % (y, y, len(g)) for y, g in years)

    blocks = []
    for y, g in years:
        items = []
        for r in g:
            cat = esc(r["cat"])
            if r.get("series"):
                cat += "<i>%s</i>" % esc(r["series"])
            meta = [x for x in (r.get("author", ""), r["src"]) if x]
            if r.get("pages"):
                meta.append("原始 PDF %d 页" % r["pages"])
            st = ('<div class="st">%s</div>' % esc(r["subtitle"])) if r.get("subtitle") else ""
            items.append(
                '<a class="item" href="%s%s/">'
                '<div class="when">%02d.%02d</div>'
                '<div><div class="cat">%s</div><div class="t">%s</div>%s'
                '<div class="tz">%s</div><div class="src">%s</div></div></a>'
                % (cfg["base"], r["slug"], r["m"], r["d"], cat, esc(r["title"]), st,
                   esc(r["teaser"]), " · ".join(esc(x) for x in meta))
            )
        blocks.append(
            '<section class="yblock" id="y%d">\n  <div class="yhead"><b>%d</b><span>%s篇</span></div>\n  %s\n</section>'
            % (y, y, cn_num(len(g)), "\n  ".join(items))
        )

    lede = "%d 篇按发表年份排列，最近的在最前，最早的一篇在页面末尾。" % n
    if n_wechat:
        lede += "其中 %d 篇原载「321互动艺术」公众号，本站保留原始 PDF、完整署名与原载日期" % n_wechat
        lede += ("；另 %d 篇为本站首发的长文与作者稿。" % n_site) if n_site else "。"
    note = ('\n  <p class="note">%s</p>' % esc(cfg["note"])) if cfg.get("note") else ""

    return (
        '<!DOCTYPE html>\n<html lang="zh-CN"><head>\n'
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n" % esc(cfg["doctitle"] % n) +
        '<meta name="description" content="%s">\n' % esc(cfg["desc"] % (n, span)) +
        '<link rel="canonical" href="%s">\n' % cfg["canonical"] +
        "<style>\n%s\n</style></head>\n<body>\n" % CSS +
        '<nav><div class="w"><a href="/">SDE 文学</a><a href="%s">%s</a></div></nav>\n' % (cfg["back"][0], esc(cfg["back"][1])) +
        '<header>\n  <div class="eyebrow">%s</div>\n' % esc(cfg["eyebrow"]) +
        "  <h1>%s</h1>\n" % esc(cfg["h1"]) +
        '  <div class="who">%s</div>\n' % esc(cfg["who"] % (n, span)) +
        '  <div class="rule"></div>\n  <p class="lede">%s</p>%s\n</header>\n' % (esc(lede), note) +
        '<div class="years"><div class="w">%s</div></div>\n' % nav_years +
        '<main>\n%s\n  <div class="back"><a href="%s">%s</a></div>\n</main>\n' % ("\n".join(blocks), cfg["back"][0], esc(cfg["back"][2])) +
        "<footer>%s · <a href=\"/browse/\">sdeuniverses.com</a></footer>\n" % esc(cfg["footer"]) +
        '<script>window.WDS_READ={profile:"liter"};</script>\n'
        '<script src="/taste/wds-companion/wds-read.js?v=20260817c" defer></script>\n'
        '<script src="/wds-mode.js?v=20260901o" defer></script>\n'
        "</body></html>\n"
    )


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "all"
    keys = list(PAGES) if which == "all" else [which]
    for k in keys:
        h = render(PAGES[k])
        if "--dry" in sys.argv:
            sys.stdout.write(h)
        else:
            p = os.path.join(ROOT, PAGES[k]["out"])
            open(p, "w", encoding="utf-8").write(h)
            print("written %s  %d bytes" % (p, len(h)))
