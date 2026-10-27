#!/usr/bin/env python3
"""第 471 号《舍不得——悬在半空的那一步》（高鹏著，王德生指导）：把 /home/claude/book 下的三审定稿拼成 220/302 版式工具链的分卷稿。
只做格式拼装，正文文字不动（导读第九节补一句引文核验四档的说明）：
  章题「# 第一章　题」→「## 第1章　题」，其下加「这一章的问题」框（题目取九问原题）；
  节题「## 一、题」→「### ◆ 一、题」，小节「### ◆ 题」→「#### 题」；
  章末「## 带走的话」「## 两行小账」「## 想一想」→ 三框（> **带走的话** / > **小账** / > **想一想**）；
  正文引文〔参:键〕→〔参 n〕（n 为参考书目编号，书目由 cites/final.json 生成：西文按姓氏字母，中文日文按拼音，古籍佛典另列）；
  每编前接编序、后接本编总账；附录四「引文核验总表」由 cites/final.json 生成。
产物：front/00-前置.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法：python3 tools/book-m471/assemble.py
"""
import json, re, sys, unicodedata
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
S = Path(M.SRC)
A = S / 'add'
CN = '零一二三四五六七八九十'
CNUM = {c: i for i, c in enumerate(CN)}


def han(s):
    return len(re.findall(r'[一-鿿]', s))


# ── 九问原题（每章「这一章的问题」） ──
QS = {}
for line in (S / 'src.txt').read_text().splitlines():
    m = re.match(r'^第([一二三四五六七八九])问　(.+)$', line.strip())
    if m:
        QS[CNUM[m[1]]] = m[2].strip()
assert sorted(QS) == list(range(1, 10)), QS

# ── 参考书目 ──
CITES = json.loads((S / 'cites/final.json').read_text())
CJK = re.compile(r'[一-鿿぀-ヿ]')
PINYIN = {'近藤': 'jinteng', '山下': 'shanxia', '龙树': 'longshu'}


def first_author(a):
    return re.sub(r'\s*\((eds?\.)\)', '', a.split(';')[0]).strip()


def surname(c):
    fa = first_author(c['authors'])
    if ',' in fa:
        return fa.split(',')[0].strip()
    if c['key'].startswith(('UNESCO', 'ProjectMATCH')):
        return fa
    return fa.split()[-1]


def sortkey(c):
    s = unicodedata.normalize('NFKD', surname(c))
    s = ''.join(ch for ch in s if not unicodedata.combining(ch)).lower().replace('-', '')
    return (s, c['year'] or 0, c['key'])


def is_cjk(c):
    return bool(CJK.search(first_author(c['authors'])))


western = sorted([c for c in CITES if not is_cjk(c)], key=sortkey)
cjk_classic = [c for c in CITES if is_cjk(c) and c['type'] == 'classic']
cjk_modern = sorted([c for c in CITES if is_cjk(c) and c['type'] != 'classic'],
                    key=lambda c: next(v for k, v in PINYIN.items() if c['authors'].startswith(k)))
ORDER = western + cjk_modern + cjk_classic
REF = {c['key']: i for i, c in enumerate(ORDER, 1)}
assert len(REF) == len(CITES)


def west_names(a):
    names = [x.strip() for x in a.split(';') if x.strip()]
    eds = ''
    if names and re.search(r'\(eds?\.\)', names[-1]):
        eds = ' (%s)' % re.search(r'\((eds?\.)\)', names[-1])[1]
        names[-1] = re.sub(r'\s*\(eds?\.\)', '', names[-1])
    out = []
    for i, n in enumerate(names):
        if i == 0 and ',' not in n and len(n.split()) > 1 and not n.startswith(('UNESCO', 'Project')):
            parts = n.split()
            n = '%s, %s' % (parts[-1], ' '.join(parts[:-1]))
        out.append(n)
    if len(out) == 1:
        s = out[0]
    else:
        s = ', '.join(out[:-1]) + ' & ' + out[-1]
    return s.replace('等 &', '&').replace(' 等', ' et al.') + eds


def bib_line(n, c):
    t = c['title'].strip()
    v = (c.get('venue') or '').strip().rstrip('.')
    y = c['year']
    if is_cjk(c):
        if c['type'] == 'classic':
            return '%d. %s：《%s》，%s。' % (n, c['authors'], t, v)
        return '%d. %s（%s）：《%s》，%s。' % (n, c['authors'], y, t, re.sub(r',\s*\d{4}$', '', v))
    au = west_names(c['authors'])
    if c['type'] in ('book', 'classic'):
        return '%d. %s (%s). *%s*. %s.' % (n, au, y, t, v)
    if c['type'] == 'chapter':
        return '%d. %s (%s). %s. %s.' % (n, au, y, t, re.sub(r'^in ', 'In ', v))
    m = re.match(r'^(.*?[A-Za-z])(\s*[\d(:].*)$', v)
    jv = '*%s*%s' % (m[1], m[2]) if m else '*%s*' % v
    return '%d. %s (%s). %s. %s.' % (n, au, y, t, jv)


