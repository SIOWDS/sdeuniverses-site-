#!/usr/bin/env python3
"""第 36 号《人—GPT超级复合智能体》：著者 Word 初稿（pandoc 转出的 src/draft-pandoc.md）→ 分卷清稿 parts/*.md。

只做排印与结构层面的清理，文字打磨另行（见 parts/ 的提交历史）：
去稿内封面封底图与手排目录；三编七篇的标题层级统一（# 编／独立篇目，## 篇，### 章／引言／结语，#### 节，%% 篇内分编）；
连接号、破折号、引号、中西文间空格统一；稿内残留的字面 ** 与公式粘贴重影清掉。

用法：python3 convert.py            （pandoc -f docx -t markdown --wrap=none 初稿.docx -o src/draft-pandoc.md 之后）
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
CJK = r'一-鿿　-〿＀-￯“”‘’—…·'
CNUM = '一二三四五六七八九十'
PIAN = {  # 篇名｜副题（副题取自原稿篇首破折号行；第四、五篇取自原稿目录）
    1: '存在是什么？｜从 SIO 发生学到 GPT 作为新型存在者',
    2: 'GPT 是什么？｜从概率模型到理念 SIO 意义三律引擎',
    3: '何谓智能体？｜从点状幻觉到 SIO 意义整体的重构',
    4: '人—GPT 超级复合智能体的诞生（上）｜工具期与伙伴期',
    5: '人—GPT 超级复合智能体的诞生（下）｜复合萌芽与文明转向',
    6: '教育的超级复合智能体｜三体课堂与家庭—学校—GPT 的 SIO 重组',
    7: '健康的超级复合智能体｜医生、GPT 与病人的三体 SIO 对话',
}


def fix_quotes(s):
    n = 0

    def rep(m):
        nonlocal n
        n += 1
        return '“' if n % 2 else '”'
    s = re.sub(r'[“”"]', rep, s)
    # 中文语境里的单引号按序配对；英文撇号（Can't）不动
    k = [0]

    def rep1(m):
        k[0] += 1
        return '‘' if k[0] % 2 else '’'
    if len(re.findall(r"(?<![A-Za-z])['‘’]|['‘’](?![A-Za-z])", s)) % 2 == 0:
        s = re.sub(r"(?<![A-Za-z])['‘’]|['‘’](?![A-Za-z])", rep1, s)
    return s


def clean(s, bib=False):
    s = s.replace('\\*', '*').replace('\\_', '_').replace('\\[', '[').replace('\\]', ']').replace("\\'", "'").replace('\\"', '"')
    s = s.replace('\\~', '~').replace('\\<', '<').replace('\\>', '>').replace('\\$', '$').replace('\\|', '|')
    s = s.rstrip('\\').strip().strip('　').strip()
    if bib:
        return re.sub(r'(\d)--(\d)', r'\1–\2', s).replace('---', '—')
    s = s.replace('------', '——').replace('---', '——')
    s = re.sub(r'(\d)--(\d)', r'\1–\2', s).replace('--', '—')
    s = s.replace('－', '—')
    s = fix_quotes(s)
    # 中西文之间、引号内侧的空格一律去掉（排版时再按版式加细空）
    s = re.sub(r'(?<=[%s]) +(?=[A-Za-z0-9ΔθΣ=×→+/\*(])' % CJK, '', s)
    s = re.sub(r'(?<=[A-Za-z0-9ΔθΣ=×→+/\*)%%]) +(?=[%s])' % CJK, '', s)
    s = re.sub(r'(?<=[%s]) +(?=[%s])' % (CJK, CJK), '', s)
    s = re.sub(r' {2,}', ' ', s)
    s = re.sub(r' *(?<![=<>!])=(?!=) *', ' = ', s)
    s = re.sub(r' *× *', ' × ', s)
    s = re.sub(r'(?<=[一-鿿])vs ', ' vs ', s)
    s = re.sub(r'\*\*\s*\*\*', '', s)
    if s.count('**') % 2:   # 稿内落单的字面 **：去掉最后一个
        i = s.rfind('**'); s = s[:i] + s[i + 2:]
    s = re.sub(r'\*\*([，。；：、！？”）]+)\*\*', r'\1', s)
    return s.strip()


def head_text(line):
    t = re.sub(r'^#+\s*', '', line).replace('**', '')
    return clean(t)


def main():
    L = (HERE / 'src' / 'draft-pandoc.md').read_text().split('\n')
    # 0-based 行号 → 1-based 与 grep -n 一致
    out = []          # (key, lines)
    cur = None

    def start(key):
        nonlocal cur
        cur = []; out.append((key, cur))

    def nxt(i):   # 下一条非空行
        j = i + 1
        while j < len(L) and not re.sub(r'^#+\s*$', '', L[j]).strip():
            j += 1
        return j

    i, n, pian, zone = 0, len(L), 0, 'front'
    start('00-专家推荐与导论')
    while i < n:
        raw = L[i]; ln = i + 1
        s = raw.strip()
        if not s or re.fullmatch(r'#+', s) or s == '>' or s == '**    **':
            i += 1; continue
        if s.startswith('!['):
            i += 1; continue
        if 41 <= ln <= 69:   # 手排目录
            i += 1; continue
        ht = head_text(s)
        is_head = s.startswith('#') or re.fullmatch(r'\*\*[^*]+\*\*\\?\s*　*', s) is not None
        boldhead = not s.startswith('#')
        if boldhead and is_head and (len(ht) > 62 or ht.endswith(('。', '；', '：')) and not ht.startswith(('引言', '结语'))):
            is_head = False
        # ── 专家推荐 ──
        if ln == 3:
            cur += ['# 专家推荐', '']; i += 1; continue
        if s.startswith('• • '):
            who = clean(s[4:].replace('**', ''))
            body = clean(L[i + 1]).strip('“”')
            cur += ['### ' + who, '', body, '']
            i += 2; continue
        if is_head:
            j = nxt(i); nt = head_text(L[j]) if j < n else ''
            if ht == '导论':
                cur += ['# 导论　' + nt, '']; i = j + 1; continue
            m = re.match(r'^([上中下])编序?$', ht)
            if m and ht != '上编结论':
                key = {'上': '10-上编序', '中': '40-中编序', '下': '70-下编序'}[m[1]]
                start(key); cur += ['# %s编　%s' % (m[1], nt), '', '## 编序', '']; i = j + 1; continue
            m = re.match(r'^([上中下])编结论$', ht)
            if m:
                start({'上': '35-上编结', '中': '65-中编结', '下': '85-下编结'}[m[1]])
                if m[1] == '下':
                    cur += ['## 编结', '']; i += 1
                else:
                    cur += ['## 编结　' + nt, '']; i = j + 1
                continue
            m = re.match(r'^第([一二三六七])篇 ?', ht)
            if m or ht.startswith('人—GPT超级复合智能体的诞生') or ht.startswith('人-GPT超级复合智能体的诞生'):
                pian += 1
                start('%d0-第%s篇' % (pian + (0 if pian < 4 else 1 if pian < 6 else 2), CNUM[pian - 1]) if False else
                      {1: '20-第一篇', 2: '25-第二篇', 3: '30-第三篇', 4: '50-第四篇', 5: '60-第五篇', 6: '75-第六篇', 7: '80-第七篇'}[pian])
                cur += ['## 第%s篇　%s' % (CNUM[pian - 1], PIAN[pian]), '']
                i = j + 1   # 第二行（副题或「（上）」）已并入
                continue
            if ht == '摘要':
                cur += ['### 摘要', '']; i += 1; continue
            if ht.startswith('引言：'):
                t = ht[3:]
                if t.endswith('——') and L[j].startswith('#'):
                    t += nt; i = j
                cur += ['### 引言　' + t, '']; i += 1; continue
            m = re.match(r'^第([%s]+)编 ?　?(.*)$' % CNUM, ht)
            if m:
                cur += ['%%%% 第%s编　%s' % (m[1], m[2].strip()), '']; i += 1; continue
            m = re.match(r'^(第[%s]+章|特别章|结论章|附录一)　?(.*)$' % CNUM, ht)
            if m:
                t = m[2].strip()
                if t.endswith('：') and L[j].startswith('#'):
                    t += nt; i = j
                cur += ['### %s　%s' % (m[1], t), '']; i += 1; continue
            m = re.match(r'^(结语|结论|后记)：(.*)$', ht)
            if m:
                t = m[2]
                if t.endswith('——') and L[j].startswith('#'):
                    t += nt; i = j
                cur += ['### %s　%s' % (m[1], t), '']; i += 1; continue
            if ht == '结论':
                start('90-结论与后置'); cur += ['# 结论　' + nt, '']; i = j + 1; continue
            if ht in ('金句集锦', '致谢', '参考书目'):
                cur += ['# ' + ht, '']; zone = ht; i += 1; continue
            m = re.match(r'^(\d+)\. (.*)$', ht)
            if m and zone == '金句集锦':
                cur += ['### ' + m[2], '']; i += 1; continue
            if re.match(r'^[%s]、' % CNUM, ht):
                cur += ['#### ' + ht, '']; i += 1; continue
            if not boldhead:
                raise SystemExit('未识别的标题 %d: %s' % (ln, s[:80]))
            print('  bold line kept as paragraph', ln, ht[:50])
        # ── 正文 ──
        if ln == 879:   # 粘贴残留的半行题名
            i += 1; continue
        if s.startswith('> '):
            s = s[2:]
        if zone == '参考书目':
            m = re.match(r'^(\d+)\.\s+(.*)$', s)
            assert m, s
            cur += ['%s. %s' % (m[1], clean(re.sub(r'!\[.*$', '', m[2]), bib=True)), '']; i += 1; continue
        t = clean(s)
        # 「**小标题**\」换行接正文：并成一段，小标题留作段首加粗
        if raw.rstrip().endswith('\\') and i + 1 < n and L[i + 1].strip():
            t = t + '　' + clean(L[i + 1]); i += 1
        if re.match(r'^[-•]\s+', t):
            t = '- ' + re.sub(r'^[-•]\s+', '', t)
        cur += [t, '']
        i += 1

    (HERE / 'parts').mkdir(exist_ok=True)
    tot = 0
    for key, lines in out:
        txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip() + '\n'
        (HERE / 'parts' / (key + '.md')).write_text(txt)
        h = len(re.findall(r'[一-鿿]', txt)); tot += h
        print(key, 'han', h, 'h3', len(re.findall(r'^### ', txt, re.M)), 'bian', len(re.findall(r'^%% ', txt, re.M)))
    print('total han', tot)


if __name__ == '__main__':
    main()
