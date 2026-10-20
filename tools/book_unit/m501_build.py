#!/usr/bin/env python3
"""第501号《道德经SDE新解》单元生成入口（共用 build_unit.py，运行时在内存里打补丁，不改 build_unit.py）。

与一章一题的本子不同，本书 81 章 + 导论 + 结卷，学习单元 45 条，每条配置里写 units：
  整数 N        = 第 N 章（锚点取全文页 <section class="chapter" id="sN">，章内 ◆ 小节入 sections）
  "导论一" 等   = 全稿里同名 `# 导论一　……` 一节（锚点取全文页 <h1 class="fs-title">导论一</h1> 所在 section）
一条单元的原文 = 其 units 依次拼接（学习页只载入这一条的原文）。
补丁：
  ① 章数与题数不再要求相等；② 原文来源按 units 取；③ 分编标签、侧栏标题、PDF 副标题取配置里的
  partNames / partLabels / asideHeading / pdfSubtitle；④ 「章」字样改「单元」；
  ⑤ 作答横线行距 24→20（题干较长）；⑥ 读页 read.html、详情页 index.html 尚未存在时跳过接线
     （publish.py 发布后请重跑本脚本一次，接线是幂等的）；⑦ 沿用 m370 的 398 断言放宽。
用法（仓库根目录）：
  python3 tools/book_unit/m501_build.py --config tools/book_unit/m501.json --out-pdf <学习包 PDF 路径>
"""
import importlib.util, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / 'build_unit.py').read_text(encoding='utf-8')

def sub(old, new, cnt=1):
    global src
    assert src.count(old) == cnt, (src.count(old), old[:70])
    src = src.replace(old, new)

# ① 章数与题数
sub("    assert len(chaps) == nch and [c['lesson'] for c in chaps] == list(range(1, nch + 1)), 'chapters vs tasks mismatch'\n",
    "    assert [c['lesson'] for c in chaps] == list(range(1, len(chaps) + 1)), 'chapter numbering'\n"
    "    EXTRAS = extras_of(C['manuscript'])\n")
sub("    part_names = [p.split('　', 1)[1] for p in parts]\n", "    part_names = C['partNames']\n")
sub("    assert len(anchors) == nch, 'text page anchors: %d' % len(anchors)\n",
    "    assert len(anchors) == len(chaps), 'text page anchors: %d' % len(anchors)\n"
    "    exa = {m.group(2): m.group(1) for m in re.finditer(r'<section class=\"[^\"]*\" id=\"(s\\d+)\"><h1 class=\"fs-title[^\"]*\">([^<]+)</h1>', tx)}\n")
sub("'parts': part_names, 'tasks': [],", "'parts': part_names, 'partLabels': C['partLabels'], 'tasks': [],")

# ② 原文来源
a = src.index("    for t, c in zip(C['tasks'], chaps):")
b = src.index("    jw('unit/learning.json', manifest)")
NEW = '''    byno = {c['lesson']: c for c in chaps}
    url = URL + 'text/'
    for t in C['tasks']:
        i = t['lesson']; parts_txt = []; secs = []; titles = []; first = None
        for u in t['units']:
            if isinstance(u, int):
                c = byno[u]; ttl = c['title']; anc = anchors[u]; bd = plain(c['body'])
            else:
                head = [k for k in EXTRAS if k.startswith(u + '　')]
                assert len(head) == 1, u
                ttl = head[0]; anc = exa[u]; bd = plain(EXTRAS[ttl])
            first = first or anc; titles.append(ttl)
            parts_txt.append(ttl + '\\n\\n' + bd)
            secs += [{'title': m.group(1).strip(), 'url': url + '#' + anc} for m in re.finditer(r'^◆ (.*)$', bd, flags=re.M)]
        text = '\\n\\n'.join(parts_txt)
        h = sha(text.encode())
        ttl_all = ' ／ '.join(titles)
        src_ = {'book': 'm-%d' % N, 'lesson': i, 'version': C['sourceEdition'], 'title': ttl_all, 'units': t['units'], 'url': url + '#' + first, 'sha256': h, 'sections': secs, 'text': text}
        jw('unit/sources/chapter-%02d.json' % i, src_)
        manifest['tasks'].append({'lesson': i, 'problemId': 'M%d-U%02d' % (N, i), 'part': t['part'], 'title': t['name'], 'question': t['question'],
                                  'checkpoint': t['checkpoint'], 'chapterTitle': ttl_all, 'units': t['units'], 'sourceUrl': url + '#' + first,
                                  'sourceData': U + 'unit/sources/chapter-%02d.json' % i, 'sourceSha256': h})
'''
src = src[:a] + NEW + src[b:]