def bibliography():
    out = ['# 参考书目', '',
           '本书引用的来源共 %d 条，分三类：一、西文文献，按第一作者姓氏字母排序；二、中文与日文文献，按著者姓名拼音排序；三、古籍与佛典。'
           '正文中的〔参 n〕即本书目第 n 条。每条出处的核验结果，见附录四「引文核验总表」。' % len(ORDER), '']
    for label, group in (('一、西文文献', western), ('二、中文与日文文献', cjk_modern), ('三、古籍与佛典', cjk_classic)):
        out += ['## ' + label, '']
        out += [bib_line(REF[c['key']], c) for c in group]
        out.append('')
    return '\n'.join(out).strip() + '\n'


def cites(t):
    def rep(m):
        keys = re.findall(r'〔参[:：]([^〕]+)〕', m[0])
        return '〔参 %s〕' % '、'.join(str(REF[k.strip()]) for k in keys)
    t = re.sub(r'〔参[:：][^〕]+〕(?:〔参[:：][^〕]+〕)*', rep, t)
    assert not re.search(r'〔参[:：]', t)
    return t


def chs_compact(xs):
    xs = sorted(xs); out = []; i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
            j += 1
        out.append(str(xs[i]) if i == j else ('%d、%d' % (xs[i], xs[j]) if j == i + 1 else '%d–%d' % (xs[i], xs[j])))
        i = j + 1
    return '、'.join(out)


def short_src(c):
    if is_cjk(c):
        return c['authors'] + ('' if c['type'] == 'classic' else ' %s' % c['year'])
    n = len([x for x in c['authors'].split(';') if x.strip()])
    sn = surname(c)
    if n == 2:
        b = c['authors'].split(';')[1].strip()
        b = b.split(',')[0] if ',' in b else b.split()[-1]
        sn = '%s & %s' % (sn, b)
    elif n > 2:
        sn += ' 等'
    return '%s %s' % (sn, c['year'])


def hezhi():
    """附录四：引文核验总表（按书目编号）。"""
    cnt = {}
    for c in CITES:
        cnt[c['status']] = cnt.get(c['status'], 0) + 1
    assert set(cnt) <= {'核', '核：大意', '摘要核验', '题录核验'}, cnt
    out = ['## 附录四　引文核验总表', '',
           '下表按参考书目的编号，逐条列出书中转述的前人与对手：来源、出现的章、书中转述的要点、核验结果。核验分四档：'
           '〔核〕为题录已核对，转述要点与原文或摘要直接相符；〔核：大意〕为题录已核对，转述要点与可靠概述相符，措辞是本书的转述；'
           '〔摘要核验〕为只核到摘要或出版方提要，转述只落在摘要范围之内；〔题录核验〕为书目信息已核对，转述要点没能在可得材料里核到，读者引用时请回原书。'
           '全书 %d 条中，〔核〕%d 条，〔核：大意〕%d 条，〔摘要核验〕%d 条，〔题录核验〕%d 条。本书自己推出的局面一律为〔待验〕，不在此列。' % (
               len(CITES), cnt.get('核', 0), cnt.get('核：大意', 0), cnt.get('摘要核验', 0), cnt.get('题录核验', 0)), '',
           '| 书目 | 来源 | 章 | 书中转述的要点 | 核验 |', '|---|---|---|---|---|']
    for c in ORDER:
        claim = (c.get('claim') or '').replace('|', '／').replace('“', '「').replace('”', '」')
        note = (c.get('note') or '').strip().replace('|', '／').replace('“', '「').replace('”', '」')
        out.append('| %d | %s | %s | %s | 〔%s〕%s |' % (REF[c['key']], short_src(c), chs_compact(c['chapters']), claim, c['status'],
                                                    ('　' + note) if note else ''))
    return '\n'.join(out) + '\n'


# ── 章 ──
def unbold(s):
    s = s.strip()
    return s[2:-2].strip() if s.startswith('**') and s.endswith('**') and s.count('**') == 2 else s


def end_lines(body):
    ls = []
    for l in body.splitlines():
        l = re.sub(r'^>\s?', '', l.strip()).strip()
        if not l:
            continue
        l = re.sub(r'^- ', '', l)
        m = re.match(r'^(\d)\.\s+(.*)$', l)
        if m:
            l = CN[int(m[1])] + '，' + m[2]
        ls.append(l)
    return ls


