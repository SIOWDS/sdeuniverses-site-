#!/usr/bin/env python3
"""第 456 号《慌：心之荒》：把 /home/claude/hang-book 下的定稿（front、parts、back、cites）合成 220/302 版式工具链的分卷稿。
只做格式拼装：给上中下三篇加篇首、从各编第 6 章抽「本编哪里可能错」成附录五、从核验 JSON 生成附录四。正文文字不动。
产物：front/00-前置.md、front/01-导论.md、parts/0N-第N编.md、back/11-结语.md、back/12-后置.md、book.md。
用法：python3 tools/book-m456/assemble.py
"""
import json, re, shutil
from pathlib import Path

HERE = Path(__file__).parent
S = Path('/home/claude/hang-book')
CN = '零一二三四五六七八九'
PIAN = {
    1: ('上篇　慌是什么', ['上篇三编，各问一个「是什么」。第一编把慌和怕、急、累、痛、乱分开，立起三环。第二编问：沙堆、鱼群、人群里的慌，是不是同一回事；思考、现实、自我三界的荒，各是什么样子。第三编问：「别慌」「沉住气」遮住了什么。',
                         '三编合起来，只做一件事：把慌从「胆小」「不冷静」里请出来，放回一件正在发生的事里。']),
    4: ('中篇　慌怎样发生', ['中篇三编，各问一个「怎样」。第四编把一个早晨的找钥匙一步步拆开，看一次慌怎样走下来。第五编看慌怎样固化成长期的心慌、传开成一群人的抢购。第六编看好的慌：同一场荒里，新心怎样长出来。',
                           '三编合起来，看的是同一段时间差：差异已到，承受已破，重组未及，以及这段时间里还能发生什么。']),
    7: ('下篇　慌为什么被推出来', ['下篇三编，各问一个「为什么」。第七编问人为什么必然会慌。第八编问慌和创造、自由、幸福是什么关系。第九编问慌的那一刻，自己和身边的人该怎么办。',
                                 '三编合起来，把慌从一件要关掉的警报，放回心还活着的证据里。']),
}


def han(s):
    return len(re.findall(r'[一-鿿]', s))


def part(k):
    t = next(S.glob('parts/0%d-*.md' % k)).read_text()
    t = re.sub(r'^## 第 (\d+) 章　', r'## 第\1章　', t, flags=re.M)
    head, rest = t.split('\n', 1)
    assert head.startswith('# 第%s编　' % CN[k]), head
    if k in PIAN:
        name, paras = PIAN[k]
        rest = '\n\n**%s**\n\n%s\n\n' % (name, '\n\n'.join(paras)) + rest.lstrip('\n')
    return head + '\n' + rest


def wrong_sections(parts):
    out = ['## 附录五　本书自认最弱的几处与推翻条件', '',
           '每一编的第 6 章都写了「本编哪里可能错」。这里把九编的推翻条件放在一起：找到其中任何一种常见的情形，相应的判断就要收窄或改写。']
    for k, t in parts.items():
        title = t.split('\n', 1)[0].split('　', 1)[1]
        last = re.split(r'^## ', t, flags=re.M)[-1]
        m = re.search(r'^### ◆ [^\n]*可能错[^\n]*\n(.*?)(?=^### ◆|^> \*\*带走的话)', last, re.S | re.M)
        assert m, k
        body = [p.strip() for p in m.group(1).strip().split('\n\n') if p.strip()]
        body = [p for p in body if not p.startswith(('一个判断，要能被推翻', '一个判断要能被推翻', '这一编说了不少'))]
        body = [p.replace('上面那个', '本编那个').replace('前面那个小试', '本编那个小试').replace('前面那个', '本编那个') for p in body]
        out += ['', '### 第%s编　%s' % (CN[k], title), ''] + ['\n\n'.join(body)]
    return '\n'.join(out) + '\n'


def cite_table():
    rows = []
    for k in range(1, 10):
        for d in json.loads((S / 'cites' / ('%d.json' % k)).read_text()):
            src = re.sub(r'https?://\S+', '', d.get('source', '')).strip(' ；;，,')
            src = re.sub(r'\s{2,}', ' ', src).replace('|', '／')
            item = d['item'].replace('|', '／')
            st = d['status'].strip('〔〕')
            rows.append((int(d['chapter']), item, src, st))
    rows.sort(key=lambda r: r[0])
    n = {s: sum(1 for r in rows if r[3] == s) for s in ('核', '核：大意', '据研究文献', '待验')}
    out = ['## 附录四　引文核验总表', '',
           '全书引到的古今中外各家，三审时逐条查对，结果如下，共 %d 条：〔核〕%d 条，为已查对出处；〔核：大意〕%d 条，为出处已查对、引文只取大意；〔据研究文献〕%d 条，为依据研究综述；〔待验〕%d 条，为本书自己推出、尚待日子与研究去验的局面。'
           % (len(rows), n['核'], n['核：大意'], n['据研究文献'], n['待验']), '',
           '| 章 | 所涉 | 依据 | 结果 |', '|---|---|---|---|']
    for c, item, src, st in rows:
        out.append('| 第 %d 章 | %s | %s | 〔%s〕 |' % (c, item, src or '本书推出', st))
    return '\n'.join(out) + '\n', len(rows)


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    shutil.copy(S / 'front/00-前置.md', HERE / 'front/00-前置.md')
    shutil.copy(S / 'front/01-导论.md', HERE / 'front/01-导论.md')
    parts = {}
    for k in range(1, 10):
        parts[k] = part(k)
        (HERE / ('parts/0%d-第%s编.md' % (k, CN[k]))).write_text(parts[k])
    shutil.copy(S / 'back/11-结语.md', HERE / 'back/11-结语.md')
    ct, ncite = cite_table()
    head = (S / 'back/fulu-head.md').read_text().strip()
    tail = (S / 'back/fulu-tail.md').read_text().strip()
    (HERE / 'back/12-后置.md').write_text(head + '\n\n' + ct + '\n' + wrong_sections(parts) + '\n' + tail + '\n')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/0%d-第%s编.md' % (k, CN[k]) for k in range(1, 10)] + ['back/11-结语.md', 'back/12-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text().strip() + '\n' for f in files))
    b = (HERE / 'book.md').read_text()
    body = ''.join((HERE / f).read_text() for f in files[1:-1])
    print('ok chapters', len(re.findall(r'^## 第\d+章　', b, re.M)), 'cites', ncite, 'hanzi all', han(b), 'body(导论至结语)', han(body))


if __name__ == '__main__':
    main()
