#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从磁盘重建 public/students/roster.json。

为什么存在这个脚本
------------------
roster.json 是**派生数据**：谁发了哪篇、哪天发的、多少字，这些事实已经全部写在
已发布的页面里了。以前它靠手工维护，于是必然有两种死法：

  1. 漏更 —— 发表提交忘了带上 roster（commit 823c99e / 7-16 那批 / 秦莉今天两条）；
  2. 撞车 —— 两个 agent 同时改这一个文件，rebase 冲突；手工解冲突时一不小心
     就把对方的数据整段抹掉（用错 --ours/--theirs 即可，方向极易搞反）。

改成"从磁盘派生"之后，这两种死法一起消失：
  · 漏更不可能 —— 页面在磁盘上，扫描就能看见，不依赖任何人记得更新；
  · 撞车可自动化解 —— 论文页各在各的路径、天然不冲突，合并后磁盘已是双方成果的
    并集；此时只要重跑本脚本，输出就是正确的并集。任选一边收下冲突再重跑即可，
    绝不会丢数据。

哪些字段仍是手工的
------------------
slug / name / small / enrolled_order 是学员身份信息，磁盘上推不出来，继续由
roster.json 承载（新学员报名时才动）。本脚本只覆盖 papers[] 与 count。

用法
----
    python3 tools/build_roster.py            # 重建并写回
    python3 tools/build_roster.py --check    # 只比对不写（CI/提交前自检，有差异则退出码 1）
"""
import json, os, re, subprocess, sys, datetime
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDENTS = os.path.join(ROOT, 'public', 'students')
ROSTER = os.path.join(STUDENTS, 'roster.json')

# 索引页约定名：这些目录是"目录页"，不是作品本身
INDEX_NAMES = {'works', 'submit', 'starter-template',
               # 学员级频道的容器页（卡片目录，不是作品本身）
               'tcm-philosophy', 'cinema-literature', 'precision-medicine',
               'risk-and-care', 'conflict-peace', 'cancer', 'chronic-disease'}

# 频道容器页的机器可读标记。新建学员级频道时在 hub 页 <head> 里放一行
#     <meta name="sde-page-kind" content="channel">
# 即可被本脚本自动排除，不必再往上面那张名单里手工加名字。
CHANNEL_MARK = 'name="sde-page-kind" content="channel"'

# 页面骨架：这些标签/类下的文字不算正文字数
SKIP_TAGS = {'script', 'style', 'nav', 'footer', 'head'}
SKIP_CLASSES = {
    'readbar', 'topbar', 'endbox', 'foot-nav', 'navhint', 'side-tap',
    'lang-toggle', 'rb-modes', 'controls', 'nav-right', 'back', 'modes',
}


class BodyText(HTMLParser):
    """按标签与 class 跳过骨架，取正文。

    不用正则剥离骨架：`<div class="topbar">.*?</div></div>` 这类写法靠猜嵌套，
    `.*?` 会停在文档里第一个 `</div></div>`，把正文整段吞掉（黑咖啡那首诗就是
    这么从 319 字缩成 31 字的）。改为跟踪真实标签深度。
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf = []
        self.skip_depth = 0     # >0 表示正处在被跳过的子树里
        self.stack = []         # (tag, 是否是本次跳过的起点)

    def handle_starttag(self, tag, attrs):
        starts_skip = False
        if self.skip_depth == 0:
            cls = dict(attrs).get('class', '') or ''
            names = set(cls.split())
            if tag in SKIP_TAGS or (names & SKIP_CLASSES):
                starts_skip = True
                self.skip_depth = 1
        elif tag not in ('br', 'img', 'hr', 'meta', 'link', 'input'):
            self.skip_depth += 1
        if tag not in ('br', 'img', 'hr', 'meta', 'link', 'input'):
            self.stack.append((tag, starts_skip))

    def handle_endtag(self, tag):
        while self.stack:
            t, starts = self.stack.pop()
            if t == tag:
                if starts:
                    self.skip_depth = 0
                elif self.skip_depth > 0:
                    self.skip_depth -= 1
                break

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.buf.append(data)

    def text(self):
        return re.sub(r'\s+', '', ''.join(self.buf))



def is_leaf_item(d):
    """含 index.html 且其下再无 index.html 子目录 → 一件作品。"""
    if not os.path.exists(os.path.join(d, 'index.html')):
        return False
    for sub in os.listdir(d):
        p = os.path.join(d, sub)
        if os.path.isdir(p) and os.path.exists(os.path.join(p, 'index.html')):
            return False
    return True


