#!/usr/bin/env python3
"""第 470 号《愧——一次只走了两步的发生》（秦莉著，王德生指导）：把 /home/claude/kui 下的三审定稿拼成 220/302 版式工具链的分卷稿。
只做格式拼装，正文文字不动：
  章题「# 第一章 题」→「## 第1章　题」，节题「## 一 题」→「### ◆ 一、题」；
  正文引文代码 [W1-01] → 〔参 n〕（n 为参考书目编号，据 shimu.md 行尾的〔id〕）；
  每章末接 add/ends-chNN.md 三框；每编前接编序、后接本编总账；
  附录四由 review/r3_hezhi.json 生成。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法：python3 tools/book-m470/assemble.py
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa: E402
S = Path(M.SRC)
A = S / 'add'
CN = '零一二三四五六七八九十'
CHFILES = ['01_what1', '02_what2', '03_what3', '04_how1', '05_how2', '06_how3', '07_why1', '08_why2', '09_why3']


def han(s):
    return len(re.findall(r'[一-鿿]', s))


# ── 参考书目编号 ──
SHIMU = (A / 'shimu.md').read_text().strip()
REF = {}
for line in SHIMU.splitlines():
    m = re.match(r'^(\d+)\.\s.*〔([A-Z]\d?-\d+)〕\s*$', line.strip())
    if m:
        REF[m[2]] = int(m[1])
assert len(REF) == 47, ('书目 id 数', len(REF))
SHIMU_OUT = re.sub(r'\s*〔[A-Z]\d?-\d+〕\s*$', '', SHIMU, flags=re.M)


def cites(t):
    def rep(m):
        ids = re.findall(r'[A-Z]\d?-\d+', m[0])
        return '〔参 %s〕' % '、'.join(str(REF[i]) for i in ids)
    t = re.sub(r'(?:\[(?:G|W[123]|H[123]|Y[123])-\d+\]\s*)+', lambda m: rep(m), t)
    assert not re.search(r'\[(?:G|W|H|Y)\d?-\d+\]', t)
    return t


def sections(t):
    """「## 一 题」→「### ◆ 一、题」。"""
    return re.sub(r'^## ([一二三四五六七八九十]+)[ 　、]+(.+)$', r'### ◆ \1、\2', t, flags=re.M)


def chapter(k):
    t = (S / (CHFILES[k - 1] + '.md')).read_text().strip()
    head, _, body = t.partition('\n')
    m = re.match(r'^# 第[一二三四五六七八九十]+章\s+(.+)$', head)
    assert m, head
    body = cites(sections(body.strip()))
    ends = (A / ('ends-ch%02d.md' % k)).read_text().strip()
    return '## 第%d章　%s\n\n%s\n\n%s\n' % (k, m[1].strip(), body, ends)


def part(p):
    xu = (A / ('bian%02d-xu.md' % p)).read_text().strip()
    assert xu.startswith('# 第%s编　' % CN[p]), xu[:30]
    zh = (A / ('bian%02d-zhang.md' % p)).read_text().strip()
    assert zh.startswith('## 本编总账'), zh[:30]
    zh_head, _, zh_body = zh.partition('\n')
    zh_body = re.sub(r'^#{2,3} ', '### ', zh_body, flags=re.M)
    chs = '\n\n'.join(chapter(k).strip() for k in range(3 * p - 2, 3 * p + 1))
    return xu + '\n\n' + chs + '\n\n' + zh_head + '\n' + zh_body.strip() + '\n'


def h1(t, name):
    t = t.strip()
    head, _, body = t.partition('\n')
    title = re.sub(r'^#\s+', '', head).strip()
    title = re.sub(r'\s+', '　', title, count=1)
    return '# %s\n\n%s\n' % (title, cites(sections(body.strip())))


