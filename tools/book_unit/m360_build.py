#!/usr/bin/env python3
"""第360号《政治学学派解构入门》单元生成入口。

共用 build_unit.py，只补一处：原 cn() 只会写到九十九，本书有 116 个学习单元，
这里把 cn 换成能写到九百九十九的版本，其余一概不动。

用法（仓库根目录）：
  python3 tools/book_unit/m360_build.py --config tools/book_unit/m360.json --out-pdf <学习包 PDF 路径>
"""
import importlib.util, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('build_unit', HERE / 'build_unit.py')
bu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bu)

CN = bu.CN
_cn_orig = bu.cn


def cn_big(n):
    if n < 100:
        return _cn_orig(n)
    h, r = divmod(n, 100)
    s = CN[h] + '百'
    if r == 0:
        return s
    if r < 10:
        return s + '零' + CN[r]
    t, o = divmod(r, 10)
    return s + CN[t] + '十' + (CN[o] if o else '')


bu.cn = cn_big

if __name__ == '__main__':
    bu.main()