def ends(secs):
    tk = [unbold(x) for x in end_lines(secs['带走的话'])]
    raw = end_lines(secs['两行小账'])
    lg, i = [], 0
    while i < len(raw):
        l = raw[i]
        if l.startswith('**') and l.endswith('**') and i + 1 < len(raw) and not raw[i + 1].startswith('**'):
            lg.append(unbold(l) + '——' + raw[i + 1]); i += 2; continue
        lg.append(unbold(l)); i += 1
    ww = end_lines(secs['想一想'])
    return '\n\n'.join(['> **带走的话**\n' + '\n'.join('> ' + x for x in tk),
                        '> **小账**\n' + '\n'.join('> ' + x for x in lg),
                        '> **想一想**\n' + '\n'.join('> ' + x for x in ww)])


# 统稿遗留的两处重复字句（只删重复，不改文意）
FIXES = {9: [('还要有一个对照：有人听了，但不接着做、不接着往来；这样才分得开「有人在场」与「可再发生」（见实验二的 ⑤ 组）。还要有一个对照：有人听了，但不接着做、不接着往来；这样才分得开「有人在场」与「可再发生」（见实验二的 ⑤ 组）。',
              '还要有一个对照：有人听了，但不接着做、不接着往来；这样才分得开「有人在场」与「可再发生」（见实验二的 ⑤ 组）。'),
             ('设想设想同一个特质', '设想同一个特质')]}


def chapter(k):
    t = (S / ('ch%02d.md' % k)).read_text().strip()
    for a, b in FIXES.get(k, []):
        assert t.count(a) == 1, a[:30]
        t = t.replace(a, b)
    head, _, body = t.partition('\n')
    m = re.match(r'^# 第([一二三四五六七八九十]+)章\s+(.+)$', head)
    assert m and CNUM[m[1]] == k, head
    title = m[2].strip()
    pieces = re.split(r'^## ', body.strip(), flags=re.M)
    assert not pieces[0].strip(), pieces[0][:40]
    main, tail = [], {}
    for p in pieces[1:]:
        h, _, b = p.partition('\n')
        h = h.strip()
        if h in ('带走的话', '两行小账', '想一想'):
            tail[h] = b; continue
        assert not tail, ('章末三节之后还有节', k, h)
        mm = re.match(r'^([一二三四五六七八九十]+)、\s*(.+)$', h)
        assert mm, (k, h)
        b = re.sub(r'^### ◆ (.+)$', r'#### \1', b, flags=re.M)
        assert not re.search(r'^### ', b, re.M), (k, h)
        main.append('### ◆ %s、%s\n%s' % (mm[1], mm[2].strip(), b.rstrip()))
    assert set(tail) == {'带走的话', '两行小账', '想一想'}, (k, tail.keys())
    out = '## 第%d章　%s\n\n> **这一章的问题**：%s\n\n%s\n\n%s\n' % (k, title, QS[k], '\n\n'.join(x.strip() for x in main), ends(tail))
    return cites(out)


def part(p):
    xu = (A / ('bian%02d-xu.md' % p)).read_text().strip()
    assert xu.startswith('# 第%s编　' % CN[p]), xu[:30]
    zh = (A / ('bian%02d-zhang.md' % p)).read_text().strip()
    assert zh.startswith('## 本编总账'), zh[:30]
    zh_head, _, zh_body = zh.partition('\n')
    zh_body = re.sub(r'^#{2,3} ', '#### ', zh_body, flags=re.M)
    chs = '\n\n'.join(chapter(k).strip() for k in range(3 * p - 2, 3 * p + 1))
    return cites(xu) + '\n\n' + chs + '\n\n' + zh_head + '\n' + cites(zh_body.strip()) + '\n'


def jieyu():
    t = (A / 'jieyu.md').read_text().strip()
    head, _, body = t.partition('\n')
    assert head.startswith('# 结语　'), head
    body = re.sub(r'^## ◆ (.+)$', r'### ◆ \1', body, flags=re.M)
    assert not re.search(r'^## ', body, re.M)
    return head + '\n\n' + cites(body.strip()) + '\n'


