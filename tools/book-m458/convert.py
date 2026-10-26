#!/usr/bin/env python3
"""第 458 号《科学共同体的退位和出版典范转移》：把 /home/claude/book522 下三审定稿（00_front … 10_ch34-36_back）
转成 220/302 版式工具链（照第 520 号）的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md、parts/0N-X篇.md、back/11-结语.md、back/12-后置.md、book.md。
用法：python3 tools/book-m458/convert.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
S = Path(M.SRC)
PIANS = [('01-上篇', ['01_ch01-04.md', '02_ch05-08.md']), ('02-中篇', ['03_ch09-12.md', '04_ch13-16.md']),
         ('03-下篇', ['05_ch17-20.md', '06_ch21-23.md']), ('04-续篇', ['07_ch24-27.md', '08_ch28-30.md']),
         ('05-尾篇', ['09_ch31-33.md'])]


def ends(text):
    """章末三件 → 220 版式引用框：> **带走的话** / > **小账** / > **想一想**。"""
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^>\s*\*\*带走的话\*\*[　\s：:]*(.*)$', s)
        if m:
            out += ['> **带走的话**', '> ' + m[1].strip(), '']; i += 1; continue
        m = re.match(r'^>\s*\**小账\**[　\s：:]*(.*)$', s)
        if m:
            rows = []
            body = m[1].strip()
            i += 1
            while i < len(L) and L[i].strip().startswith('>') and not re.match(r'^>\s*\**(想一想|带走的话)', L[i].strip()):
                body += '　' + L[i].strip().lstrip('>').strip(); i += 1
            for seg in re.split(r'[　\s]*(?=第[一二]行[：:])', body):
                seg = re.sub(r'^第[一二]行[：:]\s*', '', seg.strip())
                if not seg:
                    continue
                q = re.match(r'^([^？]{2,30}？)\s*(.*)$', seg)
                rows.append('%s——%s' % (q[1], q[2]) if q and q[2] else seg)
            out += ['> **小账**'] + ['> ' + r for r in rows] + ['']
            continue
        m = re.match(r'^(?:>\s*)?(\*\*)?想一想(\*\*)?(?:[　\s：:]+(.*))?$', s)
        if m and (s.startswith('>') or m[1] or not m[3]):
            m = [None, m[1], m[2], m[3] or '']
            qs = [m[3].strip()] if m[3].strip() else []
            i += 1
            while i < len(L) and not L[i].startswith('#') and L[i].strip() != '---':
                t = L[i].strip().lstrip('>').strip()
                if t:
                    qs.append(re.sub(r'^(\d+[.、]\s*|[-·]\s*)', '', t))
                i += 1
            out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, q) for k, q in enumerate(qs)] + ['']
            continue
        if s == '---':
            i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def chap_fix(text):
    return re.sub(r'^## 第 ?(\d+) ?章[　 ]+', lambda m: '## 第 %s 章　' % m[1], text, flags=re.M)


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    fr = (S / '00_front.md').read_text()
    li = fr.index('# 导论')
    front, lun = fr[:li], fr[li:]
    front = re.sub(r'^## ', '### ', front, flags=re.M)
    front = re.sub(r'^# ', '## ', front, flags=re.M)
    lun = re.sub(r'^## ', '### ', lun, flags=re.M)
    # 出版信息表：统一为「项｜内容」两列
    (HERE / 'front/00-前置.md').write_text(front.strip() + '\n')
    (HERE / 'front/01-导论.md').write_text(ends(lun))
    for name, files in PIANS:
        t = '\n\n'.join((S / f).read_text().strip() for f in files)
        (HERE / ('parts/%s.md' % name)).write_text(ends(chap_fix(t)))
    bk = (S / '10_ch34-36_back.md').read_text()
    a = bk.index('# 结语'); b = bk.index('# 参考书目')
    tail = ends(chap_fix(bk[:a]))
    p5 = HERE / 'parts/05-尾篇.md'
    p5.write_text(p5.read_text().rstrip() + '\n\n' + tail)
    (HERE / 'back/11-结语.md').write_text(ends(bk[a:b]))
    rest = bk[b:]
    # 附录：加一个「# 附录」总页，各件降为二级
    ai = rest.index('# 附录一')
    hi = rest.index('# 后记')
    apx = rest[ai:hi]
    apx = re.sub(r'^## ', '### ', apx, flags=re.M)
    apx = re.sub(r'^# (附录[一二三四五六七八九])', r'## \1', apx, flags=re.M)
    intro = '# 附录\n\n附录四件，供查、供对、供核：附录一按时间排出 2023—2026 年的反扑大事；附录二把共同体认证、系统认证、部落认证并排对照；附录三汇总全书的引文与事实核验；附录四摊开本书自认最弱的五处。\n\n'
    bib = re.sub(r'^## ', '### ', rest[:ai], flags=re.M)
    (HERE / 'back/12-后置.md').write_text(bib.strip() + '\n\n' + intro + apx.strip() + '\n\n' + rest[hi:].strip() + '\n')
    # book.md：学习单元用的统稿（# X篇 / ## 第 N 章）
    parts = [(HERE / ('parts/%s.md' % n)).read_text() for n, _ in PIANS]
    (HERE / 'book.md').write_text('\n\n'.join(p.strip() for p in parts) + '\n')
    allmd = '\n'.join((HERE / f).read_text() for f in ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%s.md' % n for n, _ in PIANS] + ['back/11-结语.md', 'back/12-后置.md'])
    print('han', len(re.findall(r'[一-鿿]', allmd)), 'chapters', len(re.findall(r'^## 第 \d+ 章　', allmd, re.M)),
          'take', allmd.count('> **带走的话**'), 'ledger', allmd.count('> **小账**'), 'think', allmd.count('> **想一想**'),
          'q', allmd.count('**这一章的问题**'))


if __name__ == '__main__':
    main()
