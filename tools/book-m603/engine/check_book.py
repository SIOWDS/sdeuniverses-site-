#!/usr/bin/env python3
"""企业本体论审读版 · 成书体检。待裁/待核/待补只统计并列表，不当错误。
用法：python3 check_book.py --config book.json --manuscript 统稿.md --outdir out/ --report check_report.json"""
import argparse, json, os, re, subprocess, sys
ERR, WARN = [], []
def han(t): return len(re.findall(r'[一-鿿]', t))

def sections(s):
    """按 (部件/章) 切块，返回 [(label, text)]"""
    out, cur, buf = [], '前置', []
    for l in s.split('\n'):
        m1 = re.match(r'# (.+)$', l); m2 = re.match(r'## (第 \d+ 章)　(.*)$', l); m3 = re.match(r'## (附录[A-C])　', l)
        if m1 or m2 or m3:
            out.append((cur, '\n'.join(buf))); buf = []
            cur = (m2.group(1) if m2 else m3.group(1) if m3 else m1.group(1))
        buf.append(l)
    out.append((cur, '\n'.join(buf)))
    return out

def check_md(cfg, s):
    rep = {}
    tops = [l[2:].strip() for l in s.splitlines() if l.startswith('# ')]
    order = ['出版信息', '作者介绍', '前言', '导读']
    for w in order + ['结语', '参考书目', '附录']:
        if not any(t.split('　')[0] == w for t in tops): ERR.append(f'缺一级部分：{w}')
    parts = [t for t in tops if re.match(r'第[一二三四五六七八九十]+编　', t)]
    if len(parts) != 10: ERR.append(f'编数 {len(parts)}，应为10')
    chs = [int(x) for x in re.findall(r'^## 第 (\d+) 章　', s, flags=re.M)]
    if chs != list(range(1, 61)): ERR.append(f'章号不是 1..60：共 {len(chs)} 章')
    # 每章首块是证据身份引用块
    for m in re.finditer(r'\n## (第 \d+ 章)　[^\n]*\n+(.{0,12})', s):
        if not m.group(2).startswith('> 证据身份'): WARN.append(f'{m.group(1)}：章首不是「证据身份」块')
    # 每章含本章小结
    for lab, t in sections(s):
        if lab.startswith('第 ') and '### 本章小结' not in t: WARN.append(f'{lab}：缺「## 本章小结」')
    # 待标记清单
    tags = []
    for lab, t in sections(s):
        for m in re.finditer(r'〔[^〕]*?(待裁|待核|待补)[^〕]*〕', t):
            tags.append({'kind': m.group(1), 'where': lab, 'text': m.group(0)[:120]})
    rep['tag_counts'] = {k: sum(1 for x in tags if x['kind'] == k) for k in ('待裁', '待核', '待补')}
    rep['tag_list'] = tags
    # 编务词
    ed = []
    for lab, t in sections(s):
        for w in ['总纲', '任务书', '总编', '统稿']:
            for m in re.finditer(w, t):
                ed.append({'word': w, 'where': lab, 'ctx': t[max(0, m.start() - 15):m.end() + 15].replace('\n', ' ')})
    rep['editorial_words'] = ed
    # 直引号
    q = []
    for lab, t in sections(s):
        for ch in ['"', "'"]:
            for m in re.finditer(re.escape(ch), t):
                q.append({'char': ch, 'where': lab, 'ctx': t[max(0, m.start() - 12):m.end() + 12].replace('\n', ' ')})
    rep['straight_quotes'] = q
    # 案例标注
    rep['case_tag_residual'] = len(re.findall(r'【构造案例|构造案例[·・]设想', s))
    rep['case_tag_standard'] = len(re.findall(r'构造案例（设想）', s))
    rep['residual_corner_brackets'] = sorted(set(re.findall(r'【[^】]{0,20}】', s)))
    for mark in ['【交接卡】', '> 接续说明']:
        if mark in s: ERR.append(f'内部标记残留：{mark}')
    # 联系方式
    if re.search(r'1[3-9]\d{9}|@gmail|jimmywang', s): ERR.append('书稿含疑似联系方式')
    # 汉字
    body = s[s.find('\n# 第一编'):s.find('\n# 结语')]
    rep['han_total'] = han(s); rep['han_body_10parts'] = han(body)
    rep['chapters'] = len(chs); rep['parts'] = len(parts)
    return rep

def check_pdf(cfg, outdir):
    import pypdf
    rep = {}
    for kind, fn in [('print', cfg['slug'] + '-print.pdf'), ('reader', cfg['slug'] + '-reader.pdf')]:
        p = os.path.join(outdir, fn)
        if not os.path.exists(p): WARN.append(f'找不到 {fn}'); continue
        r = pypdf.PdfReader(p); rep[kind + '_pages'] = len(r.pages)
        f = subprocess.run(['pdffonts', p], capture_output=True, text=True).stdout.splitlines()[2:]
        if any(re.search(r'\sno\s+(yes|no)\s+(yes|no)', l) for l in f): ERR.append(f'{fn}：有未嵌入的字体')
        if not r.outline: ERR.append(f'{fn}：没有书签')
        if kind == 'reader':
            for i in (0, len(r.pages) - 1):
                res = r.pages[i].get('/Resources', {})
                for key in ('/Shading', '/Pattern'):
                    if key in res and len(res[key]) > 0: ERR.append(f'{fn} 第 {i + 1} 页用了渐变（{key}）')
        txt = subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, text=True).stdout.split('\f')
        tocp = '\n'.join(t for t in txt if t.strip().startswith('目 录') or '·····' in t[:3000] and '目 录' in t[:200])
        nums = re.findall(r'·\s*(\d+)\s*$', tocp, flags=re.M)
        if nums and len(set(nums)) <= 1: ERR.append(f'{fn}：目录页码全是 {nums[0]}')
    return rep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--manuscript', required=True)
    ap.add_argument('--outdir'); ap.add_argument('--report')
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf-8')); s = open(a.manuscript, encoding='utf-8').read()
    rep = check_md(cfg, s)
    if a.outdir: rep.update(check_pdf(cfg, a.outdir))
    rep['errors'] = ERR; rep['warnings'] = WARN
    if a.report: json.dump(rep, open(a.report, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    summ = {k: v for k, v in rep.items() if k not in ('tag_list', 'editorial_words', 'straight_quotes')}
    summ['editorial_words'] = len(rep['editorial_words']); summ['straight_quotes'] = len(rep['straight_quotes'])
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    sys.exit(1 if ERR else 0)
if __name__ == '__main__': main()
