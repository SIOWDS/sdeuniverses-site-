#!/usr/bin/env python3
"""合稿：按成书次序拼出《普通人都能懂的老子》全稿，生成目录并报字数。

用法：python3 assemble.py  → 写出 全稿.md，并打印各部分汉字数
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
ORDER = [
    'front/00-前置.md',
    'parts/01-第一编.md', 'parts/02-第二编.md', 'parts/03-第三编.md', 'parts/04-第四编.md',
    'parts/05-第五编.md', 'parts/06-第六编.md', 'parts/07-第七编.md', 'parts/08-第八编.md',
    'back/09-结语.md', 'back/10-后置.md',
]
HAN = re.compile(r'[一-鿿]')


def toc(texts):
    lines = ['## 目录', '']
    for t in texts:
        for ln in t.splitlines():
            if re.match(r'^# 第.编', ln):
                lines.append(f'**{ln[2:].strip()}**')
                lines.append('')
            elif re.match(r'^## 第 \d+ 章', ln):
                lines.append(f'　{ln[3:].strip()}')
                lines.append('')
            elif re.match(r'^# (结语|参考书目|附录|后记)', ln):
                lines.append(f'**{ln[2:].strip()}**')
                lines.append('')
    return '\n'.join(lines)


def main():
    texts = [(ROOT / p).read_text() for p in ORDER]
    front, body = texts[0], texts[1:]
    # 目录放在导读之后、导论之前
    marker = '## 导论'
    i = front.index(marker)
    full = front[:i] + toc(body) + '\n\n---\n\n' + front[i:]
    full += '\n\n---\n\n' + '\n\n---\n\n'.join(body)
    (ROOT / '全稿.md').write_text(full)
    total = 0
    for p, t in zip(ORDER, texts):
        n = len(HAN.findall(t))
        total += n
        print(f'{n:>7}  {p}')
    print(f'{total:>7}  合计（不含目录）')


if __name__ == '__main__':
    main()
