# SDE艺术论 · 2026年9月重修版

本版依用户要求对照第220号《我的三个宝贝》，同时修正文风与成书版式。

- 正文仍为三部32章、两份附录、47项参考资料；171处表述重新组织，移除堆积的审稿口吻，保留史实、出处与概念适用条件。
- 32章均有原创场景开篇、章首引句、章末“带走的话”；这些句子不是冒充史料或名人引言。
- PDF采用190×250毫米版面、暖纸色、深蓝标题、金色大号章码、金线引句、花饰及章末菱形；封面、封底与网页采用同一视觉体系。
- 当前PDF共154页。`content/art-theory/page-map.json`是翻页目录的页码依据；印刷页1对应PDF物理页2，offset=2。
- 单一正文源：`content/art-theory/revised-2026-09.json`。PDF、全文网页、封面及封底由`tools/build_art_theory.py`生成。
- 重建：`python3 tools/build_art_theory.py --source content/art-theory/revised-2026-09.json --out /tmp/art-book --fonts /path/to/fonts`。
- 字体目录需有NotoSerifSC-Regular.ttf与NotoSerifSC-Semibold.ttf；依赖reportlab、pypdf、PyMuPDF。重建PDF后必须按生成页码重建翻页目录。
- 网站仍走本仓库main分支的Cloudflare发布流程。目录只修改art-theory条目，再用tools/build_bookshelf.py生成三个书架；保留其他书籍并发更新。
- 未分配新的专著编号、ISBN或售价。
