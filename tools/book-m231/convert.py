#!/usr/bin/env python3
"""《科学是什么？》原稿 docx（已解析为 paras.json）→ 分卷 Markdown。只做清理，不改写正文：
去写作指令与对话残留、合并分次交付的章、去重复稿、去草案版产出物、去引用标签。"""
import json, re, sys
from pathlib import Path
P = json.load(open('paras.json')); NUM = json.load(open('num.json'))
OUT = Path('book16'); log = []
CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6}
DROP_RANGES = [(123, 153), (1310, 1337), (2115, 2136)]   # 第一章的分次重复稿；两处「产出物草案（框架版）」
CHIPS = {'《科学想象三原理》','宏大叙事的哲学与数学','科技的数学内核：微积分（下）','科技的数学内核：微积分（上）','科学的‘我’',
         'SIO三大公理','SIO逻辑学导论','科学的SIO发生学','来源','窗体顶端','窗体底端','附录A:'}
PROMPT = re.compile(r'^(写第.章|继续|第[二三]次|第.{1,2}章.{0,6}(开始|分两次|也是)|第六章 4000字|开始第\d+章|\d+章，写|下一次$|'
                    r'(分?[两二三23]次(写完|完成)|三次完成，还是)|分三次完成，记得|第22章 样本：物理学作为实体三建构（1,500）)')
CHAT = re.compile(r'^(下面按你要求|（下次交付|（下一次将|（本章下半部分将继续)')

def md_text(o):
    s = ''
    for b, t in o['segs']:
        if b and t.strip():
            lead = t[:len(t) - len(t.lstrip())]; trail = t[len(t.rstrip()):]
            s += lead + '**' + t.strip().replace('\n', '**\n**') + '**' + trail
        else:
            s += t
    s = s.replace('****', '')
    return s

def clean_head(t):
    t = t.strip().replace('**', '')
    t = re.sub(r'（约\s*[\d,，]+\s*字）|（未完待续）|（上）|（下）|（第\d/\d）|（\d/\d，约\d+字）', '', t)
    t = re.sub(r'（第?\d/\d(，约\d+字)?）|（定稿版）', '', t)
    t = re.sub(r'（最终定稿版）|（最终定稿）|（定稿）', '', t).replace('（一页版，定稿）', '（一页版）')
    t = t.replace('（可直接进入工具箱/附录，亦可置于章末）', '').replace('（可直接进入工具箱/附录，亦可用于AEI工位化协作）', '').replace('（可直接进入工具箱/附录）', '')
    t = t.replace('（可直接进入全书宪法页）', '').replace('（可直接进入宪法页）', '').replace('（可直接插入章末或宪法页后）', '').replace('（可直接复制使用）', '')
    return t.strip()

items = []   # (kind, text) kind: part/intro/chap/h3/h4/p/ul/ol/table/sec1/outro
skip = set()
for a, b in DROP_RANGES: skip.update(range(a, b + 1))
olc = {}
for i, o in enumerate(P):
    if i in skip: continue
    if o['k'] == 't':
        rows = o['rows']; w = len(rows[0])
        items.append(('table', '\n'.join(['| ' + ' | '.join(c.replace('|', '／') for c in rows[0]) + ' |', '|' + '---|' * w] +
                                        ['| ' + ' | '.join(c.replace('|', '／') for c in r) + ' |' for r in rows[1:]])))
        continue
    raw = o['text'].strip()
    if not raw: continue
    st = o['st']
    if not st.startswith('heading'):
        if raw in CHIPS or (2660 < i < 2713 and raw == '科学是什么？'):
            log.append(('chip', i, raw)); items.append(('chipgap', '')); continue
        if (st == '' and i < 2500 and PROMPT.match(raw)) or CHAT.match(raw):
            log.append(('prompt', i, raw[:60])); continue
        if st == '' and i < 2500:
            log.append(('UNSTYLED-KEPT', i, raw[:60]))
        m = re.match(r'^(基础编|第[一二三四]大编)：(.*)$', raw)
        if m and len(raw) < 40:
            items.append(('partname', m[1] + '　' + m[2])); continue
        t = md_text(o).strip()
        # 段内残留：「下一次将……」「下一次将继续：……」
        t2 = re.sub(r'下一次将[^。]*。$', '', t).strip()
        if t2 != t: log.append(('trim', i, t[len(t2):][:70])); t = t2
        prev = P[i - 1]
        kind = 'p'
        if prev['k'] == 'p' and not prev['text'].strip() and prev['numid']:
            fmt = NUM.get(prev['numid'], {}).get(str(prev['ilvl'] or 0), ['bullet'])[0]
            if fmt == 'decimal':
                olc['n'] = olc.get('n', 0) + 1   # 同一小节内相邻的编号项连续编号（原稿每项各自成表，全是 1.）
                kind = 'ol'; t = '%d. %s' % (olc['n'], t.replace('\n', ' '))
            else:
                kind = 'ul'; t = '- ' + t.replace('\n', ' ')
        if kind == 'p':
            olc['n'] = 0
            for line in t.split('\n'):
                line = line.strip()
                if line: items.append(('p', line))
        else:
            items.append((kind, t))
        continue
    lvl = int(st[-1]); t = clean_head(raw)
    olc['n'] = 0
    if not t or '<img' in t: continue
    items.append(('h%d' % lvl, t))
json.dump(items, open('items.json', 'w'), ensure_ascii=False)
json.dump(log, open('convert-log.json', 'w'), ensure_ascii=False, indent=0)
print(len(items), {k: sum(1 for x in log if x[0] == k) for k in set(x[0] for x in log)})
for x in log:
    if x[0] in ('UNSTYLED-KEPT', 'trim'): print(x)
