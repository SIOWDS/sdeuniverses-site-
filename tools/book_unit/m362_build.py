#!/usr/bin/env python3
"""第362号《传播学学派解构入门》单元生成入口（共用 build_unit.py）。

补两处：①cn() 只会写到九十九，本书 56 章虽不超百，但保持与第360号同一入口；
②学习包 PDF 一页一题，本书题干与自查略长，把作答横线行距由 24 收到 20，保证一页放得下。
用法（仓库根目录）：
  python3 tools/book_unit/m362_build.py --config tools/book_unit/m362.json --out-pdf <学习包 PDF 路径>
"""
import importlib.util, sys, tempfile, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / 'build_unit.py').read_text(encoding='utf-8')
n = src.count('y -= 24')
assert n == 3, n
src = src.replace('y -= 24', 'y -= 20')
tmp = Path(tempfile.gettempdir()) / '_build_unit_m362.py'
tmp.write_text(src, encoding='utf-8')
spec = importlib.util.spec_from_file_location('build_unit', tmp)
bu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bu)

if __name__ == '__main__':
    bu.main()