DAODU_OLD = '〔待验〕是本书自己推出、还没有人专门去验的局面，读到它时，请当作一个可以去试的问题，不要当作定论。'
DAODU_NEW = DAODU_OLD + ('每一条出处的核验结果列在附录四「引文核验总表」，分四档：〔核〕为题录已核对、转述要点与原文或摘要直接相符；'
                         '〔核：大意〕为题录已核对、转述要点与可靠概述相符；〔摘要核验〕为只核到摘要或出版方提要；'
                         '〔题录核验〕为书目信息已核对、转述要点没能在可得材料里核到。')


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    body_files = ['ch%02d.md' % k for k in range(1, 10)]
    body_han = sum(han((S / f).read_text()) for f in body_files)
    cnt = {}
    for c in CITES:
        cnt[c['status']] = cnt.get(c['status'], 0) + 1
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    pfiles = []
    parts_md = [part(p) for p in (1, 2, 3)]
    total_han = None
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('系列', M.SERIES), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR), ('指导', M.ADVISOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '@@WAN@@'),
                 ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    cp += ['',
           'AI 协作声明：本书由高鹏在王德生指导下写成，SDE（显露·差异序列·特征纠缠）方法归属王德生；根命题、铁律、九问与三十六位对手由王德生给出，原话登记见附录一。'
           '全书文字由 AI（Claude）在作者与指导者的要求下协作成稿：九路智能体并行执笔，Opus 与 Sonnet 两位独立评分员多轮盲评，据评分做了三轮定点修改，'
           '再经统稿与三审（口径审、文风审、引文与事实审），最后对全书 %d 条来源做了引文总核。' % len(CITES), '',
           '书中所引古今中外各家的话，古籍引原句，今人著作一律转述大意。正文〔参 n〕指书后参考书目第 n 条；核验结果汇总见附录四「引文核验总表」，分四档：'
           '〔核〕为题录已核对、转述要点与原文或摘要直接相符，〔核：大意〕为题录已核对、转述要点与可靠概述相符，〔摘要核验〕为只核到摘要或出版方提要，'
           '〔题录核验〕为书目信息已核对、转述要点没能在可得材料里核到。〔待验〕为本书推出、尚待验证的局面。', '',
           '书中的搪瓷缸、槐荫小区的九只手以及各章人物与场景，一律虚构，只承担画面，不承担证据。书中写到的比较与实验都是预注册的设计，没有实施过，没有数据，'
           '数字门槛是拟定的初值。本书讲的是对「舍不得」的理解，不是医学或心理治疗的书；如果停顿长久，睡不好、吃不下，或对日常的事失去兴趣，请找医生或心理咨询师。', '',
           '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录；三编九章，每编前有编序、末有本编总账；结语、附录七件、参考书目、后记。', '',
           '版权所有　侵权必究', '']
    au = (A / 'zuozhe.md').read_text().strip()
    assert au.startswith('## 作者介绍')
    daodu = (A / '00-daodu.md').read_text().strip()
    assert daodu.count(DAODU_OLD) == 1
    daodu = daodu.replace(DAODU_OLD, DAODU_NEW)
    fronts = [(A / '00-shifenzhong.md').read_text().strip(), (A / '00-qianyan.md').read_text().strip(), daodu]
    front = '\n'.join(cp) + '\n' + au + '\n\n' + '\n\n'.join(cites(x) for x in fronts) + '\n'
    for p in (1, 2, 3):
        f = 'parts/%02d-第%s编.md' % (p, CN[p]); pfiles.append(f)
        (HERE / f).write_text(parts_md[p - 1])
    (HERE / 'back/11-结语.md').write_text(jieyu())
    fu = ['# 附录', '',
          '附录七件。附录一登记王德生的口述原话与九问原题；附录二把九格摆成一张总表；附录三按章汇总判决性判据、证伪条件与预注册设计；'
          '附录四逐条列出引文与核验结果；附录五是三十六位对手与各章最近邻居的索引；附录六摊开本书最可能错的地方；附录七交代本书是怎样生成的。', '']
    for k in (1, 2, 3):
        fu.append((A / ('fulu%02d.md' % k)).read_text().strip()); fu.append('')
    fu.append(hezhi())
    for k in (5, 6, 7):
        fu.append((A / ('fulu%02d.md' % k)).read_text().strip()); fu.append('')
    fu = cites('\n'.join(fu))
    hj = (A / 'houji.md').read_text().strip()
    assert hj.startswith('## 后记')
    hj = '# 后记' + hj[len('## 后记'):]
    back = fu + '\n\n' + bibliography() + '\n' + cites(hj) + '\n'
    (HERE / 'back/12-后置.md').write_text(back)
    (HERE / 'front/00-前置.md').write_text(front)
    files = ['front/00-前置.md'] + pfiles + ['back/11-结语.md', 'back/12-后置.md']
    bk = '\n\n'.join((HERE / f).read_text().strip() for f in files) + '\n'
    wan = '约 %d 万字' % round(han(bk) / 10000)
    for f in files[:1]:
        (HERE / f).write_text((HERE / f).read_text().replace('@@WAN@@', wan))
    bk = bk.replace('@@WAN@@', wan)
    (HERE / 'book.md').write_text(bk)
    print('ok 全书汉字', han(bk), '正文汉字', body_han, '章', len(re.findall(r'^## 第\d+章　', bk, re.M)),
          '引文', len(re.findall(r'〔参 ', bk)), '书目', len(ORDER), cnt, wan)


if __name__ == '__main__':
    main()
