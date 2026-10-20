"""第 482 号《风水发生学》：把统稿后的 ch*.md 转成 build.py 要的 parts/front/back 体例。"""
import re, json
from pathlib import Path
SRC = Path('/home/claude/fengshui502'); OUT = Path(__file__).parent
PARTS = [('第一编','定义：风水是 E 对方程运行的影响',[1,2,3,4]),('第二编','回写：风水从哪里来',[5,6,7]),
         ('第三编','固化：风水怎样变成命运',[8,9,10]),('第四编','E1 三界：土的三层',[11,12,13]),
         ('第五编','E2 信息三态：符号、逻辑与数学',[14,15,16]),('第六编','E3 能量三状态：真、善、美',[17,18,19]),
         ('第七编','用这把尺子重读旧书',[20,21,22]),('第八编','解冻与重写：从看风水到写风水',[23,24,25])]
FILES = {0:'ch00_daolun.md', **{i:f'ch{i:02d}.md' for i in range(1,26)}, 26:'ch26_jieyu.md'}

def fix_ledger(items):
    out = []
    for x in items:
        x = re.sub(r'^[-*] ', '', x.strip())
        if not x: continue
        m = re.match(r'^(.{2,60}?[？?])\s*(?:——)?(.*)$', x)
        out.append(f'> {m[1]}——{m[2]}' if m and m[2] else f'> {x}')
    return out

def conv(t):
    L = t.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].rstrip()
        m = re.match(r'^> \*\*带走的话\*\*[：:]\s*(.+)$', s)
        if m: out += ['> **带走的话**', '> ' + m[1], '']; i += 1; continue
        if re.match(r'^\*\*两行小账\*\*\s*$', s):
            i += 1; items = []
            while i < len(L) and (L[i].startswith('- ') or L[i].startswith('* ') or not L[i].strip()):
                if L[i].strip(): items.append(L[i])
                i += 1
            out += ['> **小账**'] + fix_ledger(items) + ['']; continue
        m = re.match(r'^◆\s*(.+)$', s)
        if m: out.append('### ◆ ' + m[1]); i += 1; continue
        m = re.match(r'^#{4,} (.+)$', s)
        if m: out.append('**%s**' % m[1]); i += 1; continue
        out.append(s); i += 1
    return '\n'.join(out)

def chapter(n):
    t = (SRC / FILES[n]).read_text(encoding='utf-8')
    m = re.search(r'^# (第 ?\d+ ?章.*)$', t, re.M)
    pre, body = t[:m.start()], t[m.start():]
    mm = re.match(r'第 ?(\d+) ?章[　 ]*(.*)', m[1])
    body = body[body.index('\n') + 1:]
    return f'## 第 {mm[1]} 章　{mm[2]}\n\n' + conv(body).strip(), pre

def intro_of(pre):
    L = pre.split('\n')
    k = next((i for i, x in enumerate(L) if re.match(r'^#+ 第.编', x)), None)
    if k is None: return None
    return [x.strip() for x in L[k+1:] if x.strip() and not x.startswith('#')]

for idx, (p, title, rng) in enumerate(PARTS, 1):
    chs, intro = [], None
    for n in rng:
        c, pre = chapter(n); chs.append(c)
        if intro is None: intro = intro_of(pre)
    assert intro, p
    (OUT/'parts'/f'{idx:02d}-{p}.md').write_text(f'# {p}　{title}\n\n' + '\n\n'.join(intro) + '\n\n' + '\n\n'.join(chs) + '\n', encoding='utf-8')

t = (SRC/FILES[0]).read_text(encoding='utf-8')
m = re.search(r'^# (.*)$', t, re.M); tt = t[m.end():]
head = (OUT/'front_head.md').read_text(encoding='utf-8').rstrip()
(OUT/'front'/'00-前置.md').write_text(head + '\n\n## 导论　风水是被发现的，还是被回写出来的？\n\n' + conv(tt).strip() + '\n', encoding='utf-8')
t = (SRC/FILES[26]).read_text(encoding='utf-8')
m = re.search(r'^# (.*)$', t, re.M); tt = t[m.end():]
sub = re.sub(r'^结语[　 :：]*', '', m[1]).strip() or '从趋吉避凶，到解冻与重写'
(OUT/'back'/'09-结语.md').write_text(f'# 结语　{sub}\n\n' + conv(tt).strip() + '\n', encoding='utf-8')
print('ok')