def hezhi():
    """附录四：引文核验总表。"""
    rows = json.loads((S / 'review/r3_hezhi.json').read_text())
    out = ['## 附录四　引文核验总表', '',
           '下表逐条列出书中转述的前人与近邻：书中转述的要点、对应的参考书目编号、核验结果。〔核〕为已查对出处；〔核：大意〕为出处已查对、引文取大意；〔摘要核验〕为只核到摘要或出版方提要；本书自己推出的局面一律为〔待验〕，不在此逐条列出。', '',
           '| 章 | 近邻 | 书中转述的要点 | 书目 | 核验 |', '|---|---|---|---|---|']
    for r in rows:
        c = r.get('cite') or ''
        ids = re.findall(r'[A-Z]\d?-\d+', c)
        num = '、'.join(str(REF[i]) for i in ids if i in REF) or '—'
        st = (r.get('status') or '').strip()
        note = (r.get('note') or '').strip()
        claim = (r.get('claim') or '').replace('|', '／').replace('“', '「').replace('”', '」')
        note = note.replace('“', '「').replace('”', '」')
        out.append('| %s | %s | %s | %s | 〔%s〕%s |' % (r.get('chapter', ''), r.get('neighbor', ''), claim, num, st,
                                                     ('　' + note.replace('|', '／')) if note else ''))
    return '\n'.join(out) + '\n'


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    body_han = sum(han((S / (f + '.md')).read_text()) for f in ['00_intro'] + CHFILES + ['10_conclusion'])
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s——%s》' % (M.TITLE, M.SUBTITLE)), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR), ('指导', M.ADVISOR),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % round(body_han / 10000 + 0.6)),
                 ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    cp += ['',
           'AI 协作声明：本书由秦莉在王德生指导下写成，SDE（显露·差异序列·特征纠缠）方法归属王德生；九问、三十六位近邻与候选脊梁由王德生给出，原话登记见附录一。全书文字由 AI（Claude）在作者与指导者的要求下协作成稿：十路并行执笔，两轮独立评分后定点修改，再经统稿与三审（口径审、文风审、引文与事实审）。', '',
           '书中所引古今中外各家的话，古籍引原句，今人著作一律转述大意。正文〔参 n〕指书后参考书目第 n 条；核验结果汇总见附录四「引文核验总表」：〔核〕为已查对出处，〔核：大意〕为出处已查对、引文取大意，〔摘要核验〕为只核到摘要，〔待验〕为本书推出、尚待验证的局面。', '',
           '书中失约的父亲、受惠后躲开恩人的成年人以及各章的日常场景，一律虚构，只承担画面，不承担证据。书中写到的比较与实验都是设想，没有实施过。本书讲的是对「愧」的理解，不是医学或心理治疗的书；如果自责、失眠、自我否定长期缠着你，请找医生或心理咨询师。', '',
           '全书结构：出版信息、作者介绍、十分钟读完这本书、前言、导读、目录、导论；三编九章，每编前有编序、末有本编总账；结语、附录六件、参考书目、后记。', '',
           '版权所有　侵权必究', '']
    au = ['## 作者介绍', '',
          '秦莉，笔名斐索，中文专业毕业，鲁迅文学院 1999 级研修班结业。以诗歌和小说创作为本业，也研究 SDE 美学，在 SDE 学员专栏主持文学方向子平台「SDE 文学」。在德麦国际出版社出版有《心在哪里？——普通人都能明白的心理学》《情绪价值发生学》《慌：心之荒》等。', '',
          '王德生，博士，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，新加坡德麦国际（Demai International Pte. Ltd.）创始人。早年在湘潭大学、中国科学院学习与研究计算数学，曾任教于英国斯旺西大学与新加坡南洋理工大学。本书的九问与母题由他给出，全书在他指导下完成。', '']
    front = '\n'.join(cp + au) + '\n' + '\n\n'.join(cites((A / f).read_text().strip()) for f in ('00-shifenzhong.md', '00-qianyan.md', '00-daodu.md')) + '\n'
    (HERE / 'front/00-前置.md').write_text(front)
    (HERE / 'front/01-导论.md').write_text(h1((S / '00_intro.md').read_text(), '导论'))
    pfiles = []
    for p in (1, 2, 3):
        f = 'parts/%02d-第%s编.md' % (p, CN[p]); pfiles.append(f)
        (HERE / f).write_text(part(p))
    (HERE / 'back/11-结语.md').write_text(h1((S / '10_conclusion.md').read_text(), '结语'))
    fu = (A / 'fulu.md').read_text().strip()
    i = fu.index('## 附录四'); j = fu.index('## 附录五')
    fu = fu[:i] + hezhi() + '\n' + fu[j:]
    fu = cites(fu)
    back = fu + '\n\n' + SHIMU_OUT + '\n\n' + (A / 'houji.md').read_text().strip() + '\n'
    (HERE / 'back/12-后置.md').write_text(back)
    files = ['front/00-前置.md', 'front/01-导论.md'] + pfiles + ['back/11-结语.md', 'back/12-后置.md']
    bk = '\n\n'.join((HERE / f).read_text().strip() for f in files) + '\n'
    (HERE / 'book.md').write_text(bk)
    print('ok 全书汉字', han(bk), '正文汉字', body_han, '章', len(re.findall(r'^## 第\d+章　', bk, re.M)),
          '引文', len(re.findall(r'〔参 ', bk)))


if __name__ == '__main__':
    main()
