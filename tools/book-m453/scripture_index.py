"""附录一“经文索引”：据 经文核对总表.md 核对过的章稿，逐章扫描引注生成；并与总表按“书卷+章”交叉核对，差异记入 zhuangpei_issues。"""
import re, sys
from pathlib import Path

BOOKS = ['创', '出', '利', '民', '申', '士', '撒下', '诗', '箴', '伯', '耶', '何', '拿', '太', '可', '路', '约', '徒', '罗', '林前', '林后', '加', '弗', '腓', '门', '来', '雅', '彼后', '启']
FULL = {'创': '创世记', '出': '出埃及记', '利': '利未记', '民': '民数记', '申': '申命记', '士': '士师记', '撒下': '撒母耳记下', '诗': '诗篇', '箴': '箴言', '伯': '约伯记', '耶': '耶利米书',
        '何': '何西阿书', '拿': '约拿书', '太': '马太福音', '可': '马可福音', '路': '路加福音', '约': '约翰福音', '徒': '使徒行传', '罗': '罗马书', '林前': '哥林多前书', '林后': '哥林多后书',
        '加': '加拉太书', '弗': '以弗所书', '腓': '腓立比书', '门': '腓利门书', '来': '希伯来书', '雅': '雅各书', '彼后': '彼得后书', '启': '启示录'}
BK = '|'.join(sorted(BOOKS, key=len, reverse=True))
V = r'\d+(?:[-—–]\d+)?(?:[、,，]\d+(?:[-—–]\d+)?)*'
TOK = re.compile(r'(?<![一-鿿])(%s)\s?(\d+)(?:[:：](%s))?' % (BK, V))
CONT = re.compile(r'^[ ]?[；;、/／][ ]?(\d+)[:：](%s)' % V)


def scan_text(txt):
    """返回 [(书卷, '章:节' 或 '章')]。"""
    out = []
    for m in TOK.finditer(txt):
        bk, ch, vs = m[1], m[2], m[3]
        # 排除“约 3 万字”“来 3 次”之类：要求紧跟 : 或前面是左括号/顿号等；纯“书卷+数字”(无节)只在带“章”字或在括注内才算
        tail = txt[m.end():m.end() + 1]
        if vs is None:
            if tail != '章' and not re.search(r'[（(、；]\s*$', txt[max(0, m.start() - 2):m.start()]):
                continue
        out.append((bk, '%s:%s' % (ch, vs.replace('—', '-').replace('–', '-').replace('，', ',').replace(',', '、')) if vs else ch))
        # 同书卷续项 “；8:10”
        rest = txt[m.end():]
        while True:
            m2 = CONT.match(rest)
            if not m2: break
            out.append((bk, '%s:%s' % (m2[1], m2[2].replace('，', '、').replace(',', '、'))))
            rest = rest[m2.end():]
    return out


def chap_label(head):
    if head.startswith('# 导论'): return '导论'
    if head.startswith('# 结语'): return '结语'
    return re.match(r'# 第 (\d+) 章', head)[1]


def norm_spec(vs):
    return [x for x in re.split(r'[、,，]', vs.replace('—', '-').replace('–', '-')) if x]


def parse_table(path):
    """核对总表“出处”列 → {书卷: {章: {'v': set(节), 'labs': set(所在章)}}}"""
    t = Path(path).read_text(encoding='utf-8')
    idx = {}
    for sec in re.split(r'\n(?=# )', t)[1:]:
        lines = sec.split('\n')
        lab = chap_label(lines[0])
        for l in lines:
            if not l.startswith('|') or l.startswith('| #') or l.startswith('|---'): continue
            ref = [x.strip() for x in l.strip().strip('|').split('|')][1]
            if '先于' in ref or '章对象' in ref: continue
            ref = re.sub(r'[、,，](\d+[:：])', r'；\1', ref)
            for m in TOK.finditer(ref):
                bk, ch, vs = m[1], m[2], m[3]
                d = idx.setdefault(bk, {}).setdefault(int(ch), {'v': set(), 'labs': set()})
                d['labs'].add(lab)
                if vs: d['v'].update(norm_spec(vs))
                tail = ref[m.end():]
                m2 = CONT.match(tail)
                while m2:
                    d2 = idx[bk].setdefault(int(m2[1]), {'v': set(), 'labs': set()})
                    d2['labs'].add(lab); d2['v'].update(norm_spec(m2[2]))
                    tail = tail[m2.end():]; m2 = CONT.match(tail)
    return idx


def vkey(x):
    return [int(n) for n in re.findall(r'\d+', x)]


def labkey(l):
    return (0, 0) if l == '导论' else (2, 0) if l == '结语' else (1, int(l))


def render(idx):
    rows = []
    for bk in BOOKS:
        if bk not in idx: continue
        items = []
        for ch in sorted(idx[bk]):
            d = idx[bk][ch]
            labs = '、'.join(sorted(d['labs'], key=labkey))
            if d['v']:
                items.append('%d:%s（%s）' % (ch, '、'.join(sorted(d['v'], key=vkey)), labs))
            else:
                items.append('%d 章（%s）' % (ch, labs))
        rows.append('| %s | %s |' % (FULL[bk], '　'.join(items)))
    return rows


def scan_pairs(draft_dir):
    """章稿里实际出现的 (书卷, 章)，用于交叉核对。"""
    out = set()
    for p in Path(draft_dir).glob('[0-9][0-9]_*.md'):
        txt = p.read_text(encoding='utf-8')
        for m in TOK.finditer(txt):
            if m[3] or txt[m.end():m.end() + 1] == '章':
                out.add((m[1], int(m[2])))
    return out


if __name__ == '__main__':
    idx = parse_table(sys.argv[1])
    print('\n'.join(render(idx)))
    have = {(bk, ch) for bk in idx for ch in idx[bk]}
    miss = sorted(scan_pairs(sys.argv[2]) - have)
    print('table refs (book,chapter):', len(have), '| in draft text but not in 核对总表:', miss, file=sys.stderr)
