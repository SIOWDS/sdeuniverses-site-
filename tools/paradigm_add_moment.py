# -*- coding: utf-8 -*-
"""把《懂了，是一个时刻，还是一段路》并入「每日必读」。

与本栏此前各篇的两处不同，都要在页面上如实标出、不许含糊：
  ① **作者只署王德生**（用户当次明确"作者是王德生"）。此前各篇是 Claude 在王博士指导下
     对站内文章做二阶碰撞的产物，故署"王德生 ＋ Claude"；这一篇的底稿是王德生本人的长文，
     助手做的是打磨与补切，不是共同作者。
  ② **不是三篇碰撞**。本栏惯例是由站内三篇互相矛盾的文章撞成，这一篇不是。
     所以来源盒改成「来处与站内对读」：老实写明它是本人长文，并列出站内三篇最贴身的
     已发篇目直链回去——那三篇不是它的原料，是它的对手，正文里专设一章逐条交代分离线。
     把这一栏写成"由哪三篇撞成"会是一句假话。
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
PZ = ROOT / "public" / "paradigm"
TPL = PZ / "taken-out" / "index.html"
SRC = ROOT / "tools" / "paradigm_moment_body.txt"
SLUG = "moment-or-road"
PUBDATE = "2026年7月30日"
FIELDS = "教育 × 组织 × 语言哲学 × 急救医学（四域交叉）"
BYLINE = "王德生"

TITLE = "懂了，是一个时刻，还是一段路"
SUB = ("同一句「我懂了」，落在两种时间里就是两样东西：一种把懂当成一个能在某一刻完成的事件，"
       "有终点、有判定；一种把懂当成一段只能在时间里展开的过程，有方向而没有终了。"
       "你从没专门做过这个选择，但它比任何观点都更早落下——它预先决定了你的理解"
       "能不能被共享、能不能被判别、会不会在正在长的时候被一刀判死。")
DECK = ("两间会议室开同一个会：一间四十分钟就「达成共识」，散会没人回头看白板；"
        "一间谈了一上午谁也没宣布达成，却有三个人留下来继续画图。三个月后出意外，"
        "前一间的第一反应是「再开一次会」。差别不在沟通技巧，在两组人进门之前就已经定下的一件事——"
        "**他们对「懂」这回事抱着不同的时间格式**。本文认为：把理解当成一个可完成的事件、"
        "还是一段在展开的过程，这不是两种风格，是两块不相容的地基；"
        "**它比任何答案都更早落下，并且预先决定了理解在后面所有层面上的命运**——"
        "能不能被共享、能不能被判别、会不会在还在长的时候被判成「没有」。"
        "文末给六条能推翻它的条件，第一条只要两张纸和一天。")

ORIGIN = ("**这一篇与本栏其余各篇有两处不同，须先说明。**其一，**作者只署王德生**："
          "本栏此前各篇是助手在王博士指导下对站内文章做二阶碰撞的产物，故署两个名字；"
          "这一篇的底稿是王德生本人的长文，助手做的是打磨、补切与编排，不是共同作者。"
          "其二，**它不是由三篇撞成的**。所以下面这一栏不叫「由哪三篇撞成」，"
          "而是本篇最该交代的三位站内对手——它们讲的是同一件事，各自站在不同位置上，"
          "其中一篇还对本文的二分法构成实质挑战。正文第十七章逐条交代了与它们的分离线，"
          "**包括一处本文没能补上的洞**。列在这里，是因为一篇讲「理解」的文章，"
          "最不该做的事就是装作自己第一个到场。")

SOURCES = [
    ("说法与闭合 · 黄倩盈",
     "意义的栖居：预制符号如何压缩了理解的断裂—修复过程",
     "/students/huang-qianying/meaning-habitat/",
     "一个现成的说法在断裂被充分体验之前抢先到场，人拿到了标签，却逐步失去自行编织意义路径的能力。"
     "与本文的分离线：那一篇的变量是「说法的供给」，本文的变量是「判定的格式」——两个开关，缺一个都关不严。"),
    ("理解的跃迁 · 黄倩盈",
     "逼出来的清醒：论理解活动的「逼临—相变」结构",
     "/students/huang-qianying/paper-p04-d01-a04/",
     "理解的根本跃迁不在渐进累积，而在生成结构被逼塌之后那个「旧话已死、新话未生」的悬置带，随后发生一次不可逆的相变。"
     "**这是本文的真麻烦**：相变既不是点状事件也不是平滑过程，是本文那张时间底图上没有槽位的第三种形状。"),
    ("完成与判定 · 黄倩盈",
     "理解的单方完成形态及其生态条件",
     "/students/huang-qianying/unilateral-completion/",
     "在被理解者完全不参与互校的条件下，理解者可以独自在内部完成一次完整的理解。"
     "与本文的分离线：那一篇的完成发生在理解者**内部**，本文批评的是用一个**外部判定时刻**去替代它——"
     "两者不冲突，而且正好解释了二值判别为什么两头都会错。"),
]

SIBLING = ("本栏有一篇与本篇挨得极近：《一句对的话，也能把门关上》说的是同一句说法落到人身上只做两件事之一——"
           "当探针（推他回现场）或当句号（替他把现场关掉），而决定的是接的人手里还有没有对照物。"
           "那一篇管**一句话的落点**，本篇管**那把判定的尺子**：一个人手里的尺子是二值的，"
           "他就会把送到手上的每一句话都用成句号，因为他的格式里没有第三个槽可以放「还在路上」。"
           "两篇合起来才完整——一个讲话怎么落，一个讲落地之后被什么量。另有《交出去的不止那件事》讲"
           "「发现某样东西丢了，要用到那样东西本身」，与本文最后一章那个自反的难处是同一个结构。")

BANNED = ("发生学", "发现学", "发生论", "本体论", "存在论", "显露", "纠缠", "裂缝",
          "金点子", "回写", "差异序列", "SDE", "元隐喻")


def strongify(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def load_md():
    """源稿已用 ## 标章，直接读；顺手丢掉摘要/关键词行（本栏惯例：正文不放，导语承担）。"""
    out = []
    for x in SRC.read_text(encoding="utf-8").splitlines():
        s = x.rstrip()
        if s.startswith("摘要：") or s.startswith("关键词："):
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