def find_items(slug_dir):
    """返回该学员的全部作品目录（递归，跳过索引页约定名）。"""
    out = []

    def walk(d):
        idx = os.path.join(d, 'index.html')
        children = [
            os.path.join(d, name)
            for name in sorted(os.listdir(d))
            if name not in INDEX_NAMES and os.path.isdir(os.path.join(d, name))
        ]
        indexed_children = [
            child for child in children
            if os.path.exists(os.path.join(child, 'index.html'))
        ]

        if os.path.exists(idx):
            if CHANNEL_MARK in open(idx, encoding='utf-8').read():
                pass  # 频道容器页：是卡片目录，不是作品
            elif not indexed_children:
                out.append(d)
            else:
                # A published paper may also contain application sub-papers.
                # Count the parent when it carries an article signature; plain
                # collection pages (for example essays/ and poems/) stay excluded.
                source = open(idx, encoding='utf-8').read()
                if (
                    'sde-submission-id' in source
                    or re.search(r'class=["\'][^"\']*\breadbar\b', source)
                ):
                    out.append(d)

        for child in children:
            walk(child)

    for name in sorted(os.listdir(slug_dir)):
        d = os.path.join(slug_dir, name)
        if os.path.isdir(d) and name not in INDEX_NAMES:
            walk(d)
    return out


_git_cache = {}


def git_added_date(path):
    """该文件首次进入仓库的日期——发表日期的兜底来源。"""
    if path in _git_cache:
        return _git_cache[path]
    try:
        r = subprocess.run(
            ['git', 'log', '--diff-filter=A', '--follow', '--format=%as', '--', path],
            cwd=ROOT, capture_output=True, text=True, timeout=30)
        lines = [l for l in r.stdout.strip().split('\n') if l]
        d = lines[-1] if lines else None
    except Exception:
        d = None
    _git_cache[path] = d
    return d


