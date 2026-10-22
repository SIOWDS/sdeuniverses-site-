#!/usr/bin/env python3
"""第499号《走样》单元生成入口：共用 build_unit.py，运行时在内存里把学习包 PDF 的作答横线行距 24→16、段后间距 12→8、
读后追问字号 11→10.5（题干与追问较长，否则一页放不下）。不改 build_unit.py。
用法（仓库根目录）：python3 tools/book_unit/m499_build.py --config tools/book_unit/m499.json --out-pdf <PDF 路径>"""
import sys
from pathlib import Path
src = (Path(__file__).resolve().parent / 'build_unit.py').read_text(encoding='utf-8')
assert src.count('y -= 24') == 3, src.count('y -= 24')
src = src.replace('y -= 24', 'y -= 16')
assert src.count('return y - h - 12') == 1
src = src.replace('return y - h - 12', 'return y - h - 8')
assert src.count('y -= 12; y = para(') == 1 and src.count('y -= 10; y = para(') == 1
src = src.replace('y -= 12; y = para(', 'y -= 6; y = para(').replace('y -= 10; y = para(', 'y -= 6; y = para(')
old = "y = para('读后追问：' + t['checkpoint'], 43, y, size=11)"
assert src.count(old) == 1
src = src.replace(old, "y = para('读后追问：' + t['checkpoint'], 43, y, size=10.5)")
sys.argv[0] = str(Path(__file__).resolve().parent / 'build_unit.py')
exec(compile(src, 'build_unit.py', 'exec'), {'__name__': '__main__', '__file__': sys.argv[0]})
