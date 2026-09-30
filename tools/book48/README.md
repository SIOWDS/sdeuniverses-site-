# 第 48 号《三律心理学》精选本（约 20 万字）

从 `public/books/m/48/quanben/text/`（七十万字全本网页版）按选篇清单编出精选本。

1. `units.py` —— 把全本各篇切成子篇单元，写 `units.json`（选篇清单按单元序号引用）。
2. `compile.py` —— 按 `PARTS` 选篇清单抽取原文，接回 PDF 断行，还原误标为列表的正文段落，
   去掉篇内旧章号，修订编序/编结对未选篇目的提法，写 `book.json`。
3. `to_md.py` —— 生成排版稿 `manuscript.md`。
4. 用 sde-popular-philosophy-style 的 `build_book.py`（`--preset current --edition both`）排印刷版与阅读版 PDF；
   封面用 `make_cover.py --art art48.svg`。WeasyPrint 70 下目录点线需改为表格布局。
5. `gen_web.py` —— 生成 `public/books/m/48/text/` 网页版（需先从 PDF 书签导出 `outline.json`）。

脚本里的路径指向编稿时的临时目录，重跑前按需调整。