# helper: extras_of
sub("def plain(body):", '''def extras_of(path):
    s = Path(path).read_text(encoding='utf-8'); out = {}
    for blk in re.split(r'\\n(?=# )', '\\n' + s):
        blk = blk.strip('\\n')
        if not blk.startswith('# '): continue
        head, _, body = blk.partition('\\n')
        out[head[2:].strip()] = body
    return out

def plain(body):''')

# ③ 标签
sub("app = sub1(app, \"'第'+(i+1)+'编 · '\", \"'第'+(i+1)+'%s · '\" % PW)",
    "app = sub1(app, \"'第'+(i+1)+'编 · '\", \"(manifest.partLabels||[])[i]+' · '\")")
sub("'aria-label=\"%s章任务\"><h2>%s%s · %s章</h2>' % (NUMW, cn(len(parts)), PW, NUMW)",
    "'aria-label=\"%s个学习单元\"><h2>%s</h2>' % (NUMW, C['asideHeading'])")
sub("'%s%s%s章 · 阅读、学习、智能问对' % (cn(len(parts)), PW, NUMW)", "C['pdfSubtitle']")
sub("'第%d%s · %s' % (t['part'], PW, part_names[t['part'] - 1])", "'%s · %s' % (C['partLabels'][t['part'] - 1], part_names[t['part'] - 1])")

# ④ 章 → 单元
sub("'学习包 · %s章实践' % NUMW", "'学习包 · %s个学习单元' % NUMW")
sub("'下载%s章学习包 PDF' % NUMW", "'下载学习包 PDF'")
sub("'学习包 · %s章%s实践' % (NUMW, C['practiceWord'])", "'学习包 · %s个学习单元' % NUMW")
sub("学习包 · %s章实践</a>", "学习包 · %s个学习单元</a>")
sub("学习包 · %s章%s实践</a>", "学习包 · %s个学习单元</a>")
sub("U, U, NUMW, C['practiceWord'], U, C['agentName'], U, U, C['learningPdfUrl'])", "U, U, NUMW, U, C['agentName'], U, U, C['learningPdfUrl'])")
sub("点击进入本章学习、原文与%s：第%d章", "点击进入本单元学习、原文与%s：第%d单元")
sub('''app = sub1(app, "+' / 40 章 ·", "+' / %d 章 ·" % nch)''', '''app = sub1(app, "+' / 40 章 ·", "+' / %d 个单元 ·" % nch)''')
sub('''"n>%d)throw Error('题号不在本书%s章范围内。')" % (nch, NUMW)''', '''"n>%d)throw Error('单元号不在本书%s个单元范围内。')" % (nch, NUMW)''')
sub("    w('unit/app.js', app)\n", "    app = app.replace(\"'第'+lesson+'章已准备\", \"'第'+lesson+'单元已准备\")\n    w('unit/app.js', app)\n")

# ⑤ 行距
n = src.count('y -= 24'); assert n == 3, n
src = src.replace('y -= 24', 'y -= 20')

# ⑥ 接线：read.html / index.html 尚不存在时跳过
a = src.index("    p = BOOK / 'read.html'; t = p.read_text(encoding='utf-8')")
b = src.index("    print(json.dumps({'tasks': nch")
blk = src[a:b]
blk = ''.join('    ' + l if l.strip() else l for l in blk.splitlines(True))
src = (src[:a] + "    if (BOOK / 'read.html').exists() and (BOOK / 'index.html').exists():\n" + blk +
       "    else:\n        print('NOTE: read.html / index.html 尚不存在，已跳过接线；publish.py 发布后请重跑本脚本。')\n" + src[b:])

# ⑦ 断言放宽
src = src.replace("assert '398' not in app and '判生' not in app", "assert 'm-398' not in app and 'm398' not in app and '/398/' not in app and 'Book 398' not in app and '判生' not in app")
src = src.replace("assert '398' not in skill,", "assert '398' not in skill.replace(C['isbn'], ''),")
src = src.replace("assert '398' not in pg.replace('@@', ''),", "assert '398' not in pg.replace('@@', '').replace(C['isbn'], ''),")

tmp = Path(tempfile.gettempdir()) / '_build_unit_m501.py'
tmp.write_text(src, encoding='utf-8')
spec = importlib.util.spec_from_file_location('build_unit', tmp)
bu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bu)

if __name__ == '__main__':
    bu.main()
