#!/usr/bin/env python3
"""第 568 号：只把本书加进三个书架（/books/、/monographs/、/library/），不动别的书。
tools/build_bookshelf.py 按 catalog.json 重写三个书架（本地已核：对现有书目是幂等的），
但它顺带会调 build_book_agents.py 与 inject_book_agent.py，改写别的书的详情页、智能体页和智能体名录。
本脚本：记下运行前已改动的文件 → 跑 build_bookshelf.py → 把它新改的、三个书架以外的已跟踪文件还原（git restore），
本书目录 public/books/m/568/ 整个恢复成运行前的样子；最后核对三个书架的改动只涉及本书。
须在 publish.py 之后、agent_page.py --roster 之前运行（名录由 agent_page.py 定点加卡）。
用法（仓库根目录）：python3 tools/book-m568/shelves.py
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

SHELVES = ['public/books/index.html', 'public/monographs/index.html', 'public/sites/read/library/index.html']
BOOK = Path('public/books/m/568')


def changed():
    out = subprocess.run(['git', 'diff', '--name-only'], capture_output=True, text=True, check=True).stdout
    return set(x for x in out.splitlines() if x)


before = changed()
assert not (before & set(SHELVES)), '三个书架运行前已有改动，先处理'
tmp = Path(tempfile.mkdtemp()) / '568'
shutil.copytree(BOOK, tmp)
subprocess.run([sys.executable, 'tools/build_bookshelf.py'], check=True)
after = changed()
undo = sorted(f for f in after - before if f not in SHELVES and not f.startswith(str(BOOK) + '/'))
if undo:
    subprocess.run(['git', 'restore', '--'] + undo, check=True)
# 运行前已改动、又被它改写的文件（如 catalog.json）——build_bookshelf 只读不写这些；若真被写了就报错
shutil.rmtree(BOOK)
shutil.copytree(tmp, BOOK)
untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', 'public'], capture_output=True, text=True).stdout.split()
stray = [f for f in untracked if not f.startswith(str(BOOK) + '/')]
assert not stray, ('build_bookshelf 新建了别的文件', stray[:10])
import difflib
for s in SHELVES:
    old = subprocess.run(['git', 'show', 'HEAD:' + s], capture_output=True, text=True, check=True).stdout.split('<article ')
    new = Path(s).read_text(encoding='utf-8').split('<article ')
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            continue
        for k in range(j1, j2):
            if 'data-id="m-568"' in new[k]:
                continue
            # 不是本书的块：只许是书架头部的计数之类的小改动
            o = old[i1] if i1 < len(old) and i2 > i1 else ''
            assert k == 0, (s, 'non-568 card changed', new[k][:160])
            print(s, 'header changed (counts):', [t for t in difflib.SequenceMatcher(None, o, new[k]).get_opcodes() if t[0] != 'equal'][:6])
print('shelves ok; restored', len(undo), 'side-effect files')
