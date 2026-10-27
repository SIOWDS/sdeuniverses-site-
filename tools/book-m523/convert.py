#!/usr/bin/env python3
"""第 523 号《陈晓艳谈「懂」》（由第 522 号 convert.py 改来）：把 meta.SRC 定稿（YAML 头 + 作者介绍、前言、导读 + 导论 + 九编四十五章
+ 结语 + 参考书目 + 附录（总页＋附录一至五）+ 后记）转成 220/302 版式工具链的分卷稿。只做格式转换，不动正文文字。
章尾件：【带走的话】【小账】×2【想一想】×N → 三个引用框。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import meta as M  # noqa
CN = '零一二三四五六七八九'

def ends(text):
    """章末【带走的话】【小账】【想一想】 → 220 版式的三个引用框；编序【编序】去标记。"""
    L = text.split('\n'); out = []; i = 0
    while i < len(L):
        s = L[i].strip()
        m = re.match(r'^【带走的话】\s*(.*)$', s)
        if m:
            out += ['> **带走的话**', '> ' + m[1].strip(), '']; i += 1
            q = []
            while i < len(L):
                if not L[i].strip(): i += 1; continue
                mm = re.match(r'^【小账】\s*(.*)$', L[i].strip())
                if not mm: break
                q.append(mm[1].strip()); i += 1
            if q: out += ['> **小账**'] + ['> ' + c for c in q] + ['']
            qs = []
            while i < len(L):
                if not L[i].strip(): i += 1; continue
                if L[i].startswith('#') or L[i].strip() == '---': break
                mm = re.match(r'^【想一想】\s*(.*)$', L[i].strip())
                qs.append(mm[1].strip() if mm else L[i].strip()); i += 1
            if qs: out += ['> **想一想**'] + ['> %d.  %s' % (k + 1, c) for k, c in enumerate(qs)] + ['']
            continue
        m = re.match(r'^【编序】\s*(.*)$', s)
        if m: out.append(m[1]); i += 1; continue
        if s == '---': i += 1; continue
        out.append(L[i]); i += 1
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'

def main():
    raw = Path(M.SRC).read_text()
    yml, body = raw.split('\n---\n', 1)
    stmts = re.findall(r'^statement:\s*(.*)$', yml, re.M)
    execu = re.search(r'^executor:\s*(.*)$', yml, re.M)[1]
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    wan = round(han(body) / 10000)
    body = body.lstrip('\n')
    # 切块：前置（作者介绍、前言、导读）、导论、九编、结语、后置；标题一律按行首匹配
    body = '\n' + body
    def cut(a, b=None):
        i = body.index('\n' + a) + 1
        j = body.index('\n' + b, i) + 1 if b else len(body)
        return body[i:j]
    front = cut('# 作者介绍', '# 导论')
    lun = cut('# 导论', '# 第一编')
    CNB = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    NB = 9
    bian = [cut('# 第%s编　' % CNB[k], '# 第%s编　' % CNB[k + 1] if k < NB else '# 结语') for k in range(1, NB + 1)]
    jieyu = cut('# 结语', '# 参考书目')
    bib = cut('# 参考书目', '# 附录\n')
    appx = cut('# 附录\n', '# 后记')
    hou = cut('# 后记')
    cp = ['## 出版信息', '| 项 | 内容 |', '|---|---|']
    for a, b in [('书名', '《%s》' % M.FULL_TITLE), ('英文书名', M.TITLE_EN), ('著者', M.AUTHOR), ('执笔', execu),
                 ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % M.NO),
                 ('ISBN', M.ISBN), ('定价', M.PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 %d 万字' % wan), ('版次', '2026 年 10 月第 1 版')]:
        cp.append('| %s | %s |' % (a, b))
    notes = stmts + ['版权所有　侵权必究']
    front = re.sub(r'^# ', '## ', front, flags=re.M)
    front = ends(front)
    (HERE / 'front').mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(cp) + '\n\n' + '\n\n'.join(notes) + '\n\n' + front)
    (HERE / 'front/01-导论.md').write_text(ends(lun))
    (HERE / 'parts').mkdir(exist_ok=True)
    for k in range(1, NB + 1):
        t = bian[k - 1]
        head, rest = t.split('\n', 1)
        assert head.startswith('# 第%s编' % CNB[k]), head
        t = head + '\n\n' + rest.lstrip('\n')
        t = re.sub(r'^## 第 (\d+) 章　', r'## 第\1章　', t, flags=re.M)
        (HERE / ('parts/0%d-第%s编.md' % (k, CNB[k]))).write_text(ends(t))
    (HERE / 'back').mkdir(exist_ok=True)
    (HERE / 'back/11-结语.md').write_text(ends(jieyu))
    appx = re.sub(r'^# 附录([一二三四五])', r'## 附录\1', appx, flags=re.M)
    (HERE / 'back/12-后置.md').write_text(bib.strip() + '\n\n' + appx.strip() + '\n\n' + hou.strip() + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CNB[k]) for k in range(1, NB + 1)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'hanzi', han(b), 'body wan', wan)

if __name__ == '__main__':
    main()