def build_page(body, toc, pages, wan, no_cn):
    t = TPL.read_text(encoding="utf-8")
    t = re.sub(r"<title>.*?</title>",
               f"<title>{TITLE}——{SUB[:60]} · 每日必读 | SDE Universes</title>", t, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(")',
               lambda m: m.group(1) + html.escape(re.sub(r"\*\*", "", DECK)[:190], quote=True) + m.group(2), t)
    t = re.sub(r'<h1 class="art-title">.*?</h1>', f'<h1 class="art-title">{TITLE}</h1>', t, flags=re.S)
    t = re.sub(r'<(p|div) class="art-sub">.*?</\1>', f'<div class="art-sub">{SUB}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-meta">.*?</div>',
               f'<div class="art-meta">{BYLINE} · 约 {wan} 万字 · {pages} 页 · '
               f'三种阅读方式 · 发表于{PUBDATE}</div>', t, flags=re.S)
    t = re.sub(r'<div class="art-series">.*?</div>',
               f'<div class="art-series">每 日 必 读 · 典 范 文 · {no_cn}</div>', t, flags=re.S)
    t = re.sub(r'<div class="deck">.*?</div>', f'<div class="deck">{strongify(DECK)}</div>', t, flags=re.S)

    links = "".join(f'<a href="#{i}">{html.escape(x)}</a>' for i, x in toc)
    t = re.sub(r'<div class="toc">.*?</div>\s*(?=<h2|<p|<hr)',
               f'<div class="toc"><div class="tl">目 录</div>{links}</div>\n', t, flags=re.S)

    i = t.index("</div>", t.index(links)) + 6
    j = t.index('<div class="src">')
    t = (t[:i] + "\n" + body
         + f'\n<hr>\n<h2 id="sib">附：与本栏另外两篇的关系</h2><p>{strongify(SIBLING)}</p>\n'
         + t[j:])

    ones = "".join(
        f'<a class="one" href="{u}"><div class="k">{html.escape(k)}</div>'
        f'<div class="t">{html.escape(ti)}</div><div class="g">{strongify(g)}</div></a>'
        for k, ti, u, g in SOURCES)
    t = re.sub(r'<div class="src">.*?</div>\s*(?=<div class="endbox">)',
               f'<div class="src"><div class="sl">这一篇的来处，与站内三位对手</div>'
               f'<p class="sd">{strongify(ORIGIN)}</p>{ones}</div>\n', t, flags=re.S)

    t = t.replace("作者 王德生 ＋ Claude", f"作者 {BYLINE}")
    assert t.count("<html") == 1 and t.count("</html>") == 1
    hit = [w for w in BANNED if w in body]
    assert not hit, f"本篇正文残留行话：{hit}"
    assert "王德生 ＋ Claude" not in t, "本篇只署王德生，模板署名未清干净"
    return t


def add_card(pages, wan, no_card):
    f = PZ / "index.html"
    t = f.read_text(encoding="utf-8")
    before = t.count('class="item"')
    assert SLUG not in t, "卡片已存在"
    trio = "".join(f'<div><b>{html.escape(k)}</b><a href="{u}">{html.escape(ti)}</a></div>'
                   for k, ti, u, _g in SOURCES)
    who = ('本篇非三篇碰撞，是<a href="/students/" style="color:var(--clay)">王德生</a>本人长文；'
           '所列三篇为站内最贴身的对手，正文逐条交代分离线')
    card = (f'<div class="item"><div class="n">{no_card} · 四学科交叉：{FIELDS}</div>'
            f'<h2><a href="/paradigm/{SLUG}/">{html.escape(TITLE)}</a></h2>'
            f'<p class="sub">{html.escape(SUB)}</p>'
            f'<p class="hk">{html.escape(DECK.replace(chr(42)+chr(42), ""))}</p>'
            f'<div class="trio">{trio}</div>'
            f'<a class="rdmore" href="/paradigm/{SLUG}/">读全文 →</a>'
            f'<div class="meta">约 {wan} 万字 · {pages} 页 · 三种读法 · 作者 {BYLINE} · '
            f'发表于{PUBDATE} · {who}</div></div>\n')
    a = "</main>"
    assert t.count(a) == 1
    t = t.replace(a, card + a, 1)
    assert t.count('class="item"') == before + 1
    f.write_text(t, encoding="utf-8")
    print("  栏目页：追加一张卡，现共 %d 篇" % t.count('class="item"'))


def main():
    from paradigm_ordinal import claim
    no, no_card_cn = claim(f"paradigm/{SLUG}", title=TITLE)
    no_cn = " ".join(no_card_cn)          # art-series 用逐字带空格的写法
    no_card = "之" + no_card_cn
    print(f"  领到发布号 {no}（{no_card}）")

    body, toc = md_to_html(load_md())
    n = len(re.sub(r"<[^>]+>", "", body))
    wan = round(n / 10000, 1)
    d = PZ / SLUG
    d.mkdir(exist_ok=True)

    # 页数是循环依赖：先按估值出一版页面 → 生成 PDF → 读真实页数 → 回写页面 → 再出一次 PDF
    for guess in (18, None):
        (d / "index.html").write_text(build_page(body, toc, guess or pages, wan, no_cn), encoding="utf-8")
        subprocess.run([sys.executable, "tools/build_pdf_paradigm.py",
                        f"public/paradigm/{SLUG}/index.html", "-o", f"public/paradigm/{SLUG}/{SLUG}.pdf"],
                       cwd=str(ROOT), check=True, stdout=subprocess.DEVNULL)
        from pypdf import PdfReader
        pages = len(PdfReader(str(d / f"{SLUG}.pdf")).pages)
    probe = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(d / f"{SLUG}.pdf"), "-"],
                           capture_output=True, text=True).stdout
    assert re.search(r"[\u4e00-\u9fff]", probe), "PDF 首页抽不出中文"

    rd = (PZ / "taken-out" / "read.html").read_text(encoding="utf-8")
    rd = rd.replace("taken-out", SLUG).replace("一拿出来，就不是它了", TITLE)
    rd = re.sub(r"\d+ 页 · 王德生 ＋ Claude", f"{pages} 页 · {BYLINE}", rd)
    rd = rd.replace("王德生 ＋ Claude", BYLINE)
    (d / "read.html").write_text(rd, encoding="utf-8")

    add_card(pages, wan, no_card)
    print(f"  {SLUG}: {n} 字 · {pages} 页 · 目录 {len(toc)} 节 · 署名 {BYLINE}")


if __name__ == "__main__":
    main()
