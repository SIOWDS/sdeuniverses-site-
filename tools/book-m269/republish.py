#!/usr/bin/env python3
"""第 268 号回改后换新版（v1.1）：覆盖页面文件，更新书目条目；PDF 另走 R2（新文件名，不覆盖旧版）。
用法：python3 republish.py --build /home/claude/bk268"""
import argparse, json, re, shutil, datetime
from pathlib import Path
HERE = Path(__file__).parent
SITE = HERE.resolve().parents[1] / 'public'
NO = 268; V = '20261012b'; SLUG = 'jingyi-qiujing'
T = '人-AI 如何走向复合体的精益求精？'
R2 = f'https://sdeuniverses.com/students/wang-desheng/{SLUG}/m{NO}/'
DESC = '精益求精是一个方程：S3＝最优方程(D3,E3)，用最优化的能量投入，去实现预先设定的真善美。这个方程要靠意义方程与技术方程互相碰撞才能实现，六步法是发生路径，每一圈目标被抬高，圆变成螺旋。复合不是分工：两个方程在人与 AI 之间互相碰撞。全书从一碗面和一份发言稿写起，走过九编四十一章，并押上三条可错的预言。'
b = Path(argparse.ArgumentParser().parse_known_args()[0] and '.')
ap = argparse.ArgumentParser(); ap.add_argument('--build', type=Path, required=True); b = ap.parse_args().build
d = SITE / 'books' / 'm' / str(NO)
for f in ['cover.jpg', 'backcover.jpg']: shutil.copy(b / f, d / f)
shutil.copy(b / 'text.html', d / 'text' / 'index.html')
import pymupdf
pages = len(pymupdf.open(str(b / f'{SLUG}-print.pdf'))); rpages = len(pymupdf.open(str(b / f'{SLUG}-reader.pdf')))
files = sorted(str(x.relative_to(HERE)) for x in HERE.glob('front/*.md')) + sorted(str(x.relative_to(HERE)) for x in (HERE / 'parts').glob('*.md')) + sorted(str(x.relative_to(HERE)) for x in HERE.glob('back/*.md'))
han = sum(len(re.findall(r'[一-鿿]', (HERE / f).read_text())) for f in files)
# read.html：就地换目录、PDF 地址与版本
rd = d / 'read.html'; t = rd.read_text()
toc = json.loads((b / 'toc-reader.json').read_text())
toc['toc'] = [{'t': '封面', 'p': '', 'g': 1, 'l': 1}] + toc['toc'] + [{'t': '封底', 'p': '', 'g': rpages, 'l': 1}]
cfg = {'pdf': f'/students/wang-desheng/{SLUG}/m{NO}/{SLUG}-reader-v1.1.pdf', 'key': f'books-m-{NO}-v1.1', 'offset': toc['offset']}
t = re.sub(r'<script type="application/json" id="cfg">.*?</script>', lambda m: '<script type="application/json" id="cfg">%s</script>' % json.dumps(cfg, ensure_ascii=False), t, flags=re.S)
t = re.sub(r'<script type="application/json" id="toc">.*?</script>', lambda m: '<script type="application/json" id="toc">%s</script>' % json.dumps(toc['toc'], ensure_ascii=False), t, flags=re.S)
rd.write_text(t)
# 详情页：保留 build_unit 加的单元按钮，故只替换书的正文块（从 <h1> 起到 作者简介 前）
old = (d / 'index.html').read_text()
new = (HERE / 'detail.html').read_text().replace('__V__', V).replace('__PAGES__', str(pages)).replace('__WAN__', '%.0f' % (han / 10000))
(d / 'index.html').write_text(new)  # build_unit 之后会重新注入单元按钮
# 书目
p = SITE / 'books' / 'catalog.json'; data = json.loads(p.read_text())
e = next(x for x in data['books'] if x.get('number') == NO)
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
e.update(description=DESC, pdfPages=rpages, printPdfPages=pages, hanTotal=han, revision='20261012-m268-v1.1',
         pdfUrl=R2 + f'{SLUG}-reader-v1.1.pdf?v={V}', readPdfUrl=R2 + f'{SLUG}-reader-v1.1.pdf?v={V}',
         printPdfUrl=R2 + f'{SLUG}-v1.1.pdf?v={V}', coverUrl=f'https://sdeuniverses.com/books/m/{NO}/cover.jpg?v={V}',
         backcoverUrl=f'https://sdeuniverses.com/books/m/{NO}/backcover.jpg?v={V}')
e['publicationUnit']['revision'] = '20261012-m268-unit-v1.1'
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
# /today/ 卡
tp = SITE / 'today' / 'index.html'; h = tp.read_text()
h = re.sub(r'(德麦国际专著第 268 号 · 约 )\d+( 万字 · )\d+( 页)', lambda m: f'{m[1]}{han/10000:.0f}{m[2]}{pages}{m[3]}', h)
h = re.sub(r'(DEMAI MONOGRAPH No\.268 · ~)[\d,]+( CHARS · )\d+( PP)', lambda m: f'{m[1]}{han:,}{m[2]}{pages}{m[3]}', h)
h = h.replace('王德生著。精益求精不再是工匠精神，而是人-AI 复合体的发生学：意义与技术共同推动，最优化与能量相撞，真善美一圈圈走向极致。复合不是分工，矛盾发生在人与 AI 之间。九编四十一章，押上三条可错的预言。',
              '王德生著。精益求精不再是工匠精神，而是人-AI 复合体的发生学：S3＝最优方程(D3,E3)，意义方程与技术方程互相碰撞，用最优化的能量投入实现预先设定的真善美。复合不是分工，两个方程在人与 AI 之间碰撞。九编四十一章，押上三条可错的预言。')
h = h.replace('Mastery is no longer a craft virtue but the genesis of a human-AI compound: meaning and technique push together, optimization collides with energy, and truth, goodness and beauty climb round by round.',
              'Mastery is no longer a craft virtue but the genesis of a human-AI compound: S3 = Optimum(D3, E3) — the meaning equation and the technique equation collide, and optimized energy input realizes a preset truth, goodness and beauty, round by round.')
tp.write_text(h)
print('republished', pages, rpages, han)