def published_date(idx):
    """优先取页面自报的发表日期（发表规格的强制字段），缺则用 git 首次提交日兜底。"""
    s = open(idx, encoding='utf-8').read()
    m = re.search(r'发表于\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", 'page'
    m = re.search(r'Published\s+([A-Z][a-z]{2})\w*\s+(\d{1,2}),\s*(\d{4})', s)
    if m:
        mon = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(m.group(1)) + 1
        return f"{m.group(3)}-{mon:02d}-{int(m.group(2)):02d}", 'page'
    d = git_added_date(os.path.relpath(idx, ROOT))
    return d, 'git'


def paper_weight(idx):
    """页面自报的计分权重（相当于几篇标准论文）。

    为什么放在页面里：roster.json 是派生数据，每次内容 push 都由本脚本从磁盘重建，
    手写进 roster 的字段必被覆盖。长篇专著/小说这类"一件顶多篇"的作品，权重必须与
    页面同在，才能在自动重建后存活。

        <meta name="sde:paper-weight" content="20">
    """
    s = open(idx, encoding='utf-8').read()
    m = re.search(r'<meta\s+name=["\']sde:paper-weight["\']\s+content=["\']([\d.]+)["\']', s)
    if not m:
        return None
    try:
        w = float(m.group(1))
    except ValueError:
        return None
    if w <= 0 or w > 100:      # 明显写错的挡掉，不让它污染排名
        return None
    return int(w) if w == int(w) else w


try:
    from classify_fields import classify as _classify_field
except ImportError:                                   # 与本文件同目录，CI 里以 tools/ 为 cwd 之外调用时兜底
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from classify_fields import classify as _classify_field


def paper_field(idx):
    """把这篇归入一张固定的一级领域表（见 tools/classify_fields.py）。

    为什么不用页面眉题里的学科标签：那是每篇自造的长复合标签，不是分类——
    高鹏 74 篇能产出 49 个「领域」，而黄倩盈、胡敏、张琼的眉题里根本没有学科字段。
    按标签数算广度会得出与事实相反的结论，所以改由标题＋关键词＋摘要归类。
    """
    f, _n = _classify_field(idx)
    return f


def paper_iq(idx):
    """页面自报的 SDE 创新智商分及其口径。

    与 sde:paper-weight 同理：roster.json 是派生数据，手写字段必被本脚本覆盖，
    所以分数只能从页面里抽。全站现有三种写法，口径不同，必须分开标：

        「SDE 创新智商 136 → 打磨目标 146」  前者=原稿盲评，后者=打磨目标（不计分）
        「本文的盲评分为 132」               盲评
        「SDE 创新智商 138（原稿盲评…）」    盲评
        「SDE 创新智商：149」               旧 Codex 单值，口径不明 → legacy，不进排名

    返回 (分数, 口径) 或 (None, None)。排名公式只采用 kind == 'blind'。
    """
    s = open(idx, encoding='utf-8').read()
    t = re.sub(r'<[^>]+>', '', s)
    m = re.search(r'创新智商[：:\s]*(\d{3})\s*(?:→|-&gt;|->)', t)
    if m:
        return int(m.group(1)), 'blind'
    m = re.search(r'盲评分为\s*(\d{3})', t)
    if m:
        return int(m.group(1)), 'blind'
    m = re.search(r'创新智商[：:\s]*(\d{3})\s*[（(]\s*原稿盲评', t)
    if m:
        return int(m.group(1)), 'blind'
    # 「SDE 创新智商　盲评 134 → 修改设计目标 136」/「盲评 137 → 加固后 138」
    # 箭头左边是原稿盲评，右边是编辑增补后的修改设计目标（不计分）
    m = re.search(r'创新智商[：:\s\u3000]*盲评\s*(\d{3})', t)
    if m:
        return int(m.group(1)), 'blind'
    # 「关于本文的创新智商标注　本文在未经任何编辑改动的原稿状态下接受过一次盲评…按固定权重计算的综合分为 130」
    m = re.search(r'创新智商标注[\s\S]{0,600}?综合分为\s*(\d{3})', t)
    if m:
        return int(m.group(1)), 'blind'
    # 「SDE 创新智商 138　全文盲评 · 待独立复核」/「…结构化盲评…」
    # 分数后面紧跟口径标签的写法：标了盲评就是盲评，不能落进 legacy 兜底。
    m = re.search(r'创新智商[：:\s\u3000]*(\d{3})[\s\u3000]*(?:全文盲评|结构化盲评|盲评)', t)
    if m:
        return int(m.group(1)), 'blind'
    m = re.search(r'创新智商[：:\s]*(\d{3})', t)
    if m:
        return int(m.group(1)), 'legacy'
    return None, None


def body_chars(idx):
    """正文字数：跳过骨架后数字符（CJK 一字算一字）。"""
    p = BodyText()
    p.feed(open(idx, encoding='utf-8').read())
    return len(p.text())


def build():
    roster = json.load(open(ROSTER, encoding='utf-8'))
    for stu in roster['students']:
        d = os.path.join(STUDENTS, stu['slug'])
        if not os.path.isdir(d):
            stu['papers'], stu['count'] = [], 0
            continue
        papers = []
        for item in find_items(d):
            idx = os.path.join(item, 'index.html')
            date, src = published_date(idx)
            if not date:
                print(f"  ⚠ 无法确定发表日期，跳过: {os.path.relpath(item, STUDENTS)}", file=sys.stderr)
                continue
            rec = {'slug': os.path.relpath(item, STUDENTS).replace(os.sep, '/'),
                   'date': date, 'words': body_chars(idx)}
            iq, kind = paper_iq(idx)
            if iq is not None and 80 <= iq <= 175:
                rec['iq'], rec['iq_kind'] = iq, kind
            fld = paper_field(idx)
            if fld:
                rec['field'] = fld
            # 诗歌与论文同权：排名公式给 type=poem 记 depth 1.0，不按篇幅折算。
            # 站上的约定是诗歌收在该生的 poems/ 目录下。
            if os.path.basename(os.path.dirname(item)) == 'poems':
                rec['type'] = 'poem'
            w = paper_weight(idx)
            if w is not None:
                rec['weight'] = w
            papers.append(rec)
        papers.sort(key=lambda p: (p['date'], p['words']), reverse=True)
        stu['papers'] = papers
        # count 是**加权篇数**，不是页面数（王德生 2026-08-07 裁定：专著按十篇论文计算）。
        # 权重来自页面自报的 <meta name="sde:paper-weight">，缺省为 1。
        # 一部专著抵十篇写在专著条目页里，因此本脚本从磁盘重建后权重仍然存活；
        # 想知道有多少个页面，用 len(papers)，别用 count。
        stu['count'] = sum(p.get('weight', 1) for p in papers)
        stu['items'] = len(papers)
    roster['students'].sort(key=lambda s: s['enrolled_order'])
    roster['updated'] = datetime.date.today().isoformat()
    return roster


def dump(r):
    return json.dumps(r, ensure_ascii=False, indent=2) + '\n'


if __name__ == '__main__':
    new = build()
    text = dump(new)
    if '--check' in sys.argv:
        cur = open(ROSTER, encoding='utf-8').read()
        if cur == text:
            print('[OK] roster.json 与磁盘一致')
            sys.exit(0)
        print('roster.json 与磁盘不一致 ❌ —— 请运行 python3 tools/build_roster.py', file=sys.stderr)
        old = json.load(open(ROSTER, encoding='utf-8'))
        om = {s['slug']: s['count'] for s in old['students']}
        for s in new['students']:
            if om.get(s['slug']) != s['count']:
                print(f"  {s['name']}({s['slug']}): roster {om.get(s['slug'])} → 磁盘 {s['count']}", file=sys.stderr)
        sys.exit(1)
    open(ROSTER, 'w', encoding='utf-8').write(text)
    total = sum(s['count'] for s in new['students'])
    print(f"roster.json 已重建：{len(new['students'])} 名学员 · 作品合计 {total} 件")
