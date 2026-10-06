import json, re
from pathlib import Path
items = json.load(open('items.json')); OUT = Path('book16')
CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6}
# 合并被引用标签切断的段
it2 = []
i = 0
gap = False
for k, t in items:
    if k == 'chipgap':
        gap = True; continue
    if gap and k == 'p' and it2 and it2[-1][0] == 'p' and not re.search(r'[。！？”）：；…]\**$', it2[-1][1]):
        it2[-1] = ('p', it2[-1][1] + t)
    else:
        it2.append((k, t))
    gap = False
items = it2
partnames = {t.split('　')[0]: t.split('　', 1)[1] for k, t in items if k == 'partname'}
items = [x for x in items if x[0] != 'partname']
def first(pred, start=0):
    return next(i for i in range(start, len(items)) if pred(items[i]))
p0 = first(lambda x: x[0] == 'h2' and '编序' in x[1])
b0 = first(lambda x: x[0] == 'h1' and x[1].startswith('科学想象三原理'))
front, body, back = items[:p0], items[p0:b0], items[b0:]

def emit(k, t):
    if k == 'table': return '\n' + t + '\n'
    return t
# ── 前置 ──
F = ['## 出版信息', '', '| 字段 | 内容 |', '|---|---|',
     '| 书名 | 科学是什么？——从发现到发生：意义驱动下的实体创造机制 |',
     '| 英文书名 | What Is Science? From Discovery to Genesis: Meaning-Driven Mechanisms of Entity Creation |',
     '| 著者 | 王德生　牟军 |', '| 出版 | 德麦国际出版社（Demai International Press）· 新加坡 |',
     '| 编号 | 德麦国际专著第 231 号 |', '| ISBN | 978-1-970820-08-9 |', '| 定价 | US$55.00 |',
     '| 开本 | 170 mm × 240 mm（16 开） |', '| 字数 | 约 __WAN__ 万汉字 |', '| 版次 | 2026 年 1 月第 1 版 |',
     '| 网络版 | 2026 年 10 月据著者原稿重排，全文上线 sdeuniverses.com |', '',
     '全书结构：作者介绍、专家推荐语、革命宣言、目录；导论、读者导读、术语表；基础编与四大编共二十七章；附录四件、结语、金句集锦。', '',
     '版权所有　侵权必究', '', '---', '', '## 作者介绍', '',
     '王德生，SDE（显露·差异序列·特征纠缠）本体论思想体系的创立者，德麦国际（Demai International Pte. Ltd.，新加坡）创办人、首席执行官。中国科学院计算数学博士，曾任教于英国斯旺西大学与新加坡南洋理工大学，现在新加坡与中国之间工作。本书写于其思想体系的 SIO 本体论阶段。', '',
     '牟军，德麦国际专著作者，与王德生合著本书及《实践发生学》《三视角方法论与实践应用》（德麦国际专著第 212 号）。', '', '---', '']
cur = None
for k, t in front:
    if k in ('h1', 'h2'):
        t = re.sub(r'^0\.\d\s*', '', t)
        if t.startswith('导论：'): t = '导论　' + t[3:]
        if t == '革命宣言页': t = '革命宣言'
        cur = t; F += ['', '## ' + t, '']; pend = True
    elif k == 'h3':
        if cur in ('革命宣言', '读者导读与全书总图') and pend:
            F[-2] = F[-2] + '　' + t
        else:
            F += ['### ' + t, '']
        pend = False
    else:
        F += [emit(k, t), '']; pend = False
(OUT / 'front' / '00-前置.md').write_text('\n'.join(F) + '\n')

# ── 各编 ──
parts = []; cur = None
for k, t in body:
    if k == 'h2' and re.match(r'^(基础编|第[一二三四]大编)编序', t):
        key = re.match(r'^(基础编|第[一二三四]大编)', t)[1]
        cur = dict(key=key, name=partnames[key], xu=t.split('：', 1)[1], lines=[], chaps=set(), heads=set(), mode='intro', zone=False)
        parts.append(cur); continue
    L = cur['lines']
    if k in ('h1', 'h2'):
        m = re.match(r'^第\s*([一二三四五六\d]+)\s*章　?\s*(.*)$', t)
        if m:
            n = CN.get(m[1]) or int(m[1])
            if n in cur['chaps']: continue
            cur['chaps'].add(n); cur['heads'] = set(); cur['zone'] = False
            L += ['', '## 第 %d 章　%s' % (n, m[2].strip()), '']; continue
        if re.match(r'^(基础编|第[一二三四]大编)编结', t):
            L += ['', '## 编结', '']; cur['heads'] = set(); cur['zone'] = False; continue
        if t in cur['heads']: continue
        cur['heads'].add(t)
        if k == 'h1' or re.match(r'^(本章|产出物\d|发展版|产出物)', t):
            cur['zone'] = True; L += ['### ◆ ' + t, '']
        else:
            L += [('#### ' if cur['zone'] else '### ') + t, '']
        continue
    if k in ('h3', 'h4'):
        if t in cur['heads']: continue
        cur['heads'].add(t)
        if k == 'h3' and re.match(r'^\d+\.\d+\s', t.replace('　', ' ')): cur['zone'] = False
        lv = '####' if (k == 'h4' or cur['zone']) else '###'
        L += ['%s %s' % (lv, t), '']; continue
    L += [emit(k, t), '']
names = {'基础编': '基础编', '第一大编': '第一大编', '第二大编': '第二大编', '第三大编': '第三大编', '第四大编': '第四大编'}
for i, p in enumerate(parts):
    txt = '# %s　%s\n\n> 编序　%s\n\n' % (p['key'], p['name'], p['xu']) + '\n'.join(p['lines']) + '\n'
    (OUT / 'parts' / ('%02d-%s.md' % (i + 1, p['key']))).write_text(re.sub(r'\n{3,}', '\n\n', txt))
    print(p['key'], p['name'], sorted(p['chaps']))

# ── 后置 ──
B = []
for k, t in back:
    if k == 'h1' or (k == 'h2' and t == '金句集锦'):
        t = re.sub(r'^附录B:附录B：', '附录B　', t)
        t = re.sub(r'^附录([CD])：', r'附录\1　', t)
        if t.startswith('科学想象三原理'): t = '附录A　科学想象三原理（基于新的科学定义）'
        if t.startswith('结语：'): t = '结语　' + t[3:]
        B += ['', '# ' + t, '']
    elif k == 'h2': B += ['## ' + t, '']
    elif k in ('h3', 'h4'): B += ['### ' + t, '']
    else: B += [emit(k, t), '']
(OUT / 'back' / '10-后置.md').write_text(re.sub(r'\n{3,}', '\n\n', '\n'.join(B)) + '\n')
import glob
p = OUT / 'front' / '00-前置.md'
tot = sum(len(re.findall(r'[一-鿿]', open(f).read())) for f in glob.glob('book16/*/*.md'))
p.write_text(p.read_text().replace('__WAN__', '%.1f' % (tot / 10000)))
print('han', tot)
