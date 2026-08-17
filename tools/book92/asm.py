# -*- coding: utf-8 -*-
"""把前件/十章/枢纽章/合章/后件装配成 manuscript.md
层级约定：
  '# '   = 编扉页（只用于四个编）
  '## '  = 章级部件（新起一页 + 进目录）
  '### ' = 节
  '#### '= 小节
"""
import re, os
os.chdir('/home/claude/b90')

def split_h1(path):
    """按 '# 标题' 切成 [(title, body)]"""
    t = open(path, encoding='utf-8').read()
    parts = re.split(r'\n(?=# )', '\n' + t.strip())
    out = []
    for p in parts:
        p = p.strip()
        if not p.startswith('# '):
            continue
        head, _, body = p.partition('\n')
        out.append((head[2:].strip(), body.strip()))
    return out

front = dict(split_h1('front/front.md'))
back = dict(split_h1('back/back.md'))

# 编序拆成四块
bianxu = {}
for blk in re.split(r'\n(?=## 编)', front['编　序']):
    blk = blk.strip()
    if not blk.startswith('## 编'):
        continue
    head, _, body = blk.partition('\n')
    bianxu[head[3:].strip()] = body.strip()
assert len(bianxu) == 4, bianxu.keys()
BNAMES = list(bianxu.keys())

def ch(n):
    return open(f'ch/{n}.md', encoding='utf-8').read().strip()

def demote(b):
    b = re.sub(r'(?m)^### ', '#### ', b)
    b = re.sub(r'(?m)^## ', '### ', b)
    return b

def part(title, body):
    return f"## {title}\n\n{demote(body).strip()}\n"

def bian(idx, cn):
    name = BNAMES[idx]
    return f"# 第{cn}编　{name.split('　')[-1]}\n\n{bianxu[name]}\n"

# 参考书目：去掉自带的 '# 参考书目' 头
refs = open('front_refs.md', encoding='utf-8').read()
refs = refs.split('\n', 1)[1].strip()


M = []
M.append("# 谁来陪伴我？\n\n### AI 时代的婚姻困境\n\n**王德生 ＋ Claude**　编著\n\n德麦国际出版社 · 专著第 92 号\n")
M.append(part('出版信息', front['出版信息']))
M.append(part('作者介绍', front['作者介绍']))
M.append(part('前　言', front['前　言']))
M.append(part('导　读', front['导　读']))
M.append('## 目　录\n')
M.append(part('导　论　为什么这场困境不会被任何人发现', front['导　论　为什么这场困境不会被任何人发现']))
M.append(bian(0, '一'))
M.append(ch('c01')); M.append(ch('c02')); M.append(ch('c03'))
M.append(ch('sn'))
M.append(bian(1, '二'))
M.append(ch('c04')); M.append(ch('c05')); M.append(ch('c06'))
M.append(bian(2, '三'))
M.append(ch('c07')); M.append(ch('c08'))
M.append(bian(3, '四'))
M.append(ch('c09')); M.append(ch('c10'))
M.append(ch('hz'))
M.append(part('结　语　四个只能答成一件事的问题', back['结　语　四个只能答成一件事的问题']))
M.append(part('参考书目', refs))
M.append(part('附录一　十二个读数速查表', back['附录一　十二个读数速查表']))
M.append(part('附录二　判错清单', back['附录二　判错清单']))
M.append(part('附录三　十篇选目与改写说明', back['附录三　十篇选目与改写说明']))
M.append(part('全书十句', back['全书十句']))
M.append(part('后　记', back['后　记']))
M.append(part('封　底', back['封　底']))

s = '\n\n'.join(x.strip() for x in M) + '\n'
open('manuscript.md', 'w', encoding='utf-8').write(s)

han = len(re.findall(r'[\u4e00-\u9fff]', s))
print('部件数', len(M), '汉字', han)
print('章级部件：')
for l in s.split('\n'):
    if l.startswith('## ') or l.startswith('# '):
        print(' ', l[:60])
