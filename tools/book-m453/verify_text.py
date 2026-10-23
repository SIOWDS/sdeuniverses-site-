"""核对：分卷稿的章文与定稿逐字一致（仅允许的版式差异：标记符、◆ 编号、块标签、第 29 章一节归位）。"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
DRAFT = Path(sys.argv[1])


def norm_draft(t):
    out = []
    for l in t.split('\n'):
        if l.startswith('# ') and re.match(r'# (第[一二三四五六七八九十]+部|第 \d+ 章|导论|结语)', l): continue
        if re.match(r'## (带走的话|SDE 小账)$', l): continue
        l = re.sub(r'^(#{1,3} |> ?)', '', l)
        out.append(l)
    return out


def norm_conv(t):
    out = []
    for l in t.split('\n'):
        if re.match(r'#{1,2} (第 \d+ 章|第[一二三四五六七八九十]+部|导论|结语)', l): continue
        if re.match(r'> \*\*(经文|带走的话|小账)\*\*$', l): continue
        l = re.sub(r'^### ◆ [一二三四五六七八九十]+、', '', l)
        l = re.sub(r'^(#{1,3} |> ?)', '', l)
        out.append(l)
    return out


def stream(lines):
    return re.sub(r'\s+', '', ''.join(lines)).replace('**', '')


def split_chapters(text):
    parts = re.split(r'\n(?=## 第 \d+ 章)', '\n' + text)
    res = {}
    for p in parts[1:]:
        n = int(re.match(r'## 第 (\d+) 章', p)[1]); res[n] = p
    return res


bad = 0
conv = {}
for f in sorted((HERE / 'parts').glob('*.md')):
    t = f.read_text(encoding='utf-8')
    # 部首导语不在对比范围
    conv.update(split_chapters(t))
for p in sorted(DRAFT.glob('[0-9][0-9]_*.md')):
    n = int(p.name[:2])
    if n in (0, 99): continue
    d = p.read_text(encoding='utf-8')
    if n == 36:   # 稿内带部标题与部首短引
        d = d[d.index('# 第 36 章'):]
    a = stream(norm_draft(d))
    b = stream(norm_conv(conv[n]))
    if a != b:
        if n == 29:
            # 一节归位：以“十六个短句读完了”为界重排后比较
            i = d.index('## 十六个短句读完了'); j = d.index('## 带走的话')
            d2 = d[:j] if False else d
            sec = d[i:]; rest = d[:i]
            k = rest.index('## 带走的话')
            d_re = rest[:k] + sec + '\n' + rest[k:]
            a2 = stream(norm_draft(d_re))
            # 标题“十六个短句读完了”在转换稿里变成 ◆ 小节
            if a2 == b:
                print('ch29: OK（仅“十六个短句读完了”一节归位到带走的话之前）'); continue
        bad += 1
        import difflib
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        print('DIFF ch', n, [(tag, a[i1:i2][:40], b[j1:j2][:40]) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal'][:5])
for name, dn, fn in [('导论', '00_导论.md', 'front/01-导论.md'), ('结语', '99_结语.md', 'back/09-结语.md')]:
    d = (DRAFT / dn).read_text(encoding='utf-8'); c = (HERE / fn).read_text(encoding='utf-8')
    if stream(norm_draft(d)) != stream(norm_conv(c)):
        bad += 1; print('DIFF', name)
print('不一致章数：', bad)
