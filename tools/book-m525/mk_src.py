#!/usr/bin/env python3
"""第 525 号《先到一步》：把三审定稿的分章稿（front/ch00/part1-4/ch01-16/ch17/appendix）装成 convert.py 认的 src/。
只改标题层级与章节编号写法，不动正文文字。
  · 章内「## 一、T」去掉编号（convert 统一重编）；「## 本章在全书中的位置 / 本章小结 / 本章参考文献 / 本章注释」保留原名、不编号；
  · 「### （一）T」→「#### （一）T」（四级小标题）；
  · 章副题行「——T」→ 引用行；编导语的「## 一、T」→「#### 一、T」，放进该编首章之前；
  · 前言、总论、结论保留自己的节号；附录一的概念条目「### N　T」升为「## 」，其下「#### 」不变。
用法：python3 tools/book-m525/mk_src.py <三审定稿目录>"""
import re, sys
from pathlib import Path
B = Path(sys.argv[1]); OUT = Path(__file__).parent / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'):
    f.unlink()
CNP = ['一', '二', '三', '四']
NUM = re.compile(r'^## (?:[一二三四五六七八九十]+、)(.*)$', re.M)


def rd(n):
    return (B / n).read_text(encoding='utf-8').strip()


def w(n, s):
    (OUT / n).write_text(s.strip() + '\n', encoding='utf-8')


def demote3(s):
    return re.sub(r'^### ', '#### ', s, flags=re.M)


def head_body(t):
    h, _, r = t.partition('\n')
    return h.lstrip('# ').strip(), r.strip()


# 前言、总论：保留节号
for src, dst in (('front.md', 'qianyan.md'), ('ch00.md', 'daolun.md')):
    h, r = head_body(rd(src))
    w(dst, '# %s\n\n%s' % (h, demote3(r)))

parts = {1: 'part1.md', 5: 'part2.md', 9: 'part3.md', 13: 'part4.md'}
for n in range(1, 17):
    h, r = head_body(rd('ch%02d.md' % n))
    m = re.match(r'^第(\d+)章　(.*)$', h)
    assert m and int(m[1]) == n, (n, h)
    sub = ''
    if r.startswith('——'):
        line, _, r = r.partition('\n')
        sub = '> ' + line.strip() + '\n\n'
        r = r.strip()
    r = demote3(r)
    r = NUM.sub(r'## \1', r)
    pre = ''
    if n in parts:
        ph, pr = head_body(rd(parts[n]))
        pm = re.match(r'^(第[一二三四]编)　(.*)$', ph)
        assert pm, ph
        pr = re.sub(r'^## ', '#### ', demote3(pr), flags=re.M)
        assert '# 第' not in pr, ('编导语里不能有以「第」开头的标题', n)
        pre = '## %s　%s\n\n%s\n\n' % (pm[1], pm[2], pr)
    w('ch%02d.md' % n, pre + '# 第%d章　%s\n\n%s%s' % (n, m[2], sub, r))

# 结论：保留节号
h, r = head_body(rd('ch17.md'))
w('jieyu.md', '# %s\n\n%s' % (h, demote3(r)))

# 附录
a = rd('appendix.md').partition('\n')[2]
p1, p2 = re.split(r'(?=^## 附录二)', a, flags=re.M)
t1, b1 = head_body(p1.strip().lstrip('#').strip() and p1.strip()[3:])
t2, b2 = head_body(p2.strip()[3:])
b1 = re.sub(r'^### ', '## ', b1, flags=re.M)
w('fulu1.md', '# %s\n\n%s' % (t1, b1))
w('fulu2.md', '# %s\n\n%s' % (t2, b2))
print('src', sorted(p.name for p in OUT.glob('*.md')))
