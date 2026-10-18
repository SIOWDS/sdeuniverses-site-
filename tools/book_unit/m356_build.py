#!/usr/bin/env python3
"""第356号《管理学学派解构入门》单元生成入口（共用 build_unit.py）。

本书 107 章，学习包 PDF 一页一题；题干与自查偏长，把题干字号 12→10.5、追问 11→10、作答横线行距 24→20，保证一页放得下。
用法（仓库根目录）：
  python3 tools/book_unit/m356_build.py --config tools/book_unit/m356.json --out-pdf <学习包 PDF 路径>
"""
import importlib.util, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / 'build_unit.py').read_text(encoding='utf-8')
for a, b, n in [('y -= 24', 'y -= 20', 3),
                ("y = para(t['question'], 43, y, size=12)", "y = para(t['question'], 43, y, size=10.5)", 1),
                ("y = para('读后追问：' + t['checkpoint'], 43, y, size=11)", "y = para('读后追问：' + t['checkpoint'], 43, y, size=10)", 1)]:
    assert src.count(a) == n, (a, src.count(a))
    src = src.replace(a, b)
tmp = Path(tempfile.gettempdir()) / '_build_unit_m356.py'
tmp.write_text(src, encoding='utf-8')
spec = importlib.util.spec_from_file_location('build_unit', tmp)
bu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bu)

if __name__ == '__main__':
    bu.main()
