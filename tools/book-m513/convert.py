#!/usr/bin/env python3
"""第 513 号《SDE九宫格透镜问题分析法》（工具链由第 512 号改来）：把三审定稿全文（/home/claude/jiugong-lens/full.md）
转成 220 版式工具链的分卷稿。只做格式转换，不动正文文字。
用法：python3 tools/book-m513/convert.py [/home/claude/jiugong-lens/full.md]
产物：front/00-前置.md、parts/01-上篇.md、parts/02-中篇.md、parts/03-下篇.md、back/09-结语.md、back/10-后置.md，
以及 book.md（以上各件按序拼合，供 publish.py 数字数、build_unit 解析章）。

格式约定（全书一致）：
- 定稿的 `# 第N章 标题` → `## 第 N 章　标题`；`# 上篇　原理` 照留为编首；`# 前言 X`、`# 导读 X` → 前置里的 `## 前言　X`、`## 导读　X`；
  `# 结语 X` → `# 结语　X`；`# 附录A X` → `# 附录` 之下的 `## 附录A　X`；`# 参考书目` 照留。
- 节标题 `## 一、X`（附录里的 `## 卡一 X` 等也一样）一律转成 `### ◆ 一、X`；
  定稿里少数 `### X`（节内小标题）转成独立粗体行 `**X**`，版式排成段中小标题。
- 「这一章的问题」三种写法统一成 `> **这一章的问题**：…`；
- 章末「带走的话」「小账」（`## ` 标题式或 **粗体行** 式）统一转成引用块，条目前的 `- `、`1. ` 列表记号去掉；
- 分隔线 `---` 去掉（分篇与分章已由版式承担）。
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from meta import NO, ISBN, PRICE, SRC as DEFAULT_SRC  # noqa: E402

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC)

CPMETA = [
    ('书名', '《SDE九宫格透镜问题分析法》'),
    ('英文书名', 'The SDE Nine-Grid Lens Method of Problem Analysis'),
    ('著者', '王德生'),
    ('执笔', '王德生立题并口述承重命题与口径；文字由 AI（Claude）协作成稿，十五路分章执笔，经统稿、审校、复审、终审三审与文献核对'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 %d 号' % NO),
    ('ISBN', ISBN),
    ('定价', PRICE),
    ('开本', '170 mm × 240 mm'),
    ('字数', '约 31 万字'),
    ('版次', '2026 年 10 月第 1 版'),
]
CPNOTES = [
    'AI 协作声明：本书由王德生立题，承重命题与口径由他口述；文字在其指令下由 AI（Claude）协作成稿，十五路分章执笔，经统稿、审校、复审、终审三审与文献核对。书中所引各家理论只述大意，不替任何学者编原话。',
    '书中小林、林姐、老周、阿敏、陈老师等人物与场景均为构想，不当证据。本书不作心理或医学诊断，健康例子只讲行为与习惯的发生；书中读数只给本人、家人与老师自看，不进考核。平谱失效、桥协同、九组共线优势等是本书提出的待检猜想，尚无数据。',
    '全书结构：出版信息、作者介绍、前言、导读、目录；上篇原理（第 1—7 章）、中篇方法（第 8—17 章）、下篇案例（第 18—24 章）；结语、附录 A—D、参考书目。',
    '版权所有　侵权必究',
]
AUTHOR_BIO = [
    '王德生（Desheng Wang），博士，SIO 本体论与 SDE 发生学创立者。',
    '湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后。曾任英国斯旺西大学高级研究员、新加坡南洋理工大学数学系助理教授（博士生导师）与资深研究科学家。在计算数学与图形学国际期刊发表论文 47 篇。',
    '现任德麦国际（Demai International Pte. Ltd.，新加坡）创始人、董事长，主持 SDE Universes 平台（sdeuniverses.com）。',
]

MARKERS = ('带走的话', '小账')


def marker_of(l):
    s = l.strip()
    m = re.fullmatch(r'(?:#{2,3} |\*\*)(带走的话|小账)(?:\*\*)?', s)
    return m[1] if m else None


def question(l):
    """「这一章的问题」三种写法 → `> **这一章的问题**：X`。"""
    s = l.strip()
    m = re.match(r'^(\*\*)?这一(章|篇)的问题(\*\*)?[：:](\*\*)?\s*(.*)$', s)
    if not m:
        return None
    body = m[5]
    if m[1] and not m[3] and not m[4] and body.endswith('**'):
        body = body[:-2]
    return '> **这一%s的问题**：%s' % (m[2], body.strip())


def fmt(text, appx=False):
    out = []
    L = text.split('\n')
    i = 0
    while i < len(L):
        l = L[i]
        if l.strip() == '---':
            i += 1; continue
        mk = marker_of(l)
        if mk:
            out.append('> **%s**' % mk); i += 1
            while i < len(L):
                x = L[i]
                if x.startswith('#') or x.strip() == '---' or marker_of(x):
                    break
                if x.strip():
                    out.append('> ' + re.sub(r'^(?:- |\d+\. )', '', x.strip()))
                i += 1
            out.append('')
            continue
        q = question(l)
        if q:
            out.append(q); i += 1; continue
        m = re.match(r'^## (.*)$', l)
        if m:
            out.append('### ◆ ' + m[1].strip()); i += 1; continue
        m = re.match(r'^### (.*)$', l)
        if m:
            out.append('**%s**' % m[1].strip()); i += 1; continue
        out.append(l); i += 1
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip() + '\n'


def h1_split(raw):
    """按 `# ` 一级标题切块，返回 [(标题, 正文)]。"""
    out = []
    for blk in re.split(r'\n(?=# )', '\n' + raw):
        blk = blk.strip('\n')
        if not blk:
            continue
        head, _, body = blk.partition('\n')
        out.append((head[2:].strip(), body))
    return out


def main():
    raw = SRC.read_text()
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)
    blocks = h1_split(raw)
    names = [t for t, _ in blocks]
    assert names[0].startswith('前言') and names[1].startswith('导读'), names[:2]
    # 前置
    front = []
    for t, b in blocks[:2]:
        nm, _, sub = t.partition(' ')
        front.append('## %s　%s\n\n%s' % (nm, sub.strip(), fmt(b)))
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text(cp + '\n\n' + au + '\n\n' + '\n'.join(front))
    # 三篇
    (HERE / 'parts').mkdir(exist_ok=True)
    parts, cur, nums = [], None, []
    jieyu, appx, bib = None, [], None
    for t, b in blocks[2:]:
        if re.match(r'^[上中下]篇　', t):
            cur = ['# ' + t + '\n']; parts.append(cur)
            assert not b.strip(), '篇首另有导语：' + t
            continue
        m = re.match(r'^第(\d+)章 (.*)$', t)
        if m:
            n = int(m[1]); nums.append(n)
            cur.append('## 第 %d 章　%s\n\n%s' % (n, m[2].strip(), fmt(b)))
            continue
        if t.startswith('结语'):
            nm, _, sub = t.partition(' ')
            jieyu = '# 结语　%s\n\n%s' % (sub.strip(), fmt(b)); cur = None
            continue
        m = re.match(r'^(附录[A-D]) (.*)$', t)
        if m:
            appx.append('## %s　%s\n\n%s' % (m[1], m[2].strip(), fmt(b, appx=True)))
            continue
        if t == '参考书目':
            bib = '# 参考书目\n\n' + fmt(b)
            continue
        raise SystemExit('未识别的一级标题：' + t)
    assert nums == list(range(1, 25)), nums
    assert len(parts) == 3 and len(appx) == 4 and jieyu and bib
    PN = ['01-上篇', '02-中篇', '03-下篇']
    for k, p in enumerate(parts):
        (HERE / ('parts/%s.md' % PN[k])).write_text('\n'.join(p).strip() + '\n')
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/09-结语.md').write_text(jieyu)
    (HERE / 'back/10-后置.md').write_text('# 附录\n\n' + '\n'.join(appx) + '\n' + bib)
    files = ['front/00-前置.md'] + ['parts/%s.md' % x for x in PN] + ['back/09-结语.md', 'back/10-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    # 字数核对：转换前后汉字数只差前置里新加的出版信息与作者介绍
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    add = han((HERE / 'front/00-前置.md').read_text().split('## 前言')[0])
    print('ok: 3 parts, chapters', nums[0], '-', nums[-1], '| hanzi src', han(raw), 'book', han((HERE / 'book.md').read_text()), 'added', add,
          '| diff', han((HERE / 'book.md').read_text()) - add - han(raw))


if __name__ == '__main__':
    main()
