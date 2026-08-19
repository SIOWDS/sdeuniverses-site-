# -*- coding: utf-8 -*-
"""给学科通融各篇文章页换上本栏自己的学术版式。

原样式继承自每日必读（赭红／靛青），而学科通融是论文体、且首页与栏目页
用的是橄榄绿。本脚本把配色统一到橄榄绿，并按学术论文的阅读需要调整版式：

  · 摘要块改成论文摘要的样子（左侧粗竖线 + 「摘 要」标签），与导语区分
  · 关键词单独一行
  · 一级标题的编号（1、2、3…）用侧边悬挂的方式排，正文左缘保持齐整
  · 参考文献悬挂缩进；注释小一号
  · 正文行高与字号按长文阅读调（1.95 / 17px），最大行宽收到 34 个汉字左右
  · 顶部阅读进度条改用橄榄绿
  · 深色模式跟随系统

只改样式与少量结构包裹，不动任何一个字的正文。
用法： python3 tools/style_confluence.py [--all | <slug>]
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CF = ROOT / "public" / "confluence"

MARK = "<!-- confluence-academic-skin v1 -->"

SKIN = """
<!-- confluence-academic-skin v1 -->
<style>
:root{
  --ink:#15181C; --ink2:#535B63; --ink3:#7C858E;
  --paper:#F6F5F0; --card:#FCFCF8;
  --olive:#5B7247; --olive2:#7E9A55; --olive3:#3F5231;
  --line:rgba(21,24,28,.14); --line2:rgba(91,114,71,.30);
}
body{background:var(--paper);color:var(--ink);
  font-family:"Noto Serif SC","Source Han Serif SC","Songti SC",serif;
  line-height:1.95;-webkit-font-smoothing:antialiased}
