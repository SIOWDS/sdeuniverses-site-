#!/usr/bin/env python3
"""第447号《国家发生学导论》单元生成入口（共用 build_unit.py）。

本书第 1—3 章是「导论」，不属于任何一编；共用脚本只认「第X编」作分组，会把这三章落空。
这里补三处，不改共用脚本：①导论也算一个分组；②学习页分组标题写「导论」与「第一编……第六编」，
而不是「第1编……第7编」；③页面与学习包 PDF 里的规模写「导论六编」。
用法（仓库根目录）：
  python3 tools/book_unit/m447_build.py --config tools/book_unit/m447.json --out-pdf <学习包 PDF 路径>
"""
import importlib.util, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / 'build_unit.py').read_text(encoding='utf-8')
reps = [
    ("(第[一二三四五六七八九十]+[编篇]|卷", "(导论|第[一二三四五六七八九十]+[编篇]|卷"),
    ("\"'第'+(i+1)+'%s · '\" % PW", "\"(i===0?'导论 · ':'第'+'一二三四五六七八九十'[i-1]+'%s · ')\" % PW"),
    ("'第%d%s · %s' % (t['part'], PW, part_names[t['part'] - 1])",
     "(('导论 · %s' % part_names[0]) if t['part'] == 1 else ('第%s%s · %s' % (cn(t['part'] - 1), PW, part_names[t['part'] - 1])))"),
]
for a, b in reps:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
n = src.count("cn(len(parts)), PW, NUMW)")
assert n == 2, n
src = src.replace("cn(len(parts)), PW, NUMW)", "'导论与' + cn(len(parts) - 1), PW, NUMW)")
tmp = Path(tempfile.gettempdir()) / '_build_unit_m447.py'
tmp.write_text(src, encoding='utf-8')
spec = importlib.util.spec_from_file_location('build_unit', tmp)
bu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bu)

if __name__ == '__main__':
    bu.main()
