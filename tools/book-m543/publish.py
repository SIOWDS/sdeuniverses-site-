#!/usr/bin/env python3
"""第 543 号《奥特曼为何感到悲伤？》补齐“阅读 · 学习包 · 智能问对”三位一体（阅读已上线）。
在 tools/book-m543/build_unit_543.py 之后运行；只动本书与共用登记，可重跑（幂等）：

  public/books/m/543/keypoints.json          本书各章要点与带走的话（逐条标章次，取自 content.json）
  public/books/m/543/agent/index.html        智能体页（由第 541 号页的骨架换头部与书号；共用 /books/agent/app.js）
  public/books/m/543/index.html              详情页：加三位一体入口块，书生入口换成本书智能体的名字
  public/books/agents.json                   登记本书智能体（名字全站唯一）
  public/books/agent/index.html              智能体名录里把第 543 号那张“书生”卡换成本书的名字与称号
  public/books/index.html、public/monographs/index.html、public/sites/read/library/index.html
                                             书架卡（tools/build_bookshelf.py --shelf-only 由 catalog 重生成；其余各书的卡不变）
  public/books/catalog.json                  第 543 号条目补 agentLabel/agentName/agentUrl/learnLabel/learnUrl/learningUrl/learningPackUrl/publicationUnit

不跑 tools/build_book_agents.py 与 tools/inject_book_agent.py（它们会重写全站名录与全部详情页）；
rag.json 由 python3 tools/build_book_rag.py 543 另行生成。
不动 read.html、text/、封面、书本身的 PDF；不写 R2；不提交。
用法（仓库根目录）：python3 tools/book-m543/publish.py
"""
import datetime
import html
import json
import re
import subprocess
import sys
from pathlib import Path

NO = 543
HERE = Path('tools/book-m543')
CFG = json.loads(Path('tools/book_unit/m543.json').read_text(encoding='utf-8'))
CT = json.loads((HERE / 'content.json').read_text(encoding='utf-8'))
AG = CT['agent']
NAME, EPI, INTRO = AG['name'], AG['epithet'], AG['intro']
TITLE = CFG['title']
U = '/books/m/%d/' % NO
URL = 'https://sdeuniverses.com' + U
V = CFG['assetVersion']
esc = lambda s: html.escape(s, quote=True)
today = datetime.date.today().isoformat()
BOOK = Path('public/books/m/%d' % NO)


def main():
    # 1. keypoints.json
    items = CT['keypoints']
    assert len(items) >= 10 and all(len(re.sub(r'\s', '', i['x'])) >= 90 and i['ch'] for i in items)
    assert sum(len(i['x']) + len(i['t']) + len(i['ch']) + 8 for i in items) < 8000, 'agent/app.js 的 kpText 只取前 8000 字'
    kp = {'no': NO, 'title': TITLE, 'built': today, 'items': [{'t': i['t'], 'x': i['x'], 'ch': i['ch']} for i in items]}
    (BOOK / 'keypoints.json').write_text(json.dumps(kp, ensure_ascii=False) + '\n', encoding='utf-8')

    # 2. agents.json
    ap = Path('public/books/agents.json')
    reg = json.loads(ap.read_text(encoding='utf-8'))
    clash = [k for k, v in reg['agents'].items() if v.get('name') == NAME and k != str(NO)]
    assert not clash, '智能体重名：%s' % clash
    reg['agents'][str(NO)] = {'name': NAME, 'epithet': EPI, 'intro': INTRO, 'starts': AG['starts']}
    for k in ('updatedAt', 'updated'):
        if k in reg:
            reg[k] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if k == 'updatedAt' else today
    ap.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    # 3. agent/index.html：第 541 号页的骨架，换头部与书号
    src = Path('public/books/m/541/agent/index.html').read_text(encoding='utf-8')
    head_end = src.index('<link rel="stylesheet" href="/books/agent/app.css')
    head = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(NAME)} · 《{esc(TITLE)}》的智能体 | 德麦国际专著第 {NO} 号</title>
