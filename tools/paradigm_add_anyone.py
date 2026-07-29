# -*- coding: utf-8 -*-
"""把《别人怎么成的，学不来；别人怎么垮的，学得来》并入「每日必读」栏目，作「之二十八」。

沿用本栏既定形制：以 taken-out/index.html 为版式模板（进度条·目录·来源盒·回顶），
PDF 与 read.html 同批产出，栏目页追加一张卡。
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = Path("/home/claude/pz/P29.txt")
SLUG = "anyone-can-do-it"
PUBDATE = "2026年7月29日"
NO_CN = "之 二 十 九"
NO_CARD = "之二十九"
FIELDS = "改编理论 × 照护社会学 × 中国经济史（本篇是群内碰撞：三位不同学员）"

TITLE = "谁来做都一样，未必是坏消息"
SUB = "一件事里同时有三样东西——非本人做不可的、换谁做都该一样的、必须让不认识的人拿去用的；它们方向相反，而我们只有一套办法"
DECK = ("一位说：这一步别人替你做了，就等于取消了它。一位说：正相反，有一样很要紧的东西，"
        "恰恰要靠「不是同一个人」才长得出来。一位说：你们争的不是好不好，是活不活得下去——"
        "留在个人身上的门道，压力一来会无声蒸发，连尸体都没有。三方各有硬证据，谁也说服不了谁。"
        "本文认为他们说的根本不是同一样东西：任何一件真正需要人的工作里，同时跑着**动作、规矩、记档**三样，"
        "而它们的脾气正好相反——**动作怕离开人，规矩怕离不开人，记档怕离不开我们这一拨人**。"
        "麻烦在于三样在现场长得一模一样，都表现为「这个人做得好」；"
        "于是我们用同一套办法去搬三样，搬错方向的每一种做法，当期成绩都很好看。")

COLLIDE = ("三方的证据都硬，且都能当场验："
           "第一位可以让你把那段书读一遍、再看那段电影，你自己知道差在哪儿；"
           "第二位可以带你去看那个四岁半的女孩，四个月下来她确实变了，而变的条件恰恰是每次不是同一个阿姨；"
           "第三位把苏州与济南摆在一起——同一套制度，一个跟官府磨了几个月且留下碑刻，一个几个月星散无痕。"
           "既然三方都对，问题就不在谁错，而在他们各自手里拿的是同一件工作里的**不同零件**："
           "第一位说的是那道必须本人执行的工序，第二位说的是那套跟谁都无关才生效的次序，"
           "第三位说的是那份必须能被外人援引的凭据。三根轴互不平行，却同时穿过我们做的几乎每一件事。")

SOURCES = [
    ("改编理论 · 认知诗学 · 秦莉",
     "工序的不可代偿性：论《追忆似水年华》改编中一道不可能被影像代劳的感知义务",
     "/students/qin-li/obligatory-perceptual-work/",
     "书里的句子把必须由读者亲手完成的挂接、否定与时态判断编进了结构；导演把那条从触发到认出的路替观众走完，不是让它变容易，是取消了它。"),
    ("照护社会学 · 孔凡鹤",
     "接住感：社区换工照护不能给「托住」，但能给另一种未被命名的安全",
     "/students/kong-fanhe/catch-feeling/",
     "短时、可替换、程序优先的临时看管长不出家庭式依恋，却能靠「每次都一样」在孩子身上沉出「外界会按约定接下我」的预期；要求「有温度」恰恰拿走了它的原料。"),
    ("中国经济史 · 鲍锦朝",
     "通货性：解释中国经济韧性的一种知识基础视角",
     "/students/bao-jinchao/knowledge-currency/",
     "一行的门道有没有从家族、师徒、同乡圈子里被拿出来、成为谁都可以援引比对的东西，决定了它在汲取压力下是阶梯式退让并留下记录，还是无声蒸发、事后找不到任何痕迹。"),
]

SIBLING = ("本栏已有几篇容易与本篇混读，把分工写清。"
           "**之二十八**《别人怎么成的，学不来》讲的是**一个结论能不能在别的地方也成立**（单位是结论）；"
           "本篇的单位是**一件工作内部的零件**——不问这条经验能不能搬到别处，只问这一部分本来就该跟人走、该离开人、还是该离开我们这一拨人。"
           "**之二十五**《传得下去的，都是没做完的》说传下去的必须留一处承重的空白；"
           "本篇的补充是：**留空白是「动作」那一样的传法，不是三样通用的传法**——规矩与记档恰恰要传得越满越好，"
           "一份留了空白的核对表、一份说理含混的判决书都是灾难。"
           "**之一**《一拿出来，就不是它了》说一样东西离开现场就不是它了，因此验证、传递、占有同生共死；"
           "本篇多走一步：**拿出来之后剩下的不是零，是另外两样东西**，它们不是残骸，各有各的活法。"
           "**之十二**《交出去的不止那件事》问委托之后验收能力还在不在（对象是能力），"
           "**之十三**《扶一把，和替他站着》问支持有没有留出力的地方（对象是位置）；"
           "本篇问的是**这件事里一共有几样东西、各自该往哪个方向去**。")

CARDS_AFTER = 0  # 运行时按现状+1 计算
BANNED = ("发生学", "发现学", "发生论", "本体论", "存在论", "显露", "纠缠", "裂缝",
          "金点子", "回写", "差异序列", "显露", "纠缠", "发生学", "本体论", "金点子", "差异序列", "SDE")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def load_md():
    """把 一、xxx 形式的源稿转成 markdown 结构。"""
    lines = [x.rstrip() for x in SRC.read_text(encoding="utf-8").splitlines()]
    # 源稿前两行是题与副题，已由 TITLE/SUB 承担，不进正文
    while lines and not re.match(r"^[一二三四五六七八九十]+、", lines[0].strip()):
        lines.pop(0)
    out = []
    for x in lines:
        s = x.strip()
        if not s:
            out.append("")
            continue
        if s.startswith("摘要：") or s.startswith("关键词："):
            continue          # 本栏惯例：正文不放摘要与关键词，导语（deck）承担这个功能
        if re.match(r"^[一二三四五六七八九十]+、", s) and len(s) < 60:
            out.append("## " + s.split("、", 1)[1])
            continue
        out.append(s)
    return "\n".join(out)


def md_to_html(md):
    out, para, toc, n = [], [], [], 0

    def flush():
        if para:
            out.append("<p>" + strongify(" ".join(para)) + "</p>")
            para.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 2:
                n += 1
                out.append(f'<h2 id="s{n}">{strongify(txt)}</h2>')
                toc.append((f"s{n}", txt))
            else:
                out.append(f"<h{lvl}>{strongify(txt)}</h{lvl}>")
            continue
        para.append(line.strip())
    flush()
    return "".join(out), toc


def build_page(body, toc, pages, wan):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB} · 每日必读 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(DECK[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    # 模板里 art-sub 是 <div> 不是 <p>——两种都认，否则会留着模板自带的副标题
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">王德生 ＋ Claude · 约 {wan} 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">每 日 必 读 · 典 范 文 · {NO_CN}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n" + body
         + f'\n<hr>\n<h2 id="sib">附：与本栏另外几篇的关系</h2><p>{strongify(SIBLING)}</p>\n'
         + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{html.escape(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇由哪三篇撞成</div>'
               f'<p class="sd">{strongify(COLLIDE)}</p>{ones}</div>\n', t, flags=re.S)

    assert t.count("<html") == 1 and t.count("</html>") == 1
    # 行话零容忍只查本篇内容（站名 SDE Universes 在模板 chrome 里，扫全页会误报）
    mine = body + DECK + COLLIDE + SIBLING + TITLE + SUB + "".join(
        k + ti + g for k, ti, _u, g in SOURCES)
    hit = [w for w in BANNED if w in body]   # 只查正文；来源盒里是三篇原标题，属引用
    assert not hit, f"本篇正文残留行话：{hit}"
    return t


def build_print(body):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>{TITLE}</title>
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
<h1>{TITLE}</h1><div class="sub">{SUB}</div>
<div class="by">王德生 ＋ Claude　·　{PUBDATE}　·　SDE Universes 每日必读 · 典范文 · {NO_CN}</div>
<div class="src"><b>本篇由这三篇撞成</b><ol>{''.join(
    f'<li>《{ti}》—— {k}：{g}</li>' for k, ti, u, g in SOURCES)}</ol>{strongify(COLLIDE)}</div>
{body}
<hr><h2>附：与本栏另外几篇的关系</h2><p>{strongify(SIBLING)}</p>
</body></html>"""