#pbar{background:var(--olive2)!important}
.readbar,.rb-btn{border-color:var(--line)!important}
.rb-btn{color:var(--ink2)!important}
.rb-btn.cur{background:var(--olive3)!important;border-color:var(--olive3)!important;color:#F6F5F0!important}
.nav-back,a{color:var(--olive)}

/* 题头 */
.art{max-width:860px;padding:70px 24px 22px}
.art-series{color:var(--olive)!important;letter-spacing:.34em;font-size:11.5px;
  font-family:"Noto Sans SC",sans-serif}
.art-title{font-size:clamp(29px,4.4vw,43px);line-height:1.38;margin:22px 0 16px;
  letter-spacing:.005em;font-weight:700}
.art-sub{color:var(--ink2);font-size:16.5px;line-height:1.88;max-width:620px;
  margin:0 auto;font-weight:400}
.art-meta{color:var(--ink3);font-size:12.5px;margin-top:22px;letter-spacing:.05em;
  font-family:"Noto Sans SC",sans-serif}

/* 正文版心：一行约 34 个汉字 */
.wrap{max-width:700px;padding:6px 24px 56px}
.wrap p{margin:0 0 17px;text-align:justify;text-justify:inter-ideograph;font-size:17px}
.wrap strong,.wrap b{font-weight:700;color:#000}

/* 摘要：论文体 */
.deck{background:var(--card);border:1px solid var(--line);
  border-left:3.5px solid var(--olive)!important;border-radius:0 8px 8px 0!important;
  padding:22px 26px 22px 24px;margin:30px 0 22px;font-size:15.6px;line-height:1.92;
  color:#2B3138;position:relative}
.deck::before{content:"摘　要";display:block;font-family:"Noto Sans SC",sans-serif;
  font-size:11.5px;letter-spacing:.42em;color:var(--olive);margin-bottom:11px}

/* 目录 */
.toc{background:transparent!important;border:1px solid var(--line)!important;
  border-radius:9px!important;padding:20px 26px!important;margin:26px 0 46px!important}
.toc .tl{font-family:"Noto Sans SC",sans-serif;font-size:11px;letter-spacing:.44em;
  color:var(--olive)!important;margin-bottom:12px}
.toc a{display:block;padding:7px 0;color:var(--ink2)!important;font-size:15px;
  text-decoration:none;border-bottom:1px dashed rgba(21,24,28,.11)}
.toc a:last-child{border-bottom:0}
.toc a:hover{color:var(--olive3)!important;padding-left:4px;transition:padding .15s}

/* 章节标题：编号悬挂在版心左侧，正文左缘齐整 */
h2{font-size:22.5px;margin:60px 0 20px;padding:0 0 10px;line-height:1.5;
  border-left:0!important;border-bottom:1px solid var(--line2);
  color:var(--olive3);scroll-margin-top:72px;font-weight:700}
h3{font-size:18px;margin:34px 0 13px;color:#2B3A44;font-weight:700;line-height:1.6}
h4{font-size:16.5px;margin:26px 0 10px;color:var(--olive);font-weight:700}
hr{border:0;border-top:1px solid var(--line);margin:44px 0}

/* 来源盒 */
.src{margin:56px 0 8px;padding:26px 28px;border:1px solid var(--line);
  border-radius:11px;background:var(--card)}
.src .sl{font-family:"Noto Sans SC",sans-serif;font-size:11px;letter-spacing:.4em;
  color:var(--olive)!important;margin-bottom:9px}
.src .sd{font-size:14.5px;color:var(--ink2);line-height:1.9;margin:0 0 16px}
.src a.one{display:block;text-decoration:none;padding:15px 0;
  border-top:1px dashed rgba(21,24,28,.15)}
.src a.one .k{font-family:"Noto Sans SC",sans-serif;font-size:11.5px;
  color:var(--olive)!important;letter-spacing:.12em}
.src a.one .t{font-size:16px;font-weight:700;color:var(--olive3)!important;margin:5px 0 5px}
.src a.one .g{font-size:14.3px;color:var(--ink2);line-height:1.85}
.src a.one:hover .t{text-decoration:underline}

.endbox{border-top:1px solid var(--line);margin-top:52px;padding:36px 20px;
  color:var(--ink3);text-align:center;font-size:14px}
.endbox a{color:var(--olive)!important}
footer{border-top:1px solid var(--line);color:var(--ink3);font-size:12.5px}
#totop{background:var(--olive)!important}

/* 参考文献悬挂缩进 · 注释小一号（由 JS 加类） */
.wrap .refs p{padding-left:2em;text-indent:-2em;font-size:15.4px;line-height:1.85;
  margin:0 0 10px;text-align:left}
.wrap .notes p{font-size:15.6px;line-height:1.88}

@media(max-width:720px){
  .art{padding:44px 18px 16px}
  .wrap{padding:4px 18px 40px}
  .wrap p{font-size:16.3px}
  h2{font-size:20px;margin:46px 0 16px}
}
@media(prefers-color-scheme:dark){
  :root{--ink:#E6E7E1;--ink2:#A8AEA4;--ink3:#858C82;
        --paper:#171A16;--card:#1E221C;--line:rgba(230,231,225,.14);
        --line2:rgba(126,154,85,.34);--olive:#93AE6A;--olive2:#A8C077;--olive3:#B6CB8C}
  .deck{color:#D6DACD}
  .src a.one .t{color:var(--olive3)!important}
  .wrap strong,.wrap b{color:#fff}
}
</style>
<script>
/* 给「注释」「参考文献」两节的段落加类，以便悬挂缩进与字号区分。
   只按标题文本判断，不改动任何正文。 */
(function(){
  var hs=document.querySelectorAll('.wrap h2');
  for(var i=0;i<hs.length;i++){
    var t=(hs[i].textContent||'').replace(/\\s/g,'');
    var cls = /^注释/.test(t) ? 'notes' : (/^参考文献/.test(t) ? 'refs' : null);
    if(!cls) continue;
    var n=hs[i].nextElementSibling;
    while(n && n.tagName!=='H2'){ n.classList.add(cls); n=n.nextElementSibling; }
  }
})();
</script>
"""


def apply(slug: str) -> str:
    p = CF / slug / "index.html"
    t = p.read_text(encoding="utf-8")
    if MARK in t:
        # 已装过皮肤：整段换新，便于反复迭代
        i = t.index(MARK)
        j = t.index("</script>", i) + len("</script>")
        t = t[:i] + SKIN.strip() + t[j:]
        p.write_text(t, encoding="utf-8")
        return "更新"
    assert "</head>" in t, f"{slug}: 无 </head>"
    t = t.replace("</head>", SKIN + "</head>", 1)
    assert t.count("<html") == 1 and t.count("</html>") == 1
    p.write_text(t, encoding="utf-8")
    return "新装"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    slugs = ([d.name for d in sorted(CF.iterdir()) if d.is_dir()]
             if a.all else [a.slug])
    for s in slugs:
        print(f"  {s:<28s} {apply(s)}")


if __name__ == "__main__":
    main()
