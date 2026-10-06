#!/usr/bin/env python3
"""第 232 号《SDE红学》：作者 Word 稿 → 清稿 manuscript.md（只做排印层面的清理，不改正文）。

用法：python3 convert.py <书稿.docx>
清理项：去掉稿内旧封面图、旧版权页（ISBN 待申请）与手排目录（由 build.py 重排）；
引号按段配对成 “ ”；SDE 三字的中文名按现行口径（显露·差异序列·特征纠缠，共三处）；去掉 pandoc 的转义与空注释。"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def fix_quotes(line):
    n = 0
    k = [0]

    def rep1():
        k[0] += 1
        return '‘' if k[0] % 2 else '’'

    def rep(m):
        nonlocal n
        n += 1
        return '“' if n % 2 else '”'
    line = re.sub(r'[“”"]', rep, line)
    if len(re.findall(r"[‘’']", line)) % 2 == 0:   # 引号内的单引号同样按序配对
        n = 0
        line = re.sub(r"[‘’']", lambda m: rep1(), line)
    return line


def main():
    src = sys.argv[1]
    md = subprocess.run(['pandoc', src, '-t', 'gfm', '--wrap=none'], capture_output=True, text=True, check=True).stdout
    out, skip = [], False
    for line in md.splitlines():
        if line.startswith('# '):
            skip = line[2:].strip() in ('版权页', '目录')
        if skip or line.startswith('<img') or line.strip() == '<!-- -->':
            continue
        if '撕了两半**”，宝玉在旁' in line:   # 稿内此处多出一个引号，去掉以免全段引号错位
            line = line.replace('撕了两半**”，宝玉在旁', '撕了两半**，宝玉在旁')
        line = line.replace('\\> ', '').replace('\\[', '[').replace('\\]', ']')
        # S 的名称按现行口径：显露（Show），不作“结构”
        line = line.replace('SDE（结构 Structure · 差异 Difference · 纠缠 Entanglement）', 'SDE（显露 Show · 差异序列 Difference · 特征纠缠 Entanglement）')
        line = line.replace('SDE（结构·差异·纠缠）', 'SDE（显露·差异序列·特征纠缠）')
        if not line.startswith('|'):
            line = fix_quotes(line)
        else:
            line = re.sub(r'[“”]([^“”|]*)[“”]', r'“\1”', line)
        out.append(line.rstrip())
    text = re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'
    assert '\\' not in text, [l for l in text.splitlines() if '\\' in l][:3]
    (HERE / 'manuscript.md').write_text(text)
    print('han', len(re.findall(r'[一-鿿]', text)), 'h1', len(re.findall(r'^# ', text, re.M)))


if __name__ == '__main__':
    main()
