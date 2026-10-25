#!/usr/bin/env python3
"""第 408 号修订版上站（2026-10-25）：署名改为陈晓艳著、王德生指导；正文并入陈晓艳稿的文献对话。
用法（仓库根目录）：python3 tools/book-m408/update_v2.py --build /home/claude/bk408
需先跑 make_covers.py 与 build.py（产物在 --build 目录）；cover.jpg 由 /home/claude/m408/editcover.py 改署名行。
"""
import argparse, hashlib, json, re, shutil
from pathlib import Path
HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
D = SITE / 'books/m/408'
OLD, V = '20261022a', '20261025a'
SLUG = 'rongbukai-lizi'

def sub1(s, o, n, cnt=1):
    assert s.count(o) == cnt, (o[:50], s.count(o)); return s.replace(o, n)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); ap.add_argument('--cover', type=Path, required=True)
    a = ap.parse_args(); b = a.build
    import pymupdf
    pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf'))); rpages = len(pymupdf.open(str(b / f'{SLUG}-reader.pdf')))
    shutil.copy(b / f'{SLUG}-print.pdf', D / f'{SLUG}-print.pdf')
    shutil.copy(b / f'{SLUG}-reader.pdf', D / f'{SLUG}-reader.pdf')
    shutil.copy(a.cover, D / 'cover.jpg')
    # 全文网页：换 cover 版本号已在 build 里（META version）
    shutil.copy(b / 'text.html', D / 'text/index.html')

    # ── 详情页 ──
    p = D / 'index.html'; s = p.read_text()
    s = s.replace(OLD, V)
    s = sub1(s, '· 王德生 著 · 德麦国际 ·', '· 陈晓艳 著 · 王德生 指导 · 德麦国际 ·')
    s = sub1(s, '<div><b>著者</b><span>王德生</span></div>', '<div><b>著者</b><span>陈晓艳</span></div><div><b>指导</b><span>王德生</span></div>')
    s = re.sub(r'<div><b>执笔</b><span>.*?</span></div>',
               '<div><b>执笔</b><span>复合主体：王德生立题、口述承重命题并指导；陈晓艳撰写书稿，修订版并入其稿中与心理学文献的对话；AI（Claude）协作起草与统稿，经初审、复审、终审定稿</span></div>', s, count=1)
    s = re.sub(r'约 22\.7 万字 · 印刷版 455 页', '约 23 万字 · 印刷版 %d 页' % pages, s)
    s = sub1(s, '<div><b>完稿</b><span>2026 年 10 月 22 日</span></div>', '<div><b>完稿</b><span>2026 年 10 月 22 日初版；10 月 25 日修订（署名改为陈晓艳著、王德生指导，第 4、15、19 章与附录二、三补入与前人研究的对话）</span></div>')
    s = re.sub(r'<h2>作者简介</h2>\s*<p>王德生，.*?</p>',
               '<h2>作者简介</h2>\n<p>陈晓艳，生物学博士，高级健康管理师，大学教师，王德生博士终身学员，系统研修三视角理论、321 理论、SIO 体系与 SDE 本体论。在德麦国际出版社已出版《家庭教育的智慧》（第 65 号）、《陈晓艳讲海德格尔》（第 208 号）、《陈晓艳讲孔子的教育智慧》（第 233 号）等专著。<a href="/students/chen-xiaoyan/">学员主页</a></p>\n'
               '<p>指导老师王德生，SIO 本体论与 SDE 发生学的创立者，德麦国际创始人，SDE Universes 平台主持人；SDE 符号学系列理论十卷的主持人。</p>', s, count=1, flags=re.S)
    s = re.sub(r'复合主体注释：本书立题与承重命题出自王德生，写作口径由作者与编辑共同裁定，文字由 AI 协作成稿；',
               '复合主体注释：本书立题与承重命题出自王德生，书稿由陈晓艳在其指导下写成，文字由 AI 协作起草与统稿；修订版据陈晓艳稿补入赫尔曼、恐惧泛化、循证实践三要素、构念效度等前人研究，并把“场与失配交互”一处的“独有”收窄为“最想检验”；', s, count=1)
    p.write_text(s)

    # ── 学习包、问对页、单元配置 ──
    # ── 翻页器：新目录与偏移（照初版加封面、封底两条） ──
    toc = json.loads((b / 'toc-reader.json').read_text())
    items = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}] + [dict(x, t=x['t'].replace(' ', '　', 1) if x['t'].startswith(('第', '前言', '结语', '附录')) else x['t']) for x in toc['toc']] + [{'t': '封底', 'p': '', 'g': rpages, 'l': 1}]
    q = D / 'read.html'; t = q.read_text()
    cfg = {'pdf': f'/books/m/408/{SLUG}-reader.pdf?v={V}', 'key': 'books-m-408-v2', 'offset': toc['offset']}
    t, k1 = re.subn(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), t, flags=re.S)
    t, k2 = re.subn(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(items, ensure_ascii=False), t, flags=re.S)
    assert k1 == k2 == 1
    q.write_text(t)
    for f in ['agent/dialogue.html', 'agent/learning.html', 'agent/index.html', 'read.html']:
        q = D / f; t = q.read_text().replace(OLD, V)
        t = t.replace('alt="王德生著"', 'alt="陈晓艳著，王德生指导"').replace('初版（2026-10-22）', '修订版（2026-10-25）')
        t = t.replace('王德生 著', '陈晓艳 著 · 王德生 指导').replace('王德生著', '陈晓艳著、王德生指导')
        q.write_text(t)
    q = D / 'unit/app.js'; t = q.read_text()
    t = t.replace("《熔不开的粒子：心的符号学》 · 王德生 ", "《熔不开的粒子：心的符号学》 · 陈晓艳 著、王德生 指导 ").replace('初版', '修订版')
    q.write_text(t)
    q = D / 'unit/SKILL.md'; t = q.read_text()
    t = sub1(t, '《熔不开的粒子：心的符号学》，王德生著，', '《熔不开的粒子：心的符号学》，陈晓艳著、王德生指导，').replace('初版（2026-10-22）', '修订版（2026-10-25）')
    q.write_text(t)
    for f in ['publication-unit.json', 'unit/learning.json']:
        q = D / f; j = json.loads(q.read_text())
        j['authors'] = ['陈晓艳']; j['advisor'] = '王德生'
        if 'sourceEdition' in j: j['sourceEdition'] = '修订版（2026-10-25）'
        if 'revision' in j: j['revision'] = '20261025-m408-unit-v2'
        q.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
    import sys; sys.path.insert(0, str(HERE)); from md2src import chapter_md, to_plain
    files = sorted(str(x) for x in (HERE / 'parts').glob('*.md'))
    for q in (D / 'unit/sources').glob('chapter-*.json'):
        j = json.loads(q.read_text()); j['version'] = '修订版（2026-10-25）'
        if j['lesson'] in (4, 15, 19):   # 修订版改动的三章：问对智能体的章节原文同步
            t = to_plain(chapter_md(files, j['lesson']))
            if '\n\n---\n\n带走的话' in j['text']: t = t.replace('\n\n带走的话', '\n\n---\n\n带走的话')
            u = j['sections'][0]['url']
            j['sections'] = [{'title': x[2:], 'url': u} for x in re.findall(r'^◆ .+$', t, re.M)]
            j['text'] = t; j['sha256'] = hashlib.sha256(t.encode()).hexdigest()
        q.write_text(json.dumps(j, ensure_ascii=False, indent=2) + '\n')

    # ── 书目 catalog ──
    q = SITE / 'books/catalog.json'; t = q.read_text()
    i = t.index('"id": "m-408"'); j0 = t.rfind('{', 0, i); j1 = t.index('\n    }', i) + 6
    blk = t[j0:j1]
    nb = re.sub(r'"authors": \[\s*"王德生"\s*\]', '"authors": [\n        "陈晓艳"\n      ]', blk, count=1).replace(OLD, V)
    assert nb != blk and '陈晓艳' in nb
    q.write_text(t[:j0] + nb + t[j1:])
    # ── /today/ 新书卡 ──
    q = SITE / 'today/index.html'; t = q.read_text()
    k = t.count('王德生著。SDE 符号学系列理论卷书八。心里卡住的')
    assert k >= 1
    t = t.replace('王德生著。SDE 符号学系列理论卷书八。心里卡住的', '陈晓艳著，王德生指导。SDE 符号学系列理论卷书八。心里卡住的')
    t = t.replace('By Wang Desheng. What stays stuck in the mind', 'By Chen Xiaoyan, supervised by Wang Desheng. What stays stuck in the mind')
    t = t.replace('德麦国际专著第 408 号 · 约 22.7 万字 · 455 页', '德麦国际专著第 408 号 · 约 23 万字 · %d 页' % pages)
    t = t.replace('DEMAI MONOGRAPH No.408 · ~227,125 CHARS · 455 PP', 'DEMAI MONOGRAPH No.408 · ~230,000 CHARS · %d PP' % pages)
    q.write_text(t)
    print('ok pages', pages, rpages)

if __name__ == '__main__':
    main()