def add_card(pages, wan):
    f = PZ / "index.html"
    t = f.read_text(encoding="utf-8")
    before_cards = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    who = ("三篇来源分属"
           + "、".join(f'<a href="/students/{u.split("/")[2]}/" style="color:var(--clay)">{n}</a>'
                      for n, u in [("秦莉", SOURCES[0][2]), ("孔凡鹤", SOURCES[1][2]), ("鲍锦朝", SOURCES[2][2])])
           + "三位学员")
    card = (f'<div class="item"><div class="n">{NO_CARD} · 三学科交叉：{FIELDS}</div>'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK)}</p>'
            f'<div class="trio">{trio}</div>'
            f'<a class="rdmore" href="/paradigm/{SLUG}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · 作者 王德生 ＋ Claude · '
            f'发表于{PUBDATE} · {who}</div></div>\n')
    a = "</main>"
    assert t.count(a) == 1
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before_cards + 1, f'插入后卡片数 {t.count(chr(39)+chr(99)+chr(108)+chr(97)+chr(115)+chr(115)+chr(61)+chr(34)+chr(105)+chr(116)+chr(101)+chr(109)+chr(34)+chr(39))}，应为 {before_cards + 1}'
    f.write_text(t, encoding="utf-8")
    print(f"  栏目页：追加一张卡，现共 {t.count('class=\"item\"')} 篇")


def main():
    md = load_md()
    body, toc = md_to_html(md)
    n = len(re.sub(r"<[^>]+>", "", body))
    wan = round(n / 10000, 1)
    d = PZ / SLUG
    d.mkdir(exist_ok=True)

    pf = d / "_p.html"
    pf.write_text(build_print(body), encoding="utf-8")
    pdf = d / f"{SLUG}.pdf"
    subprocess.run(["wkhtmltopdf", "--enable-local-file-access", "--encoding", "utf-8",
                    "--footer-center", "[page]", "--footer-font-size", "9", str(pf), str(pdf)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pf.unlink()
    pages = int(subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
                .stdout.split("Pages:")[1].split()[0])
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"],
                           capture_output=True, text=True).stdout
    assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"

    (d / "index.html").write_text(build_page(body, toc, pages, wan), encoding="utf-8")

    rd = (PZ / "taken-out" / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("taken-out", SLUG).replace("一拿出来，就不是它了", TITLE)
    (d / "read.html").write_text(rd, encoding="utf-8")

    add_card(pages, wan)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节")


if __name__ == "__main__":
    main()
