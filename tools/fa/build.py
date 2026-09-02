#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用法: python3 build.py <slug> <模块前缀>   例: python3 build.py business-ethics-csr p156
模块: <前缀>a.py (ACT1) <前缀>b.py (ACT2) <前缀>c.py (BRIDGE1/BRIDGE2/TAIL/PROPS) refs<号>.py (REFS)"""
import re, sys, html, importlib.util, collections

SITE = '/home/claude/site/public/frontier/'

def load(name):
    spec = importlib.util.spec_from_file_location(name, f'/home/claude/fa/{name}.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def esc(s):  # 只转 & 与尖括号，保留已写好的实体
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def first_author(ref):
    head = ref.split('，')[0]
    head = re.split(r',| &| 与| 等|（', head)[0].strip()
    return head

def year_of(ref):
    m = re.search(r'，(\d{4})，', ref)
    return m.group(1) if m else '?'

def main():
    slug, pre = sys.argv[1], sys.argv[2]
    num = re.sub(r'\D', '', pre)
    A = load(pre + 'a').ACT1; B = load(pre + 'b').ACT2; C = load(pre + 'c'); REFS = load('refs' + num).REFS
    entries = A + B
    assert len(entries) == 20, len(entries)

    order = []  # ref keys in first-use order
    def rn(k):
        assert k in REFS, k
        if k not in order: order.append(k)
        return order.index(k) + 1

    def cite(k):
        return f'（{esc(first_author(REFS[k]))} {year_of(REFS[k])}，Ref.[{rn(k)}]）'

    out = []
    out.append('<main>')
    def act(title, bridge, items):
        out.append(f'<div class="act">{title}</div><p class="bridge">{esc(bridge)}</p>')
        for e in items:
            out.append('<article class="idea">')
            out.append(f'<h2>{e["n"]}、{esc(e["t"])}<span class="en">{esc(e["en"])}</span></h2>')
            s = e['src']
            k0 = s['提出']; k1, t1 = s['争议']; k2, t2 = s['最新']
            src = (f'<b>提出：</b>{esc(REFS[k0])}（Ref.[{rn(k0)}]）　'
                   f'<b>争议：</b>{esc(t1)}（Ref.[{rn(k1)}]）　'
                   f'<b>最新：</b>{esc(t2)}（Ref.[{rn(k2)}]）　'
                   f'<b>关键：</b>{esc(s["关键"])}')
            out.append(f'<div class="src">{src}</div>')
            assert 5 <= len(e['ps']) <= 7, (e['n'], len(e['ps']))
            for txt, k in e['ps']:
                assert not re.search(r'（[^（）]*Ref\.', txt), (e['n'], '正文里不要手写引注')
                out.append(f'<p>{esc(txt)}{cite(k)}</p>')
            c = e['col']
            col = '　'.join(f'<b>{f}：</b>{esc(c[f])}' for f in ['位置','单因','预设','量纲','失效','自曝','空栏','异名'])
            out.append(f'<div class="col">{col}</div></article>')
    act('【第一幕】上一个十年 · 约 2006—2016', C.BRIDGE1, A)
    act('【第二幕】这十年 · 约 2016—2026', C.BRIDGE2, B)
    for title, paras in C.TAIL:
        out.append(f'<h3 class="sec">{esc(title)}</h3>')
        for p in paras: out.append(f'<p>{esc(p)}</p>')
    out.append('<h3 class="sec">◎ 十条可做的研究命题</h3><ol class="propositions">')
    assert len(C.PROPS) == 10
    for i, (t, a, b, c) in enumerate(C.PROPS, 1):
        out.append(f'<li><b>{i}.</b> <b>{esc(t)}</b>　{esc(a)}　{esc(b)}　{esc(c)}</li>')
    out.append('</ol>')
    out.append('<h3 class="sec">◎ 资料核验</h3><div class="refs"><ol>')
    for k in order: out.append(f'<li>{esc(REFS[k])}</li>')
    out.append('</ol></div>')

    path = SITE + slug + '/index.html'
    h = open(path, encoding='utf-8').read()
    i = h.find('<main>'); j = h.find('<div class="end">')
    assert i > 0 and j > i
    new = h[:i] + '\n'.join(out) + h[j:]

    # 汉字数：header + main 的可见文本
    body = re.sub(r'<script.*?</script>|<style.*?</style>', '', new, flags=re.S)
    vis = body[body.find('<header'):body.find('<div class="end">')]
    cjk = len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', vis)))
    new, n = re.subn(r'全文 <b>\d+</b> 汉字', f'全文 <b>{cjk}</b> 汉字', new)
    assert n == 1
    open(path, 'w', encoding='utf-8').write(new)

    # 读数
    txt = re.sub(r'<[^>]+>', '', '\n'.join(out))
    pos = collections.Counter(re.findall(r'位置：\s*([SDE])', txt))
    rev = sum(1 for e in entries if re.search(r'反而', e['col']['失效']))
    fams = collections.Counter(re.findall(r'〔(\d+)', txt))
    zb = len(set(e['col']['自曝'] for e in entries))
    ym = re.findall(r'另见第 (\d+) 号', txt)
    ym_ext = sorted(set(ym))
    plens = [len(re.findall(r'[\u4e00-\u9fff]', t)) for e in entries for t, _ in e['ps']]
    print(f'{slug}: 汉字 {cjk}; 位置 S{pos["S"]}/D{pos["D"]}/E{pos["E"]}; 失效反号 {rev}/20; 前提族 {len(fams)} 种 {dict(fams)}; 自曝 {zb}/20 种; 异名指向 {ym_ext}; 文献 {len(order)} 条; 段落汉字 {min(plens)}–{max(plens)} 均 {sum(plens)//len(plens)}')
    return ym_ext

if __name__ == '__main__':
    main()