<meta name="description" content="{esc(INTRO)}">
<meta name="sde-page-kind" content="tool">
<meta name="book-agent" content="{esc(NAME)}"><meta name="book_no" content="{NO}">
<link rel="canonical" href="https://sdeuniverses.com/books/m/{NO}/agent/">
<meta property="og:title" content="{esc(NAME)} · 《{esc(TITLE)}》的智能体">
<meta property="og:description" content="{esc(INTRO)}">
<meta property="og:image" content="https://sdeuniverses.com/books/m/{NO}/cover.jpg?v={V}">
'''
    page = head + src[head_end:]
    assert page.count('window.BOOK_AGENT={no:541};') == 1
    page = page.replace('window.BOOK_AGENT={no:541};', 'window.BOOK_AGENT={no:%d};' % NO)
    assert '541' not in page and '辨名' not in page, [l[:100] for l in page.splitlines() if '541' in l]
    (BOOK / 'agent' / 'index.html').write_text(page, encoding='utf-8')

    # 4. 名录：把第 543 号那张卡（原为“书生”占位）换成本书的
    dp = Path('public/books/agent/index.html')
    d = dp.read_text(encoding='utf-8')
    card = '<a class="c" href="/books/m/%d/agent/"><b>%s</b><i>%s</i><span>《%s》 · 第 %d 号</span></a>' % (NO, esc(NAME), esc(EPI), esc(TITLE), NO)
    pat = re.compile(r'<a class="c" href="/books/m/%d/agent/">.*?</a>' % NO, re.S)
    assert len(pat.findall(d)) == 1, '名录里应恰有一张第 %d 号的卡' % NO
    dp.write_text(pat.sub(lambda m: card, d, count=1), encoding='utf-8')

    # 5. 详情页：三位一体入口块（放在按钮区之前，与第 541 号同构）+ 智能体入口换名
    ip = BOOK / 'index.html'
    t = ip.read_text(encoding='utf-8')
    S0, E0 = '<!-- UNIT_START -->', '<!-- UNIT_END -->'
    t = re.sub(re.escape(S0) + '.*?' + re.escape(E0), '', t, flags=re.S)
    blk = (S0 + '<section aria-label="三位一体出版单元" style="margin:1.3rem 0"><p style="color:#d6b663;margin-bottom:.5rem">阅读、学习、智能问对三位一体出版单元</p><div style="display:grid;gap:.6rem">'
           '<a class="btn solid" href="%sread.html">阅读 · 在线翻页</a><a class="btn" href="%sagent/learning.html">学习包 · %s件明天能试的小事</a>'
           '<a class="btn" href="%sagent/dialogue.html">智能问对 · %s</a></div><p style="color:#9aa;font-size:.85rem;margin-top:.5rem">配套学习设计，不是著者原文或能力认证；学习记录只留在你的浏览器。<a href="%sunit/SKILL.md">问对规范</a> · <a href="%spublication-unit.json">单元版本与边界</a> · <a href="%s">下载学习包 PDF</a></p></section>' + E0) % (
        U, U, CFG['countWord'], U, NAME, U, U, CFG['learningPdfUrl'])
    assert t.count('<div class="btns">') == 1
    t = t.replace('<div class="btns">', blk + '<div class="btns">', 1)
    old = re.search(r'<a class="ssh-e" href="/books/m/%d/agent/".*?</a>' % NO, t, re.S)
    assert old, 'ssh-e 入口不在'
    new = old.group(0)
    new = re.sub(r'aria-label="[^："]*：', 'aria-label="%s：' % esc(NAME), new)
    new = re.sub(r'<span class="ssh-n">[^<]*</span>', '<span class="ssh-n">%s</span>' % esc(NAME), new)
    new = re.sub(r'<b>《[^<]*》的智能体 · [^<]*</b>', '<b>《%s》的智能体 · %s</b>' % (esc(TITLE), esc(EPI)), new)
    new = re.sub(r'和「[^」]*」对话 ›', '和「%s」对话 ›' % esc(NAME), new)
    assert '书生' not in new, new
    t = t.replace(old.group(0), new, 1)
    ip.write_text(t, encoding='utf-8')

    # 6. catalog.json：只改第 543 号条目，字段名照第 541、542 号
    cp = Path('public/books/catalog.json')
    data = json.loads(cp.read_text(encoding='utf-8'))
    ent = next(b for b in data['books'] if b.get('id') == 'm-%d' % NO)
    assert ent['isbnDisplay'] == CFG['isbn'] and ent['title'] == TITLE, '条目与配置不符'
    ent.update({
        'agentUrl': URL + 'agent/dialogue.html', 'agentName': NAME, 'agentLabel': '智能问对 · ' + NAME,
        'learnUrl': URL + 'agent/learning.html', 'learningUrl': URL + 'agent/learning.html', 'learnLabel': CT['detail']['learnLabel'],
        'learningPackUrl': CFG['learningPdfUrl'],
        'publicationUnit': {'id': 'm-%d' % NO, 'type': 'reading-learning-dialogue', 'revision': CFG['unitRev']},
    })
    # 键序：把新字段放在 tier 之前，与第 542 号一致
    order = [k for k in ent if k not in ('tier', 'citeOk', 'publicationUnit')] + ['tier', 'citeOk', 'publicationUnit']
    data['books'] = [({k: b[k] for k in order} if b is ent else b) for b in data['books']]
    if data.get('updated', '') < today:
        data['updated'] = today
    cp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # 7. 书架三个入口（books/、monographs/、sites/read/library/）由 catalog 生成：只重生成书架页，不跑 build_book_agents / inject_book_agent
    subprocess.run([sys.executable, 'tools/build_bookshelf.py', '--shelf-only'], check=True)
    print('ok: keypoints %d, agent %s, catalog/detail/agents/directory updated' % (len(items), NAME))


if __name__ == '__main__':
    main()
